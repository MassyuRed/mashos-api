# -*- coding: utf-8 -*-
from __future__ import annotations

"""V3-only, body-free semantic-restatement witness for Grounded plans.

The established ``GroundedObservationPlan`` is a byte-frozen dependency of
earlier NLS v3 steps.  This adapter therefore derives the additional relation
semantics without modifying that owner.  Source text is used only while
recomputing the witness and never appears in the returned artifact or errors.
"""

from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any, Final, Literal, Mapping, Sequence

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    GroundedSemanticNucleus,
    GroundedSemanticRelation,
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256


GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.grounded_semantic_restatement_witness.v1"
)
GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3.grounded_semantic_restatement_adapter.20260715.v2"
)

EndpointSemanticRelation = Literal[
    "distinct_meanings",
    "semantic_restatement",
]

SemanticUnitKind = Literal[
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

SemanticLinkType = Literal[
    "precedes",
    "contrasts_with",
    "coexists_with",
    "qualifies",
    "supports_without_guarantee",
]

_TEXT_SOURCE_FIELDS: Final = frozenset({"memo", "memo_action"})
_DEPENDENT_FRAGMENT_RE: Final = re.compile(
    r"^(?:それ|これ|あれ|そのこと|このこと|あのこと|それだけ|これだけ|あれだけ)$"
)
_OMITTED_COMPLETION_FRAGMENT_TOKENS: Final = frozenset(
    {
        "やった",
        "終わった",
        "終わらせた",
        "終えた",
        "完了した",
        "仕上げた",
        "それ",
        "これ",
        "あれ",
        "そのこと",
        "このこと",
        "あのこと",
        "それだけ",
        "これだけ",
        "あれだけ",
    }
)
_FRAGMENT_SEPARATOR_RE: Final = re.compile(
    r"[\s\u3000、,。．.!！?？]+"
)
_COMPLETION_RE: Final = re.compile(
    r"(?:終わった|終わらせた|終えた|完了した|仕上げた)"
)
_RELOCATION_RE: Final = re.compile(r"移した")
_UNSAFE_IDENTITY_RE: Final = re.compile(
    r"(?:けれど|だけど|でも|一方|反面|かもしれ|わから|分から|不明|"
    r"迷[いうっえおわ]|できない|出来ない|しない|しなかった|せず|"
    r"終わらない|移さない)"
)
_TIME_MARKERS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("day_before_yesterday", re.compile(r"一昨日")),
    ("yesterday", re.compile(r"昨日")),
    ("today", re.compile(r"今日")),
    ("tomorrow", re.compile(r"明日")),
    ("morning", re.compile(r"(?:今朝|朝)")),
    ("noon", re.compile(r"(?:昼|正午)")),
    ("night", re.compile(r"(?:今夜|夜)")),
    ("am", re.compile(r"午前")),
    ("pm", re.compile(r"午後")),
    ("last_week", re.compile(r"先週")),
    ("this_week", re.compile(r"今週")),
    ("next_week", re.compile(r"来週")),
    ("last_month", re.compile(r"先月")),
    ("this_month", re.compile(r"今月")),
    ("next_month", re.compile(r"来月")),
)
_QUANTIFIER_RE: Final = re.compile(
    r"(?:一つ|二つ|三つ|四つ|五つ|ひとつ|ふたつ|みっつ|\d+つ|"
    r"一件|二件|三件|\d+件|一通目|二通目|三通目|\d+通目)"
)
_ARGUMENT_RE: Final = re.compile(
    r"([^\s\u3000、,。．.!！?？「」『』（）()をへにがは]+)(を|が)"
)
_COMPLETION_ARGUMENT_RE: Final = re.compile(
    r"([^\s\u3000、,。．.!！?？「」『』（）()]+?)(を|が)"
)
_TOPIC_ANCHOR_RE: Final = re.compile(
    r"([^\s\u3000、,。．.!！?？「」『』（）()は]+)は"
)
_DESTINATION_RE: Final = re.compile(
    r"([^\s\u3000、,。．.!！?？「」『』（）()をへにがは]+)(?:へ|に)"
)
_NON_ARGUMENT_ANCHORS: Final = frozenset(
    {"今日", "昨日", "明日", "朝", "昼", "夜", "今", "それ", "これ", "あれ"}
)
_LOCATION_SEMANTIC_CLASSES: Final[
    tuple[tuple[str, re.Pattern[str], re.Pattern[str]], ...]
] = (
    (
        "bright_location",
        re.compile(r"^(?:明るい場所|日の当たる場所|日当たりのよい場所|光の入る場所)$"),
        re.compile(r"^(?:窓辺|窓際|窓のそば|日向|ベランダ)$"),
    ),
)

# This is deliberately a small, closed decomposition grammar.  A comma alone
# is not a semantic boundary: the left side must end in an explicit Japanese
# connective and both sides must contain a predicate-sized fragment.  The
# adapter is used only when Grounded has one required text nucleus and no
# relation owner for that nucleus, so it cannot compete with an existing
# Grounded relation analysis.
_TWO_PREDICATE_CONNECTIVE_RE: Final = re.compile(
    r"^(?P<left>.{4,}?(?P<connector>後になると|けれど|だけど|のに|けど|て|で))、"
    r"(?P<right>.{4,})$"
)
_PREDICATE_SIGNAL_RE: Final = re.compile(
    r"(?:ない|なかった|でき|出来|なる|なった|する|した|感じ|思|気が|"
    r"不安|寂し|嬉し|楽しか|軽い|せわし|落ち着|ずれ|入っ|決め|帰っ|"
    r"たい|たかった|だろう|のか|はず)"
)
_POSITIVE_SIGNAL_RE: Final = re.compile(
    r"(?:嬉し|楽しか|喜|安心|ほっと|軽い|よかった|良かった|穏やか|満足)"
)
_NEGATIVE_SIGNAL_RE: Final = re.compile(
    r"(?:不安|寂し|悲し|怖|つら|辛|苦し|しんど|せわし|落ち着かな|"
    r"嫌|怒|困|迷|後悔)"
)
_FEELING_SIGNAL_RE: Final = re.compile(
    r"(?:気持ち|気分|気がする|感じ|嬉し|楽しか|不安|寂し|悲し|怖|"
    r"つら|辛|苦し|しんど|せわし|落ち着|安心|ほっと)"
)
_CHANGE_SIGNAL_RE: Final = re.compile(
    r"(?:ずれ|変わ|変え|なった|なる|移|減|増|軽く|重く)"
)
_ACTION_SIGNAL_RE: Final = re.compile(
    r"(?:決め|選|調べ|書|送|話|休|開け|閉め|始め|終え|やっ|した|する)"
)
_INTENTION_SIGNAL_RE: Final = re.compile(
    r"(?:たい|つもり|ようと思|(?:する|やる|行く|休む)予定)"
)
_EXPLICIT_WHY_RE: Final = re.compile(r"(?:どうして|なんで|なぜ|何故)")
_UNVERBALIZED_RE: Final = re.compile(
    r"(?:言葉にできない|言葉に出来ない|わからない|分からない|まだ不明)"
)
_COMPARATIVE_UNCERTAINTY_RE: Final = re.compile(
    r"(?:別の選択|ほうがよかった|方がよかった|選ばなかったほう|選ばなかった方)"
)
_OPEN_DECISION_RE: Final = re.compile(
    r"(?:決められない|判断できない|選べない|迷(?:う|って|い))"
)
_UNSPECIFIED_RETURN_RE: Final = re.compile(r"帰ってから")
_RETURN_LOCATION_RE: Final = re.compile(
    r"(?:家|部屋|職場|学校|店|会場|場所|実家|旅行|外)\s*(?:に|へ)?帰ってから"
)
_PAST_SIGNAL_RE: Final = re.compile(r"(?:かった|だった|した|なった|決めた|帰った)")
_CURRENT_SIGNAL_RE: Final = re.compile(r"(?:今日|今|ずっと|まだ|現在|朝から)")
_FUTURE_SIGNAL_RE: Final = re.compile(
    r"(?:明日|これから|今度|(?:する|やる|行く|休む)予定|たい|つもり)"
)
_MAX_DECOMPOSED_UNITS_PER_PARENT: Final = 4


