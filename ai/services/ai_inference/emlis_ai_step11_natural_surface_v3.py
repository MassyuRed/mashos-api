# -*- coding: utf-8 -*-
from __future__ import annotations

"""Forward-only rc0027 natural surface successor.

The module consumes only the current input projection and independently
revalidated Step 4--6 semantic artifacts.  It does not import the frozen Step
7--9 renderer, parser, gate, selector, runtime, corpus, or test owners.
"""

from dataclasses import dataclass, replace
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
from emlis_ai_step11_grounded_lexicalization_v3 import (
    Step11GroundedLexicalizationError,
    Step11GroundedPhraseSpec,
    Step11VisibleSourceAnchorUse,
    build_step11_grounded_phrase_specs,
    render_step11_grounded_phrase,
    select_step11_visible_source_anchor_use,
    step11_grounded_phrase_spec_material,
    step11_visible_source_anchor_use_material,
)
from emlis_ai_step11_semantic_overlay_v3 import (
    Step11SemanticOverlay,
    build_step11_semantic_overlay,
    step11_semantic_overlay_material,
)


STEP11_CANDIDATE_VERSION_ID = "nls_v3_rc_0027"
STEP11_SURFACE_AST_SCHEMA = "cocolon.emlis.nls_v3.step11_natural_surface_ast.v10"
STEP11_RENDERED_SURFACE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_canonical_rendered_surface.v10"
)
STEP11_CANDIDATE_SCHEMA = "cocolon.emlis.nls_v3.step11_natural_candidate.v10"
STEP11_SURFACE_REALIZATION_PLAN_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_surface_realization_plan.rc0027.v1"
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
    grounded_phrase_specs: tuple[Step11GroundedPhraseSpec, ...]
    visible_source_anchor_use: Step11VisibleSourceAnchorUse | None
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
    visible_source_anchor_count: int
    source_anchor_reason_codes: tuple[str, ...]
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
    reception_act: str = ""
    reception_scope: str = ""
    realization_status: str = ""
    typed_placeholders: tuple[tuple[str, str], ...] = ()


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
        "grounded_phrase_specs": [
            step11_grounded_phrase_spec_material(row)
            for row in value.grounded_phrase_specs
        ],
        "visible_source_anchor_use": (
            step11_visible_source_anchor_use_material(
                value.visible_source_anchor_use
            )
            if type(value.visible_source_anchor_use)
            is Step11VisibleSourceAnchorUse
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
    clause_nucleus_ids = {
        nucleus_id
        for clause in all_clauses
        for nucleus_id in clause.source_nucleus_ids
    }
    render_reachable_nucleus_ids = {
        nucleus_id
        for reference in nucleus_surface_references
        for nucleus_id in reference.nucleus_ids
    }
    additional_owner_obligation_ids = {
        nucleus_id: tuple(
            obligation_id
            for obligation_id, obligation in by_id.items()
            if nucleus_id in obligation.get("nucleus_ids", [])
        )
        for nucleus_id in sorted(
            render_reachable_nucleus_ids - clause_nucleus_ids
        )
    }
    if any(not values for values in additional_owner_obligation_ids.values()):
        raise Step11NaturalSurfaceError(
            "STEP11_GROUNDED_PHRASE_OWNER_UNRESOLVED"
        )
    label_strength_by_nucleus: dict[str, str] = {}
    action_lifecycle_by_nucleus: dict[str, str] = {}
    allowed_action_lifecycles = frozenset(
        STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["lifecycle_authority_policy"]["action_projection"]
    )
    for fragment in source_fragments:
        if fragment.label_strength is not None:
            for nucleus_id in fragment.source_nucleus_ids:
                previous = label_strength_by_nucleus.setdefault(
                    nucleus_id, fragment.label_strength
                )
                if previous != fragment.label_strength:
                    raise Step11NaturalSurfaceError(
                        "STEP11_GROUNDED_LABEL_STRENGTH_AMBIGUOUS"
                    )
        if (
            fragment.source_slot == "action"
            and fragment.fragment_role == "nucleus"
            and fragment.realization_status in allowed_action_lifecycles
        ):
            for nucleus_id in fragment.source_nucleus_ids:
                previous = action_lifecycle_by_nucleus.setdefault(
                    nucleus_id, fragment.realization_status
                )
                if previous != fragment.realization_status:
                    raise Step11NaturalSurfaceError(
                        "STEP11_GROUNDED_ACTION_LIFECYCLE_AMBIGUOUS"
                    )
    source_by_nucleus_id = {
        str(source.source_id): source
        for source in inventory_result.source_snapshot.nuclei
    }
    if any(
        str(source_by_nucleus_id[nucleus_id].kind) != "action"
        for nucleus_id in action_lifecycle_by_nucleus
        if nucleus_id in source_by_nucleus_id
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_GROUNDED_ACTION_LIFECYCLE_OWNER_INVALID"
        )
    additional_visible_features: dict[str, dict[str, str]] = {}
    for nucleus_id, label_strength in label_strength_by_nucleus.items():
        additional_visible_features.setdefault(nucleus_id, {})[
            "label_strength"
        ] = label_strength
    for nucleus_id, lifecycle in action_lifecycle_by_nucleus.items():
        additional_visible_features.setdefault(nucleus_id, {})[
            "realization_lifecycle"
        ] = lifecycle
    try:
        grounded_phrase_specs = build_step11_grounded_phrase_specs(
            inventory_result.source_snapshot,
            all_clauses,
            additional_owner_obligation_ids=(
                additional_owner_obligation_ids
            ),
            additional_visible_feature_values=additional_visible_features,
        )
        phrase_owner_nucleus_ids = {
            nucleus_id
            for spec in grounded_phrase_specs
            for nucleus_id in spec.owner_nucleus_ids
        }
        spec_by_nucleus_id = {
            spec.owner_nucleus_ids[0]: spec
            for spec in grounded_phrase_specs
        }
        source_order = {
            str(source.source_id): ordinal
            for ordinal, source in enumerate(
                inventory_result.source_snapshot.nuclei
            )
        }
        required_relation_nucleus_ids = tuple(
            dict.fromkeys(
                nucleus_id
                for relation in integrated_relations
                if relation.required
                for nucleus_id in (
                    relation.from_nucleus_id,
                    relation.to_nucleus_id,
                )
            )
        )
        required_unknown_nucleus_ids = tuple(
            dict.fromkeys(
                nucleus_id
                for unknown in integrated_unknowns
                for nucleus_id in (
                    *unknown.target_nucleus_ids,
                    *unknown.context_nucleus_ids,
                )
            )
        )
        all_render_ids = tuple(
            nucleus_id
            for source in inventory_result.source_snapshot.nuclei
            for nucleus_id in (str(source.source_id),)
            if nucleus_id in phrase_owner_nucleus_ids
        )
        lexical_catalog = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        registry = lexical_catalog["phrase_profile_registry"]
        profile_by_id = {
            str(row["profile_id"]): row for row in registry["profiles"]
        }
        generic_profile_ids = frozenset(
            str(value)
            for value in registry["specificity_policy"][
                "kind_only_generic_profile_ids"
            ]
        )
        residual_policy = lexical_catalog[
            "residual_information_loss_policy"
        ]
        semantic_prefixes = tuple(
            str(value)
            for value in residual_policy["semantic_attribute_prefixes"]
        )
        high_signal_codes = frozenset(
            str(value)
            for value in residual_policy["high_signal_attribute_codes"]
        )
        concrete_action_code = str(
            residual_policy["concrete_action_attribute_code"]
        )
        kind_implied_codes = {
            str(kind): frozenset(str(code) for code in codes)
            for kind, codes in residual_policy[
                "kind_implied_attribute_codes"
            ].items()
        }
        required_relation_or_unknown_ids = frozenset(
            (*required_relation_nucleus_ids, *required_unknown_nucleus_ids)
        )
        action_input_core = projection.action_text.strip().rstrip(
            "。！？!?"
        )
        trusted_complete_action_input = bool(
            2 <= len(action_input_core) <= 16
            and not any(
                character.isspace()
                or unicodedata.category(character).startswith("C")
                or character
                in "。、，．！？!?;；:：,.\"'`()[]{}（）［］｛｝〈〉《》【】〔〕「」『』"
                for character in action_input_core
            )
        )

        def residual_priority_key(nucleus_id: str) -> tuple[Any, ...]:
            source = source_by_nucleus_id[nucleus_id]
            spec = spec_by_nucleus_id[nucleus_id]
            profile = profile_by_id[spec.phrase_profile_id]
            match = profile["match"]
            source_codes = frozenset(
                str(value) for value in source.source_attribute_codes
            )
            captured_codes = frozenset(
                str(value)
                for value in match.get("all_attribute_codes", [])
            ) | frozenset(
                str(value)
                for value in match.get("any_attribute_codes", [])
                if str(value) in source_codes
            )
            semantic_codes = frozenset(
                code
                for code in source_codes
                if code.startswith(semantic_prefixes)
            )
            uncaptured_codes = (
                semantic_codes
                - captured_codes
                - kind_implied_codes.get(str(source.kind), frozenset())
            )
            uncaptured_high_signal_codes = (
                uncaptured_codes & high_signal_codes
            )
            required = bool(source.required)
            kind_only_generic = (
                spec.phrase_profile_id in generic_profile_ids
            )
            qualified_concrete_action = bool(
                concrete_action_code in source_codes
                and (
                    uncaptured_high_signal_codes
                    or trusted_complete_action_input
                )
            )
            return (
                -int(required and kind_only_generic),
                -int(nucleus_id in required_relation_or_unknown_ids),
                -int(required),
                -len(uncaptured_high_signal_codes),
                -int(qualified_concrete_action),
                -len(uncaptured_codes),
                -int(kind_only_generic),
                -spec.anchor_risk_rank,
                source_order[nucleus_id],
                nucleus_id,
            )

        preferred_anchor_owner_ids = tuple(
            sorted(all_render_ids, key=residual_priority_key)
        )
        visible_source_anchor_use = (
            select_step11_visible_source_anchor_use(
                grounded_phrase_specs,
                source_fragments,
                preferred_owner_nucleus_ids=preferred_anchor_owner_ids,
                require_input_specific_binding=True,
            )
        )
        if (
            registry["specificity_policy"][
                "unanchored_required_kind_only_generic"
            ]
            == "fail_closed"
        ):
            unanchored_required_generic_ids = tuple(
                nucleus_id
                for nucleus_id in all_render_ids
                if nucleus_id != visible_source_anchor_use.owner_nucleus_id
                and bool(source_by_nucleus_id[nucleus_id].required)
                and spec_by_nucleus_id[nucleus_id].phrase_profile_id
                in generic_profile_ids
            )
            if unanchored_required_generic_ids:
                raise Step11NaturalSurfaceError(
                    "STEP11_REQUIRED_OWNER_INPUT_SPECIFICITY_UNRESOLVED"
                )
    except Step11GroundedLexicalizationError as exc:
        raise Step11NaturalSurfaceError(exc.code) from None
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
        grounded_phrase_specs=grounded_phrase_specs,
        visible_source_anchor_use=visible_source_anchor_use,
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
        grounded_phrase_specs=ast.grounded_phrase_specs,
        visible_source_anchor_use=ast.visible_source_anchor_use,
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
        grounded_phrase_specs=ast.grounded_phrase_specs,
        visible_source_anchor_use=ast.visible_source_anchor_use,
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


def _grounded_phrase_spec_for_nucleus(
    ast: Step11NaturalSurfaceAst,
    nucleus_id: str,
) -> Step11GroundedPhraseSpec:
    matches = tuple(
        spec
        for spec in ast.grounded_phrase_specs
        if nucleus_id in spec.owner_nucleus_ids
    )
    if len(matches) != 1:
        raise Step11NaturalSurfaceError(
            "STEP11_GROUNDED_PHRASE_OWNER_UNRESOLVED"
        )
    return matches[0]


def _grounded_phrase_text(
    ast: Step11NaturalSurfaceAst,
    nucleus_id: str,
    *,
    include_visible_anchor: bool = False,
) -> str:
    spec = _grounded_phrase_spec_for_nucleus(ast, nucleus_id)
    anchor = (
        ast.visible_source_anchor_use
        if include_visible_anchor
        and ast.visible_source_anchor_use is not None
        and ast.visible_source_anchor_use.owner_nucleus_id == nucleus_id
        else None
    )
    try:
        return render_step11_grounded_phrase(spec, anchor)
    except Step11GroundedLexicalizationError as exc:
        raise Step11NaturalSurfaceError(exc.code) from None


def _relation_line(
    relation: Step11IntegratedRelation,
    *,
    ast: Step11NaturalSurfaceAst,
    from_is_anaphoric: bool = False,
    to_is_anaphoric: bool = False,
    visible_anchor_nucleus_id: str | None = None,
) -> str:
    grammar = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    rule = grammar["relation_atoms"][relation.relation_type][
        relation.relation_direction
    ]
    if (
        type(rule) is not dict
        or set(rule) != {"endpoint_order", "left", "right"}
        or rule["endpoint_order"] not in (["from", "to"], ["to", "from"])
        or type(rule["left"]) is not str
        or type(rule["right"]) is not str
    ):
        raise Step11NaturalSurfaceError("STEP11_RELATION_ATOMS_INVALID")
    from_text = _grounded_phrase_text(
        ast,
        relation.from_nucleus_id,
        include_visible_anchor=(
            visible_anchor_nucleus_id == relation.from_nucleus_id
        ),
    )
    to_text = _grounded_phrase_text(
        ast,
        relation.to_nucleus_id,
        include_visible_anchor=(
            visible_anchor_nucleus_id == relation.to_nucleus_id
        ),
    )
    anaphors = grammar["local_anaphors"]
    from_endpoint = (
        anaphors[relation.from_endpoint_role]
        if from_is_anaphoric
        else from_text
    )
    to_endpoint = (
        anaphors[relation.to_endpoint_role]
        if to_is_anaphoric
        else to_text
    )
    endpoints = {"from": from_endpoint, "to": to_endpoint}
    first, second = rule["endpoint_order"]
    return endpoints[first] + rule["left"] + endpoints[second] + rule["right"]


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


def _natural_introduction_line(
    fragment: Step11SourceFragment,
    *,
    ast: Step11NaturalSurfaceAst,
    include_visible_anchor: bool = False,
) -> str:
    reference = _reference_for_anchor(ast, fragment.source_anchor_id)
    if len(reference.nucleus_ids) != 1:
        raise Step11NaturalSurfaceError(
            "STEP11_GROUNDED_PHRASE_OWNER_UNRESOLVED"
        )
    return (
        _grounded_phrase_text(
            ast,
            reference.nucleus_ids[0],
            include_visible_anchor=include_visible_anchor,
        )
        + STEP11_SURFACE_CATALOG["grounded_lexicalization"][
            "observation_predicate"
        ]
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
    visible_anchor_emitted = False
    realised_unknown_obligation_ids = {
        obligation_id
        for unknown in ast.integrated_unknowns
        for obligation_id in unknown.owner_obligation_ids
    }

    def take_visible_anchor(
        nucleus_ids: Sequence[str],
    ) -> str | None:
        nonlocal visible_anchor_emitted
        anchor = ast.visible_source_anchor_use
        if (
            anchor is None
            or visible_anchor_emitted
            or anchor.owner_nucleus_id not in nucleus_ids
        ):
            return None
        visible_anchor_emitted = True
        return anchor.owner_nucleus_id
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
        from_anchor_ids = equivalent_anchor_ids(endpoint_anchor_ids[0])
        to_anchor_ids = equivalent_anchor_ids(endpoint_anchor_ids[1])
        owned_anchor_ids = tuple(
            dict.fromkeys((*from_anchor_ids, *to_anchor_ids))
        )
        from_is_anaphoric = bool(
            set(from_anchor_ids) & covered_anchor_ids
        )
        to_is_anaphoric = bool(set(to_anchor_ids) & covered_anchor_ids)
        visible_anchor_nucleus_id = take_visible_anchor(
            (relation.from_nucleus_id, relation.to_nucleus_id)
        )
        if visible_anchor_nucleus_id == relation.from_nucleus_id:
            from_is_anaphoric = False
        if visible_anchor_nucleus_id == relation.to_nucleus_id:
            to_is_anaphoric = False
        if from_is_anaphoric and to_is_anaphoric:
            raise Step11NaturalSurfaceError(
                "STEP11_RELATION_MULTI_EDGE_LOCAL_ANAPHORA_AMBIGUOUS"
            )
        literal_anchor_ids = tuple(
            dict.fromkeys(
                (
                    *(() if from_is_anaphoric else from_anchor_ids),
                    *(() if to_is_anaphoric else to_anchor_ids),
                )
            )
        )
        nucleus_ids = (relation.from_nucleus_id, relation.to_nucleus_id)
        owner_ids = tuple(
            dict.fromkeys(
                (
                    *relation.owner_obligation_ids,
                    *claim_basic_obligations(nucleus_ids),
                )
            )
        )
        lines.append(
            _Step11OwnedObservationLine(
                    text=_relation_line(
                        relation,
                        ast=ast,
                        from_is_anaphoric=from_is_anaphoric,
                        to_is_anaphoric=to_is_anaphoric,
                        visible_anchor_nucleus_id=visible_anchor_nucleus_id,
                    ),
                owned_anchor_ids=owned_anchor_ids,
                owned_nucleus_ids=nucleus_ids,
                owned_relation_ids=relation.source_relation_ids,
                owned_obligation_ids=owner_ids,
                owned_mixed_emotion_requirement_ids=(),
                    literal_anchor_ids=literal_anchor_ids,
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
        covered_anchor_ids.update(owned_anchor_ids)

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
        ordered_endpoints = tuple(
            sorted(
                (
                    (positive_reference, positive),
                    (negative_reference, negative),
                ),
                key=lambda row: row[0].reference_ordinal,
            )
        )
        anchor_ids = tuple(
            row.source_anchor_id for _reference, row in ordered_endpoints
        )
        reference_ordinals = tuple(
            row.reference_ordinal for row, _fragment in ordered_endpoints
        )
        nucleus_ids = tuple(
            dict.fromkeys(
                (*positive.source_nucleus_ids, *negative.source_nucleus_ids)
            )
        )
        if any(
            len(reference.nucleus_ids) != 1
            for reference, _fragment in ordered_endpoints
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_GROUNDED_PHRASE_OWNER_UNRESOLVED"
            )
        visible_anchor_nucleus_id = take_visible_anchor(nucleus_ids)
        lexical = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        text = (
            _grounded_phrase_text(
                ast,
                ordered_endpoints[0][0].nucleus_ids[0],
                include_visible_anchor=(
                    visible_anchor_nucleus_id
                    == ordered_endpoints[0][0].nucleus_ids[0]
                ),
            )
            + lexical["coexisting_joiner"]
            + _grounded_phrase_text(
                ast,
                ordered_endpoints[1][0].nucleus_ids[0],
                include_visible_anchor=(
                    visible_anchor_nucleus_id
                    == ordered_endpoints[1][0].nucleus_ids[0]
                ),
            )
            + lexical["coexisting_predicate"]
        )
        owned_obligation_ids = claim_basic_obligations(nucleus_ids)
        literal_anchor_ids = anchor_ids
        lines.append(
            _Step11OwnedObservationLine(
                text=text,
                owned_anchor_ids=anchor_ids,
                owned_nucleus_ids=nucleus_ids,
                owned_relation_ids=(),
                owned_obligation_ids=owned_obligation_ids,
                owned_mixed_emotion_requirement_ids=(
                    requirement.requirement_id,
                ),
                literal_anchor_ids=literal_anchor_ids,
                required_relation_ids=(requirement.requirement_id,),
                used_reference_ordinals=reference_ordinals,
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
        tail_key = (
            "other_person_awareness"
            if dimension == "other_person_awareness"
            or (
                dimension == "referent"
                and "other_person" in unknown.dimension_code.casefold()
            )
            else dimension
        )
        lexical = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        dimension_atom = lexical["unknown_dimension_atoms"].get(
            tail_key,
            lexical["unknown_dimension_atoms"]["generic"],
        )
        unknown_text = dimension_atom + lexical["unknown_predicate"]
        if type(unknown_text) is not str or not unknown_text:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_FUSED_TAIL_INVALID"
            )
        if relation_owners:
            owner_indices = tuple(
                index
                for index, line in enumerate(lines)
                if any(line is owner for owner in relation_owners)
            )
        else:
            owner_indices = tuple(
                index
                for index, line in enumerate(lines)
                if line_owns_anchor(
                    line,
                    anchor_id,
                    target_nucleus_ids=unknown.target_nucleus_ids,
                )
            )
        if len(owner_indices) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_FUSED_OWNER_INVALID"
            )
        owner_index = owner_indices[0]
        owner = lines[owner_index]
        lines[owner_index] = _Step11OwnedObservationLine(
            text=(
                f"{owner.text}が、"
                f"{unknown_text.removeprefix('ただ、')}"
            ),
            owned_anchor_ids=tuple(
                dict.fromkeys((*owner.owned_anchor_ids, *anchor_owner_ids))
            ),
            owned_nucleus_ids=tuple(
                dict.fromkeys((*owner.owned_nucleus_ids, *owned_nucleus_ids))
            ),
            owned_relation_ids=owner.owned_relation_ids,
            owned_obligation_ids=tuple(
                dict.fromkeys(
                    (*owner.owned_obligation_ids, *owner_obligation_ids)
                )
            ),
            owned_mixed_emotion_requirement_ids=(
                owner.owned_mixed_emotion_requirement_ids
            ),
            literal_anchor_ids=owner.literal_anchor_ids,
            required_relation_ids=owner.required_relation_ids,
            used_reference_ordinals=tuple(
                dict.fromkeys(
                    (
                        *owner.used_reference_ordinals,
                        *(
                    reference.reference_ordinal
                    for reference in target_references
                        ),
                    )
                )
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

    # A thought and an action with no typed relation are one neutral
    # co-presence unit.  This preserves both exact literals without inventing
    # a causal or temporal edge between them.
    if not ast.integrated_relations:
        thought_references = tuple(
            row
            for row in ast.nucleus_surface_references
            if row.source_slot == "thought"
            and not set(row.source_anchor_ids) & covered_anchor_ids
        )
        action_references = tuple(
            row
            for row in ast.nucleus_surface_references
            if row.source_slot == "action"
            and not set(row.source_anchor_ids) & covered_anchor_ids
        )
        if len(thought_references) == len(action_references) == 1:
            thought_reference = thought_references[0]
            action_reference = action_references[0]
            thought_fragment = _fragment_by_anchor_id(
                ast, thought_reference.source_anchor_ids[0]
            )
            action_fragment = _fragment_by_anchor_id(
                ast, action_reference.source_anchor_ids[0]
            )
            pair_nucleus_ids = tuple(
                dict.fromkeys(
                    (
                        *thought_reference.nucleus_ids,
                        *action_reference.nucleus_ids,
                    )
                )
            )
            pair_anchor_ids = tuple(
                dict.fromkeys(
                    (
                        *thought_reference.source_anchor_ids,
                        *action_reference.source_anchor_ids,
                    )
                )
            )
            if (
                len(thought_reference.nucleus_ids) != 1
                or len(action_reference.nucleus_ids) != 1
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_GROUNDED_PHRASE_OWNER_UNRESOLVED"
                )
            visible_anchor_nucleus_id = take_visible_anchor(pair_nucleus_ids)
            lexical = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
            text = (
                _grounded_phrase_text(
                    ast,
                    thought_reference.nucleus_ids[0],
                    include_visible_anchor=(
                        visible_anchor_nucleus_id
                        == thought_reference.nucleus_ids[0]
                    ),
                )
                + lexical["coexisting_joiner"]
                + _grounded_phrase_text(
                    ast,
                    action_reference.nucleus_ids[0],
                    include_visible_anchor=(
                        visible_anchor_nucleus_id
                        == action_reference.nucleus_ids[0]
                    ),
                )
                + lexical["coexisting_predicate"]
            )
            lines.append(
                _Step11OwnedObservationLine(
                    text=text,
                    owned_anchor_ids=pair_anchor_ids,
                    owned_nucleus_ids=pair_nucleus_ids,
                    owned_relation_ids=(),
                    owned_obligation_ids=claim_basic_obligations(
                        pair_nucleus_ids
                    ),
                    owned_mixed_emotion_requirement_ids=(),
                    literal_anchor_ids=pair_anchor_ids,
                    required_relation_ids=(),
                    used_reference_ordinals=(
                        thought_reference.reference_ordinal,
                        action_reference.reference_ordinal,
                    ),
                )
            )
            covered_anchor_ids.update(pair_anchor_ids)

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
        visible_anchor_nucleus_id = take_visible_anchor(
            fragment.source_nucleus_ids
        )
        if reference is not None:
            text = _natural_introduction_line(
                fragment,
                ast=ast,
                include_visible_anchor=(
                    visible_anchor_nucleus_id in reference.nucleus_ids
                ),
            )
        else:
            if not fragment.source_nucleus_ids:
                raise Step11NaturalSurfaceError(
                    "STEP11_GROUNDED_PHRASE_OWNER_UNRESOLVED"
                )
            lexical = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
            text = (
                lexical["coexisting_joiner"].join(
                    _grounded_phrase_text(
                        ast,
                        nucleus_id,
                        include_visible_anchor=(
                            visible_anchor_nucleus_id == nucleus_id
                        ),
                    )
                    for nucleus_id in fragment.source_nucleus_ids
                )
                + lexical["observation_predicate"]
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

    # Unknowns sharing one visible owner and one semantic boundary are one
    # compositional tail.  Their source identities and obligation ownership
    # remain a union in metadata; emitting one dependent ``...が`` chain per
    # source would make a single relation unreadable without adding meaning.
    unknown_groups: dict[
        tuple[int, str, str, str], list[Step11IntegratedUnknown]
    ] = {}
    for unknown in ast.integrated_unknowns:
        relation_owners = relation_antecedent_owners(unknown)
        if len(relation_owners) > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_ANTECEDENT_OWNER_AMBIGUOUS"
            )
        if relation_owners:
            owner_indices = tuple(
                index
                for index, line in enumerate(lines)
                if line is relation_owners[0]
            )
        else:
            owner_indices = tuple(
                index
                for index, line in enumerate(lines)
                if line_owns_anchor(
                    line,
                    unknown.source_anchor_ids[0],
                    target_nucleus_ids=unknown.target_nucleus_ids,
                )
            )
        if len(owner_indices) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_UNKNOWN_FUSED_OWNER_INVALID"
            )
        key = (
            owner_indices[0],
            _unknown_dimension_class(unknown.dimension_code),
            unknown.surface_policy,
            unknown.decision_state,
        )
        unknown_groups.setdefault(key, []).append(unknown)

    for rows in unknown_groups.values():
        first = rows[0]
        merged = replace(
            first,
            source_slots=tuple(
                dict.fromkeys(
                    slot for row in rows for slot in row.source_slots
                )
            ),
            target_nucleus_ids=tuple(
                dict.fromkeys(
                    nucleus_id
                    for row in rows
                    for nucleus_id in row.target_nucleus_ids
                )
            ),
            source_unknown_ids=tuple(
                dict.fromkeys(
                    unknown_id
                    for row in rows
                    for unknown_id in row.source_unknown_ids
                )
            ),
            owner_obligation_ids=tuple(
                dict.fromkeys(
                    obligation_id
                    for row in rows
                    for obligation_id in row.owner_obligation_ids
                )
            ),
            source_rules=tuple(
                dict.fromkeys(
                    rule for row in rows for rule in row.source_rules
                )
            ),
            context_nucleus_ids=tuple(
                dict.fromkeys(
                    nucleus_id
                    for row in rows
                    for nucleus_id in row.context_nucleus_ids
                )
            ),
            context_anchor_ids=tuple(
                dict.fromkeys(
                    anchor_id
                    for row in rows
                    for anchor_id in row.context_anchor_ids
                )
            ),
        )
        append_unknown(merged)
        realised_unknowns.update(row.source_unknown_id for row in rows)

    for anchor_id in ast.self_denial_source_anchor_ids:
        append_self_denial(anchor_id)
    if ast.visible_source_anchor_use is not None and not visible_anchor_emitted:
        raise Step11NaturalSurfaceError(
            "STEP11_VISIBLE_SOURCE_ANCHOR_OWNER_MISSING"
        )
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


def _canonical_reception_content(options: Any) -> str:
    if (
        type(options) is not list
        or not options
        or type(options[0]) is not str
        or not options[0]
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RECEPTION_ANAPHORIC_BINDING_UNREPRESENTABLE"
        )
    content = options[0]
    if content.endswith("ずに"):
        content = content[:-2] + "ず、"
    return content


def _canonical_reception_predicate(options: Any) -> str:
    if (
        type(options) is not list
        or not options
        or type(options[0]) is not str
        or not options[0]
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RECEPTION_ACT_PREDICATE_UNRESOLVED"
        )
    return options[0]


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
    globally_unique_reference_by_slot = {
        slot: rows[0]
        for slot in ("thought", "action")
        for rows in (
            tuple(
                row
                for row in ast.nucleus_surface_references
                if row.source_slot == slot
            ),
        )
        if len(rows) == 1
    }
    reference_by_ordinal = {
        row.reference_ordinal: row
        for row in ast.nucleus_surface_references
    }

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
                reception_act=existing.reception_act,
                reception_scope=existing.reception_scope,
                realization_status=existing.realization_status,
                typed_placeholders=existing.typed_placeholders,
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
        visible_reference_ordinals = frozenset(
            row.reference_ordinal for row in visible_references
        )
        unique_scope_references: tuple[
            Step11NucleusSurfaceReference, ...
        ] = ()
        if scope == "thought" and "thought" in globally_unique_reference_by_slot:
            unique_scope_references = (
                globally_unique_reference_by_slot["thought"],
            )
        elif scope == "action" and "action" in globally_unique_reference_by_slot:
            unique_scope_references = (
                globally_unique_reference_by_slot["action"],
            )
        elif scope == "thought_action" and {
            "thought",
            "action",
        } <= set(globally_unique_reference_by_slot):
            unique_scope_references = (
                globally_unique_reference_by_slot["thought"],
                globally_unique_reference_by_slot["action"],
            )
        elif (
            scope == "relation"
            and len(ast.integrated_relations) == 1
            and len(owned_relations) == 1
            and ast.integrated_relations[0].source_relation_id
            == owned_relations[0].source_relation_id
        ):
            unique_scope_references = tuple(
                reference_by_ordinal[ordinal]
                for ordinal in (
                    owned_relations[0].from_reference_ordinal,
                    owned_relations[0].to_reference_ordinal,
                )
            )
        if (
            scope not in forms["anaphoric_content_forms"]
            or status not in forms["anaphoric_content_forms"][scope]
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_ANAPHORIC_BINDING_UNREPRESENTABLE"
            )
        content = _canonical_reception_content(
            forms["anaphoric_content_forms"][scope][status]
        )
        predicate = _canonical_reception_predicate(
            forms["act_predicates"][clause.reception_act]
        )
        sentence_template = forms["sentence_templates"][0]
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
            reception_act=str(clause.reception_act),
            reception_scope=scope,
            realization_status=status,
            typed_placeholders=(),
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
                    and (
                        existing.reception_act,
                        existing.reception_scope,
                        existing.realization_status,
                        existing.typed_placeholders,
                    )
                    == (
                        new_line.reception_act,
                        new_line.reception_scope,
                        new_line.realization_status,
                        new_line.typed_placeholders,
                    )
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
                    reception_act=dominant.reception_act,
                    reception_scope=dominant.reception_scope,
                    realization_status=dominant.realization_status,
                    typed_placeholders=dominant.typed_placeholders,
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

    def render_final_line(
        line: _Step11OwnedReceptionLine,
    ) -> _Step11OwnedReceptionLine:
        scope = line.reception_scope
        status = line.realization_status
        act = line.reception_act
        visible = frozenset(line.visible_reference_ordinals)
        unique_references: tuple[Step11NucleusSurfaceReference, ...] = ()
        if scope == "thought" and "thought" in globally_unique_reference_by_slot:
            unique_references = (
                globally_unique_reference_by_slot["thought"],
            )
        elif scope == "action" and "action" in globally_unique_reference_by_slot:
            unique_references = (
                globally_unique_reference_by_slot["action"],
            )
        elif scope == "thought_action" and {
            "thought",
            "action",
        } <= set(globally_unique_reference_by_slot):
            unique_references = (
                globally_unique_reference_by_slot["thought"],
                globally_unique_reference_by_slot["action"],
            )
        elif scope == "relation" and len(ast.integrated_relations) == 1:
            relation = ast.integrated_relations[0]
            unique_references = tuple(
                reference_by_ordinal[ordinal]
                for ordinal in (
                    relation.from_reference_ordinal,
                    relation.to_reference_ordinal,
                )
            )
        use_anaphoric = bool(
            scope in forms["anaphoric_content_forms"]
            and status in forms["anaphoric_content_forms"][scope]
        )
        final_contract_id = artifact_sha256(
            {
                "reception_act": act,
                "scope": scope,
                "status": status,
                "binding_ids": list(line.binding_ids),
                "reception_obligation_ids": list(
                    line.reception_obligation_ids
                ),
                "antecedent_obligation_ids": list(
                    line.antecedent_obligation_ids
                ),
                "supporting_obligation_ids": list(
                    line.supporting_obligation_ids
                ),
                "visible_reference_ordinals": list(
                    line.visible_reference_ordinals
                ),
            }
        )[:16]
        if not use_anaphoric:
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_ANAPHORIC_BINDING_UNREPRESENTABLE"
            )
        content = _canonical_reception_content(
            forms["anaphoric_content_forms"][scope][status]
        )
        predicate = _canonical_reception_predicate(
            forms["act_predicates"][act]
        )
        sentence_template = forms["sentence_templates"][0]
        text = sentence_template.format(
            content=content,
            predicate=predicate,
        )
        quote_tokens = tuple(
            token
            for pair in STEP11_SURFACE_CATALOG["layout"]["quote_pairs"]
            for token in (pair["open"], pair["close"])
        )
        if any(token in text for token in quote_tokens):
            raise Step11NaturalSurfaceError(
                "STEP11_RECEPTION_LITERAL_FORBIDDEN"
            )
        return _Step11OwnedReceptionLine(
            text=text,
            binding_ids=line.binding_ids,
            reception_obligation_ids=line.reception_obligation_ids,
            antecedent_obligation_ids=line.antecedent_obligation_ids,
            supporting_obligation_ids=line.supporting_obligation_ids,
            visible_reference_ordinals=line.visible_reference_ordinals,
            antecedent_observation_line_indices=(
                line.antecedent_observation_line_indices
            ),
            literal_anchor_ids=line.literal_anchor_ids,
            reception_act=act,
            reception_scope=scope,
            realization_status=status,
            typed_placeholders=line.typed_placeholders,
        )

    return tuple(render_final_line(line) for line in lines)


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
    """Recompute the committed rc0026 plan from semantic ownership only."""

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
                    original_index,
                    min(introduced or used or (10**6,)),
                    min(
                        observation_group_index[group_id]
                        for group_id in lineage
                    ),
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
                    original_index,
                    min(introduced or used or (10**6,)),
                    min(group_index[row] for row in lineage),
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
        visible_source_anchor_count=(
            1 if ast.visible_source_anchor_use is not None else 0
        ),
        source_anchor_reason_codes=(
            (ast.visible_source_anchor_use.reason_code,)
            if ast.visible_source_anchor_use is not None
            else ()
        ),
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


# ---------------------------------------------------------------------------
# rc0028 experiment-only additive surface
#
# Keep every rc0027 definition above byte-for-byte stable.  The types and
# functions below are reached only from the disconnected rc0028 adapter.
# Successor and delta-catalog imports stay local so importing the shared
# rc0027 runtime cannot load the experiment authority transitively.

STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID = "nls_v3_rc_0028_experiment"
STEP11_RC0028_EXPERIMENT_RENDERED_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0028_experiment_rendered_surface.v1"
)
STEP11_RC0028_EXPERIMENT_CANDIDATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0028_experiment_candidate.v1"
)


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentConstructionRoleAtom:
    construction_slot_id: str
    lexical_role_kind: str
    construction_position: str
    role_position_atom_code: str
    role_position_surface_token: str
    target_owner_ordinals: tuple[int, ...]
    participation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentConstructionAtom:
    ordinal: int
    construction_instance_id: str
    construction_code: str
    catalog_atom_code: str
    surface_token: str
    construction_slot_ids: tuple[str, ...]
    role_atoms: tuple[Step11Rc0028ExperimentConstructionRoleAtom, ...]


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentRelationAtom:
    ordinal: int
    experiment_relation_id: str
    source_relation_id: str
    source_relation_type: str
    effective_relation_type: str
    from_owner_ordinal: int
    to_owner_ordinal: int
    direction: str
    authority_basis: str
    source_retention: str
    experiment_retention: str
    refines_source_relation_id: str | None


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentSemanticLinkAtom:
    ordinal: int
    source_semantic_link_id: str
    relation_type: str
    from_owner_ordinal: int
    to_owner_ordinal: int
    direction: str
    required: bool


@dataclass(frozen=True, slots=True)
class Step11Rc0028ExperimentExplicitUnknownAtom:
    ordinal: int
    source_unknown_id: str
    dimension: str
    affected_owner_ordinals: tuple[int, ...]
    required: bool


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0028ExperimentRenderedSurface:
    schema_version: str
    utf8_bytes: bytes
    sha256: str
    added_construction_line_count: int
    added_relation_line_count: int
    added_semantic_link_line_count: int
    added_explicit_unknown_line_count: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0028ExperimentSurfaceCandidate:
    schema_version: str
    candidate_version_id: str
    candidate_id: str
    base_candidate: Step11NaturalSurfaceCandidate
    rendered_surface: Step11Rc0028ExperimentRenderedSurface
    successor_snapshot_sha256: str
    lexical_atom_specs_sha256: str
    experiment_catalog_sha256: str
    owner_registry: tuple[str, ...]
    construction_atoms: tuple[Step11Rc0028ExperimentConstructionAtom, ...]
    relation_atoms: tuple[Step11Rc0028ExperimentRelationAtom, ...]
    semantic_link_atoms: tuple[Step11Rc0028ExperimentSemanticLinkAtom, ...]
    explicit_unknown_atoms: tuple[Step11Rc0028ExperimentExplicitUnknownAtom, ...]
    semantic_coverage_authorized: bool
    replan_count: int
    experimental_only: bool = True
    runtime_connected: bool = False

    @property
    def final_utf8_bytes(self) -> bytes:
        return self.rendered_surface.utf8_bytes


def _step11_rc0028_catalog() -> tuple[dict[str, Any], str]:
    from emlis_ai_step11_rc0028_experiment_surface_catalog_v3 import (
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG,
        STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256,
        validate_step11_rc0028_experiment_surface_catalog,
    )

    catalog = STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG
    issues = validate_step11_rc0028_experiment_surface_catalog(catalog)
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    return catalog, STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256


def _step11_rc0028_validate_lexical_specs(
    value: Any,
    *,
    successor_snapshot: Any,
) -> str:
    from emlis_ai_step11_grounded_lexicalization_v3 import (
        Step11Rc0028ExperimentLexicalAtomSpecs,
        validate_step11_rc0028_experiment_lexical_atom_specs,
    )

    if type(value) is not Step11Rc0028ExperimentLexicalAtomSpecs:
        raise Step11NaturalSurfaceError("STEP11_RC0028_LEXICAL_SPEC_INVALID")
    issues = validate_step11_rc0028_experiment_lexical_atom_specs(
        value,
        successor_snapshot=successor_snapshot,
    )
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    return value.specs_sha256


def _step11_rc0028_owner_registry(lexical_atom_specs: Any) -> tuple[str, ...]:
    return tuple(
        str(row.source_owner_id) for row in lexical_atom_specs.owner_bindings
    )


def _step11_rc0028_forward_atoms(
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    catalog: Mapping[str, Any],
) -> tuple[
    tuple[str, ...],
    tuple[Step11Rc0028ExperimentConstructionAtom, ...],
    tuple[Step11Rc0028ExperimentRelationAtom, ...],
    tuple[Step11Rc0028ExperimentSemanticLinkAtom, ...],
    tuple[Step11Rc0028ExperimentExplicitUnknownAtom, ...],
]:
    witness = successor_snapshot.lexical_role_witness
    owner_registry = _step11_rc0028_owner_registry(lexical_atom_specs)
    owner_ordinal = {
        owner_id: index + 1 for index, owner_id in enumerate(owner_registry)
    }
    atom_codes = catalog.get("construction_atom_codes", {})
    surface_tokens = catalog.get("construction_surface_tokens", {})
    construction_by_slot = {
        str(row.construction_slot_id): row
        for row in lexical_atom_specs.construction_atoms
    }
    constructions: list[Step11Rc0028ExperimentConstructionAtom] = []
    for index, row in enumerate(lexical_atom_specs.construction_instances, 1):
        code = str(row.construction_code)
        atom_code = atom_codes.get(code)
        token = surface_tokens.get(code)
        if type(atom_code) is not str or not atom_code or type(token) is not str or not token:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH"
            )
        role_atoms: list[Step11Rc0028ExperimentConstructionRoleAtom] = []
        for slot_id in row.slot_ids:
            slot = construction_by_slot.get(str(slot_id))
            if slot is None:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH"
                )
            if not slot.target_owner_ordinals:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0028_PARTICIPATION_OWNER_MISMATCH"
                )
            role_atoms.append(
                Step11Rc0028ExperimentConstructionRoleAtom(
                    construction_slot_id=str(slot.construction_slot_id),
                    lexical_role_kind=str(slot.lexical_role_kind),
                    construction_position=str(slot.construction_position),
                    role_position_atom_code=str(slot.role_position_atom_code),
                    role_position_surface_token=str(
                        slot.role_position_surface_token
                    ),
                    target_owner_ordinals=tuple(
                        int(value) for value in slot.target_owner_ordinals
                    ),
                    participation_ids=tuple(
                        str(value) for value in slot.participation_ids
                    ),
                )
            )
        constructions.append(
            Step11Rc0028ExperimentConstructionAtom(
                ordinal=index,
                construction_instance_id=str(row.construction_instance_id),
                construction_code=code,
                catalog_atom_code=atom_code,
                surface_token=token,
                construction_slot_ids=tuple(str(value) for value in row.slot_ids),
                role_atoms=tuple(role_atoms),
            )
        )

    relations: list[Step11Rc0028ExperimentRelationAtom] = []
    for index, row in enumerate(witness.relation_authorities, 1):
        try:
            from_ordinal = owner_ordinal[str(row.from_source_owner_id)]
            to_ordinal = owner_ordinal[str(row.to_source_owner_id)]
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0028_RELATION_ENDPOINT_MISMATCH"
            ) from exc
        relations.append(
            Step11Rc0028ExperimentRelationAtom(
                ordinal=index,
                experiment_relation_id=str(row.experiment_relation_id),
                source_relation_id=str(row.source_relation_id),
                source_relation_type=str(row.source_relation_type),
                effective_relation_type=str(row.effective_relation_type),
                from_owner_ordinal=from_ordinal,
                to_owner_ordinal=to_ordinal,
                direction=str(row.direction),
                authority_basis=str(row.authority_basis),
                source_retention=str(row.source_retention),
                experiment_retention=str(row.experiment_retention),
                refines_source_relation_id=(
                    None
                    if row.refines_source_relation_id is None
                    else str(row.refines_source_relation_id)
                ),
            )
        )

    links: list[Step11Rc0028ExperimentSemanticLinkAtom] = []
    for index, row in enumerate(witness.semantic_link_bindings, 1):
        try:
            from_ordinal = owner_ordinal[str(row.from_semantic_unit_id)]
            to_ordinal = owner_ordinal[str(row.to_semantic_unit_id)]
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0028_SEMANTIC_LINK_ENDPOINT_MISMATCH"
            ) from exc
        links.append(
            Step11Rc0028ExperimentSemanticLinkAtom(
                ordinal=index,
                source_semantic_link_id=str(row.source_semantic_link_id),
                relation_type=str(row.relation_type),
                from_owner_ordinal=from_ordinal,
                to_owner_ordinal=to_ordinal,
                direction=str(row.direction),
                required=bool(row.required),
            )
        )

    unknowns: list[Step11Rc0028ExperimentExplicitUnknownAtom] = []
    for index, row in enumerate(witness.explicit_unknown_bindings, 1):
        try:
            ordinals = tuple(
                owner_ordinal[str(owner.owner_id)]
                for owner in row.affected_source_owners
            )
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0028_EXPLICIT_UNKNOWN_OWNER_MISMATCH"
            ) from exc
        unknowns.append(
            Step11Rc0028ExperimentExplicitUnknownAtom(
                ordinal=index,
                source_unknown_id=str(row.source_unknown_id),
                dimension=str(row.dimension),
                affected_owner_ordinals=ordinals,
                required=bool(row.required),
            )
        )
    return (
        owner_registry,
        tuple(constructions),
        tuple(relations),
        tuple(links),
        tuple(unknowns),
    )


