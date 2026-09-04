# -*- coding: utf-8 -*-
from __future__ import annotations

"""Functional realizer for the distinct Grounded Human Reception layer.

RR5 consumes the body-free Move sequence produced by RR2/RR3 and the ClausePlan
binding produced by RR4. RR7 keeps that same Move ownership through recovery;
only an optional third Move may be removed. It does not use case ids, source
bodies, or a completed observation as selection cues. Surface text is composed
from move-scoped semantic referents and deterministic role/act families.
"""

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Final, Literal
import unicodedata

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import (
    GroundedHumanReceptionPlan,
    GroundedObservationPlan,
    GroundedReceptionAct,
    GroundedReceptionMovePlan,
    GroundedSemanticNucleus,
)


ReceptionRecoveryStage = Literal[
    "full",
    "optional_removed",
    "integrated",
    "hedged",
    "minimal_grounded",
]
ReceptionConnectorPolicy = Literal[
    "none",
    "grounded_reason",
    "contrast_safe",
]
ReceptionExpressionReferenceMode = Literal[
    "EXPLICIT",
    "COMPOSITE",
    "ANAPHORIC",
]

SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.human_reception.realizable_expression.v1"
)
RECEPTION_VISIBLE_SEGMENT_BINDING_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_visible_segment_binding.v1"
)

_RECOVERY_STAGES: Final = frozenset(
    {
        "full",
        "optional_removed",
        "integrated",
        "hedged",
        "minimal_grounded",
    }
)
_TERMINAL_PREDICATE_BY_ACT: Final[dict[GroundedReceptionAct, str]] = {
    "stay_with_current_burden": "human_response_stay_with_burden",
    "honor_concrete_effort": "human_response_honor_effort",
    "protect_retained_intention": "human_response_protect_intention",
    "recognize_lived_change": "human_response_recognize_change",
    "hold_help_seeking": "human_response_hold_help_seeking",
    "bounded_counter_self_denial": "human_response_bounded_counterposition",
    "respect_words_placed": "human_response_respect_words",
}
_STANCE_BY_ACT: Final[dict[GroundedReceptionAct, str]] = {
    "stay_with_current_burden": "quiet_presence",
    "honor_concrete_effort": "warm_recognition",
    "protect_retained_intention": "gentle_respect",
    "recognize_lived_change": "warm_recognition",
    "hold_help_seeking": "protective_presence",
    "bounded_counter_self_denial": "bounded_disagreement",
    "respect_words_placed": "gentle_respect",
}
_MOVE_ROLE_ORDER: Final = {
    "attention": 0,
    "significance": 1,
    "felt_response": 2,
    "bounded_counterposition": 3,
}
_MOVE_ROLE_BY_SURFACE_STRATEGY: Final = {
    "quiet_referent_first": "felt_response",
    "emlis_attention_first": "attention",
    "referent_significance_first": "significance",
    "felt_response_first": "felt_response",
    "explicit_emlis_counterposition": "bounded_counterposition",
}
_MOVE_PREDICATE_FAMILY_BY_ROLE_ACT: Final[dict[tuple[str, str], str]] = {
    ("attention", "stay_with_current_burden"): "human_response_attention_not_overlooked",
    ("attention", "honor_concrete_effort"): "human_response_attention_stood_out",
    ("attention", "protect_retained_intention"): "human_response_attention_stood_out",
    ("attention", "recognize_lived_change"): "human_response_attention_stood_out",
    ("attention", "hold_help_seeking"): "human_response_attention_not_overlooked",
    ("attention", "respect_words_placed"): "human_response_attention_not_overlooked",
    ("significance", "stay_with_current_burden"): "human_response_significance_not_minimized",
    ("significance", "honor_concrete_effort"): "human_response_significance_effort_made_concrete",
    (
        "significance",
        "protect_retained_intention",
    ): "human_response_significance_intention_preserved",
    ("significance", "recognize_lived_change"): "human_response_significance_change_confirmed",
    ("significance", "hold_help_seeking"): "human_response_significance_help_preserved",
    ("significance", "respect_words_placed"): "human_response_significance_words_placed",
    ("felt_response", "stay_with_current_burden"): "human_response_quiet_presence",
    ("felt_response", "honor_concrete_effort"): "human_response_felt_respect_for_effort",
    ("felt_response", "protect_retained_intention"): "human_response_felt_gentle_respect",
    ("felt_response", "recognize_lived_change"): "human_response_recognize_change",
    ("felt_response", "hold_help_seeking"): "human_response_hold_help_seeking",
    ("felt_response", "respect_words_placed"): "human_response_quiet_presence",
    (
        "bounded_counterposition",
        "bounded_counter_self_denial",
    ): "human_response_bounded_counterposition",
}
_SENTENCE_END_RE: Final = re.compile(r"[。！？!?]+")
_QUESTION_RE: Final = re.compile(r"[?？]")
_QUOTE_RE: Final = re.compile(r"「([^」]*)」")
_POLICY_EXPLANATION_RE: Final = re.compile(
    r"(?:理由|原因).{0,20}(?:決めつけ|断定)|"
    r"入力から言える範囲|診断はしません|ここでは事実として扱いません|"
    r"原因は分かりません"
)
_ADVICE_RE: Final = re.compile(
    r"(?:してください|しましょう|してみて|すべき|した方がいい|"
    r"相談して|連絡して|受診して)"
)
_UNSUPPORTED_CLAIM_RE: Final = re.compile(
    r"(?:必ず|絶対に|確実に|成功|解決|安全です|危険度|診断|"
    r"あなたは(?:強い|優しい|立派|素晴らしい))"
)
_ACT_RESPONSIBILITY_RE: Final[dict[GroundedReceptionAct, re.Pattern[str]]] = {
    "stay_with_current_burden": re.compile(
        r"(?:負荷|しんどさ|苦しさ|つらさ|置かれた言葉).{0,32}"
        r"(?:軽く扱|小さくせず)"
    ),
    "honor_concrete_effort": re.compile(
        r"(?:行動|動いたこと|動かしたこと|記録へ移したこと|働きかけ)"
        r".{0,48}(?:大切|受け止|軽いこととして流さ|軽く扱わ)"
    ),
    "protect_retained_intention": re.compile(
        r"(?:願い|大切にしたいもの).{0,40}(?:大切|なかったこと|消さず)"
    ),
    "recognize_lived_change": re.compile(
        r"変化.{0,40}(?:感じ|受け止|見過ご|軽く扱|軽いこと|流したく)"
    ),
    "hold_help_seeking": re.compile(
        r"(?:助け|踏みとどまり).{0,64}"
        r"(?:大切|受け止|尊重|見失わず|見守)"
    ),
    "bounded_counter_self_denial": re.compile(
        r"苦しさ.{0,48}否定せず.*Emlis.{0,48}自身.{0,24}思えません"
    ),
    "respect_words_placed": re.compile(r"言葉.{0,40}(?:大切|受け止)"),
}
_ACT_OWNED_RESPONSIBILITY_RE: Final[
    dict[GroundedReceptionAct, re.Pattern[str]]
] = {
    "stay_with_current_burden": re.compile(
        r"(?:負荷|しんどさ|苦しさ|つらさ|置かれた言葉).*?"
        r"(?:軽く扱|小さくせず)"
    ),
    "honor_concrete_effort": re.compile(
        r"(?:行動|動いたこと|動かしたこと|記録へ移したこと|働きかけ)"
        r".*?(?:大切|受け止|軽いこととして流さ|軽く扱わ)"
    ),
    "protect_retained_intention": re.compile(
        r"(?:願い|大切にしたいもの).*?(?:大切|なかったこと|消さず)"
    ),
    "recognize_lived_change": re.compile(
        r"変化.*?(?:感じ|受け止|見過ご|軽く扱|軽いこと|流したく)"
    ),
    "hold_help_seeking": re.compile(
        r"(?:助け|踏みとどまり).*?"
        r"(?:大切|受け止|尊重|見失わず|見守)"
    ),
    "bounded_counter_self_denial": re.compile(
        r"苦しさ.*?否定せず.*?Emlis.*?自身.*?思えません"
    ),
    "respect_words_placed": re.compile(r"言葉.*?(?:大切|受け止)"),
}
_ATTENTION_RESPONSIBILITY_RE: Final = re.compile(
    r"(?:目が留まり|印象に残|見過ご)"
)
_ANAPHORIC_CONTEXT_MARKER_RE: Final = re.compile(r"中(?:で|にも)|背景")
_ANAPHORIC_TOPIC_OBJECT_RE: Final = re.compile(
    r"(?:^|[、,。．.!！?？])"
    r"(?P<topic>[ぁ-んァ-ヶ一-鿿々ー]{1,18})"
    r"(?:を|は)"
    r"[ぁ-んァ-ヶ一-鿿々ー]{1,16}"
    r"(?:たい|たく)"
)
_ANAPHORIC_TOPIC_SAHEN_RE: Final = re.compile(
    r"(?:^|[、,。．.!！?？])"
    r"(?P<topic>[ァ-ヶ一-鿿々ー]{2,12})"
    r"し(?:たい|たく)"
)
_ANAPHORIC_TOPIC_SOURCE_MAX_CHARS: Final = 24
_ANCHOR_DELETE_TRANSLATION: Final = str.maketrans("", "", "「」『』?？!！")
_FINAL_FRAGMENT_DELETE_TRANSLATION: Final = str.maketrans("", "", "「」?？")
_FINAL_LEADING_CONNECTOR_RE: Final = re.compile(
    r"^(?:でも|だけど|けれど|けど|ただ|一方で?|で|そして|"
    r"と[、,]\s*それから|それでも|とはいえ|"
    r"と考えて(?:いたけど|しまって)|とか|という)[、,\s]*"
)
_FINAL_JA_SENTENCE_END: Final = "。"
_FINAL_RELATION_LABELS: Final[dict[str, str]] = {
    "temporal_before_after": "時間の前後",
    "shift_from_to": "前から後への変化",
    "contrast": "異なる向き",
    "coexistence": "同時にある状態",
    "user_stated_cause": "入力内で示された理由のつながり",
    "user_stated_result": "入力内で示された結果のつながり",
    "attempt_and_block": "試みと止まり方",
    "wish_and_constraint": "願いと制約の重なり",
    "action_supports_change": "考えと行動のつながり",
    "evaluation_about_event": "出来事への評価",
    "self_evaluation_about_state": "自己評価と状態のつながり",
    "preserves_despite": "苦しさの中にも残る向き",
    "uncertain_connection": "入力に置かれた順序上のつながり",
    "continuation_or_refusal": "続けることへの否定",
}
_FINAL_RECEPTION_RELATION_PREFERENCE: Final[dict[str, tuple[str, ...]]] = {
    "protect_retained_intention": (
        "preserves_despite",
        "wish_and_constraint",
        "coexistence",
        "contrast",
        "continuation_or_refusal",
    ),
    "hold_help_seeking": (
        "wish_and_constraint",
        "preserves_despite",
        "coexistence",
        "contrast",
    ),
    "honor_concrete_effort": (
        "action_supports_change",
        "temporal_before_after",
        "user_stated_result",
    ),
    "recognize_lived_change": (
        "action_supports_change",
        "temporal_before_after",
        "contrast",
    ),
}


class GroundedHumanReceptionSurfaceError(ValueError):
    """Raised when a grounded reception cannot satisfy its R4 contract."""


@dataclass(frozen=True, repr=False)
class RealizableReceptionArgumentV1:
    """One ordered semantic role and its grammatical realization duty."""

    semantic_ref: str
    source_evidence_refs: tuple[str, ...]
    semantic_role: str
    lexical_form: str = field(repr=False)
    requirement: Literal["REQUIRED", "OPTIONAL"]
    omission_permission: Literal["FORBIDDEN", "PERMITTED"]
    zero_realization_condition_refs: tuple[str, ...]
    omission_condition_refs: tuple[str, ...]
    case_marker: str | None
    direction_ref: str | None
    relation_endpoint_ref: str | None
    realization: Literal["EXPLICIT", "ZERO", "OMITTED"]


@dataclass(frozen=True, repr=False)
class SourceGroundedRealizableReceptionExpressionV1:
    """Request-local exact Move carrier from selected meaning to Reception."""

    schema_version: Literal[
        "cocolon.emlis.human_reception.realizable_expression.v1"
    ]
    expression_ref: str
    meaning_outcome_ref: str
    reception_binding_ref: str
    move_id: str
    source_evidence_refs: tuple[str, ...]
    actor_refs: tuple[str, ...]
    subject_refs: tuple[str, ...]
    experiencer_refs: tuple[str, ...]
    predicate_kind: str
    lexical_head: str = field(repr=False)
    arguments: tuple[RealizableReceptionArgumentV1, ...] = field(repr=False)
    polarity: str
    modality: str
    time_scope: str
    aspect: str
    degree: str
    quantity: str
    scope: str
    qualifier_refs: tuple[str, ...]
    relation_refs: tuple[str, ...]
    relation_endpoint_refs: tuple[str, ...]
    direction_refs: tuple[str, ...]
    reference_mode: ReceptionExpressionReferenceMode
    antecedent_refs: tuple[str, ...]
    antecedent_condition: str | None
    particle_plan: tuple[str, ...]
    inflection_plan: tuple[str, ...]
    nominalization_plan: tuple[str, ...]
    clause_link_plan: tuple[str, ...]
    provenance_refs: tuple[str, ...]


@dataclass(frozen=True, repr=False)
class ReceptionVisibleSegmentBindingV1:
    """Exact Human Reception-authored scalar segment and semantic owners."""

    binding_ref: str
    expression_refs: tuple[str, ...]
    move_ids: tuple[str, ...]
    human_reception_local_scalar_start: int
    human_reception_local_scalar_end: int
    surface_span_sha256: str
    clause_frame_fields: Mapping[str, Any] = field(repr=False)
    surface_derivation_refs: tuple[str, ...]


@dataclass(frozen=True)
class GroundedReceptionClausePlan:
    """Body-free RR4 binding of one surface sentence to one or two Moves."""

    sentence_slot: int
    move_ids: tuple[str, ...]
    opening_strategy: str
    connector_policy: ReceptionConnectorPolicy
    terminal_predicate_family: str
    quote_budget: int
    speaker_presence: str


@dataclass(frozen=True)
class _ReceptionArgumentRealizationV1:
    """One ID-free semantic slot and its exact grammatical duty."""

    semantic_slot: int
    semantic_role: str
    lexical_form: str = field(repr=False)
    case_marker: str | None
    relation_slot: int | None
    direction_side: Literal["FROM", "TO"] | None
    realization: Literal["EXPLICIT", "ZERO"]


@dataclass(frozen=True)
class _ReceptionRelationRealizationV1:
    """One ID-free relation with ordered endpoint slots and roles."""

    relation_kind: str
    endpoint_slots: tuple[int, int]
    endpoint_roles: tuple[str, str]


@dataclass(frozen=True)
class _ReceptionSemanticProfileV1:
    """Plan-owned syntax/voice facts for one opaque semantic slot."""

    nucleus_kind: str
    actor_kind: str
    predicate_kind: str
    performed_action: bool
    future_action: bool
    quoted_boundary: bool


@dataclass(frozen=True)
class _ReceptionMoveRealizationV1:
    """ID-free facts which alone are allowed to affect final Layer 2 bytes."""

    focus_kinds: tuple[str, ...]
    semantic_fragments: tuple[str, ...] = field(repr=False)
    semantic_heads: tuple[str, ...] = field(repr=False)
    semantic_profiles: tuple[_ReceptionSemanticProfileV1, ...]
    target_slot_count: int
    context_slots: tuple[int, ...]
    arguments: tuple[_ReceptionArgumentRealizationV1, ...] = field(
        repr=False
    )
    predicate_kind: str
    predicate_head: str = field(repr=False)
    actor_slots: tuple[int, ...]
    subject_slots: tuple[int, ...]
    experiencer_slots: tuple[int, ...]
    polarity: str
    modality: str
    time_scope: str
    aspect: str
    degree: str
    quantity: str
    scope: str
    subject_realization: Literal["EXPLICIT", "ZERO"]
    reference_mode: ReceptionExpressionReferenceMode
    antecedent_slots: tuple[int, ...]
    antecedent_condition: str | None
    relations: tuple[_ReceptionRelationRealizationV1, ...]
    relation_predicate_kinds: tuple[str, ...]
    governing_relation_slots: tuple[int, ...]
    recovery_form: ReceptionRecoveryStage
    clause_form: Literal["FINITE", "CONTINUATIVE"]


@dataclass(frozen=True)
class _ReceptionClauseRealizationV1:
    """One sentence's ordered, ID-free, surface-affecting realization."""

    sentence_slot: int
    moves: tuple[_ReceptionMoveRealizationV1, ...]


@dataclass(frozen=True)
class _ReceptionClauseBindingSeedV1:
    """Forward-only owners which never participate in wording decisions."""

    expression_refs: tuple[str, ...]
    move_ids: tuple[str, ...]
    clause_frame_fields: Mapping[str, Any] = field(repr=False)
    surface_derivation_refs: tuple[str, ...]


@dataclass(frozen=True, repr=False)
class _SourceGroundedClauseCoreV1:
    """One grammatical content core with one visible target referent."""

    text: str
    target_referent: str
    semantic_slots: tuple[int, ...]
    relation_count: int
    target_owner_slot: int
    temporal_realization: Literal[
        "SOURCE_CLAUSE", "ANTECEDENT", "ADJUNCT"
    ]
    aspect_realization: Literal[
        "SOURCE_CLAUSE", "ANTECEDENT", "ADJUNCT"
    ]
    temporal_adjunct: str = field(repr=False)
    aspect_adjunct: str = field(repr=False)
    voice: Literal[
        "SELF_PERFORMED",
        "OTHER_PERFORMED",
        "FUTURE_INTENTION",
        "RECEIVED",
        "STATE",
    ]


@dataclass(frozen=True, repr=False)
class _SourceGroundedResponsePredicateV1:
    """Independent role valency and act-governed predicate morphemes."""

    object_particle: str
    role_operator: str
    act_guard: str
    reception_operator: str
    voice_complement: str
    valency_complement: str
    predicate_lemma: str
    conjugation_class: Literal[
        "ICHIDAN", "GODAN_RU", "GODAN_TSU", "GODAN_U", "GODAN_SU"
    ]


@dataclass(frozen=True)
class GroundedReceptionReferent:
    """Short anaphoric referent selected only from plan semantics."""

    kind: str
    text: str
    nucleus_ids: tuple[str, ...]
    evidence_span_ids: tuple[str, ...]
    source_anchor_used: bool = False


@dataclass(frozen=True)
class GroundedHumanResponsePredicate:
    """Act-specific predicate fragment, not a completed sentence."""

    terminal_predicate_kind: str
    object_particle: str
    predicate_fragment: str


@dataclass(frozen=True, repr=False)
class GroundedHumanReceptionSurface:
    """Ephemeral validated reception surface and body-free diagnostics."""

    text: str
    terminal_predicate_kinds: tuple[str, ...]
    sentence_count: int
    referent_kind: str
    realized_reception_acts: tuple[GroundedReceptionAct, ...]
    realized_move_ids: tuple[str, ...]
    realized_move_roles: tuple[str, ...]
    move_predicate_families: tuple[str, ...]
    realized_clause_move_ids: tuple[tuple[str, ...], ...]
    grounded_nucleus_ids: tuple[str, ...]
    grounded_evidence_span_ids: tuple[str, ...]
    source_anchor_count: int
    source_anchor_max_visible_chars: int
    recovery_stage: ReceptionRecoveryStage
    expression_refs: tuple[str, ...] = ()
    visible_segment_bindings: tuple[ReceptionVisibleSegmentBindingV1, ...] = ()


def _private_canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _source_grounded_relation_endpoint_ref(
    relation_ref: str,
    semantic_ref: str,
    semantic_role: str,
) -> str:
    """Identify one existing expression-field endpoint without leaking ids."""

    digest = hashlib.sha256(
        b"cocolon.emlis.human_reception.relation_endpoint.v1\0"
        + _private_canonical_json_bytes(
            (relation_ref, semantic_ref, semantic_role)
        )
    ).hexdigest()
    return (
        "source-grounded-relation-endpoint:"
        f"{digest}@{SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION}"
    )


def _source_grounded_direction_ref(
    relation_ref: str,
    semantic_ref: str,
    semantic_role: str,
    direction_side: Literal["FROM", "TO"],
) -> str:
    """Identify one existing expression-field directional duty."""

    digest = hashlib.sha256(
        b"cocolon.emlis.human_reception.direction.v1\0"
        + _private_canonical_json_bytes(
            (relation_ref, semantic_ref, semantic_role, direction_side)
        )
    ).hexdigest()
    return (
        "source-grounded-direction:"
        f"{digest}@{SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION}"
    )


def _is_nonempty_private_string(value: Any) -> bool:
    return type(value) is str and bool(value.strip())


def _is_private_string_tuple(
    value: Any,
    *,
    allow_empty: bool = True,
) -> bool:
    return bool(
        type(value) is tuple
        and (allow_empty or value)
        and all(_is_nonempty_private_string(item) for item in value)
    )


def _has_unique_private_strings(value: tuple[str, ...]) -> bool:
    return len(value) == len(set(value))


def identify_source_grounded_reception_expression(
    expression: SourceGroundedRealizableReceptionExpressionV1,
) -> SourceGroundedRealizableReceptionExpressionV1:
    """Seal the complete request-local expression payload."""

    if type(expression) is not SourceGroundedRealizableReceptionExpressionV1:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    try:
        payload = asdict(expression)
        payload.pop("expression_ref", None)
        digest = hashlib.sha256(
            b"cocolon.emlis.human_reception.realizable_expression.v1\0"
            + _private_canonical_json_bytes(payload)
        ).hexdigest()
    except (AttributeError, TypeError, UnicodeError, ValueError):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        ) from None
    return replace(
        expression,
        expression_ref=(
            "source-grounded-realizable-reception-expression:"
            f"{digest}@{SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION}"
        ),
    )


