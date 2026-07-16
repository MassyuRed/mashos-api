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
_UNSPECIFIED_RETURN_RE: Final = re.compile(r"帰ってから")
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


def _explicit_unknown_witnesses(
    plan: GroundedObservationPlan,
    spans: Sequence[Any],
    units: Sequence[GroundedSemanticUnitWitness],
) -> tuple[GroundedExplicitUnknownWitness, ...]:
    """Extract source-explicit unknowns without consulting fixture metadata."""

    unit_by_parent: dict[str, list[GroundedSemanticUnitWitness]] = {}
    for unit in units:
        unit_by_parent.setdefault(unit.parent_nucleus_id, []).append(unit)
    required = frozenset(plan.coverage_requirements.required_nucleus_ids)
    span_by_id = {str(getattr(row, "span_id", "")): row for row in spans}
    rows: list[GroundedExplicitUnknownWitness] = []

    def append(
        *, dimension: str, source_span_id: str, affected_ids: Sequence[str]
    ) -> None:
        identity = {
            "adapter_version": GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
            "source_span_id": source_span_id,
            "dimension": dimension,
            "affected_unit_ids": list(affected_ids),
        }
        rows.append(
            GroundedExplicitUnknownWitness(
                unknown_id="semantic_unknown:u" + artifact_sha256(identity)[:24],
                source_span_id=source_span_id,
                dimension=dimension,
                affected_unit_ids=tuple(affected_ids),
                required=True,
            )
        )

    for parent in plan.nuclei:
        if (
            parent.nucleus_id not in required
            or not set(parent.source_fields) <= _TEXT_SOURCE_FIELDS
            or len(parent.source_span_ids) != 1
        ):
            continue
        span_id = parent.source_span_ids[0]
        span = span_by_id.get(span_id)
        if span is None:
            continue
        text = str(getattr(span, "raw_text", ""))
        targets = tuple(
            row.unit_id for row in unit_by_parent.get(parent.nucleus_id, [])
        ) or (parent.nucleus_id,)
        consequence = targets[-1:]
        if _EXPLICIT_WHY_RE.search(text) or "なんとなく" in text:
            append(
                dimension="explicit_cause_unknown",
                source_span_id=span_id,
                affected_ids=targets,
            )
        if _UNVERBALIZED_RE.search(text):
            append(
                dimension="explicit_unverbalized_unknown",
                source_span_id=span_id,
                affected_ids=consequence,
            )
        if _COMPARATIVE_UNCERTAINTY_RE.search(text) or re.search(
            r"(?:決められない|判断できない|選べない|迷(?:う|って|い))", text
        ):
            append(
                dimension="explicit_choice_decision_unknown",
                source_span_id=span_id,
                affected_ids=consequence,
            )
        if _UNSPECIFIED_RETURN_RE.search(text) and not re.search(
            r"(?:家|部屋|職場|学校|店|会場|場所|実家|旅行|外)\s*(?:に|へ)?帰ってから",
            text,
        ):
            append(
                dimension="explicit_temporal_referent_unknown",
                source_span_id=span_id,
                affected_ids=targets,
            )
    unique = {row.unknown_id: row for row in rows}
    return tuple(unique[key] for key in sorted(unique))


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
        plan, spans, semantic_units
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


__all__ = [
    "EndpointSemanticRelation",
    "GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION",
    "GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA",
    "GroundedSemanticRestatementError",
    "GroundedExplicitUnknownWitness",
    "GroundedSemanticLinkWitness",
    "GroundedSemanticRestatementRelationWitness",
    "GroundedSemanticRestatementWitness",
    "GroundedSemanticUnitWitness",
    "SemanticLinkType",
    "SemanticUnitKind",
    "build_grounded_semantic_restatement_witness",
    "validate_grounded_semantic_restatement_witness",
]