def _step11_rc0028_catalog_token(
    catalog: Mapping[str, Any],
    registry_name: str,
    semantic_type: str,
    direction: str,
) -> str:
    registry = catalog.get(registry_name, {})
    if type(registry) is not dict:
        raise Step11NaturalSurfaceError("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
    key = semantic_type + ":" + direction
    token = registry.get(key, registry.get(semantic_type))
    if type(token) is not str or not token:
        raise Step11NaturalSurfaceError("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
    return token


def _step11_rc0028_owner_token(
    catalog: Mapping[str, Any], ordinal: int
) -> str:
    registry = catalog.get("owner_ordinal_tokens", {})
    token = registry.get(str(ordinal)) if type(registry) is dict else None
    if type(token) is not str or not token:
        raise Step11NaturalSurfaceError("STEP11_RC0028_RESOURCE_BOUND_EXCEEDED")
    return token


def _step11_rc0028_structure_lines(
    *,
    catalog: Mapping[str, Any],
    constructions: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relations: Sequence[Step11Rc0028ExperimentRelationAtom],
    links: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    unknowns: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
) -> tuple[str, ...]:
    morphology = catalog.get("line_morphology", {})
    if type(morphology) is not dict:
        raise Step11NaturalSurfaceError("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
    required_morphology = (
        "atom_separator",
        "clause_separator",
        "construction_open",
        "construction_prefix",
        "construction_suffix",
        "owner_noun",
        "owner_possessive",
        "owner_separator",
        "relation_from_to_separator",
        "relation_suffix",
        "relation_to_suffix",
        "semantic_link_between",
        "semantic_link_join",
        "semantic_link_suffix",
        "unknown_owner_suffix",
        "unknown_prefix",
        "unknown_suffix",
    )
    if any(
        type(morphology.get(key)) is not str or not morphology.get(key)
        for key in required_morphology
    ):
        raise Step11NaturalSurfaceError("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
    separator = morphology["atom_separator"]
    clause_separator = morphology["clause_separator"]
    owner_noun = morphology["owner_noun"]
    owner_possessive = morphology["owner_possessive"]
    from_to = morphology["relation_from_to_separator"]
    relation_suffix = morphology["relation_suffix"]

    lines: list[str] = []
    for row in constructions:
        visible_roles: list[str] = []
        for role in row.role_atoms:
            visible_roles.extend(
                _step11_rc0028_owner_token(catalog, ordinal)
                + owner_noun
                + owner_possessive
                + role.role_position_surface_token
                for ordinal in role.target_owner_ordinals
            )
        lines.append(
            morphology["construction_prefix"]
            + clause_separator
            + row.surface_token
            + morphology["construction_open"]
            + clause_separator
            + clause_separator.join(visible_roles)
            + morphology["construction_suffix"]
        )
    for row in relations:
        left = _step11_rc0028_owner_token(catalog, row.from_owner_ordinal)
        right = _step11_rc0028_owner_token(catalog, row.to_owner_ordinal)
        token = _step11_rc0028_catalog_token(
            catalog,
            "relation_surface_tokens",
            row.effective_relation_type,
            row.direction,
        )
        lines.append(
            left
            + owner_noun
            + from_to
            + right
            + owner_noun
            + morphology["relation_to_suffix"]
            + clause_separator
            + token
            + relation_suffix
        )
    for row in links:
        left = _step11_rc0028_owner_token(catalog, row.from_owner_ordinal)
        right = _step11_rc0028_owner_token(catalog, row.to_owner_ordinal)
        token = _step11_rc0028_catalog_token(
            catalog,
            "semantic_link_surface_tokens",
            row.relation_type,
            row.direction,
        )
        lines.append(
            left
            + owner_noun
            + morphology["semantic_link_join"]
            + right
            + owner_noun
            + morphology["semantic_link_between"]
            + clause_separator
            + token
            + morphology["semantic_link_suffix"]
        )
    registry = catalog.get("unknown_surface_tokens", {})
    if type(registry) is not dict:
        raise Step11NaturalSurfaceError("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
    for row in unknowns:
        dimension = registry.get(row.dimension)
        if type(dimension) is not str or not dimension:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0028_CATALOG_TOKEN_MISMATCH"
            )
        owner_text = morphology["owner_separator"].join(
            _step11_rc0028_owner_token(catalog, ordinal) + owner_noun
            for ordinal in row.affected_owner_ordinals
        )
        lines.append(
            morphology["unknown_prefix"]
            + clause_separator
            + owner_text
            + morphology["unknown_owner_suffix"]
            + clause_separator
            + dimension
            + morphology["unknown_suffix"]
        )
    if any(not line or "\n" in line or "\r" in line for line in lines):
        raise Step11NaturalSurfaceError("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
    return tuple(lines)


def render_step11_rc0028_experiment_surface(
    base_utf8_bytes: bytes,
    *,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom] = (),
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom] = (),
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom] = (),
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom] = (),
) -> Step11Rc0028ExperimentRenderedSurface:
    if type(base_utf8_bytes) is not bytes or not base_utf8_bytes:
        raise Step11NaturalSurfaceError("STEP11_RC0028_BASE_SURFACE_INVALID")
    try:
        text = base_utf8_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11NaturalSurfaceError("STEP11_RC0028_BASE_SURFACE_INVALID") from exc
    marker = "\n\nEmlisから：\n"
    if not text.startswith("見えたこと：\n") or text.count(marker) != 1:
        raise Step11NaturalSurfaceError("STEP11_RC0028_BASE_SURFACE_INVALID")
    catalog, _catalog_sha256 = _step11_rc0028_catalog()
    lines = _step11_rc0028_structure_lines(
        catalog=catalog,
        constructions=construction_atoms,
        relations=relation_atoms,
        links=semantic_link_atoms,
        unknowns=explicit_unknown_atoms,
    )
    if lines:
        observation, reception = text.split(marker, 1)
        text = observation + "\n" + "\n".join(lines) + marker + reception
    body = text.encode("utf-8", errors="strict")
    return Step11Rc0028ExperimentRenderedSurface(
        schema_version=STEP11_RC0028_EXPERIMENT_RENDERED_SCHEMA,
        utf8_bytes=body,
        sha256=hashlib.sha256(body).hexdigest(),
        added_construction_line_count=len(construction_atoms),
        added_relation_line_count=len(relation_atoms),
        added_semantic_link_line_count=len(semantic_link_atoms),
        added_explicit_unknown_line_count=len(explicit_unknown_atoms),
    )


def _step11_rc0028_candidate_identity(
    *,
    base_candidate_id: str,
    rendered: Step11Rc0028ExperimentRenderedSurface,
    successor_snapshot_sha256: str,
    lexical_atom_specs_sha256: str,
    catalog_sha256: str,
) -> str:
    return "nls3s11rc0028cand_" + artifact_sha256(
        {
            "candidate_version_id": STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID,
            "base_candidate_id": base_candidate_id,
            "final_bytes_sha256": rendered.sha256,
            "successor_snapshot_sha256": successor_snapshot_sha256,
            "lexical_atom_specs_sha256": lexical_atom_specs_sha256,
            "catalog_sha256": catalog_sha256,
        }
    )[:20]


def build_step11_rc0028_experiment_surface_candidate(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> Step11Rc0028ExperimentSurfaceCandidate:
    successor_owner = __import__(
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        fromlist=(
            "GroundedLexicalRoleExperimentSnapshotSuccessor",
            "validate_grounded_lexical_role_experiment_snapshot_successor",
        ),
    )
    GroundedLexicalRoleExperimentSnapshotSuccessor = (
        successor_owner.GroundedLexicalRoleExperimentSnapshotSuccessor
    )
    validate_grounded_lexical_role_experiment_snapshot_successor = (
        successor_owner.validate_grounded_lexical_role_experiment_snapshot_successor
    )

    if type(base_candidate) is not Step11NaturalSurfaceCandidate:
        raise Step11NaturalSurfaceError("STEP11_RC0028_BASE_CANDIDATE_INVALID")
    if type(successor_snapshot) is not GroundedLexicalRoleExperimentSnapshotSuccessor:
        raise Step11NaturalSurfaceError("STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH")
    issues = validate_grounded_lexical_role_experiment_snapshot_successor(
        successor_snapshot
    )
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    if (
        type(successor_snapshot.semantic_coverage_authorized) is not bool
        or successor_snapshot.semantic_coverage_authorized is not False
        or successor_snapshot.runtime_connected is not False
        or successor_snapshot.experimental_only is not True
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM"
        )
    lexical_sha256 = _step11_rc0028_validate_lexical_specs(
        lexical_atom_specs,
        successor_snapshot=successor_snapshot,
    )
    catalog, catalog_sha256 = _step11_rc0028_catalog()
    owner_registry, constructions, relations, links, unknowns = (
        _step11_rc0028_forward_atoms(
            successor_snapshot,
            lexical_atom_specs,
            catalog,
        )
    )
    rendered = render_step11_rc0028_experiment_surface(
        base_candidate.final_utf8_bytes,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
    )
    candidate = Step11Rc0028ExperimentSurfaceCandidate(
        schema_version=STEP11_RC0028_EXPERIMENT_CANDIDATE_SCHEMA,
        candidate_version_id=STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID,
        candidate_id=_step11_rc0028_candidate_identity(
            base_candidate_id=base_candidate.candidate_id,
            rendered=rendered,
            successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
            lexical_atom_specs_sha256=lexical_sha256,
            catalog_sha256=catalog_sha256,
        ),
        base_candidate=base_candidate,
        rendered_surface=rendered,
        successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
        lexical_atom_specs_sha256=lexical_sha256,
        experiment_catalog_sha256=catalog_sha256,
        owner_registry=owner_registry,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        semantic_coverage_authorized=False,
        replan_count=0,
    )
    candidate_issues = validate_step11_rc0028_experiment_surface_candidate(
        candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    if candidate_issues:
        raise Step11NaturalSurfaceError(candidate_issues[0])
    return candidate


def build_step11_rc0028_experiment_surface_candidates(
    base_candidates: Sequence[Step11NaturalSurfaceCandidate],
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[Step11Rc0028ExperimentSurfaceCandidate, ...]:
    if (
        type(base_candidates) not in {tuple, list}
        or not base_candidates
        or len(base_candidates) > 12
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH"
        )
    return tuple(
        build_step11_rc0028_experiment_surface_candidate(
            row,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        for row in base_candidates
    )


def validate_step11_rc0028_experiment_surface_candidate(
    value: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0028ExperimentSurfaceCandidate:
        return ("STEP11_RC0028_CANDIDATE_TYPE_INVALID",)
    issues: set[str] = set()
    if value.schema_version != STEP11_RC0028_EXPERIMENT_CANDIDATE_SCHEMA:
        issues.add("STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH")
    if value.candidate_version_id != STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID:
        issues.add("STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH")
    if type(value.base_candidate) is not Step11NaturalSurfaceCandidate:
        issues.add("STEP11_RC0028_BASE_CANDIDATE_INVALID")
        return tuple(sorted(issues))
    try:
        catalog, catalog_sha256 = _step11_rc0028_catalog()
        lexical_sha256 = _step11_rc0028_validate_lexical_specs(
            lexical_atom_specs,
            successor_snapshot=successor_snapshot,
        )
        owner_registry, constructions, relations, links, unknowns = (
            _step11_rc0028_forward_atoms(
                successor_snapshot,
                lexical_atom_specs,
                catalog,
            )
        )
        rendered = render_step11_rc0028_experiment_surface(
            value.base_candidate.final_utf8_bytes,
            construction_atoms=constructions,
            relation_atoms=relations,
            semantic_link_atoms=links,
            explicit_unknown_atoms=unknowns,
        )
        expected_id = _step11_rc0028_candidate_identity(
            base_candidate_id=value.base_candidate.candidate_id,
            rendered=rendered,
            successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
            lexical_atom_specs_sha256=lexical_sha256,
            catalog_sha256=catalog_sha256,
        )
    except (AttributeError, KeyError, TypeError, ValueError, Step11NaturalSurfaceError):
        issues.add("STEP11_RC0028_CANDIDATE_REVALIDATION_FAILED")
        return tuple(sorted(issues))
    if value.rendered_surface != rendered:
        issues.add("STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH")
    if value.owner_registry != owner_registry:
        issues.add("STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH")
    if value.construction_atoms != constructions:
        issues.add("STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH")
    if value.relation_atoms != relations:
        issues.add("STEP11_RC0028_RELATION_ENDPOINT_MISMATCH")
    if value.semantic_link_atoms != links:
        issues.add("STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH")
    if value.explicit_unknown_atoms != unknowns:
        issues.add("STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH")
    if value.successor_snapshot_sha256 != successor_snapshot.experiment_snapshot_sha256:
        issues.add("STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH")
    if value.lexical_atom_specs_sha256 != lexical_sha256:
        issues.add("STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH")
    if value.experiment_catalog_sha256 != catalog_sha256:
        issues.add("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
    if value.candidate_id != expected_id:
        issues.add("STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH")
    if type(value.semantic_coverage_authorized) is not bool or value.semantic_coverage_authorized:
        issues.add("STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM")
    if type(value.replan_count) is not int or type(value.replan_count) is bool or not 0 <= value.replan_count <= 1:
        issues.add("STEP11_RC0028_REPLAN_BOUND_EXCEEDED")
    if value.experimental_only is not True or value.runtime_connected is not False:
        issues.add("STEP11_RC0028_RUNTIME_BOUNDARY_INVALID")
    return tuple(sorted(issues))


__all__ += [
    "STEP11_RC0028_EXPERIMENT_CANDIDATE_SCHEMA",
    "STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID",
    "STEP11_RC0028_EXPERIMENT_RENDERED_SCHEMA",
    "Step11Rc0028ExperimentConstructionAtom",
    "Step11Rc0028ExperimentConstructionRoleAtom",
    "Step11Rc0028ExperimentExplicitUnknownAtom",
    "Step11Rc0028ExperimentRelationAtom",
    "Step11Rc0028ExperimentRenderedSurface",
    "Step11Rc0028ExperimentSemanticLinkAtom",
    "Step11Rc0028ExperimentSurfaceCandidate",
    "build_step11_rc0028_experiment_surface_candidate",
    "build_step11_rc0028_experiment_surface_candidates",
    "render_step11_rc0028_experiment_surface",
    "validate_step11_rc0028_experiment_surface_candidate",
]


# ---------------------------------------------------------------------------
# rc0029 experiment-only common-Surface repair (append-only)
# ---------------------------------------------------------------------------

STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID = "nls_v3_rc_0029_experiment"
STEP11_RC0029_EXPERIMENT_RENDERED_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0029_experiment_rendered_surface.v1"
)
STEP11_RC0029_EXPERIMENT_CANDIDATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_rc0029_experiment_candidate.v1"
)


@dataclass(frozen=True, slots=True)
class Step11Rc0029ExperimentFusedStructureGroup:
    component_ordinal: int
    owner_ordinals: tuple[int, ...]
    typed_atom_keys: tuple[str, ...]
    typed_atom_count: int


@dataclass(frozen=True, slots=True)
class Step11Rc0029ExperimentReceptionBinding:
    reception_line_ordinal: int
    source_base_binding_id: str | None
    source_reception_opportunity_id: str
    reception_act: str
    source_target_owner_ids: tuple[str, ...]
    supporting_source_owner_ids: tuple[str, ...]
    target_handle_texts: tuple[str, ...]
    supporting_handle_texts: tuple[str, ...]
    additional_clause: bool


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentRenderedSurface:
    schema_version: str
    utf8_bytes: bytes
    sha256: str
    added_observation_line_count: int
    fused_structure_item_count: int
    fused_structure_group_count: int
    reception_binding_count: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0029ExperimentSurfaceCandidate:
    schema_version: str
    candidate_version_id: str
    candidate_id: str
    base_candidate: Step11NaturalSurfaceCandidate
    rendered_surface: Step11Rc0029ExperimentRenderedSurface
    successor_snapshot_sha256: str
    lexical_atom_specs_sha256: str
    experiment_catalog_sha256: str
    natural_handle_specs: Any
    owner_registry: tuple[str, ...]
    construction_atoms: tuple[Step11Rc0028ExperimentConstructionAtom, ...]
    relation_atoms: tuple[Step11Rc0028ExperimentRelationAtom, ...]
    semantic_link_atoms: tuple[Step11Rc0028ExperimentSemanticLinkAtom, ...]
    explicit_unknown_atoms: tuple[Step11Rc0028ExperimentExplicitUnknownAtom, ...]
    fused_structure_groups: tuple[
        Step11Rc0029ExperimentFusedStructureGroup, ...
    ]
    reception_bindings: tuple[Step11Rc0029ExperimentReceptionBinding, ...]
    semantic_coverage_authorized: bool
    replan_count: int
    experimental_only: bool = True
    private_body_full: bool = True
    shareable: bool = False
    runtime_connected: bool = False

    @property
    def final_utf8_bytes(self) -> bytes:
        return self.rendered_surface.utf8_bytes


def _step11_rc0029_catalog() -> tuple[dict[str, Any], str]:
    catalog_owner = __import__(
        "emlis_ai_step11_rc0029_experiment_surface_catalog_v3",
        fromlist=(
            "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG",
            "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256",
            "validate_step11_rc0029_experiment_surface_catalog",
        ),
    )
    catalog = catalog_owner.STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG
    issues = catalog_owner.validate_step11_rc0029_experiment_surface_catalog(
        catalog
    )
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    return (
        catalog,
        catalog_owner.STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256,
    )


def _step11_rc0029_handle_maps(
    natural_handle_specs: Any,
) -> tuple[dict[int, Any], dict[str, Any]]:
    lexical_owner = __import__(
        "emlis_ai_step11_grounded_lexicalization_v3",
        fromlist=("Step11Rc0029NaturalHandleSpecs",),
    )
    if type(natural_handle_specs) is not lexical_owner.Step11Rc0029NaturalHandleSpecs:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_SPECS_INVALID"
        )
    by_ordinal = {
        row.source_owner_ordinal: row for row in natural_handle_specs.handles
    }
    by_id = {row.source_owner_id: row for row in natural_handle_specs.handles}
    if (
        len(by_ordinal) != len(natural_handle_specs.handles)
        or len(by_id) != len(natural_handle_specs.handles)
        or len({row.handle_text for row in natural_handle_specs.handles})
        != len(natural_handle_specs.handles)
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_COLLISION"
        )
    return by_ordinal, by_id


def _step11_rc0029_construction_owner_ordinal(
    row: Step11Rc0028ExperimentConstructionAtom,
) -> int:
    owner_ordinals: list[int] = []
    for role in row.role_atoms:
        if len(role.target_owner_ordinals) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_CONSTRUCTION_OWNER_AMBIGUOUS"
            )
        owner_ordinals.append(role.target_owner_ordinals[0])
    if not owner_ordinals or len(set(owner_ordinals)) != 1:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_CONSTRUCTION_OWNER_AMBIGUOUS"
        )
    return owner_ordinals[0]


def _step11_rc0029_owner_semantic_key(row: Any) -> tuple[Any, ...]:
    return (
        row.semantic_head_text,
        row.role_qualifier_tokens,
        row.handle_text,
    )


def _step11_rc0029_fused_groups(
    *,
    natural_handle_specs: Any,
    constructions: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relations: Sequence[Step11Rc0028ExperimentRelationAtom],
    links: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    unknowns: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    receptions: Sequence[Step11Rc0029ExperimentReceptionBinding],
) -> tuple[Step11Rc0029ExperimentFusedStructureGroup, ...]:
    by_ordinal, by_id = _step11_rc0029_handle_maps(natural_handle_specs)
    parent: dict[int, int] = {}
    typed_by_owner: dict[int, set[str]] = {}

    def add_atom(key: str, owner_ordinals: Sequence[int]) -> None:
        if not owner_ordinals or any(
            ordinal not in by_ordinal for ordinal in owner_ordinals
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_COMPONENT_OWNER_UNRESOLVED"
            )
        if key in {
            existing
            for keys in typed_by_owner.values()
            for existing in keys
        }:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_COMPONENT_ATOM_KEY_COLLISION"
            )
        unique = tuple(dict.fromkeys(owner_ordinals))
        for ordinal in unique:
            parent.setdefault(ordinal, ordinal)

        def find(ordinal: int) -> int:
            while parent[ordinal] != ordinal:
                parent[ordinal] = parent[parent[ordinal]]
                ordinal = parent[ordinal]
            return ordinal

        anchor = unique[0]
        for ordinal in unique[1:]:
            left = find(anchor)
            right = find(ordinal)
            if left != right:
                parent[right] = left
        for ordinal in unique:
            typed_by_owner.setdefault(ordinal, set()).add(key)

    for row in constructions:
        add_atom(
            "construction:" + row.construction_instance_id,
            (_step11_rc0029_construction_owner_ordinal(row),),
        )
    for row in relations:
        add_atom(
            "relation:" + row.experiment_relation_id,
            (row.from_owner_ordinal, row.to_owner_ordinal),
        )
    for row in links:
        add_atom(
            "semantic_link:" + row.source_semantic_link_id,
            (row.from_owner_ordinal, row.to_owner_ordinal),
        )
    for row in unknowns:
        add_atom(
            "explicit_unknown:" + row.source_unknown_id,
            row.affected_owner_ordinals,
        )
    for row in receptions:
        try:
            reception_owner_ordinals = tuple(
                by_id[owner_id].source_owner_ordinal
                for owner_id in dict.fromkeys(
                    (
                        *row.source_target_owner_ids,
                        *row.supporting_source_owner_ids,
                    )
                )
            )
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_COMPONENT_OWNER_UNRESOLVED"
            ) from exc
        add_atom(
            "reception:" + row.source_reception_opportunity_id,
            reception_owner_ordinals,
        )
    if not parent:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_COMPONENT_SET_EMPTY"
        )

    def root(ordinal: int) -> int:
        while parent[ordinal] != ordinal:
            parent[ordinal] = parent[parent[ordinal]]
            ordinal = parent[ordinal]
        return ordinal

    owners_by_root: dict[int, set[int]] = {}
    atom_keys_by_root: dict[int, set[str]] = {}
    for ordinal in parent:
        component_root = root(ordinal)
        owners_by_root.setdefault(component_root, set()).add(ordinal)
        atom_keys_by_root.setdefault(component_root, set()).update(
            typed_by_owner.get(ordinal, set())
        )
    prepared: list[tuple[tuple[Any, ...], tuple[int, ...], tuple[str, ...]]] = []
    for component_root, owner_set in owners_by_root.items():
        owner_ordinals = tuple(
            sorted(
                owner_set,
                key=lambda ordinal: _step11_rc0029_owner_semantic_key(
                    by_ordinal[ordinal]
                ),
            )
        )
        semantic_key = tuple(
            _step11_rc0029_owner_semantic_key(by_ordinal[ordinal])
            for ordinal in owner_ordinals
        )
        prepared.append(
            (
                semantic_key,
                owner_ordinals,
                tuple(sorted(atom_keys_by_root[component_root])),
            )
        )
    prepared.sort(key=lambda row: row[0])
    return tuple(
        Step11Rc0029ExperimentFusedStructureGroup(
            component_ordinal=index,
            owner_ordinals=owner_ordinals,
            typed_atom_keys=typed_atom_keys,
            typed_atom_count=len(typed_atom_keys),
        )
        for index, (_key, owner_ordinals, typed_atom_keys) in enumerate(
            prepared,
            start=1,
        )
    )


