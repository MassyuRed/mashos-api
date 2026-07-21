# -*- coding: utf-8 -*-
from __future__ import annotations

"""Experiment-only relation and construction authority for rc0028 E1b.

The owner reads the byte-frozen Grounded plan, its request-local Evidence
resolver and the byte-frozen semantic-restatement adapter.  It does not alter
those owners and is not imported by a runtime path.  Returned records contain
only ids, closed codes, exact local offsets and commitments; source bodies are
retained solely by a private request-local origin capability.
"""

from dataclasses import dataclass, fields, is_dataclass, replace
import re
from typing import Any, Final, Literal, Mapping, Sequence
import weakref

from emlis_ai_evidence_ledger_service import (
    EvidenceLedgerResolutionError,
    EvidenceSpanResolver,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    GroundedSemanticNucleus,
    GroundedSemanticRelation,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    GroundedSemanticRestatementError,
    GroundedSemanticRestatementWitness,
    build_grounded_semantic_restatement_witness,
    validate_grounded_semantic_restatement_witness,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256


GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.grounded_relation_construction_authority_successor."
    "rc0028.experiment.v2"
)
GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3.grounded_relation_construction_authority_adapter."
    "20260719.v2"
)
GROUNDED_RELATION_CONSTRUCTION_MARKER_POLICY_VERSION: Final = (
    "cocolon.emlis.nls_v3.source_explicit_relation_marker_policy.20260722.v2"
)
GROUNDED_RELATION_CONSTRUCTION_GIT_BASELINE_COMMIT: Final = (
    "31d3cf183589b27481338277574f90500f3c5b11"
)
GROUNDED_RELATION_CONSTRUCTION_GIT_BASELINE_TREE: Final = (
    "c826c3ed5587356f313a90a5b67611e3972abd42"
)

MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT: Final = 6
MAX_CONSTRUCTION_INSTANCES_PER_PARENT_SPAN: Final = 6
MAX_SOURCE_OWNER_PARTICIPATIONS_PER_SLOT: Final = 4

