# -*- coding: utf-8 -*-
from __future__ import annotations

"""Pure request-local Cycle001 Product recovery candidate.

The owner starts from independently replayable Step 4 and lexical-successor
artifacts.  It neither creates nor claims an rc0027 candidate.  The rendered
body is private and every visible clause is derived from closed typed source
records and closed catalog morphology.
"""

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
from typing import Any, Final

from emlis_ai_content_selection_v3 import build_content_selection_plan
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver,
    build_evidence_ledger,
)
from emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3 import (
    GroundedLexicalRoleExperimentSnapshotSuccessor,
    validate_grounded_lexical_role_experiment_snapshot_successor,
)
from emlis_ai_grounded_observation_plan import GroundedObservationPlan
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    build_grounded_semantic_restatement_witness,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
    validate_semantic_obligation_inventory,
)
from emlis_ai_step11_grounded_lexicalization_v3 import (
    Step11Rc0028ExperimentLexicalAtomSpecs,
    validate_step11_rc0028_experiment_lexical_atom_specs,
)
from emlis_ai_step11_natural_surface_v3 import (
    _STEP11_RC0035_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA,
    _STEP11_RC0035_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID,
    _step11_rc0028_catalog,
    _step11_rc0028_forward_atoms,
    _step11_rc0031_product_source_dimensions,
    _step11_rc0031_product_surface_authorities,
    _step11_rc0031_render_semantic_clause,
    _step11_rc0035_cycle001_product_recovery_candidate_identity,
    project_step11_current_input,
)
from emlis_ai_step11_rc0029_experiment_surface_catalog_v3 import (
    STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG,
    STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256,
    validate_step11_rc0029_experiment_surface_catalog,
)


STEP11_CYCLE001_PRODUCT_RECOVERY_SOURCE_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_source.rc0035.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_OWNER_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_owner.rc0035.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_PLAN_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_plan.rc0035.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_RENDERED_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_rendered.rc0035.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID: Final = (
    _STEP11_RC0035_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID
)
STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA: Final = (
    _STEP11_RC0035_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA
)

_OWNER_MAX: Final = 24
_ROOT_MAX: Final = 24
_ATOM_MAX: Final = 64
_RECEPTION_MAX: Final = 4
_REFERENT_SCALAR_MAX: Final = 512
_ALLOWED_RECEPTION_ACTS: Final = frozenset(
    {"do_not_dismiss", "hold_in_attention", "honor_concrete_action"}
)
_INTENDED_MODALITIES: Final = frozenset({"intended"})
_FUTURE_TEMPORAL_SCOPES: Final = frozenset(
    {"future", "present_to_future", "intended_future"}
)
_SEMANTIC_COVERAGE_AUTHORITY: Final = (
    "rc0035_source_envelope_visible_inverse_replay"
)


