# -*- coding: utf-8 -*-
from __future__ import annotations

"""Forward-only rc0025 natural surface successor.

The module consumes only the current input projection and independently
revalidated Step 4--6 semantic artifacts.  It does not import the frozen Step
7--9 renderer, parser, gate, selector, runtime, corpus, or test owners.
"""

from dataclasses import dataclass
import hashlib
import re
import unicodedata
from typing import Any, Mapping, Sequence

from emlis_ai_content_selection_v3 import validate_content_selection_policy
from emlis_ai_nls_v3_artifact_contract import (
    STANCE_KIND,
    artifact_sha256,
    validate_discourse_plan,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)
from emlis_ai_step11_surface_catalog_v3 import (
    STEP11_SURFACE_CATALOG,
    STEP11_SURFACE_CATALOG_SHA256,
    validate_step11_surface_catalog,
)
from emlis_ai_step11_semantic_overlay_v3 import (
    Step11SemanticOverlay,
    build_step11_semantic_overlay,
    step11_semantic_overlay_material,
)


STEP11_CANDIDATE_VERSION_ID = "nls_v3_rc_0025"
STEP11_SURFACE_AST_SCHEMA = "cocolon.emlis.nls_v3.step11_natural_surface_ast.v6"
STEP11_RENDERED_SURFACE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_canonical_rendered_surface.v6"
)
STEP11_CANDIDATE_SCHEMA = "cocolon.emlis.nls_v3.step11_natural_candidate.v6"
STEP11_SURFACE_REALIZATION_PLAN_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_surface_realization_plan.rc0025.v1"
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_AST_ID_RE = re.compile(r"^nls3s11ast_[0-9a-f]{16}$")
_CANDIDATE_ID_RE = re.compile(r"^nls3s11cand_[0-9a-f]{20}$")
_SLOT_ORDER = {"thought": 0, "action": 1, "emotion": 2, "category": 3}
_SOURCE_FIELD_TO_SLOT = {
    "memo": "thought",
    "memo_action": "action",
    "emotion_details": "emotion",
    "emotions": "emotion",
    "category": "category",
}
_SLOT_TO_SOURCE_FIELD = {
    "thought": "memo",
    "action": "memo_action",
    "emotion": "emotions",
    "category": "category",
}
_SOURCE_FIELDS_BY_SLOT = {
    "thought": frozenset({"memo"}),
    "action": frozenset({"memo_action"}),
    "emotion": frozenset({"emotion_details", "emotions"}),
    "category": frozenset({"category"}),
}
_CLAUSE_FOR_KIND = {
    "grounded_nucleus_notice": "nucleus_notice",
    "grounded_relation_preservation": "relation_notice",
    "unknown_boundary_preservation": "unknown_boundary",
    "significance_or_shift": "shift_notice",
    "intention_or_next_action": "next_action",
    "self_denial_boundary": "self_denial_boundary",
    "bounded_counterposition": "bounded_counterposition",
    STANCE_KIND: "bound_reception",
}
_CLAUSE_FORMS = frozenset(_CLAUSE_FOR_KIND.values())
_RELATION_ENDPOINT_ROLES = frozenset({"action", "affect", "proposition"})
_UNKNOWN_DECISION_STATES = frozenset(
    {"not_applicable", "open", "completed"}
)