def _validate_realizable_reception_argument(
    argument: RealizableReceptionArgumentV1,
) -> None:
    if type(argument) is not RealizableReceptionArgumentV1:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    if (
        not _is_nonempty_private_string(argument.semantic_ref)
        or not _is_private_string_tuple(
            argument.source_evidence_refs,
            allow_empty=False,
        )
        or not _is_nonempty_private_string(argument.semantic_role)
        or not _is_nonempty_private_string(argument.lexical_form)
        or type(argument.requirement) is not str
        or argument.requirement not in {"REQUIRED", "OPTIONAL"}
        or type(argument.omission_permission) is not str
        or argument.omission_permission not in {"FORBIDDEN", "PERMITTED"}
        or not _is_private_string_tuple(
            argument.zero_realization_condition_refs
        )
        or not _is_private_string_tuple(argument.omission_condition_refs)
        or not (
            argument.case_marker is None
            or _is_nonempty_private_string(argument.case_marker)
        )
        or not (
            argument.direction_ref is None
            or _is_nonempty_private_string(argument.direction_ref)
        )
        or not (
            argument.relation_endpoint_ref is None
            or _is_nonempty_private_string(argument.relation_endpoint_ref)
        )
        or type(argument.realization) is not str
        or argument.realization not in {"EXPLICIT", "ZERO", "OMITTED"}
        or not _has_unique_private_strings(argument.source_evidence_refs)
        or not _has_unique_private_strings(
            argument.zero_realization_condition_refs
        )
        or not _has_unique_private_strings(argument.omission_condition_refs)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    if (
        argument.omission_permission == "PERMITTED"
        and (
            argument.requirement != "OPTIONAL"
            or not argument.omission_condition_refs
        )
    ) or (
        argument.omission_permission == "FORBIDDEN"
        and argument.omission_condition_refs
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    if (
        argument.realization == "ZERO"
        and not argument.zero_realization_condition_refs
    ) or (
        argument.realization == "OMITTED"
        and (
            argument.requirement != "OPTIONAL"
            or argument.omission_permission != "PERMITTED"
            or not argument.omission_condition_refs
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    # The current plan has one finite condition owner.  Prefix-shaped values
    # are not proof of an antecedent/case/omission duty; admit those only when
    # an existing typed owner is added to the plan contract.
    if any(
        ref != "shared-subject:current-user"
        for ref in argument.zero_realization_condition_refs
    ) or any(
        ref != "omission-duty:optional"
        for ref in argument.omission_condition_refs
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )


def _validate_expression_structural_types(
    expression: SourceGroundedRealizableReceptionExpressionV1,
) -> None:
    if type(expression) is not SourceGroundedRealizableReceptionExpressionV1:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    scalar_string_fields = (
        expression.schema_version,
        expression.expression_ref,
        expression.meaning_outcome_ref,
        expression.reception_binding_ref,
        expression.move_id,
        expression.predicate_kind,
        expression.lexical_head,
        expression.polarity,
        expression.modality,
        expression.time_scope,
        expression.aspect,
        expression.degree,
        expression.quantity,
        expression.scope,
        expression.reference_mode,
    )
    tuple_string_fields = (
        expression.source_evidence_refs,
        expression.actor_refs,
        expression.subject_refs,
        expression.experiencer_refs,
        expression.qualifier_refs,
        expression.relation_refs,
        expression.relation_endpoint_refs,
        expression.direction_refs,
        expression.antecedent_refs,
        expression.provenance_refs,
    )
    if (
        any(type(value) is not str for value in scalar_string_fields)
        or type(expression.arguments) is not tuple
        or any(
            type(argument) is not RealizableReceptionArgumentV1
            for argument in expression.arguments
        )
        or any(not _is_private_string_tuple(value) for value in tuple_string_fields)
        or not (
            expression.antecedent_condition is None
            or type(expression.antecedent_condition) is str
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    if any(
        not _is_private_string_tuple(value)
        for value in (
            expression.particle_plan,
            expression.inflection_plan,
            expression.nominalization_plan,
            expression.clause_link_plan,
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )


def _validate_expression_morphology(
    expression: SourceGroundedRealizableReceptionExpressionV1,
) -> None:
    expected_particle_plan = tuple(
        f"particle:{argument.semantic_role}:"
        f"{argument.case_marker or 'ZERO'}"
        for argument in expression.arguments
    )
    base_inflection = (
        f"predicate:{expression.predicate_kind}",
        f"polarity:{expression.polarity}",
        f"modality:{expression.modality}",
        f"time:{expression.time_scope}",
        f"aspect:{expression.aspect}",
    )
    inflection = expression.inflection_plan
    focus_body = (
        inflection[8].removeprefix("focus-kind:")
        if len(inflection) > 8 and type(inflection[8]) is str
        else ""
    )
    focus_kinds = tuple(focus_body.split("+")) if focus_body else ()
    focus_valid = bool(
        focus_kinds
        and all(focus_kinds)
        and len(focus_kinds) == len(set(focus_kinds))
        and "+".join(focus_kinds) == focus_body
        and all(
            kind in _SOURCE_GROUNDED_FOCUS_NOMINAL
            for kind in focus_kinds
        )
    )
    extended_suffix_valid = bool(
        len(inflection) == 13
        and inflection[:5] == base_inflection
        and inflection[5:8]
        == (
            f"degree:{expression.degree}",
            f"quantity:{expression.quantity}",
            f"scope:{expression.scope}",
        )
        and inflection[8] == f"focus-kind:{focus_body}"
        and focus_valid
        and inflection[9] == "head-class:source-grounded-proposition"
        and inflection[10] == "politeness:polite"
        and inflection[11] in {
            f"reception-form:{stage}" for stage in _RECOVERY_STAGES
        }
        and inflection[12] in {
            "clause-form:FINITE",
            "clause-form:CONTINUATIVE",
        }
    )
    typed_relation_links = bool(
        expression.relation_refs
        and len(expression.clause_link_plan)
        == len(expression.relation_refs)
        and all(
            row.startswith("relation-kind:")
            and row.removeprefix("relation-kind:") in _FINAL_RELATION_LABELS
            for row in expression.clause_link_plan
        )
    )
    expected_no_relation_links = ("clause-link:none",)
    if (
        expression.particle_plan != expected_particle_plan
        or not _has_unique_private_strings(inflection)
        or not extended_suffix_valid
        or expression.nominalization_plan
        != ("nominalization:source-grounded-reception-object",)
        or not (
            (
                not expression.relation_refs
                and expression.clause_link_plan
                == expected_no_relation_links
            )
            or (
                bool(expression.relation_refs)
                and typed_relation_links
            )
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )


def validate_source_grounded_reception_expression(
    expression: SourceGroundedRealizableReceptionExpressionV1,
) -> None:
    """Fail closed on any incomplete or non-canonical expression."""

    _validate_expression_structural_types(expression)
    if (
        expression.schema_version
        != SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION
        or not _is_nonempty_private_string(expression.predicate_kind)
        or not _is_nonempty_private_string(expression.lexical_head)
        or any(
            not _is_nonempty_private_string(value)
            for value in (
                expression.polarity,
                expression.modality,
                expression.time_scope,
                expression.aspect,
                expression.degree,
                expression.quantity,
                expression.scope,
            )
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    if (
        not _is_nonempty_private_string(expression.expression_ref)
        or not _is_nonempty_private_string(expression.meaning_outcome_ref)
        or not _is_nonempty_private_string(expression.reception_binding_ref)
        or not _is_nonempty_private_string(expression.move_id)
        or not expression.source_evidence_refs
        or not expression.provenance_refs
        or not _has_unique_private_strings(expression.source_evidence_refs)
        or not _has_unique_private_strings(expression.provenance_refs)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    expected_identity = identify_source_grounded_reception_expression(
        replace(expression, expression_ref="")
    ).expression_ref
    if expression.expression_ref != expected_identity:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    if not expression.arguments or not (
        expression.actor_refs
        or expression.subject_refs
        or expression.experiencer_refs
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    for argument in expression.arguments:
        _validate_realizable_reception_argument(argument)
    argument_semantic_refs = _dedupe(
        argument.semantic_ref for argument in expression.arguments
    )
    argument_semantic_ref_set = set(argument_semantic_refs)
    argument_keys = tuple(
        (
            argument.semantic_ref,
            argument.semantic_role,
            argument.relation_endpoint_ref,
        )
        for argument in expression.arguments
    )
    lexical_by_ref: dict[str, str] = {}
    for argument in expression.arguments:
        prior = lexical_by_ref.setdefault(
            argument.semantic_ref,
            argument.lexical_form,
        )
        if prior != argument.lexical_form:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
    if (
        len(argument_keys) != len(set(argument_keys))
        or any(
            not _has_unique_private_strings(values)
            for values in (
                expression.actor_refs,
                expression.subject_refs,
                expression.experiencer_refs,
                expression.qualifier_refs,
                expression.relation_refs,
                expression.relation_endpoint_refs,
                expression.direction_refs,
                expression.antecedent_refs,
            )
        )
        or not set(
            (
                *expression.actor_refs,
                *expression.subject_refs,
                *expression.experiencer_refs,
            )
        ).issubset(argument_semantic_ref_set)
        or expression.relation_endpoint_refs
        != _dedupe(
            argument.relation_endpoint_ref
            for argument in expression.arguments
            if argument.relation_endpoint_ref is not None
        )
        or expression.direction_refs
        != _dedupe(
            argument.direction_ref
            for argument in expression.arguments
            if argument.direction_ref is not None
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    relation_kinds = (
        ()
        if expression.clause_link_plan == ("clause-link:none",)
        else tuple(
            row.removeprefix("relation-kind:")
            for row in expression.clause_link_plan
        )
    )
    if (
        len(relation_kinds) != len(expression.relation_refs)
        or any(
            not relation_ref.startswith("edge:")
            for relation_ref in expression.relation_refs
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    endpoint_roles = {
        role
        for role_pair in _SOURCE_GROUNDED_RELATION_ROLE_PAIR.values()
        for role in role_pair
    }
    endpoint_arguments_by_relation: dict[
        int, list[RealizableReceptionArgumentV1]
    ] = {
        index: [] for index in range(len(expression.relation_refs))
    }
    for argument in expression.arguments:
        role = argument.semantic_role
        if role not in _SOURCE_GROUNDED_ARGUMENT_ROLES:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        if role in endpoint_roles:
            matches = tuple(
                index
                for index, relation_ref in enumerate(
                    expression.relation_refs
                )
                if argument.relation_endpoint_ref
                == _source_grounded_relation_endpoint_ref(
                    relation_ref,
                    argument.semantic_ref,
                    role,
                )
            )
            if len(matches) != 1:
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            relation_slot = matches[0]
            expected_role_pair = _SOURCE_GROUNDED_RELATION_ROLE_PAIR.get(
                relation_kinds[relation_slot]
            )
            direction_side = _source_grounded_direction_side(
                relation_kinds[relation_slot],
                role,
            )
            expected_direction_ref = (
                _source_grounded_direction_ref(
                    expression.relation_refs[relation_slot],
                    argument.semantic_ref,
                    role,
                    direction_side,
                )
                if direction_side is not None
                else None
            )
            if (
                expected_role_pair is None
                or role not in expected_role_pair
                or argument.direction_ref != expected_direction_ref
                or argument.case_marker
                != source_grounded_case_marker_for_role(
                    role,
                    relation_kinds[relation_slot],
                )
            ):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            endpoint_arguments_by_relation[relation_slot].append(argument)
        elif (
            argument.relation_endpoint_ref is not None
            or argument.direction_ref is not None
            or argument.case_marker
            != source_grounded_case_marker_for_role(role)
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
    for relation_slot, relation_kind in enumerate(relation_kinds):
        expected_role_pair = _SOURCE_GROUNDED_RELATION_ROLE_PAIR.get(
            relation_kind
        )
        endpoints = tuple(endpoint_arguments_by_relation[relation_slot])
        if (
            expected_role_pair is None
            or len(endpoints) != 2
            or {row.semantic_role for row in endpoints}
            != set(expected_role_pair)
            or len({row.semantic_ref for row in endpoints}) != 2
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
    if expression.source_evidence_refs != _dedupe(
        evidence_ref
        for argument in expression.arguments
        for evidence_ref in argument.source_evidence_refs
    ) or not {
        expression.meaning_outcome_ref,
        expression.reception_binding_ref,
    }.issubset(expression.provenance_refs):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    _validate_expression_morphology(expression)
    for argument in expression.arguments:
        if "shared-subject:current-user" in (
            argument.zero_realization_condition_refs
        ) and (
                argument.semantic_role != "EXPERIENCER"
                or argument.semantic_ref not in expression.experiencer_refs
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
    if expression.reference_mode not in {
        "EXPLICIT",
        "COMPOSITE",
        "ANAPHORIC",
    }:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
        )
    if expression.reference_mode == "ANAPHORIC":
        if (
            expression.antecedent_refs != argument_semantic_refs
            or expression.antecedent_condition
            != "PRIOR_LAYER1_EXACT_SEMANTIC_COVER"
            or not set(expression.antecedent_refs).issubset(
                argument_semantic_ref_set
            )
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
            )
    elif expression.antecedent_refs or expression.antecedent_condition is not None:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
        )
    elif (
        expression.reference_mode == "COMPOSITE"
        and len(argument_semantic_ref_set) < 2
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
        )


def validate_source_grounded_reception_expressions(
    reception_plan: GroundedHumanReceptionPlan,
    expressions: Sequence[SourceGroundedRealizableReceptionExpressionV1],
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[
    tuple[GroundedReceptionMovePlan, SourceGroundedRealizableReceptionExpressionV1],
    ...,
]:
    """Return the exact active Move/expression cover in canonical Move order."""

    if (
        type(reception_plan) is not GroundedHumanReceptionPlan
        or type(recovery_stage) is not str
        or recovery_stage not in _RECOVERY_STAGES
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    try:
        rows = tuple(expressions)
    except (TypeError, ValueError):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        ) from None
    try:
        active_moves = reception_active_moves(reception_plan, recovery_stage)
    except GroundedHumanReceptionSurfaceError:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        ) from None
    if any(
        type(row) is not SourceGroundedRealizableReceptionExpressionV1
        for row in rows
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    for row in rows:
        validate_source_grounded_reception_expression(row)
    move_ids = tuple(row.move_id for row in rows)
    expected_ids = tuple(move.move_id for move in active_moves)
    if (
        len(move_ids) != len(set(move_ids))
        or set(move_ids) != set(expected_ids)
        or len({row.expression_ref for row in rows}) != len(rows)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    expression_by_move = {row.move_id: row for row in rows}
    pairs = tuple(
        (move, expression_by_move[move.move_id]) for move in active_moves
    )
    for move, expression in pairs:
        recovery_rows = tuple(
            row
            for row in expression.inflection_plan
            if row.startswith("reception-form:")
        )
        if (
            recovery_rows != (f"reception-form:{recovery_stage}",)
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
            )
        effective_reference = reception_effective_move_reference_mode(
            reception_plan,
            move,
            recovery_stage,
        )
        expected_reference: ReceptionExpressionReferenceMode
        if effective_reference == "anaphoric_first":
            expected_reference = "ANAPHORIC"
        elif effective_reference == "explicit_emlis_counterposition":
            expected_reference = "EXPLICIT"
        elif effective_reference == "short_anchor_if_ambiguous":
            expected_reference = (
                "COMPOSITE"
                if len(
                    {
                        argument.semantic_ref
                        for argument in expression.arguments
                    }
                )
                > 1
                else "EXPLICIT"
            )
        else:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
            )
        if expression.reference_mode != expected_reference:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
            )
    return pairs


def reception_terminal_predicate_kind(act: GroundedReceptionAct) -> str:
    """Return the human-response terminal family owned by an act."""

    try:
        return _TERMINAL_PREDICATE_BY_ACT[act]
    except KeyError as exc:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_act:{act}"
        ) from exc


def reception_move_predicate_family(move: GroundedReceptionMovePlan) -> str:
    """Return the deterministic RR5 family for one role/act contribution."""

    try:
        return _MOVE_PREDICATE_FAMILY_BY_ROLE_ACT[
            (move.move_role, move.reception_act)
        ]
    except KeyError as exc:
        raise GroundedHumanReceptionSurfaceError(
            "unsupported_reception_move_role_act:"
            f"{move.move_role}:{move.reception_act}"
        ) from exc


def reception_active_moves(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionMovePlan, ...]:
    """Return the RR7 Move-preserving sequence for one recovery stage."""

    moves = tuple(reception_plan.moves)
    if not moves:
        raise GroundedHumanReceptionSurfaceError("human_reception_move_missing")
    if recovery_stage not in _RECOVERY_STAGES:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_recovery_stage:{recovery_stage}"
        )
    if any(move.move_role not in _MOVE_ROLE_ORDER for move in moves):
        raise GroundedHumanReceptionSurfaceError(
            "unsupported_reception_move_role"
        )
    for move in moves:
        reception_move_predicate_family(move)
    original_order = {move.move_id: index for index, move in enumerate(moves)}
    ordered = tuple(
        sorted(
            moves,
            key=lambda move: (
                _MOVE_ROLE_ORDER[move.move_role],
                original_order[move.move_id],
            ),
        )
    )
    if recovery_stage == "full":
        return ordered
    if recovery_stage == "minimal_grounded":
        if (
            reception_plan.depth_policy.level != "minimal"
            or reception_plan.depth_policy.safety_mode != "standard"
            or len(ordered) != 1
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_minimal_grounded_not_allowed"
            )
        return ordered

    retained = ordered
    if (
        recovery_stage == "optional_removed"
        and len(moves) == 3
        and not moves[2].required
    ):
        optional_move_id = moves[2].move_id
        retained = tuple(
            move for move in ordered if move.move_id != optional_move_id
        )
    required_ids = {
        move.move_id for move in reception_plan.moves if move.required
    }
    if not required_ids.issubset(move.move_id for move in retained):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_required_move_missing"
        )
    if len(retained) < reception_plan.depth_policy.min_realized_moves:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_move_budget_below_minimum"
        )
    retained_roles = {move.move_role for move in retained}
    retained_acts = {move.reception_act for move in retained}
    if (
        reception_plan.depth_policy.safety_mode == "self_denial_bounded"
        and (
            "felt_response" not in retained_roles
            or (
                any(
                    move.move_role == "bounded_counterposition"
                    for move in moves
                )
                and "bounded_counterposition" not in retained_roles
            )
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_safety_move_missing"
        )
    if (
        reception_plan.depth_policy.safety_mode == "help_seeking_bounded"
        and (
            "hold_help_seeking" not in retained_acts
            or "bounded_counterposition" not in retained_roles
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_safety_move_missing"
        )
    return retained


def build_grounded_reception_clause_plans(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionClausePlan, ...]:
    """Bind active Moves to deterministic one- or two-Move sentence slots."""

    moves = reception_active_moves(reception_plan, recovery_stage)
    quote_available = bool(
        recovery_stage in {"full", "optional_removed"}
        and reception_plan.quote_policy.max_anchor_count > 0
    )
    move_groups: tuple[tuple[GroundedReceptionMovePlan, ...], ...] = tuple(
        (move,) for move in moves
    )
    if (
        recovery_stage == "integrated"
        and len(moves) == 3
        and reception_plan.depth_policy.max_moves_per_sentence >= 2
        and reception_plan.depth_policy.min_sentences <= 2
        and not any(
            move.move_role == "bounded_counterposition"
            for move in moves[:2]
        )
    ):
        move_groups = (moves[:2], moves[2:])

    clauses: list[GroundedReceptionClausePlan] = []
    for sentence_slot, group in enumerate(move_groups, start=1):
        opening_move = group[0]
        terminal_move = group[-1]
        quote_budget = int(
            quote_available
            and any(
                move.reference_mode == "short_anchor_if_ambiguous"
                for move in group
            )
        )
        if quote_budget:
            quote_available = False
        clauses.append(
            GroundedReceptionClausePlan(
                sentence_slot=sentence_slot,
                move_ids=tuple(move.move_id for move in group),
                opening_strategy=opening_move.surface_strategy,
                connector_policy=(
                    "contrast_safe"
                    if terminal_move.move_role == "bounded_counterposition"
                    else "none"
                ),
                terminal_predicate_family=reception_move_predicate_family(
                    terminal_move
                ),
                quote_budget=quote_budget,
                speaker_presence=terminal_move.speaker_presence,
            )
        )
    return tuple(clauses)


def reception_effective_sentence_budget(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[int, int]:
    """Return the RR7 sentence budget without weakening original depth."""

    if recovery_stage == "full":
        return (
            reception_plan.depth_policy.min_sentences,
            reception_plan.depth_policy.max_sentences,
        )
    clause_count = len(
        build_grounded_reception_clause_plans(
            reception_plan,
            recovery_stage,
        )
    )
    if reception_plan.depth_policy.level == "layered" and clause_count < 2:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_layered_recovery_collapsed"
        )
    safety_requires_two_sentences = bool(
        reception_plan.depth_policy.safety_mode == "help_seeking_bounded"
        or (
            reception_plan.depth_policy.safety_mode == "self_denial_bounded"
            and any(
                move.move_role == "bounded_counterposition"
                for move in reception_plan.moves
            )
        )
    )
    if safety_requires_two_sentences and clause_count < 2:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_safety_recovery_collapsed"
        )
    return clause_count, clause_count


def reception_active_acts(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionAct, ...]:
    """Return the acts retained by one reception-only recovery stage."""

    return tuple(
        move.reception_act
        for move in reception_active_moves(reception_plan, recovery_stage)
    )


def reception_effective_speaker_presence(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Keep explicit Emlis presence only while a bounded act is active."""

    return (
        "explicit_emlis"
        if "bounded_counter_self_denial"
        in reception_active_acts(reception_plan, recovery_stage)
        else "implicit_emlis"
    )


def reception_effective_reference_mode(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Return a recovery-safe reference mode for the retained acts."""

    if (
        "bounded_counter_self_denial"
        in reception_active_acts(reception_plan, recovery_stage)
    ):
        return "explicit_emlis_counterposition"
    if recovery_stage in {"integrated", "hedged", "minimal_grounded"}:
        return "anaphoric_first"
    if reception_plan.reference_mode == "explicit_emlis_counterposition":
        return "anaphoric_first"
    return reception_plan.reference_mode or "anaphoric_first"


def reception_effective_move_reference_mode(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Return the one recovery-aware reference contract for a retained Move."""

    if move.reception_act == "bounded_counter_self_denial":
        return "explicit_emlis_counterposition"
    if recovery_stage in {"integrated", "hedged", "minimal_grounded"}:
        return "anaphoric_first"
    return move.reference_mode or "anaphoric_first"


def reception_action_is_future_intention(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Classify only affirmative, not-yet-performed typed future actions."""

    frame = nucleus.semantic_frame
    attributes = frozenset(frame.attribute_codes)
    if (
        nucleus.kind != "action"
        or frame.polarity == "negative"
        or "operator:negation" in attributes
        or "operator:performed_action" in attributes
        or frame.time_scope in {"past", "past_to_present", "completed"}
        or attributes
        & {
            "time_scope:past",
            "time_scope:past_to_present",
            "aspect:completed",
            "aspect:perfective",
        }
    ):
        return False
    return bool(
        frame.time_scope in {"future", "present_to_future"}
        or frame.modality in {"wish", "intention"}
        or "operator:wish" in attributes
    )


def reception_action_is_performed(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Classify performed action only after future intention is excluded."""

    frame = nucleus.semantic_frame
    attributes = frozenset(frame.attribute_codes)
    return bool(
        nucleus.kind == "action"
        and frame.polarity != "negative"
        and "operator:negation" not in attributes
        and not reception_action_is_future_intention(nucleus)
        and (
            frame.modality == "fact"
            or "operator:performed_action" in attributes
        )
    )


def _source_grounded_semantic_profile(
    nucleus: GroundedSemanticNucleus,
    semantic_fragment: str,
) -> _ReceptionSemanticProfileV1:
    """Project body-free syntax/voice facts before expression replay."""

    actor = str(nucleus.semantic_frame.actor).strip().lower()
    return _ReceptionSemanticProfileV1(
        nucleus_kind=str(nucleus.kind).strip().lower(),
        actor_kind=(
            "SELF"
            if actor in {"current_user", "user", "self"}
            else "OTHER"
            if actor
            not in {"", "none", "unknown", "unspecified", "source_bounded"}
            else "UNSPECIFIED"
        ),
        predicate_kind=str(
            nucleus.semantic_frame.predicate_kind
        ).strip().lower(),
        performed_action=reception_action_is_performed(nucleus),
        future_action=reception_action_is_future_intention(nucleus),
        quoted_boundary=bool(
            re.search(r"[「」『』]", semantic_fragment)
            or re.search(r"(?:まで|だけ|さえ)$", semantic_fragment)
        ),
    )


def _source_grounded_move_voice_profiles(
    move: GroundedReceptionMovePlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> tuple[tuple[_ReceptionSemanticProfileV1, ...], int]:
    """Reproject the plan-owned target/support profiles used by voice."""

    semantic_ids = _dedupe(
        (*move.target_nucleus_ids, *move.support_nucleus_ids)
    )
    if not move.target_nucleus_ids or any(
        nucleus_id not in nucleus_index for nucleus_id in semantic_ids
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    semantic_nuclei = tuple(nucleus_index[nucleus_id] for nucleus_id in semantic_ids)
    profiles = tuple(
        _source_grounded_semantic_profile(
            nucleus,
            _bounded_source_grounded_lexemes(nucleus, resolver)[0],
        )
        for nucleus in semantic_nuclei
    )
    return profiles, len(move.target_nucleus_ids)


def _dedupe(values) -> tuple[str, ...]:
    result: list[str] = []
    for value in values or ():
        item = str(value or "").strip()
        if item and item not in result:
            result.append(item)
    return tuple(result)


def _selected_nuclei(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedSemanticNucleus, ...]:
    nucleus_ids = _dedupe(
        (
            *reception_plan.target_nucleus_ids,
            *(
                ()
                if recovery_stage == "minimal_grounded"
                else reception_plan.support_nucleus_ids
            ),
        )
    )
    if recovery_stage == "minimal_grounded":
        nucleus_ids = nucleus_ids[:1]
    return tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in nucleus_ids
        if nucleus_id in nucleus_index
    )


def _semantic_attributes(
    nuclei: tuple[GroundedSemanticNucleus, ...],
) -> frozenset[str]:
    return frozenset(
        code
        for nucleus in nuclei
        for code in nucleus.semantic_frame.attribute_codes
    )


def _grounding_evidence_span_ids(
    nuclei: tuple[GroundedSemanticNucleus, ...],
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[str, ...]:
    evidence_ids = _dedupe(
        span_id
        for nucleus in nuclei
        for span_id in nucleus.source_span_ids
    )
    return evidence_ids[:1] if recovery_stage == "minimal_grounded" else evidence_ids


def _compact_bound_anchor(candidate: str, max_chars: int) -> str:
    """Return a readable source-bound excerpt without a mid-token cutoff."""

    safe_boundary = re.compile(
        r"[、,.!?！？？をへ]|"
        r"(?<=[㐀-鿿])の(?=[㐀-鿿])|"
        r"(?<=[㐀-鿿])と(?=[㐀-鿿])"
    )
    suffixes = tuple(
        suffix
        for match in safe_boundary.finditer(candidate)
        if (
            2
            <= len(
                suffix := candidate[match.end() :].strip(
                    " 　、,。．."
                )
            )
            <= max_chars
        )
        and not suffix.startswith(("、", ",", "。", "."))
    )
    # Every returned value is one contiguous source substring.  This keeps
    # Japanese quotation marks truthful while still selecting a grammatical
    # suffix instead of cutting a token at the character limit.
    return max(suffixes, key=len, default="")


def _typed_reception_source_fragment(
    nucleus: GroundedSemanticNucleus,
    raw_text: str,
) -> str | None:
    """Resolve the plan-owned source slice used by reception grounding."""

    attributes = tuple(nucleus.semantic_frame.attribute_codes)
    marker_rows = tuple(
        code
        for code in attributes
        if code == "semantic_role:generic_relation_fragment"
    )
    scalar_rows = tuple(
        code
        for code in attributes
        if code.startswith("source_fragment_scalar_range:")
    )
    source_rows = tuple(
        code
        for code in attributes
        if code.startswith("source_fragment_scalar_source:")
    )
    legacy_rows = tuple(
        code
        for code in attributes
        if code.startswith(("surface_scalar_range:", "surface_scalar_source:"))
    )
    if not marker_rows:
        if scalar_rows or source_rows or legacy_rows:
            raise GroundedHumanReceptionSurfaceError(
                "typed_reception_source_fragment_contract_invalid"
            )
        return None
    if (
        len(marker_rows) != 1
        or len(scalar_rows) != 1
        or source_rows
        != ("source_fragment_scalar_source:normalized_raw_text",)
        or legacy_rows
    ):
        raise GroundedHumanReceptionSurfaceError(
            "typed_reception_source_fragment_contract_invalid"
        )
    parts = scalar_rows[0].split(":")
    if len(parts) != 3:
        raise GroundedHumanReceptionSurfaceError(
            "typed_reception_source_fragment_contract_invalid"
        )
    try:
        start, end = int(parts[1]), int(parts[2])
    except ValueError:
        raise GroundedHumanReceptionSurfaceError(
            "typed_reception_source_fragment_contract_invalid"
        ) from None
    normalized_raw = re.sub(
        r"\s+",
        " ",
        str(raw_text or "").replace("\u3000", " "),
    ).strip()
    if not (0 <= start < end <= len(normalized_raw)):
        raise GroundedHumanReceptionSurfaceError(
            "typed_reception_source_fragment_contract_invalid"
        )
    fragment = normalized_raw[start:end]
    if not fragment or fragment != fragment.strip():
        raise GroundedHumanReceptionSurfaceError(
            "typed_reception_source_fragment_contract_invalid"
        )
    return fragment


def _short_bound_anchor(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    allowed_nucleus_ids: tuple[str, ...],
    recovery_stage: ReceptionRecoveryStage,
    *,
    support_action_only: bool = False,
    allow_truncation: bool = True,
    compact_terminal_action: bool = False,
    require_headroom: bool = False,
    effective_reference_mode: str | None = None,
) -> str:
    quote_policy = reception_plan.quote_policy
    if (
        (
            effective_reference_mode
            or reception_effective_reference_mode(
                reception_plan,
                recovery_stage,
            )
        )
        != "short_anchor_if_ambiguous"
        or quote_policy.max_anchor_count < 1
        or quote_policy.max_anchor_visible_chars < 2
    ):
        return ""
    ordered_ids = _dedupe(
        reception_plan.support_nucleus_ids
        if support_action_only
        else (
            *reception_plan.support_nucleus_ids,
            *reception_plan.target_nucleus_ids,
        )
    )
    allowed = set(allowed_nucleus_ids)
    for nucleus_id in ordered_ids:
        if nucleus_id not in allowed or nucleus_id not in nucleus_index:
            continue
        nucleus = nucleus_index[nucleus_id]
        if support_action_only and not {
            "operator:action",
            "semantic_role:concrete_action_evidence",
        } & frozenset(nucleus.semantic_frame.attribute_codes):
            continue
        for span_id in nucleus.source_span_ids:
            if resolver.unresolved_ids((span_id,)):
                continue
            raw_text = re.sub(
                r"\s+",
                " ",
                str(resolver.resolve(span_id).raw_text or "").replace(
                    "\u3000",
                    " ",
                ),
            ).strip()
            candidate = (
                _typed_reception_source_fragment(nucleus, raw_text)
                or raw_text
            )
            candidate = candidate.strip(" \u3000、,。．.")
            candidate = candidate.translate(_ANCHOR_DELETE_TRANSLATION).strip()
            if compact_terminal_action and candidate.endswith("した"):
                candidate = candidate[:-2].rstrip(" \u3000、,")
            if (
                len(candidate) < 2
                or _QUESTION_RE.search(candidate)
                or _POLICY_EXPLANATION_RE.search(candidate)
                or _ADVICE_RE.search(candidate)
                or _UNSUPPORTED_CLAIM_RE.search(candidate)
            ):
                continue
            max_chars = quote_policy.max_anchor_visible_chars
            if require_headroom and len(candidate) >= max_chars:
                continue
            if len(candidate) > max_chars:
                if not allow_truncation:
                    continue
                # A quoted anchor must remain a readable, verbatim source
                # span.  A raw prefix plus an ellipsis can stop mid-word and
                # sound machine-clipped. Prefer the longest source suffix
                # beginning at a punctuation/particle boundary; if none fits,
                # fall back to the semantic anaphor instead of fabricating a
                # clipped quote.
                candidate = _compact_bound_anchor(candidate, max_chars)
                if not candidate:
                    continue
            return candidate
    return ""


def resolve_grounded_reception_referent(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    recovery_stage: ReceptionRecoveryStage = "full",
    act: GroundedReceptionAct | None = None,
    allow_short_anchor: bool = True,
    effective_reference_mode: str | None = None,
) -> GroundedReceptionReferent:
    """Resolve an anaphor or one policy-bounded anchor from bound evidence."""

    reception_act = act or reception_plan.primary_reception_act
    if reception_act is None:
        raise GroundedHumanReceptionSurfaceError("human_reception_act_missing")
    selected = _selected_nuclei(
        reception_plan,
        nucleus_index,
        recovery_stage,
    )
    if not selected:
        raise GroundedHumanReceptionSurfaceError("human_reception_target_missing")
    attributes = _semantic_attributes(selected)
    target_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in reception_plan.target_nucleus_ids
        if nucleus_id in nucleus_index
    )
    target_attributes = _semantic_attributes(target_nuclei)
    support_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in reception_plan.support_nucleus_ids
        if nucleus_id in nucleus_index
    )
    support_attributes = _semantic_attributes(support_nuclei)
    kinds = {nucleus.kind for nucleus in selected}

    if (
        reception_act == "honor_concrete_effort"
        and any(
            reception_action_is_future_intention(nucleus)
            for nucleus in target_nuclei
        )
    ):
        kind, text = "future_action_intention", "その向き"
    elif reception_act == "stay_with_current_burden":
        if "lexical:no_new_sensation_family" in attributes:
            if "lexical:source_metaphor_present" in attributes:
                kind, text = "expressed_burden", "その言葉にある負荷"
            elif "detected_type:limit_signal" in attributes:
                kind, text = "current_suffering", "その苦しさ"
            else:
                kind, text = "current_distress", "そのつらさ"
        elif kinds & {"reaction", "state", "constraint"}:
            kind, text = "current_burden", "今のしんどさ"
        else:
            kind, text = "current_expression", "今ここに置かれた言葉"
    elif reception_act == "honor_concrete_effort":
        selected_ids = tuple(nucleus.nucleus_id for nucleus in selected)
        performed_targets = tuple(
            nucleus
            for nucleus in target_nuclei
            if reception_action_is_performed(nucleus)
        )
        performed_supports = tuple(
            nucleus
            for nucleus in support_nuclei
            if reception_action_is_performed(nucleus)
        )
        enacted_after_intention = bool(
            recovery_stage in {"full", "optional_removed"}
            and "operator:action" not in target_attributes
            and performed_supports
        )
        enacted_action_anchor = (
            _short_bound_anchor(
                reception_plan,
                nucleus_index,
                resolver,
                selected_ids,
                recovery_stage,
                support_action_only=True,
                allow_truncation=False,
                compact_terminal_action=True,
                require_headroom=True,
                effective_reference_mode=effective_reference_mode,
            )
            if enacted_after_intention
            and allow_short_anchor
            and recovery_stage in {"full", "optional_removed"}
            else ""
        )
        anchor = (
            _short_bound_anchor(
                reception_plan,
                nucleus_index,
                resolver,
                selected_ids,
                recovery_stage,
                effective_reference_mode=effective_reference_mode,
            )
            if allow_short_anchor
            and recovery_stage in {"full", "optional_removed"}
            and not enacted_after_intention
            else ""
        )
        if enacted_action_anchor:
            kind, text = (
                "anchored_enacted_effort",
                f"「{enacted_action_anchor}」という実際の行動",
            )
        elif enacted_after_intention and (
            "operator:positive_change" in target_attributes
        ):
            kind, text = (
                "next_step_effort",
                "次へつなぐために、実際に手を動かしたこと",
            )
        elif enacted_after_intention and (
            "detected_type:wish" in target_attributes
        ):
            kind, text = (
                "recorded_effort_toward_intention",
                "確かめたいことを、実際の記録へ移したこと",
            )
        elif enacted_after_intention:
            kind, text = (
                "enacted_effort_after_intention",
                "言葉だけで終わらせず、実際に動いたこと",
            )
        elif anchor:
            kind, text = (
                "anchored_concrete_effort",
                f"「{anchor}」という実際の行動",
            )
        elif performed_targets and any(
            str(nucleus.semantic_frame.actor).lower()
            in {"current_user", "user", "self"}
            for nucleus in performed_targets
        ):
            kind, text = (
                "self_started_effort",
                "自分から起こした実際の行動",
            )
        elif performed_targets:
            kind, text = (
                "concrete_effort",
                "実際に行われた行動",
            )
        else:
            kind, text = "grounded_effort", "その働きかけに伴う手間"
    elif reception_act == "protect_retained_intention":
        if "wish" in kinds or "operator:wish" in attributes:
            kind, text = "retained_wish", "その願い"
        else:
            kind, text = "retained_intention", "大切にしたいもの"
    elif reception_act == "recognize_lived_change":
        if "action" in kinds and (
            "change" in kinds or "operator:change" in attributes
        ):
            kind, text = "lived_change", "自分で確かめてきた変化"
        elif "operator:action" in attributes:
            kind, text = "enacted_change", "動きとして確かめてきた変化"
        else:
            kind, text = "lived_change", "その変化"
    elif reception_act == "hold_help_seeking":
        self_directed_targets = tuple(
            nucleus
            for nucleus in target_nuclei
            if str(nucleus.semantic_frame.actor).lower()
            in {"current_user", "user", "self"}
        )
        if self_directed_targets and any(
            reception_action_is_performed(nucleus)
            for nucleus in self_directed_targets
        ):
            kind, text = "help_seeking", "助けにつながるものを残したこと"
        elif self_directed_targets and (
            "operator:help_seeking" in target_attributes
            or any(
                nucleus.kind
                in {"wish", "direction", "intention", "help_seeking"}
                for nucleus in self_directed_targets
            )
        ):
            kind, text = "help_seeking_step", "助けへ向かう一歩を残したこと"
        else:
            kind, text = "received_help", "受け取った助け"
    elif reception_act == "bounded_counter_self_denial":
        if {
            "semantic_role:protective_or_limiting_refusal",
            "semantic_role:retained_intention",
        } & target_attributes:
            kind, text = (
                "felt_suffering_with_counterdirection",
                "今そこにある苦しさ",
            )
        else:
            kind, text = "felt_suffering", "その苦しさ自体"
    elif reception_act == "respect_words_placed":
        kind, text = "words_placed", "ここに言葉を置いたこと"
    else:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_act:{reception_act}"
        )

    progressive_owners = tuple(n for n in target_nuclei if reception_action_is_performed(n))
    if reception_act == "honor_concrete_effort" and progressive_owners:
        progressive_targets = tuple(
            nucleus for nucleus in progressive_owners
            if set(nucleus.semantic_frame.attribute_codes) & {"aspect:progressive", "aspect:ongoing"}
        )
        if progressive_targets and len(progressive_targets) == len(progressive_owners):
            text = (
                "そのとき取り組んでいた行動"
                if all(nucleus.semantic_frame.time_scope == "past" for nucleus in progressive_targets)
                else "今取り組んでいる行動"
            )

    evidence_span_ids = _grounding_evidence_span_ids(selected, recovery_stage)
    return GroundedReceptionReferent(
        kind=kind,
        text=text,
        nucleus_ids=tuple(nucleus.nucleus_id for nucleus in selected),
        evidence_span_ids=evidence_span_ids,
        source_anchor_used=bool(_QUOTE_RE.search(text)),
    )


def _scoped_reception_plan_for_move(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    recovery_stage: ReceptionRecoveryStage,
) -> GroundedHumanReceptionPlan:
    """Create an ephemeral compatibility view for one Move's grounding."""

    return replace(
        reception_plan,
        moves=(move,),
        primary_reception_act=move.reception_act,
        secondary_reception_act=None,
        target_nucleus_ids=move.target_nucleus_ids,
        support_nucleus_ids=move.support_nucleus_ids,
        source_evidence_span_ids=move.source_evidence_span_ids,
        stance=_STANCE_BY_ACT[move.reception_act],
        speaker_presence=move.speaker_presence,
        reference_mode=reception_effective_move_reference_mode(
            reception_plan,
            move,
            recovery_stage,
        ),
    )


def _short_anaphoric_topic(fragment: str) -> str:
    """Recover only a short grammatical topic, never the target clause."""

    compact = re.sub(r"\s+", "", fragment).strip(
        " 　、,。．.!！?？「」『』"
    )
    if (
        not compact
        or len(compact) > _ANAPHORIC_TOPIC_SOURCE_MAX_CHARS
        or _QUESTION_RE.search(fragment)
        or _POLICY_EXPLANATION_RE.search(fragment)
        or _ADVICE_RE.search(fragment)
        or _UNSUPPORTED_CLAIM_RE.search(fragment)
    ):
        return ""
    for pattern in (
        _ANAPHORIC_TOPIC_OBJECT_RE,
        _ANAPHORIC_TOPIC_SAHEN_RE,
    ):
        match = pattern.search(compact)
        if match is None:
            continue
        topic = match.group("topic").strip()
        if (
            not 1 <= len(topic) <= 18
            or _QUESTION_RE.search(topic)
            or _POLICY_EXPLANATION_RE.search(topic)
            or _ADVICE_RE.search(topic)
            or _UNSUPPORTED_CLAIM_RE.search(topic)
        ):
            continue
        return topic
    return ""


def _topic_bound_anaphoric_referent(
    referent: GroundedReceptionReferent,
    move: GroundedReceptionMovePlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> GroundedReceptionReferent:
    """Bind an anaphor to a short target topic without replaying its clause."""

    if move.reception_act != "protect_retained_intention":
        return referent
    for _nucleus_id, fragments in _reception_source_fragments(
        move.target_nucleus_ids,
        nucleus_index,
        resolver,
    ):
        for fragment in fragments:
            topic = _short_anaphoric_topic(fragment)
            candidate = f"{topic}についてのその願い" if topic else ""
            if candidate and fragment not in candidate:
                return replace(referent, text=candidate)
    return referent


def resolve_grounded_reception_move_referent(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    allow_short_anchor: bool,
    recovery_stage: ReceptionRecoveryStage = "full",
    allow_anaphoric_topic: bool = False,
) -> GroundedReceptionReferent:
    """Resolve one RR5 referent using only that Move's nucleus/evidence IDs."""

    effective_reference = reception_effective_move_reference_mode(
        reception_plan,
        move,
        recovery_stage,
    )
    referent = resolve_grounded_reception_referent(
        _scoped_reception_plan_for_move(
            reception_plan,
            move,
            recovery_stage,
        ),
        nucleus_index,
        resolver,
        recovery_stage=recovery_stage,
        act=move.reception_act,
        # Layer 2 integrates a bounded lexical head into its clause core.  A
        # second verbatim short anchor would both replay Layer 1 and make the
        # inverse referent depend on the caller's quote budget.
        allow_short_anchor=False,
        effective_reference_mode=effective_reference,
    )
    if allow_anaphoric_topic and effective_reference == "anaphoric_first":
        return _topic_bound_anaphoric_referent(
            referent,
            move,
            nucleus_index,
            resolver,
        )
    if effective_reference != "anaphoric_first":
        # A demonstrative belongs to anaphora.  Explicit/composite clause
        # heads govern a non-deictic typed nominal from the same sole resolver.
        return replace(
            referent,
            text=re.sub(r"^その", "", referent.text),
        )
    return referent


def _predicate_fragment(
    act: GroundedReceptionAct,
    recovery_stage: ReceptionRecoveryStage,
    *,
    referent_kind: str = "",
) -> GroundedHumanResponsePredicate:
    compact = recovery_stage in {"integrated", "minimal_grounded"}
    hedged = recovery_stage == "hedged"

    if act == "stay_with_current_burden":
        fragment = (
            "軽く扱わずに受け止めたいです"
            if hedged
            else "軽く扱わずに受け止めます"
            if compact
            else "軽く扱わず、ここで受け止めています"
            if referent_kind == "current_suffering"
            else "無理に小さくせず、受け止めています"
            if referent_kind == "current_burden"
            else "軽く扱わず、今ここにあるものとして受け止めています"
        )
    elif act == "honor_concrete_effort":
        fragment = (
            "これからの行動として大切に受け止めています"
            if referent_kind == "future_action_intention"
            else "大切なこととして受け止めたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "その手間ごと大切に受け止めています"
            if referent_kind
            in {
                "enacted_effort_after_intention",
                "anchored_enacted_effort",
                "next_step_effort",
                "recorded_effort_toward_intention",
            }
            else "簡単なこととして流さず、大切に受け止めています"
        )
    elif act == "protect_retained_intention":
        fragment = (
            "消さずに大切にしたいです"
            if hedged
            else "大切なものとして、なかったことにしません"
            if compact
            else "なかったことにせず、大切にしています"
        )
    elif act == "recognize_lived_change":
        fragment = (
            "大切な変化として感じたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "うれしく感じています"
        )
    elif act == "hold_help_seeking":
        fragment = (
            "大切な踏みとどまりとして受け止めたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "見過ごさず、大切な踏みとどまりとして受け止めています"
        )
    elif act == "respect_words_placed":
        fragment = (
            "大切に受け止めたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "そのまま静かに、大切に受け止めています"
        )
    elif act == "bounded_counter_self_denial":
        fragment = (
            "否定せず、大切に受け止めたいです"
            if hedged
            else "否定せず、大切に受け止めます"
            if compact
            else "否定せず、大切に受け止めています"
        )
    else:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_act:{act}"
        )
    return GroundedHumanResponsePredicate(
        terminal_predicate_kind=reception_terminal_predicate_kind(act),
        object_particle="を",
        predicate_fragment=fragment,
    )


def _stance_adverb(
    stance: str | None,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    if recovery_stage != "full":
        return ""
    return {
        "quiet_presence": "静かに",
        "warm_recognition": "",
        "gentle_respect": "そっと",
        "protective_presence": "大切に",
        "bounded_disagreement": "",
    }.get(stance or "", "")


def _join_object_predicate(
    referent: GroundedReceptionReferent,
    predicate: GroundedHumanResponsePredicate,
    *,
    stance_adverb: str,
    safety_prefix: str = "",
) -> str:
    predicate_text = predicate.predicate_fragment
    if stance_adverb == "あたたかく" and "うれしく感じ" in predicate_text:
        pass
    elif stance_adverb == "あたたかく" and "大切に受け止め" in predicate_text:
        predicate_text = predicate_text.replace(
            "大切に受け止め",
            "あたたかく、大切に受け止め",
            1,
        )
    elif stance_adverb == "そっと" and "そのまま静かに" in predicate_text:
        pass
    elif stance_adverb == "大切に":
        pass
    elif stance_adverb:
        for terminal in (
            "受け止めています",
            "受け止めたいです",
            "受け止めます",
            "大切にしています",
        ):
            if terminal in predicate_text:
                predicate_text = predicate_text.replace(
                    terminal,
                    f"{stance_adverb}{terminal}",
                    1,
                )
                break
    prefix = f"{safety_prefix}、" if safety_prefix else ""
    return (
        f"{prefix}{referent.text}{predicate.object_particle}、"
        f"{predicate_text}"
    )


def _bounded_counterposition_fragment(
    *,
    preserved_action: bool = False,
    preserved_help_step: bool = False,
    preserved_counterdirection: bool = False,
) -> str:
    if preserved_help_step and preserved_action:
        return (
            "Emlisには、助けへ向けて残したその行動までなかったことにして、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    if preserved_help_step:
        return (
            "Emlisには、助けへ向かうその一歩までなかったことにして、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    if preserved_action:
        return (
            "Emlisには、残したその行動までなかったことにして、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    if preserved_counterdirection:
        return (
            "Emlisには、その自己評価だけでは終わらない別の思いも見失わずに、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    return "Emlisには、その言葉だけであなた自身が決まるとは思えません"


def _move_attributes(
    move: GroundedReceptionMovePlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> frozenset[str]:
    return frozenset(
        code
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
        if nucleus_id in nucleus_index
        for code in nucleus_index[nucleus_id].semantic_frame.attribute_codes
    )


def _realize_full_move_sentence(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    referent: GroundedReceptionReferent,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> str:
    """Realize one deterministic role/act contribution, never a case template."""

    role = move.move_role
    act = move.reception_act
    text = referent.text
    strategy = move.surface_strategy
    if _MOVE_ROLE_BY_SURFACE_STRATEGY.get(strategy) != role:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_move_surface_strategy_mismatch:"
            f"{role}:{strategy}"
        )

    if strategy == "explicit_emlis_counterposition":
        attributes = _move_attributes(move, nucleus_index)
        return _bounded_counterposition_fragment(
            preserved_help_step="operator:help_seeking" in attributes,
            preserved_action="operator:action" in attributes,
            preserved_counterdirection=bool(
                {
                    "operator:continuation",
                    "operator:refusal",
                    "semantic_role:protective_or_limiting_refusal",
                }
                & attributes
            ),
        )

    if act == "honor_concrete_effort" and referent.kind == (
        "future_action_intention"
    ):
        if strategy == "emlis_attention_first":
            return (
                f"{text}が特に印象に残り、"
                "これからの行動として大切に思います"
            )
        if strategy == "referent_significance_first":
            return (
                f"{text}を、これからの行動として"
                "軽く扱わず大切に思います"
            )
        if strategy in {"quiet_referent_first", "felt_response_first"}:
            return f"{text}を、これからの行動として大切に思います"

    if strategy == "emlis_attention_first":
        if act == "honor_concrete_effort":
            return (
                f"{text}が特に印象に残り、"
                "その手間を大切に思います"
            )
        if act == "recognize_lived_change":
            return f"{text}が特に印象に残り、見過ごしたくないと感じます"
        if act == "protect_retained_intention":
            attributes = _move_attributes(move, nucleus_index)
            target_rank = next(
                (
                    index
                    for index, nucleus_id in enumerate(
                        reception_plan.observation_owned_nucleus_ids
                    )
                    if nucleus_id in move.target_nucleus_ids
                ),
                0,
            )
            if "operator:positive_change" in attributes:
                return (
                    "変化の中にも残っているその願いが、"
                    "なかったことにしたくないほど印象に残りました"
                )
            if target_rank >= 3:
                return (
                    f"{text}を、なかったことにせず、"
                    "見過ごさずにいたいです"
                )
            return f"{text}が、なかったことにしたくないほど印象に残りました"
        if act == "hold_help_seeking":
            return f"{text}が、見過ごしたくないものとして印象に残りました"
        if act == "stay_with_current_burden":
            return f"{text}を、見過ごしたくありません"
        return f"{text}が、静かに印象に残りました"

    if strategy == "referent_significance_first":
        if act == "honor_concrete_effort":
            return f"{text}を、軽いこととして流さず大切に思います"
        if act == "protect_retained_intention":
            return f"{text}を、消さずにそっと残しておきたいです"
        if act == "recognize_lived_change":
            return f"{text}を、軽い変化として扱いたくありません"
        if act == "hold_help_seeking":
            return f"{text}を、大切な一歩として残しておきたいです"
        return f"{text}を、軽く扱いたくありません"

    if strategy not in {"quiet_referent_first", "felt_response_first"}:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_surface_strategy:{strategy}"
        )

    if act == "stay_with_current_burden":
        if reception_plan.depth_policy.safety_mode == "self_denial_bounded":
            attributes = _move_attributes(move, nucleus_index)
            if "detected_type:value" in attributes:
                return (
                    "その自己評価にある苦しさを、否定せず、"
                    "軽く扱わず受け止めています"
                )
            return (
                "今そこにある苦しさを、否定せず、"
                "無理に小さくせず受け止めています"
            )
        return _join_object_predicate(
            referent,
            _predicate_fragment(
                act,
                "full",
                referent_kind=referent.kind,
            ),
            stance_adverb=_stance_adverb("quiet_presence", "full"),
        )
    if act == "recognize_lived_change":
        attributes = _move_attributes(move, nucleus_index)
        explicitly_valued = bool(
            {
                "semantic_role:explicit_evaluation",
                "semantic_role:positive_evaluation",
                "operator:value",
            }
            & attributes
        )
        if explicitly_valued:
            if "semantic_role:embedded_turn" in attributes:
                return f"{text}を、うれしい変化だと感じます"
            if "operator:contrast" in attributes:
                return f"{text}に、静かなうれしさを感じます"
            return f"{text}を、うれしく感じます"
        if "semantic_role:embedded_turn" in attributes:
            return f"{text}を、軽く扱わずにいたいです"
        if "operator:contrast" in attributes:
            return f"{text}を、見過ごしたくありません"
        if "semantic_role:explicit_result" in attributes:
            if "semantic_role:contrast_before" in attributes:
                return f"{text}を、見過ごさずにいたいです"
            return f"{text}を、軽いこととして流したくありません"
        return f"{text}を、見過ごさずにいたいです"
    if act == "protect_retained_intention":
        return f"{text}を、そっと大切にしたいです"
    if act == "honor_concrete_effort":
        return f"{text}を、その手間ごと大切に思います"
    if act == "hold_help_seeking":
        prefix = (
            "今ある苦しさを否定せず、"
            if reception_plan.depth_policy.safety_mode == "help_seeking_bounded"
            else ""
        )
        return f"{prefix}{text}を、大切な一歩として見過ごしたくありません"
    if act == "respect_words_placed":
        return f"{text}を、そのまま静かに大切に受け止めています"
    raise GroundedHumanReceptionSurfaceError(
        f"unsupported_reception_move_act:{act}"
    )


def _hedge_move_sentence(text: str) -> str:
    """Weaken assertion while retaining the Move's visible responsibility."""

    replacements = (
        ("見過ごしたくありません", "見過ごさずにいたいです"),
        ("見過ごしたくないと感じます", "見過ごさずにいたいと感じています"),
        ("扱いたくありません", "扱わずにいたいです"),
        (
            "その手間ごと大切に思います",
            "その手間ごと軽く扱わずにいたいです",
        ),
        (
            "その手間を大切に思います",
            "その手間を軽いこととして流さずにいたいです",
        ),
        (
            "うれしい変化だと感じます",
            "うれしい変化として受け止めたいです",
        ),
        ("受け止めています", "受け止めたいです"),
        ("受け止めます", "受け止めたいです"),
        ("印象に残りました", "印象に残っています"),
        ("うれしく感じます", "うれしく感じています"),
        ("うれしさを感じます", "うれしさを感じています"),
    )
    for source, replacement in replacements:
        if source in text:
            return text.replace(source, replacement, 1)
    return text


def _realize_move_sentence(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    referent: GroundedReceptionReferent,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Realize every recovery stage from the same Move-owned surface path."""

    text = _realize_full_move_sentence(
        reception_plan,
        move,
        referent,
        nucleus_index,
    )
    return (
        _hedge_move_sentence(text)
        if recovery_stage == "hedged"
        and move.move_role != "bounded_counterposition"
        else text
    )


def _integrate_move_sentences(first: str, second: str) -> str:
    """Join two complete Move contributions without deleting either one."""

    lead_endings = (
        ("見過ごしたくないと感じます", "見過ごしたくないと感じ"),
        (
            "なかったことにしたくないほど印象に残りました",
            "なかったことにしたくないほど印象に残り",
        ),
        ("印象に残りました", "印象に残り"),
        ("見過ごしたくありません", "見過ごさず"),
        ("見過ごさずにいたいです", "見過ごさずにいたいと感じ"),
        ("残しておきたいです", "残しておきたく"),
        ("大切にしたいです", "大切にしたく"),
        ("扱いたくありません", "扱わずにいたく"),
        ("大切に思います", "大切に思い"),
        ("受け止めています", "受け止めており"),
        ("受け止めます", "受け止め"),
        ("感じます", "感じ"),
    )
    clean_first = first.rstrip("。")
    clean_second = second.rstrip("。")
    for ending, lead in lead_endings:
        if clean_first.endswith(ending):
            return f"{clean_first[:-len(ending)]}{lead}、{clean_second}"
    raise GroundedHumanReceptionSurfaceError(
        "human_reception_integrated_lead_unsupported"
    )


def _validate_clause_plan_binding(
    reception_plan: GroundedHumanReceptionPlan,
    clauses: Sequence[GroundedReceptionClausePlan],
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionMovePlan, ...]:
    active_moves = reception_active_moves(reception_plan, recovery_stage)
    move_index = {move.move_id: move for move in active_moves}
    canonical_clauses = build_grounded_reception_clause_plans(
        reception_plan,
        recovery_stage,
    )
    if len(clauses) != len(canonical_clauses):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_count_mismatch"
        )
    if tuple(clause.sentence_slot for clause in clauses) != tuple(
        range(1, len(clauses) + 1)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_slot_invalid"
        )
    flattened_ids = tuple(
        move_id for clause in clauses for move_id in clause.move_ids
    )
    expected_ids = tuple(move.move_id for move in active_moves)
    if len(flattened_ids) != len(set(flattened_ids)):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_move_duplicate"
        )
    if flattened_ids != expected_ids:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_move_binding_mismatch"
        )
    if sum(clause.quote_budget for clause in clauses) > (
        reception_plan.quote_policy.max_anchor_count
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_quote_budget_exceeded"
        )
    for clause, canonical_clause in zip(clauses, canonical_clauses):
        if not 1 <= len(clause.move_ids) <= min(
            2,
            reception_plan.depth_policy.max_moves_per_sentence,
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_move_limit_invalid"
            )
        moves = tuple(move_index[move_id] for move_id in clause.move_ids)
        if any(
            move.move_role == "bounded_counterposition" for move in moves
        ) and len(moves) != 1:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_counterposition_clause_not_independent"
            )
        if len(moves) == 2 and recovery_stage != "integrated":
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_multi_move_clause_wrong_stage"
            )
        if len(moves) == 2 and len(clauses) < (
            reception_plan.depth_policy.min_sentences
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_integrated_depth_below_minimum"
            )
        opening_move = moves[0]
        terminal_move = moves[-1]
        if clause.terminal_predicate_family != reception_move_predicate_family(
            terminal_move
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_predicate_family_mismatch"
            )
        if clause.opening_strategy != opening_move.surface_strategy:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_opening_strategy_mismatch"
            )
        if clause.speaker_presence != terminal_move.speaker_presence:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_speaker_mismatch"
            )
        expected_connector = (
            "contrast_safe"
            if terminal_move.move_role == "bounded_counterposition"
            else "none"
        )
        if clause.connector_policy != expected_connector:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_connector_policy_mismatch"
            )
        if clause.quote_budget not in {0, 1}:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_quote_budget_invalid"
            )
        if clause.quote_budget != canonical_clause.quote_budget:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_quote_budget_mismatch"
            )
    return active_moves


def _afterglow_clause(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> str | None:
    if (
        recovery_stage != "full"
        or reception_plan.afterglow_follow_element != "intent_affirmation"
        or reception_plan.secondary_reception_act is not None
        or reception_plan.sentence_policy.max_sentences < 2
    ):
        return None
    return "そこにある意志も、大切に受け止めています"


def _compose_reception_clauses(
    reception_plan: GroundedHumanReceptionPlan,
    primary_referent: GroundedReceptionReferent,
    secondary_referent: GroundedReceptionReferent | None,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    active_acts = reception_active_acts(reception_plan, recovery_stage)
    primary_act = active_acts[0]
    primary_predicate = _predicate_fragment(
        primary_act,
        recovery_stage,
        referent_kind=primary_referent.kind,
    )
    bounded_primary = primary_act == "bounded_counter_self_denial"
    secondary_act = active_acts[1] if len(active_acts) > 1 else None
    bounded_secondary = secondary_act == "bounded_counter_self_denial"
    stance = _stance_adverb(reception_plan.stance, recovery_stage)

    if bounded_primary:
        felt_clause = _join_object_predicate(
            primary_referent,
            primary_predicate,
            stance_adverb=stance,
        )
        if recovery_stage == "full":
            clauses = (
                felt_clause,
                _bounded_counterposition_fragment(
                    preserved_counterdirection=(
                        primary_referent.kind
                        == "felt_suffering_with_counterdirection"
                    )
                ),
            )
        else:
            clauses = (
                f"{felt_clause}が、{_bounded_counterposition_fragment()}",
            )
        terminal_kinds = (primary_predicate.terminal_predicate_kind,)
    else:
        safety_prefix = (
            "今ある苦しさを否定せず"
            if bounded_secondary
            else ""
        )
        primary_clause = _join_object_predicate(
            primary_referent,
            primary_predicate,
            stance_adverb=stance,
            safety_prefix=safety_prefix,
        )
        if secondary_act is not None:
            if bounded_secondary:
                secondary_clause = _bounded_counterposition_fragment(
                    preserved_action=(
                        primary_act == "hold_help_seeking"
                        and primary_referent.kind == "help_seeking"
                    ),
                    preserved_help_step=(
                        primary_act == "hold_help_seeking"
                        and primary_referent.kind == "help_seeking_step"
                    ),
                )
            else:
                if secondary_referent is None:
                    raise GroundedHumanReceptionSurfaceError(
                        "human_reception_secondary_referent_missing"
                    )
                secondary_predicate = _predicate_fragment(
                    secondary_act,
                    recovery_stage,
                    referent_kind=secondary_referent.kind,
                )
                secondary_clause = _join_object_predicate(
                    secondary_referent,
                    secondary_predicate,
                    stance_adverb=_stance_adverb(
                        _STANCE_BY_ACT[secondary_act],
                        recovery_stage,
                    ),
                )
            clauses = (primary_clause, secondary_clause)
            terminal_kinds = tuple(
                reception_terminal_predicate_kind(act)
                for act in active_acts
            )
        else:
            clauses = (primary_clause,)
            terminal_kinds = (primary_predicate.terminal_predicate_kind,)

    afterglow = _afterglow_clause(reception_plan, recovery_stage)
    if afterglow is not None and len(clauses) < reception_plan.sentence_policy.max_sentences:
        clauses = (*clauses, afterglow)
    return clauses, terminal_kinds


def _sentence_count(text: str) -> int:
    return len(
        tuple(
            part.strip()
            for part in _SENTENCE_END_RE.split(text)
            if part.strip()
        )
    )


def validate_grounded_human_reception_surface(
    surface: GroundedHumanReceptionSurface,
    reception_plan: GroundedHumanReceptionPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Validate the R4 surface without reconstructing observation meaning."""

    issues: list[str] = []
    if not surface.text.strip():
        issues.append("human_reception_surface_empty")
    actual_sentence_count = _sentence_count(surface.text)
    if surface.sentence_count != actual_sentence_count:
        issues.append("human_reception_sentence_diagnostic_mismatch")
    try:
        min_sentences, max_sentences = reception_effective_sentence_budget(
            reception_plan,
            surface.recovery_stage,
        )
    except GroundedHumanReceptionSurfaceError as exc:
        issues.append(str(exc))
        min_sentences, max_sentences = (1, 0)
    if not (
        min_sentences <= actual_sentence_count <= max_sentences
    ):
        issues.append("human_reception_sentence_budget_exceeded")
    if _QUESTION_RE.search(surface.text):
        issues.append("human_reception_question_forbidden")
    if _POLICY_EXPLANATION_RE.search(surface.text):
        issues.append("human_reception_policy_explanation_forbidden")
    if _ADVICE_RE.search(surface.text):
        issues.append("human_reception_advice_forbidden")
    if _UNSUPPORTED_CLAIM_RE.search(surface.text):
        issues.append("human_reception_unsupported_claim_forbidden")

    quote_values = tuple(_QUOTE_RE.findall(surface.text))
    quote_policy = reception_plan.quote_policy
    if len(quote_values) > quote_policy.max_anchor_count:
        issues.append("human_reception_quote_anchor_count_exceeded")
    if any(len(value) > quote_policy.max_anchor_visible_chars for value in quote_values):
        issues.append("human_reception_quote_anchor_length_exceeded")
    if surface.source_anchor_count != len(quote_values):
        issues.append("human_reception_quote_diagnostic_mismatch")
    max_visible = max((len(value) for value in quote_values), default=0)
    if surface.source_anchor_max_visible_chars != max_visible:
        issues.append("human_reception_quote_length_diagnostic_mismatch")

    if surface.recovery_stage not in _RECOVERY_STAGES:
        issues.append("unsupported_reception_recovery_stage")
        active_acts: tuple[GroundedReceptionAct, ...] = ()
        active_moves: tuple[GroundedReceptionMovePlan, ...] = ()
    else:
        active_moves = reception_active_moves(
            reception_plan,
            surface.recovery_stage,
        )
        active_acts = reception_active_acts(
            reception_plan,
            surface.recovery_stage,
        )
    if surface.realized_reception_acts != active_acts:
        issues.append("human_reception_realized_act_mismatch")
    expected_kinds = tuple(
        reception_terminal_predicate_kind(act) for act in active_acts
    )
    if surface.terminal_predicate_kinds != expected_kinds:
        issues.append("human_reception_terminal_predicate_mismatch")
    expected_move_ids = tuple(move.move_id for move in active_moves)
    expected_move_roles = tuple(move.move_role for move in active_moves)
    expected_move_families = tuple(
        reception_move_predicate_family(move) for move in active_moves
    )
    if surface.realized_move_ids != expected_move_ids:
        issues.append("human_reception_realized_move_mismatch")
    if surface.realized_move_roles != expected_move_roles:
        issues.append("human_reception_realized_move_role_mismatch")
    if surface.move_predicate_families != expected_move_families:
        issues.append("human_reception_move_predicate_family_mismatch")
    flattened_clause_moves = tuple(
        move_id
        for move_ids in surface.realized_clause_move_ids
        for move_id in move_ids
    )
    if flattened_clause_moves != expected_move_ids:
        issues.append("human_reception_realized_clause_move_mismatch")
    if any(
        not kind.startswith("human_response_")
        for kind in (
            *surface.terminal_predicate_kinds,
            *surface.move_predicate_families,
        )
    ):
        issues.append("human_reception_non_human_terminal_predicate")
    for act in active_acts:
        responsibility = _ACT_OWNED_RESPONSIBILITY_RE[act]
        if not responsibility.search(surface.text):
            issues.append(f"human_reception_act_responsibility_missing:{act}")
    if active_acts and all(
        not _ACT_OWNED_RESPONSIBILITY_RE[act].search(surface.text)
        for act in active_acts
    ):
        issues.append("human_reception_generic_suffix_forbidden")

    bounded_counterposition = "bounded_counter_self_denial" in active_acts
    if bounded_counterposition and "Emlis" not in surface.text:
        issues.append("self_denial_explicit_stance_missing")
    if not bounded_counterposition and "Emlis" in surface.text:
        issues.append("human_reception_implicit_speaker_overstated")
    allowed_nucleus_ids = {
        nucleus_id
        for move in active_moves
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
    }
    allowed_evidence_span_ids = {
        span_id
        for move in active_moves
        for span_id in move.source_evidence_span_ids
    }
    if (
        not surface.grounded_nucleus_ids
        or set(surface.grounded_nucleus_ids) != allowed_nucleus_ids
    ):
        issues.append("human_reception_surface_grounding_mismatch")
    if (
        not surface.grounded_evidence_span_ids
        or set(surface.grounded_evidence_span_ids)
        != allowed_evidence_span_ids
    ):
        issues.append("human_reception_surface_evidence_mismatch")
    if (
        any(move.required for move in reception_plan.moves)
        and not {
            move.move_id for move in reception_plan.moves if move.required
        }.issubset(surface.realized_move_ids)
    ):
        issues.append("human_reception_required_move_missing")
    if surface.recovery_stage == "minimal_grounded":
        if (
            len(surface.realized_reception_acts) != 1
            or len(surface.grounded_nucleus_ids) != 1
            or len(surface.grounded_evidence_span_ids) != 1
        ):
            issues.append("human_reception_minimal_grounding_invalid")
        if reception_plan.target_nucleus_ids and (
            surface.grounded_nucleus_ids[:1]
            != reception_plan.target_nucleus_ids[:1]
        ):
            issues.append("human_reception_minimal_target_mismatch")
    if resolver.unresolved_ids(surface.grounded_evidence_span_ids):
        issues.append("human_reception_source_evidence_unresolved")
    return _dedupe(issues)


def _reception_source_fragments(
    nucleus_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    rows: list[tuple[str, tuple[str, ...]]] = []
    for nucleus_id in nucleus_ids:
        nucleus = nucleus_index.get(nucleus_id)
        if nucleus is None:
            continue
        values_list: list[str] = []
        for span_id in nucleus.source_span_ids:
            if resolver.unresolved_ids((span_id,)):
                continue
            raw_text = re.sub(
                r"\s+",
                " ",
                str(resolver.resolve(span_id).raw_text or "").replace(
                    "\u3000",
                    " ",
                ),
            ).strip()
            fragment = (
                _typed_reception_source_fragment(nucleus, raw_text)
                or raw_text
            ).strip(" \u3000、,。．.!！?？「」『』")
            if fragment:
                values_list.append(fragment)
        values = _dedupe(values_list)
        if values:
            rows.append((nucleus_id, values))
    return tuple(rows)


def _visible_fragment_occurrence_count(
    text: str,
    fragments: Sequence[str],
) -> int:
    """Count disjoint source-fragment witnesses in one authored clause."""

    values = tuple(
        sorted(
            _dedupe(fragment for fragment in fragments if fragment),
            key=lambda fragment: (-len(fragment), fragment),
        )
    )
    if not values:
        return 0
    pattern = re.compile("|".join(re.escape(value) for value in values))
    return sum(1 for _match in pattern.finditer(text))


def _source_grounded_context_occurrence_text(value: Any) -> str:
    """Normalize only for rejecting disguised duplicate context adjuncts."""

    normalized = unicodedata.normalize("NFKC", str(value or "")).lower()
    return "".join(
        character
        for character in normalized
        if not character.isspace()
        and unicodedata.category(character)[0] not in {"P", "S", "Z"}
        and unicodedata.category(character) not in {"Cf", "Mn"}
    )


def _final_clean(value: Any) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or "").replace("\u3000", " "),
    ).strip()


def _final_clean_fragment(value: Any) -> str:
    text = _final_clean(value).translate(_FINAL_FRAGMENT_DELETE_TRANSLATION)
    text = text.strip(" 、,。．.!！\t\n\r")
    text = _FINAL_LEADING_CONNECTOR_RE.sub("", text)
    return text.strip()


def _final_quote(value: Any) -> str:
    text = _final_clean_fragment(value)
    return f"「{text}」" if text else ""


def _final_surface_fragment_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    raw_text: Any,
) -> str:
    """Preserve the previous final-Reception source-fragment semantics."""

    text = _final_clean(raw_text)
    attributes = set(nucleus.semantic_frame.attribute_codes)
    typed_fragment = _typed_reception_source_fragment(nucleus, text)
    if typed_fragment is not None:
        return typed_fragment
    if "lexical:preserve_source_predicate" in attributes:
        return text
    if len(text) > 40 and any(
        code.startswith("semantic_role:") for code in attributes
    ):
        parts = re.split(
            r"(?:けれども?|だけど|けど|一方で|ただ)[、,\s]*",
            text,
        )
        candidate = _final_clean(parts[-1]) if len(parts) > 1 else ""
        if len(candidate) >= 8:
            if "semantic_role:initial_condition" in attributes:
                initial = _final_clean(parts[0])
                if initial:
                    return f"{initial}一方、{candidate}"
            return candidate
    return text


def _final_texts_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    return _dedupe(
        _final_clean_fragment(
            _final_surface_fragment_for_nucleus(
                nucleus,
                resolver.resolve(span_id).raw_text,
            )
        )
        for span_id in nucleus.source_span_ids
        if re.fullmatch(r"s[1-9][0-9]*", span_id)
    )


def _final_join_relation_fragments(fragments: Sequence[str]) -> str:
    values = [item for item in fragments if item]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]}と{values[1]}"
    return "、".join(values[:-1]) + f"、そして{values[-1]}"


def final_reception_related_nucleus_id(
    *,
    target_nucleus_ids: Sequence[str],
    reception_act: str,
    plan: GroundedObservationPlan,
) -> str:
    target_set = set(target_nucleus_ids)
    preference = {
        relation_type: index
        for index, relation_type in enumerate(
            _FINAL_RECEPTION_RELATION_PREFERENCE.get(reception_act, ())
        )
    }
    candidates: list[tuple[int, int, str]] = []
    required_relation_ids = tuple(
        plan.coverage_requirements.required_relation_ids
    )
    for relation_index, relation_id in enumerate(required_relation_ids):
        relation = next(
            (row for row in plan.relations if row.relation_id == relation_id),
            None,
        )
        if relation is None:
            continue
        endpoints = (relation.from_nucleus_id, relation.to_nucleus_id)
        if not target_set.intersection(endpoints):
            continue
        other_ids = tuple(item for item in endpoints if item not in target_set)
        if len(other_ids) != 1:
            continue
        candidates.append(
            (
                preference.get(relation.type, len(preference) + 1),
                relation_index,
                other_ids[0],
            )
        )
    if not candidates:
        return ""
    candidates.sort()
    return candidates[0][2]


def final_reception_nucleus_text(
    nucleus_id: str,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    nucleus = nucleus_index.get(nucleus_id)
    if nucleus is None:
        return ""
    values = _final_texts_for_nucleus(nucleus, resolver)
    return values[0] if values else ""


def final_reception_source_anchor_text(
    nucleus_id: str,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    """Return the exact typed fragment independently required by inverse."""

    nucleus = nucleus_index.get(nucleus_id)
    if nucleus is None:
        return ""
    for span_id in nucleus.source_span_ids:
        if not re.fullmatch(r"s[1-9][0-9]*", span_id):
            continue
        raw_text = _final_clean(
            getattr(resolver.resolve(span_id), "raw_text", "")
        )
        typed_fragment = _typed_reception_source_fragment(nucleus, raw_text)
        target = _final_clean_fragment(
            typed_fragment if typed_fragment is not None else raw_text
        )
        if target:
            return target
    return ""


def final_reception_context_nucleus_ids(
    *,
    move: GroundedReceptionMovePlan,
    plan: GroundedObservationPlan,
) -> tuple[str, ...]:
    """Select every Move-owned support, then one existing relation context."""

    target_ids = set(move.target_nucleus_ids)
    direct_support_ids = _dedupe(
        nucleus_id
        for nucleus_id in move.support_nucleus_ids
        if nucleus_id not in target_ids
    )
    if direct_support_ids:
        return direct_support_ids
    related_id = final_reception_related_nucleus_id(
        target_nucleus_ids=move.target_nucleus_ids,
        reception_act=move.reception_act,
        plan=plan,
    )
    return (related_id,) if related_id else ()


def final_reception_context_nucleus_id(
    *,
    move: GroundedReceptionMovePlan,
    plan: GroundedObservationPlan,
) -> str:
    return next(
        iter(final_reception_context_nucleus_ids(move=move, plan=plan)),
        "",
    )


def final_reception_anaphoric_context(
    *,
    move: GroundedReceptionMovePlan,
    context_nucleus_ids: Sequence[str],
    plan: GroundedObservationPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    """Compose a typed context anaphor without replaying its source text."""

    if not context_nucleus_ids:
        return ""
    context_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in context_nucleus_ids
        if nucleus_id in nucleus_index
    )
    context_attributes = frozenset(
        code
        for nucleus in context_nuclei
        for code in nucleus.semantic_frame.attribute_codes
    )
    context_kinds = {nucleus.kind for nucleus in context_nuclei}
    if {
        "operator:residue",
        "semantic_role:present_residue",
    } & context_attributes:
        typed_context = "あとに残る反応"
    elif "constraint" in context_kinds:
        if (
            "operator:uncertainty" in context_attributes
            or any(
                nucleus.semantic_frame.modality == "uncertain"
                for nucleus in context_nuclei
            )
        ):
            typed_context = "まだ定まらない迷い"
        elif (
            "operator:negation" in context_attributes
            or any(
                nucleus.semantic_frame.polarity == "negative"
                for nucleus in context_nuclei
            )
        ):
            typed_context = "動きを止める制約"
        else:
            typed_context = "動きを狭める制約"
    elif "reaction" in context_kinds:
        typed_context = (
            "今の不安"
            if "detected_type:fear" in context_attributes
            else "今の負担"
        )
    elif "change" in context_kinds:
        typed_context = "その後の変化"
    elif "action" in context_kinds:
        typed_context = "そこまでの行動"
    else:
        context_label_by_kind = {
            "event": "そこまでの出来事",
            "state": "その状態",
            "wish": "その願い",
            "self_evaluation": "その自分への見方",
            "value": "そこで大切にされているもの",
            "uncertainty": "まだ定まらないこと",
            "conclusion": "そこでたどり着いた考え",
            "other_explicit": "そこに置かれた言葉",
        }
        typed_context = next(
            (
                context_label_by_kind[kind]
                for kind in (
                    "event",
                    "state",
                    "wish",
                    "self_evaluation",
                    "value",
                    "uncertainty",
                    "conclusion",
                    "other_explicit",
                )
                if kind in context_kinds
            ),
            "",
        )
        if not typed_context:
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )

    # Context is an adjunct, never a flattened member of the relation NP.
    # Relation kind/endpoints are realized by the relation clause itself.
    candidate = typed_context
    exact_context_fragments = _dedupe(
        final_reception_source_anchor_text(
            nucleus_id,
            nucleus_index,
            resolver,
        )
        for nucleus_id in context_nucleus_ids
    )
    if any(
        fragment
        and (
            candidate.count(fragment) > 1
            or fragment in candidate
            and not typed_context.startswith(fragment)
            and not typed_context.endswith(fragment)
        )
        for fragment in exact_context_fragments
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    if not candidate:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    return candidate


_SOURCE_GROUNDED_FOCUS_NOMINAL: Final[dict[str, str]] = {
    "event": "出来事",
    "state": "状態",
    "reaction": "感じ",
    "wish": "望まれていること",
    "constraint": "制約",
    "action": "行動",
    "change": "変化",
    "self_evaluation": "自分への見方",
    "value": "大切にしているもの",
    "uncertainty": "まだ定まらないこと",
    "conclusion": "たどり着いた考え",
    "other_explicit": "ここに置かれた言葉",
}
_SOURCE_GROUNDED_SCOPE_BY_PLAN_SCOPE: Final[dict[str, str]] = {
    "explicit_current_input": "source_bounded",
    "source_bounded_relation": "source_bounded",
    "selected_label_only": "selected_label_only",
}
_SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE: Final = re.compile(
    r"[「」『』\r\n!?！？]|(?:してください|しましょう|すべき)"
)
_SOURCE_GROUNDED_SINGLE_QUOTE_RE: Final = re.compile(
    r"「(?P<corner>[^「」『』\r\n!?！？]{1,16})」"
    r"|『(?P<double>[^「」『』\r\n!?！？]{1,16})』"
)
_SOURCE_GROUNDED_LEXEME_MAX_CHARS: Final = 24
_SOURCE_GROUNDED_STRONG_PARTICLES: Final[tuple[str, ...]] = (
    "について",
    "に対して",
    "によって",
    "には",
    "では",
    "とは",
    "から",
    "まで",
    "より",
    "を",
    "へ",
    "は",
    "が",
)
_SOURCE_GROUNDED_WEAK_PARTICLES: Final[tuple[str, ...]] = (
    "に",
    "で",
    "と",
)
_SOURCE_GROUNDED_TRAILING_CONNECTIVE_RE: Final = re.compile(
    r"(?:けれども?|けど|のに|とはいえ)[、,\s]*$"
)
_SOURCE_GROUNDED_FINITE_END_RE: Final = re.compile(
    r"(?:かも|感じ|予定|つもり|まま|こと|"
    r"なかった|ない|たい|ほしい|欲しい|"
    r"している|ている|でいる|ていた|でいた|"
    r"した|できた|できない|分からない|わからない|"
    r"だった|です|ます|ある|いる|なる|する|"
    r"[ただいうくぐすつぬぶむるん])$"
)


def _source_grounded_axis(values: Sequence[str], *, default: str) -> str:
    rows = _dedupe(values)
    if not rows:
        return default
    if len(rows) != 1:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    return rows[0]


def _source_grounded_clause_candidate(
    nucleus: GroundedSemanticNucleus,
    resolver: EvidenceSpanResolver,
) -> str:
    candidates: list[str] = []
    for span_id in nucleus.source_span_ids:
        if (
            type(span_id) is not str
            or not re.fullmatch(r"s[1-9][0-9]*", span_id)
            or resolver.unresolved_ids((span_id,))
        ):
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        raw = re.sub(
            r"\s+",
            " ",
            str(getattr(resolver.resolve(span_id), "raw_text", "") or "")
            .replace("\u3000", " "),
        ).strip()
        if not raw:
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        precise = _typed_reception_source_fragment(nucleus, raw)
        bounded_source = precise if precise is not None else raw
        for row in re.split(r"[。．.!！?？]+", bounded_source):
            value = re.sub(r"\s+", " ", row).strip(
                " \u3000、,。．.!！?？「」『』"
            )
            if value:
                candidates.append(value)
    candidates = list(_dedupe(candidates))
    if not candidates:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    # Without a typed scalar range the plan must own one unambiguous clause.
    # Lexical inspection must never choose between competing source clauses.
    if len(candidates) != 1:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    return candidates[0]


def _source_grounded_particle_positions(
    value: str,
    particles: Sequence[str],
) -> tuple[tuple[int, int, str], ...]:
    """Return particle boundaries, excluding finite-word lookalikes."""

    positions: list[tuple[int, int, str]] = []
    for particle in particles:
        cursor = 0
        while (start := value.find(particle, cursor)) >= 0:
            end = start + len(particle)
            before = value[:start]
            after = value[end:]
            cursor = start + 1
            if not before or not after:
                continue
            if (
                particle == "から"
                and before.endswith(("分", "わ"))
                and after.startswith("な")
            ):
                continue
            if particle == "が" and after.startswith(
                ("ら", "り", "る", "れ", "ろ", "っ")
            ):
                continue
            if particle == "で" and after.startswith(("き", "は", "も")):
                continue
            if particle == "と" and before.endswith("こ"):
                continue
            if particle == "に" and before.endswith(
                ("気", "ため", "よう", "こと")
            ):
                continue
            positions.append((start, end, particle))
    # Prefer the longest token when alternatives begin at one position.
    by_start: dict[int, tuple[int, int, str]] = {}
    for row in positions:
        incumbent = by_start.get(row[0])
        if incumbent is None or len(row[2]) > len(incumbent[2]):
            by_start[row[0]] = row
    longest = tuple(by_start[index] for index in sorted(by_start))
    return tuple(
        row
        for row in longest
        if not any(
            other[0] <= row[0]
            and row[1] <= other[1]
            and len(other[2]) > len(row[2])
            for other in longest
        )
    )


def _source_grounded_trim_modifier(value: str) -> str:
    clean = value.strip(" 　、,…")
    return _SOURCE_GROUNDED_TRAILING_CONNECTIVE_RE.sub("", clean).strip(
        " 　、,…"
    )


def _source_grounded_final_lexical_word(value: str) -> str:
    """Keep a final content word plus okurigana, at a script boundary."""

    match = re.search(
        r"(?P<kanji>[一-龯々]+[ぁ-んァ-ヶー]*)$"
        r"|(?P<katakana>[ァ-ヶー]+[ぁ-ん]*)$",
        value,
    )
    if match is None:
        return value
    return str(match.group("kanji") or match.group("katakana") or value)


def _source_grounded_predicate_head(value: str) -> str:
    """Select a finite source predicate at grammatical boundaries only."""

    segment = re.split(r"[、,]", value)[-1]
    segment = _source_grounded_trim_modifier(segment)
    if not segment:
        return ""
    positions = _source_grounded_particle_positions(
        segment,
        (*_SOURCE_GROUNDED_STRONG_PARTICLES, *_SOURCE_GROUNDED_WEAK_PARTICLES),
    )
    finite_candidates = tuple(
        candidate
        for candidate in (
            *((segment,) if len(segment) <= _SOURCE_GROUNDED_LEXEME_MAX_CHARS else ()),
            *(
                _source_grounded_trim_modifier(segment[end:])
                for _start, end, _particle in positions
            ),
        )
        if candidate
        and not re.fullmatch(r"[ぁ-ん]{1,3}", candidate)
        and not candidate.startswith(("を", "に", "へ", "は", "が", "と", "で"))
        and len(candidate) <= _SOURCE_GROUNDED_LEXEME_MAX_CHARS
        and _SOURCE_GROUNDED_FINITE_END_RE.search(candidate)
    )
    if finite_candidates:
        # Every candidate reaches the same typed-clause boundary.  Selecting
        # the longest complete finite suffix prevents a kana inside the verb
        # from being mistaken for a case particle and surfaced as a word cut.
        return max(finite_candidates, key=len)
    lexical_segment = _source_grounded_final_lexical_word(segment)
    if len(lexical_segment) <= _SOURCE_GROUNDED_LEXEME_MAX_CHARS:
        return lexical_segment
    # Conjunctive forms are explicit grammatical boundaries.  They provide a
    # bounded final predicate when no case marker is present in a long clause.
    connective_tails = tuple(
        _source_grounded_trim_modifier(segment[match.end() :])
        for match in re.finditer(
            r"(?:なくて|ないで|して|されて|られて|って|たら|なら)",
            segment,
        )
    )
    for candidate in reversed(connective_tails):
        if (
            candidate
            and len(candidate) <= _SOURCE_GROUNDED_LEXEME_MAX_CHARS
            and _SOURCE_GROUNDED_FINITE_END_RE.search(candidate)
        ):
            return candidate
    return ""


def _bounded_source_grounded_lexemes(
    nucleus: GroundedSemanticNucleus,
    resolver: EvidenceSpanResolver,
) -> tuple[str, str]:
    """Decompose one owned source clause; never cut a Japanese word."""

    clause = _source_grounded_clause_candidate(nucleus, resolver)
    clean = clause.strip(" 　、,…")
    quoted_lexical_head = ""
    quote_chars = tuple(
        character for character in clean if character in "「」『』"
    )
    if quote_chars:
        quote_matches = tuple(_SOURCE_GROUNDED_SINGLE_QUOTE_RE.finditer(clean))
        if len(quote_chars) != 2 or len(quote_matches) != 1:
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        quote_match = quote_matches[0]
        quoted_lexical_head = str(
            quote_match.group("corner") or quote_match.group("double") or ""
        ).strip()
        if not quoted_lexical_head:
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        clean = (
            clean[: quote_match.start()]
            + quoted_lexical_head
            + clean[quote_match.end() :]
        )
    if not clean or _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(clean):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )

    predicate = _source_grounded_predicate_head(clean)
    # The selected typed/scalar clause is already the minimal semantic value.
    # Keep it intact; the 24-scalar bound belongs only to its lexical head.
    argument = clean
    if (
        not argument
        or not predicate
        or len(predicate) > _SOURCE_GROUNDED_LEXEME_MAX_CHARS
        or _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(argument)
        or _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(predicate)
        or bool(quoted_lexical_head and predicate == clean)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    return argument, predicate


_SOURCE_GROUNDED_CASE_BY_ROLE: Final[dict[str, str]] = {
    "PRIMARY": "を",
    "EXPERIENCER": "が",
}


@dataclass(frozen=True)
class _SourceGroundedRelationFrameV1:
    endpoint_roles: tuple[str, str]
    case_markers: tuple[str, str]
    direction_sides: tuple[
        Literal["FROM", "TO"] | None,
        Literal["FROM", "TO"] | None,
    ]
    continuative_predicate: str
    finite_predicate: str
    content_predicate_kind: str


_SOURCE_GROUNDED_RELATION_FRAMES: Final[
    dict[str, _SourceGroundedRelationFrameV1]
] = {
    "coexistence": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("と", "が"), (None, None),
        "並び", "並んでいる", "synthesize_relation",
    ),
    "contrast": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("と", "が"), (None, None),
        "一方で異なり", "一方で異なっている",
        "synthesize_relation",
    ),
    "wish_and_constraint": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("と", "が"), (None, None),
        "ともにあり", "ともにある", "synthesize_relation",
    ),
    "preserves_despite": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("が", "の中にも"), (None, None),
        "失われず", "失われない", "synthesize_relation",
    ),
    "attempt_and_block": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("と", "が"), (None, None),
        "ともにあり", "ともにある", "synthesize_relation",
    ),
    "continuation_or_refusal": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("と", "が"), (None, None),
        "ともにあり", "ともにある", "synthesize_relation",
    ),
    "action_supports_change": _SourceGroundedRelationFrameV1(
        ("ACTION", "CHANGE"), ("が", "を"), ("FROM", "TO"),
        "支え", "支えている", "present_change",
    ),
    "temporal_before_after": _SourceGroundedRelationFrameV1(
        ("BEFORE", "AFTER"), ("のあとに", "が"), ("FROM", "TO"),
        "あり", "ある", "present_residue",
    ),
    "shift_from_to": _SourceGroundedRelationFrameV1(
        ("BEFORE", "AFTER"), ("から", "へ"), ("FROM", "TO"),
        "移り", "移っていく", "dynamic_shift",
    ),
    "uncertain_connection": _SourceGroundedRelationFrameV1(
        ("BEFORE", "AFTER"), ("から", "へ"), ("FROM", "TO"),
        "のつながりはまだ定まらず", "のつながりはまだ定まらない",
        "present_unfinished",
    ),
    "user_stated_cause": _SourceGroundedRelationFrameV1(
        ("CAUSE", "EFFECT"), ("によって", "が"), ("FROM", "TO"),
        "生じ", "生じる", "synthesize_relation",
    ),
    "user_stated_result": _SourceGroundedRelationFrameV1(
        ("CAUSE", "EFFECT"), ("から", "へ"), ("FROM", "TO"),
        "つながり", "つながっている", "synthesize_relation",
    ),
    "evaluation_about_event": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("について", "という見方が"), ("FROM", "TO"),
        "示され", "示されている", "synthesize_relation",
    ),
    "self_evaluation_about_state": _SourceGroundedRelationFrameV1(
        ("LEFT", "RIGHT"), ("について", "という見方が"), ("FROM", "TO"),
        "示され", "示されている", "synthesize_relation",
    ),
}


def source_grounded_case_marker_for_role(
    role: str,
    relation_kind: str | None = None,
) -> str:
    """Return the sole source-grounded Japanese case owned by this module."""

    try:
        if relation_kind is not None:
            frame = _SOURCE_GROUNDED_RELATION_FRAMES[relation_kind]
            return frame.case_markers[frame.endpoint_roles.index(role)]
        return _SOURCE_GROUNDED_CASE_BY_ROLE[role]
    except (KeyError, TypeError, ValueError):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        ) from None
_SOURCE_GROUNDED_RELATION_ROLE_PAIR: Final[
    dict[str, tuple[str, str]]
] = {
    kind: frame.endpoint_roles
    for kind, frame in _SOURCE_GROUNDED_RELATION_FRAMES.items()
}
_SOURCE_GROUNDED_ARGUMENT_ROLES: Final[frozenset[str]] = frozenset(
    (*_SOURCE_GROUNDED_CASE_BY_ROLE, *(
        role
        for frame in _SOURCE_GROUNDED_RELATION_FRAMES.values()
        for role in frame.endpoint_roles
    ))
)


def _source_grounded_direction_side(
    relation_kind: str,
    role: str,
) -> Literal["FROM", "TO"] | None:
    """Resolve direction from the relation type without global role drift."""

    try:
        frame = _SOURCE_GROUNDED_RELATION_FRAMES[relation_kind]
        return frame.direction_sides[frame.endpoint_roles.index(role)]
    except (KeyError, ValueError):
        return None


def _source_grounded_direct_predicate(
    nucleus: GroundedSemanticNucleus,
) -> str:
    kind = str(nucleus.kind).lower()
    frame = nucleus.semantic_frame
    predicate = str(frame.predicate_kind).lower()
    attributes = frozenset(str(row) for row in frame.attribute_codes)
    if kind in {"wish", "direction", "desire", "intention", "goal", "help_seeking"}:
        return "present_direction"
    if kind in {"change", "bounded_change"}:
        return "present_change"
    if kind in {"uncertainty", "unfinished", "open_question"}:
        return "present_unfinished"
    if kind in {"constraint", "burden", "fatigue", "anxiety", "hesitation", "block"}:
        return "present_burden"
    if kind in {"action", "attempt"}:
        return "present_actual_output"
    metadata_burden = bool(
        predicate == "constraint"
        or "operator:constraint" in attributes
        or "detected_type:limit_signal" in attributes
        or "detected_type:fear" in attributes
        or any(row.startswith("source_claim:pressure.") for row in attributes)
    )
    if kind == "reaction":
        if (
            predicate == "change"
            or "operator:change" in attributes
            or "operator:positive_change" in attributes
        ):
            return "present_change"
        if metadata_burden:
            return "present_burden"
    if kind == "state" and metadata_burden:
        return "present_burden"
    return "present_state"


def _source_grounded_relation_endpoint_nucleus_roles(
    relation: Any,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    nucleus_rank: Mapping[str, int],
) -> tuple[tuple[str, str], tuple[str, str]]:
    """Rebuild the finite relation-role matrix using plan facts only."""

    try:
        source = nucleus_index[relation.from_nucleus_id]
        target = nucleus_index[relation.to_nucleus_id]
        role_pair = _SOURCE_GROUNDED_RELATION_ROLE_PAIR[relation.type]
    except (KeyError, TypeError):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        ) from None
    if relation.type in {"coexistence", "contrast"}:
        ordered_ids = tuple(
            sorted(
                (source.nucleus_id, target.nucleus_id),
                key=lambda nucleus_id: nucleus_rank[nucleus_id],
            )
        )
        return ((ordered_ids[0], "LEFT"), (ordered_ids[1], "RIGHT"))
    if relation.type in {
        "wish_and_constraint",
        "preserves_despite",
        "attempt_and_block",
        "continuation_or_refusal",
    }:
        rows = ((source, source.nucleus_id), (target, target.nucleus_id))
        direction_rows = tuple(
            nucleus_id
            for nucleus, nucleus_id in rows
            if (
                str(nucleus.kind).lower()
                in {"wish", "direction", "desire", "intention", "goal", "help_seeking"}
                or "semantic_role:direction_under_burden_direction"
                in set(nucleus.semantic_frame.attribute_codes)
            )
        )
        burden_rows = tuple(
            nucleus_id
            for nucleus, nucleus_id in rows
            if (
                _source_grounded_direct_predicate(nucleus)
                == "present_burden"
                or "semantic_role:direction_under_burden_burden"
                in set(nucleus.semantic_frame.attribute_codes)
            )
        )
        if (
            len(direction_rows) == 1
            and len(burden_rows) == 1
            and direction_rows[0] != burden_rows[0]
        ):
            return ((direction_rows[0], "LEFT"), (burden_rows[0], "RIGHT"))
        ordered_ids = tuple(
            sorted(
                (source.nucleus_id, target.nucleus_id),
                key=lambda nucleus_id: nucleus_rank[nucleus_id],
            )
        )
        return ((ordered_ids[0], "LEFT"), (ordered_ids[1], "RIGHT"))
    return (
        (source.nucleus_id, role_pair[0]),
        (target.nucleus_id, role_pair[1]),
    )


def _source_grounded_relation_predicate(
    relation_kind: str,
    endpoint_nuclei: tuple[GroundedSemanticNucleus, GroundedSemanticNucleus],
) -> str:
    if relation_kind == "shift_from_to":
        kinds = tuple(str(nucleus.kind).lower() for nucleus in endpoint_nuclei)
        return (
            "present_actual_output"
            if all(kind in {"action", "attempt"} for kind in kinds)
            else "present_change"
        )
    try:
        return _SOURCE_GROUNDED_RELATION_FRAMES[
            relation_kind
        ].content_predicate_kind
    except KeyError:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        ) from None


def _project_source_grounded_reception_move_realization(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    plan: GroundedObservationPlan,
    recovery_stage: ReceptionRecoveryStage,
    clause_form: Literal["FINITE", "CONTINUATIVE"],
) -> _ReceptionMoveRealizationV1:
    """Pure final grammar projection shared by bridge and plan-only replay."""

    if (
        type(reception_plan) is not GroundedHumanReceptionPlan
        or type(move) is not GroundedReceptionMovePlan
        or type(plan) is not GroundedObservationPlan
        or type(nucleus_index) is not dict
        and not isinstance(nucleus_index, Mapping)
        or recovery_stage not in _RECOVERY_STAGES
        or clause_form not in {"FINITE", "CONTINUATIVE"}
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    target_nuclei = tuple(
        nucleus_index.get(nucleus_id) for nucleus_id in move.target_nucleus_ids
    )
    support_nuclei = tuple(
        nucleus_index.get(nucleus_id) for nucleus_id in move.support_nucleus_ids
    )
    target_id_set = set(move.target_nucleus_ids)
    required_relation_ids = set(
        plan.coverage_requirements.required_relation_ids
    )
    applicable_relations = tuple(
        relation
        for relation in plan.relations
        if relation.relation_id in required_relation_ids
        and target_id_set.intersection(
            (relation.from_nucleus_id, relation.to_nucleus_id)
        )
    )
    relation_context_ids = _dedupe(
        nucleus_id
        for relation in applicable_relations
        for nucleus_id in (
            relation.from_nucleus_id,
            relation.to_nucleus_id,
        )
        if nucleus_id not in target_id_set
        and nucleus_id not in set(move.support_nucleus_ids)
    )
    context_nuclei = tuple(
        nucleus_index.get(nucleus_id) for nucleus_id in relation_context_ids
    )
    if (
        not target_nuclei
        or any(
            nucleus is None
            for nucleus in (
                *target_nuclei,
                *support_nuclei,
                *context_nuclei,
            )
        )
        or not move.source_evidence_span_ids
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    typed_targets = tuple(
        nucleus for nucleus in target_nuclei if nucleus is not None
    )
    typed_supports = tuple(
        nucleus for nucleus in support_nuclei if nucleus is not None
    )
    typed_contexts = tuple(
        nucleus for nucleus in context_nuclei if nucleus is not None
    )
    nucleus_evidence_ids = _dedupe(
        span_id
        for nucleus in (*typed_targets, *typed_supports, *typed_contexts)
        for span_id in nucleus.source_span_ids
    )
    if (
        not nucleus_evidence_ids
        or not set(move.source_evidence_span_ids).issubset(
            nucleus_evidence_ids
        )
        or resolver.unresolved_ids(nucleus_evidence_ids)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    semantic_nuclei = (*typed_targets, *typed_supports, *typed_contexts)
    lexical_rows = tuple(
        _bounded_source_grounded_lexemes(nucleus, resolver)
        for nucleus in semantic_nuclei
    )
    semantic_fragments = tuple(argument for argument, _head in lexical_rows)
    semantic_heads = tuple(head for _argument, head in lexical_rows)
    semantic_profiles = tuple(
        _source_grounded_semantic_profile(nucleus, fragment)
        for nucleus, fragment in zip(
            semantic_nuclei,
            semantic_fragments,
            strict=True,
        )
    )
    predicate_head = lexical_rows[0][1]
    focus_kinds = _dedupe(nucleus.kind for nucleus in typed_targets)
    if not semantic_fragments or not predicate_head or not focus_kinds:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    frames = tuple(nucleus.semantic_frame for nucleus in typed_targets)
    aspect = _source_grounded_axis(
        tuple(
            code.removeprefix("aspect:")
            for frame in frames
            for code in frame.attribute_codes
            if code.startswith("aspect:")
        ),
        default="unknown",
    )
    quantity = _source_grounded_axis(
        tuple(
            code.removeprefix("quantity:")
            for frame in frames
            for code in frame.attribute_codes
            if code.startswith("quantity:")
        ),
        default="not_applicable",
    )
    scope = _source_grounded_axis(
        tuple(
            _SOURCE_GROUNDED_SCOPE_BY_PLAN_SCOPE.get(
                nucleus.allowed_claim_scope,
                nucleus.allowed_claim_scope,
            )
            for nucleus in typed_targets
        ),
        default="source_bounded",
    )
    effective_reference = reception_effective_move_reference_mode(
        reception_plan,
        move,
        recovery_stage,
    )
    reference_mode: ReceptionExpressionReferenceMode
    if effective_reference == "anaphoric_first":
        reference_mode = "ANAPHORIC"
    elif effective_reference == "short_anchor_if_ambiguous":
        reference_mode = (
            "COMPOSITE" if len(semantic_fragments) > 1 else "EXPLICIT"
        )
    elif effective_reference == "explicit_emlis_counterposition":
        reference_mode = "EXPLICIT"
    else:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
        )
    semantic_slot_by_nucleus_id = {
        nucleus.nucleus_id: index
        for index, nucleus in enumerate(semantic_nuclei)
    }
    context_nucleus_ids = final_reception_context_nucleus_ids(
        move=move,
        plan=plan,
    )
    try:
        context_slots = tuple(
            semantic_slot_by_nucleus_id[nucleus_id]
            for nucleus_id in context_nucleus_ids
        )
    except KeyError:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        ) from None
    if (
        len(context_slots) != len(set(context_slots))
        or any(slot < len(typed_targets) for slot in context_slots)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    nucleus_rank = {
        nucleus.nucleus_id: index
        for index, nucleus in enumerate(plan.nuclei)
    }
    relation_rows: list[_ReceptionRelationRealizationV1] = []
    for relation in applicable_relations:
        endpoints = _source_grounded_relation_endpoint_nucleus_roles(
            relation,
            nucleus_index,
            nucleus_rank,
        )
        try:
            endpoint_slots = tuple(
                semantic_slot_by_nucleus_id[nucleus_id]
                for nucleus_id, _role in endpoints
            )
        except KeyError:
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from None
        relation_rows.append(
            _ReceptionRelationRealizationV1(
                relation_kind=relation.type,
                endpoint_slots=endpoint_slots,  # type: ignore[arg-type]
                endpoint_roles=tuple(
                    role for _nucleus_id, role in endpoints
                ),  # type: ignore[arg-type]
            )
        )

    argument_rows: list[_ReceptionArgumentRealizationV1] = []
    for semantic_slot, nucleus in enumerate(semantic_nuclei):
        relation_arguments = tuple(
            (relation_slot, endpoint_index, relation)
            for relation_slot, relation in enumerate(relation_rows)
            for endpoint_index, endpoint_slot in enumerate(
                relation.endpoint_slots
            )
            if endpoint_slot == semantic_slot
        )
        if relation_arguments:
            for relation_slot, endpoint_index, relation in relation_arguments:
                role = relation.endpoint_roles[endpoint_index]
                argument_rows.append(
                    _ReceptionArgumentRealizationV1(
                        semantic_slot=semantic_slot,
                        semantic_role=role,
                        lexical_form=semantic_fragments[semantic_slot],
                        case_marker=source_grounded_case_marker_for_role(
                            role,
                            relation.relation_kind,
                        ),
                        relation_slot=relation_slot,
                        direction_side=_source_grounded_direction_side(
                            relation.relation_kind,
                            role,
                        ),
                        realization="EXPLICIT",
                    )
                )
            continue
        direct_roles = ["PRIMARY"]
        if (
            str(nucleus.semantic_frame.actor).lower()
            in {"current_user", "user"}
            and str(nucleus.semantic_frame.modality).lower()
            in {"feeling", "wish", "intention", "refusal", "uncertain"}
        ):
            direct_roles.append("EXPERIENCER")
        argument_rows.extend(
            _ReceptionArgumentRealizationV1(
                semantic_slot=semantic_slot,
                semantic_role=role,
                lexical_form=semantic_fragments[semantic_slot],
                case_marker=_SOURCE_GROUNDED_CASE_BY_ROLE[role],
                relation_slot=None,
                direction_side=None,
                realization=(
                    "ZERO" if role == "EXPERIENCER" else "EXPLICIT"
                ),
            )
            for role in direct_roles
        )

    relation_predicate_kinds = tuple(
        _source_grounded_relation_predicate(
            relation.relation_kind,
            tuple(
                semantic_nuclei[slot]
                for slot in relation.endpoint_slots
            ),  # type: ignore[arg-type]
        )
        for relation in relation_rows
    )
    governing_relation_slots = tuple(
        relation_slot
        for relation_slot, relation in enumerate(relation_rows)
        if 0 in relation.endpoint_slots
        and any(
            role not in {"LEFT", "RIGHT"} and slot == 0
            for role, slot in zip(
                relation.endpoint_roles,
                relation.endpoint_slots,
                strict=True,
            )
        )
    )
    if not governing_relation_slots and relation_rows:
        governing_relation_slots = tuple(
            relation_slot
            for relation_slot, relation in enumerate(relation_rows)
            if 0 in relation.endpoint_slots
        )
    target_relation_predicates = tuple(
        relation_predicate_kinds[relation_slot]
        for relation_slot in governing_relation_slots
    )
    predicate_values = _dedupe(
        target_relation_predicates
        or tuple(
            _source_grounded_direct_predicate(nucleus)
            for nucleus in typed_targets
        )
    )
    if len(predicate_values) != 1:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    actor_slots = tuple(dict.fromkeys(
        row.semantic_slot
        for row in argument_rows
        if row.semantic_role in {"ACTION", "CAUSE"}
        or str(semantic_nuclei[row.semantic_slot].kind).lower()
        == "action"
    ))
    subject_slots = tuple(dict.fromkeys(
        row.semantic_slot
        for row in argument_rows
        if row.semantic_role
        in {
            "PRIMARY",
            "LEFT",
            "RIGHT",
            "BEFORE",
            "AFTER",
            "CHANGE",
            "EFFECT",
        }
    )) or (0,)
    experiencer_slots = tuple(dict.fromkeys(
        row.semantic_slot
        for row in argument_rows
        if row.semantic_role == "EXPERIENCER"
    ))
    return _ReceptionMoveRealizationV1(
        focus_kinds=focus_kinds,
        semantic_fragments=semantic_fragments,
        semantic_heads=semantic_heads,
        semantic_profiles=semantic_profiles,
        target_slot_count=len(typed_targets),
        context_slots=context_slots,
        arguments=tuple(argument_rows),
        predicate_kind=predicate_values[0],
        predicate_head=predicate_head,
        actor_slots=actor_slots,
        subject_slots=subject_slots,
        experiencer_slots=experiencer_slots,
        polarity=_source_grounded_axis(
            tuple(frame.polarity for frame in frames),
            default="source_bounded",
        ),
        modality=_source_grounded_axis(
            tuple(frame.modality for frame in frames),
            default="source_bounded",
        ),
        time_scope=_source_grounded_axis(
            tuple(frame.time_scope for frame in frames),
            default="current_input",
        ),
        aspect=aspect,
        degree=_source_grounded_axis(
            tuple(frame.degree for frame in frames),
            default="source_bounded",
        ),
        quantity=quantity,
        scope=scope,
        # The current plan has no grammatical subject-duty carrier.  Actor
        # identity alone cannot prove Japanese zero realization.
        subject_realization="EXPLICIT",
        reference_mode=reference_mode,
        antecedent_slots=(
            tuple(range(len(semantic_fragments)))
            if reference_mode == "ANAPHORIC"
            else ()
        ),
        antecedent_condition=(
            "PRIOR_LAYER1_EXACT_SEMANTIC_COVER"
            if reference_mode == "ANAPHORIC"
            else None
        ),
        relations=tuple(relation_rows),
        relation_predicate_kinds=relation_predicate_kinds,
        governing_relation_slots=governing_relation_slots,
        recovery_form=recovery_stage,
        clause_form=clause_form,
    )


def _one_inflection_value(
    inflection_plan: tuple[str, ...],
    prefix: str,
) -> str:
    rows = tuple(
        row.removeprefix(prefix)
        for row in inflection_plan
        if row.startswith(prefix)
    )
    if len(rows) != 1 or not rows[0]:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    return rows[0]


def _expression_source_grounded_move_realization(
    expression: SourceGroundedRealizableReceptionExpressionV1,
    *,
    expected_semantic_profiles: tuple[
        _ReceptionSemanticProfileV1, ...
    ] | None = None,
    expected_target_slot_count: int | None = None,
    expected_context_slots: tuple[int, ...] | None = None,
    expected_relation_predicate_kinds: tuple[str, ...] | None = None,
) -> _ReceptionMoveRealizationV1:
    """Project only identity-bearing expression grammar into the final IR."""

    inflection = expression.inflection_plan
    if len(inflection) != 13:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    focus_kinds = tuple(
        item
        for item in _one_inflection_value(
            inflection,
            "focus-kind:",
        ).split("+")
        if item
    )
    relation_kinds = (
        ()
        if expression.clause_link_plan == ("clause-link:none",)
        else tuple(
            row.removeprefix("relation-kind:")
            for row in expression.clause_link_plan
        )
    )
    if len(relation_kinds) != len(expression.relation_refs):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    semantic_refs = _dedupe(
        argument.semantic_ref for argument in expression.arguments
    )
    semantic_slot_by_ref = {
        semantic_ref: index
        for index, semantic_ref in enumerate(semantic_refs)
    }
    lexical_by_ref: dict[str, str] = {}
    for argument in expression.arguments:
        prior = lexical_by_ref.setdefault(
            argument.semantic_ref,
            argument.lexical_form,
        )
        if prior != argument.lexical_form:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
    semantic_fragments = tuple(
        lexical_by_ref[semantic_ref] for semantic_ref in semantic_refs
    )
    semantic_heads = tuple(
        _source_grounded_predicate_head(fragment)
        for fragment in semantic_fragments
    )
    if (
        expected_semantic_profiles is None
        or expected_target_slot_count is None
        or expected_context_slots is None
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    semantic_profiles = expected_semantic_profiles
    target_slot_count = expected_target_slot_count
    context_slots = expected_context_slots
    if (
        len(semantic_profiles) != len(semantic_fragments)
        or not 1 <= target_slot_count <= len(semantic_fragments)
        or len(context_slots) != len(set(context_slots))
        or any(
            type(slot) is not int
            or not target_slot_count <= slot < len(semantic_fragments)
            for slot in context_slots
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    if (
        not focus_kinds
        or any(kind not in _SOURCE_GROUNDED_FOCUS_NOMINAL for kind in focus_kinds)
        or not semantic_fragments
        or any(not head for head in semantic_heads)
        or any(
            _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(fragment)
            for fragment in semantic_fragments
        )
        or _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(
            expression.lexical_head
        )
        or any(
            argument.realization == "OMITTED"
            for argument in expression.arguments
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    argument_rows: list[_ReceptionArgumentRealizationV1] = []
    for argument in expression.arguments:
        role = argument.semantic_role
        if role not in _SOURCE_GROUNDED_ARGUMENT_ROLES:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        relation_slot: int | None = None
        direction_side: Literal["FROM", "TO"] | None = None
        endpoint_role = any(
            role in role_pair
            for role_pair in _SOURCE_GROUNDED_RELATION_ROLE_PAIR.values()
        )
        if endpoint_role:
            matches = tuple(
                index
                for index, relation_ref in enumerate(
                    expression.relation_refs
                )
                if argument.relation_endpoint_ref
                == _source_grounded_relation_endpoint_ref(
                    relation_ref,
                    argument.semantic_ref,
                    role,
                )
            )
            if len(matches) != 1:
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            relation_slot = matches[0]
            direction_side = _source_grounded_direction_side(
                relation_kinds[relation_slot],
                role,
            )
            expected_direction_ref = (
                _source_grounded_direction_ref(
                    expression.relation_refs[relation_slot],
                    argument.semantic_ref,
                    role,
                    direction_side,
                )
                if direction_side is not None
                else None
            )
            if argument.direction_ref != expected_direction_ref:
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
        elif (
            argument.relation_endpoint_ref is not None
            or argument.direction_ref is not None
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        expected_case_marker = source_grounded_case_marker_for_role(
            role,
            relation_kinds[relation_slot]
            if relation_slot is not None
            else None,
        )
        if argument.case_marker != expected_case_marker:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        same_semantic_primary = any(
            peer.semantic_ref == argument.semantic_ref
            and peer.semantic_role == "PRIMARY"
            and peer.relation_endpoint_ref is None
            and peer.realization == "EXPLICIT"
            for peer in expression.arguments
        )
        if argument.realization == "ZERO":
            if (
                role != "EXPERIENCER"
                or endpoint_role
                or argument.zero_realization_condition_refs
                != ("shared-subject:current-user",)
                or not same_semantic_primary
            ):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
        elif argument.zero_realization_condition_refs:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        argument_rows.append(
            _ReceptionArgumentRealizationV1(
                semantic_slot=semantic_slot_by_ref[argument.semantic_ref],
                semantic_role=role,
                lexical_form=argument.lexical_form,
                case_marker=argument.case_marker,
                relation_slot=relation_slot,
                direction_side=direction_side,
                realization=argument.realization,
            )
        )

    relation_rows: list[_ReceptionRelationRealizationV1] = []
    for relation_slot, relation_kind in enumerate(relation_kinds):
        try:
            expected_roles = _SOURCE_GROUNDED_RELATION_ROLE_PAIR[
                relation_kind
            ]
        except KeyError:
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from None
        endpoint_arguments = tuple(
            argument
            for argument in argument_rows
            if argument.relation_slot == relation_slot
        )
        by_role = {argument.semantic_role: argument for argument in endpoint_arguments}
        if (
            len(endpoint_arguments) != 2
            or len(by_role) != 2
            or set(by_role) != set(expected_roles)
            or by_role[expected_roles[0]].semantic_slot
            == by_role[expected_roles[1]].semantic_slot
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        relation_rows.append(
            _ReceptionRelationRealizationV1(
                relation_kind=relation_kind,
                endpoint_slots=(
                    by_role[expected_roles[0]].semantic_slot,
                    by_role[expected_roles[1]].semantic_slot,
                ),
                endpoint_roles=expected_roles,
            )
        )

    def _slots(refs: tuple[str, ...]) -> tuple[int, ...]:
        try:
            slots = tuple(semantic_slot_by_ref[ref] for ref in refs)
        except KeyError:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            ) from None
        if len(slots) != len(set(slots)):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        return slots

    if expected_relation_predicate_kinds is None:
        if any(
            _SOURCE_GROUNDED_RELATION_FRAMES[
                relation.relation_kind
            ].content_predicate_kind
            == "dynamic_shift"
            for relation in relation_rows
        ):
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        expected_relation_predicate_kinds = tuple(
            _SOURCE_GROUNDED_RELATION_FRAMES[
                relation.relation_kind
            ].content_predicate_kind
            for relation in relation_rows
        )
    if len(expected_relation_predicate_kinds) != len(relation_rows):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    relation_predicate_kinds = tuple(
        (
            expected_relation_predicate_kinds[relation_slot]
            if _SOURCE_GROUNDED_RELATION_FRAMES[
                relation.relation_kind
            ].content_predicate_kind
            == "dynamic_shift"
            else _SOURCE_GROUNDED_RELATION_FRAMES[
                relation.relation_kind
            ].content_predicate_kind
        )
        for relation_slot, relation in enumerate(relation_rows)
    )
    if relation_predicate_kinds != expected_relation_predicate_kinds:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    governing_relation_slots = tuple(
        relation_slot
        for relation_slot, relation in enumerate(relation_rows)
        if 0 in relation.endpoint_slots
        and any(
            role not in {"LEFT", "RIGHT"} and slot == 0
            for role, slot in zip(
                relation.endpoint_roles,
                relation.endpoint_slots,
                strict=True,
            )
        )
    )
    if not governing_relation_slots and relation_rows:
        governing_relation_slots = tuple(
            relation_slot
            for relation_slot, relation in enumerate(relation_rows)
            if 0 in relation.endpoint_slots
        )
    if relation_rows and _dedupe(tuple(
        relation_predicate_kinds[relation_slot]
        for relation_slot in governing_relation_slots
    )) != (expression.predicate_kind,):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )

    return _ReceptionMoveRealizationV1(
        focus_kinds=focus_kinds,
        semantic_fragments=semantic_fragments,
        semantic_heads=semantic_heads,
        semantic_profiles=semantic_profiles,
        target_slot_count=target_slot_count,
        context_slots=context_slots,
        arguments=tuple(argument_rows),
        predicate_kind=expression.predicate_kind,
        predicate_head=expression.lexical_head,
        actor_slots=_slots(expression.actor_refs),
        subject_slots=_slots(expression.subject_refs),
        experiencer_slots=_slots(expression.experiencer_refs),
        polarity=expression.polarity,
        modality=expression.modality,
        time_scope=expression.time_scope,
        aspect=expression.aspect,
        degree=expression.degree,
        quantity=expression.quantity,
        scope=expression.scope,
        subject_realization="EXPLICIT",
        reference_mode=expression.reference_mode,
        antecedent_slots=_slots(expression.antecedent_refs),
        antecedent_condition=expression.antecedent_condition,
        relations=tuple(relation_rows),
        relation_predicate_kinds=relation_predicate_kinds,
        governing_relation_slots=governing_relation_slots,
        recovery_form=_one_inflection_value(
            inflection,
            "reception-form:",
        ),  # type: ignore[arg-type]
        clause_form=_one_inflection_value(
            inflection,
            "clause-form:",
        ),  # type: ignore[arg-type]
    )


def _source_grounded_plan_clause_realizations(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    plan: GroundedObservationPlan,
    recovery_stage: ReceptionRecoveryStage,
    clause_plans: tuple[GroundedReceptionClausePlan, ...],
) -> tuple[_ReceptionClauseRealizationV1, ...]:
    active_moves = reception_active_moves(reception_plan, recovery_stage)
    move_index = {move.move_id: move for move in active_moves}
    return tuple(
        _ReceptionClauseRealizationV1(
            sentence_slot=clause.sentence_slot,
            moves=tuple(
                _project_source_grounded_reception_move_realization(
                    reception_plan,
                    move_index[move_id],
                    nucleus_index,
                    resolver,
                    plan=plan,
                    recovery_stage=recovery_stage,
                    clause_form=(
                        "FINITE"
                        if index == len(clause.move_ids) - 1
                        else "CONTINUATIVE"
                    ),
                )
                for index, move_id in enumerate(clause.move_ids)
            ),
        )
        for clause in clause_plans
    )


def _source_grounded_expression_clause_realizations(
    clause_plans: tuple[GroundedReceptionClausePlan, ...],
    expression_by_move: Mapping[
        str,
        SourceGroundedRealizableReceptionExpressionV1,
    ],
    expected_realizations: tuple[_ReceptionClauseRealizationV1, ...],
) -> tuple[_ReceptionClauseRealizationV1, ...]:
    try:
        if (
            len(clause_plans) != len(expected_realizations)
            or any(
                clause.sentence_slot != expected.sentence_slot
                or len(clause.move_ids) != len(expected.moves)
                for clause, expected in zip(
                    clause_plans,
                    expected_realizations,
                    strict=True,
                )
            )
        ):
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        return tuple(
            _ReceptionClauseRealizationV1(
                sentence_slot=clause.sentence_slot,
                moves=tuple(
                    _expression_source_grounded_move_realization(
                        expression_by_move[move_id],
                        expected_relation_predicate_kinds=(
                            expected.moves[index].relation_predicate_kinds
                        ),
                        expected_semantic_profiles=(
                            expected.moves[index].semantic_profiles
                        ),
                        expected_target_slot_count=(
                            expected.moves[index].target_slot_count
                        ),
                        expected_context_slots=(
                            expected.moves[index].context_slots
                        ),
                    )
                    for index, move_id in enumerate(clause.move_ids)
                ),
            )
            for clause, expected in zip(
                clause_plans,
                expected_realizations,
                strict=True,
            )
        )
    except KeyError:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        ) from None


_SOURCE_GROUNDED_POLARITY_PREFIX: Final[dict[str, str]] = {
    "positive": "",
    "affirmative": "",
    "neutral": "",
    "negative": "否定を含みながら、",
    "mixed": "異なる向きをともに含みながら、",
    "source_bounded": "",
}
_SOURCE_GROUNDED_MODALITY_PREFIX: Final[dict[str, str]] = {
    "fact": "",
    "feeling": "",
    "wish": "",
    "possibility": "可能性として、",
    "uncertain": "まだ定め切らず、",
    "refusal": "拒む向きも含め、",
    "intention": "これからへの意図として、",
    "source_bounded": "",
}
_SOURCE_GROUNDED_TIME_PREFIX: Final[dict[str, str]] = {
    "current_input": "",
    "present": "今、",
    "continuing": "今も、",
    "past": "これまで、",
    "past_to_present": "これまでから今も、",
    "completed": "すでに、",
    "future": "これから、",
    "present_to_future": "今から先も、",
    "unknown": "",
    "source_bounded": "",
}
_SOURCE_GROUNDED_ASPECT_PREFIX: Final[dict[str, str]] = {
    "unknown": "",
    "source_bounded": "",
    "not_applicable": "",
    "completed": "すでに、",
    "perfective": "すでに、",
    "ongoing": "続いて、",
    "progressive": "続いて、",
}
_SOURCE_GROUNDED_DEGREE_PREFIX: Final[dict[str, str]] = {
    "source_bounded": "",
    "not_applicable": "",
    "unknown": "",
    "small": "小さく見えるとしても、",
    "low": "わずかに見えるとしても、",
    "medium": "",
    "high": "強く示されたものとして、",
    "strong": "強く示されたものとして、",
}
_SOURCE_GROUNDED_QUANTITY_PREFIX: Final[dict[str, str]] = {
    "not_applicable": "",
    "source_bounded": "",
    "unknown": "",
    "single": "一つのものとして、",
    "multiple": "いくつか重なるものとして、",
}
_SOURCE_GROUNDED_SCOPE_PREFIX: Final[dict[str, str]] = {
    "source_bounded": "ここで示された範囲では、",
    "current_input": "ここで示された範囲では、",
    "explicit_current_input": "ここで示された範囲では、",
    "source_bounded_relation": "ここで示されたつながりでは、",
    "selected_label_only": "示されたラベルの範囲では、",
}
_SOURCE_GROUNDED_RECOVERY_PREFIX: Final[dict[str, str]] = {
    "full": "",
    "optional_removed": "",
    "integrated": "ひとまとまりにすると、",
    "hedged": "慎重に受け取ると、",
    "minimal_grounded": "一つに絞ると、",
}
_SOURCE_GROUNDED_PREDICATE_ATTRIBUTIVE: Final[dict[str, str]] = {
    "present_direction": "残されている",
    "present_burden": "今ここにある",
    "present_change": "ここに生じた",
    "present_actual_output": "実際に示された",
    "present_unfinished": "まだ定まらない",
    "present_state": "今ここにある",
    "present_residue": "その後にも残る",
    "synthesize_relation": "",
    "source_bounded": "ここに示された",
}

def _source_grounded_relation_predicate_morphemes(
    relation: _ReceptionRelationRealizationV1,
    *,
    predicate_kind: str | None = None,
) -> tuple[str, str]:
    """Select continuative/finite relation verbs from typed grammar axes."""

    try:
        frame = _SOURCE_GROUNDED_RELATION_FRAMES[relation.relation_kind]
    except KeyError:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        ) from None
    if (
        relation.endpoint_roles != frame.endpoint_roles
        or tuple(
            _source_grounded_direction_side(relation.relation_kind, role)
            for role in relation.endpoint_roles
        )
        != frame.direction_sides
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    if (
        predicate_kind is not None
        and frame.content_predicate_kind == "dynamic_shift"
        and predicate_kind not in {"present_actual_output", "present_change"}
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    return frame.continuative_predicate, frame.finite_predicate


def _source_grounded_relation_endpoint_anaphor(
    relation_kind: str,
    role: str,
) -> str:
    """Retain a repeated endpoint's typed role without source replay."""

    directional = {
        "ACTION": "先の行動",
        "CHANGE": "続く変化",
        "BEFORE": "前の状態",
        "AFTER": "後の状態",
        "CAUSE": "示された理由",
        "EFFECT": "続く結果",
    }
    if role in directional:
        return directional[role]
    paired = {
        ("wish_and_constraint", "LEFT"): "残る願い",
        ("wish_and_constraint", "RIGHT"): "動きを狭める制約",
        ("preserves_despite", "LEFT"): "残る向き",
        ("preserves_despite", "RIGHT"): "今の負荷",
        ("attempt_and_block", "LEFT"): "続けた試み",
        ("attempt_and_block", "RIGHT"): "動きを止めたもの",
        ("continuation_or_refusal", "LEFT"): "続ける向き",
        ("continuation_or_refusal", "RIGHT"): "拒む向き",
        ("evaluation_about_event", "LEFT"): "示された出来事",
        ("evaluation_about_event", "RIGHT"): "出来事への評価",
        ("self_evaluation_about_state", "LEFT"): "自分への見方",
        ("self_evaluation_about_state", "RIGHT"): "今の状態",
        ("coexistence", "LEFT"): "一方の向き",
        ("coexistence", "RIGHT"): "もう一方の向き",
        ("contrast", "LEFT"): "一方の向き",
        ("contrast", "RIGHT"): "もう一方の向き",
    }
    try:
        return paired[(relation_kind, role)]
    except KeyError:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        ) from None


def _source_grounded_anaphoric_nominal(
    value: str,
    *,
    predicate_kind: str,
) -> str:
    """Nominalize one complete typed clause without rebuilding its verb."""

    clean = value.strip()
    if not clean:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    if re.search(r"[一-龯々ァ-ヶー]$", clean) or clean.endswith(
        ("こと", "もの", "の", "気持ち", "状態", "感じ")
    ):
        return clean
    if clean.endswith(("たい", "ほしい", "欲しい")):
        return f"{clean}気持ち"
    if clean.endswith("かも"):
        return f"{clean}という感覚"
    if predicate_kind in {"present_state", "present_burden"}:
        return f"{clean}という状態"
    if clean.endswith(("です", "ます")):
        return f"{clean}ということ"
    if (
        clean.endswith(
            (
                "なかった",
                "ない",
                "ている",
                "でいる",
                "ていた",
                "でいた",
                "だった",
                "た",
                "ある",
                "いる",
                "なる",
                "する",
            )
        )
        or re.search(r"[うくぐすつぬぶむるい]$", clean)
    ):
        return f"{clean}こと"
    return f"{clean}ということ"


def _source_grounded_context_head_nominal(value: str) -> str:
    """Nominalize one complete, already source-bound context clause."""

    clean = value.strip(" \u3000、,。．.")
    if (
        not clean
        or _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(clean)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    if re.search(r"[一-龯々ァ-ヶー]$", clean) or clean.endswith(
        ("こと", "もの", "の", "気持ち", "状態", "感じ")
    ):
        return clean
    if clean.endswith(("たい", "ほしい", "欲しい")):
        return f"{clean}気持ち"
    if clean.endswith("かも"):
        return f"{clean}という感覚"
    if (
        clean.endswith(
            (
                "なかった",
                "ない",
                "ている",
                "でいる",
                "ていた",
                "でいた",
                "だった",
                "です",
                "ます",
                "た",
                "ある",
                "いる",
                "なる",
                "する",
            )
        )
        or re.search(r"[うくぐすつぬぶむるい]$", clean)
    ):
        return f"{clean}こと"
    return f"{clean}ということ"


def _source_grounded_context_adjunct_from_heads(
    semantic_heads: Sequence[str],
) -> str:
    """Compose one complete context adjunct from ordered bounded heads."""

    if not semantic_heads:
        return ""
    nominals = tuple(
        _source_grounded_context_head_nominal(head)
        for head in semantic_heads
    )
    if len(nominals) != len(set(nominals)):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    joined = _final_join_relation_fragments(nominals)
    if not joined:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    return f"{joined}を背景に、"


def _source_grounded_context_adjunct(
    move: _ReceptionMoveRealizationV1,
) -> str:
    """Realize the exact plan-owned EXPLICIT context as one adjunct."""

    if move.reference_mode == "ANAPHORIC" or not move.context_slots:
        return ""
    return _source_grounded_context_adjunct_from_heads(
        tuple(move.semantic_fragments[slot] for slot in move.context_slots)
    )


def _source_grounded_axis_prefix(
    mapping: Mapping[str, str],
    value: str,
) -> str:
    try:
        return mapping[value]
    except (KeyError, TypeError):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        ) from None


def _source_grounded_boundary_prefix(
    recovery_form: str,
    scope: str,
) -> str:
    """Combine recovery and scope into one bounded, natural adjunct."""

    # Validate the two independent IR axes before combining their wording.
    _source_grounded_axis_prefix(
        _SOURCE_GROUNDED_RECOVERY_PREFIX,
        recovery_form,
    )
    _source_grounded_axis_prefix(
        _SOURCE_GROUNDED_SCOPE_PREFIX,
        scope,
    )
    scope_noun = {
        "source_bounded": "ここで示された内容",
        "current_input": "ここで示された内容",
        "explicit_current_input": "ここで示された内容",
        "source_bounded_relation": "ここで示されたつながり",
        "selected_label_only": "示されたラベル",
    }[scope]
    if recovery_form in {"full", "optional_removed"}:
        return f"{scope_noun}の範囲では、"
    if recovery_form == "integrated":
        return f"{scope_noun}をひとまとまりにすると、"
    if recovery_form == "hedged":
        return f"{scope_noun}から慎重に受け取ると、"
    if recovery_form == "minimal_grounded":
        return f"{scope_noun}を一つに絞ると、"
    raise GroundedHumanReceptionSurfaceError(
        "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
    )


def _validate_source_grounded_move_ir(
    move: _ReceptionMoveRealizationV1,
) -> None:
    """Consume every grammatical IR duty before it can affect Layer 2."""

    semantic_count = len(move.semantic_fragments)
    if (
        semantic_count < 1
        or len(move.semantic_heads) != semantic_count
        or len(move.semantic_profiles) != semantic_count
        or not 1 <= move.target_slot_count <= semantic_count
        or len(move.context_slots) != len(set(move.context_slots))
        or any(
            type(slot) is not int
            or not move.target_slot_count <= slot < semantic_count
            for slot in move.context_slots
        )
        or not move.arguments
        or move.subject_realization != "EXPLICIT"
        or any(
            type(value) is not str
            or not value.strip()
            or _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(value)
            for value in (*move.semantic_fragments, move.predicate_head)
        )
        or any(
            not head
            or head not in move.semantic_fragments[index]
            or _SOURCE_GROUNDED_LEXICAL_FORBIDDEN_RE.search(head)
            for index, head in enumerate(move.semantic_heads)
        )
        or move.predicate_head != move.semantic_heads[0]
        or any(
            not profile.nucleus_kind
            or not profile.predicate_kind
            or profile.actor_kind not in {"SELF", "OTHER", "UNSPECIFIED"}
            or type(profile.performed_action) is not bool
            or type(profile.future_action) is not bool
            or type(profile.quoted_boundary) is not bool
            or profile.performed_action and profile.future_action
            for profile in move.semantic_profiles
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )

    relation_arguments_by_slot: dict[
        int, list[_ReceptionArgumentRealizationV1]
    ] = {index: [] for index in range(len(move.relations))}
    arguments_by_semantic_slot: dict[
        int, list[_ReceptionArgumentRealizationV1]
    ] = {index: [] for index in range(semantic_count)}
    for argument in move.arguments:
        if (
            type(argument.semantic_slot) is not int
            or argument.semantic_slot not in arguments_by_semantic_slot
            or argument.lexical_form
            != move.semantic_fragments[argument.semantic_slot]
            or argument.realization not in {"EXPLICIT", "ZERO"}
            or argument.semantic_role not in _SOURCE_GROUNDED_ARGUMENT_ROLES
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        arguments_by_semantic_slot[argument.semantic_slot].append(argument)
        if argument.relation_slot is None:
            if argument.case_marker != source_grounded_case_marker_for_role(
                argument.semantic_role
            ):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            if argument.direction_side is not None:
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            if argument.realization == "ZERO" and (
                argument.semantic_role != "EXPERIENCER"
                or not any(
                    peer.semantic_slot == argument.semantic_slot
                    and peer.semantic_role == "PRIMARY"
                    and peer.relation_slot is None
                    and peer.realization == "EXPLICIT"
                    for peer in move.arguments
                )
            ):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            continue
        if (
            type(argument.relation_slot) is not int
            or argument.relation_slot not in relation_arguments_by_slot
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        relation_arguments_by_slot[argument.relation_slot].append(argument)
        if argument.case_marker != source_grounded_case_marker_for_role(
            argument.semantic_role,
            move.relations[argument.relation_slot].relation_kind,
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        if argument.realization != "EXPLICIT":
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )

    # The compiler's argument sequence is semantic-slot-major and then
    # relation-slot-major.  It is an ordered grammatical plan, not a set.
    expected_argument_order: list[_ReceptionArgumentRealizationV1] = []
    for semantic_slot in range(semantic_count):
        rows = tuple(arguments_by_semantic_slot[semantic_slot])
        if not rows:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        relation_rows = tuple(
            row for row in rows if row.relation_slot is not None
        )
        direct_rows = tuple(
            row for row in rows if row.relation_slot is None
        )
        if relation_rows:
            if direct_rows or tuple(
                row.relation_slot for row in relation_rows
            ) != tuple(sorted(row.relation_slot for row in relation_rows)):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            expected_argument_order.extend(relation_rows)
        else:
            if tuple(row.semantic_role for row in direct_rows) not in {
                ("PRIMARY",),
                ("PRIMARY", "EXPERIENCER"),
            }:
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            expected_argument_order.extend(direct_rows)
    if tuple(expected_argument_order) != move.arguments:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )

    for relation_slot, relation in enumerate(move.relations):
        expected_roles = _SOURCE_GROUNDED_RELATION_ROLE_PAIR.get(
            relation.relation_kind
        )
        endpoints = tuple(relation_arguments_by_slot[relation_slot])
        if (
            expected_roles is None
            or relation.endpoint_roles != expected_roles
            or len(relation.endpoint_slots) != 2
            or len(set(relation.endpoint_slots)) != 2
            or any(
                type(slot) is not int or not 0 <= slot < semantic_count
                for slot in relation.endpoint_slots
            )
            or len(endpoints) != 2
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        endpoint_by_role = {row.semantic_role: row for row in endpoints}
        if set(endpoint_by_role) != set(expected_roles):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        for endpoint_index, role in enumerate(expected_roles):
            endpoint = endpoint_by_role[role]
            if (
                endpoint.semantic_slot != relation.endpoint_slots[endpoint_index]
                or endpoint.direction_side
                != _source_grounded_direction_side(
                    relation.relation_kind,
                    role,
                )
            ):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )

    if move.relations:
        if len(move.relation_predicate_kinds) != len(move.relations):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        for relation_slot, relation in enumerate(move.relations):
            frame = _SOURCE_GROUNDED_RELATION_FRAMES[relation.relation_kind]
            relation_predicate_kind = move.relation_predicate_kinds[
                relation_slot
            ]
            if (
                frame.content_predicate_kind == "dynamic_shift"
                and relation_predicate_kind
                not in {"present_actual_output", "present_change"}
            ) or (
                frame.content_predicate_kind != "dynamic_shift"
                and relation_predicate_kind != frame.content_predicate_kind
            ):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )

        expected_governing_relation_slots = tuple(
            relation_slot
            for relation_slot, relation in enumerate(move.relations)
            if 0 in relation.endpoint_slots
            and any(
                role not in {"LEFT", "RIGHT"} and semantic_slot == 0
                for role, semantic_slot in zip(
                    relation.endpoint_roles,
                    relation.endpoint_slots,
                    strict=True,
                )
            )
        )
        if not expected_governing_relation_slots:
            expected_governing_relation_slots = tuple(
                relation_slot
                for relation_slot, relation in enumerate(move.relations)
                if 0 in relation.endpoint_slots
            )
        if (
            not expected_governing_relation_slots
            or move.governing_relation_slots
            != expected_governing_relation_slots
            or _dedupe(tuple(
                move.relation_predicate_kinds[relation_slot]
                for relation_slot in expected_governing_relation_slots
            ))
            != (move.predicate_kind,)
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
    elif move.relation_predicate_kinds or move.governing_relation_slots:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )

    expected_subject_slots = tuple(dict.fromkeys(
        row.semantic_slot
        for row in move.arguments
        if row.semantic_role
        in {
            "PRIMARY",
            "LEFT",
            "RIGHT",
            "BEFORE",
            "AFTER",
            "CHANGE",
            "EFFECT",
        }
    )) or (0,)
    expected_experiencer_slots = tuple(dict.fromkeys(
        row.semantic_slot
        for row in move.arguments
        if row.semantic_role == "EXPERIENCER"
    ))
    required_actor_slots = {
        row.semantic_slot
        for row in move.arguments
        if row.semantic_role in {"ACTION", "CAUSE"}
    }
    if (
        move.subject_slots != expected_subject_slots
        or move.experiencer_slots != expected_experiencer_slots
        or len(move.actor_slots) != len(set(move.actor_slots))
        or any(
            type(slot) is not int or not 0 <= slot < semantic_count
            for slot in (
                *move.actor_slots,
                *move.subject_slots,
                *move.experiencer_slots,
            )
        )
        or not required_actor_slots.issubset(move.actor_slots)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )

    if move.reference_mode == "ANAPHORIC":
        if (
            move.antecedent_slots != tuple(range(semantic_count))
            or move.antecedent_condition
            != "PRIOR_LAYER1_EXACT_SEMANTIC_COVER"
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
            )
    elif (
        move.reference_mode not in {"EXPLICIT", "COMPOSITE"}
        or move.antecedent_slots
        or move.antecedent_condition is not None
        or move.reference_mode == "COMPOSITE"
        and semantic_count < 2
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
        )


def _source_grounded_argument_surface(
    move: _ReceptionMoveRealizationV1,
    *,
    target_nominal: str | None = None,
    target_owner_slot: int = 0,
) -> str:
    """Realize bounded heads in one relation clause per endpoint pair."""

    realized_semantic_slots: set[int] = set()
    relation_endpoints = tuple(
        (relation, role, semantic_slot)
        for relation in move.relations
        for role, semantic_slot in zip(
            relation.endpoint_roles,
            relation.endpoint_slots,
            strict=True,
        )
    )
    relation_occurrences_by_slot = {
        semantic_slot: sum(
            endpoint_slot == semantic_slot
            for _relation, _role, endpoint_slot in relation_endpoints
        )
        for _relation, _role, semantic_slot in relation_endpoints
    }
    first_relation_role_by_slot = {
        semantic_slot: (relation.relation_kind, role)
        for relation, role, semantic_slot in reversed(relation_endpoints)
    }
    typed_nominal_by_slot = {
        semantic_slot: _source_grounded_relation_endpoint_anaphor(
            relation_kind,
            role,
        )
        for semantic_slot, (
            relation_kind,
            role,
        ) in first_relation_role_by_slot.items()
    }
    slots_by_typed_nominal: dict[str, list[int]] = {}
    for semantic_slot, nominal in typed_nominal_by_slot.items():
        slots_by_typed_nominal.setdefault(nominal, []).append(semantic_slot)
    for nominal, semantic_slots in slots_by_typed_nominal.items():
        if len(semantic_slots) < 2:
            continue
        if len(semantic_slots) > 3:
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
            )
        for collision_index, semantic_slot in enumerate(
            sorted(semantic_slots)
        ):
            typed_nominal_by_slot[semantic_slot] = (
                nominal
                if collision_index == 0
                else f"もう一つの{nominal}"
                if collision_index == 1
                else f"さらに別の{nominal}"
            )

    target_inserted = False

    def relation_nominal_for_slot(
        semantic_slot: int,
        relation: _ReceptionRelationRealizationV1,
        role: str,
    ) -> str:
        first_realization = semantic_slot not in realized_semantic_slots
        realized_semantic_slots.add(semantic_slot)
        nonlocal target_inserted
        if (
            first_realization
            and semantic_slot == target_owner_slot
            and target_nominal is not None
        ):
            target_inserted = True
            return target_nominal
        if (
            first_realization
            and semantic_slot in move.context_slots
        ):
            return typed_nominal_by_slot[semantic_slot]
        if (
            not first_realization
            or move.reference_mode == "ANAPHORIC"
        ):
            return typed_nominal_by_slot[semantic_slot]
        return _source_grounded_anaphoric_nominal(
            move.semantic_fragments[semantic_slot],
            predicate_kind=move.predicate_kind,
        )

    direct_phrases: list[str] = []
    for semantic_slot in range(len(move.semantic_fragments)):
        rows = tuple(
            row
            for row in move.arguments
            if row.semantic_slot == semantic_slot
            and row.relation_slot is None
        )
        if not rows:
            continue
        explicit_rows = tuple(
            row for row in rows if row.realization == "EXPLICIT"
        )
        if not explicit_rows:
            continue
        if semantic_slot == target_owner_slot and target_nominal is not None:
            direct_phrases.append(target_nominal)
            realized_semantic_slots.add(semantic_slot)
            target_inserted = True
        elif semantic_slot in move.context_slots:
            # The context head has one dedicated adjunct owner.  A direct
            # argument would duplicate it inside the same Move.
            realized_semantic_slots.add(semantic_slot)
        elif move.reference_mode != "ANAPHORIC":
            direct_phrases.append(
                _source_grounded_anaphoric_nominal(
                    move.semantic_fragments[semantic_slot],
                    predicate_kind=move.predicate_kind,
                )
            )
            realized_semantic_slots.add(semantic_slot)

    relation_phrases: list[str] = []
    for relation_slot, relation in enumerate(move.relations):
        endpoints = {
            argument.semantic_role: argument
            for argument in move.arguments
            if argument.relation_slot == relation_slot
        }
        first_role, second_role = relation.endpoint_roles
        first = endpoints[first_role]
        second = endpoints[second_role]
        first_nominal = relation_nominal_for_slot(
            first.semantic_slot,
            relation,
            first_role,
        )
        second_nominal = relation_nominal_for_slot(
            second.semantic_slot,
            relation,
            second_role,
        )
        _continuative, finite = _source_grounded_relation_predicate_morphemes(
            relation
        )
        relation_phrases.append(
            f"{first_nominal}{first.case_marker}"
            f"{second_nominal}{second.case_marker}{finite}こと"
        )
    independent_target = (
        (target_nominal,)
        if target_nominal is not None and not target_inserted
        else ()
    )
    phrases = (*independent_target, *direct_phrases, *relation_phrases)
    if not phrases:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        )
    return "、また、".join(phrases)


def _source_grounded_meaning_fragment(
    move: _ReceptionMoveRealizationV1,
    *,
    semantic_slot: int = 0,
) -> str:
    _validate_source_grounded_move_ir(move)
    if (
        not 0 <= semantic_slot < len(move.semantic_fragments)
        or
        any(kind not in _SOURCE_GROUNDED_FOCUS_NOMINAL for kind in move.focus_kinds)
        or move.predicate_kind not in _SOURCE_GROUNDED_PREDICATE_ATTRIBUTIVE
        or move.semantic_heads[semantic_slot]
        not in move.semantic_fragments[semantic_slot]
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    # Validate every axis, then compose one finite clause.  Defaults and
    # source bounds remain zero-realized rather than becoming meta labels.
    _source_grounded_boundary_prefix(move.recovery_form, move.scope)
    for mapping, value in (
        (_SOURCE_GROUNDED_DEGREE_PREFIX, move.degree),
        (_SOURCE_GROUNDED_QUANTITY_PREFIX, move.quantity),
        (_SOURCE_GROUNDED_POLARITY_PREFIX, move.polarity),
        (_SOURCE_GROUNDED_MODALITY_PREFIX, move.modality),
    ):
        _source_grounded_axis_prefix(mapping, value)
    _source_grounded_axis_prefix(_SOURCE_GROUNDED_TIME_PREFIX, move.time_scope)
    _source_grounded_axis_prefix(_SOURCE_GROUNDED_ASPECT_PREFIX, move.aspect)

    return (
        ""
        if move.reference_mode == "ANAPHORIC"
        else move.semantic_fragments[semantic_slot]
    )


def _source_grounded_future_action(
    realization: _ReceptionMoveRealizationV1,
    *,
    reception_act: GroundedReceptionAct,
    referent_kind: str = "",
) -> bool:
    return bool(
        reception_act == "honor_concrete_effort"
        and (
            referent_kind == "future_action_intention"
            or "action" in realization.focus_kinds
            and realization.modality == "intention"
            and realization.time_scope
            in {"present", "future", "present_to_future"}
        )
    )


def _source_grounded_target_owner_slot(
    realization: _ReceptionMoveRealizationV1,
    referent_kind: str,
) -> int:
    """Bind a typed referent only to a semantically compatible slot."""

    return _source_grounded_target_owner_from_profiles(
        realization.semantic_profiles,
        realization.target_slot_count,
        referent_kind,
    )


def _source_grounded_target_owner_from_profiles(
    semantic_profiles: tuple[_ReceptionSemanticProfileV1, ...],
    target_slot_count: int,
    referent_kind: str,
) -> int:
    """Resolve exactly one owner within the referent's typed slot range."""

    indexed_profiles = tuple(enumerate(semantic_profiles))
    target_profiles = indexed_profiles[:target_slot_count]
    support_profiles = indexed_profiles[target_slot_count:]
    action_referents = {
        "anchored_concrete_effort",
        "self_started_effort",
        "concrete_effort",
    }
    support_action_referents = {
        "anchored_enacted_effort",
        "enacted_effort_after_intention",
        "next_step_effort",
        "recorded_effort_toward_intention",
    }
    if referent_kind in action_referents:
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.performed_action
        )
    elif referent_kind in support_action_referents:
        candidates = tuple(
            slot
            for slot, profile in support_profiles
            if profile.performed_action
        )
    elif referent_kind == "future_action_intention":
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.future_action
        )
    elif referent_kind in {"retained_wish", "retained_intention"}:
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.nucleus_kind
            in {"wish", "direction", "desire", "intention", "goal"}
        )
    elif referent_kind in {"lived_change", "enacted_change"}:
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.nucleus_kind in {"change", "bounded_change"}
            or profile.predicate_kind == "change"
        )
    elif referent_kind in {
        "current_burden",
        "current_distress",
        "current_suffering",
        "expressed_burden",
        "felt_suffering",
        "felt_suffering_with_counterdirection",
    }:
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.nucleus_kind
            in {"constraint", "burden", "fatigue", "anxiety", "state", "reaction"}
            or profile.predicate_kind == "constraint"
        )
    elif referent_kind in {"help_seeking", "help_seeking_step"}:
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.actor_kind == "SELF"
            and profile.nucleus_kind
            in {"action", "wish", "direction", "intention", "help_seeking"}
        )
    elif referent_kind == "received_help":
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.actor_kind != "SELF"
        )
    elif referent_kind == "grounded_effort":
        candidates = tuple(
            slot
            for slot, profile in target_profiles
            if profile.nucleus_kind in {"action", "attempt"}
        )
    else:
        candidates = tuple(slot for slot, _profile in target_profiles)
    strict_profile_referents = {
        *action_referents,
        *support_action_referents,
        "future_action_intention",
        "received_help",
    }
    if (
        not candidates
        and referent_kind not in strict_profile_referents
        and len(target_profiles) == 1
    ):
        # A non-status-bearing Move referent denotes the Move's content.
        # When the plan gives it exactly one target, that target is an exact
        # owner rather than a positional fallback.  Multi-target ambiguity
        # and all performed/future/support status claims still fail closed.
        candidates = (target_profiles[0][0],)
    if len(candidates) != 1:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
        )
    return candidates[0]


def _source_grounded_clause_voice(
    realization: _ReceptionMoveRealizationV1,
    *,
    target_owner_slot: int,
    referent_kind: str,
) -> Literal[
    "SELF_PERFORMED",
    "OTHER_PERFORMED",
    "FUTURE_INTENTION",
    "RECEIVED",
    "STATE",
]:
    return _source_grounded_profile_voice(
        realization.semantic_profiles[target_owner_slot],
        referent_kind,
    )


def _source_grounded_profile_voice(
    profile: _ReceptionSemanticProfileV1,
    referent_kind: str,
) -> Literal[
    "SELF_PERFORMED",
    "OTHER_PERFORMED",
    "FUTURE_INTENTION",
    "RECEIVED",
    "STATE",
]:
    if referent_kind == "received_help":
        return "RECEIVED"
    if referent_kind == "future_action_intention":
        return "FUTURE_INTENTION"
    if profile.performed_action and profile.actor_kind == "SELF":
        return "SELF_PERFORMED"
    if profile.performed_action:
        return "OTHER_PERFORMED"
    if profile.future_action:
        return "FUTURE_INTENTION"
    return "STATE"


def _source_grounded_referent_predicate_kind(referent_kind: str) -> str:
    if referent_kind in {
        "future_action_intention",
        "retained_wish",
        "retained_intention",
    }:
        return "present_direction"
    if referent_kind in {
        "current_burden",
        "current_distress",
        "current_suffering",
        "expressed_burden",
        "felt_suffering",
        "felt_suffering_with_counterdirection",
    }:
        return "present_burden"
    if referent_kind in {"lived_change", "enacted_change"}:
        return "present_change"
    if referent_kind in {
        "anchored_concrete_effort",
        "anchored_enacted_effort",
        "self_started_effort",
        "concrete_effort",
        "enacted_effort_after_intention",
        "next_step_effort",
        "recorded_effort_toward_intention",
        "help_seeking",
    }:
        return "present_actual_output"
    if referent_kind == "help_seeking_step":
        return "present_direction"
    if referent_kind == "grounded_effort":
        return "present_unfinished"
    if referent_kind in {"current_expression", "words_placed"}:
        return "source_bounded"
    return "present_state"


_SOURCE_GROUNDED_TEMPORAL_LEXICAL_MARKERS: Final[
    Mapping[str, tuple[str, ...]]
] = {
    "current_input": (),
    "present": ("今",),
    "continuing": ("今",),
    "past": ("これまで",),
    "past_to_present": ("これまで", "今"),
    "completed": ("すでに",),
    "future": ("これから",),
    "present_to_future": ("今", "これから"),
    "unknown": (),
    "source_bounded": (),
}
_SOURCE_GROUNDED_PAST_MORPHOLOGY_RE: Final = re.compile(
    r"(?:なかった|ではなかった|だった|でした|ました|ていた|でいた|"
    r"った|いた|いだ|した|んだ|た)$"
)
_SOURCE_GROUNDED_PROGRESSIVE_MORPHOLOGY_RE: Final = re.compile(
    r"(?:て|で)(?:い|お)(?:る|ます|た|ました)$"
)
_SOURCE_GROUNDED_PAST_TO_PRESENT_MORPHOLOGY_RE: Final = re.compile(
    r"(?:て|で)き(?:た|ました)$"
)
_SOURCE_GROUNDED_NONPAST_MORPHOLOGY_RE: Final = re.compile(
    r"(?:ない|たい|です|ます|ある|いる|なる|する|"
    r"[うくぐすつぬぶむるい])$"
)


def _source_grounded_temporal_aspect_realization(
    realization: _ReceptionMoveRealizationV1,
    semantic_head: str,
) -> tuple[
    Literal["SOURCE_CLAUSE", "ANTECEDENT", "ADJUNCT"],
    Literal["SOURCE_CLAUSE", "ANTECEDENT", "ADJUNCT"],
    str,
    str,
]:
    """Assign each typed temporal axis to one grammatical surface owner."""

    time_adjunct = _source_grounded_axis_prefix(
        _SOURCE_GROUNDED_TIME_PREFIX,
        realization.time_scope,
    )
    aspect_adjunct = _source_grounded_axis_prefix(
        _SOURCE_GROUNDED_ASPECT_PREFIX,
        realization.aspect,
    )
    if realization.reference_mode == "ANAPHORIC":
        return "ANTECEDENT", "ANTECEDENT", "", ""

    clean_head = semantic_head.strip(" \u3000、,。．.")
    lexical_time = any(
        marker in clean_head
        for marker in _SOURCE_GROUNDED_TEMPORAL_LEXICAL_MARKERS[
            realization.time_scope
        ]
    )
    if realization.time_scope in {"past", "completed"}:
        morphological_time = bool(
            _SOURCE_GROUNDED_PAST_MORPHOLOGY_RE.search(clean_head)
        )
    elif realization.time_scope == "past_to_present":
        morphological_time = bool(
            _SOURCE_GROUNDED_PAST_TO_PRESENT_MORPHOLOGY_RE.search(clean_head)
            or _SOURCE_GROUNDED_PROGRESSIVE_MORPHOLOGY_RE.search(clean_head)
        )
    elif realization.time_scope == "continuing":
        morphological_time = bool(
            _SOURCE_GROUNDED_PROGRESSIVE_MORPHOLOGY_RE.search(clean_head)
        )
    elif realization.time_scope in {
        "present",
        "future",
        "present_to_future",
    }:
        morphological_time = bool(
            _SOURCE_GROUNDED_NONPAST_MORPHOLOGY_RE.search(clean_head)
        )
    else:
        morphological_time = True
    time_in_source = lexical_time or morphological_time or not time_adjunct

    if realization.aspect in {"completed", "perfective"}:
        aspect_in_source = bool(
            _SOURCE_GROUNDED_PAST_MORPHOLOGY_RE.search(clean_head)
        )
    elif realization.aspect in {"ongoing", "progressive"}:
        aspect_in_source = bool(
            _SOURCE_GROUNDED_PROGRESSIVE_MORPHOLOGY_RE.search(clean_head)
        )
    else:
        aspect_in_source = True

    return (
        "SOURCE_CLAUSE" if time_in_source else "ADJUNCT",
        "SOURCE_CLAUSE" if aspect_in_source else "ADJUNCT",
        "" if time_in_source else time_adjunct,
        "" if aspect_in_source else aspect_adjunct,
    )


def _validate_source_grounded_clause_core(
    core: _SourceGroundedClauseCoreV1,
    *,
    realization: _ReceptionMoveRealizationV1,
    target_owner_slot: int,
) -> None:
    """Fail closed when a ClauseCore loses or duplicates an axis owner."""

    expected_time, expected_aspect, expected_time_adjunct, expected_aspect_adjunct = (
        _source_grounded_temporal_aspect_realization(
            realization,
            realization.semantic_fragments[target_owner_slot],
        )
    )
    if (
        core.target_owner_slot != target_owner_slot
        or core.temporal_realization != expected_time
        or core.aspect_realization != expected_aspect
        or core.temporal_adjunct != expected_time_adjunct
        or core.aspect_adjunct != expected_aspect_adjunct
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    ownership_rows = (
        (core.temporal_realization, core.temporal_adjunct),
        (core.aspect_realization, core.aspect_adjunct),
    )
    if any(
        owner == "ADJUNCT" and not adjunct
        or owner != "ADJUNCT" and bool(adjunct)
        for owner, adjunct in ownership_rows
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    visible_adjuncts = _dedupe(
        adjunct for _owner, adjunct in ownership_rows if adjunct
    )
    source_values = (*realization.semantic_heads, *realization.semantic_fragments)
    nonexpected_adjuncts = tuple(
        adjunct
        for adjunct in _dedupe(
            (
                *_SOURCE_GROUNDED_TIME_PREFIX.values(),
                *_SOURCE_GROUNDED_ASPECT_PREFIX.values(),
            )
        )
        if adjunct not in visible_adjuncts
        and not any(adjunct in value for value in source_values)
    )
    if (
        _visible_fragment_occurrence_count(
            core.text,
            (core.target_referent,),
        )
        != 1
        or any(core.text.count(adjunct) != 1 for adjunct in visible_adjuncts)
        or any(
            core.text.count(adjunct)
            > sum(
                core.text.count(visible_adjunct)
                * visible_adjunct.count(adjunct)
                for visible_adjunct in visible_adjuncts
            )
            for adjunct in nonexpected_adjuncts
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
        )


def _source_grounded_target_np(
    move: GroundedReceptionMovePlan,
    realization: _ReceptionMoveRealizationV1,
    *,
    meaning_fragment: str,
    referent_text: str,
    referent_kind: str,
    source_anchor_used: bool,
    target_owner_slot: int,
) -> _SourceGroundedClauseCoreV1:
    """Build one grammatical content core with one inverse referent."""

    (
        temporal_realization,
        aspect_realization,
        temporal_adjunct,
        aspect_adjunct,
    ) = _source_grounded_temporal_aspect_realization(
        realization,
        realization.semantic_fragments[target_owner_slot],
    )
    if realization.reference_mode == "ANAPHORIC":
        referent_np = (
            f"{referent_text}と、それに重なるもの"
            if realization.quantity == "multiple"
            else referent_text
        )
        content_target = f"{meaning_fragment}{referent_np}"
    else:
        if referent_text.startswith(("その", "それらの")):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
            )
        quantity_modifier = {
            "not_applicable": "",
            "source_bounded": "",
            "unknown": "",
            "single": "一つの",
            "multiple": "いくつかの",
        }[realization.quantity]
        profile = realization.semantic_profiles[target_owner_slot]
        proposition = (
            f"{meaning_fragment}という言葉"
            if profile.quoted_boundary
            else _source_grounded_anaphoric_nominal(
                meaning_fragment,
                predicate_kind=realization.predicate_kind,
            )
        )
        content_target = (
            f"{proposition}に表れた{quantity_modifier}{referent_text}"
        )
    if realization.relations:
        # A relation clause is already a complete grammatical core.  Never
        # feed its governed endpoints through a target or act wrapper.
        target = _source_grounded_argument_surface(
            realization,
            target_nominal=content_target,
            target_owner_slot=target_owner_slot,
        )
    else:
        target = content_target
    adjuncts = _dedupe(
        adjunct
        for adjunct in (temporal_adjunct, aspect_adjunct)
        if adjunct
    )
    target = f"{''.join(adjuncts)}{target}"
    core = _SourceGroundedClauseCoreV1(
        text=target,
        target_referent=referent_text,
        semantic_slots=tuple(range(len(realization.semantic_fragments))),
        relation_count=len(realization.relations),
        target_owner_slot=target_owner_slot,
        temporal_realization=temporal_realization,
        aspect_realization=aspect_realization,
        temporal_adjunct=temporal_adjunct,
        aspect_adjunct=aspect_adjunct,
        voice=_source_grounded_clause_voice(
            realization,
            target_owner_slot=target_owner_slot,
            referent_kind=referent_kind,
        ),
    )
    _validate_source_grounded_clause_core(
        core,
        realization=realization,
        target_owner_slot=target_owner_slot,
    )
    return core


def _validate_source_grounded_predicate_voice(
    *,
    semantic_profile: _ReceptionSemanticProfileV1,
    referent_kind: str,
    target_predicate_kind: str,
    voice: Literal[
        "SELF_PERFORMED",
        "OTHER_PERFORMED",
        "FUTURE_INTENTION",
        "RECEIVED",
        "STATE",
    ],
) -> None:
    """Validate one plan-owned voice against its governed predicate."""

    expected_voice = _source_grounded_profile_voice(
        semantic_profile,
        referent_kind,
    )
    expected_predicate = _source_grounded_referent_predicate_kind(
        referent_kind
    )
    allowed_voices = {
        "present_direction": {"STATE", "FUTURE_INTENTION"},
        "present_burden": {"STATE"},
        "present_change": {"STATE"},
        "present_actual_output": {
            "SELF_PERFORMED",
            "OTHER_PERFORMED",
        },
        "present_unfinished": {"STATE"},
        "present_state": {"STATE", "RECEIVED"},
        "present_residue": {"STATE"},
        "synthesize_relation": {"STATE"},
        "source_bounded": {"STATE", "RECEIVED"},
    }.get(target_predicate_kind)
    profile_matches_voice = {
        "SELF_PERFORMED": (
            semantic_profile.performed_action
            and semantic_profile.actor_kind == "SELF"
        ),
        "OTHER_PERFORMED": (
            semantic_profile.performed_action
            and semantic_profile.actor_kind != "SELF"
        ),
        "FUTURE_INTENTION": (
            semantic_profile.future_action
            and not semantic_profile.performed_action
        ),
        "RECEIVED": (
            referent_kind == "received_help"
            and semantic_profile.actor_kind != "SELF"
            and not semantic_profile.performed_action
            and not semantic_profile.future_action
        ),
        "STATE": (
            referent_kind != "received_help"
            and not semantic_profile.performed_action
            and not semantic_profile.future_action
        ),
    }[voice]
    if (
        voice != expected_voice
        or target_predicate_kind != expected_predicate
        or allowed_voices is None
        or voice not in allowed_voices
        or not profile_matches_voice
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )


def _source_grounded_response_predicate(
    reception_act: GroundedReceptionAct,
    move_role: str,
    *,
    future_action: bool,
    target_predicate_kind: str,
    semantic_profile: _ReceptionSemanticProfileV1,
    referent_kind: str,
    voice: Literal[
        "SELF_PERFORMED",
        "OTHER_PERFORMED",
        "FUTURE_INTENTION",
        "RECEIVED",
        "STATE",
    ],
) -> _SourceGroundedResponsePredicateV1:
    """Compose role valency independently from the act predicate."""

    _validate_source_grounded_predicate_voice(
        semantic_profile=semantic_profile,
        referent_kind=referent_kind,
        target_predicate_kind=target_predicate_kind,
        voice=voice,
    )

    role_morphemes = {
        "attention": ("に", "目が留まり、"),
        "significance": ("を", "見失わず、"),
        "felt_response": ("を", ""),
    }
    try:
        object_particle, role_operator = role_morphemes[move_role]
    except KeyError:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        ) from None

    if future_action != (
        reception_act == "honor_concrete_effort"
        and voice == "FUTURE_INTENTION"
    ):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    # The target clause carries state and agency. The predicate expresses
    # the already selected Reception act; it does not narrate those facts.
    if reception_act == "stay_with_current_burden":
        act_guard, predicate_lemma, conjugation_class = "小さくせずに", "受け止める", "ICHIDAN"
    elif reception_act == "protect_retained_intention":
        act_guard, predicate_lemma, conjugation_class = "大切に", "受け止める", "ICHIDAN"
    elif reception_act == "recognize_lived_change":
        act_guard, predicate_lemma, conjugation_class = "", "感じる", "ICHIDAN"
    elif reception_act in {"honor_concrete_effort", "hold_help_seeking", "respect_words_placed"}:
        act_guard, predicate_lemma, conjugation_class = "大切に", "受け止める", "ICHIDAN"
    else:
        raise GroundedHumanReceptionSurfaceError("MEANING_REALIZATION_CAPABILITY_GAP")
    reception_operator = voice_complement = valency_complement = ""
    return _SourceGroundedResponsePredicateV1(
        object_particle=object_particle,
        role_operator=role_operator,
        act_guard=act_guard,
        reception_operator=reception_operator,
        voice_complement=voice_complement,
        valency_complement=valency_complement,
        predicate_lemma=predicate_lemma,
        conjugation_class=conjugation_class,
    )


def _source_grounded_inflect_response_predicate(
    predicate: _SourceGroundedResponsePredicateV1,
    *,
    clause_form: Literal["FINITE", "CONTINUATIVE"],
    hedged: bool,
) -> str:
    """Inflect one governed lemma without storing a completed close."""

    lemma = predicate.predicate_lemma
    conjugation = predicate.conjugation_class
    if conjugation == "ICHIDAN" and lemma.endswith("る"):
        te_form = lemma[:-1] + "て"
        desire_form = lemma[:-1] + "たいです"
    elif conjugation == "GODAN_RU" and lemma.endswith("る"):
        te_form = lemma[:-1] + "って"
        desire_form = lemma[:-1] + "りたいです"
    elif conjugation == "GODAN_TSU" and lemma.endswith("つ"):
        te_form = lemma[:-1] + "って"
        desire_form = lemma[:-1] + "ちたいです"
    elif conjugation == "GODAN_U" and lemma.endswith("う"):
        te_form = lemma[:-1] + "って"
        desire_form = lemma[:-1] + "いたいです"
    elif conjugation == "GODAN_SU" and lemma.endswith("す"):
        te_form = lemma[:-1] + "して"
        desire_form = lemma[:-1] + "したいです"
    else:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    if hedged:
        if clause_form != "FINITE":
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
            )
        return desire_form
    return te_form + ("います" if clause_form == "FINITE" else "いて")


def _source_grounded_response_predicate_surface(
    reception_act: GroundedReceptionAct,
    move_role: str,
    *,
    future_action: bool,
    target_predicate_kind: str,
    semantic_profile: _ReceptionSemanticProfileV1,
    referent_kind: str,
    voice: Literal[
        "SELF_PERFORMED",
        "OTHER_PERFORMED",
        "FUTURE_INTENTION",
        "RECEIVED",
        "STATE",
    ],
    clause_form: Literal["FINITE", "CONTINUATIVE"],
    recovery_stage: ReceptionRecoveryStage = "full",
) -> str:
    """Author and binder share one exact governed predicate surface."""

    predicate = _source_grounded_response_predicate(
        reception_act,
        move_role,
        future_action=future_action,
        target_predicate_kind=target_predicate_kind,
        semantic_profile=semantic_profile,
        referent_kind=referent_kind,
        voice=voice,
    )
    if recovery_stage not in _RECOVERY_STAGES:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
        )
    governed_predicate = _source_grounded_inflect_response_predicate(
        predicate,
        clause_form=clause_form,
        hedged=recovery_stage == "hedged",
    )
    return (
        f"{predicate.object_particle}{predicate.role_operator}"
        f"{predicate.act_guard}{predicate.reception_operator}"
        f"{predicate.voice_complement}{predicate.valency_complement}"
        f"{governed_predicate}"
    )


def _source_grounded_reception_fragment(
    move: GroundedReceptionMovePlan,
    realization: _ReceptionMoveRealizationV1,
    *,
    context_prefix: str,
    target_core: _SourceGroundedClauseCoreV1,
    referent_kind: str,
    target_owner_slot: int,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Compose one content core with one role/focus reception predicate."""

    _validate_source_grounded_clause_core(
        target_core,
        realization=realization,
        target_owner_slot=target_owner_slot,
    )
    if target_core.target_owner_slot != target_owner_slot:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    core = f"{context_prefix}{target_core.text}"
    if move.move_role == "bounded_counterposition":
        reference_complement = (
            "その見方だけで"
            if realization.reference_mode == "ANAPHORIC"
            else "その言葉だけで"
        )
        negative_ending = (
            "ません"
            if realization.clause_form == "FINITE"
            else "ず"
        )
        return (
            f"{core}を否定せず受け止め、"
            f"Emlisには、{reference_complement}あなた自身が"
            f"決まるとは思え{negative_ending}"
        )
    if move.move_role not in {"attention", "significance", "felt_response"}:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )

    predicate_surface = _source_grounded_response_predicate_surface(
        move.reception_act,
        move.move_role,
        future_action=_source_grounded_future_action(
            realization,
            reception_act=move.reception_act,
            referent_kind=referent_kind,
        ),
        target_predicate_kind=_source_grounded_referent_predicate_kind(
            referent_kind
        ),
        semantic_profile=(
            realization.semantic_profiles[target_owner_slot]
        ),
        referent_kind=referent_kind,
        voice=_source_grounded_clause_voice(
            realization,
            target_owner_slot=target_owner_slot,
            referent_kind=referent_kind,
        ),
        clause_form=realization.clause_form,
        recovery_stage=recovery_stage,
    )
    return f"{core}{predicate_surface}"


def _author_source_grounded_reception_clauses(
    reception_plan: GroundedHumanReceptionPlan,
    clause_plans: tuple[GroundedReceptionClausePlan, ...],
    clause_realizations: tuple[_ReceptionClauseRealizationV1, ...],
    resolver: EvidenceSpanResolver,
    *,
    plan: GroundedObservationPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    recovery_stage: ReceptionRecoveryStage,
    binding_seeds: tuple[_ReceptionClauseBindingSeedV1, ...] = (),
) -> GroundedHumanReceptionSurface:
    """The sole final author; bindings are emitted in the same append pass."""

    expected_clause_realizations = _source_grounded_plan_clause_realizations(
        reception_plan,
        nucleus_index,
        resolver,
        plan=plan,
        recovery_stage=recovery_stage,
        clause_plans=clause_plans,
    )
    if clause_realizations != expected_clause_realizations:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    if (
        len(clause_plans) != len(clause_realizations)
        or binding_seeds
        and len(binding_seeds) != len(clause_realizations)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
        )
    active_moves = reception_active_moves(reception_plan, recovery_stage)
    move_index = {move.move_id: move for move in active_moves}
    parts: list[str] = []
    bindings: list[ReceptionVisibleSegmentBindingV1] = []
    referent_kinds: list[str] = []
    anchor_used = False
    cursor = 0
    for clause_index, (clause_plan, realization) in enumerate(
        zip(clause_plans, clause_realizations, strict=True)
    ):
        if (
            realization.sentence_slot != clause_plan.sentence_slot
            or len(realization.moves) != len(clause_plan.move_ids)
            or not realization.moves
            or any(
                row.clause_form
                != (
                    "FINITE"
                    if index == len(realization.moves) - 1
                    else "CONTINUATIVE"
                )
                for index, row in enumerate(realization.moves)
            )
        ):
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
            )
        move_sentences: list[str] = []
        for move_id, meaning_realization in zip(
            clause_plan.move_ids,
            realization.moves,
            strict=True,
        ):
            move = move_index.get(move_id)
            if move is None:
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
                )
            referent = resolve_grounded_reception_move_referent(
                reception_plan=reception_plan,
                move=move,
                nucleus_index=nucleus_index,
                resolver=resolver,
                allow_short_anchor=False,
                recovery_stage=recovery_stage,
                allow_anaphoric_topic=True,
            )
            anchor_used = anchor_used or referent.source_anchor_used
            referent_kinds.append(referent.kind)
            target_owner_slot = _source_grounded_target_owner_slot(
                meaning_realization,
                referent.kind,
            )
            meaning_fragment = _source_grounded_meaning_fragment(
                meaning_realization,
                semantic_slot=target_owner_slot,
            )
            # A short source-bound lexical anchor may be part of an existing
            # referent duty, but final Layer 2 never presents it as a quote.
            referent_text = referent.text.replace("「", "").replace("」", "")
            context_ids = final_reception_context_nucleus_ids(
                move=move,
                plan=plan,
            )
            target_core = _source_grounded_target_np(
                move,
                meaning_realization,
                referent_text=referent_text,
                referent_kind=referent.kind,
                meaning_fragment=meaning_fragment,
                source_anchor_used=referent.source_anchor_used,
                target_owner_slot=target_owner_slot,
            )
            if meaning_realization.reference_mode == "ANAPHORIC":
                context_value = final_reception_anaphoric_context(
                    move=move,
                    context_nucleus_ids=context_ids,
                    plan=plan,
                    nucleus_index=nucleus_index,
                    resolver=resolver,
                )
                context_prefix = (
                    f"{context_value}が重なる中で、"
                    if context_value
                    and meaning_realization.relations
                    else f"{context_value}を背景に、"
                    if context_value
                    else ""
                )
            else:
                context_prefix = _source_grounded_context_adjunct(
                    meaning_realization
                )
            move_sentence = _source_grounded_reception_fragment(
                move,
                meaning_realization,
                context_prefix=context_prefix,
                target_core=target_core,
                referent_kind=referent.kind,
                target_owner_slot=target_owner_slot,
                recovery_stage=recovery_stage,
            )
            if (
                _visible_fragment_occurrence_count(
                    move_sentence,
                    (referent_text,),
                )
                != 1
                or not _ACT_OWNED_RESPONSIBILITY_RE[
                    move.reception_act
                ].search(move_sentence)
                or move.move_role == "attention"
                and not _ATTENTION_RESPONSIBILITY_RE.search(move_sentence)
            ):
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
                )
            move_sentences.append(move_sentence)
        segment = (
            move_sentences[0]
            if len(move_sentences) == 1
            else "、".join(
                sentence.rstrip("。、") for sentence in move_sentences
            )
        ).rstrip("。") + "。"
        if not segment.strip():
            raise GroundedHumanReceptionSurfaceError(
                "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
            )
        start = cursor
        parts.append(segment)
        cursor += len(segment)
        if binding_seeds:
            seed = binding_seeds[clause_index]
            if seed.move_ids != clause_plan.move_ids:
                raise GroundedHumanReceptionSurfaceError(
                    "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
                )
            draft = ReceptionVisibleSegmentBindingV1(
                binding_ref="",
                expression_refs=seed.expression_refs,
                move_ids=seed.move_ids,
                human_reception_local_scalar_start=start,
                human_reception_local_scalar_end=cursor,
                surface_span_sha256=hashlib.sha256(
                    segment.encode("utf-8")
                ).hexdigest(),
                clause_frame_fields=seed.clause_frame_fields,
                surface_derivation_refs=seed.surface_derivation_refs,
            )
            bindings.append(_identify_visible_segment_binding(draft))

    text = "".join(parts)
    realized_move_ids = tuple(move.move_id for move in active_moves)
    grounded_nucleus_ids = _dedupe(
        nucleus_id
        for move in active_moves
        for nucleus_id in (*move.target_nucleus_ids, *move.support_nucleus_ids)
    )
    grounded_evidence_ids = _dedupe(
        span_id
        for move in active_moves
        for span_id in move.source_evidence_span_ids
    )
    expression_refs = _dedupe(
        expression_ref
        for seed in binding_seeds
        for expression_ref in seed.expression_refs
    )
    if binding_seeds and (
        len(expression_refs)
        != sum(len(seed.expression_refs) for seed in binding_seeds)
        or _dedupe(
            move_id for seed in binding_seeds for move_id in seed.move_ids
        )
        != realized_move_ids
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
        )
    quote_values = tuple(_QUOTE_RE.findall(text))
    surface = GroundedHumanReceptionSurface(
        text=text,
        terminal_predicate_kinds=tuple(
            reception_terminal_predicate_kind(move.reception_act)
            for move in active_moves
        ),
        sentence_count=_sentence_count(text),
        referent_kind="+".join(referent_kinds),
        realized_reception_acts=tuple(
            move.reception_act for move in active_moves
        ),
        realized_move_ids=realized_move_ids,
        realized_move_roles=tuple(move.move_role for move in active_moves),
        move_predicate_families=tuple(
            reception_move_predicate_family(move) for move in active_moves
        ),
        realized_clause_move_ids=tuple(
            clause.move_ids for clause in clause_plans
        ),
        grounded_nucleus_ids=grounded_nucleus_ids,
        grounded_evidence_span_ids=grounded_evidence_ids,
        source_anchor_count=len(quote_values),
        source_anchor_max_visible_chars=max(
            (len(value) for value in quote_values),
            default=0,
        ),
        recovery_stage=recovery_stage,
        expression_refs=expression_refs,
        visible_segment_bindings=tuple(bindings),
    )
    issues = validate_grounded_human_reception_surface(
        surface,
        reception_plan,
        resolver,
    )
    if issues:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
        )
    return surface


def _replay_source_grounded_human_reception_from_plan(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    plan: GroundedObservationPlan,
    recovery_stage: ReceptionRecoveryStage,
    clause_plans: Sequence[GroundedReceptionClausePlan],
) -> GroundedHumanReceptionSurface:
    """Validation-only replay from existing grounding inputs, never a carrier."""

    resolved_clause_plans = tuple(clause_plans)
    _validate_clause_plan_binding(
        reception_plan,
        resolved_clause_plans,
        recovery_stage,
    )
    realizations = _source_grounded_plan_clause_realizations(
        reception_plan,
        nucleus_index,
        resolver,
        plan=plan,
        recovery_stage=recovery_stage,
        clause_plans=resolved_clause_plans,
    )
    return _author_source_grounded_reception_clauses(
        reception_plan,
        resolved_clause_plans,
        realizations,
        resolver,
        plan=plan,
        nucleus_index=nucleus_index,
        recovery_stage=recovery_stage,
    )


_RECEPTION_VISIBLE_CLAUSE_FRAME_FIELD_ORDER: Final = (
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


def _clause_frame_fields_for_expressions(
    expressions: Sequence[SourceGroundedRealizableReceptionExpressionV1],
) -> Mapping[str, Any]:
    rows = tuple(expressions)
    arguments = tuple(
        argument for expression in rows for argument in expression.arguments
    )
    semantic_refs = _dedupe(
        (
            *(argument.semantic_ref for argument in arguments),
            *(ref for expression in rows for ref in expression.relation_refs),
        )
    )
    subject_refs = _dedupe(
        ref for expression in rows for ref in expression.subject_refs
    )
    if not rows or not semantic_refs:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
        )
    expression_frames = tuple(
        (
            row.expression_ref,
            row.predicate_kind,
            row.lexical_head,
            row.polarity,
            row.modality,
            row.time_scope,
            row.aspect,
            row.degree,
            row.quantity,
            row.scope,
            row.reference_mode,
            row.antecedent_refs,
            row.antecedent_condition,
            (
                row.move_id,
                _dedupe(
                    (
                        *(
                            argument.semantic_ref
                            for argument in row.arguments
                        ),
                        *row.relation_refs,
                    )
                ),
                row.qualifier_refs,
                row.relation_refs,
                row.relation_endpoint_refs,
                row.direction_refs,
                row.actor_refs,
                row.subject_refs,
                row.experiencer_refs,
            ),
        )
        for row in rows
    )
    semantic_refs = _dedupe(
        ref
        for frame in expression_frames
        for ref in frame[13][1]
    )
    payload: dict[str, Any] = {
        "semantic_refs": semantic_refs,
        "source_evidence_refs": _dedupe(
            ref for row in rows for ref in row.source_evidence_refs
        ),
        "predicate_operator": tuple(row.predicate_kind for row in rows),
        "lexical_heads": tuple(row.lexical_head for row in rows),
        "topic_ref": subject_refs[0] if subject_refs else semantic_refs[0],
        "object_ref": semantic_refs[1] if len(semantic_refs) > 1 else None,
        "argument_bindings": tuple(
            (
                argument.semantic_role,
                argument.semantic_ref,
                argument.lexical_form,
                argument.source_evidence_refs,
                argument.requirement,
                argument.omission_permission,
                argument.zero_realization_condition_refs,
                argument.omission_condition_refs,
                argument.case_marker,
                argument.direction_ref,
                argument.relation_endpoint_ref,
                argument.realization,
            )
            for argument in arguments
        ),
        "qualifier_refs": _dedupe(
            ref for row in rows for ref in row.qualifier_refs
        ),
        "relation_refs": _dedupe(
            ref for row in rows for ref in row.relation_refs
        ),
        "relation_endpoint_refs": _dedupe(
            ref for row in rows for ref in row.relation_endpoint_refs
        ),
        "direction_refs": _dedupe(
            ref for row in rows for ref in row.direction_refs
        ),
        "polarity": tuple(row.polarity for row in rows),
        "modality": tuple(row.modality for row in rows),
        "time_scope": tuple(row.time_scope for row in rows),
        "aspect": tuple(row.aspect for row in rows),
        "degree": tuple(row.degree for row in rows),
        "quantity": tuple(row.quantity for row in rows),
        "scope": tuple(row.scope for row in rows),
        "actor_refs": _dedupe(ref for row in rows for ref in row.actor_refs),
        "subject_refs": subject_refs,
        "experiencer_refs": _dedupe(
            ref for row in rows for ref in row.experiencer_refs
        ),
        "reference_modes": tuple(row.reference_mode for row in rows),
        "antecedent_refs": tuple(row.antecedent_refs for row in rows),
        "antecedent_conditions": tuple(
            row.antecedent_condition for row in rows
        ),
        "particle_plans": tuple(row.particle_plan for row in rows),
        "inflection_plans": tuple(row.inflection_plan for row in rows),
        "nominalization_plans": tuple(
            row.nominalization_plan for row in rows
        ),
        "clause_link_plans": tuple(row.clause_link_plan for row in rows),
        "meaning_outcome_refs": tuple(
            row.meaning_outcome_ref for row in rows
        ),
        "reception_binding_refs": tuple(
            row.reception_binding_ref for row in rows
        ),
        "expression_frames": expression_frames,
    }
    if tuple(payload) != _RECEPTION_VISIBLE_CLAUSE_FRAME_FIELD_ORDER:
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
        )
    return MappingProxyType(payload)


def _identify_visible_segment_binding(
    binding: ReceptionVisibleSegmentBindingV1,
) -> ReceptionVisibleSegmentBindingV1:
    if (
        type(binding) is not ReceptionVisibleSegmentBindingV1
        or not isinstance(binding.clause_frame_fields, Mapping)
        or tuple(binding.clause_frame_fields)
        != _RECEPTION_VISIBLE_CLAUSE_FRAME_FIELD_ORDER
    ):
        raise GroundedHumanReceptionSurfaceError(
            "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
        )
    frozen_clause_frame_fields = MappingProxyType(
        dict(binding.clause_frame_fields)
    )
    payload = {
        "expression_refs": binding.expression_refs,
        "move_ids": binding.move_ids,
        "human_reception_local_scalar_start": (
            binding.human_reception_local_scalar_start
        ),
        "human_reception_local_scalar_end": (
            binding.human_reception_local_scalar_end
        ),
        "surface_span_sha256": binding.surface_span_sha256,
        "clause_frame_fields": dict(frozen_clause_frame_fields),
        "surface_derivation_refs": binding.surface_derivation_refs,
    }
    digest = hashlib.sha256(
        b"cocolon.emlis.reception_visible_segment_binding.v1\0"
        + _private_canonical_json_bytes(payload)
    ).hexdigest()
    return replace(
        binding,
        binding_ref=(
            f"reception-visible-segment-binding:{digest}"
            f"@{RECEPTION_VISIBLE_SEGMENT_BINDING_SCHEMA_VERSION}"
        ),
        clause_frame_fields=frozen_clause_frame_fields,
    )


def _realize_source_grounded_human_reception(
    reception_plan: GroundedHumanReceptionPlan,
    expressions: Sequence[SourceGroundedRealizableReceptionExpressionV1],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    plan: GroundedObservationPlan,
    recovery_stage: ReceptionRecoveryStage,
    clause_plans: Sequence[GroundedReceptionClausePlan],
) -> GroundedHumanReceptionSurface:
    """Consume exact selected-meaning expressions and author Layer 2 once."""

    pairs = validate_source_grounded_reception_expressions(
        reception_plan,
        expressions,
        recovery_stage,
    )
    expression_by_move = {
        expression.move_id: expression for _move, expression in pairs
    }
    for _move, expression in pairs:
        # Expression evidence refs are canonical graph identities (opaque
        # ``evidence:ev-...@version``), while the plan/resolver owns local
        # ``sN`` ids.  Their exact join is proved by the compiler bridge.  Do
        # not invent an sN decoder here; the independent expression-vs-plan
        # realization comparison below closes source grounding at this owner.
        if any(
            re.fullmatch(r"evidence:[^@\s]+@[^@\s]+", evidence_ref)
            is None
            for evidence_ref in expression.source_evidence_refs
        ):
            raise GroundedHumanReceptionSurfaceError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )

    resolved_clause_plans = tuple(clause_plans)
    _validate_clause_plan_binding(
        reception_plan,
        resolved_clause_plans,
        recovery_stage=recovery_stage,
    )
    plan_realizations = _source_grounded_plan_clause_realizations(
        reception_plan,
        nucleus_index,
        resolver,
        plan=plan,
        recovery_stage=recovery_stage,
        clause_plans=resolved_clause_plans,
    )
    expression_realizations = _source_grounded_expression_clause_realizations(
        resolved_clause_plans,
        expression_by_move,
        plan_realizations,
    )
    if expression_realizations != plan_realizations:
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    seeds: list[_ReceptionClauseBindingSeedV1] = []
    for clause_plan in resolved_clause_plans:
        clause_expressions = tuple(
            expression_by_move[move_id] for move_id in clause_plan.move_ids
        )
        seeds.append(
            _ReceptionClauseBindingSeedV1(
            expression_refs=tuple(
                row.expression_ref for row in clause_expressions
            ),
            move_ids=clause_plan.move_ids,
            clause_frame_fields=_clause_frame_fields_for_expressions(
                clause_expressions
            ),
            surface_derivation_refs=_dedupe(
                (
                    "surface-derivation:human-reception-expression"
                    "@cocolon.emlis.human_reception.realizable_expression.v1",
                    *(row.expression_ref for row in clause_expressions),
                )
            ),
            )
        )
    return _author_source_grounded_reception_clauses(
        reception_plan,
        resolved_clause_plans,
        expression_realizations,
        resolver,
        plan=plan,
        nucleus_index=nucleus_index,
        recovery_stage=recovery_stage,
        binding_seeds=tuple(seeds),
    )


_SOURCE_GROUNDED_NAMED_FAILURES: Final = frozenset(
    {
        "MEANING_REALIZATION_CAPABILITY_GAP",
        "MEANING_REALIZATION_CAUSAL_TRACE_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP",
    }
)


def _normalize_source_grounded_failure(failure: str) -> str:
    if failure in _SOURCE_GROUNDED_NAMED_FAILURES:
        return failure
    if any(
        marker in failure
        for marker in ("anaphor", "reference", "referent", "quote")
    ):
        return "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
    if any(
        marker in failure
        for marker in ("morph", "predicate", "inflection", "integrat")
    ):
        return "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP"
    if any(
        marker in failure
        for marker in ("clause", "surface", "sentence", "binding", "range", "hash")
    ):
        return "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
    if any(
        marker in failure
        for marker in ("move", "source", "evidence", "ground", "target")
    ):
        return "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
    return "MEANING_REALIZATION_CAPABILITY_GAP"


def replay_source_grounded_human_reception_from_plan(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    plan: GroundedObservationPlan,
    recovery_stage: ReceptionRecoveryStage,
    clause_plans: Sequence[GroundedReceptionClausePlan],
) -> GroundedHumanReceptionSurface:
    """Independently rebuild final bytes from plan inputs only."""

    try:
        return _replay_source_grounded_human_reception_from_plan(
            reception_plan,
            nucleus_index,
            resolver,
            plan=plan,
            recovery_stage=recovery_stage,
            clause_plans=clause_plans,
        )
    except GroundedHumanReceptionSurfaceError as exc:
        raise GroundedHumanReceptionSurfaceError(
            _normalize_source_grounded_failure(str(exc))
        ) from None
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        ) from None


def realize_source_grounded_human_reception(
    reception_plan: GroundedHumanReceptionPlan,
    expressions: Sequence[SourceGroundedRealizableReceptionExpressionV1],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    plan: GroundedObservationPlan,
    recovery_stage: ReceptionRecoveryStage,
    clause_plans: Sequence[GroundedReceptionClausePlan],
) -> GroundedHumanReceptionSurface:
    """Named-failure boundary for the final source-grounded author."""

    try:
        return _realize_source_grounded_human_reception(
            reception_plan,
            expressions,
            nucleus_index,
            resolver,
            plan=plan,
            recovery_stage=recovery_stage,
            clause_plans=clause_plans,
        )
    except GroundedHumanReceptionSurfaceError as exc:
        raise GroundedHumanReceptionSurfaceError(
            _normalize_source_grounded_failure(str(exc))
        ) from None
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        raise GroundedHumanReceptionSurfaceError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        ) from None


def bind_and_validate_grounded_human_reception_surface(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    actual_text: str,
    recovery_stage: ReceptionRecoveryStage = "full",
    clause_plans: Sequence[GroundedReceptionClausePlan] | None = None,
    context_nucleus_ids_by_move: Mapping[str, Sequence[str]] | None = None,
    allow_anaphoric_topic: bool = False,
) -> GroundedHumanReceptionSurface:
    """Bind an already-realized body to RR4 and validate that exact body."""

    if recovery_stage not in _RECOVERY_STAGES:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_recovery_stage:{recovery_stage}"
        )
    if not reception_plan.required:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_plan_present_but_not_required"
        )
    active_moves = reception_active_moves(reception_plan, recovery_stage)
    active_acts = tuple(move.reception_act for move in active_moves)
    resolved_clause_plans = tuple(
        clause_plans
        if clause_plans is not None
        else build_grounded_reception_clause_plans(
            reception_plan,
            recovery_stage,
        )
    )
    _validate_clause_plan_binding(
        reception_plan,
        resolved_clause_plans,
        recovery_stage,
    )
    move_index = {move.move_id: move for move in active_moves}
    referents: list[GroundedReceptionReferent] = []
    referent_by_move: dict[str, GroundedReceptionReferent] = {}
    anchor_used = False
    for clause_plan in resolved_clause_plans:
        for move_id in clause_plan.move_ids:
            move = move_index[move_id]
            referent = resolve_grounded_reception_move_referent(
                reception_plan,
                move,
                nucleus_index,
                resolver,
                allow_short_anchor=bool(
                    clause_plan.quote_budget and not anchor_used
                ),
                recovery_stage=recovery_stage,
                allow_anaphoric_topic=allow_anaphoric_topic,
            )
            anchor_used = anchor_used or referent.source_anchor_used
            referents.append(referent)
            referent_by_move[move_id] = referent

    quote_values = tuple(_QUOTE_RE.findall(actual_text))
    surface = GroundedHumanReceptionSurface(
        text=actual_text,
        terminal_predicate_kinds=tuple(
            reception_terminal_predicate_kind(move.reception_act)
            for move in active_moves
        ),
        sentence_count=_sentence_count(actual_text),
        referent_kind="+".join(referent.kind for referent in referents),
        realized_reception_acts=active_acts,
        realized_move_ids=tuple(move.move_id for move in active_moves),
        realized_move_roles=tuple(move.move_role for move in active_moves),
        move_predicate_families=tuple(
            reception_move_predicate_family(move) for move in active_moves
        ),
        realized_clause_move_ids=tuple(
            clause.move_ids for clause in resolved_clause_plans
        ),
        grounded_nucleus_ids=_dedupe(
            nucleus_id
            for referent in referents
            for nucleus_id in referent.nucleus_ids
        ),
        grounded_evidence_span_ids=_dedupe(
            span_id
            for referent in referents
            for span_id in referent.evidence_span_ids
        ),
        source_anchor_count=len(quote_values),
        source_anchor_max_visible_chars=max(
            (len(value) for value in quote_values),
            default=0,
        ),
        recovery_stage=recovery_stage,
    )
    issues = list(
        validate_grounded_human_reception_surface(
            surface,
            reception_plan,
            resolver,
        )
    )
    actual_clause_texts = tuple(
        part.strip()
        for part in _SENTENCE_END_RE.split(actual_text)
        if part.strip()
    )
    actual_text_by_move = {
        move_id: clause_text
        for clause_plan, clause_text in zip(
            resolved_clause_plans,
            actual_clause_texts,
        )
        for move_id in clause_plan.move_ids
    }

    active_nucleus_ids = _dedupe(
        nucleus_id
        for move in active_moves
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
    )
    allowed_source_fragments = tuple(
        fragment
        for _nucleus_id, fragments in _reception_source_fragments(
            active_nucleus_ids,
            nucleus_index,
            resolver,
        )
        for fragment in fragments
    )
    for quote in quote_values:
        if not any(quote in fragment for fragment in allowed_source_fragments):
            issues.append("human_reception_source_anchor_unbound")

    context_map = context_nucleus_ids_by_move or {}
    for move in active_moves:
        move_text = actual_text_by_move.get(move.move_id, "")
        referent = referent_by_move.get(move.move_id)
        if not _ACT_RESPONSIBILITY_RE[move.reception_act].search(move_text):
            issues.append(
                "human_reception_act_responsibility_missing:"
                f"{move.reception_act}"
            )
        if (
            move.move_role == "attention"
            and not _ATTENTION_RESPONSIBILITY_RE.search(move_text)
        ):
            issues.append(
                f"human_reception_move_attention_missing:{move.move_id}"
            )

        effective_reference = reception_effective_move_reference_mode(
            reception_plan,
            move,
            recovery_stage,
        )
        target_rows = _reception_source_fragments(
            move.target_nucleus_ids,
            nucleus_index,
            resolver,
        )
        target_fragments = tuple(
            fragment
            for _nucleus_id, fragments in target_rows
            for fragment in fragments
        )
        referent_visible = bool(
            referent is not None and referent.text in move_text
        )
        if not referent_visible:
            issues.append(
                f"human_reception_move_target_missing:{move.move_id}"
            )
        if effective_reference == "anaphoric_first" and any(
            fragment in move_text for fragment in target_fragments
        ):
            issues.append(
                f"human_reception_anaphoric_target_replayed:{move.move_id}"
            )
        if effective_reference == "short_anchor_if_ambiguous" and any(
            len(fragment)
            > reception_plan.quote_policy.max_anchor_visible_chars
            and fragment in move_text
            for fragment in target_fragments
        ):
            issues.append(
                f"human_reception_long_target_replayed:{move.move_id}"
            )

        context_ids = tuple(context_map.get(move.move_id, ()))
        context_rows = _reception_source_fragments(
            context_ids,
            nucleus_index,
            resolver,
        )
        if context_rows and effective_reference == "anaphoric_first":
            if not any(
                marker in move_text
                for marker in ("中で", "中にも", "背景")
            ):
                issues.append(
                    f"human_reception_context_anaphor_missing:{move.move_id}"
                )
            if any(
                fragment in move_text
                for _nucleus_id, fragments in context_rows
                for fragment in fragments
            ):
                issues.append(
                    f"human_reception_anaphoric_context_replayed:{move.move_id}"
                )
        elif context_rows and any(
            not any(fragment in move_text for fragment in fragments)
            for _nucleus_id, fragments in context_rows
        ):
            issues.append(
                f"human_reception_move_context_missing:{move.move_id}"
            )

    issues = list(_dedupe(issues))
    if issues:
        raise GroundedHumanReceptionSurfaceError(
            "invalid_grounded_human_reception_surface:" + ",".join(issues)
        )
    return surface


def realize_grounded_human_reception(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    recovery_stage: ReceptionRecoveryStage = "full",
    clause_plans: Sequence[GroundedReceptionClausePlan] | None = None,
) -> GroundedHumanReceptionSurface:
    """Realize deterministic Move contributions from one body-free ClausePlan."""

    if recovery_stage not in _RECOVERY_STAGES:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_recovery_stage:{recovery_stage}"
        )
    if not reception_plan.required:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_plan_present_but_not_required"
        )
    active_moves = reception_active_moves(reception_plan, recovery_stage)
    active_acts = tuple(move.reception_act for move in active_moves)
    resolved_clause_plans = tuple(
        clause_plans
        if clause_plans is not None
        else build_grounded_reception_clause_plans(
            reception_plan,
            recovery_stage,
        )
    )
    _validate_clause_plan_binding(
        reception_plan,
        resolved_clause_plans,
        recovery_stage,
    )
    move_index = {move.move_id: move for move in active_moves}

    clauses: list[str] = []
    referents: list[GroundedReceptionReferent] = []
    anchor_used = False
    for clause_plan in resolved_clause_plans:
        move_sentences: list[str] = []
        for move_id in clause_plan.move_ids:
            move = move_index[move_id]
            referent = resolve_grounded_reception_move_referent(
                reception_plan,
                move,
                nucleus_index,
                resolver,
                allow_short_anchor=bool(
                    clause_plan.quote_budget and not anchor_used
                ),
                recovery_stage=recovery_stage,
            )
            anchor_used = anchor_used or referent.source_anchor_used
            referents.append(referent)
            move_sentences.append(
                _realize_move_sentence(
                    reception_plan,
                    move,
                    referent,
                    nucleus_index,
                    recovery_stage,
                )
            )
        clauses.append(
            move_sentences[0]
            if len(move_sentences) == 1
            else _integrate_move_sentences(
                move_sentences[0],
                move_sentences[1],
            )
        )
    terminal_kinds = tuple(
        reception_terminal_predicate_kind(move.reception_act)
        for move in active_moves
    )

    text = "".join(f"{clause.rstrip('。')}。" for clause in clauses if clause.strip())
    quote_values = tuple(_QUOTE_RE.findall(text))
    surface = GroundedHumanReceptionSurface(
        text=text,
        terminal_predicate_kinds=terminal_kinds,
        sentence_count=_sentence_count(text),
        referent_kind="+".join(referent.kind for referent in referents),
        realized_reception_acts=active_acts,
        realized_move_ids=tuple(move.move_id for move in active_moves),
        realized_move_roles=tuple(move.move_role for move in active_moves),
        move_predicate_families=tuple(
            reception_move_predicate_family(move) for move in active_moves
        ),
        realized_clause_move_ids=tuple(
            clause.move_ids for clause in resolved_clause_plans
        ),
        grounded_nucleus_ids=_dedupe(
            nucleus_id
            for referent in referents
            for nucleus_id in referent.nucleus_ids
        ),
        grounded_evidence_span_ids=_dedupe(
            span_id
            for referent in referents
            for span_id in referent.evidence_span_ids
        ),
        source_anchor_count=len(quote_values),
        source_anchor_max_visible_chars=max(
            (len(value) for value in quote_values),
            default=0,
        ),
        recovery_stage=recovery_stage,
    )
    issues = validate_grounded_human_reception_surface(
        surface,
        reception_plan,
        resolver,
    )
    if issues:
        raise GroundedHumanReceptionSurfaceError(
            "invalid_grounded_human_reception_surface:" + ",".join(issues)
        )
    return surface


__all__ = [
    "ReceptionRecoveryStage",
    "ReceptionConnectorPolicy",
    "ReceptionExpressionReferenceMode",
    "SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION",
    "RECEPTION_VISIBLE_SEGMENT_BINDING_SCHEMA_VERSION",
    "GroundedHumanReceptionSurfaceError",
    "RealizableReceptionArgumentV1",
    "SourceGroundedRealizableReceptionExpressionV1",
    "ReceptionVisibleSegmentBindingV1",
    "GroundedReceptionClausePlan",
    "GroundedReceptionReferent",
    "GroundedHumanResponsePredicate",
    "GroundedHumanReceptionSurface",
    "reception_terminal_predicate_kind",
    "reception_move_predicate_family",
    "reception_active_moves",
    "reception_active_acts",
    "build_grounded_reception_clause_plans",
    "reception_effective_sentence_budget",
    "reception_effective_speaker_presence",
    "reception_effective_reference_mode",
    "reception_effective_move_reference_mode",
    "reception_action_is_future_intention",
    "source_grounded_case_marker_for_role",
    "resolve_grounded_reception_referent",
    "resolve_grounded_reception_move_referent",
    "validate_grounded_human_reception_surface",
    "identify_source_grounded_reception_expression",
    "validate_source_grounded_reception_expression",
    "validate_source_grounded_reception_expressions",
    "bind_and_validate_grounded_human_reception_surface",
    "realize_grounded_human_reception",
    "replay_source_grounded_human_reception_from_plan",
    "realize_source_grounded_human_reception",
]