class GroundedSemanticRestatementError(ValueError):
    """Fail-closed adapter error containing only a stable machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class GroundedSemanticRestatementRelationWitness:
    relation_id: str
    endpoint_semantic_relation: EndpointSemanticRelation
    semantic_restatement_unit_nucleus_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedSemanticUnitWitness:
    """One source-bound unit recovered from a collapsed Grounded nucleus."""

    unit_id: str
    parent_nucleus_id: str
    source_span_id: str
    start_index: int
    end_index: int
    source_fragment_sha256: str
    connective_code: str
    unit_role: Literal["antecedent", "consequent"]
    kind: SemanticUnitKind
    source_predicate_kind: str
    polarity: Literal["positive", "negative", "mixed", "neutral"]
    source_modality: Literal[
        "fact",
        "feeling",
        "wish",
        "intention",
        "possibility",
        "uncertain",
    ]
    source_time_scope: str
    required: bool
    forbidden_claim_codes: tuple[str, ...]


@dataclass(frozen=True)
class GroundedSemanticLinkWitness:
    """A typed relation between two recovered semantic units."""

    link_id: str
    source_span_id: str
    connective_code: str
    relation_type: SemanticLinkType
    relation_direction: Literal["source_to_target", "bidirectional"]
    from_unit_id: str
    to_unit_id: str
    required: bool
    forbidden_claim_codes: tuple[str, ...]


@dataclass(frozen=True)
class GroundedExplicitUnknownWitness:
    """An unknown explicitly expressed by the current source body."""

    unknown_id: str
    source_span_id: str
    dimension: str
    affected_unit_ids: tuple[str, ...]
    required: bool


_OpenSlotDimension = Literal[
    "explicit_cause_unknown",
    "explicit_unverbalized_unknown",
    "explicit_choice_decision_unknown",
    "explicit_temporal_referent_unknown",
    "explicit_referent_unknown",
]
_OpenSlotArgumentCompleteness = Literal[
    "not_applicable",
    "complete",
    "referent_open",
]
_OpenSlotResolutionBasis = Literal[
    "exact_parent_governor",
    "exact_semantic_unit",
    "exact_required_user_stated_relation_antecedent",
    "exact_required_temporal_relation_antecedent",
    "exact_required_semantic_link_antecedent",
    "exact_response_governor",
]


@dataclass(frozen=True, slots=True, repr=False)
class _GroundedFormalSourceParse:
    """Closed, body-free projection of the existing source grammar."""

    source_span_id: str
    cause_marker_range: tuple[int, int] | None
    unverbalized_marker_range: tuple[int, int] | None
    decision_marker_range: tuple[int, int] | None
    temporal_marker_range: tuple[int, int] | None
    completion_argument_completeness: _OpenSlotArgumentCompleteness
    completion_marker_range: tuple[int, int] | None
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class _GroundedOpenSlotMarker:
    """Private body-free marker resolved before public unknown materialisation."""

    marker_id: str
    source_span_id: str
    dimension: _OpenSlotDimension
    governor_nucleus_id: str
    antecedent_nucleus_ids: tuple[str, ...]
    affected_unit_ids: tuple[str, ...]
    argument_completeness: _OpenSlotArgumentCompleteness
    resolution_basis: _OpenSlotResolutionBasis
    required: bool
    body_free: bool = True


@dataclass(frozen=True)
class GroundedSemanticRestatementWitness:
    schema_version: str
    adapter_version: str
    plan_binding_sha256: str
    relations: tuple[GroundedSemanticRestatementRelationWitness, ...]
    semantic_units: tuple[GroundedSemanticUnitWitness, ...]
    semantic_links: tuple[GroundedSemanticLinkWitness, ...]
    explicit_unknowns: tuple[GroundedExplicitUnknownWitness, ...]
    witness_sha256: str
    body_free: bool = True

    def as_body_free_meta(self) -> dict[str, Any]:
        """Return the closed JSON projection; source bodies never enter it."""

        return {
            "schema_version": self.schema_version,
            "adapter_version": self.adapter_version,
            "plan_binding_sha256": self.plan_binding_sha256,
            "relations": [
                {
                    "relation_id": row.relation_id,
                    "endpoint_semantic_relation": (
                        row.endpoint_semantic_relation
                    ),
                    "semantic_restatement_unit_nucleus_ids": list(
                        row.semantic_restatement_unit_nucleus_ids
                    ),
                }
                for row in self.relations
            ],
            "semantic_units": [
                {
                    "unit_id": row.unit_id,
                    "parent_nucleus_id": row.parent_nucleus_id,
                    "source_span_id": row.source_span_id,
                    "start_index": row.start_index,
                    "end_index": row.end_index,
                    "source_fragment_sha256": row.source_fragment_sha256,
                    "connective_code": row.connective_code,
                    "unit_role": row.unit_role,
                    "kind": row.kind,
                    "source_predicate_kind": row.source_predicate_kind,
                    "polarity": row.polarity,
                    "source_modality": row.source_modality,
                    "source_time_scope": row.source_time_scope,
                    "required": row.required,
                    "forbidden_claim_codes": list(row.forbidden_claim_codes),
                }
                for row in self.semantic_units
            ],
            "semantic_links": [
                {
                    "link_id": row.link_id,
                    "source_span_id": row.source_span_id,
                    "connective_code": row.connective_code,
                    "relation_type": row.relation_type,
                    "relation_direction": row.relation_direction,
                    "from_unit_id": row.from_unit_id,
                    "to_unit_id": row.to_unit_id,
                    "required": row.required,
                    "forbidden_claim_codes": list(row.forbidden_claim_codes),
                }
                for row in self.semantic_links
            ],
            "explicit_unknowns": [
                {
                    "unknown_id": row.unknown_id,
                    "source_span_id": row.source_span_id,
                    "dimension": row.dimension,
                    "affected_unit_ids": list(row.affected_unit_ids),
                    "required": row.required,
                }
                for row in self.explicit_unknowns
            ],
            "witness_sha256": self.witness_sha256,
            "body_free": self.body_free,
        }


def _clean(value: Any) -> str:
    return re.sub(
        r"\s+", " ", str(value or "").replace("\u3000", " ")
    ).strip()


def _canonical_body_free(value: Any) -> Any:
    """Convert a body-free dataclass projection to strict canonical JSON."""

    if is_dataclass(value):
        return _canonical_body_free(asdict(value))
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        return format(value, ".17g")
    if isinstance(value, (tuple, list)):
        return [_canonical_body_free(item) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_body_free(item)
            for key, item in value.items()
        }
    raise GroundedSemanticRestatementError(
        "SEMANTIC_RESTATEMENT_PLAN_PROJECTION_INVALID"
    )


def _resolver_spans(resolver: EvidenceSpanResolver) -> tuple[Any, ...]:
    try:
        return tuple(resolver.resolve(span_id) for span_id in resolver.span_ids)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_RESOLVER_INVALID"
        ) from exc


def _reconstruct_text(spans: Sequence[Any], source_field: str) -> str:
    selected = [
        span
        for span in spans
        if getattr(span, "source_field", None) == source_field
        and type(getattr(span, "start_index", None)) is int
        and type(getattr(span, "end_index", None)) is int
        and span.start_index >= 0
        and span.end_index >= span.start_index
    ]
    if not selected:
        return ""
    output = ["。"] * max(span.end_index for span in selected)
    for span in selected:
        raw_text = str(getattr(span, "raw_text", ""))
        if len(raw_text) != span.end_index - span.start_index:
            raise GroundedSemanticRestatementError(
                "SEMANTIC_RESTATEMENT_RESOLVER_INVALID"
            )
        output[span.start_index : span.end_index] = list(raw_text)
    return "".join(output)


def _reconstructed_input_bundle(spans: Sequence[Any]) -> dict[str, Any]:
    emotion_types: list[str] = []
    detail_values = [
        _clean(getattr(span, "raw_text", ""))
        for span in spans
        if getattr(span, "source_field", None) == "emotion_details"
    ]
    fallback_values = [
        _clean(getattr(span, "raw_text", ""))
        for span in spans
        if getattr(span, "source_field", None) == "emotions"
    ]
    for value in detail_values or fallback_values:
        if value and value not in emotion_types:
            emotion_types.append(value)
    categories: list[str] = []
    for span in spans:
        if getattr(span, "source_field", None) != "category":
            continue
        value = _clean(getattr(span, "raw_text", ""))
        if value and value not in categories:
            categories.append(value)
    return {
        "thought_text": _reconstruct_text(spans, "memo"),
        "action_text": _reconstruct_text(spans, "memo_action"),
        "emotions": [
            {"type": value, "strength": "medium"}
            for value in emotion_types
        ],
        "categories": categories,
    }


def _validated_plan_and_spans(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[Any, ...]:
    if type(plan) is not GroundedObservationPlan:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_PLAN_INVALID"
        )
    try:
        plan_issues = validate_grounded_observation_plan(plan, resolver)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_PLAN_INVALID"
        ) from exc
    if plan_issues:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_PLAN_INVALID"
        )
    spans = _resolver_spans(resolver)
    try:
        recomputed_plan = build_grounded_observation_plan(
            _reconstructed_input_bundle(spans),
            evidence_spans=spans,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_PLAN_RESOLVER_MISMATCH"
        ) from exc
    if recomputed_plan != plan:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_PLAN_RESOLVER_MISMATCH"
        )
    return spans


def _plan_binding_sha256(
    plan: GroundedObservationPlan,
    spans: Sequence[Any],
) -> str:
    evidence_commitments = [
        {
            "span_id": str(getattr(span, "span_id", "")),
            "source_field": str(getattr(span, "source_field", "")),
            "start_index": int(getattr(span, "start_index", -1)),
            "end_index": int(getattr(span, "end_index", -1)),
            "detected_type": str(getattr(span, "detected_type", "")),
            "raw_text_sha256": artifact_sha256(
                {"raw_text": str(getattr(span, "raw_text", ""))}
            ),
        }
        for span in spans
    ]
    return artifact_sha256(
        {
            "schema_version": GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA,
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "grounded_plan_body_free_meta": _canonical_body_free(
                plan.as_body_free_meta()
            ),
            "evidence_commitments": evidence_commitments,
        }
    )


def _source_text(
    nucleus: GroundedSemanticNucleus,
    span_by_id: Mapping[str, Any],
) -> str:
    return " ".join(
        _clean(getattr(span_by_id.get(span_id), "raw_text", ""))
        for span_id in nucleus.source_span_ids
        if span_id in span_by_id
    )


def _time_markers(text: str) -> frozenset[str]:
    return frozenset(
        code for code, pattern in _TIME_MARKERS if pattern.search(text)
    )


def _anchors(pattern: re.Pattern[str], text: str) -> frozenset[str]:
    return frozenset(
        value
        for value in (_clean(item) for item in pattern.findall(text))
        if value and value not in _NON_ARGUMENT_ANCHORS
    )


def _location_compatible(left: str, right: str) -> bool:
    if left == right:
        return True
    return any(
        (
            generic.fullmatch(left) is not None
            and specific.fullmatch(right) is not None
        )
        or (
            generic.fullmatch(right) is not None
            and specific.fullmatch(left) is not None
        )
        for _class_code, generic, specific in _LOCATION_SEMANTIC_CLASSES
    )


def _is_closed_omitted_completion_fragment(text: str) -> bool:
    tokens = tuple(
        token
        for token in _FRAGMENT_SEPARATOR_RE.split(_clean(text))
        if token
    )
    return bool(tokens) and all(
        token in _OMITTED_COMPLETION_FRAGMENT_TOKENS
        for token in tokens
    )


def _completion_argument_roles(
    text: str,
) -> tuple[frozenset[str], frozenset[str]]:
    subjects: set[str] = set()
    objects: set[str] = set()
    for raw_value, particle in _COMPLETION_ARGUMENT_RE.findall(text):
        value = _clean(raw_value)
        if not value or value in _NON_ARGUMENT_ANCHORS:
            continue
        if particle == "が":
            subjects.add(value)
        else:
            objects.add(value)
    return frozenset(subjects), frozenset(objects)


def _relocation_argument_roles(
    text: str,
) -> tuple[frozenset[str], frozenset[str]]:
    subjects: set[str] = set()
    objects: set[str] = set()
    for raw_value, particle in _ARGUMENT_RE.findall(text):
        value = _clean(raw_value)
        if not value or value in _NON_ARGUMENT_ANCHORS:
            continue
        if particle == "が":
            subjects.add(value)
        else:
            objects.add(value)
    return frozenset(subjects), frozenset(objects)


def _completed_event_is_same(left_text: str, right_text: str) -> bool:
    if not (_COMPLETION_RE.search(left_text) and _COMPLETION_RE.search(right_text)):
        return False
    left_subjects, left_objects = _completion_argument_roles(left_text)
    right_subjects, right_objects = _completion_argument_roles(right_text)
    left_topics = _anchors(_TOPIC_ANCHOR_RE, left_text)
    right_topics = _anchors(_TOPIC_ANCHOR_RE, right_text)
    left_explicit = left_subjects | left_objects
    right_explicit = right_subjects | right_objects
    if left_explicit and right_explicit:
        return bool(
            left_subjects == right_subjects
            and left_objects == right_objects
            and left_topics == right_topics
        )
    if left_explicit or right_explicit:
        explicit = left_explicit or right_explicit
        explicit_topics = left_topics if left_explicit else right_topics
        topic_only = right_topics if left_explicit else left_topics
        return bool(
            len(explicit) == 1
            and not explicit_topics
            and topic_only == explicit
        )
    if left_topics or right_topics:
        return bool(left_topics and left_topics == right_topics)
    return _is_closed_omitted_completion_fragment(
        left_text
    ) and _is_closed_omitted_completion_fragment(right_text)


def _relocation_event_is_same(left_text: str, right_text: str) -> bool:
    if not (_RELOCATION_RE.search(left_text) and _RELOCATION_RE.search(right_text)):
        return False
    left_subjects, left_objects = _relocation_argument_roles(left_text)
    right_subjects, right_objects = _relocation_argument_roles(right_text)
    if (
        not left_objects
        or left_objects != right_objects
        or left_subjects != right_subjects
        or _anchors(_TOPIC_ANCHOR_RE, left_text)
        != _anchors(_TOPIC_ANCHOR_RE, right_text)
    ):
        return False
    left_destinations = _anchors(_DESTINATION_RE, left_text)
    right_destinations = _anchors(_DESTINATION_RE, right_text)
    if len(left_destinations) != 1 or len(right_destinations) != 1:
        return False
    return _location_compatible(
        next(iter(left_destinations)),
        next(iter(right_destinations)),
    )


def _endpoint_semantic_relation(
    relation: GroundedSemanticRelation,
    left: GroundedSemanticNucleus,
    right: GroundedSemanticNucleus,
    *,
    span_by_id: Mapping[str, Any],
) -> EndpointSemanticRelation:
    if (
        relation.type != "uncertain_connection"
        or relation.grounding_kind != "bounded_structural_inference"
        or "whole_input_source_order" not in relation.source_relation_ids
    ):
        return "distinct_meanings"
    if {
        frozenset(left.source_fields),
        frozenset(right.source_fields),
    } != {frozenset({"memo"}), frozenset({"memo_action"})}:
        return "distinct_meanings"
    left_text = _source_text(left, span_by_id)
    right_text = _source_text(right, span_by_id)
    if not left_text or not right_text:
        return "distinct_meanings"
    if _UNSAFE_IDENTITY_RE.search(left_text) or _UNSAFE_IDENTITY_RE.search(right_text):
        return "distinct_meanings"
    if (left.semantic_frame.polarity == "negative") != (
        right.semantic_frame.polarity == "negative"
    ):
        return "distinct_meanings"
    left_times, right_times = _time_markers(left_text), _time_markers(right_text)
    if left_times and right_times and not left_times & right_times:
        return "distinct_meanings"
    left_quantifiers = frozenset(_QUANTIFIER_RE.findall(left_text))
    right_quantifiers = frozenset(_QUANTIFIER_RE.findall(right_text))
    if (left_quantifiers or right_quantifiers) and left_quantifiers != right_quantifiers:
        return "distinct_meanings"
    if _completed_event_is_same(left_text, right_text) or _relocation_event_is_same(
        left_text, right_text
    ):
        return "semantic_restatement"
    return "distinct_meanings"


def _semantic_unit_ids(
    relation: GroundedSemanticRelation,
    status: EndpointSemanticRelation,
    *,
    plan: GroundedObservationPlan,
    span_by_id: Mapping[str, Any],
    span_order: Mapping[str, int],
) -> tuple[str, ...]:
    if status != "semantic_restatement":
        return ()
    endpoints = {relation.from_nucleus_id, relation.to_nucleus_id}
    endpoint_positions = [
        span_order[span_id]
        for nucleus in plan.nuclei
        if nucleus.nucleus_id in endpoints
        for span_id in nucleus.source_span_ids
        if span_id in span_order
    ]
    if not endpoint_positions:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_ENDPOINT_UNRESOLVED"
        )
    lower, upper = min(endpoint_positions), max(endpoint_positions)
    members: list[str] = []
    for nucleus in plan.nuclei:
        if nucleus.nucleus_id in endpoints:
            members.append(nucleus.nucleus_id)
            continue
        if not nucleus.source_fields or not set(nucleus.source_fields) <= _TEXT_SOURCE_FIELDS:
            continue
        positions = [
            span_order[span_id]
            for span_id in nucleus.source_span_ids
            if span_id in span_order
        ]
        if not positions or not all(lower < item < upper for item in positions):
            continue
        if _DEPENDENT_FRAGMENT_RE.fullmatch(_source_text(nucleus, span_by_id)):
            members.append(nucleus.nucleus_id)
    return tuple(members)


def _relation_witnesses(
    plan: GroundedObservationPlan,
    spans: Sequence[Any],
) -> tuple[GroundedSemanticRestatementRelationWitness, ...]:
    span_by_id = {str(getattr(span, "span_id", "")): span for span in spans}
    span_order = {span_id: index for index, span_id in enumerate(span_by_id)}
    nucleus_by_id = {row.nucleus_id: row for row in plan.nuclei}
    witnesses: list[GroundedSemanticRestatementRelationWitness] = []
    for relation in sorted(plan.relations, key=lambda row: row.relation_id):
        left = nucleus_by_id.get(relation.from_nucleus_id)
        right = nucleus_by_id.get(relation.to_nucleus_id)
        if left is None or right is None:
            raise GroundedSemanticRestatementError(
                "SEMANTIC_RESTATEMENT_ENDPOINT_UNRESOLVED"
            )
        status = _endpoint_semantic_relation(
            relation, left, right, span_by_id=span_by_id
        )
        witnesses.append(
            GroundedSemanticRestatementRelationWitness(
                relation_id=relation.relation_id,
                endpoint_semantic_relation=status,
                semantic_restatement_unit_nucleus_ids=_semantic_unit_ids(
                    relation,
                    status,
                    plan=plan,
                    span_by_id=span_by_id,
                    span_order=span_order,
                ),
            )
        )
    return tuple(witnesses)


def _connective_code(connector: str) -> str:
    return {
        "のに": "CONTRAST_DESPITE",
        "けれど": "CONTRAST_BUT",
        "だけど": "CONTRAST_BUT",
        "けど": "CONTRAST_BUT",
        "後になると": "POST_EVENT_WHEN",
        "て": "EXPLICIT_CONJUNCTIVE_TE",
        "で": "EXPLICIT_CONJUNCTIVE_DE",
    }[connector]


def _unit_kind(text: str, parent: GroundedSemanticNucleus) -> SemanticUnitKind:
    if _FEELING_SIGNAL_RE.search(text):
        return "change" if _CHANGE_SIGNAL_RE.search(text) else "reaction"
    if _INTENTION_SIGNAL_RE.search(text):
        return "wish"
    if _CHANGE_SIGNAL_RE.search(text):
        return "change"
    if _ACTION_SIGNAL_RE.search(text):
        return "action"
    if parent.kind in {
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
    }:
        return parent.kind
    return "other_explicit"


def _unit_polarity(
    text: str, parent: GroundedSemanticNucleus
) -> Literal["positive", "negative", "mixed", "neutral"]:
    positive = bool(_POSITIVE_SIGNAL_RE.search(text))
    negative = bool(_NEGATIVE_SIGNAL_RE.search(text))
    if positive and negative:
        return "mixed"
    if positive:
        return "positive"
    if negative:
        return "negative"
    parent_polarity = str(parent.semantic_frame.polarity)
    return parent_polarity if parent_polarity in {
        "positive", "negative", "mixed", "neutral"
    } else "neutral"


def _unit_modality(
    text: str, kind: SemanticUnitKind
) -> Literal["fact", "feeling", "wish", "intention", "possibility", "uncertain"]:
    if kind in {"reaction", "change"} and _FEELING_SIGNAL_RE.search(text):
        return "feeling"
    if kind == "wish":
        return "wish"
    if kind == "action" and _INTENTION_SIGNAL_RE.search(text):
        return "intention"
    if _UNVERBALIZED_RE.search(text):
        return "uncertain"
    return "fact"


def _unit_time_scope(text: str) -> str:
    if _FUTURE_SIGNAL_RE.search(text) and not _PAST_SIGNAL_RE.search(text):
        return "intended_future"
    if _PAST_SIGNAL_RE.search(text):
        return "reported_past"
    if _CURRENT_SIGNAL_RE.search(text):
        return "current_input"
    return "current_input"


def _unit_id(
    *, parent_nucleus_id: str, source_span_id: str, start: int, end: int,
    fragment_sha256: str, role: str,
) -> str:
    digest = artifact_sha256(
        {
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "parent_nucleus_id": parent_nucleus_id,
            "source_span_id": source_span_id,
            "start_index": start,
            "end_index": end,
            "source_fragment_sha256": fragment_sha256,
            "unit_role": role,
        }
    )[:24]
    return f"semantic_unit:u{digest}"


def _semantic_decomposition(
    plan: GroundedObservationPlan,
    spans: Sequence[Any],
) -> tuple[
    tuple[GroundedSemanticUnitWitness, ...],
    tuple[GroundedSemanticLinkWitness, ...],
]:
    """Recover only closed, source-explicit two-predicate structures."""

    required = frozenset(plan.coverage_requirements.required_nucleus_ids)
    required_text = [
        row
        for row in plan.nuclei
        if row.nucleus_id in required
        and set(row.source_fields) <= _TEXT_SOURCE_FIELDS
        and len(row.source_span_ids) == 1
    ]
    if len(required_text) != 1 or plan.relations:
        return (), ()
    parent = required_text[0]
    span_by_id = {str(getattr(row, "span_id", "")): row for row in spans}
    span = span_by_id.get(parent.source_span_ids[0])
    if span is None or getattr(span, "source_field", None) not in _TEXT_SOURCE_FIELDS:
        return (), ()
    raw_text = str(getattr(span, "raw_text", ""))
    match = _TWO_PREDICATE_CONNECTIVE_RE.fullmatch(raw_text)
    if match is None:
        return (), ()
    left = match.group("left")
    right = match.group("right")
    if not _PREDICATE_SIGNAL_RE.search(left) or not _PREDICATE_SIGNAL_RE.search(right):
        return (), ()
    connector = match.group("connector")
    separator_index = match.start("right") - 1
    fragments = (
        ("antecedent", left, 0, separator_index),
        ("consequent", right, match.start("right"), len(raw_text)),
    )
    if len(fragments) > _MAX_DECOMPOSED_UNITS_PER_PARENT:
        raise GroundedSemanticRestatementError("SEMANTIC_UNIT_BOUND_EXCEEDED")
    units: list[GroundedSemanticUnitWitness] = []
    for role, fragment, start, end in fragments:
        fragment_sha = artifact_sha256({"source_fragment": fragment})
        kind = _unit_kind(fragment, parent)
        unit_id = _unit_id(
            parent_nucleus_id=parent.nucleus_id,
            source_span_id=str(span.span_id),
            start=start,
            end=end,
            fragment_sha256=fragment_sha,
            role=role,
        )
        units.append(
            GroundedSemanticUnitWitness(
                unit_id=unit_id,
                parent_nucleus_id=parent.nucleus_id,
                source_span_id=str(span.span_id),
                start_index=start,
                end_index=end,
                source_fragment_sha256=fragment_sha,
                connective_code=_connective_code(connector),
                unit_role=role,  # type: ignore[arg-type]
                kind=kind,
                source_predicate_kind=(
                    "feeling"
                    if kind in {"reaction", "change"}
                    and _FEELING_SIGNAL_RE.search(fragment)
                    else "action" if kind in {"action", "wish"} else "event"
                ),
                polarity=_unit_polarity(fragment, parent),
                source_modality=_unit_modality(fragment, kind),
                source_time_scope=_unit_time_scope(fragment),
                required=True,
                forbidden_claim_codes=(
                    "NO_SEMANTIC_UNIT_COLLAPSE",
                    "NO_SOURCE_PREDICATE_INVENTION",
                ),
            )
        )
    left_unit, right_unit = units
    if connector == "後になると" or (
        connector in {"のに", "けれど", "だけど", "けど"}
        and _UNSPECIFIED_RETURN_RE.search(right)
    ):
        relation_type: SemanticLinkType = "precedes"
        direction: Literal["source_to_target", "bidirectional"] = "source_to_target"
    elif connector in {"のに", "けれど", "だけど", "けど"}:
        relation_type = "coexists_with"
        direction = "bidirectional"
    else:
        relation_type = "coexists_with"
        direction = "bidirectional"
    link_digest = artifact_sha256(
        {
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "source_span_id": str(span.span_id),
            "connective_code": _connective_code(connector),
            "relation_type": relation_type,
            "relation_direction": direction,
            "from_unit_id": left_unit.unit_id,
            "to_unit_id": right_unit.unit_id,
        }
    )[:24]
    link = GroundedSemanticLinkWitness(
        link_id=f"semantic_link:r{link_digest}",
        source_span_id=str(span.span_id),
        connective_code=_connective_code(connector),
        relation_type=relation_type,
        relation_direction=direction,
        from_unit_id=left_unit.unit_id,
        to_unit_id=right_unit.unit_id,
        required=True,
        forbidden_claim_codes=(
            "NO_RELATION_DIRECTION_REVERSAL",
            "NO_CAUSAL_GUARANTEE",
        ),
    )
    return tuple(units), (link,)


def _formal_source_parse(
    source_span_id: str,
    text: str,
) -> _GroundedFormalSourceParse:
    """Project the established grammar once; retain no source bytes."""

    cause = _EXPLICIT_WHY_RE.search(text)
    if cause is None and "なんとなく" in text:
        cause_start = text.index("なんとなく")
        cause_range = (cause_start, cause_start + len("なんとなく"))
    else:
        cause_range = cause.span() if cause is not None else None
    decision_candidates = tuple(
        row
        for row in (
            _COMPARATIVE_UNCERTAINTY_RE.search(text),
            _OPEN_DECISION_RE.search(text),
        )
        if row is not None
    )
    decision = (
        min(decision_candidates, key=lambda row: (row.start(), row.end()))
        if decision_candidates
        else None
    )
    temporal = _UNSPECIFIED_RETURN_RE.search(text)
    if temporal is not None and _RETURN_LOCATION_RE.search(text) is not None:
        temporal = None
    completion = _COMPLETION_RE.search(text)
    if completion is None:
        completeness: _OpenSlotArgumentCompleteness = "not_applicable"
    else:
        completion_subjects, completion_objects = _completion_argument_roles(text)
        completion_topics = _anchors(_TOPIC_ANCHOR_RE, text)
        completeness = (
            "referent_open"
            if not completion_subjects
            and not completion_objects
            and not completion_topics
            and _is_closed_omitted_completion_fragment(text)
            else "complete"
        )
    return _GroundedFormalSourceParse(
        source_span_id=source_span_id,
        cause_marker_range=cause_range,
        unverbalized_marker_range=(
            match.span() if (match := _UNVERBALIZED_RE.search(text)) else None
        ),
        decision_marker_range=(decision.span() if decision is not None else None),
        temporal_marker_range=(temporal.span() if temporal is not None else None),
        completion_argument_completeness=completeness,
        completion_marker_range=(
            completion.span() if completion is not None else None
        ),
        body_free=True,
    )


def _expanded_owner_ids(
    nucleus_id: str,
    units_by_parent: Mapping[str, tuple[GroundedSemanticUnitWitness, ...]],
) -> tuple[str, ...]:
    return tuple(
        row.unit_id for row in units_by_parent.get(nucleus_id, ())
    ) or (nucleus_id,)


def _exact_marker_owner_ids(
    *,
    parent_nucleus_id: str,
    source_span_id: str,
    marker_range: tuple[int, int],
    units_by_parent: Mapping[str, tuple[GroundedSemanticUnitWitness, ...]],
) -> tuple[tuple[str, ...], _OpenSlotResolutionBasis]:
    units = units_by_parent.get(parent_nucleus_id, ())
    if not units:
        return (parent_nucleus_id,), "exact_parent_governor"
    start, end = marker_range
    candidates = tuple(
        row.unit_id
        for row in units
        if row.source_span_id == source_span_id
        and row.start_index <= start
        and end <= row.end_index
    )
    if len(candidates) != 1:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_OPEN_SLOT_AMBIGUOUS"
        )
    return candidates, "exact_semantic_unit"


def _exact_user_stated_antecedent(
    *,
    plan: GroundedObservationPlan,
    parent_nucleus_id: str,
    source_span_id: str,
    units_by_parent: Mapping[str, tuple[GroundedSemanticUnitWitness, ...]],
) -> tuple[str, tuple[str, ...]] | None:
    required_relation_ids = frozenset(
        plan.coverage_requirements.required_relation_ids
    )
    candidates = tuple(
        row
        for row in plan.relations
        if row.relation_id in required_relation_ids
        and row.grounding_kind == "user_stated_relation"
        and row.to_nucleus_id == parent_nucleus_id
        and source_span_id in row.source_span_ids
    )
    if len(candidates) > 1:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_OPEN_SLOT_AMBIGUOUS"
        )
    if not candidates:
        return None
    relation = candidates[0]
    return relation.from_nucleus_id, _expanded_owner_ids(
        relation.from_nucleus_id,
        units_by_parent,
    )


def _has_required_target_relation(
    *,
    plan: GroundedObservationPlan,
    parent_nucleus_id: str,
    source_span_id: str,
) -> bool:
    required_relation_ids = frozenset(
        plan.coverage_requirements.required_relation_ids
    )
    return any(
        row.relation_id in required_relation_ids
        and row.to_nucleus_id == parent_nucleus_id
        and source_span_id in row.source_span_ids
        for row in plan.relations
    )


def _exact_semantic_link_antecedent(
    *,
    marker_owner_ids: Sequence[str],
    source_span_id: str,
    semantic_links: Sequence[GroundedSemanticLinkWitness],
    relation_type: SemanticLinkType | None = None,
) -> tuple[str, ...] | None:
    if len(marker_owner_ids) != 1:
        return None
    target_id = marker_owner_ids[0]
    candidates = tuple(
        row
        for row in semantic_links
        if row.required is True
        and row.source_span_id == source_span_id
        and row.to_unit_id == target_id
        and (relation_type is None or row.relation_type == relation_type)
    )
    if len(candidates) > 1:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_OPEN_SLOT_AMBIGUOUS"
        )
    return (candidates[0].from_unit_id,) if candidates else None


def _exact_temporal_antecedent(
    *,
    plan: GroundedObservationPlan,
    parent_nucleus_id: str,
    source_span_id: str,
    marker_owner_ids: Sequence[str],
    units_by_parent: Mapping[str, tuple[GroundedSemanticUnitWitness, ...]],
    semantic_links: Sequence[GroundedSemanticLinkWitness],
) -> tuple[
    str,
    tuple[str, ...],
    _OpenSlotResolutionBasis,
] | None:
    required_relation_ids = frozenset(
        plan.coverage_requirements.required_relation_ids
    )
    plan_candidates = tuple(
        row
        for row in plan.relations
        if row.relation_id in required_relation_ids
        and row.type == "temporal_before_after"
        and row.to_nucleus_id == parent_nucleus_id
        and source_span_id in row.source_span_ids
    )
    semantic_candidates = tuple(
        row
        for row in semantic_links
        if row.required is True
        and row.relation_type == "precedes"
        and row.source_span_id == source_span_id
        and len(marker_owner_ids) == 1
        and row.to_unit_id == marker_owner_ids[0]
    )
    if len(plan_candidates) + len(semantic_candidates) > 1:
        raise GroundedSemanticRestatementError(
            "SEMANTIC_RESTATEMENT_OPEN_SLOT_AMBIGUOUS"
        )
    if plan_candidates:
        relation = plan_candidates[0]
        return (
            relation.from_nucleus_id,
            _expanded_owner_ids(relation.from_nucleus_id, units_by_parent),
            "exact_required_temporal_relation_antecedent",
        )
    if semantic_candidates:
        link = semantic_candidates[0]
        return (
            parent_nucleus_id,
            (link.from_unit_id,),
            "exact_required_semantic_link_antecedent",
        )
    return None


def _completion_open_slot_markers(
    *,
    plan: GroundedObservationPlan,
    formal_by_parent: Mapping[str, _GroundedFormalSourceParse],
    relations: Sequence[GroundedSemanticRestatementRelationWitness],
    units_by_parent: Mapping[str, tuple[GroundedSemanticUnitWitness, ...]],
) -> tuple[_GroundedOpenSlotMarker, ...]:
    open_parent_ids = tuple(
        sorted(
            parent_id
            for parent_id, parsed in formal_by_parent.items()
            if parsed.completion_argument_completeness == "referent_open"
        )
    )
    if not open_parent_ids:
        return ()
    components = tuple(
        frozenset(row.semantic_restatement_unit_nucleus_ids)
        for row in relations
        if row.endpoint_semantic_relation == "semantic_restatement"
        and row.semantic_restatement_unit_nucleus_ids
    )
    grouped: dict[tuple[str, ...], list[str]] = {}
    for parent_id in open_parent_ids:
        memberships = tuple(
            component for component in components if parent_id in component
        )
        if len(memberships) > 1:
            raise GroundedSemanticRestatementError(
                "SEMANTIC_RESTATEMENT_OPEN_SLOT_AMBIGUOUS"
            )
        key = tuple(sorted(memberships[0])) if memberships else (parent_id,)
        grouped.setdefault(key, []).append(parent_id)

    reception_plan = plan.response_plan.human_reception_plan
    authority_sets = tuple(
        frozenset(values)
        for values in (
            plan.response_plan.primary_nucleus_ids,
            plan.response_plan.human_follow_target_ids,
            tuple(
                nucleus_id
                for move in (
                    reception_plan.moves if reception_plan is not None else ()
                )
                if move.required is True
                for nucleus_id in move.target_nucleus_ids
            ),
        )
        if values
    )
    result: list[_GroundedOpenSlotMarker] = []
    for component_key in sorted(grouped):
        candidates = tuple(sorted(grouped[component_key]))
        if len(candidates) == 1:
            governor_id = candidates[0]
            basis: _OpenSlotResolutionBasis = "exact_parent_governor"
        else:
            scoped_authorities = tuple(
                values & set(candidates)
                for values in authority_sets
                if values & set(candidates)
            )
            exact = (
                set.intersection(*(set(values) for values in scoped_authorities))
                if scoped_authorities
                else set()
            )
            if len(exact) != 1:
                raise GroundedSemanticRestatementError(
                    "SEMANTIC_RESTATEMENT_OPEN_SLOT_AMBIGUOUS"
                )
            governor_id = next(iter(exact))
            basis = "exact_response_governor"
        parsed = formal_by_parent[governor_id]
        affected_ids = _expanded_owner_ids(governor_id, units_by_parent)
        identity = {
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "source_span_id": parsed.source_span_id,
            "dimension": "explicit_referent_unknown",
            "affected_unit_ids": list(affected_ids),
        }
        result.append(
            _GroundedOpenSlotMarker(
                marker_id="open_slot:m" + artifact_sha256(identity)[:24],
                source_span_id=parsed.source_span_id,
                dimension="explicit_referent_unknown",
                governor_nucleus_id=governor_id,
                antecedent_nucleus_ids=(),
                affected_unit_ids=affected_ids,
                argument_completeness="referent_open",
                resolution_basis=basis,
                required=True,
                body_free=True,
            )
        )
    return tuple(result)


def _explicit_unknown_witnesses(
    plan: GroundedObservationPlan,
    spans: Sequence[Any],
    units: Sequence[GroundedSemanticUnitWitness],
    relations: Sequence[GroundedSemanticRestatementRelationWitness],
    semantic_links: Sequence[GroundedSemanticLinkWitness],
) -> tuple[GroundedExplicitUnknownWitness, ...]:
    """Resolve source-explicit open slots through typed upstream authority."""

    units_by_parent: dict[str, tuple[GroundedSemanticUnitWitness, ...]] = {}
    for unit in units:
        units_by_parent[unit.parent_nucleus_id] = (
            *units_by_parent.get(unit.parent_nucleus_id, ()),
            unit,
        )
    required = frozenset(plan.coverage_requirements.required_nucleus_ids)
    span_by_id = {str(getattr(row, "span_id", "")): row for row in spans}
    parent_by_id = {
        row.nucleus_id: row
        for row in plan.nuclei
        if row.nucleus_id in required
        and set(row.source_fields) <= _TEXT_SOURCE_FIELDS
        and len(row.source_span_ids) == 1
    }
    formal_by_parent: dict[str, _GroundedFormalSourceParse] = {}
    for parent_id, parent in parent_by_id.items():
        span_id = parent.source_span_ids[0]
        span = span_by_id.get(span_id)
        if span is None:
            continue
        formal_by_parent[parent_id] = _formal_source_parse(
            span_id,
            str(getattr(span, "raw_text", "")),
        )

    markers: list[_GroundedOpenSlotMarker] = []

    def append_marker(
        *,
        dimension: _OpenSlotDimension,
        source_span_id: str,
        governor_nucleus_id: str,
        antecedent_nucleus_ids: Sequence[str],
        affected_unit_ids: Sequence[str],
        argument_completeness: _OpenSlotArgumentCompleteness,
        resolution_basis: _OpenSlotResolutionBasis,
    ) -> None:
        affected = tuple(dict.fromkeys(affected_unit_ids))
        if not affected:
            raise GroundedSemanticRestatementError(
                "SEMANTIC_RESTATEMENT_OPEN_SLOT_UNRESOLVED"
            )
        identity = {
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "source_span_id": source_span_id,
            "dimension": dimension,
            "affected_unit_ids": list(affected),
        }
        markers.append(
            _GroundedOpenSlotMarker(
                marker_id="open_slot:m" + artifact_sha256(identity)[:24],
                source_span_id=source_span_id,
                dimension=dimension,
                governor_nucleus_id=governor_nucleus_id,
                antecedent_nucleus_ids=tuple(
                    dict.fromkeys(antecedent_nucleus_ids)
                ),
                affected_unit_ids=affected,
                argument_completeness=argument_completeness,
                resolution_basis=resolution_basis,
                required=True,
                body_free=True,
            )
        )

    for parent_id in sorted(formal_by_parent):
        parsed = formal_by_parent[parent_id]
        all_parent_owners = _expanded_owner_ids(parent_id, units_by_parent)
        if parsed.cause_marker_range is not None:
            append_marker(
                dimension="explicit_cause_unknown",
                source_span_id=parsed.source_span_id,
                governor_nucleus_id=parent_id,
                antecedent_nucleus_ids=(),
                affected_unit_ids=all_parent_owners,
                argument_completeness="not_applicable",
                resolution_basis="exact_parent_governor",
            )
        if parsed.unverbalized_marker_range is not None:
            exact_user_relation = _exact_user_stated_antecedent(
                plan=plan,
                parent_nucleus_id=parent_id,
                source_span_id=parsed.source_span_id,
                units_by_parent=units_by_parent,
            )
            if exact_user_relation is not None:
                antecedent_id, affected_ids = exact_user_relation
                basis = "exact_required_user_stated_relation_antecedent"
                antecedent_ids = (antecedent_id,)
            elif _has_required_target_relation(
                plan=plan,
                parent_nucleus_id=parent_id,
                source_span_id=parsed.source_span_id,
            ):
                # A required relation is already the owner authority.  If it
                # is not an exact user-stated link, the marker may not fall
                # back to source order or to the containing parent.
                continue
            else:
                direct_ids, direct_basis = _exact_marker_owner_ids(
                    parent_nucleus_id=parent_id,
                    source_span_id=parsed.source_span_id,
                    marker_range=parsed.unverbalized_marker_range,
                    units_by_parent=units_by_parent,
                )
                semantic_antecedent = _exact_semantic_link_antecedent(
                    marker_owner_ids=direct_ids,
                    source_span_id=parsed.source_span_id,
                    semantic_links=semantic_links,
                )
                affected_ids = semantic_antecedent or direct_ids
                basis = (
                    "exact_required_semantic_link_antecedent"
                    if semantic_antecedent is not None
                    else direct_basis
                )
                antecedent_ids = semantic_antecedent or ()
            append_marker(
                dimension="explicit_unverbalized_unknown",
                source_span_id=parsed.source_span_id,
                governor_nucleus_id=parent_id,
                antecedent_nucleus_ids=antecedent_ids,
                affected_unit_ids=affected_ids,
                argument_completeness="not_applicable",
                resolution_basis=basis,
            )
        if parsed.decision_marker_range is not None:
            affected_ids, basis = _exact_marker_owner_ids(
                parent_nucleus_id=parent_id,
                source_span_id=parsed.source_span_id,
                marker_range=parsed.decision_marker_range,
                units_by_parent=units_by_parent,
            )
            append_marker(
                dimension="explicit_choice_decision_unknown",
                source_span_id=parsed.source_span_id,
                governor_nucleus_id=parent_id,
                antecedent_nucleus_ids=(),
                affected_unit_ids=affected_ids,
                argument_completeness="not_applicable",
                resolution_basis=basis,
            )
        if parsed.temporal_marker_range is not None:
            marker_owner_ids, _direct_basis = _exact_marker_owner_ids(
                parent_nucleus_id=parent_id,
                source_span_id=parsed.source_span_id,
                marker_range=parsed.temporal_marker_range,
                units_by_parent=units_by_parent,
            )
            temporal = _exact_temporal_antecedent(
                plan=plan,
                parent_nucleus_id=parent_id,
                source_span_id=parsed.source_span_id,
                marker_owner_ids=marker_owner_ids,
                units_by_parent=units_by_parent,
                semantic_links=semantic_links,
            )
            if temporal is not None:
                antecedent_id, affected_ids, basis = temporal
                append_marker(
                    dimension="explicit_temporal_referent_unknown",
                    source_span_id=parsed.source_span_id,
                    governor_nucleus_id=parent_id,
                    antecedent_nucleus_ids=(antecedent_id,),
                    affected_unit_ids=affected_ids,
                    argument_completeness="referent_open",
                    resolution_basis=basis,
                )

    markers.extend(
        _completion_open_slot_markers(
            plan=plan,
            formal_by_parent=formal_by_parent,
            relations=relations,
            units_by_parent=units_by_parent,
        )
    )
    unique_markers = {row.marker_id: row for row in markers}
    result = tuple(
        GroundedExplicitUnknownWitness(
            unknown_id="semantic_unknown:u" + row.marker_id.removeprefix(
                "open_slot:m"
            ),
            source_span_id=row.source_span_id,
            dimension=row.dimension,
            affected_unit_ids=row.affected_unit_ids,
            required=row.required,
        )
        for row in (
            unique_markers[key] for key in sorted(unique_markers)
        )
    )
    return tuple(sorted(result, key=lambda row: row.unknown_id))


def _witness_sha256(
    plan_binding_sha256: str,
    relations: Sequence[GroundedSemanticRestatementRelationWitness],
    semantic_units: Sequence[GroundedSemanticUnitWitness],
    semantic_links: Sequence[GroundedSemanticLinkWitness],
    explicit_unknowns: Sequence[GroundedExplicitUnknownWitness],
) -> str:
    return artifact_sha256(
        {
            "schema_version": GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA,
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "plan_binding_sha256": plan_binding_sha256,
            "relations": [
                {
                    "relation_id": row.relation_id,
                    "endpoint_semantic_relation": row.endpoint_semantic_relation,
                    "semantic_restatement_unit_nucleus_ids": list(
                        row.semantic_restatement_unit_nucleus_ids
                    ),
                }
                for row in relations
            ],
            "semantic_units": [
                _canonical_body_free(row) for row in semantic_units
            ],
            "semantic_links": [
                _canonical_body_free(row) for row in semantic_links
            ],
            "explicit_unknowns": [
                _canonical_body_free(row) for row in explicit_unknowns
            ],
            "body_free": True,
        }
    )


def build_grounded_semantic_restatement_witness(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> GroundedSemanticRestatementWitness:
    """Build one deterministic witness bound to validated source evidence."""

    spans = _validated_plan_and_spans(plan, resolver)
    binding = _plan_binding_sha256(plan, spans)
    relations = _relation_witnesses(plan, spans)
    semantic_units, semantic_links = _semantic_decomposition(plan, spans)
    explicit_unknowns = _explicit_unknown_witnesses(
        plan,
        spans,
        semantic_units,
        relations,
        semantic_links,
    )
    return GroundedSemanticRestatementWitness(
        schema_version=GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA,
        adapter_version=GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
        plan_binding_sha256=binding,
        relations=relations,
        semantic_units=semantic_units,
        semantic_links=semantic_links,
        explicit_unknowns=explicit_unknowns,
        witness_sha256=_witness_sha256(
            binding,
            relations,
            semantic_units,
            semantic_links,
            explicit_unknowns,
        ),
        body_free=True,
    )


def validate_grounded_semantic_restatement_witness(
    value: Any,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Independently recompute and compare every witness field."""

    try:
        expected = build_grounded_semantic_restatement_witness(plan, resolver)
    except GroundedSemanticRestatementError as exc:
        return (exc.code,)
    issues: list[str] = []
    if type(value) is not GroundedSemanticRestatementWitness:
        return ("SEMANTIC_RESTATEMENT_WITNESS_TYPE_INVALID",)
    if value.schema_version != GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA:
        issues.append("SEMANTIC_RESTATEMENT_WITNESS_SCHEMA_MISMATCH")
    if value.adapter_version != GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION:
        issues.append("SEMANTIC_RESTATEMENT_WITNESS_ADAPTER_MISMATCH")
    if value.plan_binding_sha256 != expected.plan_binding_sha256:
        issues.append("SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH")
    if type(value.relations) is not tuple or value.relations != expected.relations:
        issues.append("SEMANTIC_RESTATEMENT_RELATIONS_MISMATCH")
    if (
        type(value.semantic_units) is not tuple
        or value.semantic_units != expected.semantic_units
    ):
        issues.append("SEMANTIC_RESTATEMENT_UNITS_MISMATCH")
    if (
        type(value.semantic_links) is not tuple
        or value.semantic_links != expected.semantic_links
    ):
        issues.append("SEMANTIC_RESTATEMENT_LINKS_MISMATCH")
    if (
        type(value.explicit_unknowns) is not tuple
        or value.explicit_unknowns != expected.explicit_unknowns
    ):
        issues.append("SEMANTIC_RESTATEMENT_EXPLICIT_UNKNOWNS_MISMATCH")
    try:
        presented_witness_sha256 = _witness_sha256(
            value.plan_binding_sha256,
            value.relations,
            value.semantic_units,
            value.semantic_links,
            value.explicit_unknowns,
        )
    except (AttributeError, TypeError, ValueError):
        presented_witness_sha256 = ""
    if (
        value.witness_sha256 != expected.witness_sha256
        or value.witness_sha256 != presented_witness_sha256
    ):
        issues.append("SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH")
    if value.body_free is not True:
        issues.append("SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED")
    return tuple(sorted(set(issues)))


GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.grounded_cross_role_semantic_restatement_witness.v1"
)
GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3."
    "grounded_cross_role_semantic_restatement_adapter.20260723.v1"
)
CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.cross_role_semantic_depth_equivalence.v1"
)
GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_NEGATIVE_CODES: Final = frozenset(
    {
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_TYPE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_ADAPTER_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_KIND_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_CODE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_BASIS_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_DEPTH_CONTRACT_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ORDER_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH",
    }
)

_CROSS_ROLE_PROOF_CODE: Final = "TYPED_SEMANTIC_GRAPH_EQUIVALENCE"
_CROSS_ROLE_PROOF_BASIS: Final = (
    "COMPLETE_BODY_FREE_TYPED_COMPONENT_BIJECTION"
)
_CROSS_ROLE_EFFECT_SCOPE: Final = "CONTENT_DEPTH_ONLY"
_CROSS_ROLE_ROLES: Final = ("original_input", "supplemental_answer")
_CROSS_ROLE_COMPONENT_KINDS: Final = frozenset(
    {"nucleus", "relation", "unknown_boundary"}
)
_CROSS_ROLE_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_CROSS_ROLE_RELATION_DESCRIPTOR: Final = {
    "temporal_before_after": ("precedes", "source_to_target"),
    "shift_from_to": ("precedes", "source_to_target"),
    "contrast": ("contrasts_with", "source_to_target"),
    "attempt_and_block": ("contrasts_with", "source_to_target"),
    "wish_and_constraint": ("contrasts_with", "source_to_target"),
    "continuation_or_refusal": ("contrasts_with", "source_to_target"),
    "coexistence": ("coexists_with", "bidirectional"),
    "preserves_despite": ("coexists_with", "source_to_target"),
    "evaluation_about_event": ("qualifies", "source_to_target"),
    "self_evaluation_about_state": ("qualifies", "source_to_target"),
    "uncertain_connection": ("qualifies", "source_to_target"),
    "user_stated_cause": ("supports_without_guarantee", "source_to_target"),
    "user_stated_result": ("supports_without_guarantee", "source_to_target"),
    "action_supports_change": (
        "supports_without_guarantee",
        "source_to_target",
    ),
}