class Step11NaturalSurfaceError(ValueError):
    """Fail-closed error carrying only a body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11CurrentInputProjection:
    thought_text: str
    action_text: str
    emotions: tuple[str, ...]
    categories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Step11SourceFragment:
    source_slot: str
    source_field: str
    source_ordinal: int | None
    fragment_role: str
    text: str
    source_start: int
    source_end: int
    source_anchor_id: str
    source_nucleus_ids: tuple[str, ...]
    source_role: str
    modality: str
    temporal_scope: str
    realization_status: str
    label_strength: str | None
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11NucleusSurfaceReference:
    reference_ordinal: int
    endpoint_role: str
    source_identity_key: str
    source_slot: str
    source_field: str
    source_ordinal: int | None
    source_start: int
    source_end: int
    source_anchor_ids: tuple[str, ...]
    nucleus_ids: tuple[str, ...]
    introduction_sentence_group_id: str


@dataclass(frozen=True, slots=True)
class Step11IntegratedRelation:
    source_relation_id: str
    source_relation_ids: tuple[str, ...]
    relation_type: str
    relation_direction: str
    from_nucleus_id: str
    to_nucleus_id: str
    from_source_slots: tuple[str, ...]
    to_source_slots: tuple[str, ...]
    from_source_anchor_ids: tuple[str, ...]
    to_source_anchor_ids: tuple[str, ...]
    from_endpoint_role: str
    to_endpoint_role: str
    from_reference_ordinal: int
    to_reference_ordinal: int
    required: bool
    owner_obligation_ids: tuple[str, ...]
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11IntegratedUnknown:
    source_unknown_id: str
    dimension_code: str
    source_slots: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    target_nucleus_ids: tuple[str, ...]
    source_unknown_ids: tuple[str, ...]
    owner_obligation_ids: tuple[str, ...]
    source_rules: tuple[str, ...]
    epistemic_basis: str
    decision_state: str
    context_nucleus_ids: tuple[str, ...]
    context_anchor_ids: tuple[str, ...]
    surface_policy: str


@dataclass(frozen=True, slots=True)
class Step11IntegratedMixedEmotionRequirement:
    requirement_id: str
    positive_label_anchor_ids: tuple[str, ...]
    negative_label_anchor_ids: tuple[str, ...]
    relation_type: str
    relation_direction: str
    required: bool
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11IntegratedReceptionAntecedentBinding:
    binding_id: str
    reception_obligation_id: str
    reception_node_id: str
    source_target_obligation_ids: tuple[str, ...]
    source_target_node_ids: tuple[str, ...]
    source_target_nucleus_ids: tuple[str, ...]
    antecedent_obligation_ids: tuple[str, ...]
    antecedent_node_ids: tuple[str, ...]
    antecedent_nucleus_ids: tuple[str, ...]
    supporting_obligation_ids: tuple[str, ...]
    supporting_node_ids: tuple[str, ...]
    supporting_nucleus_ids: tuple[str, ...]
    support_role: str
    source_reception_opportunity_ids: tuple[str, ...]
    action_lifecycle: str
    allowed_response_acts: tuple[str, ...]
    evidence_grade: str


@dataclass(frozen=True, slots=True)
class Step11SurfaceClause:
    discourse_node_id: str
    obligation_id: str
    section_role: str
    clause_form: str
    source_slots: tuple[str, ...]
    source_nucleus_ids: tuple[str, ...]
    source_relation_ids: tuple[str, ...]
    polarity: str
    modality: str
    temporal_scope: str
    referent_scope: str
    relation_types: tuple[str, ...]
    relation_directions: tuple[str, ...]
    unknown_dimension_codes: tuple[str, ...]
    reception_act: str | None
    target_obligation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Step11SurfaceSentence:
    discourse_sentence_group_id: str
    section_role: str
    clauses: tuple[Step11SurfaceClause, ...]


@dataclass(frozen=True, slots=True)
class Step11NaturalSurfaceAst:
    schema_version: str
    candidate_version_id: str
    surface_ast_id: str
    source_obligation_ledger_sha256: str
    source_content_plan_sha256: str
    source_discourse_plan_sha256: str
    source_semantic_overlay_sha256: str
    current_input_projection_sha256: str
    surface_catalog_sha256: str
    surface_realization_plan: Step11SurfaceRealizationPlan | None
    source_fragments: tuple[Step11SourceFragment, ...]
    nucleus_surface_references: tuple[
        Step11NucleusSurfaceReference, ...
    ]
    sentences: tuple[Step11SurfaceSentence, ...]
    integrated_relations: tuple[Step11IntegratedRelation, ...]
    integrated_unknowns: tuple[Step11IntegratedUnknown, ...]
    mixed_emotion_requirements: tuple[
        Step11IntegratedMixedEmotionRequirement, ...
    ]
    reception_antecedent_bindings: tuple[
        Step11IntegratedReceptionAntecedentBinding, ...
    ]
    identity_claim_must_not_be_accepted_as_fact: bool
    self_denial_source_slots: tuple[str, ...]
    self_denial_source_anchor_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class Step11CanonicalRenderedSurface:
    schema_version: str
    source_surface_ast_sha256: str
    surface_catalog_sha256: str
    utf8_bytes: bytes
    sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11NaturalSurfaceCandidate:
    schema_version: str
    candidate_version_id: str
    candidate_id: str
    discourse_plan: dict[str, Any]
    current_input_projection: Step11CurrentInputProjection
    surface_ast: Step11NaturalSurfaceAst
    rendered_surface: Step11CanonicalRenderedSurface

    @property
    def final_utf8_bytes(self) -> bytes:
        return self.rendered_surface.utf8_bytes


@dataclass(frozen=True, slots=True)
class _Step11OwnedObservationLine:
    text: str
    owned_anchor_ids: tuple[str, ...]
    owned_nucleus_ids: tuple[str, ...]
    owned_relation_ids: tuple[str, ...]
    owned_obligation_ids: tuple[str, ...]
    owned_mixed_emotion_requirement_ids: tuple[str, ...]
    literal_anchor_ids: tuple[str, ...]
    required_relation_ids: tuple[str, ...]
    used_reference_ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class _Step11OwnedReceptionLine:
    text: str
    binding_ids: tuple[str, ...]
    reception_obligation_ids: tuple[str, ...]
    antecedent_obligation_ids: tuple[str, ...]
    supporting_obligation_ids: tuple[str, ...]
    visible_reference_ordinals: tuple[int, ...]
    antecedent_observation_line_indices: tuple[int, ...]
    literal_anchor_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _Step11OwnedSentenceLine:
    discourse_sentence_group_id: str
    section_role: str
    text: str
    clause_count: int


@dataclass(frozen=True, slots=True)
class Step11SurfaceRealizationUnit:
    """One source-owned unit scheduled between planning and rendering.

    The unit contains body-free ownership and dependency metadata only.  It
    deliberately excludes rendered text, corpus identity, and fixture oracle
    material, so balancing cannot become a case-specific response path.
    """

    semantic_unit_id: str
    section_role: str
    phase: str
    owner_obligation_ids: tuple[str, ...]
    owner_anchor_ids: tuple[str, ...]
    owner_nucleus_ids: tuple[str, ...]
    owner_relation_ids: tuple[str, ...]
    owner_mixed_emotion_requirement_ids: tuple[str, ...]
    introduced_reference_ordinals: tuple[int, ...]
    used_reference_ordinals: tuple[int, ...]
    required_reference_ordinals: tuple[int, ...]
    visible_reference_count: int
    body_free_complexity_weight: int
    parent_sentence_group_ids: tuple[str, ...]
    assigned_sentence_group_id: str
    assigned_grammatical_chunk_ordinal: int
    source_order: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11SurfaceRealizationPlan:
    schema_version: str
    candidate_version_id: str
    realization_plan_id: str
    units: tuple[Step11SurfaceRealizationUnit, ...]
    observation_sentence_group_ids: tuple[str, ...]
    reception_sentence_group_ids: tuple[str, ...]
    maximum_observation_clauses_per_sentence: int
    maximum_visible_clauses_per_grammatical_sentence: int
    maximum_grammatical_complexity_load: int
    maximum_repeated_joiner_per_group: int
    peak_observation_clause_count: int
    peak_grammatical_clause_count: int
    peak_grammatical_complexity_load: int
    peak_group_repeated_joiner_count: int
    body_free: bool = True


_SURFACE_PHASE_ORDER = {
    "source_introduction": 0,
    "relation": 1,
    "unknown_boundary": 2,
    "self_denial_boundary": 3,
    "bounded_counterposition": 4,
    "reception": 0,
}


def _surface_realization_unit_material(
    value: Step11SurfaceRealizationUnit,
) -> dict[str, Any]:
    return {
        "semantic_unit_id": value.semantic_unit_id,
        "section_role": value.section_role,
        "phase": value.phase,
        "owner_obligation_ids": list(value.owner_obligation_ids),
        "owner_anchor_ids": list(value.owner_anchor_ids),
        "owner_nucleus_ids": list(value.owner_nucleus_ids),
        "owner_relation_ids": list(value.owner_relation_ids),
        "owner_mixed_emotion_requirement_ids": list(
            value.owner_mixed_emotion_requirement_ids
        ),
        "introduced_reference_ordinals": list(
            value.introduced_reference_ordinals
        ),
        "used_reference_ordinals": list(
            value.used_reference_ordinals
        ),
        "required_reference_ordinals": list(
            value.required_reference_ordinals
        ),
        "visible_reference_count": value.visible_reference_count,
        "body_free_complexity_weight": value.body_free_complexity_weight,
        "parent_sentence_group_ids": list(
            value.parent_sentence_group_ids
        ),
        "assigned_sentence_group_id": value.assigned_sentence_group_id,
        "assigned_grammatical_chunk_ordinal": (
            value.assigned_grammatical_chunk_ordinal
        ),
        "source_order": value.source_order,
    }


def step11_surface_realization_plan_material(
    value: Step11SurfaceRealizationPlan,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "realization_plan_id": value.realization_plan_id,
        "units": [
            _surface_realization_unit_material(row) for row in value.units
        ],
        "observation_sentence_group_ids": list(
            value.observation_sentence_group_ids
        ),
        "reception_sentence_group_ids": list(
            value.reception_sentence_group_ids
        ),
        "maximum_observation_clauses_per_sentence": (
            value.maximum_observation_clauses_per_sentence
        ),
        "maximum_visible_clauses_per_grammatical_sentence": (
            value.maximum_visible_clauses_per_grammatical_sentence
        ),
        "maximum_grammatical_complexity_load": (
            value.maximum_grammatical_complexity_load
        ),
        "maximum_repeated_joiner_per_group": (
            value.maximum_repeated_joiner_per_group
        ),
        "peak_observation_clause_count": (
            value.peak_observation_clause_count
        ),
        "peak_grammatical_clause_count": (
            value.peak_grammatical_clause_count
        ),
        "peak_grammatical_complexity_load": (
            value.peak_grammatical_complexity_load
        ),
        "peak_group_repeated_joiner_count": (
            value.peak_group_repeated_joiner_count
        ),
        "body_free": value.body_free,
    }
    if not include_id:
        result.pop("realization_plan_id")
    return result


def _bounded_group_widths(
    units: Sequence[Step11SurfaceRealizationUnit],
    group_ids: Sequence[str],
    *,
    maximum: int,
) -> tuple[int, ...]:
    """Choose a balanced contiguous partition with structural constraints."""

    total = len(units)
    group_count = len(group_ids)
    if not group_count:
        if total:
            raise Step11NaturalSurfaceError(
                "STEP11_SURFACE_PLAN_GROUP_COVERAGE_INVALID"
            )
        return ()
    if total < group_count or total > group_count * maximum:
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_DENSITY_UNSATISFIABLE"
        )

    candidates: list[tuple[int, ...]] = []

    def visit(remaining: int, slots: int, prefix: tuple[int, ...]) -> None:
        if slots == 0:
            if remaining == 0:
                candidates.append(prefix)
            return
        minimum_remaining = slots - 1
        maximum_width = min(maximum, remaining - minimum_remaining)
        for width in range(1, maximum_width + 1):
            visit(remaining - width, slots - 1, (*prefix, width))

    visit(total, group_count, ())
    group_index = {group_id: index for index, group_id in enumerate(group_ids)}

    def assignments(widths: Sequence[int]) -> tuple[int, ...]:
        return tuple(
            group
            for group, width in enumerate(widths)
            for _ in range(width)
        )

    def allowed(widths: Sequence[int]) -> bool:
        assigned = assignments(widths)
        self_groups = {
            assigned[index]
            for index, row in enumerate(units)
            if row.phase == "self_denial_boundary"
        }
        counter_groups = {
            assigned[index]
            for index, row in enumerate(units)
            if row.phase == "bounded_counterposition"
        }
        return not (self_groups & counter_groups)

    candidates = [row for row in candidates if allowed(row)]
    if not candidates:
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_DENSITY_UNSATISFIABLE"
        )

    def displacement(widths: Sequence[int]) -> int:
        return sum(
            min(
                (
                    abs(assigned_index - group_index[parent_id])
                    for parent_id in unit.parent_sentence_group_ids
                    if parent_id in group_index
                ),
                default=0,
            )
            for unit, assigned_index in zip(units, assignments(widths))
        )

    return min(
        candidates,
        key=lambda widths: (
            max(widths),
            max(widths) - min(widths),
            displacement(widths),
            tuple(-width for width in widths),
        ),
    )


def _grammatical_chunk_assignments(
    units: Sequence[Step11SurfaceRealizationUnit],
    *,
    maximum_clauses: int,
    maximum_load: int,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """Partition one discourse group into bounded grammatical chunks."""

    if not units:
        return (), (), ()
    ordinals: list[int] = []
    clause_counts: list[int] = []
    complexity_loads: list[int] = []
    for row in units:
        weight = row.body_free_complexity_weight
        if weight > maximum_load:
            raise Step11NaturalSurfaceError(
                "STEP11_SURFACE_PLAN_GRAMMATICAL_LOAD_UNSATISFIABLE"
            )
        if (
            not clause_counts
            or clause_counts[-1] >= maximum_clauses
            or complexity_loads[-1] + weight > maximum_load
        ):
            clause_counts.append(0)
            complexity_loads.append(0)
        clause_counts[-1] += 1
        complexity_loads[-1] += weight
        ordinals.append(len(clause_counts))
    return tuple(ordinals), tuple(clause_counts), tuple(complexity_loads)


def build_step11_surface_realization_plan(
    units: Sequence[Step11SurfaceRealizationUnit],
    *,
    observation_group_ids: Sequence[str],
    reception_group_ids: Sequence[str],
) -> Step11SurfaceRealizationPlan:
    """Freeze and balance body-free surface units before final rendering."""

    if type(units) not in {list, tuple} or any(
        type(row) is not Step11SurfaceRealizationUnit for row in units
    ):
        raise Step11NaturalSurfaceError("STEP11_SURFACE_PLAN_UNIT_INVALID")
    observation_groups = tuple(observation_group_ids)
    reception_groups = tuple(reception_group_ids)
    all_groups = (*observation_groups, *reception_groups)
    if (
        not all(type(row) is str and row for row in all_groups)
        or len(all_groups) != len(set(all_groups))
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_GROUP_ID_INVALID"
        )
    ordered = tuple(sorted(units, key=lambda row: row.source_order))
    if tuple(row.source_order for row in ordered) != tuple(
        range(len(ordered))
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_SOURCE_ORDER_INVALID"
        )
    if any(
        row.section_role not in {"observation", "reception"}
        or row.phase not in _SURFACE_PHASE_ORDER
        or (
            row.section_role == "reception" and row.phase != "reception"
        )
        or (
            row.section_role == "observation" and row.phase == "reception"
        )
        or not row.semantic_unit_id
        or row.assigned_sentence_group_id
        or row.assigned_grammatical_chunk_ordinal != 0
        or type(row.visible_reference_count) is not int
        or row.visible_reference_count < 0
        or type(row.body_free_complexity_weight) is not int
        or row.body_free_complexity_weight < 1
        or not row.parent_sentence_group_ids
        or not set(row.parent_sentence_group_ids) <= set(all_groups)
        for row in ordered
    ):
        raise Step11NaturalSurfaceError("STEP11_SURFACE_PLAN_UNIT_INVALID")
    if len({row.semantic_unit_id for row in ordered}) != len(ordered):
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_UNIT_ID_DUPLICATE"
        )

    introduced: set[int] = set()
    for section in ("observation", "reception"):
        section_rows = tuple(
            row for row in ordered if row.section_role == section
        )
        for row in section_rows:
            introduced_values = row.introduced_reference_ordinals
            used_values = row.used_reference_ordinals
            required_values = row.required_reference_ordinals
            row_introduced = set(introduced_values)
            row_used = set(used_values)
            row_required = set(required_values)
            if (
                any(type(value) is not int or value < 1 for value in row_introduced)
                or any(type(value) is not int or value < 1 for value in row_used)
                or any(type(value) is not int or value < 1 for value in row_required)
                or len(row_introduced) != len(introduced_values)
                or len(row_used) != len(used_values)
                or len(row_required) != len(required_values)
                or introduced & row_introduced
                or not row_introduced <= row_used
                or row_required != row_used - row_introduced
                or not row_required <= introduced
                or row.visible_reference_count != len(row_used)
                or row.body_free_complexity_weight
                != max(1, row.visible_reference_count)
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_SURFACE_PLAN_REFERENCE_ORDER_INVALID"
                )
            introduced.update(row_introduced)
        phases = tuple(_SURFACE_PHASE_ORDER[row.phase] for row in section_rows)
        if phases != tuple(sorted(phases)):
            raise Step11NaturalSurfaceError(
                "STEP11_SURFACE_PLAN_PHASE_ORDER_INVALID"
            )

    maximum = int(
        STEP11_SURFACE_CATALOG["group_grammar"]
        ["maximum_observation_clauses_per_sentence"]
    )
    maximum_grammatical_clauses = int(
        STEP11_SURFACE_CATALOG["group_grammar"]
        ["maximum_visible_clauses_per_grammatical_sentence"]
    )
    maximum_grammatical_load = int(
        STEP11_SURFACE_CATALOG["group_grammar"]
        ["maximum_grammatical_complexity_load"]
    )
    maximum_group_joiners = int(
        STEP11_SURFACE_CATALOG["group_grammar"]
        ["maximum_repeated_joiner_per_group"]
    )
    observation = tuple(
        row for row in ordered if row.section_role == "observation"
    )
    reception = tuple(
        row for row in ordered if row.section_role == "reception"
    )
    observation_widths = _bounded_group_widths(
        observation, observation_groups, maximum=maximum
    )
    reception_widths = _bounded_group_widths(
        reception, reception_groups, maximum=maximum
    )

    assigned_units: list[Step11SurfaceRealizationUnit] = []
    grammatical_clause_counts: list[int] = []
    grammatical_loads: list[int] = []
    group_joiner_counts: list[int] = []
    for section_rows, group_ids, widths in (
        (observation, observation_groups, observation_widths),
        (reception, reception_groups, reception_widths),
    ):
        cursor = 0
        for group_id, width in zip(group_ids, widths):
            group_rows = section_rows[cursor : cursor + width]
            (
                chunk_ordinals,
                chunk_clause_counts,
                chunk_loads,
            ) = _grammatical_chunk_assignments(
                group_rows,
                maximum_clauses=maximum_grammatical_clauses,
                maximum_load=maximum_grammatical_load,
            )
            joiner_count = sum(
                max(0, count - 1) for count in chunk_clause_counts
            )
            if joiner_count > maximum_group_joiners:
                raise Step11NaturalSurfaceError(
                    "STEP11_SURFACE_PLAN_GROUP_JOINER_BUDGET_EXCEEDED"
                )
            grammatical_clause_counts.extend(chunk_clause_counts)
            grammatical_loads.extend(chunk_loads)
            group_joiner_counts.append(joiner_count)
            for row, chunk_ordinal in zip(group_rows, chunk_ordinals):
                assigned_units.append(
                    Step11SurfaceRealizationUnit(
                        semantic_unit_id=row.semantic_unit_id,
                        section_role=row.section_role,
                        phase=row.phase,
                        owner_obligation_ids=row.owner_obligation_ids,
                        owner_anchor_ids=row.owner_anchor_ids,
                        owner_nucleus_ids=row.owner_nucleus_ids,
                        owner_relation_ids=row.owner_relation_ids,
                        owner_mixed_emotion_requirement_ids=(
                            row.owner_mixed_emotion_requirement_ids
                        ),
                        introduced_reference_ordinals=(
                            row.introduced_reference_ordinals
                        ),
                        used_reference_ordinals=(
                            row.used_reference_ordinals
                        ),
                        required_reference_ordinals=(
                            row.required_reference_ordinals
                        ),
                        visible_reference_count=(
                            row.visible_reference_count
                        ),
                        body_free_complexity_weight=(
                            row.body_free_complexity_weight
                        ),
                        parent_sentence_group_ids=(
                            row.parent_sentence_group_ids
                        ),
                        assigned_sentence_group_id=group_id,
                        assigned_grammatical_chunk_ordinal=(
                            chunk_ordinal
                        ),
                        source_order=row.source_order,
                    )
                )
            cursor += width
    assigned_units.sort(key=lambda row: row.source_order)
    provisional = Step11SurfaceRealizationPlan(
        schema_version=STEP11_SURFACE_REALIZATION_PLAN_SCHEMA,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        realization_plan_id="nls3s11real_0000000000000000",
        units=tuple(assigned_units),
        observation_sentence_group_ids=observation_groups,
        reception_sentence_group_ids=reception_groups,
        maximum_observation_clauses_per_sentence=maximum,
        maximum_visible_clauses_per_grammatical_sentence=(
            maximum_grammatical_clauses
        ),
        maximum_grammatical_complexity_load=maximum_grammatical_load,
        maximum_repeated_joiner_per_group=maximum_group_joiners,
        peak_observation_clause_count=(
            max(observation_widths) if observation_widths else 0
        ),
        peak_grammatical_clause_count=(
            max(grammatical_clause_counts)
            if grammatical_clause_counts
            else 0
        ),
        peak_grammatical_complexity_load=(
            max(grammatical_loads) if grammatical_loads else 0
        ),
        peak_group_repeated_joiner_count=(
            max(group_joiner_counts) if group_joiner_counts else 0
        ),
        body_free=True,
    )
    realization_plan_id = "nls3s11real_" + artifact_sha256(
        step11_surface_realization_plan_material(
            provisional, include_id=False
        )
    )[:16]
    return Step11SurfaceRealizationPlan(
        schema_version=provisional.schema_version,
        candidate_version_id=provisional.candidate_version_id,
        realization_plan_id=realization_plan_id,
        units=provisional.units,
        observation_sentence_group_ids=(
            provisional.observation_sentence_group_ids
        ),
        reception_sentence_group_ids=provisional.reception_sentence_group_ids,
        maximum_observation_clauses_per_sentence=maximum,
        maximum_visible_clauses_per_grammatical_sentence=(
            provisional.maximum_visible_clauses_per_grammatical_sentence
        ),
        maximum_grammatical_complexity_load=(
            provisional.maximum_grammatical_complexity_load
        ),
        maximum_repeated_joiner_per_group=(
            provisional.maximum_repeated_joiner_per_group
        ),
        peak_observation_clause_count=(
            provisional.peak_observation_clause_count
        ),
        peak_grammatical_clause_count=(
            provisional.peak_grammatical_clause_count
        ),
        peak_grammatical_complexity_load=(
            provisional.peak_grammatical_complexity_load
        ),
        peak_group_repeated_joiner_count=(
            provisional.peak_group_repeated_joiner_count
        ),
        body_free=True,
    )


def _normalise_text(value: str) -> str:
    value = unicodedata.normalize(
        "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
    )
    # A source-bound display projection: preserve every non-whitespace scalar,
    # while keeping the public section layout canonical and parseable.
    return " ".join(value.split())


def _label_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise Step11NaturalSurfaceError(f"STEP11_{field.upper()}_ARRAY_REQUIRED")
    labels: list[str] = []
    for item in value:
        if type(item) is str:
            label = item
        elif type(item) is dict and type(item.get("type")) is str:
            label = item["type"]
        else:
            raise Step11NaturalSurfaceError(
                f"STEP11_{field.upper()}_ENTRY_INVALID"
            )
        normalised = _normalise_text(label)
        if not normalised:
            raise Step11NaturalSurfaceError(
                f"STEP11_{field.upper()}_ENTRY_EMPTY"
            )
        labels.append(normalised)
    if len(labels) != len(set(labels)):
        raise Step11NaturalSurfaceError(
            f"STEP11_{field.upper()}_DUPLICATE"
        )
    return tuple(labels)


def project_step11_current_input(
    current_input: Mapping[str, Any],
) -> Step11CurrentInputProjection:
    """Project exactly the four current-input fields used by the app path."""

    if type(current_input) is not dict:
        raise Step11NaturalSurfaceError("STEP11_CURRENT_INPUT_MAPPING_REQUIRED")
    thought = current_input.get("thought_text")
    action = current_input.get("action_text")
    if type(thought) is not str or type(action) is not str:
        raise Step11NaturalSurfaceError("STEP11_CURRENT_TEXT_FIELDS_INVALID")
    thought = _normalise_text(thought)
    action = _normalise_text(action)
    if not thought and not action:
        raise Step11NaturalSurfaceError("STEP11_CURRENT_TEXT_REQUIRED")
    return Step11CurrentInputProjection(
        thought_text=thought,
        action_text=action,
        emotions=_label_tuple(current_input.get("emotions"), field="emotions"),
        categories=_label_tuple(
            current_input.get("categories"), field="categories"
        ),
    )


def _meaningful_char_count(value: str) -> int:
    return sum(
        1
        for char in value
        if not char.isspace() and char not in "。！？!?、，,.;；:："
    )


def _source_fragments(
    semantic_overlay: Step11SemanticOverlay,
) -> tuple[Step11SourceFragment, ...]:
    """Copy exact text and label anchors without slot-level substitution."""

    nuclei_by_anchor: dict[str, list[str]] = {}
    bindings_by_anchor: dict[str, list[Any]] = {}
    for binding in semantic_overlay.nucleus_anchor_bindings:
        for anchor_id in binding.source_anchor_ids:
            nuclei_by_anchor.setdefault(anchor_id, []).append(
                binding.nucleus_id
            )
            bindings_by_anchor.setdefault(anchor_id, []).append(binding)
    required_anchor_ids = {
        anchor_id
        for binding in semantic_overlay.nucleus_anchor_bindings
        for anchor_id in (
            *binding.source_anchor_ids,
            *binding.source_label_anchor_ids,
        )
    }
    required_anchor_ids.update(
        anchor_id
        for row in semantic_overlay.unknowns
        for anchor_id in (
            *row.source_anchor_ids,
            *row.context_anchor_ids,
        )
    )
    required_anchor_ids.update(
        row.source_anchor_id
        for row in semantic_overlay.reported_self_evaluations
    )
    required_anchor_ids.update(
        anchor_id
        for row in semantic_overlay.relations
        for anchor_id in (
            *row.from_source_anchor_ids,
            *row.from_label_anchor_ids,
            *row.to_source_anchor_ids,
            *row.to_label_anchor_ids,
        )
    )
    whole_max = int(
        STEP11_SURFACE_CATALOG["fragment_policy"]["whole_text_max_chars"]
    )
    result: list[Step11SourceFragment] = []
    for anchor in semantic_overlay.anchors:
        if anchor.anchor_id not in required_anchor_ids:
            continue
        if len(anchor.text) > whole_max:
            raise Step11NaturalSurfaceError(
                "STEP11_SOURCE_ANCHOR_WHOLE_BOUND_EXCEEDED"
            )
        bound = bindings_by_anchor.get(anchor.anchor_id, [])
        modalities = {row.modality for row in bound}
        temporal_scopes = {row.temporal_scope for row in bound}
        statuses = {row.realization_status for row in bound}
        source_roles = {row.source_role for row in bound}
        result.append(
            Step11SourceFragment(
                source_slot=anchor.source_slot,
                source_field=_SLOT_TO_SOURCE_FIELD[anchor.source_slot],
                source_ordinal=None,
                fragment_role=anchor.role,
                text=anchor.text,
                source_start=anchor.start,
                source_end=anchor.end,
                source_anchor_id=anchor.anchor_id,
                source_nucleus_ids=tuple(
                    sorted(nuclei_by_anchor.get(anchor.anchor_id, ()))
                ),
                source_role=(
                    next(iter(source_roles))
                    if len(source_roles) == 1
                    else anchor.source_slot
                ),
                modality=(next(iter(modalities)) if len(modalities) == 1 else "mixed"),
                temporal_scope=(
                    next(iter(temporal_scopes))
                    if len(temporal_scopes) == 1
                    else "mixed"
                ),
                realization_status=(
                    next(iter(statuses))
                    if len(statuses) == 1
                    else "undetermined"
                ),
                label_strength=None,
                evidence_grade="exact_source_span",
            )
        )
    for label_anchor in semantic_overlay.label_anchors:
        if label_anchor.label_anchor_id not in required_anchor_ids:
            continue
        result.append(
            Step11SourceFragment(
                source_slot=label_anchor.source_slot,
                source_field=label_anchor.source_field,
                source_ordinal=label_anchor.source_ordinal,
                fragment_role="label",
                text=label_anchor.label,
                source_start=label_anchor.source_ordinal,
                source_end=label_anchor.source_ordinal + 1,
                source_anchor_id=label_anchor.label_anchor_id,
                source_nucleus_ids=tuple(
                    sorted(
                        binding.nucleus_id
                        for binding in semantic_overlay.nucleus_anchor_bindings
                        if label_anchor.label_anchor_id
                        in binding.source_label_anchor_ids
                    )
                ),
                source_role=label_anchor.source_slot,
                modality="reported_content",
                temporal_scope="current",
                realization_status="reported_content",
                label_strength=label_anchor.strength,
                evidence_grade=label_anchor.evidence_grade,
            )
        )
    if len({row.source_anchor_id for row in result}) != len(result):
        raise Step11NaturalSurfaceError(
            "STEP11_SOURCE_FRAGMENT_ANCHOR_DUPLICATE"
        )
    return tuple(result)


def _nucleus_surface_references(
    source_fragments: Sequence[Step11SourceFragment],
    sentences: Sequence[Step11SurfaceSentence],
    *,
    semantic_overlay: Step11SemanticOverlay,
) -> tuple[Step11NucleusSurfaceReference, ...]:
    """Build the deterministic exact-source handle registry.

    The registry is derived before rendering and is therefore independent of
    line order.  Equal source identities coalesce; overlapping, non-identical
    text ranges fail closed because quoting both would violate the one-owner
    budget.  Endpoint roles come from the typed source relation when present
    and otherwise from the app slot.
    """

    active_nucleus_ids = {
        nucleus_id
        for sentence in sentences
        if sentence.section_role == "observation"
        for clause in sentence.clauses
        for nucleus_id in clause.source_nucleus_ids
    }
    active_nucleus_ids.update(
        semantic_overlay.planning_frontier.active_nucleus_ids
    )
    relation_role_by_anchor: dict[str, str] = {}
    for relation in semantic_overlay.relations:
        for anchor_id in (
            *relation.from_source_anchor_ids,
            *relation.from_label_anchor_ids,
        ):
            previous = relation_role_by_anchor.setdefault(
                anchor_id, relation.from_endpoint_role
            )
            if previous != relation.from_endpoint_role:
                raise Step11NaturalSurfaceError(
                    "STEP11_ENDPOINT_REFERENCE_ROLE_AMBIGUOUS"
                )
        for anchor_id in (
            *relation.to_source_anchor_ids,
            *relation.to_label_anchor_ids,
        ):
            previous = relation_role_by_anchor.setdefault(
                anchor_id, relation.to_endpoint_role
            )
            if previous != relation.to_endpoint_role:
                raise Step11NaturalSurfaceError(
                    "STEP11_ENDPOINT_REFERENCE_ROLE_AMBIGUOUS"
                )

    grouped: dict[tuple[Any, ...], list[Step11SourceFragment]] = {}
    for fragment in source_fragments:
        if (
            fragment.fragment_role not in {"nucleus", "label"}
            or not set(fragment.source_nucleus_ids) & active_nucleus_ids
        ):
            continue
        if fragment.fragment_role == "label":
            identity = (
                "label",
                fragment.source_slot,
                fragment.source_field,
                fragment.source_ordinal,
            )
        else:
            identity = (
                "text",
                fragment.source_slot,
                fragment.source_start,
                fragment.source_end,
            )
        grouped.setdefault(identity, []).append(fragment)

    text_ranges = sorted(
        (
            identity[1],
            int(identity[2]),
            int(identity[3]),
            identity,
        )
        for identity in grouped
        if identity[0] == "text"
    )
    for index, (slot, start, end, _identity) in enumerate(text_ranges):
        for other_slot, other_start, other_end, _other in text_ranges[
            index + 1 :
        ]:
            if other_slot != slot:
                break
            if other_start >= end:
                break
            if start < other_end and other_start < end:
                raise Step11NaturalSurfaceError(
                    "STEP11_NUCLEUS_REFERENCE_RANGE_OVERLAP_UNREPRESENTABLE"
                )

    sentence_group_by_nucleus: dict[str, str] = {}
    for sentence in sentences:
        if sentence.section_role != "observation":
            continue
        for clause in sentence.clauses:
            for nucleus_id in clause.source_nucleus_ids:
                sentence_group_by_nucleus.setdefault(
                    nucleus_id, sentence.discourse_sentence_group_id
                )
    for integration in semantic_overlay.planning_frontier.integrations:
        for nucleus_id in integration.nucleus_ids:
            sentence_group_by_nucleus.setdefault(
                nucleus_id, integration.target_sentence_group_id
            )

    ordered_identities = sorted(
        grouped,
        key=lambda identity: (
            _SLOT_ORDER[identity[1]],
            0 if identity[0] == "text" else 1,
            identity[2],
            identity[3],
        ),
    )
    result: list[Step11NucleusSurfaceReference] = []
    for ordinal, identity in enumerate(ordered_identities, start=1):
        fragments = grouped[identity]
        anchor_ids = tuple(
            sorted({row.source_anchor_id for row in fragments})
        )
        nucleus_ids = tuple(
            sorted(
                {
                    nucleus_id
                    for row in fragments
                    for nucleus_id in row.source_nucleus_ids
                    if nucleus_id in active_nucleus_ids
                }
            )
        )
        roles = {
            relation_role_by_anchor.get(
                anchor_id,
                "action"
                if fragments[0].source_slot == "action"
                else "affect"
                if fragments[0].source_slot == "emotion"
                else "proposition",
            )
            for anchor_id in anchor_ids
        }
        group_ids = {
            sentence_group_by_nucleus[nucleus_id]
            for nucleus_id in nucleus_ids
            if nucleus_id in sentence_group_by_nucleus
        }
        if len(roles) != 1 or not nucleus_ids or not group_ids:
            raise Step11NaturalSurfaceError(
                "STEP11_ENDPOINT_REFERENCE_CONTRACT_UNRESOLVED"
            )
        fragment = fragments[0]
        result.append(
            Step11NucleusSurfaceReference(
                reference_ordinal=ordinal,
                endpoint_role=next(iter(roles)),
                source_identity_key=artifact_sha256(
                    {"identity": list(identity)}
                ),
                source_slot=fragment.source_slot,
                source_field=fragment.source_field,
                source_ordinal=fragment.source_ordinal,
                source_start=fragment.source_start,
                source_end=fragment.source_end,
                source_anchor_ids=anchor_ids,
                nucleus_ids=nucleus_ids,
                introduction_sentence_group_id=next(
                    sentence.discourse_sentence_group_id
                    for sentence in sentences
                    if sentence.discourse_sentence_group_id in group_ids
                ),
            )
        )
    if not result:
        raise Step11NaturalSurfaceError(
            "STEP11_ENDPOINT_REFERENCE_REGISTRY_EMPTY"
        )
    return tuple(result)


def _projection_material(value: Step11CurrentInputProjection) -> dict[str, Any]:
    if type(value) is not Step11CurrentInputProjection:
        raise Step11NaturalSurfaceError("STEP11_INPUT_PROJECTION_INVALID")
    return {
        "thought_text": value.thought_text,
        "action_text": value.action_text,
        "emotions": list(value.emotions),
        "categories": list(value.categories),
    }


def _fragment_material(value: Step11SourceFragment) -> dict[str, Any]:
    return {
        "source_slot": value.source_slot,
        "source_field": value.source_field,
        "source_ordinal": value.source_ordinal,
        "fragment_role": value.fragment_role,
        "text": value.text,
        "source_start": value.source_start,
        "source_end": value.source_end,
        "source_anchor_id": value.source_anchor_id,
        "source_nucleus_ids": list(value.source_nucleus_ids),
        "source_role": value.source_role,
        "modality": value.modality,
        "temporal_scope": value.temporal_scope,
        "realization_status": value.realization_status,
        "label_strength": value.label_strength,
        "evidence_grade": value.evidence_grade,
    }


def _nucleus_surface_reference_material(
    value: Step11NucleusSurfaceReference,
) -> dict[str, Any]:
    return {
        "reference_ordinal": value.reference_ordinal,
        "endpoint_role": value.endpoint_role,
        "source_identity_key": value.source_identity_key,
        "source_slot": value.source_slot,
        "source_field": value.source_field,
        "source_ordinal": value.source_ordinal,
        "source_start": value.source_start,
        "source_end": value.source_end,
        "source_anchor_ids": list(value.source_anchor_ids),
        "nucleus_ids": list(value.nucleus_ids),
        "introduction_sentence_group_id": (
            value.introduction_sentence_group_id
        ),
    }


def _relation_material(value: Step11IntegratedRelation) -> dict[str, Any]:
    return {
        "source_relation_id": value.source_relation_id,
        "source_relation_ids": list(value.source_relation_ids),
        "relation_type": value.relation_type,
        "relation_direction": value.relation_direction,
        "from_nucleus_id": value.from_nucleus_id,
        "to_nucleus_id": value.to_nucleus_id,
        "from_source_slots": list(value.from_source_slots),
        "to_source_slots": list(value.to_source_slots),
        "from_source_anchor_ids": list(value.from_source_anchor_ids),
        "to_source_anchor_ids": list(value.to_source_anchor_ids),
        "from_endpoint_role": value.from_endpoint_role,
        "to_endpoint_role": value.to_endpoint_role,
        "from_reference_ordinal": value.from_reference_ordinal,
        "to_reference_ordinal": value.to_reference_ordinal,
        "required": value.required,
        "owner_obligation_ids": list(value.owner_obligation_ids),
        "evidence_grade": value.evidence_grade,
    }


def _unknown_material(value: Step11IntegratedUnknown) -> dict[str, Any]:
    return {
        "source_unknown_id": value.source_unknown_id,
        "dimension_code": value.dimension_code,
        "source_slots": list(value.source_slots),
        "source_anchor_ids": list(value.source_anchor_ids),
        "target_nucleus_ids": list(value.target_nucleus_ids),
        "source_unknown_ids": list(value.source_unknown_ids),
        "owner_obligation_ids": list(value.owner_obligation_ids),
        "source_rules": list(value.source_rules),
        "epistemic_basis": value.epistemic_basis,
        "decision_state": value.decision_state,
        "context_nucleus_ids": list(value.context_nucleus_ids),
        "context_anchor_ids": list(value.context_anchor_ids),
        "surface_policy": value.surface_policy,
    }


def _mixed_emotion_material(
    value: Step11IntegratedMixedEmotionRequirement,
) -> dict[str, Any]:
    return {
        "requirement_id": value.requirement_id,
        "positive_label_anchor_ids": list(
            value.positive_label_anchor_ids
        ),
        "negative_label_anchor_ids": list(
            value.negative_label_anchor_ids
        ),
        "relation_type": value.relation_type,
        "relation_direction": value.relation_direction,
        "required": value.required,
        "evidence_grade": value.evidence_grade,
    }


def _reception_antecedent_binding_material(
    value: Step11IntegratedReceptionAntecedentBinding,
) -> dict[str, Any]:
    return {
        "binding_id": value.binding_id,
        "reception_obligation_id": value.reception_obligation_id,
        "reception_node_id": value.reception_node_id,
        "source_target_obligation_ids": list(
            value.source_target_obligation_ids
        ),
        "source_target_node_ids": list(value.source_target_node_ids),
        "source_target_nucleus_ids": list(
            value.source_target_nucleus_ids
        ),
        "antecedent_obligation_ids": list(value.antecedent_obligation_ids),
        "antecedent_node_ids": list(value.antecedent_node_ids),
        "antecedent_nucleus_ids": list(value.antecedent_nucleus_ids),
        "supporting_obligation_ids": list(
            value.supporting_obligation_ids
        ),
        "supporting_node_ids": list(value.supporting_node_ids),
        "supporting_nucleus_ids": list(value.supporting_nucleus_ids),
        "support_role": value.support_role,
        "source_reception_opportunity_ids": list(
            value.source_reception_opportunity_ids
        ),
        "action_lifecycle": value.action_lifecycle,
        "allowed_response_acts": list(value.allowed_response_acts),
        "evidence_grade": value.evidence_grade,
    }


def _clause_material(value: Step11SurfaceClause) -> dict[str, Any]:
    return {
        "discourse_node_id": value.discourse_node_id,
        "obligation_id": value.obligation_id,
        "section_role": value.section_role,
        "clause_form": value.clause_form,
        "source_slots": list(value.source_slots),
        "source_nucleus_ids": list(value.source_nucleus_ids),
        "source_relation_ids": list(value.source_relation_ids),
        "polarity": value.polarity,
        "modality": value.modality,
        "temporal_scope": value.temporal_scope,
        "referent_scope": value.referent_scope,
        "relation_types": list(value.relation_types),
        "relation_directions": list(value.relation_directions),
        "unknown_dimension_codes": list(value.unknown_dimension_codes),
        "reception_act": value.reception_act,
        "target_obligation_ids": list(value.target_obligation_ids),
    }


def _sentence_material(value: Step11SurfaceSentence) -> dict[str, Any]:
    return {
        "discourse_sentence_group_id": value.discourse_sentence_group_id,
        "section_role": value.section_role,
        "clauses": [_clause_material(row) for row in value.clauses],
    }


def step11_surface_ast_material(
    value: Step11NaturalSurfaceAst,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "surface_ast_id": value.surface_ast_id,
        "source_obligation_ledger_sha256": (
            value.source_obligation_ledger_sha256
        ),
        "source_content_plan_sha256": value.source_content_plan_sha256,
        "source_discourse_plan_sha256": value.source_discourse_plan_sha256,
        "source_semantic_overlay_sha256": (
            value.source_semantic_overlay_sha256
        ),
        "current_input_projection_sha256": (
            value.current_input_projection_sha256
        ),
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "surface_realization_plan": (
            step11_surface_realization_plan_material(
                value.surface_realization_plan
            )
            if type(value.surface_realization_plan)
            is Step11SurfaceRealizationPlan
            else None
        ),
        "source_fragments": [
            _fragment_material(row) for row in value.source_fragments
        ],
        "nucleus_surface_references": [
            _nucleus_surface_reference_material(row)
            for row in value.nucleus_surface_references
        ],
        "sentences": [_sentence_material(row) for row in value.sentences],
        "integrated_relations": [
            _relation_material(row) for row in value.integrated_relations
        ],
        "integrated_unknowns": [
            _unknown_material(row) for row in value.integrated_unknowns
        ],
        "mixed_emotion_requirements": [
            _mixed_emotion_material(row)
            for row in value.mixed_emotion_requirements
        ],
        "reception_antecedent_bindings": [
            _reception_antecedent_binding_material(row)
            for row in value.reception_antecedent_bindings
        ],
        "identity_claim_must_not_be_accepted_as_fact": (
            value.identity_claim_must_not_be_accepted_as_fact
        ),
        "self_denial_source_slots": list(value.self_denial_source_slots),
        "self_denial_source_anchor_ids": list(
            value.self_denial_source_anchor_ids
        ),
    }
    if not include_id:
        result.pop("surface_ast_id")
    return result


def _slots_for_nucleus(snapshot: Any, nucleus_id: str) -> tuple[str, ...]:
    row = next(
        (item for item in snapshot.nuclei if item.source_id == nucleus_id),
        None,
    )
    if row is None:
        raise Step11NaturalSurfaceError("STEP11_NUCLEUS_SOURCE_UNRESOLVED")
    return tuple(
        sorted(
            {
                _SOURCE_FIELD_TO_SLOT[field]
                for field in row.source_fields
                if field in _SOURCE_FIELD_TO_SLOT
            },
            key=_SLOT_ORDER.__getitem__,
        )
    )


def _slots_for_obligation(
    row: Mapping[str, Any],
    *,
    snapshot: Any,
) -> tuple[str, ...]:
    slots = {
        slot
        for nucleus_id in row.get("nucleus_ids", [])
        for slot in _slots_for_nucleus(snapshot, nucleus_id)
    }
    return tuple(sorted(slots, key=_SLOT_ORDER.__getitem__))


def _terminal_self_denial_plan_valid(
    discourse_plan: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
) -> bool:
    """Verify the plan, not the renderer, owns terminal boundary ordering."""

    node_for_obligation = {
        str(node.get("obligation_id")): str(node.get("node_id"))
        for node in discourse_plan.get("nodes", [])
        if type(node) is dict
        and type(node.get("obligation_id")) is str
        and type(node.get("node_id")) is str
    }
    active_ids = set(node_for_obligation)
    target_ids = sorted(
        {
            str(target_id)
            for obligation_id in active_ids
            if by_id.get(obligation_id, {}).get("kind") == STANCE_KIND
            for target_id in by_id[obligation_id].get(
                "target_obligation_ids", []
            )
            if target_id in active_ids
            and by_id.get(str(target_id), {}).get("kind")
            == "self_denial_boundary"
        }
    )
    units: list[tuple[str, str]] = []
    for target_id in target_ids:
        target = by_id[target_id]
        nuclei = set(target.get("nucleus_ids", []))
        counters = tuple(
            obligation_id
            for obligation_id in active_ids
            if by_id.get(obligation_id, {}).get("kind")
            == "bounded_counterposition"
            and nuclei
            and set(by_id[obligation_id].get("nucleus_ids", [])) == nuclei
            and obligation_id in set(target.get("must_not_merge_with", []))
            and target_id
            in set(by_id[obligation_id].get("must_not_merge_with", []))
        )
        if len(counters) != 1:
            return False
        units.append(
            (
                node_for_obligation[target_id],
                node_for_obligation[counters[0]],
            )
        )
    if not units:
        return True
    observation_groups = tuple(
        tuple(group.get("node_ids", []))
        for group in discourse_plan.get("sentence_groups", [])
        if type(group) is dict and group.get("section_role") == "observation"
    )
    group_index = {
        node_id: index
        for index, group in enumerate(observation_groups)
        for node_id in group
    }
    edge_set = {
        (edge.get("from"), edge.get("to"), edge.get("type"))
        for edge in discourse_plan.get("edges", [])
        if type(edge) is dict
    }
    if any(
        left not in group_index
        or right not in group_index
        or group_index[left] == group_index[right]
        or (left, right, "separates_self_denial_from") not in edge_set
        for left, right in units
    ):
        return False
    flat = tuple(node_id for group in observation_groups for node_id in group)
    suffix = flat[-(2 * len(units)) :]
    remaining = list(units)
    cursor = 0
    while remaining:
        matches = [
            (index, unit)
            for index, unit in enumerate(remaining)
            if suffix[cursor : cursor + 2] == unit
        ]
        if len(matches) != 1:
            return False
        index, _unit = matches[0]
        cursor += 2
        remaining.pop(index)
    return cursor == len(suffix)


def _trusted_parents(
    inventory_result: Any,
    content_plan: Any,
    discourse_plan: Any,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if type(inventory_result) is not SemanticObligationInventoryResult:
        raise Step11NaturalSurfaceError("STEP11_INVENTORY_RESULT_REQUIRED")
    ledger = inventory_result.ledger
    try:
        inventory_issues = validate_semantic_obligation_inventory(
            ledger,
            source_snapshot=inventory_result.source_snapshot,
        )
        content_issues = validate_content_selection_policy(
            content_plan,
            inventory_result=inventory_result,
        )
        discourse_issues = validate_discourse_plan(
            discourse_plan,
            content_plan=content_plan,
            obligation_ledger=ledger,
        )
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError) as exc:
        raise Step11NaturalSurfaceError("STEP11_PARENT_REVALIDATION_FAILED") from exc
    if inventory_issues:
        raise Step11NaturalSurfaceError("STEP11_INVENTORY_REVALIDATION_FAILED")
    if content_issues:
        raise Step11NaturalSurfaceError("STEP11_CONTENT_REVALIDATION_FAILED")
    if discourse_issues:
        raise Step11NaturalSurfaceError("STEP11_DISCOURSE_REVALIDATION_FAILED")
    rows = ledger.get("obligations")
    if type(rows) is not list:
        raise Step11NaturalSurfaceError("STEP11_LEDGER_ROWS_INVALID")
    by_id = {
        row.get("obligation_id"): row
        for row in rows
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    if len(by_id) != len(rows):
        raise Step11NaturalSurfaceError("STEP11_LEDGER_IDENTITY_INVALID")
    if not _terminal_self_denial_plan_valid(discourse_plan, by_id):
        raise Step11NaturalSurfaceError(
            "STEP11_DISCOURSE_TERMINAL_BOUNDARY_INVALID"
        )
    return ledger, by_id


def _clause_from_node(
    node: Mapping[str, Any],
    *,
    by_id: Mapping[str, Mapping[str, Any]],
    inventory_result: SemanticObligationInventoryResult,
) -> Step11SurfaceClause:
    obligation_id = node.get("obligation_id")
    row = by_id.get(obligation_id)
    if row is None:
        raise Step11NaturalSurfaceError("STEP11_NODE_OBLIGATION_UNRESOLVED")
    kind = row.get("kind")
    clause_form = _CLAUSE_FOR_KIND.get(kind)
    if clause_form is None:
        raise Step11NaturalSurfaceError("STEP11_OBLIGATION_KIND_UNSUPPORTED")
    relation_rows = [
        item
        for item in inventory_result.source_snapshot.relations
        if item.source_id in row.get("relation_ids", [])
    ]
    unknown_rows = [
        item
        for item in inventory_result.source_snapshot.unknowns
        if item.source_id in row.get("unknown_boundary_ids", [])
    ]
    allowed_acts = row.get("allowed_response_acts", [])
    reception_act = (
        next(
            (
                item
                for item in allowed_acts
                if item in STEP11_SURFACE_CATALOG["reception_acts"]
            ),
            None,
        )
        if kind == STANCE_KIND
        else None
    )
    if kind == STANCE_KIND and reception_act is None:
        raise Step11NaturalSurfaceError("STEP11_RECEPTION_ACT_UNSUPPORTED")
    return Step11SurfaceClause(
        discourse_node_id=str(node.get("node_id")),
        obligation_id=str(obligation_id),
        section_role=str(node.get("section_role")),
        clause_form=clause_form,
        source_slots=_slots_for_obligation(
            row,
            snapshot=inventory_result.source_snapshot,
        ),
        source_nucleus_ids=tuple(row.get("nucleus_ids", [])),
        source_relation_ids=tuple(row.get("relation_ids", [])),
        polarity=str(row.get("polarity")),
        modality=str(row.get("modality")),
        temporal_scope=str(row.get("temporal_scope")),
        referent_scope=str(row.get("referent_scope")),
        relation_types=tuple(item.relation_type for item in relation_rows),
        relation_directions=tuple(
            item.relation_direction for item in relation_rows
        ),
        unknown_dimension_codes=tuple(
            item.dimension_code for item in unknown_rows
        ),
        reception_act=reception_act,
        target_obligation_ids=tuple(row.get("target_obligation_ids", [])),
    )


def _surface_semantic_overlay(
    clauses: Sequence[Step11SurfaceClause],
    *,
    inventory_result: SemanticObligationInventoryResult,
    semantic_overlay: Step11SemanticOverlay,
) -> tuple[
    tuple[Step11IntegratedUnknown, ...],
    bool,
    tuple[str, ...],
    tuple[str, ...],
]:
    """Return source-authorised additions deferred by frozen selection.

    This deliberately small boundary is where the Step 11 semantic-overlay
    owner can be connected.  It currently consumes only the already frozen
    source snapshot: no corpus row, family, cue annotation, or expected body
    is observable here.
    """

    active_obligation_ids = {row.obligation_id for row in clauses}
    ledger_by_id = {
        row["obligation_id"]: row
        for row in inventory_result.ledger["obligations"]
    }
    active_nucleus_ids = {
        nucleus_id
        for obligation_id in active_obligation_ids
        for nucleus_id in ledger_by_id[obligation_id].get("nucleus_ids", [])
    }
    active_nucleus_ids.update(
        row.nucleus_id for row in semantic_overlay.nucleus_anchor_bindings
    )
    unknowns: list[Step11IntegratedUnknown] = []
    for row in semantic_overlay.unknowns:
        affected = set(row.target_nucleus_ids)
        if affected and not affected <= active_nucleus_ids:
            continue
        unknowns.append(
            Step11IntegratedUnknown(
                source_unknown_id=row.unknown_id,
                dimension_code=row.unknown_type,
                source_slots=tuple(
                    sorted(row.source_slots, key=_SLOT_ORDER.__getitem__)
                ),
                source_anchor_ids=row.source_anchor_ids,
                target_nucleus_ids=row.target_nucleus_ids,
                source_unknown_ids=row.source_unknown_ids,
                owner_obligation_ids=tuple(
                    clause.obligation_id
                    for clause in clauses
                    if clause.section_role == "observation"
                    and clause.clause_form == "unknown_boundary"
                    and bool(
                        set(
                            ledger_by_id[clause.obligation_id].get(
                                "unknown_boundary_ids", []
                            )
                        )
                        & set(row.source_unknown_ids)
                    )
                ),
                source_rules=row.source_rules,
                epistemic_basis=row.epistemic_basis,
                decision_state=row.decision_state,
                context_nucleus_ids=row.context_nucleus_ids,
                context_anchor_ids=row.context_anchor_ids,
                surface_policy=row.surface_policy,
            )
        )
    # The exact Step 11 overlay is authoritative for identity boundaries.
    # A coarse upstream safety flag without a source-resolved self-evaluation
    # must not fabricate a denial anchor or turn accountability into identity.
    self_evaluations = semantic_overlay.reported_self_evaluations
    identity_boundary = bool(self_evaluations)
    self_denial_slots = {row.source_slot for row in self_evaluations}
    self_denial_anchor_ids = [
        row.source_anchor_id for row in self_evaluations
    ]
    return (
        tuple(
            sorted(
                unknowns,
                key=lambda row: (
                    row.source_unknown_id,
                    row.dimension_code,
                    row.source_slots,
                ),
            )
        ),
        identity_boundary,
        tuple(sorted(self_denial_slots, key=_SLOT_ORDER.__getitem__)),
        tuple(dict.fromkeys(self_denial_anchor_ids)),
    )


def _relations_from_semantic_overlay(
    semantic_overlay: Step11SemanticOverlay,
    *,
    clauses: Sequence[Step11SurfaceClause],
    nucleus_surface_references: Sequence[
        Step11NucleusSurfaceReference
    ],
) -> tuple[Step11IntegratedRelation, ...]:
    reference_by_anchor = {
        anchor_id: reference
        for reference in nucleus_surface_references
        for anchor_id in reference.source_anchor_ids
    }
    result: list[Step11IntegratedRelation] = []
    for row in semantic_overlay.relations:
        from_anchor_ids = (
            *row.from_source_anchor_ids,
            *row.from_label_anchor_ids,
        )
        to_anchor_ids = (
            *row.to_source_anchor_ids,
            *row.to_label_anchor_ids,
        )
        if (
            len(from_anchor_ids) != 1
            or len(to_anchor_ids) != 1
            or from_anchor_ids == to_anchor_ids
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RELATION_EXACT_TWO_ANCHORS_REQUIRED"
            )
        owner_obligation_ids = tuple(
            clause.obligation_id
            for clause in clauses
            if clause.section_role == "observation"
            and clause.clause_form == "relation_notice"
            and set(clause.source_relation_ids) & set(row.source_relation_ids)
        )
        if not owner_obligation_ids:
            raise Step11NaturalSurfaceError(
                "STEP11_RELATION_OWNER_OBLIGATION_UNRESOLVED"
            )
        from_reference = reference_by_anchor.get(from_anchor_ids[0])
        to_reference = reference_by_anchor.get(to_anchor_ids[0])
        if (
            from_reference is None
            or to_reference is None
            or from_reference.reference_ordinal
            == to_reference.reference_ordinal
            or row.from_nucleus_id not in from_reference.nucleus_ids
            or row.to_nucleus_id not in to_reference.nucleus_ids
            or from_reference.endpoint_role != row.from_endpoint_role
            or to_reference.endpoint_role != row.to_endpoint_role
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RELATION_ENDPOINT_REFERENCE_MISMATCH"
            )
        result.append(
            Step11IntegratedRelation(
                source_relation_id=row.source_relation_id,
                source_relation_ids=row.source_relation_ids,
                relation_type=row.relation_type,
                relation_direction=row.relation_direction,
                from_nucleus_id=row.from_nucleus_id,
                to_nucleus_id=row.to_nucleus_id,
                from_source_slots=row.from_source_slots,
                to_source_slots=row.to_source_slots,
                from_source_anchor_ids=from_anchor_ids,
                to_source_anchor_ids=to_anchor_ids,
                from_endpoint_role=row.from_endpoint_role,
                to_endpoint_role=row.to_endpoint_role,
                from_reference_ordinal=(
                    from_reference.reference_ordinal
                ),
                to_reference_ordinal=to_reference.reference_ordinal,
                required=row.required,
                owner_obligation_ids=owner_obligation_ids,
                evidence_grade=row.evidence_grade,
            )
        )
    return tuple(result)


def _mixed_emotion_requirements_from_semantic_overlay(
    semantic_overlay: Step11SemanticOverlay,
) -> tuple[Step11IntegratedMixedEmotionRequirement, ...]:
    return tuple(
        Step11IntegratedMixedEmotionRequirement(
            requirement_id=row.requirement_id,
            positive_label_anchor_ids=row.positive_label_anchor_ids,
            negative_label_anchor_ids=row.negative_label_anchor_ids,
            relation_type=row.relation_type,
            relation_direction=row.relation_direction,
            required=row.required,
            evidence_grade=row.evidence_grade,
        )
        for row in semantic_overlay.mixed_emotion_requirements
    )


def _reception_bindings_from_semantic_overlay(
    semantic_overlay: Step11SemanticOverlay,
) -> tuple[Step11IntegratedReceptionAntecedentBinding, ...]:
    return tuple(
        Step11IntegratedReceptionAntecedentBinding(
            binding_id=row.binding_id,
            reception_obligation_id=row.reception_obligation_id,
            reception_node_id=row.reception_node_id,
            source_target_obligation_ids=row.source_target_obligation_ids,
            source_target_node_ids=row.source_target_node_ids,
            source_target_nucleus_ids=row.source_target_nucleus_ids,
            antecedent_obligation_ids=row.antecedent_obligation_ids,
            antecedent_node_ids=row.antecedent_node_ids,
            antecedent_nucleus_ids=row.antecedent_nucleus_ids,
            supporting_obligation_ids=row.supporting_obligation_ids,
            supporting_node_ids=row.supporting_node_ids,
            supporting_nucleus_ids=row.supporting_nucleus_ids,
            support_role=row.support_role,
            source_reception_opportunity_ids=(
                row.source_reception_opportunity_ids
            ),
            action_lifecycle=row.action_lifecycle,
            allowed_response_acts=row.allowed_response_acts,
            evidence_grade=row.evidence_grade,
        )
        for row in semantic_overlay.reception_antecedent_bindings
    )


def _rc0020_repartition_sentences(
    sentences: Sequence[Step11SurfaceSentence],
) -> tuple[Step11SurfaceSentence, ...]:
    """Project frozen Step 6 groups onto the rc0020 two-phase order.

    Step 6 remains byte-frozen for the v1/v2 parser lineage.  rc0020 keeps the
    exact group IDs and group cardinalities, but repartitions their clauses so
    every source nucleus is introduced before typed relations, and every
    relation before unknown/self-denial boundaries.  This is a general typed
    phase order; source text and corpus case IDs are not inspected.
    """

    observation = tuple(
        row for row in sentences if row.section_role == "observation"
    )
    reception = tuple(
        row for row in sentences if row.section_role == "reception"
    )
    if not observation or not reception:
        raise Step11NaturalSurfaceError(
            "STEP11_SENTENCE_PHASE_PARTITION_INVALID"
        )
    phase_by_form = {
        "nucleus_notice": 0,
        "shift_notice": 0,
        "next_action": 0,
        "relation_notice": 1,
        "unknown_boundary": 2,
        "self_denial_boundary": 3,
        "bounded_counterposition": 4,
    }
    indexed_clauses = tuple(
        (index, clause)
        for index, clause in enumerate(
            clause
            for sentence in observation
            for clause in sentence.clauses
        )
    )
    if any(clause.clause_form not in phase_by_form for _, clause in indexed_clauses):
        raise Step11NaturalSurfaceError(
            "STEP11_SENTENCE_PHASE_CLAUSE_UNSUPPORTED"
        )
    ordered = tuple(
        clause
        for _index, clause in sorted(
            indexed_clauses,
            key=lambda item: (phase_by_form[item[1].clause_form], item[0]),
        )
    )
    cursor = 0
    projected: list[Step11SurfaceSentence] = []
    for sentence in observation:
        width = len(sentence.clauses)
        clauses = ordered[cursor : cursor + width]
        cursor += width
        if len(clauses) != width:
            raise Step11NaturalSurfaceError(
                "STEP11_SENTENCE_PHASE_CARDINALITY_INVALID"
            )
        projected.append(
            Step11SurfaceSentence(
                discourse_sentence_group_id=(
                    sentence.discourse_sentence_group_id
                ),
                section_role="observation",
                clauses=clauses,
            )
        )
    if cursor != len(ordered):
        raise Step11NaturalSurfaceError(
            "STEP11_SENTENCE_PHASE_CARDINALITY_INVALID"
        )
    return tuple((*projected, *reception))


def _build_ast(
    discourse_plan: Mapping[str, Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    projection: Step11CurrentInputProjection,
    current_input: Mapping[str, Any],
) -> Step11NaturalSurfaceAst:
    ledger, by_id = _trusted_parents(
        inventory_result, content_plan, discourse_plan
    )
    semantic_overlay = build_step11_semantic_overlay(
        current_input,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=discourse_plan,
    )
    node_by_id = {
        row["node_id"]: row for row in discourse_plan["nodes"]
    }
    sentences: list[Step11SurfaceSentence] = []
    seen_nodes: list[str] = []
    for group in discourse_plan["sentence_groups"]:
        clauses = tuple(
            _clause_from_node(
                node_by_id[node_id],
                by_id=by_id,
                inventory_result=inventory_result,
            )
            for node_id in group["node_ids"]
        )
        seen_nodes.extend(group["node_ids"])
        sentences.append(
            Step11SurfaceSentence(
                discourse_sentence_group_id=group["sentence_group_id"],
                section_role=group["section_role"],
                clauses=clauses,
            )
        )
    if sorted(seen_nodes) != sorted(node_by_id):
        raise Step11NaturalSurfaceError("STEP11_DISCOURSE_NODE_COVERAGE_INVALID")
    sentences = list(_rc0020_repartition_sentences(sentences))
    all_clauses = tuple(
        clause for sentence in sentences for clause in sentence.clauses
    )
    (
        integrated_unknowns,
        identity_boundary,
        self_denial_slots,
        self_denial_anchor_ids,
    ) = (
        _surface_semantic_overlay(
            all_clauses,
            inventory_result=inventory_result,
            semantic_overlay=semantic_overlay,
        )
    )
    source_fragments = _source_fragments(semantic_overlay)
    nucleus_surface_references = _nucleus_surface_references(
        source_fragments,
        sentences,
        semantic_overlay=semantic_overlay,
    )
    integrated_relations = _relations_from_semantic_overlay(
        semantic_overlay,
        clauses=all_clauses,
        nucleus_surface_references=nucleus_surface_references,
    )
    ast = Step11NaturalSurfaceAst(
        schema_version=STEP11_SURFACE_AST_SCHEMA,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        surface_ast_id="nls3s11ast_0000000000000000",
        source_obligation_ledger_sha256=artifact_sha256(ledger),
        source_content_plan_sha256=artifact_sha256(content_plan),
        source_discourse_plan_sha256=artifact_sha256(discourse_plan),
        source_semantic_overlay_sha256=artifact_sha256(
            step11_semantic_overlay_material(semantic_overlay)
        ),
        current_input_projection_sha256=artifact_sha256(
            _projection_material(projection)
        ),
        surface_catalog_sha256=STEP11_SURFACE_CATALOG_SHA256,
        surface_realization_plan=None,
        source_fragments=source_fragments,
        nucleus_surface_references=nucleus_surface_references,
        sentences=tuple(sentences),
        integrated_relations=integrated_relations,
        integrated_unknowns=integrated_unknowns,
        mixed_emotion_requirements=(
            _mixed_emotion_requirements_from_semantic_overlay(
                semantic_overlay
            )
        ),
        reception_antecedent_bindings=(
            _reception_bindings_from_semantic_overlay(semantic_overlay)
        ),
        identity_claim_must_not_be_accepted_as_fact=identity_boundary,
        self_denial_source_slots=self_denial_slots,
        self_denial_source_anchor_ids=self_denial_anchor_ids,
    )
    observation_lines = _additional_observation_lines(ast)
    reception_lines = _reception_lines(
        ast, observation_lines=observation_lines
    )
    realization_plan = _derive_surface_realization_plan(
        ast, observation_lines, reception_lines
    )
    ast = Step11NaturalSurfaceAst(
        schema_version=ast.schema_version,
        candidate_version_id=ast.candidate_version_id,
        surface_ast_id=ast.surface_ast_id,
        source_obligation_ledger_sha256=ast.source_obligation_ledger_sha256,
        source_content_plan_sha256=ast.source_content_plan_sha256,
        source_discourse_plan_sha256=ast.source_discourse_plan_sha256,
        source_semantic_overlay_sha256=ast.source_semantic_overlay_sha256,
        current_input_projection_sha256=ast.current_input_projection_sha256,
        surface_catalog_sha256=ast.surface_catalog_sha256,
        surface_realization_plan=realization_plan,
        source_fragments=ast.source_fragments,
        nucleus_surface_references=ast.nucleus_surface_references,
        sentences=ast.sentences,
        integrated_relations=ast.integrated_relations,
        integrated_unknowns=ast.integrated_unknowns,
        mixed_emotion_requirements=ast.mixed_emotion_requirements,
        reception_antecedent_bindings=ast.reception_antecedent_bindings,
        identity_claim_must_not_be_accepted_as_fact=(
            ast.identity_claim_must_not_be_accepted_as_fact
        ),
        self_denial_source_slots=ast.self_denial_source_slots,
        self_denial_source_anchor_ids=ast.self_denial_source_anchor_ids,
    )
    derived_id = "nls3s11ast_" + artifact_sha256(
        step11_surface_ast_material(ast, include_id=False)
    )[:16]
    return Step11NaturalSurfaceAst(
        schema_version=ast.schema_version,
        candidate_version_id=ast.candidate_version_id,
        surface_ast_id=derived_id,
        source_obligation_ledger_sha256=ast.source_obligation_ledger_sha256,
        source_content_plan_sha256=ast.source_content_plan_sha256,
        source_discourse_plan_sha256=ast.source_discourse_plan_sha256,
        source_semantic_overlay_sha256=(
            ast.source_semantic_overlay_sha256
        ),
        current_input_projection_sha256=ast.current_input_projection_sha256,
        surface_catalog_sha256=ast.surface_catalog_sha256,
        surface_realization_plan=ast.surface_realization_plan,
        source_fragments=ast.source_fragments,
        nucleus_surface_references=ast.nucleus_surface_references,
        sentences=ast.sentences,
        integrated_relations=ast.integrated_relations,
        integrated_unknowns=ast.integrated_unknowns,
        mixed_emotion_requirements=ast.mixed_emotion_requirements,
        reception_antecedent_bindings=ast.reception_antecedent_bindings,
        identity_claim_must_not_be_accepted_as_fact=(
            ast.identity_claim_must_not_be_accepted_as_fact
        ),
        self_denial_source_slots=ast.self_denial_source_slots,
        self_denial_source_anchor_ids=ast.self_denial_source_anchor_ids,
    )


def _quoted(value: str) -> str:
    layout = STEP11_SURFACE_CATALOG["layout"]
    opening = layout["quote_open"]
    closing = layout["quote_close"]
    alternate = layout["quote_pairs"][1]
    if opening not in value and closing not in value:
        return f"{opening}{value}{closing}"
    if alternate["open"] not in value and alternate["close"] not in value:
        return f"{alternate['open']}{value}{alternate['close']}"
    # Rare mixed-pair fallback: escape backslash first, then only the primary
    # pair.  The alternate pair remains literal; the transform is injective
    # and canonical re-encoding can be checked by the body-only parser.
    escaped = (
        value.replace("\\", "\\\\")
        .replace(opening, "\\" + opening)
        .replace(closing, "\\" + closing)
    )
    return f"{opening}{escaped}{closing}"


def _pick_variant(
    options: Sequence[Any],
    *,
    fingerprint: str,
    form_id: str,
) -> Any:
    if type(options) not in {list, tuple} or not options:
        raise Step11NaturalSurfaceError("STEP11_SURFACE_VARIANT_SET_INVALID")
    digest = hashlib.sha256(
        f"{fingerprint}\x00{form_id}".encode("utf-8")
    ).digest()
    return options[int.from_bytes(digest[:8], "big") % len(options)]


def _fragment_by_anchor_id(
    ast: Step11NaturalSurfaceAst,
    anchor_id: str,
) -> Step11SourceFragment:
    result = next(
        (
            row
            for row in ast.source_fragments
            if row.source_anchor_id == anchor_id
        ),
        None,
    )
    if result is None:
        raise Step11NaturalSurfaceError(
            "STEP11_SOURCE_ANCHOR_FRAGMENT_UNRESOLVED"
        )
    return result


def _relation_line(
    relation: Step11IntegratedRelation,
    *,
    ast: Step11NaturalSurfaceAst,
) -> str:
    variants = STEP11_SURFACE_CATALOG["relation_forms"][
        relation.relation_type
    ][relation.relation_direction][relation.from_endpoint_role][
        relation.to_endpoint_role
    ]
    rule = _pick_variant(
        variants,
        fingerprint=ast.current_input_projection_sha256,
        form_id=(
            f"relation:{relation.source_relation_id}:"
            f"{relation.relation_type}:{relation.relation_direction}:"
            f"{relation.from_endpoint_role}:{relation.to_endpoint_role}"
        ),
    )
    if (
        rule.get("endpoint_realization") != "typed_reference_only"
        or type(rule.get("stem")) is not str
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RELATION_REFERENCE_FORM_INVALID"
        )
    return rule["stem"].format(
        from_ref=_endpoint_reference_token(
            relation.from_reference_ordinal,
            relation.from_endpoint_role,
        ),
        to_ref=_endpoint_reference_token(
            relation.to_reference_ordinal,
            relation.to_endpoint_role,
        ),
    )


def _endpoint_reference_token(ordinal: int, endpoint_role: str) -> str:
    grammar = STEP11_SURFACE_CATALOG["endpoint_reference_grammar"]
    labels = grammar["role_labels"]
    if (
        type(ordinal) is not int
        or ordinal < grammar["minimum_ordinal"]
        or endpoint_role not in labels
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_ENDPOINT_REFERENCE_TOKEN_INVALID"
        )
    return grammar["reference_token_template"].format(
        ordinal=ordinal,
        role_label=labels[endpoint_role],
    )


def _reference_for_anchor(
    ast: Step11NaturalSurfaceAst,
    anchor_id: str,
) -> Step11NucleusSurfaceReference:
    matches = tuple(
        row
        for row in ast.nucleus_surface_references
        if anchor_id in row.source_anchor_ids
    )
    if len(matches) != 1:
        raise Step11NaturalSurfaceError(
            "STEP11_ENDPOINT_REFERENCE_ANCHOR_UNRESOLVED"
        )
    return matches[0]


def _references_for_unknown_targets(
    ast: Step11NaturalSurfaceAst,
    target_nucleus_ids: Sequence[str],
) -> tuple[Step11NucleusSurfaceReference, ...]:
    """Resolve every unknown target to one unique typed source reference."""

    targets = frozenset(str(value) for value in target_nucleus_ids)
    if not targets:
        raise Step11NaturalSurfaceError(
            "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
        )
    resolved: dict[int, Step11NucleusSurfaceReference] = {}
    for nucleus_id in sorted(targets):
        matches = tuple(
            row
            for row in ast.nucleus_surface_references
            if nucleus_id in row.nucleus_ids
        )
        if len(matches) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
            )
        resolved[matches[0].reference_ordinal] = matches[0]
    references = tuple(resolved[key] for key in sorted(resolved))
    if targets != frozenset(
        nucleus_id
        for reference in references
        for nucleus_id in reference.nucleus_ids
        if nucleus_id in targets
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
        )
    return references


def _direct_introduction_line(
    fragment: Step11SourceFragment,
    *,
    ast: Step11NaturalSurfaceAst,
) -> str:
    reference = _reference_for_anchor(ast, fragment.source_anchor_id)
    direct = STEP11_SURFACE_CATALOG[
        "endpoint_reference_grammar"
    ]["direct_introduction"]
    stem = _pick_variant(
        direct["stems"],
        fingerprint=ast.current_input_projection_sha256,
        form_id=(
            f"endpoint_introduction:{reference.reference_ordinal}:"
            f"{reference.endpoint_role}:{reference.source_identity_key}"
        ),
    )
    return direct["wrapper"].format(
        reference=_endpoint_reference_token(
            reference.reference_ordinal,
            reference.endpoint_role,
        ),
        stem=stem.format(quoted_literal=_quoted(fragment.text)),
    )


def _relation_endpoint_texts(
    relation: Step11IntegratedRelation,
    *,
    ast: Step11NaturalSurfaceAst,
) -> tuple[str, str]:
    if (
        len(relation.from_source_anchor_ids) != 1
        or len(relation.to_source_anchor_ids) != 1
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RELATION_EXACT_TWO_ANCHORS_REQUIRED"
        )
    from_text = _fragment_by_anchor_id(
        ast, relation.from_source_anchor_ids[0]
    ).text
    to_text = _fragment_by_anchor_id(
        ast, relation.to_source_anchor_ids[0]
    ).text
    if from_text == to_text:
        raise Step11NaturalSurfaceError(
            "STEP11_RELATION_ENDPOINT_TEXT_EQUAL"
        )
    return from_text, to_text


def _observation_rule(
    fragment: Step11SourceFragment,
    *,
    ast: Step11NaturalSurfaceAst,
) -> Mapping[str, str]:
    forms = STEP11_SURFACE_CATALOG["observation_forms"]
    if fragment.source_slot not in {"thought", "action", "emotion", "category"}:
        raise Step11NaturalSurfaceError(
            "STEP11_OBSERVATION_SOURCE_ROLE_UNSUPPORTED"
        )
    key = fragment.source_slot
    options = forms[key]
    form_class = (
        "question"
        if key == "thought" and fragment.text.rstrip().endswith(("？", "?"))
        else "default"
    )
    if key == "thought":
        indices = STEP11_SURFACE_CATALOG["observation_form_indices"][
            "thought"
        ][form_class]
        options = [options[index] for index in indices]
    return _pick_variant(
        options,
        fingerprint=ast.current_input_projection_sha256,
        form_id=(
            f"source_nucleus:{fragment.source_anchor_id}:"
            f"{key}:{form_class}"
        ),
    )


def _unknown_dimension_class(value: str) -> str:
    code = unicodedata.normalize("NFC", value).casefold()
    if code == "decision_state" or "unresolved_intention" in code:
        return "decision_state"
    if code == "post_decision_comparative_merit":
        return "post_decision_comparative_merit"
    if code in {"other_person", "other_person_awareness"}:
        return "other_person_awareness"
    if any(token in code for token in ("cause", "reason", "background")):
        return "cause"
    if any(
        token in code
        for token in ("referent", "target", "subject", "other_person")
    ):
        return "referent"
    if "decision" in code:
        return "decision_state"
    if any(token in code for token in ("future", "next", "later")):
        return "future"
    if any(token in code for token in ("outcome", "result", "effect")):
        return "outcome"
    if any(token in code for token in ("relation", "connection", "link")):
        return "relation"
    return "generic"


def _additional_observation_lines(
    ast: Step11NaturalSurfaceAst,
) -> tuple[_Step11OwnedObservationLine, ...]:
    lines: list[_Step11OwnedObservationLine] = []
    forms = STEP11_SURFACE_CATALOG["observation_forms"]
    covered_anchor_ids: set[str] = set()
    realised_self: set[str] = set()
    observation_clauses = tuple(
        clause
        for sentence in ast.sentences
        if sentence.section_role == "observation"
        for clause in sentence.clauses
    )
    claimed_basic_obligations: set[str] = set()
    realised_unknown_obligation_ids = {
        obligation_id
        for unknown in ast.integrated_unknowns
        for obligation_id in unknown.owner_obligation_ids
    }
    def equivalent_anchor_ids(anchor_id: str) -> tuple[str, ...]:
        fragment = _fragment_by_anchor_id(ast, anchor_id)
        if fragment.fragment_role == "label":
            return (anchor_id,)
        return tuple(
            row.source_anchor_id
            for row in ast.source_fragments
            if row.fragment_role != "label"
            and row.source_slot == fragment.source_slot
            and row.source_start == fragment.source_start
            and row.source_end == fragment.source_end
            and row.text == fragment.text
        )

    def anchors_overlap(left_anchor_id: str, right_anchor_id: str) -> bool:
        left = _fragment_by_anchor_id(ast, left_anchor_id)
        right = _fragment_by_anchor_id(ast, right_anchor_id)
        if left.fragment_role == "label" or right.fragment_role == "label":
            return left_anchor_id == right_anchor_id
        return (
            left.source_slot == right.source_slot
            and max(left.source_start, right.source_start)
            < min(left.source_end, right.source_end)
        )

    def line_owns_anchor(
        line: _Step11OwnedObservationLine,
        target_anchor_id: str,
        *,
        target_nucleus_ids: Sequence[str] = (),
    ) -> bool:
        target = _fragment_by_anchor_id(ast, target_anchor_id)
        if target_nucleus_ids:
            target_nucleus_set = set(target_nucleus_ids)
            # A typed unknown is owned by the one exact source introduction
            # for its target nucleus.  Mere enclosing-range coverage is not
            # ownership, and a quote-free relation cannot become an owner.
            return target_nucleus_set <= set(line.owned_nucleus_ids) and any(
                target_nucleus_set
                & set(
                    _fragment_by_anchor_id(ast, literal_anchor_id)
                    .source_nucleus_ids
                )
                for literal_anchor_id in line.literal_anchor_ids
            )
        exact_owners = tuple(
            owner
            for literal_anchor_id in line.literal_anchor_ids
            for owner in (_fragment_by_anchor_id(ast, literal_anchor_id),)
            if owner.fragment_role == target.fragment_role
            and owner.source_slot == target.source_slot
            and owner.source_field == target.source_field
            and owner.source_ordinal == target.source_ordinal
            and owner.source_start == target.source_start
            and owner.source_end == target.source_end
            and owner.text == target.text
        )
        if not exact_owners:
            return False
        # rc0020 owner cardinality is a semantic-key count.  An enclosing
        # unknown span cannot become a second owner of a nested nucleus merely
        # because its byte range covers that nucleus.  Exact range/label
        # identity is necessary, and a nucleus-bearing anchor also retains its
        # target-nucleus ownership.
        return not target.source_nucleus_ids or set(
            target.source_nucleus_ids
        ) <= set(line.owned_nucleus_ids)

    def visible_literal_owner_count(
        anchor_id: str,
        *,
        target_nucleus_ids: Sequence[str] = (),
    ) -> int:
        return sum(
            line_owns_anchor(
                line,
                anchor_id,
                target_nucleus_ids=target_nucleus_ids,
            )
            for line in lines
        )

    def claim_basic_obligations(
        nucleus_ids: Sequence[str],
    ) -> tuple[str, ...]:
        nucleus_set = set(nucleus_ids)
        claimed = tuple(
            clause.obligation_id
            for clause in observation_clauses
            if clause.clause_form not in {
                "relation_notice",
                "self_denial_boundary",
                "bounded_counterposition",
            }
            and not (
                clause.clause_form == "unknown_boundary"
                and clause.obligation_id
                in realised_unknown_obligation_ids
            )
            and clause.obligation_id not in claimed_basic_obligations
            and bool(clause.source_nucleus_ids)
            and set(clause.source_nucleus_ids) <= nucleus_set
        )
        claimed_basic_obligations.update(claimed)
        return claimed

    for relation in ast.integrated_relations:
        endpoint_anchor_ids = (
            relation.from_source_anchor_ids[0],
            relation.to_source_anchor_ids[0],
        )
        owned_anchor_ids = tuple(
            dict.fromkeys(
                anchor_id
                for endpoint_id in endpoint_anchor_ids
                for anchor_id in equivalent_anchor_ids(endpoint_id)
            )
        )
        nucleus_ids = (relation.from_nucleus_id, relation.to_nucleus_id)
        owner_ids = relation.owner_obligation_ids
        lines.append(
            _Step11OwnedObservationLine(
                text=_relation_line(relation, ast=ast),
                owned_anchor_ids=owned_anchor_ids,
                owned_nucleus_ids=nucleus_ids,
                owned_relation_ids=relation.source_relation_ids,
                owned_obligation_ids=owner_ids,
                owned_mixed_emotion_requirement_ids=(),
                literal_anchor_ids=(),
                required_relation_ids=(
                    (relation.source_relation_id,)
                    if relation.required
                    else ()
                ),
                used_reference_ordinals=tuple(
                    dict.fromkeys(
                        (
                            relation.from_reference_ordinal,
                            relation.to_reference_ordinal,
                        )
                    )
                ),
            )
        )

    for requirement in ast.mixed_emotion_requirements:
        if (
            not requirement.required
            or requirement.relation_type != "coexists_with"
            or requirement.relation_direction != "bidirectional"
            or not requirement.positive_label_anchor_ids
            or not requirement.negative_label_anchor_ids
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_MIXED_EMOTION_REQUIREMENT_INVALID"
            )
        positive_id = requirement.positive_label_anchor_ids[0]
        negative_id = requirement.negative_label_anchor_ids[0]
        positive = _fragment_by_anchor_id(ast, positive_id)
        negative = _fragment_by_anchor_id(ast, negative_id)
        if any(
            row.fragment_role != "label" or row.source_slot != "emotion"
            for row in (positive, negative)
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_MIXED_EMOTION_LABEL_ANCHOR_INVALID"
            )
        positive_reference = _reference_for_anchor(ast, positive_id)
        negative_reference = _reference_for_anchor(ast, negative_id)
        if (
            positive_reference.endpoint_role != "affect"
            or negative_reference.endpoint_role != "affect"
            or positive_reference.reference_ordinal
            == negative_reference.reference_ordinal
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_MIXED_EMOTION_REFERENCE_INVALID"
            )
        compound = STEP11_SURFACE_CATALOG[
            "mixed_emotion_compound_grammar"
        ]
        rule = _pick_variant(
            compound["forms"],
            fingerprint=ast.current_input_projection_sha256,
            form_id=(
                "mixed_emotion_compound:"
                f"{requirement.requirement_id}"
            ),
        )
        anchor_ids = (positive_id, negative_id)
        nucleus_ids = tuple(
            dict.fromkeys(
                (*positive.source_nucleus_ids, *negative.source_nucleus_ids)
            )
        )
        lines.append(
            _Step11OwnedObservationLine(
                text=rule.format(
                        positive_ref=_endpoint_reference_token(
                            positive_reference.reference_ordinal,
                            "affect",
                        ),
                        positive_literal=_quoted(positive.text),
                        negative_ref=_endpoint_reference_token(
                            negative_reference.reference_ordinal,
                            "affect",
                        ),
                        negative_literal=_quoted(negative.text),
                ),
                owned_anchor_ids=anchor_ids,
                owned_nucleus_ids=nucleus_ids,
                owned_relation_ids=(),
                owned_obligation_ids=claim_basic_obligations(
                    nucleus_ids
                ),
                owned_mixed_emotion_requirement_ids=(
                    requirement.requirement_id,
                ),
                literal_anchor_ids=anchor_ids,
                required_relation_ids=(requirement.requirement_id,),
                used_reference_ordinals=(
                    positive_reference.reference_ordinal,
                    negative_reference.reference_ordinal,
                ),
            )
        )
        covered_anchor_ids.update(anchor_ids)

    unknown_by_anchor: dict[str, list[Step11IntegratedUnknown]] = {}
    for row in ast.integrated_unknowns:
        if len(row.source_anchor_ids) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_EXACT_SOURCE_ANCHOR_REQUIRED"
            )
        unknown_by_anchor.setdefault(row.source_anchor_ids[0], []).append(row)
    realised_unknowns: set[str] = set()
    used_unknown_rule_indices: dict[str, set[int]] = {}

    def relation_antecedent_owners(
        unknown: Step11IntegratedUnknown,
    ) -> tuple[_Step11OwnedObservationLine, ...]:
        target_set = frozenset(unknown.target_nucleus_ids)
        return tuple(
            line
            for line in lines
            if line.owned_relation_ids
            and target_set
            and frozenset(line.owned_nucleus_ids) == target_set
        )

    def append_unknown(
        unknown: Step11IntegratedUnknown,
    ) -> None:
        if unknown.source_unknown_id in realised_unknowns:
            return
        realised_unknowns.add(unknown.source_unknown_id)
        anchor_id = unknown.source_anchor_ids[0]
        dimension = _unknown_dimension_class(unknown.dimension_code)
        owned_nucleus_ids = tuple(
            dict.fromkeys(
                (
                    *unknown.target_nucleus_ids,
                    *unknown.context_nucleus_ids,
                )
            )
        )
        owner_obligation_ids = unknown.owner_obligation_ids
        anchor_owner_ids = tuple(
            dict.fromkeys(
                (
                    *equivalent_anchor_ids(anchor_id),
                    *unknown.context_anchor_ids,
                )
            )
        )
        relation_owners = relation_antecedent_owners(unknown)
        if len(relation_owners) > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_ANTECEDENT_OWNER_AMBIGUOUS"
            )
        owner_count = (
            1
            if relation_owners
            else visible_literal_owner_count(
                anchor_id,
                target_nucleus_ids=unknown.target_nucleus_ids,
            )
        )
        if owner_count == 0:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_ANTECEDENT_OWNER_MISSING"
            )
        if owner_count > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_ANTECEDENT_OWNER_AMBIGUOUS"
            )
        anaphora_key = (
            "referent_other"
            if dimension == "other_person_awareness"
            or (
                dimension == "referent"
                and "other_person" in unknown.dimension_code.casefold()
            )
            else dimension
        )
        target_references = _references_for_unknown_targets(
            ast,
            unknown.target_nucleus_ids,
        )
        if len(target_references) == 2:
            if len(relation_owners) != 1:
                raise Step11NaturalSurfaceError(
                    "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
                )
            owner_relation_ids = set(
                relation_owners[0].owned_relation_ids
            )
            target_set = frozenset(unknown.target_nucleus_ids)
            source_relations = tuple(
                row
                for row in ast.integrated_relations
                if owner_relation_ids
                & set((row.source_relation_id, *row.source_relation_ids))
                and frozenset(
                    (row.from_nucleus_id, row.to_nucleus_id)
                )
                == target_set
            )
            if len(source_relations) != 1:
                raise Step11NaturalSurfaceError(
                    "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
                )
            reference_by_ordinal = {
                row.reference_ordinal: row for row in target_references
            }
            source_relation = source_relations[0]
            if {
                source_relation.from_reference_ordinal,
                source_relation.to_reference_ordinal,
            } != set(reference_by_ordinal):
                raise Step11NaturalSurfaceError(
                    "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
                )
            target_references = (
                reference_by_ordinal[
                    source_relation.from_reference_ordinal
                ],
                reference_by_ordinal[source_relation.to_reference_ordinal],
            )
        if dimension == "relation":
            if len(target_references) != 2:
                raise Step11NaturalSurfaceError(
                    "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
                )
        elif len(target_references) not in {1, 2}:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_TARGET_REFERENCE_UNRESOLVED"
            )
        unknown_rules = forms["unknown_anaphora"][anaphora_key]
        preferred = _pick_variant(
            unknown_rules,
            fingerprint=ast.current_input_projection_sha256,
            form_id=(
                f"unknown_anaphora:{anaphora_key}:"
                f"{unknown.source_unknown_id}:{anchor_id}"
            ),
        )
        preferred_index = unknown_rules.index(preferred)
        used_indices = used_unknown_rule_indices.setdefault(
            anaphora_key, set()
        )
        available_indices = tuple(
            index
            for offset in range(len(unknown_rules))
            for index in ((preferred_index + offset) % len(unknown_rules),)
            if index not in used_indices
        )
        selected_index = (
            available_indices[0]
            if available_indices
            else preferred_index
        )
        used_indices.add(selected_index)
        rule = unknown_rules[selected_index]
        if type(rule) is not dict or set(rule) != {"stem"}:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_TARGET_REFERENCE_FORM_INVALID"
            )
        if dimension == "relation":
            unknown_text = str(rule["stem"]).format(
                from_ref=_endpoint_reference_token(
                    target_references[0].reference_ordinal,
                    target_references[0].endpoint_role,
                ),
                to_ref=_endpoint_reference_token(
                    target_references[1].reference_ordinal,
                    target_references[1].endpoint_role,
                ),
            )
        else:
            target_reference_text = "と".join(
                _endpoint_reference_token(
                    reference.reference_ordinal,
                    reference.endpoint_role,
                )
                for reference in target_references
            )
            unknown_text = str(rule["stem"]).format(
                target_ref=target_reference_text
            )
        lines.append(
            _Step11OwnedObservationLine(
                text=unknown_text,
                owned_anchor_ids=anchor_owner_ids,
                owned_nucleus_ids=owned_nucleus_ids,
                owned_relation_ids=(),
                owned_obligation_ids=owner_obligation_ids,
                owned_mixed_emotion_requirement_ids=(),
                literal_anchor_ids=(),
                required_relation_ids=(),
                used_reference_ordinals=tuple(
                    reference.reference_ordinal
                    for reference in target_references
                ),
            ),
        )

    def append_self_denial(
        anchor_id: str,
    ) -> None:
        if anchor_id in realised_self:
            return
        realised_self.add(anchor_id)
        fragment = _fragment_by_anchor_id(ast, anchor_id)
        nucleus_ids = fragment.source_nucleus_ids or tuple(
            dict.fromkeys(
                nucleus_id
                for candidate in ast.source_fragments
                if candidate.fragment_role == "nucleus"
                and candidate.source_slot == fragment.source_slot
                and max(candidate.source_start, fragment.source_start)
                < min(candidate.source_end, fragment.source_end)
                for nucleus_id in candidate.source_nucleus_ids
            )
        )
        self_owner_ids = tuple(
            clause.obligation_id
            for clause in observation_clauses
            if clause.clause_form == "self_denial_boundary"
            and bool(clause.source_nucleus_ids)
            and frozenset(clause.source_nucleus_ids)
            == frozenset(nucleus_ids)
        )
        counter_owner_ids = tuple(
            clause.obligation_id
            for clause in observation_clauses
            if clause.clause_form == "bounded_counterposition"
            and bool(clause.source_nucleus_ids)
            and frozenset(clause.source_nucleus_ids)
            == frozenset(nucleus_ids)
        )
        if len(self_owner_ids) != 1 or len(counter_owner_ids) > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_SELF_DENIAL_PAIR_OWNERSHIP_INVALID"
            )
        owner_count = visible_literal_owner_count(anchor_id)
        if owner_count == 0:
            raise Step11NaturalSurfaceError(
                "STEP11_SELF_DENIAL_ANTECEDENT_OWNER_MISSING"
            )
        if owner_count > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_SELF_DENIAL_ANTECEDENT_OWNER_AMBIGUOUS"
            )
        lines.append(
            _Step11OwnedObservationLine(
                text=_pick_variant(
                    forms["self_denial_anaphora"],
                    fingerprint=ast.current_input_projection_sha256,
                    form_id=f"self_denial_anaphora:{anchor_id}",
                ),
                owned_anchor_ids=equivalent_anchor_ids(anchor_id),
                owned_nucleus_ids=nucleus_ids,
                owned_relation_ids=(),
                owned_obligation_ids=self_owner_ids,
                owned_mixed_emotion_requirement_ids=(),
                literal_anchor_ids=(),
                required_relation_ids=(),
                used_reference_ordinals=(),
            )
        )
        if counter_owner_ids:
            lines.append(
                _Step11OwnedObservationLine(
                    text=_pick_variant(
                        forms["bounded_counter_anaphora"],
                        fingerprint=ast.current_input_projection_sha256,
                        form_id=(
                            "bounded_counter_anaphora:"
                            f"{anchor_id}"
                        ),
                    ),
                    owned_anchor_ids=equivalent_anchor_ids(anchor_id),
                    owned_nucleus_ids=nucleus_ids,
                    owned_relation_ids=(),
                    owned_obligation_ids=counter_owner_ids,
                    owned_mixed_emotion_requirement_ids=(),
                    literal_anchor_ids=(),
                    required_relation_ids=(),
                    used_reference_ordinals=(),
                )
            )

    def unknown_has_unique_semantic_owner(
        anchor_id: str,
    ) -> bool:
        unknowns = unknown_by_anchor.get(anchor_id, ())
        return bool(unknowns) and all(
            len(relation_antecedent_owners(unknown)) == 1
            or visible_literal_owner_count(
                anchor_id,
                target_nucleus_ids=unknown.target_nucleus_ids,
            )
            == 1
            for unknown in unknowns
        )

    # Preserve every active exact nucleus or label through an internally
    # owned line.  A standalone unknown or self-evaluation span also needs
    # one literal source owner before its boundary is stated anaphorically.
    # Overlapping boundary spans reuse the already-visible owner instead of
    # replaying a subspan.  No slot-level source substitution is permitted.
    for fragment in ast.source_fragments:
        if (
            fragment.fragment_role
            not in {"nucleus", "label", "unknown", "self_evaluation"}
            or fragment.source_anchor_id in covered_anchor_ids
            or (
                fragment.fragment_role == "unknown"
                and unknown_has_unique_semantic_owner(
                    fragment.source_anchor_id
                )
            )
            or (
                fragment.fragment_role in {"unknown", "self_evaluation"}
                and visible_literal_owner_count(
                    fragment.source_anchor_id
                )
                != 0
            )
        ):
            continue
        equivalent_ids = equivalent_anchor_ids(fragment.source_anchor_id)
        is_reference_owner = any(
            fragment.source_anchor_id in reference.source_anchor_ids
            for reference in ast.nucleus_surface_references
        )
        reference = (
            _reference_for_anchor(ast, fragment.source_anchor_id)
            if is_reference_owner
            else None
        )
        if reference is not None:
            text = _direct_introduction_line(fragment, ast=ast)
        else:
            rule = _observation_rule(fragment, ast=ast)
            text = (
                f"{rule['prefix']}{_quoted(fragment.text)}"
                f"{rule['suffix']}"
            )
        lines.append(
            _Step11OwnedObservationLine(
                text=text,
                owned_anchor_ids=equivalent_ids,
                owned_nucleus_ids=fragment.source_nucleus_ids,
                owned_relation_ids=(),
                owned_obligation_ids=claim_basic_obligations(
                    fragment.source_nucleus_ids
                ),
                owned_mixed_emotion_requirement_ids=(),
                literal_anchor_ids=equivalent_ids,
                required_relation_ids=(),
                used_reference_ordinals=(
                    (reference.reference_ordinal,)
                    if reference is not None
                    else ()
                ),
            )
        )
        covered_anchor_ids.update(equivalent_ids)

    # Each typed unknown is realised exactly once by its overlay-owned anchor.
    for _anchor_id, unknowns in unknown_by_anchor.items():
        for unknown in unknowns:
            append_unknown(unknown)

    for anchor_id in ast.self_denial_source_anchor_ids:
        append_self_denial(anchor_id)
    result = tuple(lines)
    if not result or any(not row.text for row in result):
        raise Step11NaturalSurfaceError(
            "STEP11_OBSERVATION_OWNED_LINE_INVALID"
        )
    for clause in observation_clauses:
        owner_count = sum(
            clause.obligation_id in row.owned_obligation_ids
            for row in result
        )
        if owner_count == 0:
            raise Step11NaturalSurfaceError(
                "STEP11_OBSERVATION_OBLIGATION_OWNER_MISSING"
            )
        if owner_count > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_OBSERVATION_OBLIGATION_OWNER_AMBIGUOUS"
            )
    for left_index, left in enumerate(result):
        for right in result[left_index + 1 :]:
            overlaps = any(
                anchors_overlap(left_anchor_id, right_anchor_id)
                for left_anchor_id in left.literal_anchor_ids
                for right_anchor_id in right.literal_anchor_ids
            )
            if not overlaps:
                continue
            raise Step11NaturalSurfaceError(
                "STEP11_OVERLAPPING_LITERAL_REPLAY_FORBIDDEN"
            )
    return result


_ACTION_ONGOING_RE = re.compile(
    r"(?:て|で)(?:いる|います)(?:[。！？!?]|$)"
)


def _reception_action_status(
    action_fragments: Sequence[Step11SourceFragment],
) -> str:
    if not action_fragments:
        return "undetermined"
    statuses = {
        row.realization_status
        for row in action_fragments
        if row.realization_status
        in {
            "undetermined",
            "intended",
            "reported_ongoing",
            "reported_not_completed",
            "reported_completed",
        }
    }
    if statuses == {"undetermined"} and any(
        _ACTION_ONGOING_RE.search(row.text) is not None
        for row in action_fragments
    ):
        return "reported_ongoing"
    return next(iter(statuses)) if len(statuses) == 1 else "undetermined"


def _reception_relation_action_status(
    action_fragments: Sequence[Step11SourceFragment],
) -> str:
    """Keep lifecycle claims local when a relation has mixed endpoints."""

    if not action_fragments:
        return "status_neutral"
    statuses = {
        row.realization_status
        for row in action_fragments
        if row.realization_status
        in {
            "undetermined",
            "intended",
            "reported_ongoing",
            "reported_not_completed",
            "reported_completed",
        }
    }
    if len(statuses) != 1:
        return "status_neutral"
    return _reception_action_status(action_fragments)


def _reception_lines(
    ast: Step11NaturalSurfaceAst,
    *,
    observation_lines: Sequence[_Step11OwnedObservationLine],
) -> tuple[_Step11OwnedReceptionLine, ...]:
    reception_clauses = tuple(
        clause
        for sentence in ast.sentences
        if sentence.section_role == "reception"
        for clause in sentence.clauses
        if clause.clause_form == "bound_reception"
        and clause.reception_act is not None
    )
    if not reception_clauses:
        raise Step11NaturalSurfaceError(
            "STEP11_BOUND_RECEPTION_CARDINALITY_INVALID"
        )
    reception_group_by_obligation = {
        clause.obligation_id: sentence.discourse_sentence_group_id
        for sentence in ast.sentences
        if sentence.section_role == "reception"
        for clause in sentence.clauses
    }
    binding_by_obligation = {
        row.reception_obligation_id: row
        for row in ast.reception_antecedent_bindings
    }
    if (
        len(binding_by_obligation) != len(ast.reception_antecedent_bindings)
        or set(binding_by_obligation)
        != {row.obligation_id for row in reception_clauses}
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RECEPTION_BINDING_CARDINALITY_INVALID"
        )
    forms = STEP11_SURFACE_CATALOG["reception_forms"]
    typed_grammar = forms["typed_reference_grammar"]

    def references_for_nuclei(
        nucleus_ids: Sequence[str],
    ) -> tuple[Step11NucleusSurfaceReference, ...]:
        wanted = frozenset(nucleus_ids)
        rows = tuple(
            sorted(
                (
                    row
                    for row in ast.nucleus_surface_references
                    if set(row.nucleus_ids) & wanted
                ),
                key=lambda row: row.reference_ordinal,
            )
        )
        covered = {
            nucleus_id
            for row in rows
            for nucleus_id in row.nucleus_ids
            if nucleus_id in wanted
        }
        if not wanted or covered != set(wanted):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_VISIBLE_REFERENCE_UNRESOLVED"
            )
        return rows

    def reference_token(row: Step11NucleusSurfaceReference) -> str:
        # The typed content forms own the visible delimiters.  Supplying the
        # wrapper here would render ``〔〔…〕〕`` and would make the independent
        # parser disagree with the catalog grammar.
        return _endpoint_reference_token(
            row.reference_ordinal, row.endpoint_role
        )

    lines: list[_Step11OwnedReceptionLine] = []
    line_index_by_contract: dict[tuple[Any, ...], int] = {}
    line_index_by_family: dict[tuple[Any, ...], int | None] = {}
    for clause in reception_clauses:
        binding = binding_by_obligation[clause.obligation_id]
        reception_group_id = reception_group_by_obligation.get(
            clause.obligation_id
        )
        if reception_group_id is None:
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_SENTENCE_GROUP_UNRESOLVED"
            )
        if (
            binding.reception_node_id != clause.discourse_node_id
            or binding.source_target_obligation_ids
            != clause.target_obligation_ids
            or clause.reception_act not in binding.allowed_response_acts
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_BINDING_MISMATCH"
            )
        antecedent_indices: list[int] = []
        for obligation_id in binding.antecedent_obligation_ids:
            owners = tuple(
                index
                for index, line in enumerate(observation_lines)
                if obligation_id in line.owned_obligation_ids
            )
            if len(owners) != 1:
                raise Step11NaturalSurfaceError(
                    "STEP11_RECEPTION_ANTECEDENT_OWNER_INVALID"
                )
            antecedent_indices.extend(owners)
        support_indices: list[int] = []
        for obligation_id in binding.supporting_obligation_ids:
            owners = tuple(
                index
                for index, line in enumerate(observation_lines)
                if obligation_id in line.owned_obligation_ids
            )
            if len(owners) != 1:
                raise Step11NaturalSurfaceError(
                    "STEP11_RECEPTION_SUPPORT_OWNER_INVALID"
                )
            support_indices.extend(owners)
        antecedent_indices = list(dict.fromkeys(antecedent_indices))
        support_indices = list(dict.fromkeys(support_indices))
        if set(antecedent_indices) & set(support_indices):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_SUPPORT_OWNER_OVERLAP"
            )
        antecedent_lines = tuple(
            observation_lines[index] for index in antecedent_indices
        )
        support_lines = tuple(
            observation_lines[index] for index in support_indices
        )
        owned_nucleus_ids = {
            nucleus_id
            for line in antecedent_lines
            for nucleus_id in line.owned_nucleus_ids
        }
        if (
            not binding.antecedent_nucleus_ids
            or not set(binding.antecedent_nucleus_ids) <= owned_nucleus_ids
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_ANTECEDENT_NUCLEUS_OWNER_INVALID"
            )
        support_owned_nucleus_ids = {
            nucleus_id
            for line in support_lines
            for nucleus_id in line.owned_nucleus_ids
        }
        if (
            bool(binding.supporting_nucleus_ids) != bool(support_lines)
            or not set(binding.supporting_nucleus_ids)
            <= support_owned_nucleus_ids
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_SUPPORT_NUCLEUS_OWNER_INVALID"
            )
        target_fragments = tuple(
            row
            for row in ast.source_fragments
            if row.fragment_role in {"nucleus", "label"}
            and set(row.source_nucleus_ids)
            & set(
                (
                    *binding.antecedent_nucleus_ids,
                    *binding.supporting_nucleus_ids,
                )
            )
        )
        action_fragments = tuple(
            row for row in target_fragments if row.source_slot == "action"
        )
        thought_fragments = tuple(
            row for row in target_fragments if row.source_slot == "thought"
        )
        visible_nucleus_ids = frozenset(
            (
                *binding.antecedent_nucleus_ids,
                *binding.supporting_nucleus_ids,
            )
        )
        reception_relation_owner_ids = frozenset(
            (
                *binding.source_target_obligation_ids,
                *binding.antecedent_obligation_ids,
            )
        )
        owned_relations = tuple(
            row
            for row in ast.integrated_relations
            if set(row.owner_obligation_ids)
            & reception_relation_owner_ids
            and frozenset(
                (row.from_nucleus_id, row.to_nucleus_id)
            )
            == visible_nucleus_ids
        )
        if len(owned_relations) > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_RELATION_OWNER_INVALID"
            )
        if owned_relations:
            scope = "relation_action" if action_fragments else "relation"
            status = (
                binding.action_lifecycle
                if binding.action_lifecycle != "not_applicable"
                else _reception_relation_action_status(action_fragments)
                if action_fragments
                else "status_neutral"
            )
        elif thought_fragments and action_fragments:
            scope = "thought_action"
            status = (
                binding.action_lifecycle
                if binding.action_lifecycle != "not_applicable"
                else _reception_action_status(action_fragments)
            )
        elif thought_fragments:
            scope = "thought"
            status = "reported_content"
        elif action_fragments:
            scope = "action"
            status = (
                binding.action_lifecycle
                if binding.action_lifecycle != "not_applicable"
                else _reception_action_status(action_fragments)
            )
        else:
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_ANTECEDENT_SCOPE_UNSUPPORTED"
            )
        antecedent_references = references_for_nuclei(
            binding.antecedent_nucleus_ids
        )
        support_references = (
            references_for_nuclei(binding.supporting_nucleus_ids)
            if binding.supporting_nucleus_ids
            else ()
        )
        visible_references = tuple(
            sorted(
                {
                    row.reference_ordinal: row
                    for row in (
                        *antecedent_references,
                        *support_references,
                    )
                }.values(),
                key=lambda row: row.reference_ordinal,
            )
        )
        reference_by_ordinal = {
            row.reference_ordinal: row
            for row in ast.nucleus_surface_references
        }
        placeholders: dict[str, str] = {}
        if scope in {"relation", "relation_action"}:
            if len(owned_relations) != 1:
                raise Step11NaturalSurfaceError(
                    "STEP11_RECEPTION_RELATION_OWNER_INVALID"
                )
            relation = owned_relations[0]
            from_reference = reference_by_ordinal.get(
                relation.from_reference_ordinal
            )
            to_reference = reference_by_ordinal.get(
                relation.to_reference_ordinal
            )
            if (
                from_reference is None
                or to_reference is None
                or from_reference not in visible_references
                or to_reference not in visible_references
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RECEPTION_RELATION_REFERENCE_INVALID"
                )
            placeholders.update(
                {
                    "from_ref": reference_token(from_reference),
                    "to_ref": reference_token(to_reference),
                }
            )
        else:
            thought_references = tuple(
                row
                for row in visible_references
                if row.source_slot == "thought"
            )
            if scope in {"thought", "thought_action"}:
                if len(thought_references) != 1:
                    raise Step11NaturalSurfaceError(
                        "STEP11_RECEPTION_THOUGHT_REFERENCE_INVALID"
                    )
                placeholders["thought_ref"] = reference_token(
                    thought_references[0]
                )
        if scope in {"action", "thought_action", "relation_action"}:
            action_references = tuple(
                row
                for row in visible_references
                if row.source_slot == "action"
            )
            if len(action_references) != 1:
                raise Step11NaturalSurfaceError(
                    "STEP11_RECEPTION_ACTION_REFERENCE_INVALID"
                )
            placeholders["action_ref"] = reference_token(
                action_references[0]
            )
        canonical_contract = (
            reception_group_id,
            clause.reception_act,
            scope,
            status,
            tuple(row.reference_ordinal for row in visible_references),
            binding.antecedent_obligation_ids,
            binding.antecedent_node_ids,
            binding.antecedent_nucleus_ids,
            binding.supporting_obligation_ids,
            binding.supporting_node_ids,
            binding.supporting_nucleus_ids,
            tuple((*antecedent_indices, *support_indices)),
        )
        family_contract = (
            reception_group_id,
            clause.reception_act,
            binding.source_target_obligation_ids,
        )
        existing_index = line_index_by_contract.get(canonical_contract)
        if existing_index is not None:
            existing = lines[existing_index]
            if (
                binding.binding_id in existing.binding_ids
                or clause.obligation_id
                in existing.reception_obligation_ids
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RECEPTION_CANONICAL_OWNER_DUPLICATE"
                )
            lines[existing_index] = _Step11OwnedReceptionLine(
                text=existing.text,
                binding_ids=(*existing.binding_ids, binding.binding_id),
                reception_obligation_ids=(
                    *existing.reception_obligation_ids,
                    clause.obligation_id,
                ),
                antecedent_obligation_ids=(
                    existing.antecedent_obligation_ids
                ),
                supporting_obligation_ids=(
                    existing.supporting_obligation_ids
                ),
                visible_reference_ordinals=(
                    existing.visible_reference_ordinals
                ),
                antecedent_observation_line_indices=(
                    existing.antecedent_observation_line_indices
                ),
            )
            continue
        canonical_contract_id = artifact_sha256(
            {
                "reception_act": clause.reception_act,
                "scope": scope,
                "status": status,
                "antecedent_obligation_ids": list(
                    binding.antecedent_obligation_ids
                ),
                "antecedent_node_ids": list(binding.antecedent_node_ids),
                "antecedent_nucleus_ids": list(
                    binding.antecedent_nucleus_ids
                ),
                "supporting_obligation_ids": list(
                    binding.supporting_obligation_ids
                ),
                "supporting_node_ids": list(binding.supporting_node_ids),
                "supporting_nucleus_ids": list(
                    binding.supporting_nucleus_ids
                ),
                "visible_reference_ordinals": [
                    row.reference_ordinal for row in visible_references
                ],
            }
        )[:16]
        content = _pick_variant(
            typed_grammar["content_forms"][scope][status],
            fingerprint=ast.current_input_projection_sha256,
            form_id=(
                f"reception_typed_content:{canonical_contract_id}:"
                f"{clause.reception_act}:{scope}:{status}"
            ),
        ).format(**placeholders)
        predicate = _pick_variant(
            forms["act_predicates"][clause.reception_act],
            fingerprint=ast.current_input_projection_sha256,
            form_id=(
                f"reception_predicate:{canonical_contract_id}:"
                f"{clause.reception_act}:{scope}:{status}"
            ),
        )
        sentence_template = _pick_variant(
            forms["sentence_templates"],
            fingerprint=ast.current_input_projection_sha256,
            form_id=(
                f"reception_sentence:{canonical_contract_id}:"
                f"{clause.reception_act}:{scope}:{status}"
            ),
        )
        text = sentence_template.format(content=content, predicate=predicate)
        quote_tokens = tuple(
            token
            for pair in STEP11_SURFACE_CATALOG["layout"]["quote_pairs"]
            for token in (pair["open"], pair["close"])
        )
        if any(token in text for token in quote_tokens):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_LITERAL_FORBIDDEN"
            )
        new_line = _Step11OwnedReceptionLine(
            text=text,
            binding_ids=(binding.binding_id,),
            reception_obligation_ids=(clause.obligation_id,),
            antecedent_obligation_ids=binding.antecedent_obligation_ids,
            supporting_obligation_ids=(
                binding.supporting_obligation_ids
            ),
            visible_reference_ordinals=tuple(
                row.reference_ordinal for row in visible_references
            ),
            antecedent_observation_line_indices=tuple(
                (*antecedent_indices, *support_indices)
            ),
        )
        family_index = line_index_by_family.get(family_contract)
        if type(family_index) is int:
            existing = lines[family_index]
            existing_references = frozenset(
                existing.visible_reference_ordinals
            )
            new_references = frozenset(
                new_line.visible_reference_ordinals
            )
            comparable = (
                existing_references < new_references
                or new_references < existing_references
                or (
                    existing_references == new_references
                    and existing.text == new_line.text
                )
            )
            if comparable:
                dominant = (
                    new_line
                    if existing_references < new_references
                    else existing
                )
                lines[family_index] = _Step11OwnedReceptionLine(
                    text=dominant.text,
                    binding_ids=tuple(
                        dict.fromkeys(
                            (*existing.binding_ids, *new_line.binding_ids)
                        )
                    ),
                    reception_obligation_ids=tuple(
                        dict.fromkeys(
                            (
                                *existing.reception_obligation_ids,
                                *new_line.reception_obligation_ids,
                            )
                        )
                    ),
                    antecedent_obligation_ids=tuple(
                        dict.fromkeys(
                            (
                                *existing.antecedent_obligation_ids,
                                *new_line.antecedent_obligation_ids,
                            )
                        )
                    ),
                    supporting_obligation_ids=tuple(
                        dict.fromkeys(
                            (
                                *existing.supporting_obligation_ids,
                                *new_line.supporting_obligation_ids,
                            )
                        )
                    ),
                    visible_reference_ordinals=(
                        dominant.visible_reference_ordinals
                    ),
                    antecedent_observation_line_indices=tuple(
                        dict.fromkeys(
                            (
                                *existing.antecedent_observation_line_indices,
                                *new_line.antecedent_observation_line_indices,
                            )
                        )
                    ),
                )
                line_index_by_contract[canonical_contract] = family_index
                continue
            # Incomparable local-referent sets are distinct receptions even
            # when their legacy target lineage is shared.
            line_index_by_family[family_contract] = None
        lines.append(new_line)
        new_index = len(lines) - 1
        line_index_by_contract[canonical_contract] = new_index
        if family_contract not in line_index_by_family:
            line_index_by_family[family_contract] = new_index
    flattened_binding_ids = tuple(
        binding_id for line in lines for binding_id in line.binding_ids
    )
    flattened_obligation_ids = tuple(
        obligation_id
        for line in lines
        for obligation_id in line.reception_obligation_ids
    )
    if (
        len(flattened_binding_ids) != len(set(flattened_binding_ids))
        or set(flattened_binding_ids)
        != {row.binding_id for row in binding_by_obligation.values()}
        or len(flattened_obligation_ids)
        != len(set(flattened_obligation_ids))
        or set(flattened_obligation_ids) != set(binding_by_obligation)
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RECEPTION_CANONICAL_OWNER_CARDINALITY_INVALID"
        )
    return tuple(lines)


def _separator_occurs_outside_quotes(value: str, separator: str) -> bool:
    pairs = tuple(
        (row["open"], row["close"])
        for row in STEP11_SURFACE_CATALOG["layout"]["quote_pairs"]
    )
    active_close: str | None = None
    escaped = False
    index = 0
    while index < len(value):
        char = value[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if active_close is not None:
            if value.startswith(active_close, index):
                index += len(active_close)
                active_close = None
            else:
                index += 1
            continue
        opening = next(
            (
                (open_token, close_token)
                for open_token, close_token in pairs
                if value.startswith(open_token, index)
            ),
            None,
        )
        if opening is not None:
            active_close = opening[1]
            index += len(opening[0])
            continue
        if value.startswith(separator, index):
            return True
        index += 1
    if active_close is not None or escaped:
        raise Step11NaturalSurfaceError(
            "STEP11_GROUP_QUOTE_STATE_INVALID"
        )
    return False


def _group_clause_stem(value: str) -> str:
    grammar = STEP11_SURFACE_CATALOG["group_grammar"]
    suffix = grammar["sentence_suffix"]
    separator = grammar["clause_separator"]
    stem = value[: -len(suffix)] if value.endswith(suffix) else value
    if (
        not stem
        or stem.endswith(("。", "！", "？", "!", "?"))
        or _separator_occurs_outside_quotes(stem, separator)
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_GROUP_CLAUSE_STEM_INVALID"
        )
    return stem


def _join_group_clauses(
    values: Sequence[str],
    *,
    grammatical_chunk_ordinals: Sequence[int],
) -> str:
    if not values or len(values) != len(grammatical_chunk_ordinals):
        raise Step11NaturalSurfaceError(
            "STEP11_GROUP_CLAUSE_REQUIRED"
        )
    grammar = STEP11_SURFACE_CATALOG["group_grammar"]
    ordinals = tuple(grammatical_chunk_ordinals)
    if (
        any(type(value) is not int or value < 1 for value in ordinals)
        or ordinals != tuple(sorted(ordinals))
        or set(ordinals) != set(range(1, max(ordinals) + 1))
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_GROUP_GRAMMATICAL_CHUNK_INVALID"
        )
    chunks = tuple(
        tuple(
            _group_clause_stem(value)
            for value, assigned in zip(values, ordinals)
            if assigned == chunk_ordinal
        )
        for chunk_ordinal in range(1, max(ordinals) + 1)
    )
    maximum_clauses = grammar[
        "maximum_visible_clauses_per_grammatical_sentence"
    ]
    joiner_count = sum(max(0, len(chunk) - 1) for chunk in chunks)
    if (
        any(not chunk or len(chunk) > maximum_clauses for chunk in chunks)
        or joiner_count > grammar["maximum_repeated_joiner_per_group"]
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_GROUP_GRAMMATICAL_CHUNK_INVALID"
        )
    return (
        grammar["grammatical_chunk_separator"].join(
            grammar["clause_separator"].join(chunk) for chunk in chunks
        )
        + grammar["sentence_suffix"]
    )


def _coalesce_observation_lines(
    lines: Sequence[_Step11OwnedObservationLine],
) -> tuple[_Step11OwnedObservationLine, ...]:
    result: list[_Step11OwnedObservationLine] = []
    index_by_key: dict[tuple[Any, ...], int] = {}
    for line in lines:
        key = (
            line.text,
            line.owned_anchor_ids,
            line.owned_nucleus_ids,
            line.literal_anchor_ids,
            line.used_reference_ordinals,
        )
        existing_index = index_by_key.get(key)
        if existing_index is None:
            index_by_key[key] = len(result)
            result.append(line)
            continue
        existing = result[existing_index]
        result[existing_index] = _Step11OwnedObservationLine(
            text=existing.text,
            owned_anchor_ids=existing.owned_anchor_ids,
            owned_nucleus_ids=existing.owned_nucleus_ids,
            owned_relation_ids=tuple(
                dict.fromkeys(
                    (*existing.owned_relation_ids, *line.owned_relation_ids)
                )
            ),
            owned_obligation_ids=tuple(
                dict.fromkeys(
                    (
                        *existing.owned_obligation_ids,
                        *line.owned_obligation_ids,
                    )
                )
            ),
            owned_mixed_emotion_requirement_ids=tuple(
                dict.fromkeys(
                    (
                        *existing.owned_mixed_emotion_requirement_ids,
                        *line.owned_mixed_emotion_requirement_ids,
                    )
                )
            ),
            literal_anchor_ids=existing.literal_anchor_ids,
            required_relation_ids=tuple(
                dict.fromkeys(
                    (
                        *existing.required_relation_ids,
                        *line.required_relation_ids,
                    )
                )
            ),
            used_reference_ordinals=existing.used_reference_ordinals,
        )
    return tuple(result)


def _derive_surface_realization_plan(
    ast: Step11NaturalSurfaceAst,
    observation_lines: Sequence[_Step11OwnedObservationLine],
    reception_lines: Sequence[_Step11OwnedReceptionLine],
) -> Step11SurfaceRealizationPlan:
    """Recompute the committed rc0025 plan from semantic ownership only."""

    observation_sentences = tuple(
        row for row in ast.sentences if row.section_role == "observation"
    )
    reception_sentences = tuple(
        row for row in ast.sentences if row.section_role == "reception"
    )
    observation_group_ids = tuple(
        row.discourse_sentence_group_id for row in observation_sentences
    )
    reception_group_ids = tuple(
        row.discourse_sentence_group_id for row in reception_sentences
    )
    observation_group_index = {
        group_id: index for index, group_id in enumerate(observation_group_ids)
    }
    observation_group_by_obligation = {
        clause.obligation_id: sentence.discourse_sentence_group_id
        for sentence in observation_sentences
        for clause in sentence.clauses
    }
    clause_form_by_obligation = {
        clause.obligation_id: clause.clause_form
        for sentence in observation_sentences
        for clause in sentence.clauses
    }
    reference_by_anchor = {
        anchor_id: reference
        for reference in ast.nucleus_surface_references
        for anchor_id in reference.source_anchor_ids
    }

    def observation_lineage(
        line: _Step11OwnedObservationLine,
    ) -> tuple[str, ...]:
        groups = {
            observation_group_by_obligation[obligation_id]
            for obligation_id in line.owned_obligation_ids
            if obligation_id in observation_group_by_obligation
        }
        groups.update(
            reference_by_anchor[anchor_id].introduction_sentence_group_id
            for anchor_id in line.owned_anchor_ids
            if anchor_id in reference_by_anchor
        )
        if not groups:
            groups.update(
                sentence.discourse_sentence_group_id
                for sentence in observation_sentences
                if any(
                    set(clause.source_nucleus_ids)
                    & set(line.owned_nucleus_ids)
                    for clause in sentence.clauses
                )
            )
        if not groups:
            raise Step11NaturalSurfaceError(
                "STEP11_AUXILIARY_CLAUSE_GROUP_UNRESOLVED"
            )
        return tuple(
            sorted(groups, key=observation_group_index.__getitem__)
        )

    def observation_phase(line: _Step11OwnedObservationLine) -> str:
        if line.literal_anchor_ids:
            return "source_introduction"
        if line.owned_relation_ids or line.owned_mixed_emotion_requirement_ids:
            return "relation"
        forms = {
            clause_form_by_obligation[obligation_id]
            for obligation_id in line.owned_obligation_ids
            if obligation_id in clause_form_by_obligation
        }
        if "bounded_counterposition" in forms:
            return "bounded_counterposition"
        if "self_denial_boundary" in forms:
            return "self_denial_boundary"
        if "unknown_boundary" in forms:
            return "unknown_boundary"
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_PHASE_UNRESOLVED"
        )

    def reference_ordinals(anchor_ids: Sequence[str]) -> tuple[int, ...]:
        return tuple(
            sorted(
                {
                    reference_by_anchor[anchor_id].reference_ordinal
                    for anchor_id in anchor_ids
                    if anchor_id in reference_by_anchor
                }
            )
        )

    observation_rows = []
    for original_index, line in enumerate(
        _coalesce_observation_lines(observation_lines)
    ):
        row_phase = observation_phase(line)
        used = tuple(line.used_reference_ordinals)
        introduced = tuple(
            ordinal
            for ordinal in reference_ordinals(line.literal_anchor_ids)
            if ordinal in set(used)
        )
        required = tuple(
            ordinal for ordinal in used if ordinal not in set(introduced)
        )
        lineage = observation_lineage(line)
        observation_rows.append(
            (
                (
                    _SURFACE_PHASE_ORDER[row_phase],
                    min(introduced or used or (10**6,)),
                    min(
                        observation_group_index[group_id]
                        for group_id in lineage
                    ),
                    original_index,
                ),
                line,
                row_phase,
                lineage,
                introduced,
                used,
                required,
            )
        )
    observation_rows.sort(key=lambda row: row[0])
    units: list[Step11SurfaceRealizationUnit] = []
    for source_order, (
        _sort_key,
        line,
        row_phase,
        lineage,
        introduced,
        used,
        required,
    ) in enumerate(observation_rows):
        material = {
            "section_role": "observation",
            "phase": row_phase,
            "owner_obligation_ids": list(line.owned_obligation_ids),
            "owner_anchor_ids": list(line.owned_anchor_ids),
            "owner_nucleus_ids": list(line.owned_nucleus_ids),
            "owner_relation_ids": list(line.owned_relation_ids),
            "owner_mixed_emotion_requirement_ids": list(
                line.owned_mixed_emotion_requirement_ids
            ),
            "introduced_reference_ordinals": list(introduced),
            "used_reference_ordinals": list(used),
            "required_reference_ordinals": list(required),
            "visible_reference_count": len(used),
            "body_free_complexity_weight": max(1, len(used)),
            "parent_sentence_group_ids": list(lineage),
            "source_order": source_order,
        }
        units.append(
            Step11SurfaceRealizationUnit(
                semantic_unit_id=(
                    "nls3s11unit_" + artifact_sha256(material)[:16]
                ),
                section_role="observation",
                phase=row_phase,
                owner_obligation_ids=line.owned_obligation_ids,
                owner_anchor_ids=line.owned_anchor_ids,
                owner_nucleus_ids=line.owned_nucleus_ids,
                owner_relation_ids=line.owned_relation_ids,
                owner_mixed_emotion_requirement_ids=(
                    line.owned_mixed_emotion_requirement_ids
                ),
                introduced_reference_ordinals=introduced,
                used_reference_ordinals=used,
                required_reference_ordinals=required,
                visible_reference_count=len(used),
                body_free_complexity_weight=max(1, len(used)),
                parent_sentence_group_ids=lineage,
                assigned_sentence_group_id="",
                assigned_grammatical_chunk_ordinal=0,
                source_order=source_order,
            )
        )

    reception_group_by_obligation = {
        clause.obligation_id: sentence.discourse_sentence_group_id
        for sentence in reception_sentences
        for clause in sentence.clauses
    }
    reception_group_index = {
        group_id: index for index, group_id in enumerate(reception_group_ids)
    }
    reception_rows = []
    for original_index, line in enumerate(reception_lines):
        groups = {
            reception_group_by_obligation[obligation_id]
            for obligation_id in line.reception_obligation_ids
            if obligation_id in reception_group_by_obligation
        }
        if len(groups) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_CLAUSE_GROUP_OWNERSHIP_INVALID"
            )
        lineage = tuple(groups)
        reception_rows.append(
            (
                (
                    reception_group_index[lineage[0]],
                    original_index,
                ),
                line,
                lineage,
            )
        )
    reception_rows.sort(key=lambda row: row[0])
    for reception_index, (_sort_key, line, lineage) in enumerate(
        reception_rows,
        start=len(units),
    ):
        material = {
            "section_role": "reception",
            "phase": "reception",
            "owner_obligation_ids": list(line.reception_obligation_ids),
            "antecedent_obligation_ids": list(
                line.antecedent_obligation_ids
            ),
            "supporting_obligation_ids": list(
                line.supporting_obligation_ids
            ),
            "binding_ids": list(line.binding_ids),
            "introduced_reference_ordinals": [],
            "used_reference_ordinals": list(
                line.visible_reference_ordinals
            ),
            "required_reference_ordinals": list(
                line.visible_reference_ordinals
            ),
            "visible_reference_count": len(
                line.visible_reference_ordinals
            ),
            "body_free_complexity_weight": max(
                1, len(line.visible_reference_ordinals)
            ),
            "parent_sentence_group_ids": list(lineage),
            "source_order": reception_index,
        }
        units.append(
            Step11SurfaceRealizationUnit(
                semantic_unit_id=(
                    "nls3s11unit_" + artifact_sha256(material)[:16]
                ),
                section_role="reception",
                phase="reception",
                owner_obligation_ids=line.reception_obligation_ids,
                owner_anchor_ids=(),
                owner_nucleus_ids=(),
                owner_relation_ids=(),
                owner_mixed_emotion_requirement_ids=(),
                introduced_reference_ordinals=(),
                used_reference_ordinals=line.visible_reference_ordinals,
                required_reference_ordinals=(
                    line.visible_reference_ordinals
                ),
                visible_reference_count=len(
                    line.visible_reference_ordinals
                ),
                body_free_complexity_weight=max(
                    1, len(line.visible_reference_ordinals)
                ),
                parent_sentence_group_ids=lineage,
                assigned_sentence_group_id="",
                assigned_grammatical_chunk_ordinal=0,
                source_order=reception_index,
            )
        )
    return build_step11_surface_realization_plan(
        tuple(units),
        observation_group_ids=observation_group_ids,
        reception_group_ids=reception_group_ids,
    )


def _observation_sentence_lines(
    ast: Step11NaturalSurfaceAst,
    atomic_lines: Sequence[_Step11OwnedObservationLine],
) -> tuple[_Step11OwnedSentenceLine, ...]:
    """Balance source-owned units without changing their semantic order."""

    sentences = tuple(
        row for row in ast.sentences if row.section_role == "observation"
    )
    group_by_obligation = {
        clause.obligation_id: sentence.discourse_sentence_group_id
        for sentence in sentences
        for clause in sentence.clauses
    }
    clause_form_by_obligation = {
        clause.obligation_id: clause.clause_form
        for sentence in sentences
        for clause in sentence.clauses
    }
    group_index = {
        sentence.discourse_sentence_group_id: index
        for index, sentence in enumerate(sentences)
    }
    reference_by_anchor = {
        anchor_id: reference
        for reference in ast.nucleus_surface_references
        for anchor_id in reference.source_anchor_ids
    }
    coalesced = _coalesce_observation_lines(atomic_lines)

    def parent_groups(
        line: _Step11OwnedObservationLine,
    ) -> tuple[str, ...]:
        owned_groups = {
            group_by_obligation[obligation_id]
            for obligation_id in line.owned_obligation_ids
            if obligation_id in group_by_obligation
        }
        owned_groups.update(
            reference_by_anchor[anchor_id].introduction_sentence_group_id
            for anchor_id in line.owned_anchor_ids
            if anchor_id in reference_by_anchor
        )
        if not owned_groups:
            owned_groups = {
                sentence.discourse_sentence_group_id
                for sentence in sentences
                if any(
                    set(clause.source_nucleus_ids)
                    & set(line.owned_nucleus_ids)
                    for clause in sentence.clauses
                )
            }
        if not owned_groups:
            raise Step11NaturalSurfaceError(
                "STEP11_AUXILIARY_CLAUSE_GROUP_UNRESOLVED"
            )
        return tuple(sorted(owned_groups, key=group_index.__getitem__))

    def phase(line: _Step11OwnedObservationLine) -> str:
        if line.literal_anchor_ids:
            return "source_introduction"
        if line.owned_relation_ids or line.owned_mixed_emotion_requirement_ids:
            return "relation"
        forms = {
            clause_form_by_obligation[obligation_id]
            for obligation_id in line.owned_obligation_ids
            if obligation_id in clause_form_by_obligation
        }
        if "bounded_counterposition" in forms:
            return "bounded_counterposition"
        if "self_denial_boundary" in forms:
            return "self_denial_boundary"
        if "unknown_boundary" in forms:
            return "unknown_boundary"
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_PHASE_UNRESOLVED"
        )

    def reference_ordinals(anchor_ids: Sequence[str]) -> tuple[int, ...]:
        return tuple(
            sorted(
                {
                    reference_by_anchor[anchor_id].reference_ordinal
                    for anchor_id in anchor_ids
                    if anchor_id in reference_by_anchor
                }
            )
        )

    sortable: list[tuple[Any, ...]] = []
    for original_index, line in enumerate(coalesced):
        row_phase = phase(line)
        used = tuple(line.used_reference_ordinals)
        introduced = tuple(
            ordinal
            for ordinal in reference_ordinals(line.literal_anchor_ids)
            if ordinal in set(used)
        )
        required = tuple(
            ordinal for ordinal in used if ordinal not in set(introduced)
        )
        lineage = parent_groups(line)
        sortable.append(
            (
                (
                    _SURFACE_PHASE_ORDER[row_phase],
                    min(introduced or used or (10**6,)),
                    min(group_index[row] for row in lineage),
                    original_index,
                ),
                line,
                row_phase,
                lineage,
                introduced,
                used,
                required,
            )
        )
    sortable.sort(key=lambda row: row[0])
    units: list[Step11SurfaceRealizationUnit] = []
    line_by_unit_id: dict[str, _Step11OwnedObservationLine] = {}
    for source_order, (
        _sort_key,
        line,
        row_phase,
        lineage,
        introduced,
        used,
        required,
    ) in enumerate(sortable):
        material = {
            "section_role": "observation",
            "phase": row_phase,
            "owner_obligation_ids": list(line.owned_obligation_ids),
            "owner_anchor_ids": list(line.owned_anchor_ids),
            "owner_nucleus_ids": list(line.owned_nucleus_ids),
            "owner_relation_ids": list(line.owned_relation_ids),
            "owner_mixed_emotion_requirement_ids": list(
                line.owned_mixed_emotion_requirement_ids
            ),
            "introduced_reference_ordinals": list(introduced),
            "used_reference_ordinals": list(used),
            "required_reference_ordinals": list(required),
            "visible_reference_count": len(used),
            "body_free_complexity_weight": max(1, len(used)),
            "parent_sentence_group_ids": list(lineage),
            "source_order": source_order,
        }
        unit_id = "nls3s11unit_" + artifact_sha256(material)[:16]
        unit = Step11SurfaceRealizationUnit(
            semantic_unit_id=unit_id,
            section_role="observation",
            phase=row_phase,
            owner_obligation_ids=line.owned_obligation_ids,
            owner_anchor_ids=line.owned_anchor_ids,
            owner_nucleus_ids=line.owned_nucleus_ids,
            owner_relation_ids=line.owned_relation_ids,
            owner_mixed_emotion_requirement_ids=(
                line.owned_mixed_emotion_requirement_ids
            ),
            introduced_reference_ordinals=introduced,
            used_reference_ordinals=used,
            required_reference_ordinals=required,
            visible_reference_count=len(used),
            body_free_complexity_weight=max(1, len(used)),
            parent_sentence_group_ids=lineage,
            assigned_sentence_group_id="",
            assigned_grammatical_chunk_ordinal=0,
            source_order=source_order,
        )
        units.append(unit)
        line_by_unit_id[unit_id] = line
    plan = build_step11_surface_realization_plan(
        tuple(units),
        observation_group_ids=tuple(group_index),
        reception_group_ids=(),
    )
    if ast.surface_realization_plan is not None:
        committed_units = tuple(
            row
            for row in ast.surface_realization_plan.units
            if row.section_role == "observation"
        )
        if (
            ast.surface_realization_plan.schema_version
            != STEP11_SURFACE_REALIZATION_PLAN_SCHEMA
            or ast.surface_realization_plan.candidate_version_id
            != STEP11_CANDIDATE_VERSION_ID
            or committed_units != plan.units
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_SURFACE_REALIZATION_PLAN_MISMATCH"
            )
        plan_units = committed_units
    else:
        plan_units = plan.units
    assigned: dict[
        str,
        list[tuple[Step11SurfaceRealizationUnit, _Step11OwnedObservationLine]],
    ] = {
        sentence.discourse_sentence_group_id: [] for sentence in sentences
    }
    for unit in plan_units:
        assigned[unit.assigned_sentence_group_id].append(
            (unit, line_by_unit_id[unit.semantic_unit_id])
        )

    introduced_ordinals: set[int] = set()
    result: list[_Step11OwnedSentenceLine] = []
    for sentence in sentences:
        assigned_rows = assigned[sentence.discourse_sentence_group_id]
        if not assigned_rows:
            raise Step11NaturalSurfaceError(
                "STEP11_SENTENCE_GROUP_SURFACE_EMPTY"
            )

        for unit, _row in assigned_rows:
            introduced = set(unit.introduced_reference_ordinals)
            if introduced & introduced_ordinals:
                raise Step11NaturalSurfaceError(
                    "STEP11_NUCLEUS_LITERAL_OWNER_DUPLICATE"
                )
            required = set(unit.required_reference_ordinals)
            if not required <= introduced_ordinals:
                raise Step11NaturalSurfaceError(
                    "STEP11_ENDPOINT_REFERENCE_ORDER_INVALID"
                )
            introduced_ordinals.update(introduced)
        if len(assigned_rows) > plan.maximum_observation_clauses_per_sentence:
            raise Step11NaturalSurfaceError(
                "STEP11_SURFACE_PLAN_DENSITY_INVALID"
            )
        result.append(
            _Step11OwnedSentenceLine(
                discourse_sentence_group_id=(
                    sentence.discourse_sentence_group_id
                ),
                section_role="observation",
                text=_join_group_clauses(
                    [row.text for _unit, row in assigned_rows],
                    grammatical_chunk_ordinals=[
                        unit.assigned_grammatical_chunk_ordinal
                        for unit, _row in assigned_rows
                    ],
                ),
                clause_count=len(assigned_rows),
            )
        )
    if introduced_ordinals != {
        row.reference_ordinal for row in ast.nucleus_surface_references
    }:
        raise Step11NaturalSurfaceError(
            "STEP11_ENDPOINT_REFERENCE_INTRODUCTION_INCOMPLETE"
        )
    return tuple(result)


def _reception_sentence_lines(
    ast: Step11NaturalSurfaceAst,
    atomic_lines: Sequence[_Step11OwnedReceptionLine],
) -> tuple[_Step11OwnedSentenceLine, ...]:
    sentences = tuple(
        row for row in ast.sentences if row.section_role == "reception"
    )
    group_by_obligation = {
        clause.obligation_id: sentence.discourse_sentence_group_id
        for sentence in sentences
        for clause in sentence.clauses
    }
    group_ids = tuple(
        sentence.discourse_sentence_group_id for sentence in sentences
    )
    group_index = {
        group_id: index for index, group_id in enumerate(group_ids)
    }
    assigned: dict[str, list[_Step11OwnedReceptionLine]] = {
        sentence.discourse_sentence_group_id: [] for sentence in sentences
    }
    ordered_rows = []
    for original_index, line in enumerate(atomic_lines):
        groups = {
            group_by_obligation[obligation_id]
            for obligation_id in line.reception_obligation_ids
            if obligation_id in group_by_obligation
        }
        if len(groups) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_CLAUSE_GROUP_OWNERSHIP_INVALID"
            )
        group_id = next(iter(groups))
        ordered_rows.append(
            ((group_index[group_id], original_index), line, (group_id,))
        )
    ordered_rows.sort(key=lambda row: row[0])
    if type(ast.surface_realization_plan) is not Step11SurfaceRealizationPlan:
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_REALIZATION_PLAN_REQUIRED"
        )
    committed = tuple(
        row
        for row in ast.surface_realization_plan.units
        if row.section_role == "reception"
    )
    start_order = len(ast.surface_realization_plan.units) - len(committed)
    line_by_unit_id: dict[str, _Step11OwnedReceptionLine] = {}
    expected_ids: list[str] = []
    for source_order, (_sort_key, line, lineage) in enumerate(
        ordered_rows, start=start_order
    ):
        material = {
            "section_role": "reception",
            "phase": "reception",
            "owner_obligation_ids": list(line.reception_obligation_ids),
            "antecedent_obligation_ids": list(
                line.antecedent_obligation_ids
            ),
            "supporting_obligation_ids": list(
                line.supporting_obligation_ids
            ),
            "binding_ids": list(line.binding_ids),
            "introduced_reference_ordinals": [],
            "used_reference_ordinals": list(
                line.visible_reference_ordinals
            ),
            "required_reference_ordinals": list(
                line.visible_reference_ordinals
            ),
            "visible_reference_count": len(
                line.visible_reference_ordinals
            ),
            "body_free_complexity_weight": max(
                1, len(line.visible_reference_ordinals)
            ),
            "parent_sentence_group_ids": list(lineage),
            "source_order": source_order,
        }
        unit_id = "nls3s11unit_" + artifact_sha256(material)[:16]
        expected_ids.append(unit_id)
        line_by_unit_id[unit_id] = line
    if tuple(row.semantic_unit_id for row in committed) != tuple(
        expected_ids
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_REALIZATION_PLAN_MISMATCH"
        )
    assigned_units_by_group: dict[
        str,
        list[tuple[Step11SurfaceRealizationUnit, _Step11OwnedReceptionLine]],
    ] = {group_id: [] for group_id in group_ids}
    for unit in committed:
        line = line_by_unit_id[unit.semantic_unit_id]
        assigned[unit.assigned_sentence_group_id].append(line)
        assigned_units_by_group[unit.assigned_sentence_group_id].append(
            (unit, line)
        )
    result: list[_Step11OwnedSentenceLine] = []
    for sentence in sentences:
        rows = assigned[sentence.discourse_sentence_group_id]
        assigned_rows = assigned_units_by_group[
            sentence.discourse_sentence_group_id
        ]
        if not rows:
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_SENTENCE_GROUP_SURFACE_EMPTY"
            )
        result.append(
            _Step11OwnedSentenceLine(
                discourse_sentence_group_id=(
                    sentence.discourse_sentence_group_id
                ),
                section_role="reception",
                text=_join_group_clauses(
                    [row.text for _unit, row in assigned_rows],
                    grammatical_chunk_ordinals=[
                        unit.assigned_grammatical_chunk_ordinal
                        for unit, _row in assigned_rows
                    ],
                ),
                clause_count=len(rows),
            )
        )
    return tuple(result)


def render_step11_natural_surface(
    ast: Step11NaturalSurfaceAst,
    *,
    discourse_plan: Mapping[str, Any],
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11CanonicalRenderedSurface:
    issues = validate_step11_surface_ast(
        ast,
        discourse_plan=discourse_plan,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    observation_lines = _additional_observation_lines(ast)
    reception_lines = _reception_lines(
        ast,
        observation_lines=observation_lines,
    )
    observation_sentences = _observation_sentence_lines(
        ast, observation_lines
    )
    reception_sentences = _reception_sentence_lines(ast, reception_lines)
    labels = STEP11_SURFACE_CATALOG["labels"]
    body = (
        labels["observation"]
        + "\n"
        + "\n".join(row.text for row in observation_sentences)
        + "\n\n"
        + labels["reception"]
        + "\n"
        + "\n".join(row.text for row in reception_sentences)
    )
    body = unicodedata.normalize("NFC", body)
    if "\r" in body or body.endswith("\n"):
        raise Step11NaturalSurfaceError("STEP11_CANONICAL_LAYOUT_INVALID")
    utf8_bytes = body.encode("utf-8", errors="strict")
    return Step11CanonicalRenderedSurface(
        schema_version=STEP11_RENDERED_SURFACE_SCHEMA,
        source_surface_ast_sha256=artifact_sha256(
            step11_surface_ast_material(ast)
        ),
        surface_catalog_sha256=STEP11_SURFACE_CATALOG_SHA256,
        utf8_bytes=utf8_bytes,
        sha256=hashlib.sha256(utf8_bytes).hexdigest(),
    )


def validate_step11_surface_ast(
    value: Any,
    *,
    discourse_plan: Mapping[str, Any],
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> tuple[str, ...]:
    issues: set[str] = set(validate_step11_surface_catalog())
    if type(value) is not Step11NaturalSurfaceAst:
        return ("STEP11_SURFACE_AST_TYPE_INVALID",)
    try:
        projection = project_step11_current_input(current_input)
        ledger, _by_id = _trusted_parents(
            inventory_result, content_plan, discourse_plan
        )
        semantic_overlay = build_step11_semantic_overlay(
            current_input,
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plan=discourse_plan,
        )
    except (AttributeError, Step11NaturalSurfaceError, TypeError, ValueError):
        return ("STEP11_SURFACE_AST_PARENT_INVALID",)
    if value.schema_version != STEP11_SURFACE_AST_SCHEMA:
        issues.add("STEP11_SURFACE_AST_SCHEMA_INVALID")
    if value.candidate_version_id != STEP11_CANDIDATE_VERSION_ID:
        issues.add("STEP11_SURFACE_AST_VERSION_INVALID")
    if value.source_obligation_ledger_sha256 != artifact_sha256(ledger):
        issues.add("STEP11_SURFACE_AST_LEDGER_PARENT_MISMATCH")
    if value.source_content_plan_sha256 != artifact_sha256(content_plan):
        issues.add("STEP11_SURFACE_AST_CONTENT_PARENT_MISMATCH")
    if value.source_discourse_plan_sha256 != artifact_sha256(discourse_plan):
        issues.add("STEP11_SURFACE_AST_DISCOURSE_PARENT_MISMATCH")
    if value.source_semantic_overlay_sha256 != artifact_sha256(
        step11_semantic_overlay_material(semantic_overlay)
    ):
        issues.add("STEP11_SURFACE_AST_OVERLAY_PARENT_MISMATCH")
    if value.current_input_projection_sha256 != artifact_sha256(
        _projection_material(projection)
    ):
        issues.add("STEP11_SURFACE_AST_INPUT_PARENT_MISMATCH")
    if value.surface_catalog_sha256 != STEP11_SURFACE_CATALOG_SHA256:
        issues.add("STEP11_SURFACE_AST_CATALOG_MISMATCH")
    if not _AST_ID_RE.fullmatch(value.surface_ast_id):
        issues.add("STEP11_SURFACE_AST_ID_INVALID")
    else:
        expected_id = "nls3s11ast_" + artifact_sha256(
            step11_surface_ast_material(value, include_id=False)
        )[:16]
        if value.surface_ast_id != expected_id:
            issues.add("STEP11_SURFACE_AST_ID_MISMATCH")
    try:
        expected = _build_ast(
            discourse_plan,
            inventory_result=inventory_result,
            content_plan=content_plan,
            projection=projection,
            current_input=current_input,
        )
    except (
        AttributeError,
        IndexError,
        KeyError,
        Step11NaturalSurfaceError,
        TypeError,
        ValueError,
    ):
        issues.add("STEP11_SURFACE_AST_RECOMPUTATION_FAILED")
    else:
        if value != expected:
            issues.add("STEP11_SURFACE_AST_RECOMPUTATION_MISMATCH")
    if not value.sentences or any(
        type(row) is not Step11SurfaceSentence
        or not row.clauses
        or row.section_role not in {"observation", "reception"}
        or any(
            type(clause) is not Step11SurfaceClause
            or clause.clause_form not in _CLAUSE_FORMS
            or clause.section_role != row.section_role
            for clause in row.clauses
        )
        for row in value.sentences
    ):
        issues.add("STEP11_SURFACE_AST_CLOSED_UNION_INVALID")
    fragment_anchor_ids = [
        row.source_anchor_id for row in value.source_fragments
        if type(row) is Step11SourceFragment
    ]
    if (
        len(fragment_anchor_ids) != len(value.source_fragments)
        or len(fragment_anchor_ids) != len(set(fragment_anchor_ids))
        or any(
            type(row) is not Step11SourceFragment
            or row.source_slot not in _SLOT_ORDER
            or row.source_field
            not in _SOURCE_FIELDS_BY_SLOT[row.source_slot]
            or not row.text
            or (
                row.fragment_role == "label"
                and (
                    row.source_slot not in {"emotion", "category"}
                    or row.source_role != row.source_slot
                    or type(row.source_ordinal) is not int
                    or row.source_ordinal < 0
                )
            )
            or (
                row.fragment_role != "label"
                and row.source_ordinal is not None
            )
            for row in value.source_fragments
        )
    ):
        issues.add("STEP11_SURFACE_AST_SOURCE_FRAGMENT_INVALID")
    fragment_anchor_id_set = set(fragment_anchor_ids)
    reference_by_ordinal = {
        row.reference_ordinal: row
        for row in value.nucleus_surface_references
        if type(row) is Step11NucleusSurfaceReference
    }
    sentence_group_ids = {
        row.discourse_sentence_group_id for row in value.sentences
    }
    if (
        len(reference_by_ordinal) != len(value.nucleus_surface_references)
        or tuple(sorted(reference_by_ordinal))
        != tuple(range(1, len(reference_by_ordinal) + 1))
        or len(
            {row.source_identity_key for row in value.nucleus_surface_references}
        )
        != len(value.nucleus_surface_references)
        or any(
            type(row) is not Step11NucleusSurfaceReference
            or row.endpoint_role not in _RELATION_ENDPOINT_ROLES
            or not row.source_anchor_ids
            or not set(row.source_anchor_ids) <= fragment_anchor_id_set
            or not row.nucleus_ids
            or row.introduction_sentence_group_id not in sentence_group_ids
            or not _SHA_RE.fullmatch(row.source_identity_key)
            for row in value.nucleus_surface_references
        )
    ):
        issues.add("STEP11_SURFACE_AST_REFERENCE_REGISTRY_INVALID")
    observation_obligation_ids = {
        clause.obligation_id
        for sentence in value.sentences
        if sentence.section_role == "observation"
        for clause in sentence.clauses
    }
    if any(
        type(row) is not Step11IntegratedRelation
        or len(row.from_source_anchor_ids) != 1
        or len(row.to_source_anchor_ids) != 1
        or row.from_source_anchor_ids == row.to_source_anchor_ids
        or not set(row.from_source_anchor_ids + row.to_source_anchor_ids)
        <= fragment_anchor_id_set
        or not row.from_nucleus_id
        or not row.to_nucleus_id
        or row.from_endpoint_role not in _RELATION_ENDPOINT_ROLES
        or row.to_endpoint_role not in _RELATION_ENDPOINT_ROLES
        or row.from_reference_ordinal not in reference_by_ordinal
        or row.to_reference_ordinal not in reference_by_ordinal
        or row.from_reference_ordinal == row.to_reference_ordinal
        or (
            row.from_reference_ordinal in reference_by_ordinal
            and (
                row.from_nucleus_id
                not in reference_by_ordinal[
                    row.from_reference_ordinal
                ].nucleus_ids
                or row.from_endpoint_role
                != reference_by_ordinal[
                    row.from_reference_ordinal
                ].endpoint_role
            )
        )
        or (
            row.to_reference_ordinal in reference_by_ordinal
            and (
                row.to_nucleus_id
                not in reference_by_ordinal[
                    row.to_reference_ordinal
                ].nucleus_ids
                or row.to_endpoint_role
                != reference_by_ordinal[
                    row.to_reference_ordinal
                ].endpoint_role
            )
        )
        or type(row.required) is not bool
        or not row.owner_obligation_ids
        or not set(row.owner_obligation_ids) <= observation_obligation_ids
        or row.relation_type not in STEP11_SURFACE_CATALOG["relation_types"]
        or row.relation_direction
        not in STEP11_SURFACE_CATALOG["relation_directions"]
        for row in value.integrated_relations
    ):
        issues.add("STEP11_SURFACE_AST_RELATION_BINDING_INVALID")
    if any(
        type(row) is not Step11IntegratedUnknown
        or len(row.source_anchor_ids) != 1
        or not set((*row.source_anchor_ids, *row.context_anchor_ids))
        <= fragment_anchor_id_set
        or row.dimension_code == "choice"
        or row.decision_state not in _UNKNOWN_DECISION_STATES
        or not set(row.owner_obligation_ids) <= observation_obligation_ids
        or (
            "frozen_required_unknown" in row.source_rules
            and not row.owner_obligation_ids
        )
        or (
            row.dimension_code == "decision_state"
            and row.decision_state != "open"
        )
        or (
            row.dimension_code == "post_decision_comparative_merit"
            and row.decision_state != "completed"
        )
        or (
            row.dimension_code
            not in {
                "decision_state",
                "post_decision_comparative_merit",
            }
            and row.decision_state != "not_applicable"
        )
        or not row.surface_policy
        for row in value.integrated_unknowns
    ):
        issues.add("STEP11_SURFACE_AST_UNKNOWN_BINDING_INVALID")
    label_anchor_ids = {
        row.source_anchor_id
        for row in value.source_fragments
        if row.fragment_role == "label"
    }
    if any(
        type(row) is not Step11IntegratedMixedEmotionRequirement
        or not row.required
        or row.relation_type != "coexists_with"
        or row.relation_direction != "bidirectional"
        or not row.positive_label_anchor_ids
        or not row.negative_label_anchor_ids
        or not set(
            (*row.positive_label_anchor_ids, *row.negative_label_anchor_ids)
        )
        <= label_anchor_ids
        or set(row.positive_label_anchor_ids)
        & set(row.negative_label_anchor_ids)
        for row in value.mixed_emotion_requirements
    ):
        issues.add("STEP11_SURFACE_AST_MIXED_EMOTION_INVALID")
    reception_clauses = {
        clause.obligation_id: clause
        for sentence in value.sentences
        if sentence.section_role == "reception"
        for clause in sentence.clauses
        if clause.clause_form == "bound_reception"
    }
    if (
        len(reception_clauses) != sum(
            clause.clause_form == "bound_reception"
            for sentence in value.sentences
            if sentence.section_role == "reception"
            for clause in sentence.clauses
        )
        or len(value.reception_antecedent_bindings) != len(reception_clauses)
        or any(
            type(row) is not Step11IntegratedReceptionAntecedentBinding
            or row.reception_obligation_id not in reception_clauses
            or row.reception_node_id
            != reception_clauses[row.reception_obligation_id].discourse_node_id
            or row.source_target_obligation_ids
            != reception_clauses[
                row.reception_obligation_id
            ].target_obligation_ids
            or not row.source_target_node_ids
            or not row.source_target_nucleus_ids
            or not row.antecedent_obligation_ids
            or not row.antecedent_node_ids
            or not row.antecedent_nucleus_ids
            or bool(row.supporting_obligation_ids)
            != bool(row.supporting_node_ids)
            or bool(row.supporting_obligation_ids)
            != bool(row.supporting_nucleus_ids)
            or row.support_role
            not in {
                "none",
                "source_opportunity_support",
                "source_progressive_concrete_action",
                "legacy_purpose_negation_scope_corrected_action",
            }
            or (row.support_role == "none")
            != (not row.supporting_obligation_ids)
            or row.action_lifecycle
            not in {
                "not_applicable",
                "undetermined",
                "intended",
                "reported_ongoing",
                "reported_not_completed",
                "reported_completed",
            }
            or row.evidence_grade
            != "visible_typed_antecedent_exact_source_owner"
            or not row.allowed_response_acts
            or reception_clauses[row.reception_obligation_id].reception_act
            not in row.allowed_response_acts
            for row in value.reception_antecedent_bindings
        )
    ):
        issues.add("STEP11_SURFACE_AST_RECEPTION_BINDING_INVALID")
    self_denial_anchor_ids = set(value.self_denial_source_anchor_ids)
    denial_fragments = tuple(
        row
        for row in value.source_fragments
        if row.source_anchor_id in self_denial_anchor_ids
    )
    if (
        value.identity_claim_must_not_be_accepted_as_fact
        is not bool(self_denial_anchor_ids)
        or len(denial_fragments) != len(self_denial_anchor_ids)
        or any(
            row.fragment_role != "self_evaluation"
            for row in denial_fragments
        )
        or set(value.self_denial_source_slots)
        != {row.source_slot for row in denial_fragments}
    ):
        issues.add("STEP11_SURFACE_AST_SELF_DENIAL_ANCHOR_INVALID")
    try:
        owned_observation_lines = _additional_observation_lines(
            value
        )
        owned_reception_lines = _reception_lines(
            value,
            observation_lines=owned_observation_lines,
        )
        expected_realization_plan = _derive_surface_realization_plan(
            value,
            owned_observation_lines,
            owned_reception_lines,
        )
        if (
            type(value.surface_realization_plan)
            is not Step11SurfaceRealizationPlan
            or value.surface_realization_plan != expected_realization_plan
            or value.surface_realization_plan.schema_version
            != STEP11_SURFACE_REALIZATION_PLAN_SCHEMA
            or value.surface_realization_plan.candidate_version_id
            != STEP11_CANDIDATE_VERSION_ID
            or value.surface_realization_plan.body_free is not True
            or value.surface_realization_plan.realization_plan_id
            != "nls3s11real_"
            + artifact_sha256(
                step11_surface_realization_plan_material(
                    value.surface_realization_plan,
                    include_id=False,
                )
            )[:16]
        ):
            issues.add("STEP11_SURFACE_REALIZATION_PLAN_INVALID")
        observation_sentence_lines = _observation_sentence_lines(
            value, owned_observation_lines
        )
        reception_sentence_lines = _reception_sentence_lines(
            value, owned_reception_lines
        )
        if any(row.literal_anchor_ids for row in owned_reception_lines):
            issues.add("STEP11_SURFACE_AST_RECEPTION_LITERAL_INVALID")
        if (
            len(observation_sentence_lines)
            != sum(
                row.section_role == "observation"
                for row in value.sentences
            )
            or len(reception_sentence_lines)
            != sum(
                row.section_role == "reception"
                for row in value.sentences
            )
        ):
            issues.add("STEP11_SURFACE_AST_SENTENCE_GROUP_RENDER_INVALID")
    except (
        AttributeError,
        IndexError,
        KeyError,
        Step11NaturalSurfaceError,
        TypeError,
        ValueError,
    ):
        issues.add("STEP11_SURFACE_AST_OWNERSHIP_RENDERABILITY_INVALID")
    return tuple(sorted(issues))


def _candidate_identity(
    ast: Step11NaturalSurfaceAst,
    rendered: Step11CanonicalRenderedSurface,
) -> str:
    return "nls3s11cand_" + artifact_sha256(
        {
            "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
            "surface_ast_sha256": artifact_sha256(
                step11_surface_ast_material(ast)
            ),
            "rendered_surface_sha256": rendered.sha256,
            "surface_catalog_sha256": STEP11_SURFACE_CATALOG_SHA256,
        }
    )[:20]


def build_step11_natural_surface_candidate(
    discourse_plan: Mapping[str, Any],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11NaturalSurfaceCandidate:
    projection = project_step11_current_input(current_input)
    ast = _build_ast(
        discourse_plan,
        inventory_result=inventory_result,
        content_plan=content_plan,
        projection=projection,
        current_input=current_input,
    )
    rendered = render_step11_natural_surface(
        ast,
        discourse_plan=discourse_plan,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )
    candidate = Step11NaturalSurfaceCandidate(
        schema_version=STEP11_CANDIDATE_SCHEMA,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        candidate_id=_candidate_identity(ast, rendered),
        discourse_plan=dict(discourse_plan),
        current_input_projection=projection,
        surface_ast=ast,
        rendered_surface=rendered,
    )
    issues = validate_step11_natural_surface_candidate(
        candidate,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    return candidate


def build_step11_natural_surface_candidates(
    discourse_plans: Sequence[Mapping[str, Any]],
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> tuple[Step11NaturalSurfaceCandidate, ...]:
    if type(discourse_plans) not in {list, tuple} or not discourse_plans:
        raise Step11NaturalSurfaceError("STEP11_DISCOURSE_PLAN_SET_REQUIRED")
    candidate_rows: list[Step11NaturalSurfaceCandidate] = []
    for plan in discourse_plans:
        try:
            candidate_rows.append(
                build_step11_natural_surface_candidate(
                    plan,
                    inventory_result=inventory_result,
                    content_plan=content_plan,
                    current_input=current_input,
                )
            )
        except Step11NaturalSurfaceError as exc:
            # One frozen discourse candidate may have too few sentence groups
            # for the independently reconstructed semantic-unit count.  That
            # candidate fails closed; structurally larger candidates remain
            # eligible.  Every other error remains terminal.
            if exc.code != "STEP11_SURFACE_PLAN_DENSITY_UNSATISFIABLE":
                raise
    candidates = tuple(candidate_rows)
    if not candidates:
        raise Step11NaturalSurfaceError(
            "STEP11_SURFACE_PLAN_DENSITY_UNSATISFIABLE"
        )
    by_body: dict[str, Step11NaturalSurfaceCandidate] = {}
    for row in sorted(candidates, key=lambda item: item.candidate_id):
        by_body.setdefault(row.rendered_surface.sha256, row)
    # Multiple planner variants may legitimately lead to the same canonical
    # bytes.  Expose one deterministic candidate for that body instead of
    # pretending identical product choices are distinct.
    ordered = tuple(sorted(by_body.values(), key=lambda row: row.candidate_id))
    if len({row.candidate_id for row in ordered}) != len(ordered):
        raise Step11NaturalSurfaceError("STEP11_CANDIDATE_ID_DUPLICATE")
    return ordered


def validate_step11_natural_surface_candidate(
    value: Any,
    *,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not Step11NaturalSurfaceCandidate:
        return ("STEP11_CANDIDATE_TYPE_INVALID",)
    issues: set[str] = set()
    if value.schema_version != STEP11_CANDIDATE_SCHEMA:
        issues.add("STEP11_CANDIDATE_SCHEMA_INVALID")
    if value.candidate_version_id != STEP11_CANDIDATE_VERSION_ID:
        issues.add("STEP11_CANDIDATE_VERSION_INVALID")
    if not _CANDIDATE_ID_RE.fullmatch(value.candidate_id):
        issues.add("STEP11_CANDIDATE_ID_INVALID")
    try:
        expected_projection = project_step11_current_input(current_input)
        ast_issues = validate_step11_surface_ast(
            value.surface_ast,
            discourse_plan=value.discourse_plan,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        expected_render = render_step11_natural_surface(
            value.surface_ast,
            discourse_plan=value.discourse_plan,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
    except (
        AttributeError,
        IndexError,
        KeyError,
        Step11NaturalSurfaceError,
        TypeError,
        ValueError,
    ):
        return tuple(sorted(issues | {"STEP11_CANDIDATE_REVALIDATION_FAILED"}))
    issues.update(ast_issues)
    if value.current_input_projection != expected_projection:
        issues.add("STEP11_CANDIDATE_INPUT_PROJECTION_MISMATCH")
    if type(value.rendered_surface) is not Step11CanonicalRenderedSurface:
        issues.add("STEP11_RENDERED_SURFACE_TYPE_INVALID")
    elif value.rendered_surface != expected_render:
        issues.add("STEP11_RENDERED_SURFACE_RECOMPUTATION_MISMATCH")
    elif (
        value.rendered_surface.sha256
        != hashlib.sha256(value.rendered_surface.utf8_bytes).hexdigest()
        or value.rendered_surface.utf8_bytes.decode("utf-8").encode("utf-8")
        != value.rendered_surface.utf8_bytes
    ):
        issues.add("STEP11_RENDERED_SURFACE_BYTES_INVALID")
    if value.candidate_id != _candidate_identity(
        value.surface_ast, value.rendered_surface
    ):
        issues.add("STEP11_CANDIDATE_ID_MISMATCH")
    return tuple(sorted(issues))


__all__ = [
    "STEP11_CANDIDATE_SCHEMA",
    "STEP11_CANDIDATE_VERSION_ID",
    "STEP11_RENDERED_SURFACE_SCHEMA",
    "STEP11_SURFACE_AST_SCHEMA",
    "STEP11_SURFACE_REALIZATION_PLAN_SCHEMA",
    "Step11CanonicalRenderedSurface",
    "Step11CurrentInputProjection",
    "Step11IntegratedMixedEmotionRequirement",
    "Step11IntegratedReceptionAntecedentBinding",
    "Step11IntegratedRelation",
    "Step11IntegratedUnknown",
    "Step11NaturalSurfaceAst",
    "Step11NaturalSurfaceCandidate",
    "Step11NaturalSurfaceError",
    "Step11NucleusSurfaceReference",
    "Step11SourceFragment",
    "Step11SurfaceClause",
    "Step11SurfaceRealizationPlan",
    "Step11SurfaceRealizationUnit",
    "Step11SurfaceSentence",
    "build_step11_natural_surface_candidate",
    "build_step11_natural_surface_candidates",
    "build_step11_surface_realization_plan",
    "project_step11_current_input",
    "render_step11_natural_surface",
    "step11_surface_ast_material",
    "step11_surface_realization_plan_material",
    "validate_step11_natural_surface_candidate",
    "validate_step11_surface_ast",
]