_TEXT_SOURCE_FIELDS: Final = frozenset({"memo", "memo_action"})
_RELATION_TYPES: Final = frozenset(
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
_EXPLICIT_UNKNOWN_DIMENSIONS: Final = frozenset(
    {
        "explicit_cause_unknown",
        "explicit_unverbalized_unknown",
        "explicit_choice_decision_unknown",
        "explicit_temporal_referent_unknown",
    }
)
_LEXICAL_ROLE_KINDS: Final = frozenset(
    {
        "referent_primary",
        "referent_secondary",
        "antecedent_predication",
        "consequent_predication",
        "predicate_or_event",
        "state_or_quality",
        "transition_or_relation",
        "action_lifecycle",
        "unknown_or_limit",
    }
)
_CONSTRUCTION_CODES: Final = frozenset(
    {
        "comparative_assessment",
        "particle_object",
        "choice_uncertainty",
        "decision_timing",
        "purpose_action",
        "explicit_contrast",
        "ordered_sequence",
        "reported_self_assessment",
        "explicit_coexistence",
        "parallel_addition",
        "nonreduction_boundary",
        "withheld_action",
        "balanced_consideration",
    }
)
_CONSTRUCTION_POSITIONS: Final = frozenset(
    {
        "primary",
        "secondary",
        "antecedent",
        "consequent",
        "predicate",
        "quality",
        "connector",
        "limit",
        "lifecycle",
    }
)
GROUNDED_SUCCESSOR_LEXICAL_ROLE_KINDS: Final = _LEXICAL_ROLE_KINDS
GROUNDED_SUCCESSOR_CONSTRUCTION_CODES: Final = _CONSTRUCTION_CODES
GROUNDED_SUCCESSOR_CONSTRUCTION_POSITIONS: Final = _CONSTRUCTION_POSITIONS

GROUNDED_SUCCESSOR_INTERNAL_LINK_BY_CONSTRUCTION: Final = (
    ("balanced_consideration", "coexistence"),
    ("choice_uncertainty", "limits"),
    ("comparative_assessment", "qualifies"),
    ("decision_timing", "limits"),
    ("explicit_coexistence", "coexistence"),
    ("explicit_contrast", "contrast"),
    ("nonreduction_boundary", "limits"),
    ("ordered_sequence", "precedes"),
    ("parallel_addition", "coexistence"),
    ("particle_object", "qualifies"),
    ("purpose_action", "qualifies"),
    ("reported_self_assessment", "qualifies"),
    ("withheld_action", "precedes"),
)
_INTERNAL_LINK_BY_CONSTRUCTION: Final = dict(
    GROUNDED_SUCCESSOR_INTERNAL_LINK_BY_CONSTRUCTION
)

# The grammar is closed and topic-independent.  Multiple matching
# constructions are retained as distinct instances; role cardinality is
# enforced within an instance, never across overlapping instances.
_COMPARATIVE_RE: Final = re.compile(
    r"^(?P<primary>.+?)(?:の方|のほう)が[、,]?(?P<quality>.+)$"
)
_PARTICLE_OBJECT_RE: Final = re.compile(
    r"^(?:.{1,32}?(?:は|が)[、,]?)?"
    r"(?P<primary>[^、,。．.!！?？を]{1,32})を"
    r"(?P<predicate>[^、,。．.!！?？]{2,})$"
)
_AMBIGUOUS_PARTICLE_OBJECT_SCOPE_RE: Final = re.compile(r"(?:で|に|へ).+")
_CHOICE_UNCERTAINTY_RE: Final = re.compile(
    r"^(?P<primary>.+?)(?:かどうか|か)"
    r"(?P<limit>(?:迷|決めかね|判断でき|選べ).+)$"
)
_DECISION_TIMING_RE: Final = re.compile(
    r"^(?P<primary>.+?時期)(?:も|は|を)?"
    r"(?P<limit>(?:決め|判断|選)[^、,。]*ない)$"
)
_PURPOSE_ACTION_RE: Final = re.compile(
    r"^(?P<connector>.{2,}?よう)[、,](?P<predicate>.{2,})$"
)
_EXPLICIT_CONTRAST_RE: Final = re.compile(
    r"^(?P<antecedent>.{2,}?)"
    r"(?P<connector>けれども|けれど|だけど|けど|のに|とはいえ)"
    r"[、,]?(?P<consequent>.{2,})$"
)
_ORDERED_SEQUENCE_RE: Final = re.compile(
    r"^(?P<antecedent>.{2,}?)(?P<connector>(?:て|で)から|後で|あとで)"
    r"[、,]?(?P<consequent>.{2,})$"
)
_SELF_ASSESSMENT_RE: Final = re.compile(
    r"^(?P<primary>.*?(?:自分|私)(?:に|には|は)?)"
    r"(?P<quality>.{0,}?(?:"
    r"向いて(?:い)?ない|"
    r"(?:価値|資格|適性)(?:が|は)?ない|"
    r"(?:苦手|だめ|駄目|無理)(?:だ|だと|だと思|かもしれ|だろう|なの)"
    r").*)$"
)
_COEXISTENCE_RE: Final = re.compile(
    r"^(?P<primary>.+?)と[、,](?P<secondary>.+?)(?P<connector>両方).+$"
)
_PARALLEL_ADDITION_RE: Final = re.compile(
    r"^(?P<antecedent>.{2,}?[いきくすつぬぶむるただ])"
    r"(?P<connector>し)[、,](?P<consequent>.{2,})$"
)
_NONREDUCTION_RE: Final = re.compile(
    r"^(?P<primary>.+?)(?P<connector>だけで)[、,]"
    r"(?P<limit>.+?まで.*?(?:決め|判断|断定|みな|扱|とは限|わけでは).*)$"
)
_WITHHELD_ACTION_RE: Final = re.compile(
    r"^(?P<lifecycle>.{2,}?(?:ず|ないで))[、,](?P<remainder>.{2,})$"
)
_BALANCED_RE: Final = re.compile(
    r"^(?P<primary>.+?)も(?P<secondary>.+?)も[、,]"
    r"(?P<connector>どちらか一方).+$"
)
_SIMULTANEOUS_MARKER_RE: Final = re.compile(
    r"^(?P<marker>同時に)(?=[、,\s]|$)"
)
_SEPARATION_MARKER_RE: Final = re.compile(
    r"^(?P<marker>(?:それ|これ)とは?別に)(?=[、,\s]|$)"
)

_MARKER_POLICY_SHA256: Final = artifact_sha256(
    {
        "policy_version": GROUNDED_RELATION_CONSTRUCTION_MARKER_POLICY_VERSION,
        "closed_marker_codes": [
            "explicit_separation_connector",
            "explicit_simultaneous_connector",
        ],
        "closed_source_markers": [
            "(?:それ|これ)とは?別に",
            "同時に",
        ],
        "position": "to_endpoint_span_prefix",
        "closed_source_signatures": [
            {
                "marker_code": "explicit_simultaneous_connector",
                "source_relation_type": "uncertain_connection",
                "source_grounding_kind": "bounded_structural_inference",
                "source_retention": "should",
            },
            {
                "marker_code": "explicit_separation_connector",
                "source_relation_type": "continuation_or_refusal",
                "source_grounding_kind": "user_stated_relation",
                "source_retention": "required",
                "source_relation_ids": ["whole_input_source_order"],
                "source_meaning_arc_keys": ["whole_input:source_order"],
            },
        ],
        "requires_adjacent_required_text_endpoints": True,
        "requires_no_competing_required_relation": True,
    }
)


class GroundedRelationConstructionAuthoritySuccessorError(ValueError):
    """Fail-closed error containing only one stable body-free code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class GroundedSourceOwnerParticipation:
    participation_id: str
    parent_nucleus_id: str
    construction_slot_id: str
    target_owner_kind: Literal["nucleus", "semantic_unit"]
    target_owner_id: str
    owner_resolution: Literal[
        "exact_semantic_unit",
        "crosses_semantic_unit_boundary",
        "parent_nucleus_fallback",
    ]
    source_span_id: str
    intersection_start_index: int
    intersection_end_index: int
    semantic_equivalence_authorized: bool = False


@dataclass(frozen=True)
class GroundedConstructionInstance:
    construction_instance_id: str
    parent_nucleus_id: str
    construction_code: str
    source_field: Literal["memo", "memo_action"]
    source_field_role: Literal["thought", "action"]
    source_span_id: str
    evidence_alias_ids: tuple[str, ...]
    instance_start_index: int
    instance_end_index: int
    slot_ids: tuple[str, ...]
    participation_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroundedConstructionSlot:
    construction_slot_id: str
    construction_instance_id: str
    lexical_role_kind: str
    construction_position: str
    source_field: Literal["memo", "memo_action"]
    source_field_role: Literal["thought", "action"]
    source_span_id: str
    slot_start_index: int
    slot_end_index: int
    evidence_alias_ids: tuple[str, ...]
    participation_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroundedConstructionIntervalEdge:
    left_construction_instance_id: str
    right_construction_instance_id: str
    range_relation: Literal[
        "disjoint",
        "contains",
        "contained_by",
        "partial_overlap",
        "coextensive",
    ]


@dataclass(frozen=True)
class GroundedExperimentRelationAuthority:
    experiment_relation_id: str
    authority_basis: Literal[
        "grounded_plan_projection",
        "source_explicit_refinement",
    ]
    source_relation_id: str
    refines_source_relation_id: str | None
    source_relation_type: str
    effective_relation_type: str
    source_grounding_kind: str
    source_certainty: float
    source_from_nucleus_id: str
    source_to_nucleus_id: str
    source_relation_ids: tuple[str, ...]
    source_meaning_arc_keys: tuple[str, ...]
    from_source_owner_id: str
    to_source_owner_id: str
    direction: Literal["source_to_target", "bidirectional"]
    source_retention: str
    experiment_retention: Literal[
        "source_projection",
        "experiment_required_refinement",
    ]
    evidence_alias_ids: tuple[str, ...]
    marker_code: Literal[
        "explicit_separation_connector",
        "explicit_simultaneous_connector",
    ] | None
    marker_policy_version: str | None
    marker_policy_sha256: str | None
    marker_source_span_id: str | None
    marker_start_index: int | None
    marker_end_index: int | None


@dataclass(frozen=True)
class GroundedLexicalSemanticLinkBinding:
    source_semantic_link_id: str
    source_span_id: str
    connective_code: str
    relation_type: str
    from_semantic_unit_id: str
    to_semantic_unit_id: str
    direction: Literal["source_to_target", "bidirectional"]
    required: bool

    @property
    def from_source_owner_id(self) -> str:
        """Compatibility view; the closed owner remains a semantic unit."""

        return self.from_semantic_unit_id

    @property
    def to_source_owner_id(self) -> str:
        """Compatibility view; the closed owner remains a semantic unit."""

        return self.to_semantic_unit_id


@dataclass(frozen=True)
class GroundedExplicitUnknownAffectedOwner:
    owner_kind: Literal["nucleus", "semantic_unit"]
    owner_id: str


@dataclass(frozen=True)
class GroundedExplicitUnknownAuthority:
    source_unknown_id: str
    dimension: str
    source_span_id: str
    affected_source_owners: tuple[GroundedExplicitUnknownAffectedOwner, ...]
    lexical_role_kind: Literal["unknown_or_limit"]
    required: bool


@dataclass(frozen=True)
class GroundedSuccessorAuthorityResourceCounts:
    required_text_parent_nucleus_count: int
    plan_relation_count: int
    semantic_unit_count: int
    semantic_link_count: int
    source_explicit_unknown_count: int
    construction_instance_count: int
    lexical_construction_slot_count: int
    source_owner_participation_count: int
    interval_edge_count: int
    effective_relation_count: int


@dataclass(frozen=True)
class GroundedSuccessorAuthorityResourceBounds:
    max_lexical_construction_slots: int
    max_construction_instances: int
    max_instances_per_parent_source_span: int
    max_source_owner_participations_per_slot: int
    max_source_owner_participations: int
    exact_effective_relations: int
    exact_semantic_links: int
    exact_explicit_unknowns: int
    max_chargeable_role_endpoint_unknown_records: int


@dataclass(frozen=True)
class GroundedRelationConstructionAuthoritySuccessor:
    schema_version: str
    adapter_version: str
    marker_policy_version: str
    marker_policy_sha256: str
    git_baseline_commit: str
    git_baseline_tree: str
    plan_commitment_sha256: str
    semantic_restatement_witness_sha256: str
    construction_instances: tuple[GroundedConstructionInstance, ...]
    construction_slots: tuple[GroundedConstructionSlot, ...]
    source_owner_participations: tuple[GroundedSourceOwnerParticipation, ...]
    interval_edges: tuple[GroundedConstructionIntervalEdge, ...]
    relation_authorities: tuple[GroundedExperimentRelationAuthority, ...]
    semantic_link_bindings: tuple[GroundedLexicalSemanticLinkBinding, ...]
    explicit_unknown_authorities: tuple[GroundedExplicitUnknownAuthority, ...]
    resource_counts: GroundedSuccessorAuthorityResourceCounts
    resource_bounds: GroundedSuccessorAuthorityResourceBounds
    authority_sha256: str
    experimental_only: bool = True
    body_free: bool = True
    runtime_connected: bool = False

    def __deepcopy__(
        self,
        memo: dict[int, Any],
    ) -> "GroundedRelationConstructionAuthoritySuccessor":
        # Preserve the module-owned request-local origin capability.
        return self


def grounded_successor_internal_link_for_construction(
    construction_code: str,
) -> str:
    try:
        return _INTERNAL_LINK_BY_CONSTRUCTION[construction_code]
    except (KeyError, TypeError) as exc:
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_CONSTRUCTION_CODE_INVALID"
        ) from exc


def _project(value: Any) -> Any:
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        return format(value, ".17g")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            row.name: _project(getattr(value, row.name))
            for row in fields(value)
        }
    if type(value) in {tuple, list}:
        return [_project(item) for item in value]
    if type(value) in {set, frozenset}:
        return sorted((_project(item) for item in value), key=repr)
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_PROJECTION_INVALID"
            )
        return {key: _project(value[key]) for key in sorted(value)}
    raise GroundedRelationConstructionAuthoritySuccessorError(
        "SUCCESSOR_AUTHORITY_PROJECTION_INVALID"
    )


def _source_field_role(value: str) -> Literal["thought", "action"]:
    if value == "memo":
        return "thought"
    if value == "memo_action":
        return "action"
    raise GroundedRelationConstructionAuthoritySuccessorError(
        "SUCCESSOR_AUTHORITY_SOURCE_FIELD_INVALID"
    )


def _trim_range(text: str, start: int, end: int) -> tuple[int, int]:
    trim = " \t\r\n\u3000、,。．.!！?？"
    while start < end and text[start] in trim:
        start += 1
    while end > start and text[end - 1] in trim:
        end -= 1
    return start, end


def _required_text_nuclei(
    plan: GroundedObservationPlan,
) -> tuple[GroundedSemanticNucleus, ...]:
    required = frozenset(plan.coverage_requirements.required_nucleus_ids)
    return tuple(
        row
        for row in plan.nuclei
        if row.nucleus_id in required
        and bool(row.source_fields)
        and set(row.source_fields) <= _TEXT_SOURCE_FIELDS
    )


def _validated_sources(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[tuple[Any, ...], GroundedSemanticRestatementWitness]:
    if type(plan) is not GroundedObservationPlan:
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_PLAN_INVALID"
        )
    if type(resolver) is not EvidenceSpanResolver:
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_RESOLVER_INVALID"
        )
    try:
        if validate_grounded_observation_plan(plan, resolver):
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_PLAN_INVALID"
            )
        spans = tuple(resolver.resolve(row) for row in resolver.span_ids)
        restatement = build_grounded_semantic_restatement_witness(
            plan,
            resolver,
        )
        if validate_grounded_semantic_restatement_witness(
            restatement,
            plan=plan,
            resolver=resolver,
        ):
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_RESTATEMENT_INVALID"
            )
    except GroundedRelationConstructionAuthoritySuccessorError:
        raise
    except (
        AttributeError,
        EvidenceLedgerResolutionError,
        GroundedSemanticRestatementError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_SOURCE_INVALID"
        ) from exc
    return spans, restatement


def _plan_commitment_sha256(plan: GroundedObservationPlan) -> str:
    return artifact_sha256(
        {
            "commitment_kind": "byte_frozen_grounded_observation_plan",
            "schema_version": GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_SCHEMA,
            "plan_body_free_meta": _project(plan.as_body_free_meta()),
        }
    )


@dataclass(frozen=True)
class _Pattern:
    code: str
    expression: re.Pattern[str]
    groups: tuple[tuple[str, str, str], ...]
    action_only: bool = False


_PRIMARY_PATTERNS: Final = (
    _Pattern(
        "explicit_contrast",
        _EXPLICIT_CONTRAST_RE,
        (
            ("antecedent", "antecedent_predication", "antecedent"),
            ("connector", "transition_or_relation", "connector"),
            ("consequent", "consequent_predication", "consequent"),
        ),
    ),
    _Pattern(
        "ordered_sequence",
        _ORDERED_SEQUENCE_RE,
        (
            ("antecedent", "antecedent_predication", "antecedent"),
            ("connector", "transition_or_relation", "connector"),
            ("consequent", "consequent_predication", "consequent"),
        ),
    ),
    _Pattern(
        "withheld_action",
        _WITHHELD_ACTION_RE,
        (("lifecycle", "action_lifecycle", "lifecycle"),),
        action_only=True,
    ),
    _Pattern(
        "explicit_coexistence",
        _COEXISTENCE_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("secondary", "referent_secondary", "secondary"),
            ("connector", "transition_or_relation", "connector"),
        ),
    ),
    _Pattern(
        "balanced_consideration",
        _BALANCED_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("secondary", "referent_secondary", "secondary"),
            ("connector", "transition_or_relation", "connector"),
        ),
    ),
    _Pattern(
        "parallel_addition",
        _PARALLEL_ADDITION_RE,
        (
            ("antecedent", "antecedent_predication", "antecedent"),
            ("connector", "transition_or_relation", "connector"),
            ("consequent", "consequent_predication", "consequent"),
        ),
    ),
    _Pattern(
        "nonreduction_boundary",
        _NONREDUCTION_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("connector", "transition_or_relation", "connector"),
            ("limit", "unknown_or_limit", "limit"),
        ),
    ),
    _Pattern(
        "comparative_assessment",
        _COMPARATIVE_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("quality", "state_or_quality", "quality"),
        ),
    ),
    _Pattern(
        "choice_uncertainty",
        _CHOICE_UNCERTAINTY_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("limit", "unknown_or_limit", "limit"),
        ),
    ),
    _Pattern(
        "decision_timing",
        _DECISION_TIMING_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("limit", "unknown_or_limit", "limit"),
        ),
    ),
    _Pattern(
        "purpose_action",
        _PURPOSE_ACTION_RE,
        (
            ("connector", "transition_or_relation", "connector"),
            ("predicate", "predicate_or_event", "predicate"),
        ),
    ),
)
_FALLBACK_PATTERNS: Final = (
    _Pattern(
        "reported_self_assessment",
        _SELF_ASSESSMENT_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("quality", "state_or_quality", "quality"),
        ),
    ),
    _Pattern(
        "particle_object",
        _PARTICLE_OBJECT_RE,
        (
            ("primary", "referent_primary", "primary"),
            ("predicate", "predicate_or_event", "predicate"),
        ),
    ),
)


def _matching_patterns(
    nucleus: GroundedSemanticNucleus,
    span: Any,
) -> tuple[tuple[_Pattern, re.Match[str]], ...]:
    raw = str(getattr(span, "raw_text", ""))
    source_field = str(getattr(span, "source_field", ""))
    matches: list[tuple[_Pattern, re.Match[str]]] = []
    for pattern in _PRIMARY_PATTERNS:
        if pattern.action_only and not (
            source_field == "memo_action" and nucleus.kind == "action"
        ):
            continue
        match = pattern.expression.fullmatch(raw)
        if match is not None:
            matches.append((pattern, match))
    if matches:
        return tuple(matches)
    for pattern in _FALLBACK_PATTERNS:
        match = pattern.expression.fullmatch(raw)
        if match is None:
            continue
        if (
            pattern.code == "particle_object"
            and _AMBIGUOUS_PARTICLE_OBJECT_SCOPE_RE.search(
                match.group("primary")
            )
        ):
            continue
        return ((pattern, match),)
    return ()


def _construction_identity(
    *,
    plan_commitment_sha256: str,
    restatement_sha256: str,
    parent_nucleus_id: str,
    source_span_id: str,
    start_index: int,
    end_index: int,
    construction_code: str,
) -> str:
    return "successor_construction:i" + artifact_sha256(
        {
            "domain": "rc0028_relation_construction_instance.v2",
            "plan_commitment_sha256": plan_commitment_sha256,
            "semantic_restatement_witness_sha256": restatement_sha256,
            "parent_nucleus_id": parent_nucleus_id,
            "source_span_id": source_span_id,
            "start_index": start_index,
            "end_index": end_index,
            "construction_code": construction_code,
        }
    )[:24]


def _slot_identity(
    *,
    instance_id: str,
    source_span_id: str,
    start_index: int,
    end_index: int,
    role_kind: str,
    position: str,
) -> str:
    return "successor_construction_slot:s" + artifact_sha256(
        {
            "domain": "rc0028_relation_construction_slot.v2",
            "construction_instance_id": instance_id,
            "source_span_id": source_span_id,
            "start_index": start_index,
            "end_index": end_index,
            "lexical_role_kind": role_kind,
            "construction_position": position,
        }
    )[:24]


def _build_constructions(
    *,
    plan: GroundedObservationPlan,
    span_by_id: Mapping[str, Any],
    restatement: GroundedSemanticRestatementWitness,
    plan_commitment_sha256: str,
) -> tuple[
    tuple[GroundedConstructionInstance, ...],
    tuple[GroundedConstructionSlot, ...],
]:
    instances: list[GroundedConstructionInstance] = []
    slots: list[GroundedConstructionSlot] = []
    for nucleus in _required_text_nuclei(plan):
        if len(nucleus.source_span_ids) != 1:
            continue
        span_id = nucleus.source_span_ids[0]
        span = span_by_id.get(span_id)
        if span is None:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_SOURCE_SPAN_UNRESOLVED"
            )
        source_field = str(getattr(span, "source_field", ""))
        if source_field not in _TEXT_SOURCE_FIELDS:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_SOURCE_FIELD_INVALID"
            )
        raw = str(getattr(span, "raw_text", ""))
        matches = _matching_patterns(nucleus, span)
        if len(matches) > MAX_CONSTRUCTION_INSTANCES_PER_PARENT_SPAN:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_RESOURCE_BOUND_EXCEEDED"
            )
        parent_slot_count = sum(len(row.groups) for row, _match in matches)
        if parent_slot_count > MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_RESOURCE_BOUND_EXCEEDED"
            )
        for pattern, match in matches:
            instance_start, instance_end = _trim_range(raw, *match.span())
            if not 0 <= instance_start < instance_end <= len(raw):
                raise GroundedRelationConstructionAuthoritySuccessorError(
                    "SUCCESSOR_AUTHORITY_CONSTRUCTION_RANGE_INVALID"
                )
            instance_id = _construction_identity(
                plan_commitment_sha256=plan_commitment_sha256,
                restatement_sha256=restatement.witness_sha256,
                parent_nucleus_id=nucleus.nucleus_id,
                source_span_id=span_id,
                start_index=instance_start,
                end_index=instance_end,
                construction_code=pattern.code,
            )
            instance_slots: list[GroundedConstructionSlot] = []
            roles: set[str] = set()
            for group_name, role_kind, position in pattern.groups:
                start, end = _trim_range(raw, *match.span(group_name))
                if (
                    role_kind not in _LEXICAL_ROLE_KINDS
                    or position not in _CONSTRUCTION_POSITIONS
                    or role_kind in roles
                    or not instance_start <= start < end <= instance_end
                ):
                    raise GroundedRelationConstructionAuthoritySuccessorError(
                        "SUCCESSOR_AUTHORITY_CONSTRUCTION_SLOT_INVALID"
                    )
                roles.add(role_kind)
                instance_slots.append(
                    GroundedConstructionSlot(
                        construction_slot_id=_slot_identity(
                            instance_id=instance_id,
                            source_span_id=span_id,
                            start_index=start,
                            end_index=end,
                            role_kind=role_kind,
                            position=position,
                        ),
                        construction_instance_id=instance_id,
                        lexical_role_kind=role_kind,
                        construction_position=position,
                        source_field=source_field,  # type: ignore[arg-type]
                        source_field_role=_source_field_role(source_field),
                        source_span_id=span_id,
                        slot_start_index=start,
                        slot_end_index=end,
                        evidence_alias_ids=(span_id,),
                        participation_ids=(),
                    )
                )
            instances.append(
                GroundedConstructionInstance(
                    construction_instance_id=instance_id,
                    parent_nucleus_id=nucleus.nucleus_id,
                    construction_code=pattern.code,
                    source_field=source_field,  # type: ignore[arg-type]
                    source_field_role=_source_field_role(source_field),
                    source_span_id=span_id,
                    evidence_alias_ids=(span_id,),
                    instance_start_index=instance_start,
                    instance_end_index=instance_end,
                    slot_ids=tuple(
                        row.construction_slot_id for row in instance_slots
                    ),
                    participation_ids=(),
                )
            )
            slots.extend(instance_slots)
    if len({row.construction_instance_id for row in instances}) != len(instances):
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_CONSTRUCTION_ID_DUPLICATE"
        )
    if len({row.construction_slot_id for row in slots}) != len(slots):
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_CONSTRUCTION_SLOT_ID_DUPLICATE"
        )
    return tuple(instances), tuple(slots)


def _participation_identity(
    *,
    slot_id: str,
    parent_nucleus_id: str,
    owner_kind: str,
    owner_id: str,
    resolution: str,
    source_span_id: str,
    start_index: int,
    end_index: int,
) -> str:
    return "successor_participation:p" + artifact_sha256(
        {
            "domain": "rc0028_source_owner_participation.v2",
            "construction_slot_id": slot_id,
            "parent_nucleus_id": parent_nucleus_id,
            "target_owner_kind": owner_kind,
            "target_owner_id": owner_id,
            "owner_resolution": resolution,
            "source_span_id": source_span_id,
            "intersection_start_index": start_index,
            "intersection_end_index": end_index,
        }
    )[:24]


def _attach_participations(
    *,
    instances: Sequence[GroundedConstructionInstance],
    slots: Sequence[GroundedConstructionSlot],
    restatement: GroundedSemanticRestatementWitness,
) -> tuple[
    tuple[GroundedConstructionInstance, ...],
    tuple[GroundedConstructionSlot, ...],
    tuple[GroundedSourceOwnerParticipation, ...],
]:
    instance_by_id = {row.construction_instance_id: row for row in instances}
    units_by_parent_span: dict[tuple[str, str], list[Any]] = {}
    for unit in restatement.semantic_units:
        units_by_parent_span.setdefault(
            (unit.parent_nucleus_id, unit.source_span_id), []
        ).append(unit)
    for rows in units_by_parent_span.values():
        rows.sort(key=lambda row: (row.start_index, row.end_index, row.unit_id))

    attached_slots: list[GroundedConstructionSlot] = []
    participations: list[GroundedSourceOwnerParticipation] = []
    for slot in slots:
        instance = instance_by_id.get(slot.construction_instance_id)
        if instance is None:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_CONSTRUCTION_ORPHAN"
            )
        units = units_by_parent_span.get(
            (instance.parent_nucleus_id, slot.source_span_id), []
        )
        intersections = [
            (
                unit,
                max(slot.slot_start_index, unit.start_index),
                min(slot.slot_end_index, unit.end_index),
            )
            for unit in units
            if max(slot.slot_start_index, unit.start_index)
            < min(slot.slot_end_index, unit.end_index)
        ]
        rows: list[GroundedSourceOwnerParticipation] = []
        if not units:
            members = (
                (
                    "nucleus",
                    instance.parent_nucleus_id,
                    "parent_nucleus_fallback",
                    slot.slot_start_index,
                    slot.slot_end_index,
                ),
            )
        else:
            if not intersections:
                raise GroundedRelationConstructionAuthoritySuccessorError(
                    "SUCCESSOR_AUTHORITY_PARTICIPATION_UNRESOLVED"
                )
            exact = (
                len(intersections) == 1
                and intersections[0][1] == slot.slot_start_index
                and intersections[0][2] == slot.slot_end_index
            )
            members = tuple(
                (
                    "semantic_unit",
                    unit.unit_id,
                    (
                        "exact_semantic_unit"
                        if exact
                        else "crosses_semantic_unit_boundary"
                    ),
                    start,
                    end,
                )
                for unit, start, end in intersections
            )
        if len(members) > MAX_SOURCE_OWNER_PARTICIPATIONS_PER_SLOT:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_RESOURCE_BOUND_EXCEEDED"
            )
        for owner_kind, owner_id, resolution, start, end in members:
            participation_id = _participation_identity(
                slot_id=slot.construction_slot_id,
                parent_nucleus_id=instance.parent_nucleus_id,
                owner_kind=owner_kind,
                owner_id=owner_id,
                resolution=resolution,
                source_span_id=slot.source_span_id,
                start_index=start,
                end_index=end,
            )
            rows.append(
                GroundedSourceOwnerParticipation(
                    participation_id=participation_id,
                    parent_nucleus_id=instance.parent_nucleus_id,
                    construction_slot_id=slot.construction_slot_id,
                    target_owner_kind=owner_kind,  # type: ignore[arg-type]
                    target_owner_id=owner_id,
                    owner_resolution=resolution,  # type: ignore[arg-type]
                    source_span_id=slot.source_span_id,
                    intersection_start_index=start,
                    intersection_end_index=end,
                    semantic_equivalence_authorized=False,
                )
            )
        participation_ids = tuple(row.participation_id for row in rows)
        attached_slots.append(replace(slot, participation_ids=participation_ids))
        participations.extend(rows)

    ids_by_instance: dict[str, set[str]] = {
        row.construction_instance_id: set() for row in instances
    }
    for slot in attached_slots:
        ids_by_instance[slot.construction_instance_id].update(
            slot.participation_ids
        )
    attached_instances = tuple(
        replace(
            row,
            participation_ids=tuple(
                sorted(ids_by_instance[row.construction_instance_id])
            ),
        )
        for row in instances
    )
    if len({row.participation_id for row in participations}) != len(
        participations
    ):
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_PARTICIPATION_ID_DUPLICATE"
        )
    return attached_instances, tuple(attached_slots), tuple(participations)


def _interval_relation(
    left: GroundedConstructionInstance,
    right: GroundedConstructionInstance,
) -> str:
    if (
        left.instance_start_index == right.instance_start_index
        and left.instance_end_index == right.instance_end_index
    ):
        return "coextensive"
    if (
        left.instance_end_index <= right.instance_start_index
        or right.instance_end_index <= left.instance_start_index
    ):
        return "disjoint"
    if (
        left.instance_start_index <= right.instance_start_index
        and left.instance_end_index >= right.instance_end_index
    ):
        return "contains"
    if (
        right.instance_start_index <= left.instance_start_index
        and right.instance_end_index >= left.instance_end_index
    ):
        return "contained_by"
    return "partial_overlap"


def _build_interval_edges(
    instances: Sequence[GroundedConstructionInstance],
) -> tuple[GroundedConstructionIntervalEdge, ...]:
    groups: dict[tuple[str, str], list[GroundedConstructionInstance]] = {}
    for row in instances:
        groups.setdefault(
            (row.parent_nucleus_id, row.source_span_id), []
        ).append(row)
    edges: list[GroundedConstructionIntervalEdge] = []
    for key in sorted(groups):
        rows = sorted(
            groups[key], key=lambda row: row.construction_instance_id
        )
        if len(rows) > MAX_CONSTRUCTION_INSTANCES_PER_PARENT_SPAN:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_RESOURCE_BOUND_EXCEEDED"
            )
        for index, left in enumerate(rows):
            for right in rows[index + 1 :]:
                edges.append(
                    GroundedConstructionIntervalEdge(
                        left_construction_instance_id=(
                            left.construction_instance_id
                        ),
                        right_construction_instance_id=(
                            right.construction_instance_id
                        ),
                        range_relation=_interval_relation(  # type: ignore[arg-type]
                            left,
                            right,
                        ),
                    )
                )
    return tuple(edges)


def _required_text_endpoint_positions(
    plan: GroundedObservationPlan,
) -> dict[str, int]:
    return {
        row.nucleus_id: index
        for index, row in enumerate(_required_text_nuclei(plan))
    }


def _coexistence_marker(
    relation: GroundedSemanticRelation,
    *,
    plan: GroundedObservationPlan,
    span_by_id: Mapping[str, Any],
) -> tuple[
    Literal[
        "explicit_separation_connector",
        "explicit_simultaneous_connector",
    ],
    str,
    int,
    int,
] | None:
    marker_code: Literal[
        "explicit_separation_connector",
        "explicit_simultaneous_connector",
    ]
    marker_pattern: re.Pattern[str]
    if (
        relation.type == "uncertain_connection"
        and relation.grounding_kind == "bounded_structural_inference"
        and relation.retention == "should"
    ):
        marker_code = "explicit_simultaneous_connector"
        marker_pattern = _SIMULTANEOUS_MARKER_RE
    elif (
        relation.type == "continuation_or_refusal"
        and relation.grounding_kind == "user_stated_relation"
        and relation.retention == "required"
        and tuple(relation.source_relation_ids)
        == ("whole_input_source_order",)
        and tuple(relation.source_meaning_arc_keys)
        == ("whole_input:source_order",)
    ):
        marker_code = "explicit_separation_connector"
        marker_pattern = _SEPARATION_MARKER_RE
    else:
        return None
    nucleus_by_id = {row.nucleus_id: row for row in plan.nuclei}
    left = nucleus_by_id.get(relation.from_nucleus_id)
    right = nucleus_by_id.get(relation.to_nucleus_id)
    if left is None or right is None:
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_RELATION_ENDPOINT_UNRESOLVED"
        )
    positions = _required_text_endpoint_positions(plan)
    if (
        relation.from_nucleus_id not in positions
        or relation.to_nucleus_id not in positions
        or positions[relation.to_nucleus_id]
        != positions[relation.from_nucleus_id] + 1
    ):
        return None
    competitors = tuple(
        row
        for row in plan.relations
        if row.relation_id != relation.relation_id
        and row.retention == "required"
        and {row.from_nucleus_id, row.to_nucleus_id}
        == {relation.from_nucleus_id, relation.to_nucleus_id}
    )
    marker_rows: list[tuple[str, int, int]] = []
    for span_id in right.source_span_ids:
        if span_id not in relation.source_span_ids:
            continue
        span = span_by_id.get(span_id)
        if span is None:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_SOURCE_SPAN_UNRESOLVED"
            )
        match = marker_pattern.search(
            str(getattr(span, "raw_text", ""))
        )
        if match is not None:
            marker_rows.append((span_id, *match.span("marker")))
    if not marker_rows:
        return None
    if len(marker_rows) != 1 or competitors:
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_RELATION_REFINEMENT_CONFLICT"
        )
    marker_span_id, marker_start, marker_end = marker_rows[0]
    return marker_code, marker_span_id, marker_start, marker_end


def _build_relation_authorities(
    *,
    plan: GroundedObservationPlan,
    span_by_id: Mapping[str, Any],
    plan_commitment_sha256: str,
) -> tuple[GroundedExperimentRelationAuthority, ...]:
    rows: list[GroundedExperimentRelationAuthority] = []
    for relation in sorted(plan.relations, key=lambda row: row.relation_id):
        if relation.type not in _RELATION_TYPES:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_RELATION_TYPE_INVALID"
            )
        marker = _coexistence_marker(
            relation,
            plan=plan,
            span_by_id=span_by_id,
        )
        refined = marker is not None
        effective_type = "coexistence" if refined else relation.type
        direction = (
            "bidirectional"
            if effective_type == "coexistence"
            else "source_to_target"
        )
        marker_code, marker_span_id, marker_start, marker_end = (
            marker if marker is not None else (None, None, None, None)
        )
        identity = {
            "domain": "rc0028_experiment_relation_authority.v2",
            "plan_commitment_sha256": plan_commitment_sha256,
            "source_relation_id": relation.relation_id,
            "authority_basis": (
                "source_explicit_refinement"
                if refined
                else "grounded_plan_projection"
            ),
            "effective_relation_type": effective_type,
            "marker_policy_sha256": _MARKER_POLICY_SHA256 if refined else None,
            "marker_source_span_id": marker_span_id,
            "marker_start_index": marker_start,
            "marker_end_index": marker_end,
        }
        rows.append(
            GroundedExperimentRelationAuthority(
                experiment_relation_id=(
                    "successor_relation:r" + artifact_sha256(identity)[:24]
                ),
                authority_basis=(
                    "source_explicit_refinement"
                    if refined
                    else "grounded_plan_projection"
                ),
                source_relation_id=relation.relation_id,
                refines_source_relation_id=(
                    relation.relation_id if refined else None
                ),
                source_relation_type=relation.type,
                effective_relation_type=effective_type,
                source_grounding_kind=relation.grounding_kind,
                source_certainty=relation.certainty,
                source_from_nucleus_id=relation.from_nucleus_id,
                source_to_nucleus_id=relation.to_nucleus_id,
                source_relation_ids=relation.source_relation_ids,
                source_meaning_arc_keys=relation.source_meaning_arc_keys,
                from_source_owner_id=relation.from_nucleus_id,
                to_source_owner_id=relation.to_nucleus_id,
                direction=direction,  # type: ignore[arg-type]
                source_retention=relation.retention,
                experiment_retention=(
                    "experiment_required_refinement"
                    if refined
                    else "source_projection"
                ),
                evidence_alias_ids=relation.source_span_ids,
                marker_code=marker_code,
                marker_policy_version=(
                    GROUNDED_RELATION_CONSTRUCTION_MARKER_POLICY_VERSION
                    if refined
                    else None
                ),
                marker_policy_sha256=(
                    _MARKER_POLICY_SHA256 if refined else None
                ),
                marker_source_span_id=marker_span_id,
                marker_start_index=marker_start,
                marker_end_index=marker_end,
            )
        )
    if len(rows) != len(plan.relations) or len(
        {row.source_relation_id for row in rows}
    ) != len(rows):
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_RELATION_PROJECTION_INCOMPLETE"
        )
    return tuple(rows)


def _build_semantic_link_bindings(
    restatement: GroundedSemanticRestatementWitness,
) -> tuple[GroundedLexicalSemanticLinkBinding, ...]:
    return tuple(
        GroundedLexicalSemanticLinkBinding(
            source_semantic_link_id=row.link_id,
            source_span_id=row.source_span_id,
            connective_code=row.connective_code,
            relation_type=row.relation_type,
            from_semantic_unit_id=row.from_unit_id,
            to_semantic_unit_id=row.to_unit_id,
            direction=row.relation_direction,
            required=row.required,
        )
        for row in restatement.semantic_links
    )


def _build_explicit_unknown_authorities(
    *,
    plan: GroundedObservationPlan,
    restatement: GroundedSemanticRestatementWitness,
) -> tuple[GroundedExplicitUnknownAuthority, ...]:
    nucleus_ids = frozenset(row.nucleus_id for row in plan.nuclei)
    unit_ids = frozenset(row.unit_id for row in restatement.semantic_units)
    rows: list[GroundedExplicitUnknownAuthority] = []
    for row in restatement.explicit_unknowns:
        if row.dimension not in _EXPLICIT_UNKNOWN_DIMENSIONS:
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_EXPLICIT_UNKNOWN_DIMENSION_INVALID"
            )
        affected: list[GroundedExplicitUnknownAffectedOwner] = []
        for owner_id in row.affected_unit_ids:
            if owner_id in unit_ids:
                owner_kind = "semantic_unit"
            elif owner_id in nucleus_ids:
                owner_kind = "nucleus"
            else:
                raise GroundedRelationConstructionAuthoritySuccessorError(
                    "SUCCESSOR_AUTHORITY_EXPLICIT_UNKNOWN_OWNER_UNRESOLVED"
                )
            affected.append(
                GroundedExplicitUnknownAffectedOwner(
                    owner_kind=owner_kind,  # type: ignore[arg-type]
                    owner_id=owner_id,
                )
            )
        if not affected or len({item.owner_id for item in affected}) != len(
            affected
        ):
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_EXPLICIT_UNKNOWN_OWNER_INVALID"
            )
        rows.append(
            GroundedExplicitUnknownAuthority(
                source_unknown_id=row.unknown_id,
                dimension=row.dimension,
                source_span_id=row.source_span_id,
                affected_source_owners=tuple(affected),
                lexical_role_kind="unknown_or_limit",
                required=row.required,
            )
        )
    if len({row.source_unknown_id for row in rows}) != len(rows):
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_EXPLICIT_UNKNOWN_ID_DUPLICATE"
        )
    return tuple(rows)


def _authority_payload(
    *,
    schema_version: str,
    adapter_version: str,
    marker_policy_version: str,
    marker_policy_sha256: str,
    git_baseline_commit: str,
    git_baseline_tree: str,
    plan_commitment_sha256: str,
    semantic_restatement_witness_sha256: str,
    construction_instances: Sequence[GroundedConstructionInstance],
    construction_slots: Sequence[GroundedConstructionSlot],
    source_owner_participations: Sequence[GroundedSourceOwnerParticipation],
    interval_edges: Sequence[GroundedConstructionIntervalEdge],
    relation_authorities: Sequence[GroundedExperimentRelationAuthority],
    semantic_link_bindings: Sequence[GroundedLexicalSemanticLinkBinding],
    explicit_unknown_authorities: Sequence[GroundedExplicitUnknownAuthority],
    resource_counts: GroundedSuccessorAuthorityResourceCounts,
    resource_bounds: GroundedSuccessorAuthorityResourceBounds,
    experimental_only: bool,
    body_free: bool,
    runtime_connected: bool,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "adapter_version": adapter_version,
        "marker_policy_version": marker_policy_version,
        "marker_policy_sha256": marker_policy_sha256,
        "git_baseline_commit": git_baseline_commit,
        "git_baseline_tree": git_baseline_tree,
        "plan_commitment_sha256": plan_commitment_sha256,
        "semantic_restatement_witness_sha256": (
            semantic_restatement_witness_sha256
        ),
        "construction_instances": _project(tuple(construction_instances)),
        "construction_slots": _project(tuple(construction_slots)),
        "source_owner_participations": _project(
            tuple(source_owner_participations)
        ),
        "interval_edges": _project(tuple(interval_edges)),
        "relation_authorities": _project(tuple(relation_authorities)),
        "semantic_link_bindings": _project(tuple(semantic_link_bindings)),
        "explicit_unknown_authorities": _project(
            tuple(explicit_unknown_authorities)
        ),
        "resource_counts": _project(resource_counts),
        "resource_bounds": _project(resource_bounds),
        "experimental_only": experimental_only,
        "body_free": body_free,
        "runtime_connected": runtime_connected,
    }


@dataclass(frozen=True, slots=True, repr=False)
class _GroundedRelationConstructionAuthorityOrigin:
    plan: GroundedObservationPlan
    evidence_spans: tuple[Any, ...]

    def __repr__(self) -> str:
        return "<_GroundedRelationConstructionAuthorityOrigin request_local>"

    def rebuild(self) -> GroundedRelationConstructionAuthoritySuccessor:
        resolver = EvidenceSpanResolver(self.evidence_spans)
        return _build_grounded_relation_construction_authority_successor(
            self.plan,
            resolver,
            register_origin=False,
        )


def _origin_store():
    registry: dict[
        int,
        tuple[
            weakref.ReferenceType[
                GroundedRelationConstructionAuthoritySuccessor
            ],
            _GroundedRelationConstructionAuthorityOrigin,
        ],
    ] = {}

    def register(
        value: GroundedRelationConstructionAuthoritySuccessor,
        origin: _GroundedRelationConstructionAuthorityOrigin,
    ) -> None:
        if value != origin.rebuild():
            raise GroundedRelationConstructionAuthoritySuccessorError(
                "SUCCESSOR_AUTHORITY_ORIGIN_REGISTRATION_MISMATCH"
            )
        key = id(value)

        def remove(
            reference: weakref.ReferenceType[
                GroundedRelationConstructionAuthoritySuccessor
            ],
            *,
            registry_key: int = key,
        ) -> None:
            current = registry.get(registry_key)
            if current is not None and current[0] is reference:
                registry.pop(registry_key, None)

        reference = weakref.ref(value, remove)
        registry[key] = (reference, origin)

    def resolve(
        value: GroundedRelationConstructionAuthoritySuccessor,
    ) -> _GroundedRelationConstructionAuthorityOrigin | None:
        current = registry.get(id(value))
        if current is None or current[0]() is not value:
            return None
        return current[1]

    return register, resolve


_register_origin, _resolve_origin = _origin_store()


def _build_grounded_relation_construction_authority_successor(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    register_origin: bool,
) -> GroundedRelationConstructionAuthoritySuccessor:
    spans, restatement = _validated_sources(plan, resolver)
    span_by_id = {
        str(getattr(row, "span_id", "")): row for row in spans
    }
    plan_commitment = _plan_commitment_sha256(plan)
    instances, slots = _build_constructions(
        plan=plan,
        span_by_id=span_by_id,
        restatement=restatement,
        plan_commitment_sha256=plan_commitment,
    )
    instances, slots, participations = _attach_participations(
        instances=instances,
        slots=slots,
        restatement=restatement,
    )
    interval_edges = _build_interval_edges(instances)
    relation_authorities = _build_relation_authorities(
        plan=plan,
        span_by_id=span_by_id,
        plan_commitment_sha256=plan_commitment,
    )
    semantic_links = _build_semantic_link_bindings(restatement)
    explicit_unknowns = _build_explicit_unknown_authorities(
        plan=plan,
        restatement=restatement,
    )
    required_text_count = len(_required_text_nuclei(plan))
    resource_bounds = GroundedSuccessorAuthorityResourceBounds(
        max_lexical_construction_slots=(
            MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT
            * required_text_count
        ),
        max_construction_instances=(
            MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT
            * required_text_count
        ),
        max_instances_per_parent_source_span=(
            MAX_CONSTRUCTION_INSTANCES_PER_PARENT_SPAN
        ),
        max_source_owner_participations_per_slot=(
            MAX_SOURCE_OWNER_PARTICIPATIONS_PER_SLOT
        ),
        max_source_owner_participations=(
            MAX_SOURCE_OWNER_PARTICIPATIONS_PER_SLOT
            * MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT
            * required_text_count
        ),
        exact_effective_relations=len(plan.relations),
        exact_semantic_links=len(restatement.semantic_links),
        exact_explicit_unknowns=len(restatement.explicit_unknowns),
        max_chargeable_role_endpoint_unknown_records=(
            MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT
            * required_text_count
            + 2 * len(plan.relations)
            + len(restatement.explicit_unknowns)
        ),
    )
    resource_counts = GroundedSuccessorAuthorityResourceCounts(
        required_text_parent_nucleus_count=required_text_count,
        plan_relation_count=len(plan.relations),
        semantic_unit_count=len(restatement.semantic_units),
        semantic_link_count=len(restatement.semantic_links),
        source_explicit_unknown_count=len(restatement.explicit_unknowns),
        construction_instance_count=len(instances),
        lexical_construction_slot_count=len(slots),
        source_owner_participation_count=len(participations),
        interval_edge_count=len(interval_edges),
        effective_relation_count=len(relation_authorities),
    )
    if (
        len(slots) > resource_bounds.max_lexical_construction_slots
        or len(instances) > resource_bounds.max_construction_instances
        or len(participations)
        > resource_bounds.max_source_owner_participations
        or len(relation_authorities)
        != resource_bounds.exact_effective_relations
        or len(semantic_links) != resource_bounds.exact_semantic_links
        or len(explicit_unknowns) != resource_bounds.exact_explicit_unknowns
    ):
        raise GroundedRelationConstructionAuthoritySuccessorError(
            "SUCCESSOR_AUTHORITY_RESOURCE_BOUND_EXCEEDED"
        )
    payload = _authority_payload(
        schema_version=GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_SCHEMA,
        adapter_version=(
            GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_ADAPTER_VERSION
        ),
        marker_policy_version=(
            GROUNDED_RELATION_CONSTRUCTION_MARKER_POLICY_VERSION
        ),
        marker_policy_sha256=_MARKER_POLICY_SHA256,
        git_baseline_commit=(
            GROUNDED_RELATION_CONSTRUCTION_GIT_BASELINE_COMMIT
        ),
        git_baseline_tree=GROUNDED_RELATION_CONSTRUCTION_GIT_BASELINE_TREE,
        plan_commitment_sha256=plan_commitment,
        semantic_restatement_witness_sha256=restatement.witness_sha256,
        construction_instances=instances,
        construction_slots=slots,
        source_owner_participations=participations,
        interval_edges=interval_edges,
        relation_authorities=relation_authorities,
        semantic_link_bindings=semantic_links,
        explicit_unknown_authorities=explicit_unknowns,
        resource_counts=resource_counts,
        resource_bounds=resource_bounds,
        experimental_only=True,
        body_free=True,
        runtime_connected=False,
    )
    value = GroundedRelationConstructionAuthoritySuccessor(
        schema_version=GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_SCHEMA,
        adapter_version=(
            GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_ADAPTER_VERSION
        ),
        marker_policy_version=(
            GROUNDED_RELATION_CONSTRUCTION_MARKER_POLICY_VERSION
        ),
        marker_policy_sha256=_MARKER_POLICY_SHA256,
        git_baseline_commit=(
            GROUNDED_RELATION_CONSTRUCTION_GIT_BASELINE_COMMIT
        ),
        git_baseline_tree=GROUNDED_RELATION_CONSTRUCTION_GIT_BASELINE_TREE,
        plan_commitment_sha256=plan_commitment,
        semantic_restatement_witness_sha256=restatement.witness_sha256,
        construction_instances=instances,
        construction_slots=slots,
        source_owner_participations=participations,
        interval_edges=interval_edges,
        relation_authorities=relation_authorities,
        semantic_link_bindings=semantic_links,
        explicit_unknown_authorities=explicit_unknowns,
        resource_counts=resource_counts,
        resource_bounds=resource_bounds,
        authority_sha256=artifact_sha256(payload),
        experimental_only=True,
        body_free=True,
        runtime_connected=False,
    )
    if register_origin:
        _register_origin(
            value,
            _GroundedRelationConstructionAuthorityOrigin(
                plan=plan,
                evidence_spans=spans,
            ),
        )
    return value


def build_grounded_relation_construction_authority_successor(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> GroundedRelationConstructionAuthoritySuccessor:
    """Build one deterministic, runtime-disconnected successor authority."""

    return _build_grounded_relation_construction_authority_successor(
        plan,
        resolver,
        register_origin=True,
    )


def validate_grounded_relation_construction_authority_successor(
    value: Any,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Independently rebuild and compare all closed authority collections."""

    if type(value) is not GroundedRelationConstructionAuthoritySuccessor:
        return ("SUCCESSOR_AUTHORITY_TYPE_INVALID",)
    try:
        expected = _build_grounded_relation_construction_authority_successor(
            plan,
            resolver,
            register_origin=False,
        )
    except GroundedRelationConstructionAuthoritySuccessorError as exc:
        return (exc.code,)
    issues: list[str] = []
    scalar_fields = (
        ("schema_version", "SUCCESSOR_AUTHORITY_SCHEMA_MISMATCH"),
        ("adapter_version", "SUCCESSOR_AUTHORITY_ADAPTER_MISMATCH"),
        ("marker_policy_version", "SUCCESSOR_AUTHORITY_MARKER_POLICY_MISMATCH"),
        ("marker_policy_sha256", "SUCCESSOR_AUTHORITY_MARKER_POLICY_MISMATCH"),
        ("git_baseline_commit", "SUCCESSOR_AUTHORITY_GIT_BASELINE_MISMATCH"),
        ("git_baseline_tree", "SUCCESSOR_AUTHORITY_GIT_BASELINE_MISMATCH"),
        ("plan_commitment_sha256", "SUCCESSOR_AUTHORITY_PLAN_COMMITMENT_MISMATCH"),
        (
            "semantic_restatement_witness_sha256",
            "SUCCESSOR_AUTHORITY_RESTATEMENT_COMMITMENT_MISMATCH",
        ),
    )
    for name, code in scalar_fields:
        if getattr(value, name) != getattr(expected, name):
            issues.append(code)
    collection_fields = (
        ("construction_instances", "SUCCESSOR_AUTHORITY_CONSTRUCTIONS_MISMATCH"),
        ("construction_slots", "SUCCESSOR_AUTHORITY_CONSTRUCTION_SLOTS_MISMATCH"),
        (
            "source_owner_participations",
            "SUCCESSOR_AUTHORITY_PARTICIPATIONS_MISMATCH",
        ),
        ("interval_edges", "SUCCESSOR_AUTHORITY_INTERVAL_EDGES_MISMATCH"),
        ("relation_authorities", "SUCCESSOR_AUTHORITY_RELATIONS_MISMATCH"),
        ("semantic_link_bindings", "SUCCESSOR_AUTHORITY_SEMANTIC_LINKS_MISMATCH"),
        (
            "explicit_unknown_authorities",
            "SUCCESSOR_AUTHORITY_EXPLICIT_UNKNOWNS_MISMATCH",
        ),
    )
    for name, code in collection_fields:
        if type(getattr(value, name)) is not tuple or getattr(
            value, name
        ) != getattr(expected, name):
            issues.append(code)
    if type(value.resource_counts) is not GroundedSuccessorAuthorityResourceCounts or (
        value.resource_counts != expected.resource_counts
    ):
        issues.append("SUCCESSOR_AUTHORITY_RESOURCE_COUNTS_MISMATCH")
    if type(value.resource_bounds) is not GroundedSuccessorAuthorityResourceBounds or (
        value.resource_bounds != expected.resource_bounds
    ):
        issues.append("SUCCESSOR_AUTHORITY_RESOURCE_BOUNDS_MISMATCH")
    try:
        presented_payload = _authority_payload(
            schema_version=value.schema_version,
            adapter_version=value.adapter_version,
            marker_policy_version=value.marker_policy_version,
            marker_policy_sha256=value.marker_policy_sha256,
            git_baseline_commit=value.git_baseline_commit,
            git_baseline_tree=value.git_baseline_tree,
            plan_commitment_sha256=value.plan_commitment_sha256,
            semantic_restatement_witness_sha256=(
                value.semantic_restatement_witness_sha256
            ),
            construction_instances=value.construction_instances,
            construction_slots=value.construction_slots,
            source_owner_participations=value.source_owner_participations,
            interval_edges=value.interval_edges,
            relation_authorities=value.relation_authorities,
            semantic_link_bindings=value.semantic_link_bindings,
            explicit_unknown_authorities=value.explicit_unknown_authorities,
            resource_counts=value.resource_counts,
            resource_bounds=value.resource_bounds,
            experimental_only=value.experimental_only,
            body_free=value.body_free,
            runtime_connected=value.runtime_connected,
        )
        presented_hash = artifact_sha256(presented_payload)
    except (
        AttributeError,
        GroundedRelationConstructionAuthoritySuccessorError,
        TypeError,
        ValueError,
    ):
        presented_hash = ""
    if (
        value.authority_sha256 != expected.authority_sha256
        or value.authority_sha256 != presented_hash
    ):
        issues.append("SUCCESSOR_AUTHORITY_HASH_MISMATCH")
    if value.experimental_only is not True:
        issues.append("SUCCESSOR_AUTHORITY_EXPERIMENTAL_ONLY_REQUIRED")
    if value.body_free is not True:
        issues.append("SUCCESSOR_AUTHORITY_BODY_FREE_REQUIRED")
    if value.runtime_connected is not False:
        issues.append("SUCCESSOR_AUTHORITY_RUNTIME_DISCONNECT_REQUIRED")
    origin = _resolve_origin(value)
    if origin is None:
        issues.append("SUCCESSOR_AUTHORITY_ORIGIN_CAPABILITY_MISSING")
    else:
        try:
            if origin.rebuild() != value or origin.rebuild() != expected:
                issues.append("SUCCESSOR_AUTHORITY_ORIGIN_MISMATCH")
        except (
            AttributeError,
            GroundedRelationConstructionAuthoritySuccessorError,
            TypeError,
            ValueError,
        ):
            issues.append("SUCCESSOR_AUTHORITY_ORIGIN_MISMATCH")
    return tuple(sorted(set(issues)))


def grounded_relation_construction_authority_successor_material(
    value: GroundedRelationConstructionAuthoritySuccessor,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> dict[str, Any]:
    """Validate then expose the closed body-free authority projection."""

    issues = validate_grounded_relation_construction_authority_successor(
        value,
        plan=plan,
        resolver=resolver,
    )
    if issues:
        primary = next(
            (
                code
                for code in issues
                if code
                not in {
                    "SUCCESSOR_AUTHORITY_HASH_MISMATCH",
                    "SUCCESSOR_AUTHORITY_ORIGIN_CAPABILITY_MISSING",
                    "SUCCESSOR_AUTHORITY_ORIGIN_MISMATCH",
                }
            ),
            issues[0],
        )
        raise GroundedRelationConstructionAuthoritySuccessorError(primary)
    payload = _authority_payload(
        schema_version=value.schema_version,
        adapter_version=value.adapter_version,
        marker_policy_version=value.marker_policy_version,
        marker_policy_sha256=value.marker_policy_sha256,
        git_baseline_commit=value.git_baseline_commit,
        git_baseline_tree=value.git_baseline_tree,
        plan_commitment_sha256=value.plan_commitment_sha256,
        semantic_restatement_witness_sha256=(
            value.semantic_restatement_witness_sha256
        ),
        construction_instances=value.construction_instances,
        construction_slots=value.construction_slots,
        source_owner_participations=value.source_owner_participations,
        interval_edges=value.interval_edges,
        relation_authorities=value.relation_authorities,
        semantic_link_bindings=value.semantic_link_bindings,
        explicit_unknown_authorities=value.explicit_unknown_authorities,
        resource_counts=value.resource_counts,
        resource_bounds=value.resource_bounds,
        experimental_only=value.experimental_only,
        body_free=value.body_free,
        runtime_connected=value.runtime_connected,
    )
    return {**payload, "authority_sha256": value.authority_sha256}