@dataclass(frozen=True)
class _GroundedCrossRoleTypedSemanticComponent:
    source_role: str
    source_kind: str
    component_id: str
    component_kind: str
    semantic_identity_sha256: str
    referent_identity_sha256: str
    topic_identity_sha256: str
    predicate_identity_sha256: str
    polarity: str
    modality: str
    time_scope: str
    quantifier_degree: str
    relation_type: str | None
    relation_direction: str | None
    relation_from_identity_sha256: str | None
    relation_to_identity_sha256: str | None
    unknown_dimension: str | None
    affected_identity_sha256s: tuple[str, ...]
    must_separate: bool
    required: bool
    body_free: bool


@dataclass(frozen=True)
class GroundedCrossRoleSemanticComponentBinding:
    binding_id: str
    component_kind: str
    original_source_role: str
    original_source_kind: str
    original_component_id: str
    supplemental_source_role: str
    supplemental_source_kind: str
    supplemental_component_id: str
    canonical_typed_component_sha256: str
    proof_code: str
    proof_basis: str


@dataclass(frozen=True)
class GroundedCrossRoleSemanticRestatementWitness:
    schema_version: str
    adapter_version: str
    original_plan_binding_sha256: str
    supplemental_plan_binding_sha256: str
    original_source_witness_sha256: str
    supplemental_source_witness_sha256: str
    component_bindings: tuple[
        GroundedCrossRoleSemanticComponentBinding, ...
    ]
    effect_scope: str
    depth_equivalence_schema_version: str
    witness_sha256: str
    body_free: bool

    def as_body_free_meta(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_version": self.adapter_version,
            "original_plan_binding_sha256": (
                self.original_plan_binding_sha256
            ),
            "supplemental_plan_binding_sha256": (
                self.supplemental_plan_binding_sha256
            ),
            "original_source_witness_sha256": (
                self.original_source_witness_sha256
            ),
            "supplemental_source_witness_sha256": (
                self.supplemental_source_witness_sha256
            ),
            "component_bindings": [
                _canonical_body_free(row) for row in self.component_bindings
            ],
            "effect_scope": self.effect_scope,
            "depth_equivalence_schema_version": (
                self.depth_equivalence_schema_version
            ),
            "witness_sha256": self.witness_sha256,
            "body_free": self.body_free,
        }