def _step11_rc0029_reception_bindings(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    natural_handle_specs: Any,
) -> tuple[Step11Rc0029ExperimentReceptionBinding, ...]:
    _by_ordinal, handle_by_id = _step11_rc0029_handle_maps(
        natural_handle_specs
    )
    nuclei = tuple(successor_snapshot.base_snapshot.nuclei)
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    if len(actual_by_source) != len(nuclei):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_RECEPTION_SOURCE_OWNER_INVALID"
        )

    def actual_ids(source_ids: Sequence[str]) -> tuple[str, ...]:
        try:
            return tuple(
                actual_by_source[str(source_id)] for source_id in source_ids
            )
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_RECEPTION_SOURCE_OWNER_INVALID"
            ) from exc

    base_bindings = tuple(
        base_candidate.surface_ast.reception_antecedent_bindings
    )
    line_binding_by_opportunity: dict[str, tuple[int, Any]] = {}
    for line_ordinal, binding in enumerate(base_bindings, start=1):
        for opportunity_id in binding.source_reception_opportunity_ids:
            key = str(opportunity_id)
            if key in line_binding_by_opportunity:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0029_RECEPTION_LINE_ASSOCIATION_AMBIGUOUS"
                )
            line_binding_by_opportunity[key] = (line_ordinal, binding)
    required_opportunities = tuple(
        row
        for row in successor_snapshot.base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    if not required_opportunities or not base_bindings:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_RECEPTION_BINDING_REQUIRED"
        )
    rows: list[Step11Rc0029ExperimentReceptionBinding] = []
    for opportunity in required_opportunities:
        opportunity_id = str(opportunity.source_id)
        association = line_binding_by_opportunity.get(opportunity_id)
        if association is None:
            if len(base_bindings) != 1:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0029_RECEPTION_LINE_ASSOCIATION_UNRESOLVED"
                )
            line_ordinal = 1
            source_base_binding_id = None
            additional_clause = True
        else:
            line_ordinal, binding = association
            if str(opportunity.reception_act) not in {
                str(item) for item in binding.allowed_response_acts
            }:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0029_RECEPTION_ACT_ASSOCIATION_MISMATCH"
                )
            source_base_binding_id = str(binding.binding_id)
            additional_clause = False
        target_ids = actual_ids(opportunity.target_nucleus_ids)
        support_ids = actual_ids(opportunity.support_nucleus_ids)
        if (
            not target_ids
            or any(
                owner_id not in handle_by_id
                for owner_id in (*target_ids, *support_ids)
            )
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_RECEPTION_SOURCE_OWNER_INVALID"
            )
        rows.append(
            Step11Rc0029ExperimentReceptionBinding(
                reception_line_ordinal=line_ordinal,
                source_base_binding_id=source_base_binding_id,
                source_reception_opportunity_id=opportunity_id,
                reception_act=str(opportunity.reception_act),
                source_target_owner_ids=target_ids,
                supporting_source_owner_ids=support_ids,
                target_handle_texts=tuple(
                    handle_by_id[owner_id].handle_text
                    for owner_id in target_ids
                ),
                supporting_handle_texts=tuple(
                    handle_by_id[owner_id].handle_text
                    for owner_id in support_ids
                ),
                additional_clause=additional_clause,
            )
        )
    handle_key = {
        owner_id: _step11_rc0029_owner_semantic_key(handle_by_id[owner_id])
        for owner_id in handle_by_id
    }
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.reception_line_ordinal,
                row.additional_clause,
                tuple(handle_key[item] for item in row.source_target_owner_ids),
                tuple(
                    handle_key[item]
                    for item in row.supporting_source_owner_ids
                ),
                row.reception_act,
                row.source_reception_opportunity_id,
            ),
        )
    )


def _step11_rc0029_surface_family_clauses(
    *,
    catalog: Mapping[str, Any],
    natural_handle_specs: Any,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
) -> tuple[str, ...]:
    morphology = catalog["morphology"]
    handle_by_ordinal, _handle_by_id = _step11_rc0029_handle_maps(
        natural_handle_specs
    )

    def handle(ordinal: int) -> str:
        row = handle_by_ordinal.get(ordinal)
        if row is None:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_UNRESOLVED"
            )
        return (
            morphology["handle_open"]
            + row.handle_text
            + morphology["handle_close"]
        )

    family_clauses: list[str] = []
    construction_tokens = catalog["construction_surface_tokens"]
    construction_role_layouts = catalog["construction_role_layouts"]
    role_tokens = catalog["role_position_surface_tokens"]
    construction_token_rank = {
        token: index for index, token in enumerate(construction_tokens.values())
    }
    constructions_by_owner: dict[int, list[str]] = {}
    for row in construction_atoms:
        token = construction_tokens.get(row.construction_code)
        if token != row.surface_token:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_CONSTRUCTION_TOKEN_MISMATCH"
            )
        actual_role_layout = tuple(
            role.lexical_role_kind + ":" + role.construction_position
            for role in row.role_atoms
        )
        if tuple(
            construction_role_layouts.get(row.construction_code, ())
        ) != actual_role_layout:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_CONSTRUCTION_ROLE_MISMATCH"
            )
        for role in row.role_atoms:
            role_key = role.lexical_role_kind + ":" + role.construction_position
            role_token = role_tokens.get(role_key)
            if type(role_token) is not str or not role_token:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0029_CONSTRUCTION_ROLE_MISMATCH"
                )
        owner_ordinal = _step11_rc0029_construction_owner_ordinal(row)
        constructions_by_owner.setdefault(owner_ordinal, []).append(token)
    if constructions_by_owner:
        owner_ordinals = tuple(
            sorted(
                constructions_by_owner,
                key=lambda ordinal: _step11_rc0029_owner_semantic_key(
                    handle_by_ordinal[ordinal]
                ),
            )
        )
        construction_segments: list[str] = []
        for owner_ordinal in owner_ordinals:
            tokens = sorted(
                constructions_by_owner[owner_ordinal],
                key=lambda token: (
                    construction_token_rank.get(token, 10_000),
                    token,
                ),
            )
            construction_segments.append(
                handle(owner_ordinal)
                + morphology["construction_handle_link"]
                + morphology["construction_token_join"].join(tokens)
            )
        family_clauses.append(
            morphology["construction_owner_group_join"].join(
                construction_segments
            )
            + morphology["construction_suffix"]
        )

    relation_tokens = catalog["relation_surface_tokens"]
    relation_rows: list[tuple[Any, str]] = []
    for row in relation_atoms:
        token = relation_tokens.get(
            row.effective_relation_type + ":" + row.direction
        )
        if type(token) is not str:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_RELATION_TOKEN_MISMATCH"
            )
        if (
            row.from_owner_ordinal not in handle_by_ordinal
            or row.to_owner_ordinal not in handle_by_ordinal
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_NATURAL_HANDLE_UNRESOLVED"
            )
        relation_rows.append((row, token))

    def relation_key(item: tuple[Any, str]) -> tuple[Any, ...]:
        row, token = item
        return (
            _step11_rc0029_owner_semantic_key(
                handle_by_ordinal[row.from_owner_ordinal]
            ),
            _step11_rc0029_owner_semantic_key(
                handle_by_ordinal[row.to_owner_ordinal]
            ),
            token,
            row.effective_relation_type,
            row.direction,
            row.experiment_relation_id,
        )

    remaining = sorted(relation_rows, key=relation_key)
    relation_chains: list[list[tuple[Any, str]]] = []
    while remaining:
        target_ordinals = {item[0].to_owner_ordinal for item in remaining}
        starts = tuple(
            item
            for item in remaining
            if item[0].from_owner_ordinal not in target_ordinals
        )
        first = min(starts or tuple(remaining), key=relation_key)
        remaining.remove(first)
        chain = [first]
        current_to = first[0].to_owner_ordinal
        while True:
            continuations = tuple(
                item
                for item in remaining
                if item[0].from_owner_ordinal == current_to
            )
            if not continuations:
                break
            next_item = min(continuations, key=relation_key)
            remaining.remove(next_item)
            chain.append(next_item)
            current_to = next_item[0].to_owner_ordinal
        relation_chains.append(chain)
    if relation_chains:
        rendered_chains: list[str] = []
        for chain in relation_chains:
            first_row, first_token = chain[0]
            rendered_chain = (
                handle(first_row.from_owner_ordinal)
                + morphology["relation_from"]
                + handle(first_row.to_owner_ordinal)
                + morphology["relation_to"]
                + first_token
            )
            for continuation_row, continuation_token in chain[1:]:
                rendered_chain += (
                    morphology["relation_chain_step"]
                    + handle(continuation_row.to_owner_ordinal)
                    + morphology["relation_to"]
                    + continuation_token
                )
            rendered_chains.append(rendered_chain)
        family_clauses.append(
            morphology["relation_chain_join"].join(rendered_chains)
            + morphology["relation_suffix"]
        )

    link_tokens = catalog["semantic_link_surface_tokens"]
    rendered_links: list[tuple[tuple[Any, ...], str]] = []
    for row in semantic_link_atoms:
        token = link_tokens.get(row.relation_type + ":" + row.direction)
        if type(token) is not str:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_SEMANTIC_LINK_TOKEN_MISMATCH"
            )
        rendered = (
            handle(row.from_owner_ordinal)
            + morphology["link_handle_join"]
            + handle(row.to_owner_ordinal)
            + morphology["link_between"]
            + token
        )
        rendered_links.append(
            (
                (
                    _step11_rc0029_owner_semantic_key(
                        handle_by_ordinal[row.from_owner_ordinal]
                    ),
                    _step11_rc0029_owner_semantic_key(
                        handle_by_ordinal[row.to_owner_ordinal]
                    ),
                    token,
                    row.relation_type,
                    row.direction,
                    row.source_semantic_link_id,
                ),
                rendered,
            )
        )
    if rendered_links:
        family_clauses.append(
            morphology["link_item_join"].join(
                rendered for _key, rendered in sorted(rendered_links)
            )
            + morphology["link_suffix"]
        )

    unknown_tokens = catalog["unknown_surface_tokens"]
    rendered_unknowns: list[tuple[tuple[Any, ...], str]] = []
    for row in explicit_unknown_atoms:
        token = unknown_tokens.get(row.dimension)
        if type(token) is not str or not row.affected_owner_ordinals:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_EXPLICIT_UNKNOWN_TOKEN_MISMATCH"
            )
        rendered = (
            morphology["unknown_owner_join"].join(
                handle(ordinal) for ordinal in row.affected_owner_ordinals
            )
            + morphology["unknown_between"]
            + token
        )
        rendered_unknowns.append(
            (
                (
                    tuple(
                        _step11_rc0029_owner_semantic_key(
                            handle_by_ordinal[ordinal]
                        )
                        for ordinal in row.affected_owner_ordinals
                    ),
                    token,
                    row.dimension,
                    row.source_unknown_id,
                ),
                rendered,
            )
        )
    if rendered_unknowns:
        family_clauses.append(
            morphology["unknown_item_join"].join(
                rendered for _key, rendered in sorted(rendered_unknowns)
            )
            + morphology["unknown_suffix"]
        )
    if any(
        not item or "\n" in item or "\r" in item
        for item in family_clauses
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_FUSED_SURFACE_INVALID"
        )
    return tuple(family_clauses)


def render_step11_rc0029_experiment_surface(
    base_final_utf8_bytes: bytes,
    *,
    natural_handle_specs: Any,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    fused_structure_groups: Sequence[Step11Rc0029ExperimentFusedStructureGroup],
    reception_bindings: Sequence[Step11Rc0029ExperimentReceptionBinding],
) -> Step11Rc0029ExperimentRenderedSurface:
    if type(base_final_utf8_bytes) is not bytes or not base_final_utf8_bytes:
        raise Step11NaturalSurfaceError("STEP11_RC0029_BASE_SURFACE_INVALID")
    try:
        text = base_final_utf8_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_BASE_SURFACE_INVALID"
        ) from exc
    marker = "\n\nEmlisから：\n"
    if not text.startswith("見えたこと：\n") or text.count(marker) != 1:
        raise Step11NaturalSurfaceError("STEP11_RC0029_BASE_SURFACE_INVALID")
    catalog, _catalog_sha256 = _step11_rc0029_catalog()
    morphology = catalog["morphology"]
    family_clauses = _step11_rc0029_surface_family_clauses(
        catalog=catalog,
        natural_handle_specs=natural_handle_specs,
        construction_atoms=construction_atoms,
        relation_atoms=relation_atoms,
        semantic_link_atoms=semantic_link_atoms,
        explicit_unknown_atoms=explicit_unknown_atoms,
    )
    expected_groups = _step11_rc0029_fused_groups(
        natural_handle_specs=natural_handle_specs,
        constructions=construction_atoms,
        relations=relation_atoms,
        links=semantic_link_atoms,
        unknowns=explicit_unknown_atoms,
        receptions=reception_bindings,
    )
    if tuple(fused_structure_groups) != expected_groups:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_FUSED_GROUP_COMMITMENT_MISMATCH"
        )
    observation, reception = text.split(marker, 1)
    observation_lines = observation.split("\n")
    reception_lines = reception.split("\n")
    if (
        len(observation_lines) < 2
        or any(not line for line in observation_lines)
        or any(not line for line in reception_lines)
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_SURFACE_LAYOUT_INVALID"
        )
    if family_clauses:
        base_tail = observation_lines[-1].removesuffix("。")
        observation_lines[-1] = (
            base_tail
            + morphology["observation_insert"]
            + morphology["structural_prefix"]
            + morphology["family_join"].join(family_clauses)
            + "。"
        )
    _handle_by_ordinal, handle_by_id = _step11_rc0029_handle_maps(
        natural_handle_specs
    )
    act_tokens = catalog["reception_act_surface_tokens"]
    if (
        not reception_bindings
        or len(
            {
                row.source_reception_opportunity_id
                for row in reception_bindings
            }
        )
        != len(reception_bindings)
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_RECEPTION_BINDING_CARDINALITY_MISMATCH"
        )
    by_line: dict[int, list[Step11Rc0029ExperimentReceptionBinding]] = {}
    for binding in reception_bindings:
        if (
            not 1 <= binding.reception_line_ordinal <= len(reception_lines)
            or binding.reception_act not in act_tokens
            or not binding.source_target_owner_ids
            or binding.target_handle_texts
            != tuple(
                handle_by_id[owner_id].handle_text
                for owner_id in binding.source_target_owner_ids
                if owner_id in handle_by_id
            )
            or len(binding.target_handle_texts)
            != len(binding.source_target_owner_ids)
            or binding.supporting_handle_texts
            != tuple(
                handle_by_id[owner_id].handle_text
                for owner_id in binding.supporting_source_owner_ids
                if owner_id in handle_by_id
            )
            or len(binding.supporting_handle_texts)
            != len(binding.supporting_source_owner_ids)
            or binding.additional_clause
            != (binding.source_base_binding_id is None)
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_RECEPTION_BINDING_INVALID"
            )
        by_line.setdefault(binding.reception_line_ordinal, []).append(binding)

    def quoted_handles(values: Sequence[str], join_key: str) -> str:
        return morphology[join_key].join(
            morphology["handle_open"]
            + value
            + morphology["handle_close"]
            for value in values
        )

    def reception_prefix(
        binding: Step11Rc0029ExperimentReceptionBinding,
    ) -> str:
        support = ""
        if binding.supporting_handle_texts:
            support = (
                quoted_handles(
                    binding.supporting_handle_texts,
                    "reception_support_join",
                )
                + morphology["reception_support_suffix"]
            )
        return (
            support
            + quoted_handles(
                binding.target_handle_texts,
                "reception_target_join",
            )
            + morphology["reception_target_suffix"]
        )

    for line_ordinal, bindings in by_line.items():
        mapped = tuple(row for row in bindings if not row.additional_clause)
        additional = tuple(row for row in bindings if row.additional_clause)
        if len(mapped) > 1:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0029_RECEPTION_LINE_ASSOCIATION_AMBIGUOUS"
            )
        line = reception_lines[line_ordinal - 1]
        if mapped:
            line = reception_prefix(mapped[0]) + line
        if additional:
            if not line.endswith("。"):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0029_RECEPTION_SURFACE_INVALID"
                )
            line = line.removesuffix("。")
            for binding in additional:
                line += (
                    morphology["reception_additional_join"]
                    + reception_prefix(binding)
                    + act_tokens[binding.reception_act]
                )
            line += "。"
        reception_lines[line_ordinal - 1] = line
    text = "\n".join(observation_lines) + marker + "\n".join(reception_lines)
    body = text.encode("utf-8", errors="strict")
    return Step11Rc0029ExperimentRenderedSurface(
        schema_version=STEP11_RC0029_EXPERIMENT_RENDERED_SCHEMA,
        utf8_bytes=body,
        sha256=hashlib.sha256(body).hexdigest(),
        added_observation_line_count=0,
        fused_structure_item_count=len(family_clauses),
        fused_structure_group_count=len(expected_groups),
        reception_binding_count=len(reception_bindings),
    )


def _step11_rc0029_candidate_identity(
    *,
    base_candidate_id: str,
    rendered: Step11Rc0029ExperimentRenderedSurface,
    successor_snapshot_sha256: str,
    lexical_atom_specs_sha256: str,
    natural_handle_specs_sha256: str,
    catalog_sha256: str,
) -> str:
    return "nls3s11rc0029cand_" + artifact_sha256(
        {
            "candidate_version_id": STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID,
            "base_candidate_id": base_candidate_id,
            "final_bytes_sha256": rendered.sha256,
            "successor_snapshot_sha256": successor_snapshot_sha256,
            "lexical_atom_specs_sha256": lexical_atom_specs_sha256,
            "natural_handle_specs_sha256": natural_handle_specs_sha256,
            "catalog_sha256": catalog_sha256,
        }
    )[:20]


def _build_step11_rc0029_experiment_surface_candidate(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    validate_output: bool,
) -> Step11Rc0029ExperimentSurfaceCandidate:
    if type(base_candidate) is not Step11NaturalSurfaceCandidate:
        raise Step11NaturalSurfaceError("STEP11_RC0029_BASE_CANDIDATE_INVALID")
    lexical_sha256 = _step11_rc0028_validate_lexical_specs(
        lexical_atom_specs,
        successor_snapshot=successor_snapshot,
    )
    rc0028_catalog, _rc0028_catalog_sha256 = _step11_rc0028_catalog()
    owner_registry, constructions, relations, links, unknowns = (
        _step11_rc0028_forward_atoms(
            successor_snapshot,
            lexical_atom_specs,
            rc0028_catalog,
        )
    )
    lexical_owner = __import__(
        "emlis_ai_step11_grounded_lexicalization_v3",
        fromlist=(
            "build_step11_rc0029_natural_handle_specs",
            "validate_step11_rc0029_natural_handle_specs",
        ),
    )
    handles = lexical_owner.build_step11_rc0029_natural_handle_specs(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    reception_bindings = _step11_rc0029_reception_bindings(
        base_candidate,
        successor_snapshot=successor_snapshot,
        natural_handle_specs=handles,
    )
    groups = _step11_rc0029_fused_groups(
        natural_handle_specs=handles,
        constructions=constructions,
        relations=relations,
        links=links,
        unknowns=unknowns,
        receptions=reception_bindings,
    )
    rendered = render_step11_rc0029_experiment_surface(
        base_candidate.final_utf8_bytes,
        natural_handle_specs=handles,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        fused_structure_groups=groups,
        reception_bindings=reception_bindings,
    )
    catalog, catalog_sha256 = _step11_rc0029_catalog()
    del catalog
    candidate = Step11Rc0029ExperimentSurfaceCandidate(
        schema_version=STEP11_RC0029_EXPERIMENT_CANDIDATE_SCHEMA,
        candidate_version_id=STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID,
        candidate_id=_step11_rc0029_candidate_identity(
            base_candidate_id=base_candidate.candidate_id,
            rendered=rendered,
            successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
            lexical_atom_specs_sha256=lexical_sha256,
            natural_handle_specs_sha256=handles.specs_sha256,
            catalog_sha256=catalog_sha256,
        ),
        base_candidate=base_candidate,
        rendered_surface=rendered,
        successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
        lexical_atom_specs_sha256=lexical_sha256,
        experiment_catalog_sha256=catalog_sha256,
        natural_handle_specs=handles,
        owner_registry=owner_registry,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        fused_structure_groups=groups,
        reception_bindings=reception_bindings,
        semantic_coverage_authorized=False,
        replan_count=0,
    )
    if validate_output:
        issues = validate_step11_rc0029_experiment_surface_candidate(
            candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        if issues:
            raise Step11NaturalSurfaceError(issues[0])
    return candidate


def build_step11_rc0029_experiment_surface_candidate(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> Step11Rc0029ExperimentSurfaceCandidate:
    return _build_step11_rc0029_experiment_surface_candidate(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        validate_output=True,
    )


def build_step11_rc0029_experiment_surface_candidates(
    base_candidates: Sequence[Step11NaturalSurfaceCandidate],
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[Step11Rc0029ExperimentSurfaceCandidate, ...]:
    if (
        type(base_candidates) not in {tuple, list}
        or not base_candidates
        or len(base_candidates) > 12
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_CANDIDATE_BOUND_INVALID"
        )
    candidates: list[Step11Rc0029ExperimentSurfaceCandidate] = []
    for row in base_candidates:
        try:
            candidates.append(
                build_step11_rc0029_experiment_surface_candidate(
                    row,
                    successor_snapshot=successor_snapshot,
                    lexical_atom_specs=lexical_atom_specs,
                )
            )
        except Step11GroundedLexicalizationError:
            # A candidate whose selected content cannot name every required
            # source owner fails closed; another bounded planner candidate may.
            continue
    if not candidates:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0029_NATURAL_HANDLE_UNRESOLVED"
        )
    return tuple(candidates)


def validate_step11_rc0029_experiment_surface_candidate(
    value: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0029ExperimentSurfaceCandidate:
        return ("STEP11_RC0029_CANDIDATE_TYPE_INVALID",)
    issues: set[str] = set()
    try:
        expected = _build_step11_rc0029_experiment_surface_candidate(
            value.base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            validate_output=False,
        )
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
        return ("STEP11_RC0029_CANDIDATE_REVALIDATION_FAILED",)
    if value != expected:
        issues.add("STEP11_RC0029_CANDIDATE_SOURCE_MISMATCH")
    if value.semantic_coverage_authorized is not False:
        issues.add("STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM")
    if (
        value.experimental_only is not True
        or value.private_body_full is not True
        or value.shareable is not False
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_RC0029_RUNTIME_BOUNDARY_INVALID")
    if type(value.replan_count) is not int or not 0 <= value.replan_count <= 1:
        issues.add("STEP11_RC0029_REPLAN_BOUND_EXCEEDED")
    return tuple(sorted(issues))


__all__ += [
    "STEP11_RC0029_EXPERIMENT_CANDIDATE_SCHEMA",
    "STEP11_RC0029_EXPERIMENT_CANDIDATE_VERSION_ID",
    "STEP11_RC0029_EXPERIMENT_RENDERED_SCHEMA",
    "Step11Rc0029ExperimentFusedStructureGroup",
    "Step11Rc0029ExperimentReceptionBinding",
    "Step11Rc0029ExperimentRenderedSurface",
    "Step11Rc0029ExperimentSurfaceCandidate",
    "build_step11_rc0029_experiment_surface_candidate",
    "build_step11_rc0029_experiment_surface_candidates",
    "render_step11_rc0029_experiment_surface",
    "validate_step11_rc0029_experiment_surface_candidate",
]


# ---------------------------------------------------------------------------
# rc0030 experiment-only Surface planning (append-only P2 forward owner)
# ---------------------------------------------------------------------------

STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID = "nls_v3_rc_0030_experiment"
STEP11_RC0030_EXPERIMENT_PLAN_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_surface_realization_plan.v1"
)
STEP11_RC0030_EXPERIMENT_RENDERED_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_rendered_surface.v1"
)
STEP11_RC0030_EXPERIMENT_CANDIDATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_candidate.v1"
)

_STEP11_RC0030_CANDIDATE_MAX = 12
_STEP11_RC0030_REPLAN_MAX = 1
_STEP11_RC0030_OWNER_MAX = 24
_STEP11_RC0030_RECEPTION_MOVE_MAX = 3
_STEP11_RC0030_RECEPTION_SENTENCE_MAX = 3
_STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX = 2


@dataclass(frozen=True, slots=True)
class Step11Rc0030BaseBodyExactReuseBinding:
    """Body-free commitment produced outside the forward owner.

    P2 accepts and schedules these values but never creates one by parsing the
    base body.  The disconnected P3/P4 composition must bind the three hashes
    to an independently produced base-body match before granting reuse credit.
    """

    source_atom_id: str
    semantic_family: str
    base_parsed_atom_id: str
    base_obligation_id: str
    match_basis: str
    base_surface_sha256: str
    source_authority_sha256: str
    independent_binding_sha256: str


@dataclass(frozen=True, slots=True)
class Step11Rc0030ObservationChunkAssignment:
    sentence_group_ordinal: int
    chunk_ordinal: int
    source_unit_ids: tuple[str, ...]
    source_atom_ids: tuple[str, ...]
    visible_clause_count: int
    complexity_load: int


@dataclass(frozen=True, slots=True)
class Step11Rc0030SemanticChunkBinding:
    source_atom_id: str
    semantic_family: str
    source_owner_ids: tuple[str, ...]
    owner_base_nucleus_ids: tuple[str, ...]
    owner_sentence_group_ordinals: tuple[int, ...]
    sentence_group_ordinal: int
    chunk_ordinal: int
    clause_unit_id: str
    cross_group_bridge: bool
    direction: str


@dataclass(frozen=True, slots=True)
class Step11Rc0030ReceptionPredicationBinding:
    reception_line_ordinal: int
    sentence_group_ordinal: int
    chunk_ordinal: int
    source_base_binding_id: str | None
    source_reception_opportunity_id: str
    reception_act: str
    source_target_owner_ids: tuple[str, ...]
    supporting_source_owner_ids: tuple[str, ...]
    target_referent_texts: tuple[str, ...]
    supporting_referent_texts: tuple[str, ...]
    association_basis: str
    additional_clause: bool


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030SurfaceRealizationPlan:
    schema_version: str
    candidate_version_id: str
    realization_plan_id: str
    source_base_candidate_id: str
    source_base_realization_plan_id: str
    source_successor_snapshot_sha256: str
    source_lexical_atom_specs_sha256: str
    source_clause_ready_lexical_specs_sha256: str
    surface_catalog_sha256: str
    base_leading_observation_unit_id: str
    structure_only_unit_ids: tuple[str, ...]
    observation_chunk_assignments: tuple[
        Step11Rc0030ObservationChunkAssignment, ...
    ]
    semantic_chunk_bindings: tuple[Step11Rc0030SemanticChunkBinding, ...]
    base_body_exact_reuse_bindings: tuple[
        Step11Rc0030BaseBodyExactReuseBinding, ...
    ]
    reception_predication_bindings: tuple[
        Step11Rc0030ReceptionPredicationBinding, ...
    ]
    maximum_observation_clauses_per_sentence: int
    maximum_visible_clauses_per_grammatical_sentence: int
    maximum_grammatical_complexity_load: int
    maximum_repeated_joiner_per_group: int
    peak_observation_clause_count: int
    peak_grammatical_clause_count: int
    peak_grammatical_complexity_load: int
    peak_group_repeated_joiner_count: int
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ExperimentRenderedSurface:
    schema_version: str
    utf8_bytes: bytes
    sha256: str
    observation_group_count: int
    semantic_atom_count: int
    exact_reuse_count: int
    reception_predication_count: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0030ExperimentSurfaceCandidate:
    schema_version: str
    candidate_version_id: str
    candidate_id: str
    base_candidate: Step11NaturalSurfaceCandidate
    rendered_surface: Step11Rc0030ExperimentRenderedSurface
    surface_realization_plan: Step11Rc0030SurfaceRealizationPlan
    successor_snapshot_sha256: str
    lexical_atom_specs_sha256: str
    experiment_catalog_sha256: str
    natural_handle_specs: Any
    owner_registry: tuple[str, ...]
    construction_atoms: tuple[Step11Rc0028ExperimentConstructionAtom, ...]
    relation_atoms: tuple[Step11Rc0028ExperimentRelationAtom, ...]
    semantic_link_atoms: tuple[Step11Rc0028ExperimentSemanticLinkAtom, ...]
    explicit_unknown_atoms: tuple[Step11Rc0028ExperimentExplicitUnknownAtom, ...]
    reception_bindings: tuple[Step11Rc0030ReceptionPredicationBinding, ...]
    semantic_coverage_authorized: bool
    replan_count: int
    experimental_only: bool = True
    private_body_full: bool = True
    shareable: bool = False
    runtime_connected: bool = False

    @property
    def final_utf8_bytes(self) -> bytes:
        return self.rendered_surface.utf8_bytes


def _step11_rc0030_exact_reuse_material(
    value: Step11Rc0030BaseBodyExactReuseBinding,
) -> dict[str, Any]:
    return {
        "source_atom_id": value.source_atom_id,
        "semantic_family": value.semantic_family,
        "base_parsed_atom_id": value.base_parsed_atom_id,
        "base_obligation_id": value.base_obligation_id,
        "match_basis": value.match_basis,
        "base_surface_sha256": value.base_surface_sha256,
        "source_authority_sha256": value.source_authority_sha256,
        "independent_binding_sha256": value.independent_binding_sha256,
    }


def _step11_rc0030_chunk_assignment_material(
    value: Step11Rc0030ObservationChunkAssignment,
) -> dict[str, Any]:
    return {
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "chunk_ordinal": value.chunk_ordinal,
        "source_unit_ids": list(value.source_unit_ids),
        "source_atom_ids": list(value.source_atom_ids),
        "visible_clause_count": value.visible_clause_count,
        "complexity_load": value.complexity_load,
    }


def _step11_rc0030_semantic_binding_material(
    value: Step11Rc0030SemanticChunkBinding,
) -> dict[str, Any]:
    return {
        "source_atom_id": value.source_atom_id,
        "semantic_family": value.semantic_family,
        "source_owner_ids": list(value.source_owner_ids),
        "owner_base_nucleus_ids": list(value.owner_base_nucleus_ids),
        "owner_sentence_group_ordinals": list(
            value.owner_sentence_group_ordinals
        ),
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "chunk_ordinal": value.chunk_ordinal,
        "clause_unit_id": value.clause_unit_id,
        "cross_group_bridge": value.cross_group_bridge,
        "direction": value.direction,
    }


def _step11_rc0030_reception_binding_material(
    value: Step11Rc0030ReceptionPredicationBinding,
) -> dict[str, Any]:
    return {
        "reception_line_ordinal": value.reception_line_ordinal,
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "chunk_ordinal": value.chunk_ordinal,
        "source_base_binding_id": value.source_base_binding_id,
        "source_reception_opportunity_id": (
            value.source_reception_opportunity_id
        ),
        "reception_act": value.reception_act,
        "source_target_owner_ids": list(value.source_target_owner_ids),
        "supporting_source_owner_ids": list(
            value.supporting_source_owner_ids
        ),
        "association_basis": value.association_basis,
        "additional_clause": value.additional_clause,
    }


def step11_rc0030_surface_realization_plan_material(
    value: Step11Rc0030SurfaceRealizationPlan,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "realization_plan_id": value.realization_plan_id,
        "source_base_candidate_id": value.source_base_candidate_id,
        "source_base_realization_plan_id": (
            value.source_base_realization_plan_id
        ),
        "source_successor_snapshot_sha256": (
            value.source_successor_snapshot_sha256
        ),
        "source_lexical_atom_specs_sha256": (
            value.source_lexical_atom_specs_sha256
        ),
        "source_clause_ready_lexical_specs_sha256": (
            value.source_clause_ready_lexical_specs_sha256
        ),
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "base_leading_observation_unit_id": (
            value.base_leading_observation_unit_id
        ),
        "structure_only_unit_ids": list(value.structure_only_unit_ids),
        "observation_chunk_assignments": [
            _step11_rc0030_chunk_assignment_material(row)
            for row in value.observation_chunk_assignments
        ],
        "semantic_chunk_bindings": [
            _step11_rc0030_semantic_binding_material(row)
            for row in value.semantic_chunk_bindings
        ],
        "base_body_exact_reuse_bindings": [
            _step11_rc0030_exact_reuse_material(row)
            for row in value.base_body_exact_reuse_bindings
        ],
        "reception_predication_bindings": [
            _step11_rc0030_reception_binding_material(row)
            for row in value.reception_predication_bindings
        ],
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
        "peak_observation_clause_count": value.peak_observation_clause_count,
        "peak_grammatical_clause_count": value.peak_grammatical_clause_count,
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


def _step11_rc0030_catalog() -> tuple[dict[str, Any], str]:
    owner = __import__(
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3",
        fromlist=(
            "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG",
            "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256",
            "validate_step11_rc0030_experiment_surface_catalog",
        ),
    )
    catalog = owner.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG
    issues = owner.validate_step11_rc0030_experiment_surface_catalog(catalog)
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    return catalog, owner.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256


def _step11_rc0030_lexemes(value: Any) -> tuple[Any, ...]:
    rows = getattr(value, "lexemes", None)
    if type(rows) is not tuple:
        rows = getattr(value, "referents", None)
    if type(rows) is not tuple:
        rows = getattr(value, "handles", None)
    if type(rows) is not tuple or not rows:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_CLAUSE_READY_LEXEME_SET_INVALID"
        )
    return rows


def _step11_rc0030_atom_records(
    *,
    lexemes: Sequence[Any],
    constructions: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relations: Sequence[Step11Rc0028ExperimentRelationAtom],
    links: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    unknowns: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
) -> tuple[tuple[str, str, tuple[str, ...], tuple[int, ...], str], ...]:
    by_ordinal = {row.source_owner_ordinal: row for row in lexemes}
    if len(by_ordinal) != len(lexemes):
        raise Step11NaturalSurfaceError("STEP11_RC0030_OWNER_REGISTRY_INVALID")

    def owners(ordinals: Sequence[int]) -> tuple[tuple[str, ...], tuple[int, ...]]:
        unique = tuple(dict.fromkeys(ordinals))
        try:
            return (
                tuple(by_ordinal[value].source_owner_id for value in unique),
                unique,
            )
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_OWNER_REGISTRY_INVALID"
            ) from exc

    result: list[tuple[str, str, tuple[str, ...], tuple[int, ...], str]] = []
    for row in constructions:
        owner_ids, ordinals = owners(
            (_step11_rc0029_construction_owner_ordinal(row),)
        )
        result.append(
            (row.construction_instance_id, "construction", owner_ids, ordinals, "")
        )
    for row in relations:
        owner_ids, ordinals = owners(
            (row.from_owner_ordinal, row.to_owner_ordinal)
        )
        result.append(
            (
                row.experiment_relation_id,
                "relation",
                owner_ids,
                ordinals,
                row.direction,
            )
        )
    for row in links:
        owner_ids, ordinals = owners(
            (row.from_owner_ordinal, row.to_owner_ordinal)
        )
        result.append(
            (
                row.source_semantic_link_id,
                "semantic_link",
                owner_ids,
                ordinals,
                row.direction,
            )
        )
    for row in unknowns:
        owner_ids, ordinals = owners(row.affected_owner_ordinals)
        result.append(
            (row.source_unknown_id, "explicit_unknown", owner_ids, ordinals, "")
        )
    if len({row[0] for row in result}) != len(result):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_SOURCE_ATOM_ID_COLLISION"
        )
    return tuple(result)