class Step11Cycle001ProductRecoveryError(ValueError):
    """Fail-closed error containing one body-free code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoveryCurrentInputBinding:
    thought_text: str
    action_text: str
    emotions: tuple[str, ...]
    categories: tuple[str, ...]
    projected_material_sha256: str
    normalized_bundle_sha256: str
    snapshot_original_input_bundle_sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoveryOwnerBinding:
    schema_version: str
    source_owner_id: str
    source_owner_kind: str
    source_owner_ordinal: int
    source_nucleus_id: str
    semantic_kind: str
    dimensions: tuple[str, str, str, str]
    typed_role_tokens: tuple[str, ...]
    referent_text: str
    referent_text_sha256: str
    referent_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoverySourceFragmentBinding:
    source_fragment_id: str
    source_owner_id: str
    source_nucleus_id: str
    source_span_id: str
    source_field: str
    span_relative_start_index: int
    span_relative_end_index: int
    source_fragment_text: str
    source_fragment_text_sha256: str
    binding_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoveryRootBinding:
    source_root_id: str
    source_owner_id: str
    source_nucleus_id: str
    source_obligation_ids: tuple[str, ...]
    source_fragments: tuple[
        Step11Cycle001ProductRecoverySourceFragmentBinding, ...
    ]
    semantic_kind: str
    dimensions: tuple[str, str, str, str]
    required: bool


@dataclass(frozen=True, slots=True)
class Step11Cycle001ProductRecoveryConstructionRoleBinding:
    construction_slot_id: str
    parent_nucleus_id: str
    source_span_id: str
    slot_start_index: int
    slot_end_index: int
    lexical_role_kind: str
    construction_position: str
    role_position_surface_token: str
    source_owner_ids: tuple[str, ...]
    source_owner_dimensions: tuple[tuple[str, str, str, str], ...]
    participation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Step11Cycle001ProductRecoveryAtomBinding:
    source_atom_id: str
    semantic_family: str
    semantic_key: str
    source_owner_ids: tuple[str, ...]
    direction: str
    dimensions: tuple[str, str, str, str]
    source_nucleus_owner_ids: tuple[str, ...]
    source_semantic_unit_owner_ids: tuple[str, ...]
    source_parent_nucleus_ids: tuple[str, ...]
    source_span_ids: tuple[str, ...]
    source_evidence_alias_ids: tuple[str, ...]
    source_marker_span_ids: tuple[str, ...]
    construction_roles: tuple[
        Step11Cycle001ProductRecoveryConstructionRoleBinding, ...
    ]
    source_order: int


@dataclass(frozen=True, slots=True)
class Step11Cycle001ProductRecoveryReceptionBinding:
    source_reception_opportunity_id: str
    source_scope: str
    source_focus_owner_ids: tuple[str, ...]
    source_target_owner_ids: tuple[str, ...]
    supporting_source_owner_ids: tuple[str, ...]
    visible_support_owner_ids: tuple[str, ...]
    inventory_reception_act: str
    effective_reception_act: str
    act_refinement_basis: str
    sentence_group_ordinal: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoverySourceEnvelope:
    schema_version: str
    candidate_version_id: str
    source_candidate_id: str
    source_observation_plan_sha256: str
    source_successor_snapshot_sha256: str
    source_lexical_atom_specs_sha256: str
    source_semantic_restatement_witness_sha256: str
    source_inventory_ledger_sha256: str
    source_content_plan_sha256: str
    source_discourse_plan_sha256: str
    current_input_binding: Step11Cycle001ProductRecoveryCurrentInputBinding
    source_lexical_catalog_sha256: str
    surface_catalog_sha256: str
    duplicated_typed_payload_sha256: str
    owner_bindings: tuple[Step11Cycle001ProductRecoveryOwnerBinding, ...]
    root_bindings: tuple[Step11Cycle001ProductRecoveryRootBinding, ...]
    atom_bindings: tuple[Step11Cycle001ProductRecoveryAtomBinding, ...]
    reception_bindings: tuple[
        Step11Cycle001ProductRecoveryReceptionBinding, ...
    ]
    source_counts: tuple[tuple[str, int], ...]
    old_gate_consulted: bool
    old_selector_consulted: bool
    base_acceptance_claimed: bool
    semantic_coverage_authorized: bool
    semantic_coverage_authority: str
    source_envelope_sha256: str
    experimental_only: bool = True
    private_body_full: bool = True
    shareable: bool = False
    runtime_connected: bool = False


@dataclass(frozen=True, slots=True)
class Step11Cycle001ProductRecoveryRealizationUnit:
    line_ordinal: int
    section_role: str
    source_unit_id: str
    source_atom_ids: tuple[str, ...]
    source_owner_ids: tuple[str, ...]
    source_owner_dimensions: tuple[
        tuple[str, tuple[str, str, str, str]], ...
    ]
    source_obligation_ids: tuple[str, ...]
    source_fragment_ids: tuple[str, ...]
    dimensions: tuple[str, str, str, str]
    visible_clause_count: int


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoveryPlan:
    schema_version: str
    candidate_version_id: str
    realization_plan_id: str
    ast_id: str
    source_envelope_sha256: str
    duplicated_typed_payload_sha256: str
    candidate_boundary_sha256: str
    units: tuple[Step11Cycle001ProductRecoveryRealizationUnit, ...]
    observation_line_count: int
    reception_line_count: int
    maximum_visible_clauses_per_line: int
    body_free: bool = True


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoveryRenderedSurface:
    schema_version: str
    source_envelope_sha256: str
    source_realization_plan_id: str
    utf8_bytes: bytes
    sha256: str
    observation_line_count: int
    reception_line_count: int


@dataclass(frozen=True, slots=True)
class Step11Cycle001ProductRecoveryVisibleBinding:
    line_ordinal: int
    section_role: str
    source_unit_id: str
    source_atom_ids: tuple[str, ...]
    source_owner_ids: tuple[str, ...]
    source_owner_dimensions: tuple[
        tuple[str, tuple[str, str, str, str]], ...
    ]
    source_obligation_ids: tuple[str, ...]
    source_fragment_ids: tuple[str, ...]
    source_fragment_text_sha256s: tuple[str, ...]
    visible_line_sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class Step11Cycle001ProductRecoveryCandidate:
    schema_version: str
    candidate_version_id: str
    candidate_id: str
    source_envelope: Step11Cycle001ProductRecoverySourceEnvelope
    realization_plan: Step11Cycle001ProductRecoveryPlan
    rendered_surface: Step11Cycle001ProductRecoveryRenderedSurface
    owner_registry: tuple[str, ...]
    construction_atoms: tuple[Any, ...]
    relation_atoms: tuple[Any, ...]
    semantic_link_atoms: tuple[Any, ...]
    explicit_unknown_atoms: tuple[Any, ...]
    reception_bindings: tuple[
        Step11Cycle001ProductRecoveryReceptionBinding, ...
    ]
    semantic_coverage_authorized: bool
    old_gate_consulted: bool
    old_selector_consulted: bool
    base_acceptance_claimed: bool
    experimental_only: bool = True
    private_body_full: bool = True
    shareable: bool = False
    runtime_connected: bool = False

    @property
    def final_utf8_bytes(self) -> bytes:
        return self.rendered_surface.utf8_bytes


def _plain(value: Any) -> Any:
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is tuple:
        return [_plain(row) for row in value]
    if type(value) is list:
        return [_plain(row) for row in value]
    if type(value) is dict:
        return {str(key): _plain(child) for key, child in value.items()}
    if is_dataclass(value):
        return {
            row.name: _plain(getattr(value, row.name))
            for row in fields(value)
        }
    raise Step11Cycle001ProductRecoveryError(
        "STEP11_CYCLE001_RECOVERY_MATERIAL_INVALID"
    )


def _source_envelope_material(
    value: Step11Cycle001ProductRecoverySourceEnvelope,
    *,
    include_identity: bool = True,
) -> dict[str, Any]:
    result = _plain(value)
    if type(result) is not dict:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_SOURCE_INVALID"
        )
    if not include_identity:
        result.pop("source_candidate_id")
        result.pop("source_envelope_sha256")
    return result


def step11_cycle001_product_recovery_source_envelope_material(
    value: Step11Cycle001ProductRecoverySourceEnvelope,
    *,
    include_id: bool = True,
) -> dict[str, Any]:
    if type(value) is not Step11Cycle001ProductRecoverySourceEnvelope:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_SOURCE_INVALID"
        )
    return _source_envelope_material(value, include_identity=include_id)


def _plan_material(
    value: Step11Cycle001ProductRecoveryPlan,
    *,
    include_identity: bool = True,
) -> dict[str, Any]:
    result = _plain(value)
    if type(result) is not dict:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_PLAN_INVALID"
        )
    if not include_identity:
        result.pop("realization_plan_id")
        result.pop("ast_id")
    return result


def _candidate_boundary_material(
    *,
    semantic_coverage_authorized: bool,
    old_gate_consulted: bool,
    old_selector_consulted: bool,
    base_acceptance_claimed: bool,
    experimental_only: bool,
    private_body_full: bool,
    shareable: bool,
    runtime_connected: bool,
) -> dict[str, bool]:
    return {
        "semantic_coverage_authorized": semantic_coverage_authorized,
        "old_gate_consulted": old_gate_consulted,
        "old_selector_consulted": old_selector_consulted,
        "base_acceptance_claimed": base_acceptance_claimed,
        "experimental_only": experimental_only,
        "private_body_full": private_body_full,
        "shareable": shareable,
        "runtime_connected": runtime_connected,
    }


def _typed_payload_material(
    *,
    owner_registry: Sequence[str],
    constructions: Sequence[Any],
    relations: Sequence[Any],
    links: Sequence[Any],
    unknowns: Sequence[Any],
    receptions: Sequence[Step11Cycle001ProductRecoveryReceptionBinding],
) -> dict[str, Any]:
    return {
        "owner_registry": _plain(tuple(owner_registry)),
        "construction_atoms": _plain(tuple(constructions)),
        "relation_atoms": _plain(tuple(relations)),
        "semantic_link_atoms": _plain(tuple(links)),
        "explicit_unknown_atoms": _plain(tuple(unknowns)),
        "reception_bindings": _plain(tuple(receptions)),
    }


def _validated_sources(
    *,
    plan: Any,
    resolver: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: Any,
    content_plan: Any,
    discourse_plans: Any,
    current_input: Any,
) -> tuple[
    tuple[Mapping[str, Any], ...],
    Any,
    Step11Cycle001ProductRecoveryCurrentInputBinding,
]:
    if (
        type(plan) is not GroundedObservationPlan
        or type(resolver) is not EvidenceSpanResolver
        or type(successor_snapshot)
        is not GroundedLexicalRoleExperimentSnapshotSuccessor
        or type(lexical_atom_specs)
        is not Step11Rc0028ExperimentLexicalAtomSpecs
        or type(inventory_result) is not SemanticObligationInventoryResult
        or type(content_plan) is not dict
        or type(current_input) is not dict
        or type(discourse_plans) not in {tuple, list}
        or not 1 <= len(discourse_plans) <= 12
        or any(type(row) is not dict for row in discourse_plans)
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_SOURCE_INVALID"
        )
    if validate_grounded_lexical_role_experiment_snapshot_successor(
        successor_snapshot
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_SUCCESSOR_INVALID"
        )
    if validate_step11_rc0028_experiment_lexical_atom_specs(
        lexical_atom_specs,
        successor_snapshot=successor_snapshot,
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_LEXICAL_SPECS_INVALID"
        )
    if (
        inventory_result.source_snapshot != successor_snapshot.base_snapshot
        or validate_semantic_obligation_inventory(
            inventory_result.ledger,
            source_snapshot=inventory_result.source_snapshot,
        )
        or build_content_selection_plan(inventory_result) != content_plan
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_INVENTORY_INVALID"
        )
    projection = project_step11_current_input(current_input)
    projection_material = {
        "thought_text": projection.thought_text,
        "action_text": projection.action_text,
        "emotions": list(projection.emotions),
        "categories": list(projection.categories),
    }
    normalized_current_input = normalize_emlis_current_input(current_input)
    snapshot = successor_snapshot.base_snapshot
    original_bundle_sha256 = artifact_sha256(normalized_current_input)
    snapshot_original_bundle_sha256 = str(
        snapshot.observation_stage_source_binding.original_input_bundle_sha256
    )
    rebuilt_evidence = tuple(build_evidence_ledger(normalized_current_input))
    resolved_evidence = tuple(
        resolver.resolve(span_id) for span_id in resolver.span_ids
    )
    if (
        original_bundle_sha256 != snapshot_original_bundle_sha256
        or rebuilt_evidence != resolved_evidence
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_CURRENT_INPUT_SOURCE_MISMATCH"
        )
    current_input_binding = Step11Cycle001ProductRecoveryCurrentInputBinding(
        thought_text=projection.thought_text,
        action_text=projection.action_text,
        emotions=tuple(projection.emotions),
        categories=tuple(projection.categories),
        projected_material_sha256=artifact_sha256(projection_material),
        normalized_bundle_sha256=original_bundle_sha256,
        snapshot_original_input_bundle_sha256=(
            snapshot_original_bundle_sha256
        ),
    )
    witness = build_grounded_semantic_restatement_witness(plan, resolver)
    if (
        witness.plan_binding_sha256
        != snapshot.semantic_restatement_plan_binding_sha256
        or witness.witness_sha256
        != snapshot.source_semantic_restatement_witness_sha256
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_PLAN_SOURCE_MISMATCH"
        )
    return tuple(discourse_plans), witness, current_input_binding


def _nucleus_dimensions(value: Any) -> tuple[str, str, str, str]:
    return (
        str(value.temporal_scope),
        str(value.modality),
        str(value.polarity),
        str(value.referent_scope),
    )


def _ordered_unique(values: Sequence[Any]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values))


def _reception_bindings(
    *,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
) -> tuple[Step11Cycle001ProductRecoveryReceptionBinding, ...]:
    snapshot = successor_snapshot.base_snapshot
    nuclei = tuple(snapshot.nuclei)
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    nucleus_by_actual = {str(row.actual_source_id): row for row in nuclei}

    def actual(value: Any) -> str:
        key = str(value)
        return actual_by_source.get(key, key)

    rows: list[Step11Cycle001ProductRecoveryReceptionBinding] = []
    opportunities = tuple(
        row
        for row in snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    if not 1 <= len(opportunities) <= _RECEPTION_MAX:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RECEPTION_BOUND_INVALID"
        )
    for ordinal, opportunity in enumerate(opportunities, start=1):
        targets = _ordered_unique(
            tuple(actual(value) for value in opportunity.target_nucleus_ids)
        )
        supports = _ordered_unique(
            tuple(actual(value) for value in opportunity.support_nucleus_ids)
        )
        if (
            not targets
            or any(value not in nucleus_by_actual for value in targets)
            or any(value not in nucleus_by_actual for value in supports)
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_OWNER_INVALID"
            )
        inventory_act = str(opportunity.reception_act)
        if inventory_act not in _ALLOWED_RECEPTION_ACTS:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        target_rows = tuple(nucleus_by_actual[value] for value in targets)
        intention = bool(
            any(
                str(row.modality) in _INTENDED_MODALITIES
                or str(row.temporal_scope) in _FUTURE_TEMPORAL_SCOPES
                for row in target_rows
            )
        )
        if inventory_act == "honor_concrete_action" and intention:
            effective = "do_not_dismiss"
            basis = "intended_or_future_action_nonpromotion"
        else:
            effective = inventory_act
            basis = "source_reception_act_projection"
        visible_support = tuple(
            value for value in supports if value not in set(targets)
        )
        rows.append(
            Step11Cycle001ProductRecoveryReceptionBinding(
                source_reception_opportunity_id=str(opportunity.source_id),
                source_scope=str(opportunity.family),
                source_focus_owner_ids=(),
                source_target_owner_ids=targets,
                supporting_source_owner_ids=supports,
                visible_support_owner_ids=visible_support,
                inventory_reception_act=inventory_act,
                effective_reception_act=effective,
                act_refinement_basis=basis,
                sentence_group_ordinal=ordinal,
            )
        )
    return tuple(rows)


def _role_tokens(
    *,
    lexical_atom_specs: Step11Rc0028ExperimentLexicalAtomSpecs,
    reception_bindings: Sequence[
        Step11Cycle001ProductRecoveryReceptionBinding
    ],
) -> dict[str, tuple[str, ...]]:
    rows: dict[str, list[str]] = defaultdict(list)
    role_catalog = STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG[
        "owner_role_surface_tokens"
    ]
    owner_by_ordinal = {
        int(row.owner_ordinal): str(row.source_owner_id)
        for row in lexical_atom_specs.owner_bindings
    }
    for atom in lexical_atom_specs.construction_atoms:
        for ordinal in atom.target_owner_ordinals:
            rows[owner_by_ordinal[int(ordinal)]].append(
                str(atom.role_position_surface_token)
            )
    for atom in lexical_atom_specs.relation_endpoint_atoms:
        rows[str(atom.source_owner_id)].append(
            str(atom.relation_surface_token)
            + str(role_catalog["relation_" + atom.relation_endpoint_role])
        )
    for atom in lexical_atom_specs.semantic_link_atoms:
        rows[str(atom.from_semantic_unit_id)].append(
            str(atom.semantic_link_surface_token)
            + str(role_catalog["semantic_link_from"])
        )
        rows[str(atom.to_semantic_unit_id)].append(
            str(atom.semantic_link_surface_token)
            + str(role_catalog["semantic_link_to"])
        )
    for atom in lexical_atom_specs.explicit_unknown_atoms:
        for _kind, owner_id, _ordinal in atom.affected_source_owners:
            rows[str(owner_id)].append(
                str(atom.unknown_surface_token)
                + str(role_catalog["explicit_unknown"])
            )
    for binding in reception_bindings:
        for owner_id in binding.source_target_owner_ids:
            rows[owner_id].append(str(role_catalog["reception_target"]))
        for owner_id in binding.visible_support_owner_ids:
            rows[owner_id].append(str(role_catalog["reception_support"]))
        for owner_id in binding.source_focus_owner_ids:
            rows[owner_id].append(str(role_catalog["reception_antecedent"]))
    return {
        owner_id: tuple(dict.fromkeys(values))
        for owner_id, values in rows.items()
    }


def _owner_bindings(
    *,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    lexical_atom_specs: Step11Rc0028ExperimentLexicalAtomSpecs,
    active_owner_ids: set[str],
    role_tokens: Mapping[str, tuple[str, ...]],
) -> tuple[Step11Cycle001ProductRecoveryOwnerBinding, ...]:
    snapshot = successor_snapshot.base_snapshot
    nucleus_by_actual = {
        str(row.actual_source_id): row for row in snapshot.nuclei
    }
    owner_rows = tuple(
        row
        for row in lexical_atom_specs.owner_bindings
        if str(row.source_owner_id) in active_owner_ids
    )
    if not 1 <= len(owner_rows) <= _OWNER_MAX:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_OWNER_BOUND_INVALID"
        )
    head_catalog = STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG[
        "owner_kind_surface_tokens"
    ]
    prepared: list[tuple[Any, Any, str, tuple[str, ...]]] = []
    for owner in owner_rows:
        nucleus = nucleus_by_actual.get(str(owner.source_owner_id))
        if nucleus is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_SOURCE_UNRESOLVED"
            )
        kind = str(nucleus.kind)
        head = head_catalog.get(kind)
        if type(head) is not str or not head:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_KIND_INVALID"
            )
        prepared.append(
            (owner, nucleus, head, role_tokens.get(str(owner.source_owner_id), ()))
        )

    referents = [row[2] for row in prepared]
    duplicate_heads = {
        head
        for head, count in Counter(referents).items()
        if count > 1
    }
    for head in duplicate_heads:
        indices = [
            index
            for index, row in enumerate(prepared)
            if row[2] == head
        ]
        options_by_index = {index: prepared[index][3] for index in indices}
        assigned: dict[int, str] = {}
        for index in indices:
            options = options_by_index[index]
            for option in options:
                if sum(option in options_by_index[other] for other in indices) == 1:
                    assigned[index] = option + "に関わる" + head
                    break
        for index in indices:
            if index in assigned:
                continue
            joined = "、".join(options_by_index[index])
            if joined:
                candidate = joined + "に関わる" + head
                other_candidates = tuple(
                    "、".join(options_by_index[other]) + "に関わる" + head
                    for other in indices
                    if other not in assigned
                    and options_by_index[other]
                )
                if candidate not in other_candidates:
                    assigned[index] = candidate
        unresolved = tuple(index for index in indices if index not in assigned)
        if len(unresolved) > 1:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_REFERENT_COLLISION"
            )
        for index, referent in assigned.items():
            referents[index] = referent
        values = tuple(referents[index] for index in indices)
        if len(set(values)) != len(values):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_REFERENT_COLLISION"
            )

    result: list[Step11Cycle001ProductRecoveryOwnerBinding] = []
    for (owner, nucleus, _head, tokens), referent in zip(
        prepared, referents, strict=True
    ):
        if (
            not referent
            or len(referent) > _REFERENT_SCALAR_MAX
            or any(marker in referent for marker in ("\r", "\n"))
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_REFERENT_INVALID"
            )
        result.append(
            Step11Cycle001ProductRecoveryOwnerBinding(
                schema_version=STEP11_CYCLE001_PRODUCT_RECOVERY_OWNER_SCHEMA,
                source_owner_id=str(owner.source_owner_id),
                source_owner_kind=str(owner.source_owner_kind),
                source_owner_ordinal=int(owner.owner_ordinal),
                source_nucleus_id=str(nucleus.source_id),
                semantic_kind=str(nucleus.kind),
                dimensions=_nucleus_dimensions(nucleus),
                typed_role_tokens=tuple(tokens),
                referent_text=referent,
                referent_text_sha256=hashlib.sha256(
                    referent.encode("utf-8")
                ).hexdigest(),
                referent_basis=(
                    "typed_kind"
                    if referent == str(_head)
                    else "typed_incident_role_disambiguation"
                ),
            )
        )
    if len({row.referent_text for row in result}) != len(result):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_OWNER_REFERENT_COLLISION"
        )
    return tuple(result)


def _root_bindings(
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    semantic_restatement_witness: Any,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    inventory_result: SemanticObligationInventoryResult,
) -> tuple[Step11Cycle001ProductRecoveryRootBinding, ...]:
    snapshot = successor_snapshot.base_snapshot
    obligations = tuple(inventory_result.ledger["obligations"])
    grounded_nucleus_by_id = {
        str(row.nucleus_id): row for row in plan.nuclei
    }
    semantic_unit_by_id = {
        str(row.unit_id): row
        for row in semantic_restatement_witness.semantic_units
    }

    def fragment_binding(
        *,
        owner_id: str,
        nucleus_id: str,
        span_id: str,
        relative_start: int,
        relative_end: int,
        basis: str,
        expected_artifact_sha256: str | None = None,
    ) -> Step11Cycle001ProductRecoverySourceFragmentBinding:
        span = resolver.resolve(span_id)
        raw_text = getattr(span, "raw_text", None)
        source_field = getattr(span, "source_field", None)
        if (
            type(raw_text) is not str
            or not raw_text
            or type(source_field) is not str
            or not source_field
            or type(relative_start) is not int
            or type(relative_end) is not int
            or relative_start < 0
            or relative_end <= relative_start
            or relative_end > len(raw_text)
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
            )
        text = raw_text[relative_start:relative_end]
        if (
            not text
            or any(character in text for character in ("\r", "\n"))
            or any(ord(character) < 32 for character in text)
            or (
                expected_artifact_sha256 is not None
                and artifact_sha256({"source_fragment": text})
                != expected_artifact_sha256
            )
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
            )
        text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        material = {
            "source_owner_id": owner_id,
            "source_nucleus_id": nucleus_id,
            "source_span_id": span_id,
            "source_field": source_field,
            "span_relative_start_index": relative_start,
            "span_relative_end_index": relative_end,
            "source_fragment_text_sha256": text_sha256,
            "binding_basis": basis,
        }
        return Step11Cycle001ProductRecoverySourceFragmentBinding(
            source_fragment_id=(
                "nls3s11rc0035fragment_" + artifact_sha256(material)[:16]
            ),
            source_owner_id=owner_id,
            source_nucleus_id=nucleus_id,
            source_span_id=span_id,
            source_field=source_field,
            span_relative_start_index=relative_start,
            span_relative_end_index=relative_end,
            source_fragment_text=text,
            source_fragment_text_sha256=text_sha256,
            binding_basis=basis,
        )

    rows: list[Step11Cycle001ProductRecoveryRootBinding] = []
    for nucleus in snapshot.nuclei:
        if nucleus.required is not True:
            continue
        source_nucleus_id = str(nucleus.source_id)
        owner_id = str(nucleus.actual_source_id)
        aliases = {source_nucleus_id, owner_id}
        owner_obligations = tuple(
            str(row["obligation_id"])
            for row in obligations
            if type(row) is dict
            and row.get("required") is True
            and aliases & {str(value) for value in row.get("nucleus_ids", ())}
        )
        if not owner_obligations:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_OBLIGATION_INVALID"
            )
        semantic_unit = semantic_unit_by_id.get(owner_id)
        if semantic_unit is not None:
            fragments = (
                fragment_binding(
                    owner_id=owner_id,
                    nucleus_id=source_nucleus_id,
                    span_id=str(semantic_unit.source_span_id),
                    relative_start=int(semantic_unit.start_index),
                    relative_end=int(semantic_unit.end_index),
                    basis="semantic_unit_exact_typed_range",
                    expected_artifact_sha256=str(
                        semantic_unit.source_fragment_sha256
                    ),
                ),
            )
        else:
            grounded_nucleus = grounded_nucleus_by_id.get(owner_id)
            if grounded_nucleus is None:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_ROOT_SOURCE_UNRESOLVED"
                )
            span_ids = _ordered_unique(
                tuple(grounded_nucleus.source_span_ids)
            )
            if not span_ids:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_ROOT_SOURCE_UNRESOLVED"
                )
            fragments = tuple(
                fragment_binding(
                    owner_id=owner_id,
                    nucleus_id=source_nucleus_id,
                    span_id=span_id,
                    relative_start=0,
                    relative_end=len(str(resolver.resolve(span_id).raw_text)),
                    basis="grounded_nucleus_exact_evidence_span",
                )
                for span_id in span_ids
            )
        material = {
            "source_owner_id": owner_id,
            "source_nucleus_id": source_nucleus_id,
            "source_obligation_ids": list(owner_obligations),
            "source_fragment_ids": [
                row.source_fragment_id for row in fragments
            ],
            "semantic_kind": str(nucleus.kind),
            "dimensions": list(_nucleus_dimensions(nucleus)),
        }
        rows.append(
            Step11Cycle001ProductRecoveryRootBinding(
                source_root_id=(
                    "nls3s11rc0035root_" + artifact_sha256(material)[:16]
                ),
                source_owner_id=owner_id,
                source_nucleus_id=source_nucleus_id,
                source_obligation_ids=owner_obligations,
                source_fragments=fragments,
                semantic_kind=str(nucleus.kind),
                dimensions=_nucleus_dimensions(nucleus),
                required=True,
            )
        )
    if not 1 <= len(rows) <= _ROOT_MAX:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_ROOT_BOUND_INVALID"
        )
    return tuple(rows)


def _aggregate_dimensions(
    values: Sequence[tuple[str, str, str, str]],
) -> tuple[str, str, str, str]:
    rows = tuple(values)
    if not rows:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_CONSTRUCTION_SOURCE_INVALID"
        )
    return tuple(
        column[0] if len(set(column)) == 1 else "unknown"
        for column in zip(*rows, strict=True)
    )  # type: ignore[return-value]


def _atom_bindings(
    *,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    lexical_atom_specs: Step11Rc0028ExperimentLexicalAtomSpecs,
    owner_registry: Sequence[str],
    constructions: Sequence[Any],
    relations: Sequence[Any],
    links: Sequence[Any],
    unknowns: Sequence[Any],
) -> tuple[Step11Cycle001ProductRecoveryAtomBinding, ...]:
    owner_by_ordinal = {
        int(row.owner_ordinal): str(row.source_owner_id)
        for row in lexical_atom_specs.owner_bindings
    }
    owner_kind_by_id = {
        str(row.source_owner_id): str(row.source_owner_kind)
        for row in lexical_atom_specs.owner_bindings
    }
    nucleus_by_owner = {
        str(row.actual_source_id): str(row.source_id)
        for row in successor_snapshot.base_snapshot.nuclei
    }
    dimensions_by_owner = {
        str(row.actual_source_id): _nucleus_dimensions(row)
        for row in successor_snapshot.base_snapshot.nuclei
    }
    construction_instance_by_id = {
        str(row.construction_instance_id): row
        for row in lexical_atom_specs.construction_instances
    }
    construction_spec_by_slot = {
        str(row.construction_slot_id): row
        for row in lexical_atom_specs.construction_atoms
    }
    semantic_link_spec_by_id = {
        str(row.source_semantic_link_id): row
        for row in lexical_atom_specs.semantic_link_atoms
    }
    unknown_spec_by_id = {
        str(row.source_unknown_id): row
        for row in lexical_atom_specs.explicit_unknown_atoms
    }
    relation_specs_by_id: dict[str, list[Any]] = defaultdict(list)
    for row in lexical_atom_specs.relation_endpoint_atoms:
        relation_specs_by_id[str(row.experiment_relation_id)].append(row)
    result: list[Step11Cycle001ProductRecoveryAtomBinding] = []

    def add(
        *,
        atom_id: str,
        family: str,
        key: str,
        owners: tuple[str, ...],
        direction: str,
        dimensions: tuple[str, str, str, str],
        parent_nucleus_ids: tuple[str, ...] = (),
        source_span_ids: tuple[str, ...] = (),
        evidence_alias_ids: tuple[str, ...] = (),
        marker_span_ids: tuple[str, ...] = (),
        roles: tuple[Step11Cycle001ProductRecoveryConstructionRoleBinding, ...] = (),
    ) -> None:
        if (
            not owners
            or not set(owners) <= set(owner_registry)
            or any(owner not in owner_kind_by_id for owner in owners)
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ATOM_OWNER_INVALID"
            )
        nucleus_owners = tuple(
            owner for owner in owners if owner_kind_by_id[owner] == "nucleus"
        )
        semantic_unit_owners = tuple(
            owner
            for owner in owners
            if owner_kind_by_id[owner] == "semantic_unit"
        )
        if len(nucleus_owners) + len(semantic_unit_owners) != len(owners):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ATOM_OWNER_KIND_INVALID"
            )
        result.append(
            Step11Cycle001ProductRecoveryAtomBinding(
                source_atom_id=atom_id,
                semantic_family=family,
                semantic_key=key,
                source_owner_ids=owners,
                direction=direction,
                dimensions=dimensions,
                source_nucleus_owner_ids=nucleus_owners,
                source_semantic_unit_owner_ids=semantic_unit_owners,
                source_parent_nucleus_ids=parent_nucleus_ids,
                source_span_ids=source_span_ids,
                source_evidence_alias_ids=evidence_alias_ids,
                source_marker_span_ids=marker_span_ids,
                construction_roles=roles,
                source_order=len(result) + 1,
            )
        )

    for atom in constructions:
        instance_id = str(atom.construction_instance_id)
        instance = construction_instance_by_id.get(instance_id)
        if instance is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_CONSTRUCTION_SOURCE_INVALID"
            )
        role_rows: list[Step11Cycle001ProductRecoveryConstructionRoleBinding] = []
        owner_ids: list[str] = []
        for role in atom.role_atoms:
            slot_id = str(role.construction_slot_id)
            role_spec = construction_spec_by_slot.get(slot_id)
            role_owners = tuple(
                owner_by_ordinal[int(value)] for value in role.target_owner_ordinals
            )
            if (
                role_spec is None
                or str(role_spec.construction_instance_id) != instance_id
                or tuple(int(value) for value in role_spec.target_owner_ordinals)
                != tuple(int(value) for value in role.target_owner_ordinals)
                or any(value not in dimensions_by_owner for value in role_owners)
            ):
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_CONSTRUCTION_SOURCE_INVALID"
                )
            role_dimensions = tuple(
                dimensions_by_owner[value] for value in role_owners
            )
            owner_ids.extend(role_owners)
            role_rows.append(
                Step11Cycle001ProductRecoveryConstructionRoleBinding(
                    construction_slot_id=slot_id,
                    parent_nucleus_id=str(role_spec.parent_nucleus_id),
                    source_span_id=str(role_spec.source_span_id),
                    slot_start_index=int(role_spec.slot_start_index),
                    slot_end_index=int(role_spec.slot_end_index),
                    lexical_role_kind=str(role.lexical_role_kind),
                    construction_position=str(role.construction_position),
                    role_position_surface_token=str(
                        role.role_position_surface_token
                    ),
                    source_owner_ids=role_owners,
                    source_owner_dimensions=role_dimensions,
                    participation_ids=tuple(
                        str(value) for value in role.participation_ids
                    ),
                )
            )
        add(
            atom_id=instance_id,
            family="construction",
            key=str(atom.construction_code),
            owners=_ordered_unique(tuple(owner_ids)),
            direction="",
            dimensions=_aggregate_dimensions(
                tuple(
                    dimensions_by_owner[value]
                    for value in _ordered_unique(tuple(owner_ids))
                )
            ),
            parent_nucleus_ids=(str(instance.parent_nucleus_id),),
            source_span_ids=(str(instance.source_span_id),),
            evidence_alias_ids=tuple(
                str(value) for value in instance.evidence_alias_ids
            ),
            roles=tuple(role_rows),
        )
    for atom in relations:
        owners = (
            owner_by_ordinal[int(atom.from_owner_ordinal)],
            owner_by_ordinal[int(atom.to_owner_ordinal)],
        )
        relation_specs = tuple(
            relation_specs_by_id.get(str(atom.experiment_relation_id), ())
        )
        if (
            len(relation_specs) != 2
            or len(
                {
                    (
                        str(row.source_from_nucleus_id),
                        str(row.source_to_nucleus_id),
                    )
                    for row in relation_specs
                }
            )
            != 1
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RELATION_SOURCE_INVALID"
            )
        add(
            atom_id=str(atom.experiment_relation_id),
            family="relation",
            key=str(atom.effective_relation_type),
            owners=owners,
            direction=str(atom.direction),
            dimensions=_step11_rc0031_product_source_dimensions(
                str(atom.experiment_relation_id),
                "relation",
                owners,
                successor_snapshot=successor_snapshot,
                rc0031_nucleus_by_owner=nucleus_by_owner,
            ),
            parent_nucleus_ids=_ordered_unique(
                tuple(
                    value
                    for row in relation_specs
                    for value in (
                        row.source_from_nucleus_id,
                        row.source_to_nucleus_id,
                    )
                )
            ),
            evidence_alias_ids=_ordered_unique(
                tuple(
                    value
                    for row in relation_specs
                    for value in row.evidence_alias_ids
                )
            ),
            marker_span_ids=_ordered_unique(
                tuple(
                    str(row.marker_source_span_id)
                    for row in relation_specs
                    if row.marker_source_span_id is not None
                )
            ),
        )
    for atom in links:
        owners = (
            owner_by_ordinal[int(atom.from_owner_ordinal)],
            owner_by_ordinal[int(atom.to_owner_ordinal)],
        )
        link_spec = semantic_link_spec_by_id.get(
            str(atom.source_semantic_link_id)
        )
        if link_spec is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ATOM_SOURCE_INVALID"
            )
        add(
            atom_id=str(atom.source_semantic_link_id),
            family="semantic_link",
            key=str(atom.relation_type),
            owners=owners,
            direction=str(atom.direction),
            dimensions=_step11_rc0031_product_source_dimensions(
                str(atom.source_semantic_link_id),
                "semantic_link",
                owners,
                successor_snapshot=successor_snapshot,
                rc0031_nucleus_by_owner=nucleus_by_owner,
            ),
            parent_nucleus_ids=(),
            source_span_ids=(str(link_spec.source_span_id),),
        )
    for atom in unknowns:
        owners = tuple(
            owner_by_ordinal[int(value)] for value in atom.affected_owner_ordinals
        )
        unknown_spec = unknown_spec_by_id.get(str(atom.source_unknown_id))
        if unknown_spec is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ATOM_SOURCE_INVALID"
            )
        add(
            atom_id=str(atom.source_unknown_id),
            family="explicit_unknown",
            key=str(atom.dimension),
            owners=owners,
            direction="",
            dimensions=("unknown", "unknown", "unknown", "unknown"),
            parent_nucleus_ids=(),
            source_span_ids=(str(unknown_spec.source_span_id),),
        )
    if len(result) > _ATOM_MAX or len(
        {row.source_atom_id for row in result}
    ) != len(result):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_ATOM_BOUND_INVALID"
        )
    return tuple(result)


def _dimension_prefix(
    dimensions: tuple[str, str, str, str],
    grammar: Mapping[str, Any],
) -> str:
    temporal, modality, polarity, scope = dimensions
    return (
        str(
            grammar["temporal_scope_cues"].get(
                temporal, grammar["temporal_scope_cues"]["unknown"]
            )
        )
        + str(
            grammar["modality_cues"].get(
                modality, grammar["modality_cues"]["unknown"]
            )
        )
        + str(
            grammar["polarity_cues"].get(
                polarity, grammar["polarity_cues"]["unknown"]
            )
        )
        + str(
            grammar["referent_scope_cues"].get(
                scope, grammar["referent_scope_cues"]["unknown"]
            )
        )
    )


def _render_construction(
    binding: Step11Cycle001ProductRecoveryAtomBinding,
    atom: Any,
    referents: Mapping[str, str],
    morphology: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> str:
    role_texts = tuple(
        row.role_position_surface_token
        + "は"
        + str(morphology["target_owner_join"]).join(
            _dimension_prefix(dimensions, grammar) + referents[owner_id]
            for owner_id, dimensions in zip(
                row.source_owner_ids,
                row.source_owner_dimensions,
                strict=True,
            )
        )
        for row in binding.construction_roles
    )
    if not role_texts:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_CONSTRUCTION_ROLE_INVALID"
        )
    return (
        "、".join(role_texts)
        + "という"
        + str(atom.surface_token)
        + str(morphology["construction_standalone_predicate"])
    )


def _render(
    *,
    envelope: Step11Cycle001ProductRecoverySourceEnvelope,
    constructions: Sequence[Any],
    relations: Sequence[Any],
    links: Sequence[Any],
    unknowns: Sequence[Any],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[bytes, tuple[Step11Cycle001ProductRecoveryRealizationUnit, ...]]:
    referents = {
        row.source_owner_id: row.referent_text for row in envelope.owner_bindings
    }
    dimensions_by_owner = {
        row.source_owner_id: row.dimensions for row in envelope.owner_bindings
    }
    dimensioned_referents = {
        owner_id: _dimension_prefix(dimensions_by_owner[owner_id], grammar)
        + referent
        for owner_id, referent in referents.items()
    }
    construction_by_id = {
        str(row.construction_instance_id): row for row in constructions
    }
    relation_by_id = {
        str(row.experiment_relation_id): row for row in relations
    }
    link_by_id = {str(row.source_semantic_link_id): row for row in links}
    unknown_by_id = {str(row.source_unknown_id): row for row in unknowns}
    observation_lines: list[str] = []
    units: list[Step11Cycle001ProductRecoveryRealizationUnit] = []
    for root in envelope.root_bindings:
        fragments = "／".join(
            row.source_fragment_text for row in root.source_fragments
        )
        if not fragments:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
            )
        text = (
            _dimension_prefix(root.dimensions, grammar)
            + "「"
            + fragments
            + "」に表れている"
            + referents[root.source_owner_id]
            + "がここにあります"
        )
        observation_lines.append(text)
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="observation",
                source_unit_id=root.source_root_id,
                source_atom_ids=(),
                source_owner_ids=(root.source_owner_id,),
                source_owner_dimensions=((root.source_owner_id, root.dimensions),),
                source_obligation_ids=root.source_obligation_ids,
                source_fragment_ids=tuple(
                    row.source_fragment_id for row in root.source_fragments
                ),
                dimensions=root.dimensions,
                visible_clause_count=1,
            )
        )
    for binding in envelope.atom_bindings:
        if binding.semantic_family == "construction":
            atom = construction_by_id.get(binding.source_atom_id)
            if atom is None:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_RENDER_SOURCE_MISMATCH"
                )
            clause = _render_construction(
                binding,
                atom,
                referents,
                catalog["clause_morphology"],
                grammar,
            )
        else:
            clause = _step11_rc0031_render_semantic_clause(
                source_atom_id=binding.source_atom_id,
                semantic_family=binding.semantic_family,
                catalog=catalog,
                referent_by_owner=dimensioned_referents,
                owner_ids=binding.source_owner_ids,
                construction_by_id=construction_by_id,
                relation_by_id=relation_by_id,
                link_by_id=link_by_id,
                unknown_by_id=unknown_by_id,
            )
        observation_lines.append(clause)
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="observation",
                source_unit_id=binding.source_atom_id,
                source_atom_ids=(binding.source_atom_id,),
                source_owner_ids=binding.source_owner_ids,
                source_owner_dimensions=tuple(
                    (owner_id, dimensions_by_owner[owner_id])
                    for owner_id in binding.source_owner_ids
                ),
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=binding.dimensions,
                visible_clause_count=1,
            )
        )
    morphology = catalog["clause_morphology"]
    reception_lines: list[str] = []
    for binding in envelope.reception_bindings:
        targets = str(morphology["target_owner_join"]).join(
            referents[value] for value in binding.source_target_owner_ids
        )
        support_ids = _ordered_unique(
            tuple(
                value
                for value in (
                    *binding.source_focus_owner_ids,
                    *binding.visible_support_owner_ids,
                )
                if value not in set(binding.source_target_owner_ids)
                and value in referents
            )
        )
        support = (
            str(morphology["support_owner_join"]).join(
                referents[value] for value in support_ids
            )
            + str(morphology["support_target_link"])
            if support_ids
            else ""
        )
        reception_lines.append(
            support
            + targets
            + str(morphology["reception_object_particle"])
            + str(
                catalog["reception_act_predicate_fragments"][
                    binding.effective_reception_act
                ]
            )
        )
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="reception",
                source_unit_id=binding.source_reception_opportunity_id,
                source_atom_ids=(),
                source_owner_ids=_ordered_unique(
                    (
                        *(
                            value
                            for value in binding.source_focus_owner_ids
                            if value in referents
                        ),
                        *(
                            value
                            for value in binding.source_target_owner_ids
                            if value in referents
                        ),
                        *(
                            value
                            for value in binding.visible_support_owner_ids
                            if value in referents
                        ),
                    )
                ),
                source_owner_dimensions=tuple(
                    (owner_id, dimensions_by_owner[owner_id])
                    for owner_id in _ordered_unique(
                        (
                            *binding.source_focus_owner_ids,
                            *binding.source_target_owner_ids,
                            *binding.visible_support_owner_ids,
                        )
                    )
                    if owner_id in dimensions_by_owner
                ),
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=("unknown", "unknown", "unknown", "unknown"),
                visible_clause_count=1,
            )
        )
    suffix = str(morphology["sentence_suffix"])
    body = (
        str(grammar["observation_header"])
        + "\n".join(value + suffix for value in observation_lines)
        + str(grammar["section_separator"])
        + "\n".join(value + suffix for value in reception_lines)
    )
    return body.encode("utf-8", errors="strict"), tuple(units)


def step11_cycle001_product_recovery_visible_inverse(
    value: Step11Cycle001ProductRecoveryCandidate,
) -> tuple[Step11Cycle001ProductRecoveryVisibleBinding, ...]:
    """Bind every rendered line to one replay-plan unit in exact order."""

    if type(value) is not Step11Cycle001ProductRecoveryCandidate:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_CANDIDATE_TYPE_INVALID"
        )
    _owner, catalog, grammar, _catalog_sha256 = (
        _step11_rc0031_product_surface_authorities()
    )
    try:
        body = value.rendered_surface.utf8_bytes.decode(
            "utf-8", errors="strict"
        )
    except (AttributeError, UnicodeDecodeError) as exc:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_VISIBLE_INVERSE_INVALID"
        ) from exc
    header = str(grammar["observation_header"])
    separator = str(grammar["section_separator"])
    suffix = str(catalog["clause_morphology"]["sentence_suffix"])
    if not body.startswith(header) or body.count(separator) != 1:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_VISIBLE_INVERSE_INVALID"
        )
    observation_body, reception_body = body[len(header) :].split(
        separator, 1
    )

    def lines(section: str) -> tuple[str, ...]:
        if not section:
            return ()
        rows = tuple(section.split("\n"))
        if any(not row or not row.endswith(suffix) for row in rows):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_VISIBLE_INVERSE_INVALID"
            )
        return rows

    observation_lines = lines(observation_body)
    reception_lines = lines(reception_body)
    plan_units = tuple(value.realization_plan.units)
    observation_units = tuple(
        row for row in plan_units if row.section_role == "observation"
    )
    reception_units = tuple(
        row for row in plan_units if row.section_role == "reception"
    )
    if (
        len(observation_lines) != len(observation_units)
        or len(reception_lines) != len(reception_units)
        or len(plan_units) != len(observation_units) + len(reception_units)
        or tuple(row.line_ordinal for row in plan_units)
        != tuple(range(1, len(plan_units) + 1))
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_VISIBLE_INVERSE_INVALID"
        )
    result: list[Step11Cycle001ProductRecoveryVisibleBinding] = []
    fragment_by_id = {
        fragment.source_fragment_id: fragment
        for root in value.source_envelope.root_bindings
        for fragment in root.source_fragments
    }
    for unit, line in (
        *zip(observation_units, observation_lines, strict=True),
        *zip(reception_units, reception_lines, strict=True),
    ):
        result.append(
            Step11Cycle001ProductRecoveryVisibleBinding(
                line_ordinal=int(unit.line_ordinal),
                section_role=str(unit.section_role),
                source_unit_id=str(unit.source_unit_id),
                source_atom_ids=tuple(unit.source_atom_ids),
                source_owner_ids=tuple(unit.source_owner_ids),
                source_owner_dimensions=tuple(
                    unit.source_owner_dimensions
                ),
                source_obligation_ids=tuple(unit.source_obligation_ids),
                source_fragment_ids=tuple(unit.source_fragment_ids),
                source_fragment_text_sha256s=tuple(
                    fragment_by_id[fragment_id].source_fragment_text_sha256
                    for fragment_id in unit.source_fragment_ids
                ),
                visible_line_sha256=hashlib.sha256(
                    line.encode("utf-8")
                ).hexdigest(),
            )
        )
    roots = tuple(
        row.source_root_id for row in value.source_envelope.root_bindings
    )
    atoms = tuple(
        row.source_atom_id for row in value.source_envelope.atom_bindings
    )
    receptions = tuple(
        row.source_reception_opportunity_id
        for row in value.source_envelope.reception_bindings
    )
    root_visible = result[: len(roots)]
    if any(
        binding.source_owner_ids != (root.source_owner_id,)
        or binding.source_obligation_ids != root.source_obligation_ids
        or binding.source_fragment_ids
        != tuple(
            fragment.source_fragment_id
            for fragment in root.source_fragments
        )
        or binding.source_fragment_text_sha256s
        != tuple(
            fragment.source_fragment_text_sha256
            for fragment in root.source_fragments
        )
        for root, binding in zip(
            value.source_envelope.root_bindings,
            root_visible,
            strict=True,
        )
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_VISIBLE_ROOT_COVERAGE_INVALID"
        )
    if (
        tuple(row.source_unit_id for row in result[: len(roots)]) != roots
        or tuple(
            row.source_unit_id
            for row in result[len(roots) : len(roots) + len(atoms)]
        )
        != atoms
        or tuple(row.source_unit_id for row in result[-len(receptions) :])
        != receptions
        or tuple(
            atom_id for row in result for atom_id in row.source_atom_ids
        )
        != atoms
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_VISIBLE_COVERAGE_INVALID"
        )
    return tuple(result)


def _build_step11_cycle001_product_recovery_candidate(
    *,
    plan: Any,
    resolver: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: Any,
    content_plan: Any,
    discourse_plans: Any,
    current_input: Any,
    validate_output: bool,
) -> Step11Cycle001ProductRecoveryCandidate:
    try:
        discourse_rows, witness, current_input_binding = _validated_sources(
            plan=plan,
            resolver=resolver,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plans=discourse_plans,
            current_input=current_input,
        )
        if validate_step11_rc0029_experiment_surface_catalog(
            STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_CATALOG_INVALID"
            )
        rc0028_catalog, _rc0028_catalog_sha256 = _step11_rc0028_catalog()
        (
            owner_registry,
            constructions,
            relations,
            links,
            unknowns,
        ) = _step11_rc0028_forward_atoms(
            successor_snapshot, lexical_atom_specs, rc0028_catalog
        )
        _catalog_owner, catalog, grammar, catalog_sha256 = (
            _step11_rc0031_product_surface_authorities()
        )
        receptions = _reception_bindings(successor_snapshot=successor_snapshot)
        roots = _root_bindings(
            plan=plan,
            resolver=resolver,
            semantic_restatement_witness=witness,
            successor_snapshot=successor_snapshot,
            inventory_result=inventory_result,
        )
        atoms = _atom_bindings(
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            owner_registry=owner_registry,
            constructions=constructions,
            relations=relations,
            links=links,
            unknowns=unknowns,
        )
        available_owner_ids = set(owner_registry)
        resolvable_owner_ids = {
            str(row.actual_source_id)
            for row in successor_snapshot.base_snapshot.nuclei
        }
        essential_owner_ids = {
            *(row.source_owner_id for row in roots),
            *(owner for row in atoms for owner in row.source_owner_ids),
            *(
                owner
                for row in receptions
                for owner in row.source_target_owner_ids
            ),
        }
        if not essential_owner_ids <= available_owner_ids:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_SOURCE_UNRESOLVED"
            )
        active_owner_ids = essential_owner_ids | {
            owner
            for row in receptions
            for owner in (
                *row.source_focus_owner_ids,
                *row.visible_support_owner_ids,
            )
            if owner in available_owner_ids
            and owner in resolvable_owner_ids
        }
        owners = _owner_bindings(
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            active_owner_ids=active_owner_ids,
            role_tokens=_role_tokens(
                lexical_atom_specs=lexical_atom_specs,
                reception_bindings=receptions,
            ),
        )
        if active_owner_ids != {row.source_owner_id for row in owners}:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_COVERAGE_INVALID"
            )
        typed_payload_sha256 = artifact_sha256(
            _typed_payload_material(
                owner_registry=owner_registry,
                constructions=constructions,
                relations=relations,
                links=links,
                unknowns=unknowns,
                receptions=receptions,
            )
        )
        candidate_boundary_sha256 = artifact_sha256(
            _candidate_boundary_material(
                semantic_coverage_authorized=True,
                old_gate_consulted=False,
                old_selector_consulted=False,
                base_acceptance_claimed=False,
                experimental_only=True,
                private_body_full=True,
                shareable=False,
                runtime_connected=False,
            )
        )
        discourse_sha256 = artifact_sha256(
            {
                "ordered_discourse_plan_sha256s": [
                    artifact_sha256(row) for row in discourse_rows
                ],
                "discourse_plan_count": len(discourse_rows),
            }
        )
        provisional_source = Step11Cycle001ProductRecoverySourceEnvelope(
            schema_version=STEP11_CYCLE001_PRODUCT_RECOVERY_SOURCE_SCHEMA,
            candidate_version_id=(
                STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID
            ),
            source_candidate_id="nls3s11rc0035source_0000000000000000",
            source_observation_plan_sha256=(
                successor_snapshot.base_snapshot.source_observation_plan_sha256
            ),
            source_successor_snapshot_sha256=(
                successor_snapshot.experiment_snapshot_sha256
            ),
            source_lexical_atom_specs_sha256=lexical_atom_specs.specs_sha256,
            source_semantic_restatement_witness_sha256=witness.witness_sha256,
            source_inventory_ledger_sha256=artifact_sha256(
                inventory_result.ledger
            ),
            source_content_plan_sha256=artifact_sha256(content_plan),
            source_discourse_plan_sha256=discourse_sha256,
            current_input_binding=current_input_binding,
            source_lexical_catalog_sha256=(
                STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256
            ),
            surface_catalog_sha256=catalog_sha256,
            duplicated_typed_payload_sha256=typed_payload_sha256,
            owner_bindings=owners,
            root_bindings=roots,
            atom_bindings=atoms,
            reception_bindings=receptions,
            source_counts=(
                ("owners", len(owners)),
                ("roots", len(roots)),
                ("constructions", len(constructions)),
                ("relations", len(relations)),
                ("semantic_links", len(links)),
                ("explicit_unknowns", len(unknowns)),
                ("receptions", len(receptions)),
            ),
            old_gate_consulted=False,
            old_selector_consulted=False,
            base_acceptance_claimed=False,
            semantic_coverage_authorized=True,
            semantic_coverage_authority=_SEMANTIC_COVERAGE_AUTHORITY,
            source_envelope_sha256="0" * 64,
        )
        source_sha256 = artifact_sha256(
            _source_envelope_material(provisional_source, include_identity=False)
        )
        source = replace(
            provisional_source,
            source_candidate_id=(
                "nls3s11rc0035source_" + source_sha256[:16]
            ),
            source_envelope_sha256=source_sha256,
        )
        final_bytes, units = _render(
            envelope=source,
            constructions=constructions,
            relations=relations,
            links=links,
            unknowns=unknowns,
            catalog=catalog,
            grammar=grammar,
        )
        observation_count = sum(
            row.section_role == "observation" for row in units
        )
        reception_count = sum(row.section_role == "reception" for row in units)
        provisional_plan = Step11Cycle001ProductRecoveryPlan(
            schema_version=STEP11_CYCLE001_PRODUCT_RECOVERY_PLAN_SCHEMA,
            candidate_version_id=(
                STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID
            ),
            realization_plan_id="nls3s11rc0035plan_0000000000000000",
            ast_id="nls3s11rc0035ast_0000000000000000",
            source_envelope_sha256=source_sha256,
            duplicated_typed_payload_sha256=typed_payload_sha256,
            candidate_boundary_sha256=candidate_boundary_sha256,
            units=units,
            observation_line_count=observation_count,
            reception_line_count=reception_count,
            maximum_visible_clauses_per_line=1,
        )
        plan_sha256 = artifact_sha256(
            _plan_material(provisional_plan, include_identity=False)
        )
        recovery_plan = replace(
            provisional_plan,
            realization_plan_id="nls3s11rc0035plan_" + plan_sha256[:16],
            ast_id=(
                "nls3s11rc0035ast_"
                + artifact_sha256(
                    {
                        "source_envelope_sha256": source_sha256,
                        "plan_sha256": plan_sha256,
                        "duplicated_typed_payload_sha256": (
                            typed_payload_sha256
                        ),
                        "candidate_boundary_sha256": (
                            candidate_boundary_sha256
                        ),
                    }
                )[:16]
            ),
        )
        rendered = Step11Cycle001ProductRecoveryRenderedSurface(
            schema_version=STEP11_CYCLE001_PRODUCT_RECOVERY_RENDERED_SCHEMA,
            source_envelope_sha256=source_sha256,
            source_realization_plan_id=recovery_plan.realization_plan_id,
            utf8_bytes=final_bytes,
            sha256=hashlib.sha256(final_bytes).hexdigest(),
            observation_line_count=observation_count,
            reception_line_count=reception_count,
        )
        candidate_id = _step11_rc0035_cycle001_product_recovery_candidate_identity(
            source_envelope_sha256=source_sha256,
            source_candidate_id=source.source_candidate_id,
            final_sha256=rendered.sha256,
            realization_plan_id=recovery_plan.realization_plan_id,
            ast_id=recovery_plan.ast_id,
        )
        candidate = Step11Cycle001ProductRecoveryCandidate(
            schema_version=STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA,
            candidate_version_id=(
                STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID
            ),
            candidate_id=candidate_id,
            source_envelope=source,
            realization_plan=recovery_plan,
            rendered_surface=rendered,
            owner_registry=tuple(owner_registry),
            construction_atoms=tuple(constructions),
            relation_atoms=tuple(relations),
            semantic_link_atoms=tuple(links),
            explicit_unknown_atoms=tuple(unknowns),
            reception_bindings=receptions,
            semantic_coverage_authorized=True,
            old_gate_consulted=False,
            old_selector_consulted=False,
            base_acceptance_claimed=False,
        )
        if validate_output:
            issues = validate_step11_cycle001_product_recovery_candidate(
                candidate,
                plan=plan,
                resolver=resolver,
                successor_snapshot=successor_snapshot,
                lexical_atom_specs=lexical_atom_specs,
                inventory_result=inventory_result,
                content_plan=content_plan,
                discourse_plans=discourse_plans,
                current_input=current_input,
            )
            if issues:
                raise Step11Cycle001ProductRecoveryError(issues[0])
        return candidate
    except Step11Cycle001ProductRecoveryError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", None)
        if type(code) is str and code.startswith("STEP11_"):
            raise Step11Cycle001ProductRecoveryError(code) from None
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_BUILD_FAILED"
        ) from exc


def build_step11_cycle001_product_recovery_candidate(
    *,
    plan: Any,
    resolver: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: Any,
    content_plan: Any,
    discourse_plans: Any,
    current_input: Any,
) -> Step11Cycle001ProductRecoveryCandidate:
    return _build_step11_cycle001_product_recovery_candidate(
        plan=plan,
        resolver=resolver,
        successor_snapshot=successor_snapshot,
        lexical_atom_specs=lexical_atom_specs,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plans=discourse_plans,
        current_input=current_input,
        validate_output=True,
    )


def _validate_step11_cycle001_product_recovery_candidate_strict(
    value: Any,
    *,
    plan: Any,
    resolver: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: Any,
    content_plan: Any,
    discourse_plans: Any,
    current_input: Any,
) -> tuple[str, ...]:
    if type(value) is not Step11Cycle001ProductRecoveryCandidate:
        return ("STEP11_CYCLE001_RECOVERY_CANDIDATE_TYPE_INVALID",)
    try:
        expected = _build_step11_cycle001_product_recovery_candidate(
            plan=plan,
            resolver=resolver,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plans=discourse_plans,
            current_input=current_input,
            validate_output=False,
        )
    except Exception:
        return ("STEP11_CYCLE001_RECOVERY_REPLAY_FAILED",)
    issues: set[str] = set()
    if value != expected:
        issues.add("STEP11_CYCLE001_RECOVERY_SOURCE_MISMATCH")
    if (
        value.schema_version
        != STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA
        or value.candidate_version_id
        != STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID
        or value.semantic_coverage_authorized is not True
        or value.old_gate_consulted is not False
        or value.old_selector_consulted is not False
        or value.base_acceptance_claimed is not False
        or value.experimental_only is not True
        or value.private_body_full is not True
        or value.shareable is not False
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_CYCLE001_RECOVERY_BOUNDARY_INVALID")
    candidate_boundary_sha256 = artifact_sha256(
        _candidate_boundary_material(
            semantic_coverage_authorized=value.semantic_coverage_authorized,
            old_gate_consulted=value.old_gate_consulted,
            old_selector_consulted=value.old_selector_consulted,
            base_acceptance_claimed=value.base_acceptance_claimed,
            experimental_only=value.experimental_only,
            private_body_full=value.private_body_full,
            shareable=value.shareable,
            runtime_connected=value.runtime_connected,
        )
    )
    typed_payload_sha256 = artifact_sha256(
        _typed_payload_material(
            owner_registry=value.owner_registry,
            constructions=value.construction_atoms,
            relations=value.relation_atoms,
            links=value.semantic_link_atoms,
            unknowns=value.explicit_unknown_atoms,
            receptions=value.reception_bindings,
        )
    )
    source = value.source_envelope
    if (
        source.schema_version
        != STEP11_CYCLE001_PRODUCT_RECOVERY_SOURCE_SCHEMA
        or source.old_gate_consulted is not False
        or source.old_selector_consulted is not False
        or source.base_acceptance_claimed is not False
        or source.semantic_coverage_authorized is not True
        or source.semantic_coverage_authority
        != _SEMANTIC_COVERAGE_AUTHORITY
        or source.semantic_coverage_authorized
        != value.semantic_coverage_authorized
        or source.duplicated_typed_payload_sha256 != typed_payload_sha256
        or source.experimental_only is not True
        or source.private_body_full is not True
        or source.shareable is not False
        or source.runtime_connected is not False
        or source.source_envelope_sha256
        != artifact_sha256(
            _source_envelope_material(source, include_identity=False)
        )
        or source.source_candidate_id
        != "nls3s11rc0035source_" + source.source_envelope_sha256[:16]
    ):
        issues.add("STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_INVALID")
    rendered = value.rendered_surface
    recovery_plan = value.realization_plan
    plan_sha256 = artifact_sha256(
        _plan_material(recovery_plan, include_identity=False)
    )
    expected_plan_id = "nls3s11rc0035plan_" + plan_sha256[:16]
    expected_ast_id = (
        "nls3s11rc0035ast_"
        + artifact_sha256(
            {
                "source_envelope_sha256": source.source_envelope_sha256,
                "plan_sha256": plan_sha256,
                "duplicated_typed_payload_sha256": typed_payload_sha256,
                "candidate_boundary_sha256": candidate_boundary_sha256,
            }
        )[:16]
    )
    if (
        recovery_plan.realization_plan_id != expected_plan_id
        or recovery_plan.duplicated_typed_payload_sha256
        != typed_payload_sha256
        or recovery_plan.candidate_boundary_sha256
        != candidate_boundary_sha256
    ):
        issues.add("STEP11_CYCLE001_RECOVERY_PLAN_IDENTITY_INVALID")
    if recovery_plan.ast_id != expected_ast_id:
        issues.add("STEP11_CYCLE001_RECOVERY_AST_IDENTITY_INVALID")
    if (
        type(rendered.utf8_bytes) is not bytes
        or not rendered.utf8_bytes
        or rendered.sha256
        != hashlib.sha256(rendered.utf8_bytes).hexdigest()
        or rendered.utf8_bytes.decode("utf-8", errors="strict").encode(
            "utf-8", errors="strict"
        )
        != rendered.utf8_bytes
        or rendered.source_envelope_sha256 != source.source_envelope_sha256
        or rendered.source_realization_plan_id != expected_plan_id
    ):
        issues.add("STEP11_CYCLE001_RECOVERY_RENDER_INVALID")
    expected_id = _step11_rc0035_cycle001_product_recovery_candidate_identity(
        source_envelope_sha256=source.source_envelope_sha256,
        source_candidate_id=source.source_candidate_id,
        final_sha256=rendered.sha256,
        realization_plan_id=expected_plan_id,
        ast_id=expected_ast_id,
    )
    if value.candidate_id != expected_id:
        issues.add("STEP11_CYCLE001_RECOVERY_IDENTITY_INVALID")
    try:
        visible = step11_cycle001_product_recovery_visible_inverse(value)
        root_ids = tuple(
            row.source_root_id for row in source.root_bindings
        )
        atom_ids = tuple(
            row.source_atom_id for row in source.atom_bindings
        )
        reception_ids = tuple(
            row.source_reception_opportunity_id
            for row in source.reception_bindings
        )
        if tuple(row.source_unit_id for row in visible) != (
            *root_ids,
            *atom_ids,
            *reception_ids,
        ):
            issues.add("STEP11_CYCLE001_RECOVERY_VISIBLE_COVERAGE_INVALID")
    except Exception:
        issues.add("STEP11_CYCLE001_RECOVERY_VISIBLE_INVERSE_INVALID")
    return tuple(sorted(issues))


def validate_step11_cycle001_product_recovery_candidate(
    value: Any,
    *,
    plan: Any,
    resolver: Any,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    inventory_result: Any,
    content_plan: Any,
    discourse_plans: Any,
    current_input: Any,
) -> tuple[str, ...]:
    """Total fail-closed validator for an untrusted nested candidate."""

    if type(value) is not Step11Cycle001ProductRecoveryCandidate:
        return ("STEP11_CYCLE001_RECOVERY_CANDIDATE_TYPE_INVALID",)
    if type(value.source_envelope) is not Step11Cycle001ProductRecoverySourceEnvelope:
        return ("STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_TYPE_INVALID",)
    if type(value.realization_plan) is not Step11Cycle001ProductRecoveryPlan:
        return ("STEP11_CYCLE001_RECOVERY_PLAN_TYPE_INVALID",)
    if (
        type(value.rendered_surface)
        is not Step11Cycle001ProductRecoveryRenderedSurface
    ):
        return ("STEP11_CYCLE001_RECOVERY_RENDERED_TYPE_INVALID",)
    if (
        type(value.owner_registry) is not tuple
        or type(value.construction_atoms) is not tuple
        or type(value.relation_atoms) is not tuple
        or type(value.semantic_link_atoms) is not tuple
        or type(value.explicit_unknown_atoms) is not tuple
        or type(value.reception_bindings) is not tuple
    ):
        return ("STEP11_CYCLE001_RECOVERY_TYPED_PAYLOAD_TYPE_INVALID",)
    try:
        _typed_payload_material(
            owner_registry=value.owner_registry,
            constructions=value.construction_atoms,
            relations=value.relation_atoms,
            links=value.semantic_link_atoms,
            unknowns=value.explicit_unknown_atoms,
            receptions=value.reception_bindings,
        )
    except Exception:
        return ("STEP11_CYCLE001_RECOVERY_TYPED_PAYLOAD_INVALID",)
    try:
        return _validate_step11_cycle001_product_recovery_candidate_strict(
            value,
            plan=plan,
            resolver=resolver,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            inventory_result=inventory_result,
            content_plan=content_plan,
            discourse_plans=discourse_plans,
            current_input=current_input,
        )
    except Exception:
        return ("STEP11_CYCLE001_RECOVERY_CANDIDATE_MALFORMED",)


__all__ = [
    "STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA",
    "STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID",
    "STEP11_CYCLE001_PRODUCT_RECOVERY_OWNER_SCHEMA",
    "STEP11_CYCLE001_PRODUCT_RECOVERY_PLAN_SCHEMA",
    "STEP11_CYCLE001_PRODUCT_RECOVERY_RENDERED_SCHEMA",
    "STEP11_CYCLE001_PRODUCT_RECOVERY_SOURCE_SCHEMA",
    "Step11Cycle001ProductRecoveryAtomBinding",
    "Step11Cycle001ProductRecoveryCandidate",
    "Step11Cycle001ProductRecoveryConstructionRoleBinding",
    "Step11Cycle001ProductRecoveryCurrentInputBinding",
    "Step11Cycle001ProductRecoveryError",
    "Step11Cycle001ProductRecoveryOwnerBinding",
    "Step11Cycle001ProductRecoveryPlan",
    "Step11Cycle001ProductRecoveryRealizationUnit",
    "Step11Cycle001ProductRecoveryReceptionBinding",
    "Step11Cycle001ProductRecoveryRenderedSurface",
    "Step11Cycle001ProductRecoveryRootBinding",
    "Step11Cycle001ProductRecoverySourceFragmentBinding",
    "Step11Cycle001ProductRecoverySourceEnvelope",
    "Step11Cycle001ProductRecoveryVisibleBinding",
    "build_step11_cycle001_product_recovery_candidate",
    "step11_cycle001_product_recovery_source_envelope_material",
    "step11_cycle001_product_recovery_visible_inverse",
    "validate_step11_cycle001_product_recovery_candidate",
]