def _cross_role_commitment(namespace: str, material: Any) -> str:
    return artifact_sha256(
        {
            "namespace": (
                "cocolon.emlis.nls_v3.cross_role_semantic_restatement."
                + namespace
            ),
            "material": _canonical_body_free(material),
        }
    )


def _cross_role_quantifier_degree(text: str) -> str:
    values = tuple(sorted(_QUANTIFIER_RE.findall(text)))
    if not values:
        return "source_bounded"
    if (
        len(values) == 1
        and values[0]
        in {"一つ", "ひとつ", "一件", "一通目", "1つ", "1件", "1通目"}
    ):
        return "exact_one"
    return _cross_role_commitment("quantifier_degree", values)


def _cross_role_time_scope(
    nucleus: GroundedSemanticNucleus,
    text: str,
) -> str:
    return _cross_role_commitment(
        "time_scope",
        {
            "plan_time_scope": str(nucleus.semantic_frame.time_scope),
            "explicit_time_markers": tuple(sorted(_time_markers(text))),
        },
    )


def _cross_role_nucleus_identities(
    nucleus: GroundedSemanticNucleus,
    *,
    span_by_id: Mapping[str, Any],
) -> tuple[str, str, str, str]:
    text = _source_text(nucleus, span_by_id)
    subjects, objects = _completion_argument_roles(text)
    relocation_subjects, relocation_objects = _relocation_argument_roles(text)
    topics = _anchors(_TOPIC_ANCHOR_RE, text)
    destinations = _anchors(_DESTINATION_RE, text)
    source_lane = tuple(nucleus.source_fields)
    explicit_referents = {
        "subjects": sorted(subjects | relocation_subjects),
        "objects": sorted(objects | relocation_objects),
        "topics": sorted(topics),
        "destinations": sorted(destinations),
    }
    has_explicit_referent = any(explicit_referents.values())
    if has_explicit_referent:
        referent_material: Any = {
            "source_lane": source_lane,
            "explicit_referents": explicit_referents,
        }
    elif _COMPLETION_RE.search(text) or _RELOCATION_RE.search(text):
        referent_material = {
            "source_lane": source_lane,
            "explicit_referent": "unresolved",
        }
    else:
        referent_material = {
            "source_lane": source_lane,
            "source_meaning_blocks": tuple(
                nucleus.source_meaning_block_keys
            ),
            "source_claims": tuple(nucleus.source_claim_ids),
            "source_expression": _clean(text),
        }
    referent_identity = _cross_role_commitment(
        "referent_identity", referent_material
    )
    topic_identity = _cross_role_commitment(
        "topic_identity",
        {
            "source_lane": source_lane,
            "referent_identity_sha256": referent_identity,
            "topic_anchors": sorted(topics),
        },
    )
    if _COMPLETION_RE.search(text):
        predicate_material: Any = {
            "predicate_class": "completed_event",
            "predicate_kind": nucleus.semantic_frame.predicate_kind,
        }
    elif _RELOCATION_RE.search(text):
        predicate_material = {
            "predicate_class": "relocation_event",
            "predicate_kind": nucleus.semantic_frame.predicate_kind,
        }
    else:
        predicate_material = {
            "predicate_kind": nucleus.semantic_frame.predicate_kind,
            "nucleus_kind": nucleus.kind,
            "source_expression": _clean(text),
        }
    predicate_identity = _cross_role_commitment(
        "predicate_identity", predicate_material
    )
    semantic_identity = _cross_role_commitment(
        "semantic_identity",
        {
            "source_kind": "nucleus",
            "nucleus_kind": nucleus.kind,
            "referent_identity_sha256": referent_identity,
            "topic_identity_sha256": topic_identity,
            "predicate_identity_sha256": predicate_identity,
            "polarity": nucleus.semantic_frame.polarity,
            "modality": nucleus.semantic_frame.modality,
            "time_scope": _cross_role_time_scope(nucleus, text),
            "quantifier_degree": _cross_role_quantifier_degree(text),
        },
    )
    return (
        semantic_identity,
        referent_identity,
        topic_identity,
        predicate_identity,
    )