def _step11_rc0030_owner_positions(
    base_candidate: Step11NaturalSurfaceCandidate,
    lexemes: Sequence[Any],
) -> dict[int, tuple[str, str, int, int]]:
    base_plan = base_candidate.surface_ast.surface_realization_plan
    if type(base_plan) is not Step11SurfaceRealizationPlan:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_PLAN_INVALID")
    group_index = {
        group_id: index
        for index, group_id in enumerate(
            base_plan.observation_sentence_group_ids, start=1
        )
    }
    observation_units = tuple(
        row for row in base_plan.units if row.section_role == "observation"
    )
    references = tuple(base_candidate.surface_ast.nucleus_surface_references)
    positions: dict[int, tuple[str, str, int, int]] = {}
    for lexeme in lexemes:
        nucleus_id = str(lexeme.base_source_nucleus_id)
        owned_units = tuple(
            row for row in observation_units if nucleus_id in row.owner_nucleus_ids
        )
        owned_group_ids = {
            row.assigned_sentence_group_id for row in owned_units
        }
        lexical_group_ids = {
            str(value)
            for value in getattr(
                lexeme, "base_observation_sentence_group_ids", ()
            )
            if str(value) in group_index
        }
        obligation_ids = {
            str(value)
            for value in getattr(lexeme, "owner_obligation_ids", ())
        }
        obligation_owned_units = tuple(
            row
            for row in owned_units
            if obligation_ids & {str(value) for value in row.owner_obligation_ids}
        )
        matching_refs = tuple(
            row for row in references if nucleus_id in row.nucleus_ids
        )
        reference_group_ids = {
            row.introduction_sentence_group_id
            for row in matching_refs
            if row.introduction_sentence_group_id in group_index
        }
        owned_lexical_group_ids = owned_group_ids & lexical_group_ids
        obligation_overlap_by_group = {
            group_id: len(
                obligation_ids
                & {
                    str(obligation_id)
                    for row in obligation_owned_units
                    if row.assigned_sentence_group_id == group_id
                    for obligation_id in row.owner_obligation_ids
                }
            )
            for group_id in owned_lexical_group_ids
        }
        maximum_obligation_overlap = max(
            obligation_overlap_by_group.values(), default=0
        )
        obligation_preferred_group_ids = {
            group_id
            for group_id, overlap in obligation_overlap_by_group.items()
            if overlap == maximum_obligation_overlap and overlap > 0
        }
        if len(owned_group_ids) == 1:
            group_id = next(iter(owned_group_ids))
            candidates = tuple(
                row
                for row in owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif len(owned_lexical_group_ids) == 1:
            group_id = next(iter(owned_lexical_group_ids))
            candidates = tuple(
                row
                for row in owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif len(obligation_preferred_group_ids) == 1:
            # When one nucleus supports several base groups, the lexeme's
            # immutable obligation set selects the group with the uniquely
            # strongest owner overlap.  A tied maximum remains unresolved;
            # source order is not promoted into semantic authority.
            group_id = next(iter(obligation_preferred_group_ids))
            candidates = tuple(
                row
                for row in obligation_owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif len(reference_group_ids & owned_lexical_group_ids) == 1:
            # A nucleus may legitimately support units in more than one base
            # group.  Its immutable rc0027 reference registry still owns one
            # introduction group; use that existing witness only when it
            # selects exactly one of the lexically authorized owner groups.
            group_id = next(iter(reference_group_ids & owned_lexical_group_ids))
            candidates = tuple(
                row
                for row in owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif not owned_units and len(matching_refs) == 1:
            group_id = matching_refs[0].introduction_sentence_group_id
            candidates = tuple(
                row
                for row in observation_units
                if row.assigned_sentence_group_id == group_id
                and matching_refs[0].reference_ordinal
                in row.introduced_reference_ordinals
            )
        else:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_OWNER_BASE_GROUP_UNRESOLVED"
            )
        group_ordinal = group_index.get(group_id)
        if group_ordinal is None:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_OWNER_BASE_GROUP_UNRESOLVED"
            )
        if not candidates:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_OWNER_BASE_CHUNK_UNRESOLVED"
            )
        unit = min(
            candidates,
            key=lambda row: (
                row.assigned_grammatical_chunk_ordinal,
                row.source_order,
                row.semantic_unit_id,
            ),
        )
        positions[int(lexeme.source_owner_ordinal)] = (
            str(lexeme.source_owner_id),
            nucleus_id,
            group_ordinal,
            unit.assigned_grammatical_chunk_ordinal,
        )
    if len(positions) != len(lexemes) or len(positions) > _STEP11_RC0030_OWNER_MAX:
        raise Step11NaturalSurfaceError("STEP11_RC0030_OWNER_BOUND_EXCEEDED")
    return positions


def _step11_rc0030_reception_predications(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexemes: Sequence[Any],
) -> tuple[Step11Rc0030ReceptionPredicationBinding, ...]:
    base_plan = base_candidate.surface_ast.surface_realization_plan
    if type(base_plan) is not Step11SurfaceRealizationPlan:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_PLAN_INVALID")
    group_count = len(base_plan.reception_sentence_group_ids)
    if not 1 <= group_count <= _STEP11_RC0030_RECEPTION_SENTENCE_MAX:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_RECEPTION_GROUP_BOUND_INVALID"
        )
    nuclei = tuple(successor_snapshot.base_snapshot.nuclei)
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    by_owner = {str(row.source_owner_id): row for row in lexemes}
    base_bindings = tuple(
        base_candidate.surface_ast.reception_antecedent_bindings
    )
    exact: dict[str, tuple[int, Any]] = {}
    for line_ordinal, binding in enumerate(base_bindings, start=1):
        for opportunity_id in binding.source_reception_opportunity_ids:
            key = str(opportunity_id)
            if key in exact:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_RECEPTION_ASSOCIATION_AMBIGUOUS"
                )
            exact[key] = (line_ordinal, binding)
    opportunities = tuple(
        row
        for row in successor_snapshot.base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    if not 1 <= len(opportunities) <= _STEP11_RC0030_RECEPTION_MOVE_MAX:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_RECEPTION_MOVE_BOUND_INVALID"
        )
    loads = {ordinal: 0 for ordinal in range(1, group_count + 1)}
    prepared: list[tuple[Any, int, Any | None, str]] = []
    for opportunity in opportunities:
        opportunity_id = str(opportunity.source_id)
        association = exact.get(opportunity_id)
        if association is not None:
            ordinal, binding = association
            if not 1 <= ordinal <= group_count:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_RECEPTION_ASSOCIATION_INVALID"
                )
            basis = "exact_base_opportunity_id"
        else:
            available = tuple(
                ordinal
                for ordinal in range(1, group_count + 1)
                if loads[ordinal]
                < _STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX
            )
            if not available:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_RECEPTION_DENSITY_UNSATISFIABLE"
                )
            ordinal = min(available, key=lambda item: (loads[item], item))
            binding = None
            basis = "required_opportunity_bounded_schedule"
        loads[ordinal] += 1
        if loads[ordinal] > _STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_RECEPTION_DENSITY_UNSATISFIABLE"
            )
        prepared.append((opportunity, ordinal, binding, basis))

    rows: list[Step11Rc0030ReceptionPredicationBinding] = []
    ordinal_counts = {ordinal: 0 for ordinal in loads}
    for opportunity, ordinal, binding, basis in prepared:
        try:
            target_ids = tuple(
                actual_by_source[str(value)]
                for value in opportunity.target_nucleus_ids
            )
            support_ids = tuple(
                actual_by_source[str(value)]
                for value in opportunity.support_nucleus_ids
            )
            target_texts = tuple(by_owner[value].referent_text for value in target_ids)
            support_texts = tuple(by_owner[value].referent_text for value in support_ids)
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_RECEPTION_OWNER_UNRESOLVED"
            ) from exc
        if not target_ids or len(set(target_ids)) != len(target_ids):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_RECEPTION_TARGET_INVALID"
            )
        ordinal_counts[ordinal] += 1
        rows.append(
            Step11Rc0030ReceptionPredicationBinding(
                reception_line_ordinal=ordinal,
                sentence_group_ordinal=ordinal,
                chunk_ordinal=ordinal_counts[ordinal],
                source_base_binding_id=(
                    str(binding.binding_id) if binding is not None else None
                ),
                source_reception_opportunity_id=str(opportunity.source_id),
                reception_act=str(opportunity.reception_act),
                source_target_owner_ids=target_ids,
                supporting_source_owner_ids=support_ids,
                target_referent_texts=target_texts,
                supporting_referent_texts=support_texts,
                association_basis=basis,
                additional_clause=binding is None,
            )
        )
    return tuple(rows)


def _step11_rc0030_structure_pack_destination(
    *,
    ready_group_ordinal: int,
    preferred_chunk_ordinal: int,
    last_group_ordinal: int,
    pack_clause_count: int,
    pack_complexity_load: int,
    base_unit_count_by_group: Mapping[int, int],
    structure_count_by_group: Mapping[int, int],
    chunk_clause_count: Mapping[tuple[int, int], int],
    chunk_complexity_load: Mapping[tuple[int, int], int],
    maximum_observation_clauses_per_sentence: int,
    maximum_visible_clauses_per_grammatical_sentence: int,
    maximum_grammatical_complexity_load: int,
    maximum_repeated_joiner_per_group: int,
) -> tuple[int, int] | None:
    """Return the first owner-ready destination without mutating schedule state."""

    for group_ordinal in range(
        ready_group_ordinal, last_group_ordinal + 1
    ):
        if (
            base_unit_count_by_group[group_ordinal]
            + structure_count_by_group[group_ordinal]
            + 1
            > maximum_observation_clauses_per_sentence
        ):
            continue
        group_chunk_ordinals = tuple(
            key[1] for key in chunk_clause_count if key[0] == group_ordinal
        )
        tail_chunk = max(group_chunk_ordinals, default=0)
        effective_preferred_chunk = (
            preferred_chunk_ordinal
            if group_ordinal == ready_group_ordinal
            else 1
        )
        candidate_chunks: list[int] = []
        if tail_chunk >= effective_preferred_chunk and tail_chunk > 0:
            candidate_chunks.append(tail_chunk)
        candidate_chunks.append(max(tail_chunk + 1, effective_preferred_chunk))
        for chunk_ordinal in dict.fromkeys(candidate_chunks):
            key = (group_ordinal, chunk_ordinal)
            current_clause_count = chunk_clause_count.get(key, 0)
            current_complexity_load = chunk_complexity_load.get(key, 0)
            projected_clause_count = current_clause_count + pack_clause_count
            projected_complexity_load = (
                current_complexity_load + pack_complexity_load
            )
            if (
                projected_clause_count
                > maximum_visible_clauses_per_grammatical_sentence
                or projected_complexity_load
                > maximum_grammatical_complexity_load
            ):
                continue
            current_joiner_count = sum(
                max(0, count - 1)
                for (candidate_group, _candidate_chunk), count in (
                    chunk_clause_count.items()
                )
                if candidate_group == group_ordinal
            )
            projected_joiner_count = (
                current_joiner_count
                - max(0, current_clause_count - 1)
                + max(0, projected_clause_count - 1)
            )
            if projected_joiner_count > maximum_repeated_joiner_per_group:
                continue
            return group_ordinal, chunk_ordinal
    return None


def build_step11_rc0030_surface_realization_plan(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    clause_ready_lexical_specs: Any,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    reception_predications: Sequence[Step11Rc0030ReceptionPredicationBinding],
    base_body_exact_reuse_bindings: Sequence[
        Step11Rc0030BaseBodyExactReuseBinding
    ] = (),
) -> Step11Rc0030SurfaceRealizationPlan:
    base_plan = base_candidate.surface_ast.surface_realization_plan
    if type(base_plan) is not Step11SurfaceRealizationPlan:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_PLAN_INVALID")
    lexemes = _step11_rc0030_lexemes(clause_ready_lexical_specs)
    positions = _step11_rc0030_owner_positions(base_candidate, lexemes)
    records = _step11_rc0030_atom_records(
        lexemes=lexemes,
        constructions=construction_atoms,
        relations=relation_atoms,
        links=semantic_link_atoms,
        unknowns=explicit_unknown_atoms,
    )
    family_by_id = {row[0]: row[1] for row in records}
    reuse = tuple(base_body_exact_reuse_bindings)
    if any(type(row) is not Step11Rc0030BaseBodyExactReuseBinding for row in reuse):
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_REUSE_TYPE_INVALID")
    if len({row.source_atom_id for row in reuse}) != len(reuse):
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_REUSE_DUPLICATE")
    exact_match_basis_by_family = {
        "construction": "construction_instance_role_layout_exact",
        "relation": "relation_id_endpoint_direction_type_exact",
        "semantic_link": "semantic_link_id_endpoint_direction_type_exact",
        "explicit_unknown": "unknown_id_dimension_exact_target",
    }
    base_surface_sha256 = hashlib.sha256(
        base_candidate.final_utf8_bytes
    ).hexdigest()
    source_authority_sha256 = str(
        successor_snapshot.relation_construction_authority.authority_sha256
    )
    for row in reuse:
        if (
            family_by_id.get(row.source_atom_id) != row.semantic_family
            or not row.base_parsed_atom_id
            or not row.base_obligation_id
            or row.match_basis
            != exact_match_basis_by_family.get(row.semantic_family)
            or row.base_surface_sha256 != base_surface_sha256
            or row.source_authority_sha256 != source_authority_sha256
            or any(
                _SHA_RE.fullmatch(value) is None
                or value == "0" * 64
                for value in (
                    row.base_surface_sha256,
                    row.source_authority_sha256,
                    row.independent_binding_sha256,
                )
            )
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_BASE_REUSE_COMMITMENT_INVALID"
            )
    reused_ids = {row.source_atom_id for row in reuse}
    pending: list[
        tuple[
            str,
            str,
            tuple[str, ...],
            tuple[str, ...],
            tuple[int, ...],
            int,
            int,
            bool,
            str,
        ]
    ] = []
    for atom_id, family, owner_ids, owner_ordinals, direction in records:
        if atom_id in reused_ids:
            continue
        try:
            owner_positions = tuple(positions[value] for value in owner_ordinals)
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_OWNER_BASE_GROUP_UNRESOLVED"
            ) from exc
        group_ordinals = tuple(row[2] for row in owner_positions)
        target_group = max(group_ordinals)
        target_chunks = tuple(
            row[3] for row in owner_positions if row[2] == target_group
        )
        if not target_chunks:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_OWNER_BASE_CHUNK_UNRESOLVED"
            )
        target_chunk = max(target_chunks)
        pending.append(
            (
                atom_id,
                family,
                owner_ids,
                tuple(row[1] for row in owner_positions),
                group_ordinals,
                target_group,
                target_chunk,
                len(set(group_ordinals)) > 1,
                direction,
            )
        )
    group_ids = tuple(base_plan.observation_sentence_group_ids)
    group_index = {value: index for index, value in enumerate(group_ids, start=1)}
    base_units = tuple(
        row for row in base_plan.units if row.section_role == "observation"
    )
    by_chunk: dict[tuple[int, int], list[Step11SurfaceRealizationUnit]] = {}
    for row in base_units:
        key = (
            group_index[row.assigned_sentence_group_id],
            row.assigned_grammatical_chunk_ordinal,
        )
        by_chunk.setdefault(key, []).append(row)
    base_unit_count_by_group = {
        group_ordinal: sum(key[0] == group_ordinal for key in by_chunk for _row in by_chunk[key])
        for group_ordinal in range(1, len(group_ids) + 1)
    }
    chunk_clause_count = {
        key: len(rows) for key, rows in by_chunk.items()
    }
    chunk_complexity_load = {
        key: sum(row.body_free_complexity_weight for row in rows)
        for key, rows in by_chunk.items()
    }
    structure_count_by_group = {
        group_ordinal: 0 for group_ordinal in range(1, len(group_ids) + 1)
    }

    # Pack at most two atom clauses into one structure unit.  Packing is
    # deterministic.  A pack may move only from its latest owner-introduction
    # group to the first later group whose frozen resource bounds admit it.
    pending_by_group: dict[int, list[tuple[Any, ...]]] = {}
    for row in pending:
        pending_by_group.setdefault(int(row[5]), []).append(row)
    packed: list[tuple[int, int, str, tuple[tuple[Any, ...], ...], int]] = []
    last_group_ordinal = len(group_ids)
    for ready_group_ordinal in sorted(pending_by_group):
        ordered_rows = sorted(
            pending_by_group[ready_group_ordinal],
            key=lambda row: (row[6], row[1], row[2], row[0]),
        )
        raw_packs: list[list[tuple[Any, ...]]] = []
        for row in ordered_rows:
            placed = False
            for pack in raw_packs:
                owners = {
                    owner_id
                    for item in (*pack, row)
                    for owner_id in item[2]
                }
                if len(pack) < 2 and len(owners) <= base_plan.maximum_grammatical_complexity_load:
                    pack.append(row)
                    placed = True
                    break
            if not placed:
                raw_packs.append([row])
        for pack_rows in raw_packs:
            if len(pack_rows) > 2:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_STRUCTURE_UNIT_ATOM_BOUND_EXCEEDED"
                )
            owner_count = len(
                {
                    owner_id
                    for item in pack_rows
                    for owner_id in item[2]
                }
            )
            # Up to two nominal semantic items share one finite pack
            # predicate.  The rendered unit is therefore one grammatical
            # clause, while complexity still accounts for both atom count
            # and every distinct visible owner.
            pack_clause_count = 1
            pack_complexity_load = max(owner_count, len(pack_rows))
            preferred_chunk = max(int(item[6]) for item in pack_rows)
            ready_tail_chunk = max(
                (
                    key[1]
                    for key in chunk_clause_count
                    if key[0] == ready_group_ordinal
                ),
                default=0,
            )
            if ready_tail_chunk < preferred_chunk:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_OWNER_BASE_CHUNK_UNRESOLVED"
                )
            destination = _step11_rc0030_structure_pack_destination(
                ready_group_ordinal=ready_group_ordinal,
                preferred_chunk_ordinal=preferred_chunk,
                last_group_ordinal=last_group_ordinal,
                pack_clause_count=pack_clause_count,
                pack_complexity_load=pack_complexity_load,
                base_unit_count_by_group=base_unit_count_by_group,
                structure_count_by_group=structure_count_by_group,
                chunk_clause_count=chunk_clause_count,
                chunk_complexity_load=chunk_complexity_load,
                maximum_observation_clauses_per_sentence=(
                    base_plan.maximum_observation_clauses_per_sentence
                ),
                maximum_visible_clauses_per_grammatical_sentence=(
                    base_plan.maximum_visible_clauses_per_grammatical_sentence
                ),
                maximum_grammatical_complexity_load=(
                    base_plan.maximum_grammatical_complexity_load
                ),
                maximum_repeated_joiner_per_group=(
                    base_plan.maximum_repeated_joiner_per_group
                ),
            )
            if destination is None:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_SURFACE_PLAN_DENSITY_UNSATISFIABLE"
                )
            group_ordinal, chosen_chunk = destination
            chosen_key = (group_ordinal, chosen_chunk)
            if chosen_key not in chunk_clause_count:
                chunk_clause_count[chosen_key] = 0
                chunk_complexity_load[chosen_key] = 0
                by_chunk[chosen_key] = []
            unit_id = "nls3s11rc0030unit_" + artifact_sha256(
                {
                    "source_atom_ids": [item[0] for item in pack_rows],
                    "sentence_group_ordinal": group_ordinal,
                    "chunk_ordinal": chosen_chunk,
                }
            )[:16]
            chunk_clause_count[chosen_key] += pack_clause_count
            chunk_complexity_load[chosen_key] += pack_complexity_load
            structure_count_by_group[group_ordinal] += 1
            packed.append(
                (
                    group_ordinal,
                    chosen_chunk,
                    unit_id,
                    tuple(pack_rows),
                    pack_complexity_load,
                )
            )

    bindings: list[Step11Rc0030SemanticChunkBinding] = []
    structure_by_chunk: dict[
        tuple[int, int], list[tuple[str, tuple[tuple[Any, ...], ...], int]]
    ] = {}
    for group_ordinal, chunk_ordinal, unit_id, pack_rows, owner_count in packed:
        structure_by_chunk.setdefault((group_ordinal, chunk_ordinal), []).append(
            (unit_id, pack_rows, owner_count)
        )
        for row in pack_rows:
            bindings.append(
                Step11Rc0030SemanticChunkBinding(
                    source_atom_id=str(row[0]),
                    semantic_family=str(row[1]),
                    source_owner_ids=tuple(row[2]),
                    owner_base_nucleus_ids=tuple(row[3]),
                    owner_sentence_group_ordinals=tuple(row[4]),
                    sentence_group_ordinal=group_ordinal,
                    chunk_ordinal=chunk_ordinal,
                    clause_unit_id=unit_id,
                    cross_group_bridge=bool(row[7]),
                    direction=str(row[8]),
                )
            )
    bindings.sort(
        key=lambda row: (
            row.sentence_group_ordinal,
            row.chunk_ordinal,
            row.clause_unit_id,
            row.semantic_family,
            row.source_atom_id,
        )
    )
    if len(bindings) + len(reuse) != len(records):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_SEMANTIC_ATOM_COVERAGE_INVALID"
        )
    assignments: list[Step11Rc0030ObservationChunkAssignment] = []
    structure_ids: list[str] = []
    for key in sorted(by_chunk):
        rows = sorted(by_chunk[key], key=lambda item: item.source_order)
        structure_rows = sorted(
            structure_by_chunk.get(key, ()), key=lambda item: item[0]
        )
        semantic_unit_ids = tuple(row[0] for row in structure_rows)
        structure_ids.extend(semantic_unit_ids)
        assignments.append(
            Step11Rc0030ObservationChunkAssignment(
                sentence_group_ordinal=key[0],
                chunk_ordinal=key[1],
                source_unit_ids=(
                    *(row.semantic_unit_id for row in rows),
                    *semantic_unit_ids,
                ),
                source_atom_ids=tuple(
                    str(atom[0])
                    for _unit_id, pack_rows, _owner_count in structure_rows
                    for atom in pack_rows
                ),
                visible_clause_count=(len(rows) + len(structure_rows)),
                complexity_load=(
                    sum(row.body_free_complexity_weight for row in rows)
                    + sum(row[2] for row in structure_rows)
                ),
            )
        )
    group_clause_counts = tuple(
        base_unit_count_by_group[group_ordinal]
        + structure_count_by_group[group_ordinal]
        for group_ordinal in sorted(base_unit_count_by_group)
    )
    grammatical_clause_counts = tuple(
        row.visible_clause_count for row in assignments
    )
    grammatical_loads = tuple(row.complexity_load for row in assignments)
    joiner_counts = tuple(
        sum(
            max(0, row.visible_clause_count - 1)
            for row in assignments
            if row.sentence_group_ordinal == group_ordinal
        )
        for group_ordinal in sorted(base_unit_count_by_group)
    )
    if (
        max(group_clause_counts, default=0)
        > base_plan.maximum_observation_clauses_per_sentence
        or max(grammatical_clause_counts, default=0)
        > base_plan.maximum_visible_clauses_per_grammatical_sentence
        or max(grammatical_loads, default=0)
        > base_plan.maximum_grammatical_complexity_load
        or max(joiner_counts, default=0)
        > base_plan.maximum_repeated_joiner_per_group
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_SURFACE_PLAN_DENSITY_UNSATISFIABLE"
        )
    observation_ordered = tuple(
        sorted(
            base_units,
            key=lambda row: (
                group_index[row.assigned_sentence_group_id],
                row.assigned_grammatical_chunk_ordinal,
                row.source_order,
            ),
        )
    )
    if not observation_ordered:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_LEADING_UNIT_INVALID")
    base_leading_id = observation_ordered[0].semantic_unit_id
    first_assignment = assignments[0] if assignments else None
    if first_assignment is None or base_leading_id not in first_assignment.source_unit_ids:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_LEADING_UNIT_INVALID")
    catalog, catalog_sha256 = _step11_rc0030_catalog()
    del catalog
    provisional = Step11Rc0030SurfaceRealizationPlan(
        schema_version=STEP11_RC0030_EXPERIMENT_PLAN_SCHEMA,
        candidate_version_id=STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID,
        realization_plan_id="nls3s11rc0030plan_0000000000000000",
        source_base_candidate_id=base_candidate.candidate_id,
        source_base_realization_plan_id=base_plan.realization_plan_id,
        source_successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        source_lexical_atom_specs_sha256=lexical_atom_specs.specs_sha256,
        source_clause_ready_lexical_specs_sha256=(
            clause_ready_lexical_specs.specs_sha256
        ),
        surface_catalog_sha256=catalog_sha256,
        base_leading_observation_unit_id=base_leading_id,
        structure_only_unit_ids=tuple(structure_ids),
        observation_chunk_assignments=tuple(assignments),
        semantic_chunk_bindings=tuple(bindings),
        base_body_exact_reuse_bindings=reuse,
        reception_predication_bindings=tuple(reception_predications),
        maximum_observation_clauses_per_sentence=(
            base_plan.maximum_observation_clauses_per_sentence
        ),
        maximum_visible_clauses_per_grammatical_sentence=(
            base_plan.maximum_visible_clauses_per_grammatical_sentence
        ),
        maximum_grammatical_complexity_load=(
            base_plan.maximum_grammatical_complexity_load
        ),
        maximum_repeated_joiner_per_group=(
            base_plan.maximum_repeated_joiner_per_group
        ),
        peak_observation_clause_count=max(group_clause_counts, default=0),
        peak_grammatical_clause_count=max(
            grammatical_clause_counts, default=0
        ),
        peak_grammatical_complexity_load=max(
            grammatical_loads, default=0
        ),
        peak_group_repeated_joiner_count=max(joiner_counts, default=0),
        body_free=True,
    )
    return replace(
        provisional,
        realization_plan_id=(
            "nls3s11rc0030plan_"
            + artifact_sha256(
                step11_rc0030_surface_realization_plan_material(
                    provisional, include_id=False
                )
            )[:16]
        ),
    )