def _project_grounded_cross_role_typed_semantic_components(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    source_local_witness: GroundedSemanticRestatementWitness,
    source_role: str,
) -> tuple[_GroundedCrossRoleTypedSemanticComponent, ...]:
    if source_role not in _CROSS_ROLE_ROLES:
        raise GroundedSemanticRestatementError(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID"
        )
    if validate_grounded_semantic_restatement_witness(
        source_local_witness,
        plan=plan,
        resolver=resolver,
    ):
        raise GroundedSemanticRestatementError(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH"
        )
    spans = _validated_plan_and_spans(plan, resolver)
    span_by_id = {
        str(getattr(span, "span_id", "")): span for span in spans
    }
    required_nuclei = set(
        plan.coverage_requirements.required_nucleus_ids
    )
    required_relations = set(
        plan.coverage_requirements.required_relation_ids
    )
    separated_nuclei = set(plan.response_plan.fact_boundary_nucleus_ids)
    nucleus_identity: dict[str, str] = {}
    nucleus_rows: list[_GroundedCrossRoleTypedSemanticComponent] = []
    for nucleus in sorted(plan.nuclei, key=lambda row: row.nucleus_id):
        (
            semantic_identity,
            referent_identity,
            topic_identity,
            predicate_identity,
        ) = _cross_role_nucleus_identities(
            nucleus,
            span_by_id=span_by_id,
        )
        nucleus_identity[nucleus.nucleus_id] = semantic_identity
        text = _source_text(nucleus, span_by_id)
        nucleus_rows.append(
            _GroundedCrossRoleTypedSemanticComponent(
                source_role=source_role,
                source_kind="nucleus",
                component_id=nucleus.nucleus_id,
                component_kind="nucleus",
                semantic_identity_sha256=semantic_identity,
                referent_identity_sha256=referent_identity,
                topic_identity_sha256=topic_identity,
                predicate_identity_sha256=predicate_identity,
                polarity=str(nucleus.semantic_frame.polarity),
                modality=str(nucleus.semantic_frame.modality),
                time_scope=_cross_role_time_scope(nucleus, text),
                quantifier_degree=_cross_role_quantifier_degree(text),
                relation_type=None,
                relation_direction=None,
                relation_from_identity_sha256=None,
                relation_to_identity_sha256=None,
                unknown_dimension=None,
                affected_identity_sha256s=(),
                must_separate=nucleus.nucleus_id in separated_nuclei,
                required=nucleus.nucleus_id in required_nuclei,
                body_free=True,
            )
        )
    relation_rows: list[_GroundedCrossRoleTypedSemanticComponent] = []
    for relation in sorted(plan.relations, key=lambda row: row.relation_id):
        if (
            relation.from_nucleus_id not in nucleus_identity
            or relation.to_nucleus_id not in nucleus_identity
        ):
            raise GroundedSemanticRestatementError(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED"
            )
        semantic_relation_type, relation_direction = (
            _CROSS_ROLE_RELATION_DESCRIPTOR.get(
                relation.type,
                (str(relation.type), "source_to_target"),
            )
        )
        relation_type = str(relation.type)
        grounding_kind = str(relation.grounding_kind)
        from_identity = nucleus_identity[relation.from_nucleus_id]
        to_identity = nucleus_identity[relation.to_nucleus_id]
        predicate_identity = _cross_role_commitment(
            "relation_predicate_identity",
            {
                "source_relation_type": relation_type,
                "grounding_kind": grounding_kind,
                "semantic_relation_type": semantic_relation_type,
                "relation_direction": relation_direction,
            },
        )
        referent_identity = _cross_role_commitment(
            "relation_referent_identity",
            {
                "from": from_identity,
                "to": to_identity,
            },
        )
        topic_identity = _cross_role_commitment(
            "relation_topic_identity",
            {
                "from": from_identity,
                "to": to_identity,
            },
        )
        semantic_identity = _cross_role_commitment(
            "semantic_identity",
            {
                "source_kind": "relation",
                "source_relation_type": relation_type,
                "grounding_kind": grounding_kind,
                "semantic_relation_type": semantic_relation_type,
                "relation_direction": relation_direction,
                "from": from_identity,
                "to": to_identity,
            },
        )
        relation_rows.append(
            _GroundedCrossRoleTypedSemanticComponent(
                source_role=source_role,
                source_kind="relation",
                component_id=relation.relation_id,
                component_kind="relation",
                semantic_identity_sha256=semantic_identity,
                referent_identity_sha256=referent_identity,
                topic_identity_sha256=topic_identity,
                predicate_identity_sha256=predicate_identity,
                polarity="neutral",
                modality="fact",
                time_scope="current",
                quantifier_degree="source_bounded",
                relation_type=relation_type,
                relation_direction=relation_direction,
                relation_from_identity_sha256=from_identity,
                relation_to_identity_sha256=to_identity,
                unknown_dimension=None,
                affected_identity_sha256s=(),
                must_separate=False,
                required=relation.relation_id in required_relations,
                body_free=True,
            )
        )
    unknown_rows: list[_GroundedCrossRoleTypedSemanticComponent] = []
    for unknown in sorted(
        plan.unknown_boundaries, key=lambda row: row.unknown_id
    ):
        try:
            affected = tuple(
                nucleus_identity[source_id]
                for source_id in unknown.affected_nucleus_ids
            )
        except KeyError as exc:
            raise GroundedSemanticRestatementError(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED"
            ) from exc
        predicate_identity = _cross_role_commitment(
            "unknown_predicate_identity", unknown.dimension
        )
        referent_identity = _cross_role_commitment(
            "unknown_referent_identity", affected
        )
        topic_identity = _cross_role_commitment(
            "unknown_topic_identity", affected
        )
        semantic_identity = _cross_role_commitment(
            "semantic_identity",
            {
                "source_kind": "unknown_boundary",
                "dimension": unknown.dimension,
                "affected": affected,
            },
        )
        unknown_rows.append(
            _GroundedCrossRoleTypedSemanticComponent(
                source_role=source_role,
                source_kind="unknown_boundary",
                component_id=unknown.unknown_id,
                component_kind="unknown_boundary",
                semantic_identity_sha256=semantic_identity,
                referent_identity_sha256=referent_identity,
                topic_identity_sha256=topic_identity,
                predicate_identity_sha256=predicate_identity,
                polarity="neutral",
                modality="uncertain",
                time_scope="current",
                quantifier_degree="source_bounded",
                relation_type=None,
                relation_direction=None,
                relation_from_identity_sha256=None,
                relation_to_identity_sha256=None,
                unknown_dimension=str(unknown.dimension),
                affected_identity_sha256s=affected,
                must_separate=False,
                required=True,
                body_free=True,
            )
        )
    return tuple(
        sorted(
            (*nucleus_rows, *relation_rows, *unknown_rows),
            key=lambda row: (row.component_kind, row.component_id),
        )
    )