def _step11_rc0030_render_semantic_clause(
    binding: Step11Rc0030SemanticChunkBinding,
    *,
    catalog: Mapping[str, Any],
    referent_by_owner: Mapping[str, str],
    construction_by_id: Mapping[str, Any],
    relation_by_id: Mapping[str, Any],
    link_by_id: Mapping[str, Any],
    unknown_by_id: Mapping[str, Any],
) -> str:
    morphology = catalog["clause_morphology"]
    try:
        referents = tuple(referent_by_owner[item] for item in binding.source_owner_ids)
    except KeyError as exc:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_RENDER_OWNER_UNRESOLVED"
        ) from exc
    if binding.semantic_family == "construction":
        atom = construction_by_id[binding.source_atom_id]
        fragment = catalog["construction_clause_fragments"].get(
            atom.construction_code
        )
        text = (
            referents[0]
            + morphology["construction_item_link"]
            + str(fragment)
        )
    elif binding.semantic_family in {"relation", "semantic_link"}:
        atom = (
            relation_by_id[binding.source_atom_id]
            if binding.semantic_family == "relation"
            else link_by_id[binding.source_atom_id]
        )
        key = (
            (atom.effective_relation_type if binding.semantic_family == "relation" else atom.relation_type)
            + ":"
            + atom.direction
        )
        registry = (
            catalog["relation_clause_fragments"]
            if binding.semantic_family == "relation"
            else catalog["semantic_link_clause_fragments"]
        )
        fragment = registry.get(key)
        if atom.direction == "bidirectional":
            text = (
                referents[0]
                + morphology["symmetric_join"]
                + referents[1]
                + morphology["bidirectional_item_link"]
                + str(fragment)
            )
        else:
            text = (
                referents[0]
                + morphology["source_particle"]
                + referents[1]
                + morphology["directed_item_link"]
                + str(fragment)
            )
    elif binding.semantic_family == "explicit_unknown":
        atom = unknown_by_id[binding.source_atom_id]
        fragment = catalog["unknown_clause_fragments"].get(atom.dimension)
        text = (
            morphology["symmetric_join"].join(referents)
            + morphology["unknown_item_link"]
            + str(fragment)
        )
    else:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_SEMANTIC_FAMILY_INVALID"
        )
    if (
        not text
        or "\r" in text
        or "\n" in text
        or "「" in text
        or "」" in text
        or text.endswith(("。", "！", "？", "!", "?"))
        or "None" in text
    ):
        raise Step11NaturalSurfaceError("STEP11_RC0030_SCHEMA_FREE_CLAUSE_INVALID")
    return text


def render_step11_rc0030_experiment_surface(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    clause_ready_lexical_specs: Any,
    surface_realization_plan: Step11Rc0030SurfaceRealizationPlan,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    reception_predications: Sequence[Step11Rc0030ReceptionPredicationBinding],
) -> Step11Rc0030ExperimentRenderedSurface:
    if type(base_candidate) is not Step11NaturalSurfaceCandidate:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_CANDIDATE_INVALID")
    catalog, catalog_sha256 = _step11_rc0030_catalog()
    if surface_realization_plan.surface_catalog_sha256 != catalog_sha256:
        raise Step11NaturalSurfaceError("STEP11_RC0030_CATALOG_COMMITMENT_MISMATCH")
    try:
        text = base_candidate.final_utf8_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_SURFACE_INVALID") from exc
    marker = "\n\nEmlisから：\n"
    if not text.startswith("見えたこと：\n") or text.count(marker) != 1:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_SURFACE_INVALID")
    observation, reception = text.split(marker, 1)
    observation_lines = observation.split("\n")
    reception_lines = reception.split("\n")
    base_plan = base_candidate.surface_ast.surface_realization_plan
    if (
        type(base_plan) is not Step11SurfaceRealizationPlan
        or len(observation_lines) != len(base_plan.observation_sentence_group_ids) + 1
        or len(reception_lines) != len(base_plan.reception_sentence_group_ids)
    ):
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_SURFACE_LAYOUT_INVALID")
    lexemes = _step11_rc0030_lexemes(clause_ready_lexical_specs)
    referent_by_owner = {
        str(row.source_owner_id): str(row.referent_text) for row in lexemes
    }
    construction_by_id = {
        row.construction_instance_id: row for row in construction_atoms
    }
    relation_by_id = {row.experiment_relation_id: row for row in relation_atoms}
    link_by_id = {row.source_semantic_link_id: row for row in semantic_link_atoms}
    unknown_by_id = {row.source_unknown_id: row for row in explicit_unknown_atoms}
    clauses_by_unit: dict[
        tuple[int, int, str], list[tuple[str, str]]
    ] = {}
    for binding in surface_realization_plan.semantic_chunk_bindings:
        clause = _step11_rc0030_render_semantic_clause(
            binding,
            catalog=catalog,
            referent_by_owner=referent_by_owner,
            construction_by_id=construction_by_id,
            relation_by_id=relation_by_id,
            link_by_id=link_by_id,
            unknown_by_id=unknown_by_id,
        )
        clauses_by_unit.setdefault(
            (
                binding.sentence_group_ordinal,
                binding.chunk_ordinal,
                binding.clause_unit_id,
            ),
            [],
        ).append(
            (binding.source_atom_id, clause)
        )
    morphology = catalog["clause_morphology"]
    suffix = morphology["sentence_suffix"]
    structure_id_set = set(surface_realization_plan.structure_only_unit_ids)
    if len(structure_id_set) != len(
        surface_realization_plan.structure_only_unit_ids
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_RENDER_PLAN_CHUNK_MISMATCH"
        )
    assignment_by_chunk = {
        (row.sentence_group_ordinal, row.chunk_ordinal): row
        for row in surface_realization_plan.observation_chunk_assignments
    }
    if len(assignment_by_chunk) != len(
        surface_realization_plan.observation_chunk_assignments
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_RENDER_PLAN_CHUNK_MISMATCH"
        )
    units_by_group: dict[int, list[tuple[int, str, str]]] = {}
    for (group_ordinal, chunk_ordinal, unit_id), rows in clauses_by_unit.items():
        if not 1 <= len(rows) <= 2:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_STRUCTURE_UNIT_ATOM_BOUND_EXCEEDED"
            )
        unit_text = (
            morphology["semantic_item_join"].join(
            text for _atom_id, text in sorted(rows)
            )
            + morphology["semantic_pack_predicate_suffix"]
        )
        units_by_group.setdefault(group_ordinal, []).append(
            (chunk_ordinal, unit_id, unit_text)
        )
    rendered_structure_ids = tuple(
        unit_id
        for rows in units_by_group.values()
        for _chunk_ordinal, unit_id, _unit_text in rows
    )
    if (
        len(set(rendered_structure_ids)) != len(rendered_structure_ids)
        or set(rendered_structure_ids) != structure_id_set
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0030_RENDER_PLAN_CHUNK_MISMATCH"
        )
    for group_ordinal, rows in units_by_group.items():
        line_index = group_ordinal
        if not 1 <= line_index < len(observation_lines):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_OBSERVATION_GROUP_INVALID"
            )
        base_line = observation_lines[line_index]
        if not base_line.endswith(suffix):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_BASE_OBSERVATION_SUFFIX_INVALID"
            )
        group_id = base_plan.observation_sentence_group_ids[
            group_ordinal - 1
        ]
        base_chunk_ordinals = tuple(
            row.assigned_grammatical_chunk_ordinal
            for row in base_plan.units
            if row.section_role == "observation"
            and row.assigned_sentence_group_id == group_id
        )
        if not base_chunk_ordinals:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_RENDER_PLAN_CHUNK_MISMATCH"
            )
        base_tail_chunk = max(base_chunk_ordinals)
        rows_by_chunk: dict[int, list[tuple[str, str]]] = {}
        for chunk_ordinal, unit_id, unit_text in rows:
            rows_by_chunk.setdefault(chunk_ordinal, []).append(
                (unit_id, unit_text)
            )
        current_line = base_line
        previous_chunk = base_tail_chunk
        for chunk_ordinal in sorted(rows_by_chunk):
            assignment = assignment_by_chunk.get(
                (group_ordinal, chunk_ordinal)
            )
            ordered_rows = tuple(sorted(rows_by_chunk[chunk_ordinal]))
            planned_unit_ids = tuple(
                unit_id
                for unit_id in assignment.source_unit_ids
                if unit_id in structure_id_set
            ) if assignment is not None else ()
            actual_unit_ids = tuple(unit_id for unit_id, _text in ordered_rows)
            actual_atom_ids = tuple(
                atom_id
                for (bound_group, bound_chunk, unit_id), atom_rows
                in clauses_by_unit.items()
                if bound_group == group_ordinal
                and bound_chunk == chunk_ordinal
                and unit_id in actual_unit_ids
                for atom_id, _text in atom_rows
            )
            if (
                assignment is None
                or planned_unit_ids != actual_unit_ids
                or len(actual_atom_ids) != len(assignment.source_atom_ids)
                or set(actual_atom_ids) != set(assignment.source_atom_ids)
                or chunk_ordinal < base_tail_chunk
                or chunk_ordinal > previous_chunk + 1
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_RENDER_PLAN_CHUNK_MISMATCH"
                )
            separator = (
                morphology["clause_join"]
                if chunk_ordinal == previous_chunk
                else morphology["grammatical_chunk_join"]
            )
            chunk_text = morphology["clause_join"].join(
                text for _unit_id, text in ordered_rows
            )
            current_line = (
                current_line[: -len(suffix)]
                + separator
                + chunk_text
                + suffix
            )
            previous_chunk = chunk_ordinal
        observation_lines[line_index] = current_line
    receptions_by_line: dict[int, list[Step11Rc0030ReceptionPredicationBinding]] = {}
    for row in reception_predications:
        expected_targets = tuple(
            referent_by_owner.get(value) for value in row.source_target_owner_ids
        )
        expected_supports = tuple(
            referent_by_owner.get(value)
            for value in row.supporting_source_owner_ids
        )
        if (
            row.association_basis
            not in {
                "exact_base_opportunity_id",
                "required_opportunity_bounded_schedule",
            }
            or row.additional_clause
            is not (
                row.association_basis
                == "required_opportunity_bounded_schedule"
            )
            or (
                row.association_basis == "exact_base_opportunity_id"
                and not row.source_base_binding_id
            )
            or (
                row.association_basis
                == "required_opportunity_bounded_schedule"
                and row.source_base_binding_id is not None
            )
            or not row.source_target_owner_ids
            or None in expected_targets
            or None in expected_supports
            or row.target_referent_texts != expected_targets
            or row.supporting_referent_texts != expected_supports
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_RECEPTION_PREDICATION_INVALID"
            )
        receptions_by_line.setdefault(row.reception_line_ordinal, []).append(row)
    act_fragments = catalog["reception_act_predicate_fragments"]
    for line_ordinal, rows in receptions_by_line.items():
        if not 1 <= line_ordinal <= len(reception_lines):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_RECEPTION_GROUP_INVALID"
            )
        if len(rows) > _STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0030_RECEPTION_DENSITY_UNSATISFIABLE"
            )
        predications: list[str] = []
        for row in sorted(
            rows,
            key=lambda item: (
                item.chunk_ordinal,
                item.source_reception_opportunity_id,
            ),
        ):
            act = act_fragments.get(row.reception_act)
            if type(act) is not str or not act:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_RECEPTION_ACT_INVALID"
                )
            support = ""
            if row.supporting_referent_texts:
                support = (
                    morphology["support_join"].join(
                        row.supporting_referent_texts
                    )
                    + morphology["support_particle"]
                    + morphology["clause_join"]
                )
            predication = (
                support
                + morphology["target_join"].join(row.target_referent_texts)
                + morphology["object_particle"]
                + act
            )
            if any(marker in predication for marker in ("\r", "\n", "「", "」")):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0030_RECEPTION_PREDICATION_INVALID"
                )
            predications.append(predication)
        reception_lines[line_ordinal - 1] = (
            morphology["grammatical_chunk_join"].join(predications) + suffix
        )
    final_text = "\n".join(observation_lines) + marker + "\n".join(reception_lines)
    body = final_text.encode("utf-8", errors="strict")
    return Step11Rc0030ExperimentRenderedSurface(
        schema_version=STEP11_RC0030_EXPERIMENT_RENDERED_SCHEMA,
        utf8_bytes=body,
        sha256=hashlib.sha256(body).hexdigest(),
        observation_group_count=len(observation_lines) - 1,
        semantic_atom_count=len(surface_realization_plan.semantic_chunk_bindings),
        exact_reuse_count=len(
            surface_realization_plan.base_body_exact_reuse_bindings
        ),
        reception_predication_count=len(reception_predications),
    )


def _step11_rc0030_candidate_identity(
    *,
    base_candidate_id: str,
    rendered: Step11Rc0030ExperimentRenderedSurface,
    plan: Step11Rc0030SurfaceRealizationPlan,
) -> str:
    return "nls3s11rc0030cand_" + artifact_sha256(
        {
            "candidate_version_id": STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID,
            "base_candidate_id": base_candidate_id,
            "final_bytes_sha256": rendered.sha256,
            "realization_plan_id": plan.realization_plan_id,
        }
    )[:20]


def _build_step11_rc0030_experiment_surface_candidate(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    base_body_exact_reuse_bindings: Sequence[
        Step11Rc0030BaseBodyExactReuseBinding
    ],
    validate_output: bool,
) -> Step11Rc0030ExperimentSurfaceCandidate:
    if type(base_candidate) is not Step11NaturalSurfaceCandidate:
        raise Step11NaturalSurfaceError("STEP11_RC0030_BASE_CANDIDATE_INVALID")
    lexical_sha256 = _step11_rc0028_validate_lexical_specs(
        lexical_atom_specs, successor_snapshot=successor_snapshot
    )
    catalog, catalog_sha256 = _step11_rc0030_catalog()
    del catalog
    lexical_owner = __import__(
        "emlis_ai_step11_grounded_lexicalization_v3",
        fromlist=(
            "build_step11_rc0030_clause_ready_lexical_specs",
            "validate_step11_rc0030_clause_ready_lexical_specs",
        ),
    )
    clause_ready = lexical_owner.build_step11_rc0030_clause_ready_lexical_specs(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    lexical_issues = lexical_owner.validate_step11_rc0030_clause_ready_lexical_specs(
        clause_ready,
        base_candidate=base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    if lexical_issues:
        raise Step11NaturalSurfaceError(lexical_issues[0])
    if clause_ready.surface_catalog_sha256 != catalog_sha256:
        raise Step11NaturalSurfaceError("STEP11_RC0030_CATALOG_COMMITMENT_MISMATCH")
    rc0028_catalog, _rc0028_catalog_sha256 = _step11_rc0028_catalog()
    owner_registry, constructions, relations, links, unknowns = (
        _step11_rc0028_forward_atoms(
            successor_snapshot, lexical_atom_specs, rc0028_catalog
        )
    )
    reception_predications = _step11_rc0030_reception_predications(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexemes=_step11_rc0030_lexemes(clause_ready),
    )
    plan = build_step11_rc0030_surface_realization_plan(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        clause_ready_lexical_specs=clause_ready,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_predications=reception_predications,
        base_body_exact_reuse_bindings=base_body_exact_reuse_bindings,
    )
    rendered = render_step11_rc0030_experiment_surface(
        base_candidate,
        clause_ready_lexical_specs=clause_ready,
        surface_realization_plan=plan,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_predications=reception_predications,
    )
    candidate = Step11Rc0030ExperimentSurfaceCandidate(
        schema_version=STEP11_RC0030_EXPERIMENT_CANDIDATE_SCHEMA,
        candidate_version_id=STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID,
        candidate_id=_step11_rc0030_candidate_identity(
            base_candidate_id=base_candidate.candidate_id,
            rendered=rendered,
            plan=plan,
        ),
        base_candidate=base_candidate,
        rendered_surface=rendered,
        surface_realization_plan=plan,
        successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
        lexical_atom_specs_sha256=lexical_sha256,
        experiment_catalog_sha256=catalog_sha256,
        natural_handle_specs=clause_ready,
        owner_registry=owner_registry,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_bindings=reception_predications,
        semantic_coverage_authorized=False,
        replan_count=0,
    )
    if validate_output:
        issues = validate_step11_rc0030_experiment_surface_candidate(
            candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        if issues:
            raise Step11NaturalSurfaceError(issues[0])
    return candidate


def build_step11_rc0030_experiment_surface_candidate(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    base_body_exact_reuse_bindings: Sequence[
        Step11Rc0030BaseBodyExactReuseBinding
    ] = (),
) -> Step11Rc0030ExperimentSurfaceCandidate:
    return _build_step11_rc0030_experiment_surface_candidate(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        base_body_exact_reuse_bindings=base_body_exact_reuse_bindings,
        validate_output=True,
    )


def build_step11_rc0030_experiment_surface_candidates(
    base_candidates: Sequence[Step11NaturalSurfaceCandidate],
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    base_body_exact_reuse_bindings: Sequence[
        Step11Rc0030BaseBodyExactReuseBinding
    ] = (),
) -> tuple[Step11Rc0030ExperimentSurfaceCandidate, ...]:
    if (
        type(base_candidates) not in {tuple, list}
        or not base_candidates
        or len(base_candidates) > _STEP11_RC0030_CANDIDATE_MAX
    ):
        raise Step11NaturalSurfaceError("STEP11_RC0030_CANDIDATE_BOUND_INVALID")
    rows: list[Step11Rc0030ExperimentSurfaceCandidate] = []
    for base_candidate in base_candidates:
        try:
            rows.append(
                build_step11_rc0030_experiment_surface_candidate(
                    base_candidate,
                    successor_snapshot=successor_snapshot,
                    lexical_atom_specs=lexical_atom_specs,
                    base_body_exact_reuse_bindings=(
                        base_body_exact_reuse_bindings
                    ),
                )
            )
        except (Step11GroundedLexicalizationError, Step11NaturalSurfaceError):
            continue
    if not rows:
        raise Step11NaturalSurfaceError("STEP11_RC0030_NO_VALID_FORWARD_CANDIDATE")
    return tuple(rows)


def validate_step11_rc0030_experiment_surface_candidate(
    value: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0030ExperimentSurfaceCandidate:
        return ("STEP11_RC0030_CANDIDATE_TYPE_INVALID",)
    issues: set[str] = set()
    try:
        expected = _build_step11_rc0030_experiment_surface_candidate(
            value.base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            base_body_exact_reuse_bindings=(
                value.surface_realization_plan.base_body_exact_reuse_bindings
            ),
            validate_output=False,
        )
    except (
        AttributeError,
        KeyError,
        TypeError,
        UnicodeError,
        ValueError,
        Step11GroundedLexicalizationError,
        Step11NaturalSurfaceError,
    ):
        return ("STEP11_RC0030_CANDIDATE_REVALIDATION_FAILED",)
    if value != expected:
        issues.add("STEP11_RC0030_CANDIDATE_SOURCE_MISMATCH")
    if value.semantic_coverage_authorized is not False:
        issues.add("STEP11_RC0030_SEMANTIC_COVERAGE_SELF_CLAIM")
    if (
        value.experimental_only is not True
        or value.private_body_full is not True
        or value.shareable is not False
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_RC0030_RUNTIME_BOUNDARY_INVALID")
    if type(value.replan_count) is not int or not 0 <= value.replan_count <= 1:
        issues.add("STEP11_RC0030_REPLAN_BOUND_EXCEEDED")
    return tuple(sorted(issues))


__all__ += [
    "STEP11_RC0030_EXPERIMENT_CANDIDATE_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_CANDIDATE_VERSION_ID",
    "STEP11_RC0030_EXPERIMENT_PLAN_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_RENDERED_SCHEMA",
    "Step11Rc0030BaseBodyExactReuseBinding",
    "Step11Rc0030ExperimentRenderedSurface",
    "Step11Rc0030ExperimentSurfaceCandidate",
    "Step11Rc0030ObservationChunkAssignment",
    "Step11Rc0030ReceptionPredicationBinding",
    "Step11Rc0030SemanticChunkBinding",
    "Step11Rc0030SurfaceRealizationPlan",
    "build_step11_rc0030_experiment_surface_candidate",
    "build_step11_rc0030_experiment_surface_candidates",
    "build_step11_rc0030_surface_realization_plan",
    "render_step11_rc0030_experiment_surface",
    "step11_rc0030_surface_realization_plan_material",
    "validate_step11_rc0030_experiment_surface_candidate",
]


# ---------------------------------------------------------------------------
# rc0031 experiment-only Proposition Surface (append-only P2 forward owner)
# ---------------------------------------------------------------------------

STEP11_RC0031_EXPERIMENT_CANDIDATE_VERSION_ID = (
    "nls_v3_rc_0031_proposition_surface_experiment"
)
STEP11_RC0031_EXPERIMENT_PLAN_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_proposition_surface_plan.v1"
)
STEP11_RC0031_EXPERIMENT_AST_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_proposition_surface_ast.v1"
)
STEP11_RC0031_EXPERIMENT_RENDERED_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_experiment_rendered_surface.v1"
)
STEP11_RC0031_EXPERIMENT_CANDIDATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_experiment_candidate.v1"
)

_STEP11_RC0031_CANDIDATE_MAX = 12
_STEP11_RC0031_REPLAN_MAX = 1
_STEP11_RC0031_OWNER_MAX = 24
_STEP11_RC0031_REALIZATION_UNITS_PER_GROUP_MAX = 4
_STEP11_RC0031_RECEPTION_MOVE_MAX = 3
_STEP11_RC0031_RECEPTION_SENTENCE_MAX = 3
_STEP11_RC0031_RECEPTION_MOVES_PER_SENTENCE_MAX = 2
_STEP11_RC0031_EXACT_MATCH_BASIS = {
    "construction": "construction_instance_role_layout_exact",
    "relation": "relation_id_endpoint_direction_type_exact",
    "semantic_link": "semantic_link_id_endpoint_direction_type_exact",
    "explicit_unknown": "unknown_id_dimension_exact_target",
}
_STEP11_RC0031_BASE_PARSED_ATOM_ID_RE = re.compile(
    r"^nls3s11atom_[0-9a-f]{16}$"
)
_STEP11_RC0031_BASE_OBLIGATION_ID_RE = re.compile(r"^obl_[0-9a-f]{16}$")

# Public P2 inputs are intentionally smaller than the general Python
# ``Sequence`` protocol.  Exact builtin containers let the boundary inspect
# length before iteration, so a caller cannot smuggle an unbounded or
# side-effecting iterator into the forward owner.
_STEP11_RC0031_CONSTRUCTION_ATOM_MAX = 13
_STEP11_RC0031_RELATION_ATOM_MAX = 28
_STEP11_RC0031_SEMANTIC_LINK_ATOM_MAX = 10
_STEP11_RC0031_EXPLICIT_UNKNOWN_ATOM_MAX = 4
_STEP11_RC0031_EXACT_REUSE_MAX = 64
_STEP11_RC0031_STRUCTURAL_COMPARE_NODE_MAX = 32768
_STEP11_RC0031_COMPOSITION_MODES = frozenset(
    {"construction_modified_head", "independent_clauses"}
)

_STEP11_RC0031_KNOWN_ERROR_CODES = frozenset(
    {
        "STEP11_RC0031_AST_PLAN_MISMATCH",
        "STEP11_RC0031_BASE_CANDIDATE_COMMITMENT_INVALID",
        "STEP11_RC0031_BASE_CANDIDATE_INVALID",
        "STEP11_RC0031_BASE_PLAN_INVALID",
        "STEP11_RC0031_BASE_REUSE_TYPE_INVALID",
        "STEP11_RC0031_BASE_SURFACE_INVALID",
        "STEP11_RC0031_BASE_SURFACE_LAYOUT_INVALID",
        "STEP11_RC0031_CANDIDATE_BOUND_INVALID",
        "STEP11_RC0031_CANDIDATE_INPUT_INVALID",
        "STEP11_RC0031_CANDIDATE_REVALIDATION_FAILED",
        "STEP11_RC0031_CANDIDATE_SOURCE_MISMATCH",
        "STEP11_RC0031_CANDIDATE_TYPE_INVALID",
        "STEP11_RC0031_CANONICAL_RENDER_MISMATCH",
        "STEP11_RC0031_CATALOG_COMMITMENT_MISMATCH",
        "STEP11_RC0031_CLAUSE_READY_LEXEME_SET_INVALID",
        "STEP11_RC0031_CONSTRUCTION_OWNER_AMBIGUOUS",
        "STEP11_RC0031_COMPOSITION_INVALID",
        "STEP11_RC0031_LEXICAL_PROJECTION_COMMITMENT_INVALID",
        "STEP11_RC0031_NO_VALID_FORWARD_CANDIDATE",
        "STEP11_RC0031_OWNER_BASE_GROUP_UNRESOLVED",
        "STEP11_RC0031_OWNER_CONNECTED_GROUP_UNRESOLVED",
        "STEP11_RC0031_OWNER_REGISTRY_INVALID",
        "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE",
        "STEP11_RC0031_PLAN_INPUT_INVALID",
        "STEP11_RC0031_PROPOSITION_CLAUSE_INVALID",
        "STEP11_RC0031_RECEPTION_ASSOCIATION_AMBIGUOUS",
        "STEP11_RC0031_RECEPTION_ASSOCIATION_INVALID",
        "STEP11_RC0031_RECEPTION_COMPLEXITY_BOUND_EXCEEDED",
        "STEP11_RC0031_RECEPTION_DENSITY_UNSATISFIABLE",
        "STEP11_RC0031_RECEPTION_GROUP_BOUND_INVALID",
        "STEP11_RC0031_RECEPTION_MOVE_BOUND_INVALID",
        "STEP11_RC0031_RECEPTION_OWNER_UNRESOLVED",
        "STEP11_RC0031_RECEPTION_PLAN_MISMATCH",
        "STEP11_RC0031_RECEPTION_PREDICATION_INVALID",
        "STEP11_RC0031_RECEPTION_SOURCE_BINDING_INVALID",
        "STEP11_RC0031_RELATION_DIRECTION_INVALID",
        "STEP11_RC0031_RELATION_ENDPOINT_INVALID",
        "STEP11_RC0031_RELATION_PATTERN_INVALID",
        "STEP11_RC0031_RENDER_CLAUSE_COUNT_MISMATCH",
        "STEP11_RC0031_RENDER_GROUP_INVALID",
        "STEP11_RC0031_RENDER_INPUT_INVALID",
        "STEP11_RC0031_RENDER_LEXICAL_AUTHORITY_MISMATCH",
        "STEP11_RC0031_RENDER_OWNER_UNRESOLVED",
        "STEP11_RC0031_RENDER_PLAN_AUTHORITY_MISMATCH",
        "STEP11_RC0031_RENDER_SOURCE_ATOM_MISMATCH",
        "STEP11_RC0031_REPLAN_BOUND_EXCEEDED",
        "STEP11_RC0031_RESOURCE_CONTRACT_MISMATCH",
        "STEP11_RC0031_ROOT_PROPOSITION_DISPLACED",
        "STEP11_RC0031_ROOT_PROPOSITION_UNRESOLVED",
        "STEP11_RC0031_RUNTIME_BOUNDARY_INVALID",
        "STEP11_RC0031_SEMANTIC_ATOM_COVERAGE_INVALID",
        "STEP11_RC0031_SEMANTIC_COVERAGE_SELF_CLAIM",
        "STEP11_RC0031_SEMANTIC_FAMILY_INVALID",
        "STEP11_RC0031_SOURCE_ATOM_ID_COLLISION",
        "STEP11_RC0031_SURFACE_PLAN_DENSITY_UNSATISFIABLE",
        "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID",
    }
)


def _step11_rc0031_exact_bounded_rows(
    value: Any,
    *,
    item_types: tuple[type, ...],
    maximum: int,
    allow_empty: bool = True,
) -> tuple[Any, ...]:
    """Preflight one finite exact list/tuple before reading any element."""

    if type(value) not in {tuple, list}:
        raise TypeError("rc0031 exact finite sequence required")
    size = len(value)
    if size > maximum or (not allow_empty and size == 0):
        raise TypeError("rc0031 sequence bound invalid")
    rows = tuple(value)
    if any(type(row) not in item_types for row in rows):
        raise TypeError("rc0031 sequence item type invalid")
    return rows


def _step11_rc0031_safe_structural_equal(left: Any, right: Any) -> bool:
    """Compare canonical structures without invoking caller-defined equality."""

    remaining = [_STEP11_RC0031_STRUCTURAL_COMPARE_NODE_MAX]
    seen: set[tuple[int, int]] = set()

    def compare(actual: Any, expected: Any) -> bool:
        remaining[0] -= 1
        if remaining[0] < 0 or type(actual) is not type(expected):
            return False
        value_type = type(expected)
        if value_type in {type(None), bool, int, float, str, bytes}:
            return bool(actual == expected)
        pair = (id(actual), id(expected))
        if pair in seen:
            return True
        seen.add(pair)
        if value_type in {tuple, list}:
            return len(actual) == len(expected) and all(
                compare(actual_row, expected_row)
                for actual_row, expected_row in zip(
                    actual, expected, strict=True
                )
            )
        if value_type is dict:
            if len(actual) != len(expected):
                return False
            return all(
                compare(actual_key, expected_key)
                and compare(actual_value, expected_value)
                for (actual_key, actual_value), (
                    expected_key,
                    expected_value,
                ) in zip(actual.items(), expected.items(), strict=True)
            )
        dataclass_fields = getattr(value_type, "__dataclass_fields__", None)
        if type(dataclass_fields) is dict:
            return all(
                compare(
                    getattr(actual, field_name),
                    getattr(expected, field_name),
                )
                for field_name in dataclass_fields
            )
        # No equality fallback is permitted for an unknown object type.
        return actual is expected

    try:
        return compare(left, right)
    except Exception:
        return False


def _step11_rc0031_boundary_error(
    exc: Exception,
    *,
    input_invalid_code: str,
) -> Step11NaturalSurfaceError:
    """Preserve only P2-owned closed codes at an exported input boundary."""

    if (
        type(exc) is Step11NaturalSurfaceError
        and type(exc.code) is str
        and exc.code in _STEP11_RC0031_KNOWN_ERROR_CODES
    ):
        return Step11NaturalSurfaceError(exc.code)
    return Step11NaturalSurfaceError(input_invalid_code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0031BaseBodyExactReuseBinding:
    """Reserved P3 body-only commitment; every non-empty P2 value is rejected."""

    source_atom_id: str
    semantic_family: str
    base_parsed_atom_id: str
    base_obligation_id: str
    match_basis: str
    base_surface_sha256: str
    source_authority_sha256: str
    independent_binding_sha256: str


@dataclass(frozen=True, slots=True)
class Step11Rc0031RootPropositionBinding:
    source_semantic_unit_id: str
    source_owner_nucleus_ids: tuple[str, ...]
    source_obligation_ids: tuple[str, ...]
    source_order: int
    sentence_group_ordinal: int
    grammatical_chunk_ordinal: int
    predicate_grounding_basis: str
    complete_base_proposition_preserved: bool


@dataclass(frozen=True, slots=True)
class Step11Rc0031PropositionClauseBinding:
    proposition_unit_id: str
    composition_mode: str
    head_source_atom_id: str
    construction_modifier_atom_ids: tuple[str, ...]
    construction_modifier_target_owner_ids: tuple[str, ...]
    owner_ready_group_ordinal: int
    source_atom_ids: tuple[str, ...]
    semantic_families: tuple[str, ...]
    semantic_keys: tuple[str, ...]
    source_atom_owner_ids: tuple[tuple[str, ...], ...]
    source_owner_ids: tuple[str, ...]
    owner_base_nucleus_ids: tuple[str, ...]
    owner_sentence_group_ordinals: tuple[int, ...]
    sentence_group_ordinal: int
    grammatical_chunk_ordinal: int
    visible_clause_count: int
    complexity_load: int
    cross_group_bridge: bool
    directions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Step11Rc0031PropositionChunkAssignment:
    sentence_group_ordinal: int
    grammatical_chunk_ordinal: int
    source_unit_ids: tuple[str, ...]
    source_atom_ids: tuple[str, ...]
    visible_clause_count: int
    complexity_load: int


@dataclass(frozen=True, slots=True)
class Step11Rc0031ReceptionPredicationBinding:
    reception_line_ordinal: int
    sentence_group_ordinal: int
    grammatical_chunk_ordinal: int
    source_base_binding_id: str | None
    source_reception_opportunity_id: str
    source_scope: str
    reception_act: str
    source_target_owner_ids: tuple[str, ...]
    supporting_source_owner_ids: tuple[str, ...]
    association_basis: str
    additional_clause: bool


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0031SurfaceRealizationPlan:
    schema_version: str
    candidate_version_id: str
    realization_plan_id: str
    source_base_candidate_id: str
    source_base_realization_plan_id: str
    source_successor_snapshot_sha256: str
    source_lexical_atom_specs_sha256: str
    source_clause_ready_lexical_specs_sha256: str
    source_lexical_projection_catalog_sha256: str
    surface_catalog_sha256: str
    root_proposition_binding: Step11Rc0031RootPropositionBinding
    proposition_chunk_assignments: tuple[
        Step11Rc0031PropositionChunkAssignment, ...
    ]
    proposition_clause_bindings: tuple[
        Step11Rc0031PropositionClauseBinding, ...
    ]
    base_body_exact_reuse_bindings: tuple[
        Step11Rc0031BaseBodyExactReuseBinding, ...
    ]
    reception_predication_bindings: tuple[
        Step11Rc0031ReceptionPredicationBinding, ...
    ]
    maximum_observation_clauses_per_sentence: int
    maximum_visible_clauses_per_grammatical_sentence: int
    maximum_grammatical_complexity_load: int
    maximum_repeated_joiner_per_group: int
    peak_observation_clause_count: int
    peak_grammatical_clause_count: int
    peak_grammatical_complexity_load: int
    peak_group_repeated_joiner_count: int
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0031PropositionSurfaceAst:
    schema_version: str
    ast_id: str
    source_base_candidate_id: str
    source_base_surface_ast_id: str
    root_proposition_binding: Step11Rc0031RootPropositionBinding
    proposition_clause_bindings: tuple[
        Step11Rc0031PropositionClauseBinding, ...
    ]
    reception_predication_bindings: tuple[
        Step11Rc0031ReceptionPredicationBinding, ...
    ]
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0031ExperimentRenderedSurface:
    schema_version: str
    utf8_bytes: bytes
    sha256: str
    observation_group_count: int
    proposition_clause_count: int
    semantic_atom_count: int
    exact_reuse_count: int
    reception_predication_count: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11Rc0031ExperimentSurfaceCandidate:
    schema_version: str
    candidate_version_id: str
    candidate_id: str
    base_candidate: Step11NaturalSurfaceCandidate
    proposition_surface_ast: Step11Rc0031PropositionSurfaceAst
    rendered_surface: Step11Rc0031ExperimentRenderedSurface
    surface_realization_plan: Step11Rc0031SurfaceRealizationPlan
    successor_snapshot_sha256: str
    lexical_atom_specs_sha256: str
    experiment_catalog_sha256: str
    source_lexical_projection_catalog_sha256: str
    natural_handle_specs: Any
    owner_registry: tuple[str, ...]
    construction_atoms: tuple[Step11Rc0028ExperimentConstructionAtom, ...]
    relation_atoms: tuple[Step11Rc0028ExperimentRelationAtom, ...]
    semantic_link_atoms: tuple[Step11Rc0028ExperimentSemanticLinkAtom, ...]
    explicit_unknown_atoms: tuple[Step11Rc0028ExperimentExplicitUnknownAtom, ...]
    reception_bindings: tuple[Step11Rc0031ReceptionPredicationBinding, ...]
    semantic_coverage_authorized: bool
    replan_count: int
    experimental_only: bool = True
    private_body_full: bool = True
    shareable: bool = False
    runtime_connected: bool = False

    @property
    def final_utf8_bytes(self) -> bytes:
        return self.rendered_surface.utf8_bytes


def _step11_rc0031_preflight_forward_rows(
    *,
    construction_atoms: Any,
    relation_atoms: Any,
    semantic_link_atoms: Any,
    explicit_unknown_atoms: Any,
    reception_predications: Any,
) -> tuple[tuple[Any, ...], ...]:
    """Bound every public forward collection before a planner can iterate."""

    return (
        _step11_rc0031_exact_bounded_rows(
            construction_atoms,
            item_types=(Step11Rc0028ExperimentConstructionAtom,),
            maximum=_STEP11_RC0031_CONSTRUCTION_ATOM_MAX,
        ),
        _step11_rc0031_exact_bounded_rows(
            relation_atoms,
            item_types=(Step11Rc0028ExperimentRelationAtom,),
            maximum=_STEP11_RC0031_RELATION_ATOM_MAX,
        ),
        _step11_rc0031_exact_bounded_rows(
            semantic_link_atoms,
            item_types=(Step11Rc0028ExperimentSemanticLinkAtom,),
            maximum=_STEP11_RC0031_SEMANTIC_LINK_ATOM_MAX,
        ),
        _step11_rc0031_exact_bounded_rows(
            explicit_unknown_atoms,
            item_types=(Step11Rc0028ExperimentExplicitUnknownAtom,),
            maximum=_STEP11_RC0031_EXPLICIT_UNKNOWN_ATOM_MAX,
        ),
        _step11_rc0031_exact_bounded_rows(
            reception_predications,
            item_types=(Step11Rc0031ReceptionPredicationBinding,),
            maximum=_STEP11_RC0031_RECEPTION_MOVE_MAX,
        ),
    )


def _step11_rc0031_exact_reuse_material(
    value: Step11Rc0031BaseBodyExactReuseBinding,
) -> dict[str, Any]:
    return {
        "source_atom_id": value.source_atom_id,
        "semantic_family": value.semantic_family,
        "base_parsed_atom_id": value.base_parsed_atom_id,
        "base_obligation_id": value.base_obligation_id,
        "match_basis": value.match_basis,
        "source_authority_sha256": value.source_authority_sha256,
        "independent_binding_sha256": value.independent_binding_sha256,
        "base_surface_bound_by_source_base_candidate_id": True,
    }


def _step11_rc0031_root_material(
    value: Step11Rc0031RootPropositionBinding,
) -> dict[str, Any]:
    return {
        "source_semantic_unit_id": value.source_semantic_unit_id,
        "source_owner_nucleus_ids": list(value.source_owner_nucleus_ids),
        "source_obligation_ids": list(value.source_obligation_ids),
        "source_order": value.source_order,
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "grammatical_chunk_ordinal": value.grammatical_chunk_ordinal,
        "predicate_grounding_basis": value.predicate_grounding_basis,
        "complete_base_proposition_preserved": (
            value.complete_base_proposition_preserved
        ),
    }


def _step11_rc0031_proposition_binding_material(
    value: Step11Rc0031PropositionClauseBinding,
) -> dict[str, Any]:
    return {
        "proposition_unit_id": value.proposition_unit_id,
        "composition_mode": value.composition_mode,
        "head_source_atom_id": value.head_source_atom_id,
        "construction_modifier_atom_ids": list(
            value.construction_modifier_atom_ids
        ),
        "construction_modifier_target_owner_ids": list(
            value.construction_modifier_target_owner_ids
        ),
        "owner_ready_group_ordinal": value.owner_ready_group_ordinal,
        "source_atom_ids": list(value.source_atom_ids),
        "semantic_families": list(value.semantic_families),
        "semantic_keys": list(value.semantic_keys),
        "source_atom_owner_ids": [
            list(row) for row in value.source_atom_owner_ids
        ],
        "source_owner_ids": list(value.source_owner_ids),
        "owner_base_nucleus_ids": list(value.owner_base_nucleus_ids),
        "owner_sentence_group_ordinals": list(
            value.owner_sentence_group_ordinals
        ),
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "grammatical_chunk_ordinal": value.grammatical_chunk_ordinal,
        "visible_clause_count": value.visible_clause_count,
        "complexity_load": value.complexity_load,
        "cross_group_bridge": value.cross_group_bridge,
        "directions": list(value.directions),
    }


def _step11_rc0031_chunk_assignment_material(
    value: Step11Rc0031PropositionChunkAssignment,
) -> dict[str, Any]:
    return {
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "grammatical_chunk_ordinal": value.grammatical_chunk_ordinal,
        "source_unit_ids": list(value.source_unit_ids),
        "source_atom_ids": list(value.source_atom_ids),
        "visible_clause_count": value.visible_clause_count,
        "complexity_load": value.complexity_load,
    }


def _step11_rc0031_reception_binding_material(
    value: Step11Rc0031ReceptionPredicationBinding,
) -> dict[str, Any]:
    return {
        "reception_line_ordinal": value.reception_line_ordinal,
        "sentence_group_ordinal": value.sentence_group_ordinal,
        "grammatical_chunk_ordinal": value.grammatical_chunk_ordinal,
        "source_base_binding_id": value.source_base_binding_id,
        "source_reception_opportunity_id": (
            value.source_reception_opportunity_id
        ),
        "source_scope": value.source_scope,
        "reception_act": value.reception_act,
        "source_target_owner_ids": list(value.source_target_owner_ids),
        "supporting_source_owner_ids": list(
            value.supporting_source_owner_ids
        ),
        "association_basis": value.association_basis,
        "additional_clause": value.additional_clause,
    }


def step11_rc0031_surface_realization_plan_material(
    value: Step11Rc0031SurfaceRealizationPlan,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "candidate_version_id": value.candidate_version_id,
        "realization_plan_id": value.realization_plan_id,
        "source_base_candidate_id": value.source_base_candidate_id,
        "source_base_realization_plan_id": (
            value.source_base_realization_plan_id
        ),
        "source_successor_snapshot_sha256": (
            value.source_successor_snapshot_sha256
        ),
        "source_lexical_atom_specs_sha256": (
            value.source_lexical_atom_specs_sha256
        ),
        "source_clause_ready_lexical_specs_sha256": (
            value.source_clause_ready_lexical_specs_sha256
        ),
        "source_lexical_projection_catalog_sha256": (
            value.source_lexical_projection_catalog_sha256
        ),
        "surface_catalog_sha256": value.surface_catalog_sha256,
        "root_proposition_binding": _step11_rc0031_root_material(
            value.root_proposition_binding
        ),
        "proposition_chunk_assignments": [
            _step11_rc0031_chunk_assignment_material(row)
            for row in value.proposition_chunk_assignments
        ],
        "proposition_clause_bindings": [
            _step11_rc0031_proposition_binding_material(row)
            for row in value.proposition_clause_bindings
        ],
        "base_body_exact_reuse_bindings": [
            _step11_rc0031_exact_reuse_material(row)
            for row in value.base_body_exact_reuse_bindings
        ],
        "reception_predication_bindings": [
            _step11_rc0031_reception_binding_material(row)
            for row in value.reception_predication_bindings
        ],
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
        "peak_observation_clause_count": value.peak_observation_clause_count,
        "peak_grammatical_clause_count": value.peak_grammatical_clause_count,
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


def _step11_rc0031_ast_material(
    value: Step11Rc0031PropositionSurfaceAst,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    result = {
        "schema_version": value.schema_version,
        "ast_id": value.ast_id,
        "source_base_candidate_id": value.source_base_candidate_id,
        "source_base_surface_ast_id": value.source_base_surface_ast_id,
        "root_proposition_binding": _step11_rc0031_root_material(
            value.root_proposition_binding
        ),
        "proposition_clause_bindings": [
            _step11_rc0031_proposition_binding_material(row)
            for row in value.proposition_clause_bindings
        ],
        "reception_predication_bindings": [
            _step11_rc0031_reception_binding_material(row)
            for row in value.reception_predication_bindings
        ],
        "body_free": value.body_free,
    }
    if not include_id:
        result.pop("ast_id")
    return result


def _step11_rc0031_catalog() -> tuple[dict[str, Any], str]:
    owner = __import__(
        "emlis_ai_step11_rc0031_experiment_surface_catalog_v3",
        fromlist=(
            "STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG",
            "STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256",
            "validate_step11_rc0031_experiment_surface_catalog",
        ),
    )
    catalog = owner.STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG
    issues = owner.validate_step11_rc0031_experiment_surface_catalog(catalog)
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    return catalog, owner.STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256


def _step11_rc0031_clause_ready_projection(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> Any:
    """Reuse the public grounded projection, not any rc0030 Surface output."""

    owner = __import__(
        "emlis_ai_step11_grounded_lexicalization_v3",
        fromlist=(
            "build_step11_rc0030_clause_ready_lexical_specs",
            "validate_step11_rc0030_clause_ready_lexical_specs",
        ),
    )
    projection = owner.build_step11_rc0030_clause_ready_lexical_specs(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    issues = owner.validate_step11_rc0030_clause_ready_lexical_specs(
        projection,
        base_candidate=base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    if issues:
        raise Step11NaturalSurfaceError(issues[0])
    return projection


def _step11_rc0031_clause_ready_types() -> tuple[type, type]:
    try:
        lexical_owner = __import__(
            "emlis_ai_step11_grounded_lexicalization_v3",
            fromlist=(
                "Step11Rc0030ClauseReadyLexeme",
                "Step11Rc0030ClauseReadyLexicalSpecs",
            ),
        )
        return (
            lexical_owner.Step11Rc0030ClauseReadyLexicalSpecs,
            lexical_owner.Step11Rc0030ClauseReadyLexeme,
        )
    except Exception as exc:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_CLAUSE_READY_LEXEME_SET_INVALID"
        ) from exc


def _step11_rc0031_preflight_clause_ready(value: Any) -> None:
    specs_type, lexeme_type = _step11_rc0031_clause_ready_types()
    if type(value) is not specs_type:
        raise TypeError("rc0031 clause-ready specs type invalid")
    rows = value.lexemes
    if (
        type(rows) is not tuple
        or not rows
        or len(rows) > _STEP11_RC0031_OWNER_MAX
        or any(type(row) is not lexeme_type for row in rows)
    ):
        raise TypeError("rc0031 clause-ready lexeme set invalid")


def _step11_rc0031_lexemes(value: Any) -> tuple[Any, ...]:
    rows = getattr(value, "lexemes", None)
    if type(rows) is not tuple or not rows:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_CLAUSE_READY_LEXEME_SET_INVALID"
        )
    _specs_type, lexeme_type = _step11_rc0031_clause_ready_types()
    if (
        len(rows) > _STEP11_RC0031_OWNER_MAX
        or any(
            type(row) is not lexeme_type
            or type(row.source_owner_id) is not str
            or not row.source_owner_id
            or type(row.source_owner_ordinal) is not int
            for row in rows
        )
        or len({row.source_owner_id for row in rows}) != len(rows)
        or len({row.source_owner_ordinal for row in rows}) != len(rows)
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_OWNER_REGISTRY_INVALID"
        )
    return rows


def _step11_rc0031_atom_records(
    *,
    lexemes: Sequence[Any],
    constructions: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relations: Sequence[Step11Rc0028ExperimentRelationAtom],
    links: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    unknowns: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
) -> tuple[
    tuple[str, str, tuple[str, ...], tuple[int, ...], str, str], ...
]:
    by_ordinal = {int(row.source_owner_ordinal): row for row in lexemes}

    def owners(ordinals: Sequence[int]) -> tuple[tuple[str, ...], tuple[int, ...]]:
        unique = tuple(dict.fromkeys(int(value) for value in ordinals))
        try:
            return tuple(
                str(by_ordinal[value].source_owner_id) for value in unique
            ), unique
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_OWNER_REGISTRY_INVALID"
            ) from exc

    records: list[
        tuple[str, str, tuple[str, ...], tuple[int, ...], str, str]
    ] = []
    for row in constructions:
        construction_ordinals = tuple(
            int(ordinal)
            for role in row.role_atoms
            for ordinal in role.target_owner_ordinals
        )
        if not construction_ordinals or len(set(construction_ordinals)) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_CONSTRUCTION_OWNER_AMBIGUOUS"
            )
        owner_ids, owner_ordinals = owners((construction_ordinals[0],))
        records.append(
            (
                str(row.construction_instance_id),
                "construction",
                owner_ids,
                owner_ordinals,
                "",
                str(row.construction_code),
            )
        )
    for row in relations:
        owner_ids, owner_ordinals = owners(
            (row.from_owner_ordinal, row.to_owner_ordinal)
        )
        records.append(
            (
                str(row.experiment_relation_id),
                "relation",
                owner_ids,
                owner_ordinals,
                str(row.direction),
                str(row.effective_relation_type),
            )
        )
    for row in links:
        owner_ids, owner_ordinals = owners(
            (row.from_owner_ordinal, row.to_owner_ordinal)
        )
        records.append(
            (
                str(row.source_semantic_link_id),
                "semantic_link",
                owner_ids,
                owner_ordinals,
                str(row.direction),
                str(row.relation_type),
            )
        )
    for row in unknowns:
        owner_ids, owner_ordinals = owners(row.affected_owner_ordinals)
        records.append(
            (
                str(row.source_unknown_id),
                "explicit_unknown",
                owner_ids,
                owner_ordinals,
                "",
                str(row.dimension),
            )
        )
    if len({row[0] for row in records}) != len(records):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_SOURCE_ATOM_ID_COLLISION"
        )
    return tuple(records)


def _step11_rc0031_owner_positions(
    base_candidate: Step11NaturalSurfaceCandidate,
    lexemes: Sequence[Any],
) -> dict[int, tuple[str, str, int, int]]:
    """Resolve each owner to one existing owner-connected rc0027 group."""

    base_plan = base_candidate.surface_ast.surface_realization_plan
    if type(base_plan) is not Step11SurfaceRealizationPlan:
        raise Step11NaturalSurfaceError("STEP11_RC0031_BASE_PLAN_INVALID")
    group_index = {
        group_id: ordinal
        for ordinal, group_id in enumerate(
            base_plan.observation_sentence_group_ids, start=1
        )
    }
    observation_units = tuple(
        row for row in base_plan.units if row.section_role == "observation"
    )
    references = tuple(base_candidate.surface_ast.nucleus_surface_references)
    positions: dict[int, tuple[str, str, int, int]] = {}
    for lexeme in lexemes:
        nucleus_id = str(lexeme.base_source_nucleus_id)
        owned_units = tuple(
            row for row in observation_units if nucleus_id in row.owner_nucleus_ids
        )
        owned_group_ids = {
            row.assigned_sentence_group_id for row in owned_units
        }
        lexical_group_ids = {
            str(value)
            for value in lexeme.base_observation_sentence_group_ids
            if str(value) in group_index
        }
        obligation_ids = {
            str(value) for value in lexeme.owner_obligation_ids
        }
        obligation_owned_units = tuple(
            row
            for row in owned_units
            if obligation_ids & {
                str(value) for value in row.owner_obligation_ids
            }
        )
        matching_refs = tuple(
            row for row in references if nucleus_id in row.nucleus_ids
        )
        reference_group_ids = {
            row.introduction_sentence_group_id
            for row in matching_refs
            if row.introduction_sentence_group_id in group_index
        }
        owned_lexical_group_ids = owned_group_ids & lexical_group_ids
        overlap_by_group = {
            group_id: len(
                obligation_ids
                & {
                    str(obligation_id)
                    for row in obligation_owned_units
                    if row.assigned_sentence_group_id == group_id
                    for obligation_id in row.owner_obligation_ids
                }
            )
            for group_id in owned_lexical_group_ids
        }
        maximum_overlap = max(overlap_by_group.values(), default=0)
        overlap_preferred = {
            group_id
            for group_id, overlap in overlap_by_group.items()
            if overlap == maximum_overlap and overlap > 0
        }
        if len(owned_group_ids) == 1:
            group_id = next(iter(owned_group_ids))
            candidates = tuple(
                row
                for row in owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif len(owned_lexical_group_ids) == 1:
            group_id = next(iter(owned_lexical_group_ids))
            candidates = tuple(
                row
                for row in owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif len(overlap_preferred) == 1:
            group_id = next(iter(overlap_preferred))
            candidates = tuple(
                row
                for row in obligation_owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif len(reference_group_ids & owned_lexical_group_ids) == 1:
            group_id = next(iter(reference_group_ids & owned_lexical_group_ids))
            candidates = tuple(
                row
                for row in owned_units
                if row.assigned_sentence_group_id == group_id
            )
        elif not owned_units and len(matching_refs) == 1:
            group_id = matching_refs[0].introduction_sentence_group_id
            candidates = tuple(
                row
                for row in observation_units
                if row.assigned_sentence_group_id == group_id
                and matching_refs[0].reference_ordinal
                in row.introduced_reference_ordinals
            )
        else:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_OWNER_BASE_GROUP_UNRESOLVED"
            )
        group_ordinal = group_index.get(group_id)
        if group_ordinal is None or not candidates:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_OWNER_BASE_GROUP_UNRESOLVED"
            )
        unit = min(
            candidates,
            key=lambda row: (
                row.assigned_grammatical_chunk_ordinal,
                row.source_order,
                row.semantic_unit_id,
            ),
        )
        positions[int(lexeme.source_owner_ordinal)] = (
            str(lexeme.source_owner_id),
            nucleus_id,
            group_ordinal,
            int(unit.assigned_grammatical_chunk_ordinal),
        )
    if len(positions) != len(lexemes):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_OWNER_BASE_GROUP_UNRESOLVED"
        )
    return positions


def _step11_rc0031_root_binding(
    base_candidate: Step11NaturalSurfaceCandidate,
) -> Step11Rc0031RootPropositionBinding:
    base_plan = base_candidate.surface_ast.surface_realization_plan
    group_index = {
        group_id: ordinal
        for ordinal, group_id in enumerate(
            base_plan.observation_sentence_group_ids, start=1
        )
    }
    ordered = tuple(
        sorted(
            (
                row
                for row in base_plan.units
                if row.section_role == "observation"
            ),
            key=lambda row: (row.source_order, row.semantic_unit_id),
        )
    )
    if (
        not ordered
        or sum(row.source_order == ordered[0].source_order for row in ordered)
        != 1
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_ROOT_PROPOSITION_UNRESOLVED"
        )
    leading = ordered[0]
    group_ordinal = group_index.get(leading.assigned_sentence_group_id)
    if (
        group_ordinal != 1
        or leading.assigned_grammatical_chunk_ordinal != 1
        or not leading.semantic_unit_id
        or not leading.owner_nucleus_ids
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_ROOT_PROPOSITION_UNRESOLVED"
        )
    return Step11Rc0031RootPropositionBinding(
        source_semantic_unit_id=str(leading.semantic_unit_id),
        source_owner_nucleus_ids=tuple(
            str(value) for value in leading.owner_nucleus_ids
        ),
        source_obligation_ids=tuple(
            str(value) for value in leading.owner_obligation_ids
        ),
        source_order=int(leading.source_order),
        sentence_group_ordinal=1,
        grammatical_chunk_ordinal=1,
        predicate_grounding_basis=(
            "immutable_rc0027_complete_leading_observation"
        ),
        complete_base_proposition_preserved=True,
    )


def _step11_rc0031_reception_predications(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexemes: Sequence[Any],
    catalog: Mapping[str, Any],
) -> tuple[Step11Rc0031ReceptionPredicationBinding, ...]:
    base_plan = base_candidate.surface_ast.surface_realization_plan
    group_count = len(base_plan.reception_sentence_group_ids)
    if not 1 <= group_count <= _STEP11_RC0031_RECEPTION_SENTENCE_MAX:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RECEPTION_GROUP_BOUND_INVALID"
        )
    nuclei = tuple(successor_snapshot.base_snapshot.nuclei)
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    known_owner_ids = {str(row.source_owner_id) for row in lexemes}
    base_bindings = tuple(
        base_candidate.surface_ast.reception_antecedent_bindings
    )
    exact: dict[str, tuple[int, Any]] = {}
    for line_ordinal, binding in enumerate(base_bindings, start=1):
        for opportunity_id in binding.source_reception_opportunity_ids:
            key = str(opportunity_id)
            if key in exact:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_RECEPTION_ASSOCIATION_AMBIGUOUS"
                )
            exact[key] = (line_ordinal, binding)
    opportunities = tuple(
        row
        for row in successor_snapshot.base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    if not 1 <= len(opportunities) <= _STEP11_RC0031_RECEPTION_MOVE_MAX:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RECEPTION_MOVE_BOUND_INVALID"
        )
    loads = {ordinal: 0 for ordinal in range(1, group_count + 1)}
    prepared: list[tuple[Any, int, Any | None, str]] = []
    for opportunity in opportunities:
        opportunity_id = str(opportunity.source_id)
        association = exact.get(opportunity_id)
        if association is not None:
            line_ordinal, binding = association
            if (
                not 1 <= line_ordinal <= group_count
                or str(opportunity.reception_act)
                not in {str(value) for value in binding.allowed_response_acts}
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_RECEPTION_ASSOCIATION_INVALID"
                )
            basis = "exact_base_opportunity_id"
        else:
            available = tuple(
                ordinal
                for ordinal in range(1, group_count + 1)
                if loads[ordinal]
                < _STEP11_RC0031_RECEPTION_MOVES_PER_SENTENCE_MAX
            )
            if not available:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_RECEPTION_DENSITY_UNSATISFIABLE"
                )
            line_ordinal = min(available, key=lambda value: (loads[value], value))
            binding = None
            basis = "required_opportunity_bounded_schedule"
        loads[line_ordinal] += 1
        if loads[line_ordinal] > _STEP11_RC0031_RECEPTION_MOVES_PER_SENTENCE_MAX:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RECEPTION_DENSITY_UNSATISFIABLE"
            )
        prepared.append((opportunity, line_ordinal, binding, basis))

    ordinal_counts = {ordinal: 0 for ordinal in loads}
    rows: list[Step11Rc0031ReceptionPredicationBinding] = []
    for opportunity, line_ordinal, binding, basis in prepared:
        try:
            target_ids = tuple(
                actual_by_source[str(value)]
                for value in opportunity.target_nucleus_ids
            )
            support_ids = tuple(
                actual_by_source[str(value)]
                for value in opportunity.support_nucleus_ids
            )
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RECEPTION_OWNER_UNRESOLVED"
            ) from exc
        if (
            not target_ids
            or len(set(target_ids)) != len(target_ids)
            or len(set(support_ids)) != len(support_ids)
            or len(target_ids) + len(support_ids)
            > base_plan.maximum_grammatical_complexity_load
            or not set((*target_ids, *support_ids)) <= known_owner_ids
            or str(opportunity.reception_act)
            not in catalog["reception_act_predicate_fragments"]
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RECEPTION_COMPLEXITY_BOUND_EXCEEDED"
                if len(target_ids) + len(support_ids)
                > base_plan.maximum_grammatical_complexity_load
                else "STEP11_RC0031_RECEPTION_SOURCE_BINDING_INVALID"
            )
        ordinal_counts[line_ordinal] += 1
        rows.append(
            Step11Rc0031ReceptionPredicationBinding(
                reception_line_ordinal=line_ordinal,
                sentence_group_ordinal=line_ordinal,
                grammatical_chunk_ordinal=ordinal_counts[line_ordinal],
                source_base_binding_id=(
                    str(binding.binding_id) if binding is not None else None
                ),
                source_reception_opportunity_id=str(opportunity.source_id),
                source_scope=str(opportunity.family),
                reception_act=str(opportunity.reception_act),
                source_target_owner_ids=target_ids,
                supporting_source_owner_ids=support_ids,
                association_basis=basis,
                additional_clause=binding is None,
            )
        )
    return tuple(rows)


def _step11_rc0031_validate_exact_reuse(
    rows: Sequence[Step11Rc0031BaseBodyExactReuseBinding],
    *,
    records: Sequence[
        tuple[str, str, tuple[str, ...], tuple[int, ...], str, str]
    ],
    base_candidate: Step11NaturalSurfaceCandidate,
    successor_snapshot: Any,
) -> tuple[Step11Rc0031BaseBodyExactReuseBinding, ...]:
    if (
        type(rows) not in {tuple, list}
        or len(rows) > _STEP11_RC0031_EXACT_REUSE_MAX
        or any(
            type(row) is not Step11Rc0031BaseBodyExactReuseBinding
            for row in rows
        )
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_BASE_REUSE_TYPE_INVALID"
        )
    reuse = tuple(rows)
    if reuse:
        # P2 has no Body-only Parser or Independent Matcher and therefore has
        # no authority to grant exact-reuse credit.  P3 must add a separately
        # verified composition boundary; caller-supplied metadata is rejected.
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE"
        )
    return ()


def _step11_rc0031_validate_verified_reuse_composition(
    rows: Sequence[Step11Rc0031BaseBodyExactReuseBinding],
    *,
    records: Sequence[
        tuple[str, str, tuple[str, ...], tuple[int, ...], str, str]
    ],
    base_candidate: Step11NaturalSurfaceCandidate,
    successor_snapshot: Any,
) -> tuple[Step11Rc0031BaseBodyExactReuseBinding, ...]:
    """Validate a same-call body-free projection for private composition.

    The digests are consistency commitments, not signatures or proof of the
    caller's identity.  Public P2 inputs remain closed, and final independent
    Parser / Matcher revalidation is still required before activation.
    """

    if (
        type(rows) is not tuple
        or len(rows) > _STEP11_RC0031_EXACT_REUSE_MAX
        or any(
            type(row) is not Step11Rc0031BaseBodyExactReuseBinding
            or any(
                type(value) is not str
                for value in (
                    row.source_atom_id,
                    row.semantic_family,
                    row.base_parsed_atom_id,
                    row.base_obligation_id,
                    row.match_basis,
                    row.base_surface_sha256,
                    row.source_authority_sha256,
                    row.independent_binding_sha256,
                )
            )
            or not row.source_atom_id
            or not row.semantic_family
            or _STEP11_RC0031_BASE_PARSED_ATOM_ID_RE.fullmatch(
                row.base_parsed_atom_id
            )
            is None
            or _STEP11_RC0031_BASE_OBLIGATION_ID_RE.fullmatch(
                row.base_obligation_id
            )
            is None
            or not row.match_basis
            or any(
                _SHA_RE.fullmatch(value) is None
                for value in (
                    row.base_surface_sha256,
                    row.source_authority_sha256,
                    row.independent_binding_sha256,
                )
            )
            for row in rows
        )
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID"
        )
    if not rows:
        return ()
    if (
        len({row.source_atom_id for row in rows}) != len(rows)
        or type(base_candidate) is not Step11NaturalSurfaceCandidate
        or type(records) is not tuple
        or any(
            type(record) is not tuple
            or len(record) != 6
            or type(record[0]) is not str
            or not record[0]
            or type(record[1]) is not str
            or record[1] not in _STEP11_RC0031_EXACT_MATCH_BASIS
            for record in records
        )
        or len({record[0] for record in records}) != len(records)
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID"
        )
    try:
        base_surface_sha256 = hashlib.sha256(
            base_candidate.final_utf8_bytes
        ).hexdigest()
        source_authority_sha256 = str(
            successor_snapshot.relation_construction_authority.authority_sha256
        )
    except Exception:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID"
        ) from None
    if _SHA_RE.fullmatch(source_authority_sha256) is None:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID"
        )
    if not records:
        if any(
            row.base_surface_sha256 != base_surface_sha256
            or row.source_authority_sha256 != source_authority_sha256
            for row in rows
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID"
            )
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE"
        )
    family_by_id = {record[0]: record[1] for record in records}
    reuse_schema = (
        "cocolon.emlis.nls_v3.step11.rc0030_verified_base_reuse.v1"
    )
    for row in rows:
        expected_binding_sha256 = artifact_sha256(
            {
                "schema_version": reuse_schema,
                "source_atom_id": row.source_atom_id,
                "semantic_family": row.semantic_family,
                "base_parsed_atom_id": row.base_parsed_atom_id,
                "base_obligation_id": row.base_obligation_id,
                "match_basis": row.match_basis,
                "base_surface_sha256": row.base_surface_sha256,
                "source_authority_sha256": row.source_authority_sha256,
                "body_free": True,
            }
        )
        if (
            family_by_id.get(row.source_atom_id) != row.semantic_family
            or row.match_basis
            != _STEP11_RC0031_EXACT_MATCH_BASIS.get(row.semantic_family)
            or row.base_surface_sha256 != base_surface_sha256
            or row.source_authority_sha256 != source_authority_sha256
            or row.independent_binding_sha256 != expected_binding_sha256
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID"
            )
    return rows