def _cross_role_component_material(
    row: _GroundedCrossRoleTypedSemanticComponent,
) -> dict[str, Any]:
    return {
        field: getattr(row, field)
        for field in row.__dataclass_fields__
        if field not in {"source_role", "component_id"}
    }


def _cross_role_component_sha256(
    row: _GroundedCrossRoleTypedSemanticComponent,
) -> str:
    return _cross_role_commitment(
        "typed_component",
        _cross_role_component_material(row),
    )


def _cross_role_component_identity(
    row: _GroundedCrossRoleTypedSemanticComponent,
) -> tuple[str, str]:
    return row.component_kind, _cross_role_component_sha256(row)


def _cross_role_component_groups(
    rows: Sequence[_GroundedCrossRoleTypedSemanticComponent],
) -> tuple[tuple[_GroundedCrossRoleTypedSemanticComponent, ...], ...]:
    by_id = {row.component_id: row for row in rows}
    by_semantic_identity: dict[str, set[str]] = {}
    for row in rows:
        by_semantic_identity.setdefault(
            row.semantic_identity_sha256, set()
        ).add(row.component_id)
    adjacency = {row.component_id: set() for row in rows}
    for row in rows:
        linked_identities: tuple[str, ...] = ()
        if row.component_kind == "relation":
            linked_identities = tuple(
                value
                for value in (
                    row.relation_from_identity_sha256,
                    row.relation_to_identity_sha256,
                )
                if value is not None
            )
        elif row.component_kind == "unknown_boundary":
            linked_identities = row.affected_identity_sha256s
        for identity in linked_identities:
            for target_id in by_semantic_identity.get(identity, set()):
                adjacency[row.component_id].add(target_id)
                adjacency[target_id].add(row.component_id)
    groups: list[tuple[_GroundedCrossRoleTypedSemanticComponent, ...]] = []
    remaining = set(by_id)
    while remaining:
        seed = min(remaining)
        pending = [seed]
        closed: set[str] = set()
        while pending:
            current = pending.pop()
            if current in closed:
                continue
            closed.add(current)
            pending.extend(sorted(adjacency[current] - closed))
        remaining.difference_update(closed)
        groups.append(
            tuple(
                sorted(
                    (by_id[source_id] for source_id in closed),
                    key=lambda row: (
                        row.component_kind,
                        row.component_id,
                    ),
                )
            )
        )
    return tuple(groups)


def _cross_role_components_valid(
    rows: Any,
    *,
    expected_role: str,
) -> bool:
    return bool(
        type(rows) is tuple
        and all(
            type(row) is _GroundedCrossRoleTypedSemanticComponent
            and row.source_role == expected_role
            and row.source_kind == row.component_kind
            and row.component_kind in _CROSS_ROLE_COMPONENT_KINDS
            and type(row.component_id) is str
            and bool(row.component_id)
            and all(
                type(value) is str
                and _CROSS_ROLE_SHA256_RE.fullmatch(value) is not None
                for value in (
                    row.semantic_identity_sha256,
                    row.referent_identity_sha256,
                    row.topic_identity_sha256,
                    row.predicate_identity_sha256,
                )
            )
            and type(row.affected_identity_sha256s) is tuple
            and all(
                type(value) is str
                and _CROSS_ROLE_SHA256_RE.fullmatch(value) is not None
                for value in row.affected_identity_sha256s
            )
            and all(
                type(value) is str
                for value in (
                    row.polarity,
                    row.modality,
                    row.time_scope,
                    row.quantifier_degree,
                )
            )
            and all(
                value is None or type(value) is str
                for value in (
                    row.relation_type,
                    row.relation_direction,
                    row.relation_from_identity_sha256,
                    row.relation_to_identity_sha256,
                    row.unknown_dimension,
                )
            )
            and type(row.must_separate) is bool
            and type(row.required) is bool
            and row.body_free is True
            for row in rows
        )
        and len({row.component_id for row in rows}) == len(rows)
    )


def _cross_role_binding_sort_key(
    row: GroundedCrossRoleSemanticComponentBinding,
) -> tuple[str, str, str, str]:
    return (
        row.component_kind,
        row.original_component_id,
        row.supplemental_component_id,
        row.binding_id,
    )


def _cross_role_witness_sha256(
    *,
    original_plan_binding_sha256: str,
    supplemental_plan_binding_sha256: str,
    original_source_witness_sha256: str,
    supplemental_source_witness_sha256: str,
    component_bindings: Sequence[
        GroundedCrossRoleSemanticComponentBinding
    ],
) -> str:
    return artifact_sha256(
        {
            "schema_version": (
                GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA
            ),
            "adapter_version": (
                GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
            ),
            "original_plan_binding_sha256": (
                original_plan_binding_sha256
            ),
            "supplemental_plan_binding_sha256": (
                supplemental_plan_binding_sha256
            ),
            "original_source_witness_sha256": (
                original_source_witness_sha256
            ),
            "supplemental_source_witness_sha256": (
                supplemental_source_witness_sha256
            ),
            "component_bindings": [
                _canonical_body_free(row) for row in component_bindings
            ],
            "effect_scope": _CROSS_ROLE_EFFECT_SCOPE,
            "depth_equivalence_schema_version": (
                CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA
            ),
            "body_free": True,
        }
    )


def _build_grounded_cross_role_semantic_restatement_witness_from_typed_components(
    *,
    original_components: tuple[
        _GroundedCrossRoleTypedSemanticComponent, ...
    ],
    supplemental_components: tuple[
        _GroundedCrossRoleTypedSemanticComponent, ...
    ],
    original_plan_binding_sha256: str,
    supplemental_plan_binding_sha256: str,
    original_source_witness_sha256: str,
    supplemental_source_witness_sha256: str,
) -> GroundedCrossRoleSemanticRestatementWitness:
    hashes = (
        original_plan_binding_sha256,
        supplemental_plan_binding_sha256,
        original_source_witness_sha256,
        supplemental_source_witness_sha256,
    )
    if not all(
        type(value) is str
        and _CROSS_ROLE_SHA256_RE.fullmatch(value) is not None
        for value in hashes
    ):
        raise GroundedSemanticRestatementError(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID"
        )
    if not _cross_role_components_valid(
        original_components,
        expected_role="original_input",
    ) or not _cross_role_components_valid(
        supplemental_components,
        expected_role="supplemental_answer",
    ):
        if (
            type(original_components) is tuple
            and type(supplemental_components) is tuple
            and all(
                type(row) is _GroundedCrossRoleTypedSemanticComponent
                for row in (*original_components, *supplemental_components)
            )
            and (
                any(
                    row.source_role != "original_input"
                    for row in original_components
                )
                or any(
                    row.source_role != "supplemental_answer"
                    for row in supplemental_components
                )
            )
        ):
            raise GroundedSemanticRestatementError(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID"
            )
        raise GroundedSemanticRestatementError(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID"
        )
    for rows in (original_components, supplemental_components):
        identities = [
            _cross_role_component_identity(row) for row in rows
        ]
        if len(identities) != len(set(identities)):
            raise GroundedSemanticRestatementError(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS"
            )

    original_groups = _cross_role_component_groups(original_components)
    supplemental_groups = _cross_role_component_groups(
        supplemental_components
    )

    def eligible_groups(
        groups: Sequence[
            tuple[_GroundedCrossRoleTypedSemanticComponent, ...]
        ],
    ) -> dict[
        tuple[tuple[str, str], ...],
        tuple[_GroundedCrossRoleTypedSemanticComponent, ...],
    ]:
        output: dict[
            tuple[tuple[str, str], ...],
            tuple[_GroundedCrossRoleTypedSemanticComponent, ...],
        ] = {}
        for group in groups:
            if any(row.must_separate for row in group):
                continue
            signature = tuple(
                sorted(_cross_role_component_identity(row) for row in group)
            )
            if signature in output:
                raise GroundedSemanticRestatementError(
                    "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS"
                )
            output[signature] = group
        return output

    original_by_graph = eligible_groups(original_groups)
    supplemental_by_graph = eligible_groups(supplemental_groups)
    bindings: list[GroundedCrossRoleSemanticComponentBinding] = []
    for signature in sorted(
        set(original_by_graph) & set(supplemental_by_graph)
    ):
        original_by_identity = {
            _cross_role_component_identity(row): row
            for row in original_by_graph[signature]
        }
        supplemental_by_identity = {
            _cross_role_component_identity(row): row
            for row in supplemental_by_graph[signature]
        }
        if (
            set(original_by_identity) != set(supplemental_by_identity)
            or len(original_by_identity) != len(original_by_graph[signature])
            or len(supplemental_by_identity)
            != len(supplemental_by_graph[signature])
        ):
            raise GroundedSemanticRestatementError(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS"
            )
        for identity in sorted(original_by_identity):
            original = original_by_identity[identity]
            supplemental = supplemental_by_identity[identity]
            canonical_sha256 = identity[1]
            binding_id = "cross_role_binding:b" + artifact_sha256(
                {
                    "adapter_version": (
                        GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
                    ),
                    "component_kind": original.component_kind,
                    "original_component_id": original.component_id,
                    "supplemental_component_id": supplemental.component_id,
                    "canonical_typed_component_sha256": canonical_sha256,
                }
            )[:24]
            bindings.append(
                GroundedCrossRoleSemanticComponentBinding(
                    binding_id=binding_id,
                    component_kind=original.component_kind,
                    original_source_role=original.source_role,
                    original_source_kind=original.source_kind,
                    original_component_id=original.component_id,
                    supplemental_source_role=supplemental.source_role,
                    supplemental_source_kind=supplemental.source_kind,
                    supplemental_component_id=supplemental.component_id,
                    canonical_typed_component_sha256=canonical_sha256,
                    proof_code=_CROSS_ROLE_PROOF_CODE,
                    proof_basis=_CROSS_ROLE_PROOF_BASIS,
                )
            )
    ordered_bindings = tuple(sorted(bindings, key=_cross_role_binding_sort_key))
    witness_sha256 = _cross_role_witness_sha256(
        original_plan_binding_sha256=original_plan_binding_sha256,
        supplemental_plan_binding_sha256=supplemental_plan_binding_sha256,
        original_source_witness_sha256=original_source_witness_sha256,
        supplemental_source_witness_sha256=(
            supplemental_source_witness_sha256
        ),
        component_bindings=ordered_bindings,
    )
    return GroundedCrossRoleSemanticRestatementWitness(
        schema_version=(
            GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA
        ),
        adapter_version=(
            GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
        ),
        original_plan_binding_sha256=original_plan_binding_sha256,
        supplemental_plan_binding_sha256=(
            supplemental_plan_binding_sha256
        ),
        original_source_witness_sha256=original_source_witness_sha256,
        supplemental_source_witness_sha256=(
            supplemental_source_witness_sha256
        ),
        component_bindings=ordered_bindings,
        effect_scope=_CROSS_ROLE_EFFECT_SCOPE,
        depth_equivalence_schema_version=(
            CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA
        ),
        witness_sha256=witness_sha256,
        body_free=True,
    )