def _step11_rc0031_composition_units(
    rows: Sequence[tuple[Any, ...]],
    *,
    maximum_complexity_load: int,
) -> tuple[
    tuple[
        str,
        str,
        tuple[str, ...],
        tuple[str, ...],
        tuple[tuple[Any, ...], ...],
        int,
    ],
    ...,
]:
    """Compose only owner-connected atoms under the frozen 3-atom bound."""

    ordered = tuple(sorted(rows, key=lambda row: (row[10], row[1], row[0])))
    construction_rows = tuple(row for row in ordered if row[1] == "construction")
    head_rows = tuple(row for row in ordered if row[1] != "construction")
    constructions_by_owner: dict[str, list[tuple[Any, ...]]] = {}
    for row in construction_rows:
        if len(row[2]) != 1:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_COMPOSITION_INVALID"
            )
        constructions_by_owner.setdefault(str(row[2][0]), []).append(row)

    used_atom_ids: set[str] = set()
    units: list[
        tuple[
            str,
            str,
            tuple[str, ...],
            tuple[str, ...],
            tuple[tuple[Any, ...], ...],
            int,
        ]
    ] = []
    modifiers_by_head: dict[str, list[tuple[Any, ...]]] = {
        str(head[0]): [] for head in head_rows
    }
    targets_by_head: dict[str, list[str]] = {
        str(head[0]): [] for head in head_rows
    }
    # First give each finite head one owner-exact modifier where possible.
    # Only after that fair pass may a head take a second distinct endpoint.
    # This prevents source-order greed from starving a later connected head.
    for head in head_rows:
        for owner_id in head[2]:
            modifier = next(
                (
                    row
                    for row in constructions_by_owner.get(owner_id, ())
                    if row[0] not in used_atom_ids
                ),
                None,
            )
            if modifier is None:
                continue
            modifiers_by_head[str(head[0])].append(modifier)
            targets_by_head[str(head[0])].append(str(owner_id))
            used_atom_ids.add(str(modifier[0]))
            break
    for head in head_rows:
        head_id = str(head[0])
        if not modifiers_by_head[head_id]:
            continue
        for owner_id in head[2]:
            if str(owner_id) in targets_by_head[head_id]:
                continue
            modifier = next(
                (
                    row
                    for row in constructions_by_owner.get(owner_id, ())
                    if row[0] not in used_atom_ids
                ),
                None,
            )
            if modifier is None:
                continue
            modifiers_by_head[head_id].append(modifier)
            targets_by_head[head_id].append(str(owner_id))
            used_atom_ids.add(str(modifier[0]))
            break
    for head in head_rows:
        head_id = str(head[0])
        modifiers = modifiers_by_head[head_id]
        modifier_target_owner_ids = targets_by_head[head_id]
        if not modifiers:
            continue
        used_atom_ids.add(head_id)
        atoms = (*modifiers, head)
        owner_ready_group_ordinal = max(
            int(group) for atom in atoms for group in atom[4]
        )
        units.append(
            (
                "construction_modified_head",
                head_id,
                tuple(str(row[0]) for row in modifiers),
                tuple(modifier_target_owner_ids),
                tuple(atoms),
                owner_ready_group_ordinal,
            )
        )

    remaining = tuple(row for row in ordered if row[0] not in used_atom_ids)
    independent_packs: list[list[tuple[Any, ...]]] = []
    for row in remaining:
        row_owner_ids = set(str(value) for value in row[2])
        placed = False
        for pack in independent_packs:
            pack_owner_ids = {
                str(owner_id)
                for candidate in pack
                for owner_id in candidate[2]
            }
            if (
                len(pack) < 2
                and bool(row_owner_ids & pack_owner_ids)
                and len(row_owner_ids | pack_owner_ids)
                <= maximum_complexity_load
            ):
                pack.append(row)
                placed = True
                break
        if not placed:
            independent_packs.append([row])
    for pack in independent_packs:
        atoms = tuple(pack)
        units.append(
            (
                "independent_clauses",
                "",
                (),
                (),
                atoms,
                max(int(group) for atom in atoms for group in atom[4]),
            )
        )

    return tuple(
        sorted(
            units,
            key=lambda unit: (
                unit[5],
                min(int(atom[10]) for atom in unit[4]),
                unit[0],
                tuple(str(atom[0]) for atom in unit[4]),
            ),
        )
    )


def _step11_rc0031_build_plan_from_verified_reuse_composition(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    clause_ready_lexical_specs: Any,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    reception_predications: Sequence[
        Step11Rc0031ReceptionPredicationBinding
    ],
    verified_base_body_exact_reuse_bindings: Sequence[
        Step11Rc0031BaseBodyExactReuseBinding
    ] = (),
) -> Step11Rc0031SurfaceRealizationPlan:
    """Private P2-owned composition seam for a future verified P3 proof."""

    _step11_rc0031_validate_base_render_commitment(base_candidate)
    (
        construction_atoms,
        relation_atoms,
        semantic_link_atoms,
        explicit_unknown_atoms,
        reception_predications,
    ) = _step11_rc0031_preflight_forward_rows(
        construction_atoms=construction_atoms,
        relation_atoms=relation_atoms,
        semantic_link_atoms=semantic_link_atoms,
        explicit_unknown_atoms=explicit_unknown_atoms,
        reception_predications=reception_predications,
    )
    if verified_base_body_exact_reuse_bindings is not None:
        verified_base_body_exact_reuse_bindings = (
            _step11_rc0031_exact_bounded_rows(
                verified_base_body_exact_reuse_bindings,
                item_types=(Step11Rc0031BaseBodyExactReuseBinding,),
                maximum=_STEP11_RC0031_EXACT_REUSE_MAX,
            )
        )
    base_plan = base_candidate.surface_ast.surface_realization_plan
    if type(base_plan) is not Step11SurfaceRealizationPlan:
        raise Step11NaturalSurfaceError("STEP11_RC0031_BASE_PLAN_INVALID")
    catalog, catalog_sha256 = _step11_rc0031_catalog()
    bounds = catalog["resource_bounds"]
    if (
        base_plan.maximum_visible_clauses_per_grammatical_sentence
        != bounds["visible_clauses_per_grammatical_sentence_max"]
        or base_plan.maximum_observation_clauses_per_sentence
        != _STEP11_RC0031_REALIZATION_UNITS_PER_GROUP_MAX
        or base_plan.maximum_grammatical_complexity_load
        != bounds["grammatical_complexity_load_max"]
        or base_plan.maximum_repeated_joiner_per_group
        != bounds["repeated_joiner_per_group_max"]
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RESOURCE_CONTRACT_MISMATCH"
        )
    lexemes = _step11_rc0031_lexemes(clause_ready_lexical_specs)
    expected_receptions = _step11_rc0031_reception_predications(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexemes=lexemes,
        catalog=catalog,
    )
    if (
        not _step11_rc0031_safe_structural_equal(
            reception_predications, expected_receptions
        )
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RECEPTION_SOURCE_BINDING_INVALID"
        )
    positions = _step11_rc0031_owner_positions(base_candidate, lexemes)
    records = _step11_rc0031_atom_records(
        lexemes=lexemes,
        constructions=construction_atoms,
        relations=relation_atoms,
        links=semantic_link_atoms,
        unknowns=explicit_unknown_atoms,
    )
    reuse = _step11_rc0031_validate_verified_reuse_composition(
        verified_base_body_exact_reuse_bindings,
        records=records,
        base_candidate=base_candidate,
        successor_snapshot=successor_snapshot,
    )
    reused_ids = {row.source_atom_id for row in reuse}
    pending: list[
        tuple[
            str,
            str,
            tuple[str, ...],
            tuple[str, ...],
            tuple[int, ...],
            int,
            int,
            bool,
            str,
            str,
            int,
        ]
    ] = []
    for source_authority_order, (
        atom_id,
        family,
        owner_ids,
        owner_ordinals,
        direction,
        semantic_key,
    ) in enumerate(records, start=1):
        if atom_id in reused_ids:
            continue
        try:
            owner_positions = tuple(positions[value] for value in owner_ordinals)
        except KeyError as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_OWNER_BASE_GROUP_UNRESOLVED"
            ) from exc
        owner_groups = tuple(row[2] for row in owner_positions)
        target_group = max(owner_groups)
        target_chunks = tuple(
            row[3] for row in owner_positions if row[2] == target_group
        )
        if not target_chunks or target_group not in owner_groups:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_OWNER_CONNECTED_GROUP_UNRESOLVED"
            )
        pending.append(
            (
                atom_id,
                family,
                owner_ids,
                tuple(row[1] for row in owner_positions),
                owner_groups,
                target_group,
                max(target_chunks),
                len(set(owner_groups)) > 1,
                direction,
                semantic_key,
                source_authority_order,
            )
        )

    group_ids = tuple(base_plan.observation_sentence_group_ids)
    group_index = {
        value: ordinal for ordinal, value in enumerate(group_ids, start=1)
    }
    base_units = tuple(
        row for row in base_plan.units if row.section_role == "observation"
    )
    by_chunk: dict[tuple[int, int], list[Step11SurfaceRealizationUnit]] = {}
    for row in base_units:
        key = (
            group_index[row.assigned_sentence_group_id],
            int(row.assigned_grammatical_chunk_ordinal),
        )
        by_chunk.setdefault(key, []).append(row)
    base_unit_count_by_group = {
        group_ordinal: sum(
            len(rows)
            for (candidate_group, _chunk), rows in by_chunk.items()
            if candidate_group == group_ordinal
        )
        for group_ordinal in range(1, len(group_ids) + 1)
    }
    added_unit_count_by_group = {
        group_ordinal: 0 for group_ordinal in base_unit_count_by_group
    }
    joiner_count_by_group = {
        group_ordinal: sum(
            max(0, len(rows) - 1)
            for (candidate_group, _chunk), rows in by_chunk.items()
            if candidate_group == group_ordinal
        )
        for group_ordinal in base_unit_count_by_group
    }
    tail_chunk_by_group = {
        group_ordinal: max(
            (
                chunk
                for candidate_group, chunk in by_chunk
                if candidate_group == group_ordinal
            ),
            default=0,
        )
        for group_ordinal in base_unit_count_by_group
    }

    proposition_bindings: list[Step11Rc0031PropositionClauseBinding] = []
    structure_by_chunk: dict[
        tuple[int, int], list[Step11Rc0031PropositionClauseBinding]
    ] = {}
    composition_units = _step11_rc0031_composition_units(
        pending,
        maximum_complexity_load=(
            base_plan.maximum_grammatical_complexity_load
        ),
    )
    for (
        composition_mode,
        head_source_atom_id,
        modifier_atom_ids,
        modifier_target_owner_ids,
        pack,
        owner_ready_group_ordinal,
    ) in composition_units:
        visible_clause_count = (
            1
            if composition_mode == "construction_modified_head"
            else len(pack)
        )
        owner_rows: list[tuple[str, str, int]] = []
        for atom in pack:
            owner_rows.extend(zip(atom[2], atom[3], atom[4], strict=True))
        unique_owner_rows = tuple(dict.fromkeys(owner_rows))
        complexity_load = max(
            len(pack), len(unique_owner_rows), visible_clause_count
        )
        compact_valid = (
            composition_mode == "construction_modified_head"
            and 2 <= len(pack) <= 3
            and str(pack[-1][0]) == head_source_atom_id
            and str(pack[-1][1])
            in {"relation", "semantic_link", "explicit_unknown"}
            and tuple(str(atom[0]) for atom in pack[:-1])
            == modifier_atom_ids
            and all(str(atom[1]) == "construction" for atom in pack[:-1])
            and len(modifier_target_owner_ids) == len(pack) - 1
            and len(set(modifier_target_owner_ids))
            == len(modifier_target_owner_ids)
            and all(
                target_owner_id in pack[-1][2]
                and tuple(str(value) for value in modifier[2])
                == (target_owner_id,)
                for modifier, target_owner_id in zip(
                    pack[:-1],
                    modifier_target_owner_ids,
                    strict=True,
                )
            )
        )
        independent_valid = (
            composition_mode == "independent_clauses"
            and 1 <= len(pack) <= 2
            and head_source_atom_id == ""
            and not modifier_atom_ids
            and not modifier_target_owner_ids
            and (
                len(pack) == 1
                or bool(set(pack[0][2]) & set(pack[1][2]))
            )
        )
        if (
            composition_mode not in _STEP11_RC0031_COMPOSITION_MODES
            or not (compact_valid or independent_valid)
            or len({str(atom[0]) for atom in pack}) != len(pack)
            or owner_ready_group_ordinal
            != max(int(group) for atom in pack for group in atom[4])
            or not 1 <= visible_clause_count <= 2
            or complexity_load
            > base_plan.maximum_grammatical_complexity_load
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_COMPOSITION_INVALID"
            )
        target_group = next(
            (
                group_ordinal
                for group_ordinal in range(
                    owner_ready_group_ordinal, len(group_ids) + 1
                )
                if base_unit_count_by_group[group_ordinal]
                + added_unit_count_by_group[group_ordinal]
                + 1
                <= base_plan.maximum_observation_clauses_per_sentence
                and joiner_count_by_group[group_ordinal]
                + max(0, visible_clause_count - 1)
                <= base_plan.maximum_repeated_joiner_per_group
            ),
            None,
        )
        if target_group is None:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_SURFACE_PLAN_DENSITY_UNSATISFIABLE"
            )
        chunk_ordinal = tail_chunk_by_group[target_group] + 1
        unit_id = "nls3s11rc0031prop_" + artifact_sha256(
            {
                "composition_mode": composition_mode,
                "head_source_atom_id": head_source_atom_id,
                "construction_modifier_atom_ids": list(modifier_atom_ids),
                "construction_modifier_target_owner_ids": list(
                    modifier_target_owner_ids
                ),
                "owner_ready_group_ordinal": owner_ready_group_ordinal,
                "source_atom_ids": [atom[0] for atom in pack],
                "sentence_group_ordinal": target_group,
                "grammatical_chunk_ordinal": chunk_ordinal,
            }
        )[:16]
        binding = Step11Rc0031PropositionClauseBinding(
            proposition_unit_id=unit_id,
            composition_mode=composition_mode,
            head_source_atom_id=head_source_atom_id,
            construction_modifier_atom_ids=modifier_atom_ids,
            construction_modifier_target_owner_ids=(
                modifier_target_owner_ids
            ),
            owner_ready_group_ordinal=owner_ready_group_ordinal,
            source_atom_ids=tuple(str(atom[0]) for atom in pack),
            semantic_families=tuple(str(atom[1]) for atom in pack),
            semantic_keys=tuple(str(atom[9]) for atom in pack),
            source_atom_owner_ids=tuple(
                tuple(str(value) for value in atom[2]) for atom in pack
            ),
            source_owner_ids=tuple(row[0] for row in unique_owner_rows),
            owner_base_nucleus_ids=tuple(
                row[1] for row in unique_owner_rows
            ),
            owner_sentence_group_ordinals=tuple(
                row[2] for row in unique_owner_rows
            ),
            sentence_group_ordinal=target_group,
            grammatical_chunk_ordinal=chunk_ordinal,
            visible_clause_count=visible_clause_count,
            complexity_load=complexity_load,
            cross_group_bridge=any(bool(atom[7]) for atom in pack),
            directions=tuple(str(atom[8]) for atom in pack),
        )
        proposition_bindings.append(binding)
        structure_by_chunk.setdefault((target_group, chunk_ordinal), []).append(
            binding
        )
        tail_chunk_by_group[target_group] = chunk_ordinal
        added_unit_count_by_group[target_group] += 1
        joiner_count_by_group[target_group] += max(
            0, visible_clause_count - 1
        )

    proposition_bindings.sort(
        key=lambda row: (
            row.sentence_group_ordinal,
            row.grammatical_chunk_ordinal,
            row.proposition_unit_id,
        )
    )
    realized_ids = tuple(
        atom_id
        for binding in proposition_bindings
        for atom_id in binding.source_atom_ids
    )
    if (
        len(realized_ids) + len(reuse) != len(records)
        or len(set((*realized_ids, *reused_ids))) != len(records)
        or set(realized_ids) & reused_ids
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_SEMANTIC_ATOM_COVERAGE_INVALID"
        )

    assignments: list[Step11Rc0031PropositionChunkAssignment] = []
    all_chunk_keys = sorted(set((*by_chunk, *structure_by_chunk)))
    for key in all_chunk_keys:
        base_rows = sorted(
            by_chunk.get(key, ()), key=lambda row: row.source_order
        )
        proposition_rows = sorted(
            structure_by_chunk.get(key, ()),
            key=lambda row: row.proposition_unit_id,
        )
        assignments.append(
            Step11Rc0031PropositionChunkAssignment(
                sentence_group_ordinal=key[0],
                grammatical_chunk_ordinal=key[1],
                source_unit_ids=(
                    *(row.semantic_unit_id for row in base_rows),
                    *(row.proposition_unit_id for row in proposition_rows),
                ),
                source_atom_ids=tuple(
                    atom_id
                    for row in proposition_rows
                    for atom_id in row.source_atom_ids
                ),
                visible_clause_count=(
                    len(base_rows)
                    + sum(row.visible_clause_count for row in proposition_rows)
                ),
                complexity_load=(
                    sum(row.body_free_complexity_weight for row in base_rows)
                    + sum(row.complexity_load for row in proposition_rows)
                ),
            )
        )
    if any(
        row.visible_clause_count
        > base_plan.maximum_visible_clauses_per_grammatical_sentence
        or row.complexity_load
        > base_plan.maximum_grammatical_complexity_load
        for row in assignments
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_SURFACE_PLAN_DENSITY_UNSATISFIABLE"
        )

    root = _step11_rc0031_root_binding(base_candidate)
    if (
        not assignments
        or root.source_semantic_unit_id not in assignments[0].source_unit_ids
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_ROOT_PROPOSITION_DISPLACED"
        )
    peak_group_clause_count = max(
        (
            base_unit_count_by_group[group]
            + added_unit_count_by_group[group]
            for group in base_unit_count_by_group
        ),
        default=0,
    )
    provisional = Step11Rc0031SurfaceRealizationPlan(
        schema_version=STEP11_RC0031_EXPERIMENT_PLAN_SCHEMA,
        candidate_version_id=STEP11_RC0031_EXPERIMENT_CANDIDATE_VERSION_ID,
        realization_plan_id="nls3s11rc0031plan_0000000000000000",
        source_base_candidate_id=base_candidate.candidate_id,
        source_base_realization_plan_id=base_plan.realization_plan_id,
        source_successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        source_lexical_atom_specs_sha256=lexical_atom_specs.specs_sha256,
        source_clause_ready_lexical_specs_sha256=(
            clause_ready_lexical_specs.specs_sha256
        ),
        source_lexical_projection_catalog_sha256=(
            clause_ready_lexical_specs.surface_catalog_sha256
        ),
        surface_catalog_sha256=catalog_sha256,
        root_proposition_binding=root,
        proposition_chunk_assignments=tuple(assignments),
        proposition_clause_bindings=tuple(proposition_bindings),
        base_body_exact_reuse_bindings=reuse,
        reception_predication_bindings=expected_receptions,
        maximum_observation_clauses_per_sentence=(
            base_plan.maximum_observation_clauses_per_sentence
        ),
        maximum_visible_clauses_per_grammatical_sentence=(
            base_plan.maximum_visible_clauses_per_grammatical_sentence
        ),
        maximum_grammatical_complexity_load=(
            base_plan.maximum_grammatical_complexity_load
        ),
        maximum_repeated_joiner_per_group=(
            base_plan.maximum_repeated_joiner_per_group
        ),
        peak_observation_clause_count=peak_group_clause_count,
        peak_grammatical_clause_count=max(
            max((row.visible_clause_count for row in assignments), default=0),
            1 if expected_receptions else 0,
        ),
        peak_grammatical_complexity_load=max(
            max((row.complexity_load for row in assignments), default=0),
            max(
                (
                    len(row.source_target_owner_ids)
                    + len(row.supporting_source_owner_ids)
                    for row in expected_receptions
                ),
                default=0,
            ),
        ),
        peak_group_repeated_joiner_count=max(
            joiner_count_by_group.values(), default=0
        ),
        body_free=True,
    )
    return replace(
        provisional,
        realization_plan_id=(
            "nls3s11rc0031plan_"
            + artifact_sha256(
                step11_rc0031_surface_realization_plan_material(
                    provisional, include_id=False
                )
            )[:16]
        ),
    )


def build_step11_rc0031_surface_realization_plan(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    clause_ready_lexical_specs: Any,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    reception_predications: Sequence[
        Step11Rc0031ReceptionPredicationBinding
    ],
    base_body_exact_reuse_bindings: Sequence[
        Step11Rc0031BaseBodyExactReuseBinding
    ] = (),
) -> Step11Rc0031SurfaceRealizationPlan:
    """Build the P2 plan while rejecting all caller-claimed body reuse."""

    try:
        _step11_rc0031_preflight_clause_ready(clause_ready_lexical_specs)
        (
            construction_rows,
            relation_rows,
            link_rows,
            unknown_rows,
            reception_rows,
        ) = _step11_rc0031_preflight_forward_rows(
            construction_atoms=construction_atoms,
            relation_atoms=relation_atoms,
            semantic_link_atoms=semantic_link_atoms,
            explicit_unknown_atoms=explicit_unknown_atoms,
            reception_predications=reception_predications,
        )
        _step11_rc0031_validate_exact_reuse(
            base_body_exact_reuse_bindings,
            records=(),
            base_candidate=base_candidate,
            successor_snapshot=successor_snapshot,
        )
        if (
            type(base_candidate) is not Step11NaturalSurfaceCandidate
            or type(base_candidate.surface_ast) is not Step11NaturalSurfaceAst
            or type(base_candidate.surface_ast.surface_realization_plan)
            is not Step11SurfaceRealizationPlan
        ):
            _step11_rc0031_validate_base_render_commitment(base_candidate)
        base_plan = base_candidate.surface_ast.surface_realization_plan
        catalog, _catalog_sha256 = _step11_rc0031_catalog()
        bounds = catalog["resource_bounds"]
        if (
            base_plan.maximum_visible_clauses_per_grammatical_sentence
            != bounds["visible_clauses_per_grammatical_sentence_max"]
            or base_plan.maximum_observation_clauses_per_sentence
            != _STEP11_RC0031_REALIZATION_UNITS_PER_GROUP_MAX
            or base_plan.maximum_grammatical_complexity_load
            != bounds["grammatical_complexity_load_max"]
            or base_plan.maximum_repeated_joiner_per_group
            != bounds["repeated_joiner_per_group_max"]
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RESOURCE_CONTRACT_MISMATCH"
            )
        _step11_rc0031_validate_base_render_commitment(base_candidate)
        expected_clause_ready = _step11_rc0031_clause_ready_projection(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        if not _step11_rc0031_safe_structural_equal(
            clause_ready_lexical_specs, expected_clause_ready
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_LEXICAL_PROJECTION_COMMITMENT_INVALID"
            )
        rc0028_catalog, _rc0028_catalog_sha256 = _step11_rc0028_catalog()
        (
            _expected_owner_registry,
            expected_constructions,
            expected_relations,
            expected_links,
            expected_unknowns,
        ) = _step11_rc0028_forward_atoms(
            successor_snapshot, lexical_atom_specs, rc0028_catalog
        )
        if not all(
            (
                _step11_rc0031_safe_structural_equal(
                    construction_rows, expected_constructions
                ),
                _step11_rc0031_safe_structural_equal(
                    relation_rows, expected_relations
                ),
                _step11_rc0031_safe_structural_equal(
                    link_rows, expected_links
                ),
                _step11_rc0031_safe_structural_equal(
                    unknown_rows, expected_unknowns
                ),
            )
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RENDER_SOURCE_ATOM_MISMATCH"
            )
        expected_receptions = _step11_rc0031_reception_predications(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexemes=_step11_rc0031_lexemes(expected_clause_ready),
            catalog=catalog,
        )
        if not _step11_rc0031_safe_structural_equal(
            reception_rows, expected_receptions
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RECEPTION_SOURCE_BINDING_INVALID"
            )
        return _step11_rc0031_build_plan_from_verified_reuse_composition(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            clause_ready_lexical_specs=expected_clause_ready,
            construction_atoms=expected_constructions,
            relation_atoms=expected_relations,
            semantic_link_atoms=expected_links,
            explicit_unknown_atoms=expected_unknowns,
            reception_predications=expected_receptions,
            verified_base_body_exact_reuse_bindings=(),
        )
    except Exception as exc:
        raise _step11_rc0031_boundary_error(
            exc, input_invalid_code="STEP11_RC0031_PLAN_INPUT_INVALID"
        ) from exc


def _step11_rc0031_render_semantic_clause(
    *,
    source_atom_id: str,
    semantic_family: str,
    catalog: Mapping[str, Any],
    referent_by_owner: Mapping[str, str],
    owner_ids: Sequence[str],
    construction_by_id: Mapping[str, Any],
    relation_by_id: Mapping[str, Any],
    link_by_id: Mapping[str, Any],
    unknown_by_id: Mapping[str, Any],
) -> str:
    morphology = catalog["clause_morphology"]
    try:
        referents = tuple(referent_by_owner[value] for value in owner_ids)
    except KeyError as exc:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RENDER_OWNER_UNRESOLVED"
        ) from exc
    if not referents:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RENDER_OWNER_UNRESOLVED"
        )
    if semantic_family == "construction":
        atom = construction_by_id.get(source_atom_id)
        fragment = (
            catalog["construction_predicate_fragments"].get(
                atom.construction_code
            )
            if atom is not None
            else None
        )
        standalone_predicate = morphology.get(
            "construction_standalone_predicate"
        )
        text = referents[0] + str(fragment) + str(standalone_predicate)
    elif semantic_family in {"relation", "semantic_link"}:
        atom = (
            relation_by_id.get(source_atom_id)
            if semantic_family == "relation"
            else link_by_id.get(source_atom_id)
        )
        if atom is None or len(referents) != 2:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RELATION_ENDPOINT_INVALID"
            )
        relation_type = (
            atom.effective_relation_type
            if semantic_family == "relation"
            else atom.relation_type
        )
        key = str(relation_type) + ":" + str(atom.direction)
        registry = (
            catalog["relation_predicate_fragments"]
            if semantic_family == "relation"
            else catalog["semantic_link_predicate_fragments"]
        )
        fragment = registry.get(key)
        if atom.direction not in {"source_to_target", "bidirectional"}:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RELATION_DIRECTION_INVALID"
            )
        try:
            text = str(fragment).format(
                source=referents[0], target=referents[1]
            )
        except (AttributeError, KeyError, ValueError) as exc:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RELATION_PATTERN_INVALID"
            ) from exc
    elif semantic_family == "explicit_unknown":
        atom = unknown_by_id.get(source_atom_id)
        fragment = (
            catalog["unknown_predicate_fragments"].get(atom.dimension)
            if atom is not None
            else None
        )
        text = morphology["unknown_owner_join"].join(referents) + str(fragment)
    else:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_SEMANTIC_FAMILY_INVALID"
        )
    if (
        fragment is None
        or (
            semantic_family == "construction"
            and standalone_predicate is None
        )
        or not text
        or "None" in text
        or any(marker in text for marker in ("\r", "\n", "「", "」"))
        or text.endswith(("。", "！", "？", "!", "?"))
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_PROPOSITION_CLAUSE_INVALID"
        )
    return text


def _step11_rc0031_validate_base_render_commitment(
    base_candidate: Step11NaturalSurfaceCandidate,
) -> None:
    """Validate the self-contained rc0027 commitments needed by P2 render."""

    if type(base_candidate) is not Step11NaturalSurfaceCandidate:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_BASE_CANDIDATE_INVALID"
        )
    try:
        base_ast = base_candidate.surface_ast
        base_rendered = base_candidate.rendered_surface
        base_plan = getattr(base_ast, "surface_realization_plan", None)
        invalid = (
            type(base_candidate.schema_version) is not str
            or type(base_candidate.candidate_version_id) is not str
            or type(base_candidate.candidate_id) is not str
            or type(base_ast) is not Step11NaturalSurfaceAst
            or type(base_rendered) is not Step11CanonicalRenderedSurface
            or type(base_plan) is not Step11SurfaceRealizationPlan
            or type(base_ast.schema_version) is not str
            or type(base_ast.candidate_version_id) is not str
            or type(base_ast.surface_catalog_sha256) is not str
            or type(base_ast.surface_ast_id) is not str
            or type(base_plan.schema_version) is not str
            or type(base_plan.candidate_version_id) is not str
            or type(base_plan.realization_plan_id) is not str
            or type(base_rendered.schema_version) is not str
            or type(base_rendered.surface_catalog_sha256) is not str
            or type(base_rendered.sha256) is not str
            or type(base_rendered.source_surface_ast_sha256) is not str
            or not _step11_rc0031_safe_structural_equal(
                base_candidate.schema_version, STEP11_CANDIDATE_SCHEMA
            )
            or not _step11_rc0031_safe_structural_equal(
                base_candidate.candidate_version_id,
                STEP11_CANDIDATE_VERSION_ID,
            )
            or not _step11_rc0031_safe_structural_equal(
                base_ast.schema_version, STEP11_SURFACE_AST_SCHEMA
            )
            or not _step11_rc0031_safe_structural_equal(
                base_ast.candidate_version_id,
                STEP11_CANDIDATE_VERSION_ID,
            )
            or not _step11_rc0031_safe_structural_equal(
                base_ast.surface_catalog_sha256,
                STEP11_SURFACE_CATALOG_SHA256,
            )
            or not _step11_rc0031_safe_structural_equal(
                base_plan.schema_version,
                STEP11_SURFACE_REALIZATION_PLAN_SCHEMA,
            )
            or not _step11_rc0031_safe_structural_equal(
                base_plan.candidate_version_id,
                STEP11_CANDIDATE_VERSION_ID,
            )
            or base_plan.body_free is not True
            or not _step11_rc0031_safe_structural_equal(
                base_rendered.schema_version,
                STEP11_RENDERED_SURFACE_SCHEMA,
            )
            or not _step11_rc0031_safe_structural_equal(
                base_rendered.surface_catalog_sha256,
                STEP11_SURFACE_CATALOG_SHA256,
            )
            or type(base_rendered.utf8_bytes) is not bytes
            or not _step11_rc0031_safe_structural_equal(
                base_rendered.sha256,
                hashlib.sha256(base_rendered.utf8_bytes).hexdigest(),
            )
            or not _step11_rc0031_safe_structural_equal(
                base_rendered.source_surface_ast_sha256,
                artifact_sha256(step11_surface_ast_material(base_ast)),
            )
            or not _step11_rc0031_safe_structural_equal(
                base_plan.realization_plan_id,
                "nls3s11real_"
                + artifact_sha256(
                    step11_surface_realization_plan_material(
                        base_plan, include_id=False
                    )
                )[:16],
            )
            or not _step11_rc0031_safe_structural_equal(
                base_ast.surface_ast_id,
                "nls3s11ast_"
                + artifact_sha256(
                    step11_surface_ast_material(base_ast, include_id=False)
                )[:16],
            )
            or not _step11_rc0031_safe_structural_equal(
                base_candidate.candidate_id,
                _candidate_identity(base_ast, base_rendered),
            )
        )
    except Exception as exc:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_BASE_CANDIDATE_COMMITMENT_INVALID"
        ) from exc
    if invalid:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_BASE_CANDIDATE_COMMITMENT_INVALID"
        )