def _validate_grounded_cross_role_semantic_restatement_witness_from_typed_components(
    value: Any,
    *,
    original_components: tuple[
        _GroundedCrossRoleTypedSemanticComponent, ...
    ],
    supplemental_components: tuple[
        _GroundedCrossRoleTypedSemanticComponent, ...
    ],
    original_plan_binding_sha256: str,
    supplemental_plan_binding_sha256: str,
    original_source_witness_sha256: str,
    supplemental_source_witness_sha256: str,
) -> tuple[str, ...]:
    if type(value) is not GroundedCrossRoleSemanticRestatementWitness:
        return ("CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_TYPE_INVALID",)
    try:
        expected = (
            _build_grounded_cross_role_semantic_restatement_witness_from_typed_components(
                original_components=original_components,
                supplemental_components=supplemental_components,
                original_plan_binding_sha256=original_plan_binding_sha256,
                supplemental_plan_binding_sha256=(
                    supplemental_plan_binding_sha256
                ),
                original_source_witness_sha256=(
                    original_source_witness_sha256
                ),
                supplemental_source_witness_sha256=(
                    supplemental_source_witness_sha256
                ),
            )
        )
    except GroundedSemanticRestatementError as exc:
        return (exc.code,)
    issues: list[str] = []
    if value.schema_version != (
        GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA
    ):
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA_MISMATCH"
        )
    if value.adapter_version != (
        GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
    ):
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_ADAPTER_MISMATCH"
        )
    if (
        value.original_plan_binding_sha256
        != original_plan_binding_sha256
        or value.supplemental_plan_binding_sha256
        != supplemental_plan_binding_sha256
    ):
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH"
        )
    if (
        value.original_source_witness_sha256
        != original_source_witness_sha256
        or value.supplemental_source_witness_sha256
        != supplemental_source_witness_sha256
    ):
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH"
        )
    bindings = value.component_bindings
    if type(bindings) is not tuple or not all(
        type(row) is GroundedCrossRoleSemanticComponentBinding
        for row in bindings
    ):
        issues.append("CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID")
        bindings = ()
    elif any(
        any(
            type(getattr(row, field)) is not str
            for field in row.__dataclass_fields__
        )
        for row in bindings
    ):
        issues.append("CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID")
        bindings = ()
    original_by_id = {
        row.component_id: row for row in original_components
    }
    supplemental_by_id = {
        row.component_id: row for row in supplemental_components
    }
    original_ids: list[str] = []
    supplemental_ids: list[str] = []
    for row in bindings:
        original_ids.append(row.original_component_id)
        supplemental_ids.append(row.supplemental_component_id)
        if (
            row.original_source_role != "original_input"
            or row.supplemental_source_role != "supplemental_answer"
        ):
            issues.append(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID"
            )
        original = original_by_id.get(row.original_component_id)
        supplemental = supplemental_by_id.get(
            row.supplemental_component_id
        )
        if original is None or supplemental is None:
            issues.append(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED"
            )
            continue
        if (
            row.component_kind != original.component_kind
            or row.component_kind != supplemental.component_kind
            or row.original_source_kind != original.source_kind
            or row.supplemental_source_kind != supplemental.source_kind
        ):
            issues.append(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_KIND_MISMATCH"
            )
        if (
            _cross_role_component_identity(original)
            != _cross_role_component_identity(supplemental)
            or row.canonical_typed_component_sha256
            != _cross_role_component_sha256(original)
        ):
            issues.append(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH"
            )
        if row.proof_code != _CROSS_ROLE_PROOF_CODE:
            issues.append(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_CODE_INVALID"
            )
        if row.proof_basis != _CROSS_ROLE_PROOF_BASIS:
            issues.append(
                "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_BASIS_INVALID"
            )
    if (
        len(original_ids) != len(set(original_ids))
        or len(supplemental_ids) != len(set(supplemental_ids))
    ):
        issues.append("CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS")
    if tuple(sorted(bindings, key=_cross_role_binding_sort_key)) != bindings:
        issues.append("CROSS_ROLE_SEMANTIC_RESTATEMENT_ORDER_INVALID")
    if bindings != expected.component_bindings:
        issues.append("CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH")
    if value.effect_scope != _CROSS_ROLE_EFFECT_SCOPE:
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID"
        )
    if value.depth_equivalence_schema_version != (
        CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA
    ):
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_DEPTH_CONTRACT_INVALID"
        )
    if value.body_free is not True:
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED"
        )
    try:
        presented_sha256 = _cross_role_witness_sha256(
            original_plan_binding_sha256=(
                value.original_plan_binding_sha256
            ),
            supplemental_plan_binding_sha256=(
                value.supplemental_plan_binding_sha256
            ),
            original_source_witness_sha256=(
                value.original_source_witness_sha256
            ),
            supplemental_source_witness_sha256=(
                value.supplemental_source_witness_sha256
            ),
            component_bindings=bindings,
        )
    except (AttributeError, TypeError, ValueError):
        presented_sha256 = ""
    if (
        value.witness_sha256 != expected.witness_sha256
        or value.witness_sha256 != presented_sha256
    ):
        issues.append(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH"
        )
    return tuple(sorted(set(issues)))


def build_grounded_cross_role_semantic_restatement_witness(
    original_plan: GroundedObservationPlan,
    original_resolver: EvidenceSpanResolver,
    supplemental_plan: GroundedObservationPlan,
    supplemental_resolver: EvidenceSpanResolver,
) -> GroundedCrossRoleSemanticRestatementWitness:
    try:
        original_local = build_grounded_semantic_restatement_witness(
            original_plan, original_resolver
        )
        supplemental_local = build_grounded_semantic_restatement_witness(
            supplemental_plan, supplemental_resolver
        )
    except GroundedSemanticRestatementError as exc:
        raise GroundedSemanticRestatementError(
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH"
        ) from exc
    original_components = (
        _project_grounded_cross_role_typed_semantic_components(
            original_plan,
            original_resolver,
            original_local,
            "original_input",
        )
    )
    supplemental_components = (
        _project_grounded_cross_role_typed_semantic_components(
            supplemental_plan,
            supplemental_resolver,
            supplemental_local,
            "supplemental_answer",
        )
    )
    return (
        _build_grounded_cross_role_semantic_restatement_witness_from_typed_components(
            original_components=original_components,
            supplemental_components=supplemental_components,
            original_plan_binding_sha256=(
                original_local.plan_binding_sha256
            ),
            supplemental_plan_binding_sha256=(
                supplemental_local.plan_binding_sha256
            ),
            original_source_witness_sha256=original_local.witness_sha256,
            supplemental_source_witness_sha256=(
                supplemental_local.witness_sha256
            ),
        )
    )


def validate_grounded_cross_role_semantic_restatement_witness(
    value: Any,
    *,
    original_plan: GroundedObservationPlan,
    original_resolver: EvidenceSpanResolver,
    supplemental_plan: GroundedObservationPlan,
    supplemental_resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    try:
        original_local = build_grounded_semantic_restatement_witness(
            original_plan, original_resolver
        )
        supplemental_local = build_grounded_semantic_restatement_witness(
            supplemental_plan, supplemental_resolver
        )
    except GroundedSemanticRestatementError:
        return (
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH",
        )
    if (
        type(value) is GroundedCrossRoleSemanticRestatementWitness
        and (
            value.original_plan_binding_sha256
            != original_local.plan_binding_sha256
            or value.supplemental_plan_binding_sha256
            != supplemental_local.plan_binding_sha256
        )
    ):
        return (
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH",
        )
    try:
        original_components = (
            _project_grounded_cross_role_typed_semantic_components(
                original_plan,
                original_resolver,
                original_local,
                "original_input",
            )
        )
        supplemental_components = (
            _project_grounded_cross_role_typed_semantic_components(
                supplemental_plan,
                supplemental_resolver,
                supplemental_local,
                "supplemental_answer",
            )
        )
    except GroundedSemanticRestatementError as exc:
        return (exc.code,)
    return (
        _validate_grounded_cross_role_semantic_restatement_witness_from_typed_components(
            value,
            original_components=original_components,
            supplemental_components=supplemental_components,
            original_plan_binding_sha256=(
                original_local.plan_binding_sha256
            ),
            supplemental_plan_binding_sha256=(
                supplemental_local.plan_binding_sha256
            ),
            original_source_witness_sha256=original_local.witness_sha256,
            supplemental_source_witness_sha256=(
                supplemental_local.witness_sha256
            ),
        )
    )


__all__ = [
    "CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA",
    "EndpointSemanticRelation",
    "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION",
    "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_NEGATIVE_CODES",
    "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA",
    "GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION",
    "GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA",
    "GroundedCrossRoleSemanticComponentBinding",
    "GroundedCrossRoleSemanticRestatementWitness",
    "GroundedSemanticRestatementError",
    "GroundedExplicitUnknownWitness",
    "GroundedSemanticLinkWitness",
    "GroundedSemanticRestatementRelationWitness",
    "GroundedSemanticRestatementWitness",
    "GroundedSemanticUnitWitness",
    "SemanticLinkType",
    "SemanticUnitKind",
    "build_grounded_cross_role_semantic_restatement_witness",
    "build_grounded_semantic_restatement_witness",
    "validate_grounded_cross_role_semantic_restatement_witness",
    "validate_grounded_semantic_restatement_witness",
]