def _step11_rc0031_render_from_verified_reuse_composition(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    clause_ready_lexical_specs: Any,
    proposition_surface_ast: Step11Rc0031PropositionSurfaceAst,
    surface_realization_plan: Step11Rc0031SurfaceRealizationPlan,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    reception_predications: Sequence[
        Step11Rc0031ReceptionPredicationBinding
    ],
    verified_base_body_exact_reuse_bindings: Sequence[
        Step11Rc0031BaseBodyExactReuseBinding
    ] | None,
) -> Step11Rc0031ExperimentRenderedSurface:
    """Private canonical renderer seam for P2 or a future verified P3 proof."""

    _step11_rc0031_validate_base_render_commitment(base_candidate)
    _step11_rc0031_preflight_clause_ready(clause_ready_lexical_specs)
    (
        construction_atoms,
        relation_atoms,
        semantic_link_atoms,
        explicit_unknown_atoms,
        reception_predications,
    ) = _step11_rc0031_preflight_forward_rows(
        construction_atoms=construction_atoms,
        relation_atoms=relation_atoms,
        semantic_link_atoms=semantic_link_atoms,
        explicit_unknown_atoms=explicit_unknown_atoms,
        reception_predications=reception_predications,
    )
    if verified_base_body_exact_reuse_bindings is not None:
        verified_base_body_exact_reuse_bindings = (
            _step11_rc0031_exact_bounded_rows(
                verified_base_body_exact_reuse_bindings,
                item_types=(Step11Rc0031BaseBodyExactReuseBinding,),
                maximum=_STEP11_RC0031_EXACT_REUSE_MAX,
            )
        )
    if (
        type(surface_realization_plan) is not Step11Rc0031SurfaceRealizationPlan
        or type(proposition_surface_ast) is not Step11Rc0031PropositionSurfaceAst
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_AST_PLAN_MISMATCH"
        )
    catalog, catalog_sha256 = _step11_rc0031_catalog()
    try:
        lexical_sha256 = _step11_rc0028_validate_lexical_specs(
            lexical_atom_specs, successor_snapshot=successor_snapshot
        )
        expected_clause_ready = _step11_rc0031_clause_ready_projection(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
    except Exception as exc:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RENDER_LEXICAL_AUTHORITY_MISMATCH"
        ) from exc
    if not _step11_rc0031_safe_structural_equal(
        clause_ready_lexical_specs, expected_clause_ready
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RENDER_LEXICAL_AUTHORITY_MISMATCH"
        )
    rc0028_catalog, _rc0028_catalog_sha256 = _step11_rc0028_catalog()
    (
        _expected_owner_registry,
        expected_constructions,
        expected_relations,
        expected_links,
        expected_unknowns,
    ) = _step11_rc0028_forward_atoms(
        successor_snapshot, lexical_atom_specs, rc0028_catalog
    )
    if not all(
        (
            _step11_rc0031_safe_structural_equal(
                construction_atoms, expected_constructions
            ),
            _step11_rc0031_safe_structural_equal(
                relation_atoms, expected_relations
            ),
            _step11_rc0031_safe_structural_equal(
                semantic_link_atoms, expected_links
            ),
            _step11_rc0031_safe_structural_equal(
                explicit_unknown_atoms, expected_unknowns
            ),
        )
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RENDER_SOURCE_ATOM_MISMATCH"
        )
    lexemes = _step11_rc0031_lexemes(expected_clause_ready)
    expected_receptions = _step11_rc0031_reception_predications(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexemes=lexemes,
        catalog=catalog,
    )
    if not _step11_rc0031_safe_structural_equal(
        reception_predications, expected_receptions
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RECEPTION_PLAN_MISMATCH"
        )
    if verified_base_body_exact_reuse_bindings is None:
        expected_plan = build_step11_rc0031_surface_realization_plan(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            clause_ready_lexical_specs=expected_clause_ready,
            construction_atoms=expected_constructions,
            relation_atoms=expected_relations,
            semantic_link_atoms=expected_links,
            explicit_unknown_atoms=expected_unknowns,
            reception_predications=expected_receptions,
            base_body_exact_reuse_bindings=(
                surface_realization_plan.base_body_exact_reuse_bindings
            ),
        )
    else:
        if not _step11_rc0031_safe_structural_equal(
            verified_base_body_exact_reuse_bindings,
            surface_realization_plan.base_body_exact_reuse_bindings,
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RENDER_PLAN_AUTHORITY_MISMATCH"
            )
        expected_plan = (
            _step11_rc0031_build_plan_from_verified_reuse_composition(
                base_candidate,
                successor_snapshot=successor_snapshot,
                lexical_atom_specs=lexical_atom_specs,
                clause_ready_lexical_specs=expected_clause_ready,
                construction_atoms=expected_constructions,
                relation_atoms=expected_relations,
                semantic_link_atoms=expected_links,
                explicit_unknown_atoms=expected_unknowns,
                reception_predications=expected_receptions,
                verified_base_body_exact_reuse_bindings=tuple(
                    verified_base_body_exact_reuse_bindings
                ),
            )
        )
    if not _step11_rc0031_safe_structural_equal(
        surface_realization_plan, expected_plan
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RENDER_PLAN_AUTHORITY_MISMATCH"
        )
    expected_ast = _step11_rc0031_build_ast(base_candidate, expected_plan)
    if not _step11_rc0031_safe_structural_equal(
        proposition_surface_ast, expected_ast
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_AST_PLAN_MISMATCH"
        )
    if (
        not _step11_rc0031_safe_structural_equal(
            lexical_sha256,
            expected_plan.source_lexical_atom_specs_sha256,
        )
        or not _step11_rc0031_safe_structural_equal(
            expected_plan.surface_catalog_sha256, catalog_sha256
        )
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_CATALOG_COMMITMENT_MISMATCH"
        )
    # From this point onward, render only rederived canonical values.  Caller
    # objects have already been proven structurally identical and are no
    # longer used as rendering authority.
    surface_realization_plan = expected_plan
    proposition_surface_ast = expected_ast
    clause_ready_lexical_specs = expected_clause_ready
    construction_atoms = expected_constructions
    relation_atoms = expected_relations
    semantic_link_atoms = expected_links
    explicit_unknown_atoms = expected_unknowns
    reception_predications = expected_receptions

    try:
        text = base_candidate.final_utf8_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_BASE_SURFACE_INVALID"
        ) from exc
    marker = "\n\nEmlisから：\n"
    if not text.startswith("見えたこと：\n") or text.count(marker) != 1:
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_BASE_SURFACE_INVALID"
        )
    observation, reception = text.split(marker, 1)
    observation_lines = observation.split("\n")
    reception_lines = reception.split("\n")
    base_plan = base_candidate.surface_ast.surface_realization_plan
    if (
        len(observation_lines)
        != len(base_plan.observation_sentence_group_ids) + 1
        or len(reception_lines) != len(base_plan.reception_sentence_group_ids)
        or any(not line for line in (*observation_lines[1:], *reception_lines))
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_BASE_SURFACE_LAYOUT_INVALID"
        )
    referent_by_owner = {
        str(row.source_owner_id): str(row.referent_text) for row in lexemes
    }
    construction_by_id = {
        str(row.construction_instance_id): row for row in construction_atoms
    }
    relation_by_id = {
        str(row.experiment_relation_id): row for row in relation_atoms
    }
    link_by_id = {
        str(row.source_semantic_link_id): row
        for row in semantic_link_atoms
    }
    unknown_by_id = {
        str(row.source_unknown_id): row for row in explicit_unknown_atoms
    }
    source_records_by_atom = {
        row[0]: row
        for row in _step11_rc0031_atom_records(
            lexemes=lexemes,
            constructions=construction_atoms,
            relations=relation_atoms,
            links=semantic_link_atoms,
            unknowns=explicit_unknown_atoms,
        )
    }
    clauses_by_group: dict[int, list[tuple[int, str, tuple[str, ...]]]] = {}
    for binding in proposition_surface_ast.proposition_clause_bindings:
        clauses: list[str] = []
        atom_count = len(binding.source_atom_ids)
        if not (
            type(binding.composition_mode) is str
            and binding.composition_mode in _STEP11_RC0031_COMPOSITION_MODES
            and type(binding.head_source_atom_id) is str
            and type(binding.construction_modifier_atom_ids) is tuple
            and type(binding.construction_modifier_target_owner_ids) is tuple
            and type(binding.owner_ready_group_ordinal) is int
            and len(binding.semantic_families)
            == len(binding.semantic_keys)
            == len(binding.source_atom_owner_ids)
            == len(binding.directions)
            == atom_count
            and len(set(binding.source_atom_ids)) == atom_count
            and binding.owner_ready_group_ordinal
            == max(binding.owner_sentence_group_ordinals)
            and binding.sentence_group_ordinal
            >= binding.owner_ready_group_ordinal
            and binding.complexity_load
            == max(
                atom_count,
                len(binding.source_owner_ids),
                binding.visible_clause_count,
            )
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_COMPOSITION_INVALID"
            )
        binding_records: list[tuple[Any, ...]] = []
        for atom_id, family, semantic_key, owner_ids, direction in zip(
            binding.source_atom_ids,
            binding.semantic_families,
            binding.semantic_keys,
            binding.source_atom_owner_ids,
            binding.directions,
            strict=True,
        ):
            source_record = source_records_by_atom.get(atom_id)
            if (
                source_record is None
                or not _step11_rc0031_safe_structural_equal(
                    source_record[1], family
                )
                or not _step11_rc0031_safe_structural_equal(
                    source_record[2], owner_ids
                )
                or not _step11_rc0031_safe_structural_equal(
                    source_record[4], direction
                )
                or not _step11_rc0031_safe_structural_equal(
                    source_record[5], semantic_key
                )
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_RENDER_SOURCE_ATOM_MISMATCH"
                )
            binding_records.append(source_record)
        if binding.composition_mode == "construction_modified_head":
            if not (
                2 <= atom_count <= 3
                and binding.source_atom_ids[:-1]
                == binding.construction_modifier_atom_ids
                and binding.source_atom_ids[-1]
                == binding.head_source_atom_id
                and all(
                    row[1] == "construction" for row in binding_records[:-1]
                )
                and binding_records[-1][1]
                in {"relation", "semantic_link", "explicit_unknown"}
                and len(binding.construction_modifier_target_owner_ids)
                == atom_count - 1
                and len(
                    set(binding.construction_modifier_target_owner_ids)
                )
                == atom_count - 1
                and binding.visible_clause_count == 1
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_COMPOSITION_INVALID"
                )
            modified_referent_by_owner = dict(referent_by_owner)
            for modifier_record, target_owner_id in zip(
                binding_records[:-1],
                binding.construction_modifier_target_owner_ids,
                strict=True,
            ):
                modifier = construction_by_id.get(modifier_record[0])
                fragment = (
                    catalog["construction_predicate_fragments"].get(
                        modifier.construction_code
                    )
                    if modifier is not None
                    else None
                )
                if (
                    tuple(modifier_record[2]) != (target_owner_id,)
                    or target_owner_id not in binding_records[-1][2]
                    or target_owner_id not in referent_by_owner
                    or fragment is None
                    or not str(fragment)
                    or any(
                        marker in str(fragment)
                        for marker in ("\r", "\n", "「", "」")
                    )
                ):
                    raise Step11NaturalSurfaceError(
                        "STEP11_RC0031_COMPOSITION_INVALID"
                    )
                modified_referent_by_owner[target_owner_id] = (
                    referent_by_owner[target_owner_id] + str(fragment)
                )
            head_record = binding_records[-1]
            clauses.append(
                _step11_rc0031_render_semantic_clause(
                    source_atom_id=head_record[0],
                    semantic_family=head_record[1],
                    catalog=catalog,
                    referent_by_owner=modified_referent_by_owner,
                    owner_ids=head_record[2],
                    construction_by_id=construction_by_id,
                    relation_by_id=relation_by_id,
                    link_by_id=link_by_id,
                    unknown_by_id=unknown_by_id,
                )
            )
        else:
            if not (
                1 <= atom_count <= 2
                and binding.head_source_atom_id == ""
                and not binding.construction_modifier_atom_ids
                and not binding.construction_modifier_target_owner_ids
                and binding.visible_clause_count == atom_count
                and (
                    atom_count == 1
                    or bool(
                        set(binding_records[0][2])
                        & set(binding_records[1][2])
                    )
                )
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_COMPOSITION_INVALID"
                )
            for source_record in binding_records:
                clauses.append(
                    _step11_rc0031_render_semantic_clause(
                        source_atom_id=source_record[0],
                        semantic_family=source_record[1],
                        catalog=catalog,
                        referent_by_owner=referent_by_owner,
                        owner_ids=source_record[2],
                        construction_by_id=construction_by_id,
                        relation_by_id=relation_by_id,
                        link_by_id=link_by_id,
                        unknown_by_id=unknown_by_id,
                    )
                )
        if len(clauses) != binding.visible_clause_count:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RENDER_CLAUSE_COUNT_MISMATCH"
            )
        clauses_by_group.setdefault(binding.sentence_group_ordinal, []).append(
            (
                binding.grammatical_chunk_ordinal,
                binding.proposition_unit_id,
                tuple(clauses),
            )
        )
    morphology = catalog["clause_morphology"]
    for group_ordinal, rows in clauses_by_group.items():
        if not 1 <= group_ordinal < len(observation_lines):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RENDER_GROUP_INVALID"
            )
        base_line = observation_lines[group_ordinal]
        if not base_line.endswith(morphology["sentence_suffix"]):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_BASE_SURFACE_LAYOUT_INVALID"
            )
        additions = tuple(
            morphology["within_sentence_clause_join"].join(clauses)
            + morphology["sentence_suffix"]
            for _chunk, _unit, clauses in sorted(rows)
        )
        observation_lines[group_ordinal] = base_line + "".join(additions)
    if not observation_lines[1].startswith(
        text.split(marker, 1)[0].split("\n")[1]
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_ROOT_PROPOSITION_DISPLACED"
        )

    receptions_by_line: dict[
        int, list[Step11Rc0031ReceptionPredicationBinding]
    ] = {}
    for row in reception_predications:
        receptions_by_line.setdefault(row.reception_line_ordinal, []).append(row)
    if tuple(reception_predications) != (
        surface_realization_plan.reception_predication_bindings
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_RECEPTION_PLAN_MISMATCH"
        )
    for line_ordinal, rows in receptions_by_line.items():
        if (
            not 1 <= line_ordinal <= len(reception_lines)
            or len(rows) > _STEP11_RC0031_RECEPTION_MOVES_PER_SENTENCE_MAX
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_RECEPTION_DENSITY_UNSATISFIABLE"
            )
        rendered: list[str] = []
        for row in sorted(
            rows,
            key=lambda item: (
                item.grammatical_chunk_ordinal,
                item.source_reception_opportunity_id,
            ),
        ):
            try:
                targets = tuple(
                    referent_by_owner[value]
                    for value in row.source_target_owner_ids
                )
                supports = tuple(
                    referent_by_owner[value]
                    for value in row.supporting_source_owner_ids
                )
            except KeyError as exc:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_RECEPTION_OWNER_UNRESOLVED"
                ) from exc
            act = catalog["reception_act_predicate_fragments"].get(
                row.reception_act
            )
            if act is None or not targets:
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_RECEPTION_SOURCE_BINDING_INVALID"
                )
            support_prefix = (
                morphology["support_owner_join"].join(supports)
                + morphology["support_target_link"]
                if supports
                else ""
            )
            predication = (
                support_prefix
                + morphology["target_owner_join"].join(targets)
                + morphology["reception_object_particle"]
                + str(act)
            )
            if any(
                marker_value in predication
                for marker_value in ("\r", "\n", "「", "」")
            ):
                raise Step11NaturalSurfaceError(
                    "STEP11_RC0031_RECEPTION_PREDICATION_INVALID"
                )
            rendered.append(predication)
        reception_lines[line_ordinal - 1] = (
            morphology["grammatical_sentence_join"].join(rendered)
            + morphology["sentence_suffix"]
        )

    final_text = "\n".join(observation_lines) + marker + "\n".join(
        reception_lines
    )
    body = final_text.encode("utf-8", errors="strict")
    return Step11Rc0031ExperimentRenderedSurface(
        schema_version=STEP11_RC0031_EXPERIMENT_RENDERED_SCHEMA,
        utf8_bytes=body,
        sha256=hashlib.sha256(body).hexdigest(),
        observation_group_count=len(observation_lines) - 1,
        proposition_clause_count=sum(
            row.visible_clause_count
            for row in proposition_surface_ast.proposition_clause_bindings
        ),
        semantic_atom_count=sum(
            len(row.source_atom_ids)
            for row in proposition_surface_ast.proposition_clause_bindings
        ),
        exact_reuse_count=len(
            surface_realization_plan.base_body_exact_reuse_bindings
        ),
        reception_predication_count=len(reception_predications),
    )


def render_step11_rc0031_experiment_surface(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    clause_ready_lexical_specs: Any,
    proposition_surface_ast: Step11Rc0031PropositionSurfaceAst,
    surface_realization_plan: Step11Rc0031SurfaceRealizationPlan,
    construction_atoms: Sequence[Step11Rc0028ExperimentConstructionAtom],
    relation_atoms: Sequence[Step11Rc0028ExperimentRelationAtom],
    semantic_link_atoms: Sequence[Step11Rc0028ExperimentSemanticLinkAtom],
    explicit_unknown_atoms: Sequence[Step11Rc0028ExperimentExplicitUnknownAtom],
    reception_predications: Sequence[
        Step11Rc0031ReceptionPredicationBinding
    ],
) -> Step11Rc0031ExperimentRenderedSurface:
    """Render P2 canonically while rejecting all caller-claimed body reuse."""

    try:
        return _step11_rc0031_render_from_verified_reuse_composition(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            clause_ready_lexical_specs=clause_ready_lexical_specs,
            proposition_surface_ast=proposition_surface_ast,
            surface_realization_plan=surface_realization_plan,
            construction_atoms=construction_atoms,
            relation_atoms=relation_atoms,
            semantic_link_atoms=semantic_link_atoms,
            explicit_unknown_atoms=explicit_unknown_atoms,
            reception_predications=reception_predications,
            verified_base_body_exact_reuse_bindings=None,
        )
    except Exception as exc:
        raise _step11_rc0031_boundary_error(
            exc, input_invalid_code="STEP11_RC0031_RENDER_INPUT_INVALID"
        ) from exc


def _step11_rc0031_build_ast(
    base_candidate: Step11NaturalSurfaceCandidate,
    plan: Step11Rc0031SurfaceRealizationPlan,
) -> Step11Rc0031PropositionSurfaceAst:
    provisional = Step11Rc0031PropositionSurfaceAst(
        schema_version=STEP11_RC0031_EXPERIMENT_AST_SCHEMA,
        ast_id="nls3s11rc0031ast_0000000000000000",
        source_base_candidate_id=base_candidate.candidate_id,
        source_base_surface_ast_id=base_candidate.surface_ast.surface_ast_id,
        root_proposition_binding=plan.root_proposition_binding,
        proposition_clause_bindings=plan.proposition_clause_bindings,
        reception_predication_bindings=plan.reception_predication_bindings,
        body_free=True,
    )
    return replace(
        provisional,
        ast_id=(
            "nls3s11rc0031ast_"
            + artifact_sha256(
                _step11_rc0031_ast_material(provisional, include_id=False)
            )[:16]
        ),
    )


def _step11_rc0031_candidate_identity(
    *,
    base_candidate_id: str,
    rendered: Step11Rc0031ExperimentRenderedSurface,
    plan: Step11Rc0031SurfaceRealizationPlan,
    ast: Step11Rc0031PropositionSurfaceAst,
) -> str:
    return "nls3s11rc0031cand_" + artifact_sha256(
        {
            "candidate_version_id": (
                STEP11_RC0031_EXPERIMENT_CANDIDATE_VERSION_ID
            ),
            "base_candidate_id": base_candidate_id,
            "final_bytes_sha256": rendered.sha256,
            "realization_plan_id": plan.realization_plan_id,
            "ast_id": ast.ast_id,
        }
    )[:20]


def _step11_rc0031_build_candidate_from_verified_reuse_composition(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    verified_base_body_exact_reuse_bindings: tuple[
        Step11Rc0031BaseBodyExactReuseBinding, ...
    ],
    validate_output: bool,
) -> Step11Rc0031ExperimentSurfaceCandidate:
    _step11_rc0031_validate_base_render_commitment(base_candidate)
    lexical_sha256 = _step11_rc0028_validate_lexical_specs(
        lexical_atom_specs, successor_snapshot=successor_snapshot
    )
    catalog, catalog_sha256 = _step11_rc0031_catalog()
    clause_ready = _step11_rc0031_clause_ready_projection(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
    )
    if (
        _SHA_RE.fullmatch(str(clause_ready.surface_catalog_sha256)) is None
        or clause_ready.surface_catalog_sha256 == catalog_sha256
    ):
        raise Step11NaturalSurfaceError(
            "STEP11_RC0031_LEXICAL_PROJECTION_COMMITMENT_INVALID"
        )
    rc0028_catalog, _rc0028_catalog_sha256 = _step11_rc0028_catalog()
    owner_registry, constructions, relations, links, unknowns = (
        _step11_rc0028_forward_atoms(
            successor_snapshot, lexical_atom_specs, rc0028_catalog
        )
    )
    lexemes = _step11_rc0031_lexemes(clause_ready)
    receptions = _step11_rc0031_reception_predications(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexemes=lexemes,
        catalog=catalog,
    )
    plan = _step11_rc0031_build_plan_from_verified_reuse_composition(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        clause_ready_lexical_specs=clause_ready,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_predications=receptions,
        verified_base_body_exact_reuse_bindings=(
            verified_base_body_exact_reuse_bindings
        ),
    )
    ast = _step11_rc0031_build_ast(base_candidate, plan)
    rendered = _step11_rc0031_render_from_verified_reuse_composition(
        base_candidate,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        clause_ready_lexical_specs=clause_ready,
        proposition_surface_ast=ast,
        surface_realization_plan=plan,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_predications=receptions,
        verified_base_body_exact_reuse_bindings=(
            verified_base_body_exact_reuse_bindings
        ),
    )
    candidate = Step11Rc0031ExperimentSurfaceCandidate(
        schema_version=STEP11_RC0031_EXPERIMENT_CANDIDATE_SCHEMA,
        candidate_version_id=STEP11_RC0031_EXPERIMENT_CANDIDATE_VERSION_ID,
        candidate_id=_step11_rc0031_candidate_identity(
            base_candidate_id=base_candidate.candidate_id,
            rendered=rendered,
            plan=plan,
            ast=ast,
        ),
        base_candidate=base_candidate,
        proposition_surface_ast=ast,
        rendered_surface=rendered,
        surface_realization_plan=plan,
        successor_snapshot_sha256=successor_snapshot.experiment_snapshot_sha256,
        lexical_atom_specs_sha256=lexical_sha256,
        experiment_catalog_sha256=catalog_sha256,
        source_lexical_projection_catalog_sha256=(
            clause_ready.surface_catalog_sha256
        ),
        natural_handle_specs=clause_ready,
        owner_registry=owner_registry,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_bindings=receptions,
        semantic_coverage_authorized=False,
        replan_count=0,
    )
    if validate_output:
        issues = _step11_rc0031_validate_candidate_from_verified_reuse_composition(
            candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            verified_base_body_exact_reuse_bindings=(
                verified_base_body_exact_reuse_bindings
            ),
        )
        if issues:
            raise Step11NaturalSurfaceError(issues[0])
    return candidate


def build_step11_rc0031_experiment_surface_candidate(
    base_candidate: Step11NaturalSurfaceCandidate,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    base_body_exact_reuse_bindings: Sequence[
        Step11Rc0031BaseBodyExactReuseBinding
    ] = (),
) -> Step11Rc0031ExperimentSurfaceCandidate:
    try:
        _step11_rc0031_validate_exact_reuse(
            base_body_exact_reuse_bindings,
            records=(),
            base_candidate=base_candidate,
            successor_snapshot=successor_snapshot,
        )
        return _step11_rc0031_build_candidate_from_verified_reuse_composition(
            base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            verified_base_body_exact_reuse_bindings=(),
            validate_output=True,
        )
    except Exception as exc:
        raise _step11_rc0031_boundary_error(
            exc,
            input_invalid_code="STEP11_RC0031_CANDIDATE_INPUT_INVALID",
        ) from exc


def build_step11_rc0031_experiment_surface_candidates(
    base_candidates: Sequence[Step11NaturalSurfaceCandidate],
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    base_body_exact_reuse_bindings: Sequence[
        Step11Rc0031BaseBodyExactReuseBinding
    ] = (),
) -> tuple[Step11Rc0031ExperimentSurfaceCandidate, ...]:
    try:
        if (
            type(base_candidates) not in {tuple, list}
            or not base_candidates
            or len(base_candidates) > _STEP11_RC0031_CANDIDATE_MAX
        ):
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_CANDIDATE_BOUND_INVALID"
            )
        base_rows = _step11_rc0031_exact_bounded_rows(
            base_candidates,
            item_types=(Step11NaturalSurfaceCandidate,),
            maximum=_STEP11_RC0031_CANDIDATE_MAX,
            allow_empty=False,
        )
        _step11_rc0028_validate_lexical_specs(
            lexical_atom_specs, successor_snapshot=successor_snapshot
        )
        _step11_rc0031_validate_exact_reuse(
            base_body_exact_reuse_bindings,
            records=(),
            base_candidate=base_rows[0],
            successor_snapshot=successor_snapshot,
        )
        rows: list[Step11Rc0031ExperimentSurfaceCandidate] = []
        for base_candidate in base_rows:
            try:
                rows.append(
                    build_step11_rc0031_experiment_surface_candidate(
                        base_candidate,
                        successor_snapshot=successor_snapshot,
                        lexical_atom_specs=lexical_atom_specs,
                        base_body_exact_reuse_bindings=(),
                    )
                )
            except Step11NaturalSurfaceError as exc:
                if exc.code == "STEP11_RC0031_CANDIDATE_INPUT_INVALID":
                    raise
                continue
        if not rows:
            raise Step11NaturalSurfaceError(
                "STEP11_RC0031_NO_VALID_FORWARD_CANDIDATE"
            )
        return tuple(rows)
    except Exception as exc:
        raise _step11_rc0031_boundary_error(
            exc,
            input_invalid_code="STEP11_RC0031_CANDIDATE_INPUT_INVALID",
        ) from exc


def _step11_rc0031_validate_candidate_from_verified_reuse_composition(
    value: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    verified_base_body_exact_reuse_bindings: tuple[
        Step11Rc0031BaseBodyExactReuseBinding, ...
    ],
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0031ExperimentSurfaceCandidate:
        return ("STEP11_RC0031_CANDIDATE_TYPE_INVALID",)
    issues: set[str] = set()
    try:
        expected = _step11_rc0031_build_candidate_from_verified_reuse_composition(
            value.base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            verified_base_body_exact_reuse_bindings=(
                verified_base_body_exact_reuse_bindings
            ),
            validate_output=False,
        )
    except Exception:
        return ("STEP11_RC0031_CANDIDATE_REVALIDATION_FAILED",)
    try:
        _step11_rc0031_preflight_clause_ready(value.natural_handle_specs)
        _step11_rc0031_exact_bounded_rows(
            value.owner_registry,
            item_types=(str,),
            maximum=_STEP11_RC0031_OWNER_MAX,
        )
        _step11_rc0031_preflight_forward_rows(
            construction_atoms=value.construction_atoms,
            relation_atoms=value.relation_atoms,
            semantic_link_atoms=value.semantic_link_atoms,
            explicit_unknown_atoms=value.explicit_unknown_atoms,
            reception_predications=value.reception_bindings,
        )
        if not _step11_rc0031_safe_structural_equal(value, expected):
            issues.add("STEP11_RC0031_CANDIDATE_SOURCE_MISMATCH")
        if value.semantic_coverage_authorized is not False:
            issues.add("STEP11_RC0031_SEMANTIC_COVERAGE_SELF_CLAIM")
        if (
            value.experimental_only is not True
            or value.private_body_full is not True
            or value.shareable is not False
            or value.runtime_connected is not False
        ):
            issues.add("STEP11_RC0031_RUNTIME_BOUNDARY_INVALID")
        if (
            type(value.replan_count) is not int
            or not 0 <= value.replan_count <= _STEP11_RC0031_REPLAN_MAX
        ):
            issues.add("STEP11_RC0031_REPLAN_BOUND_EXCEEDED")
        if (
            type(value.rendered_surface)
            is not Step11Rc0031ExperimentRenderedSurface
            or type(value.proposition_surface_ast)
            is not Step11Rc0031PropositionSurfaceAst
            or type(value.surface_realization_plan)
            is not Step11Rc0031SurfaceRealizationPlan
            or type(value.rendered_surface.utf8_bytes) is not bytes
            or type(value.rendered_surface.sha256) is not str
            or not _step11_rc0031_safe_structural_equal(
                value.rendered_surface.sha256,
                hashlib.sha256(value.rendered_surface.utf8_bytes).hexdigest(),
            )
            or not _step11_rc0031_safe_structural_equal(
                value.rendered_surface, expected.rendered_surface
            )
            or not _step11_rc0031_safe_structural_equal(
                value.proposition_surface_ast, expected.proposition_surface_ast
            )
            or not _step11_rc0031_safe_structural_equal(
                value.surface_realization_plan,
                expected.surface_realization_plan,
            )
        ):
            issues.add("STEP11_RC0031_CANONICAL_RENDER_MISMATCH")
    except Exception:
        return ("STEP11_RC0031_CANDIDATE_REVALIDATION_FAILED",)
    return tuple(sorted(issues))


def validate_step11_rc0031_experiment_surface_candidate(
    value: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
) -> tuple[str, ...]:
    """Revalidate only the P2 candidate shape; caller reuse remains denied."""

    if type(value) is not Step11Rc0031ExperimentSurfaceCandidate:
        return ("STEP11_RC0031_CANDIDATE_TYPE_INVALID",)
    try:
        if type(value.surface_realization_plan) is not Step11Rc0031SurfaceRealizationPlan:
            return ("STEP11_RC0031_CANDIDATE_REVALIDATION_FAILED",)
        reuse = value.surface_realization_plan.base_body_exact_reuse_bindings
    except Exception:
        return ("STEP11_RC0031_CANDIDATE_REVALIDATION_FAILED",)
    if (
        type(reuse) is not tuple
        or len(reuse) > _STEP11_RC0031_EXACT_REUSE_MAX
        or any(
            type(row) is not Step11Rc0031BaseBodyExactReuseBinding
            for row in reuse
        )
    ):
        return ("STEP11_RC0031_CANDIDATE_REVALIDATION_FAILED",)
    if reuse:
        return ("STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE",)
    return _step11_rc0031_validate_candidate_from_verified_reuse_composition(
        value,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        verified_base_body_exact_reuse_bindings=(),
    )


__all__ += [
    "STEP11_RC0031_EXPERIMENT_AST_SCHEMA",
    "STEP11_RC0031_EXPERIMENT_CANDIDATE_SCHEMA",
    "STEP11_RC0031_EXPERIMENT_CANDIDATE_VERSION_ID",
    "STEP11_RC0031_EXPERIMENT_PLAN_SCHEMA",
    "STEP11_RC0031_EXPERIMENT_RENDERED_SCHEMA",
    "Step11Rc0031BaseBodyExactReuseBinding",
    "Step11Rc0031ExperimentRenderedSurface",
    "Step11Rc0031ExperimentSurfaceCandidate",
    "Step11Rc0031PropositionChunkAssignment",
    "Step11Rc0031PropositionClauseBinding",
    "Step11Rc0031PropositionSurfaceAst",
    "Step11Rc0031ReceptionPredicationBinding",
    "Step11Rc0031RootPropositionBinding",
    "Step11Rc0031SurfaceRealizationPlan",
    "build_step11_rc0031_experiment_surface_candidate",
    "build_step11_rc0031_experiment_surface_candidates",
    "build_step11_rc0031_surface_realization_plan",
    "render_step11_rc0031_experiment_surface",
    "step11_rc0031_surface_realization_plan_material",
    "validate_step11_rc0031_experiment_surface_candidate",
]
