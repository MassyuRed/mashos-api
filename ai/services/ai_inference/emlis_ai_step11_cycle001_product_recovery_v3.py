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
import re
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
    Step11GroundedLexicalizationError,
    Step11GroundedPhraseSpec,
    Step11VisibleSourceAnchorUse,
    Step11Rc0028ExperimentLexicalAtomSpecs,
    build_step11_grounded_phrase_specs,
    render_step11_grounded_phrase,
    select_step11_visible_source_anchor_use,
    validate_step11_rc0028_experiment_lexical_atom_specs,
)
from emlis_ai_step11_natural_surface_v3 import (
    Step11SourceFragment,
    _STEP11_RC0036_CYCLE001_PRODUCT_QUALITY_CANDIDATE_SCHEMA,
    _STEP11_RC0036_CYCLE001_PRODUCT_QUALITY_CANDIDATE_VERSION_ID,
    _clause_from_node,
    _source_fragments,
    _step11_rc0028_catalog,
    _step11_rc0028_forward_atoms,
    _step11_rc0031_product_source_dimensions,
    _step11_rc0031_product_surface_authorities,
    _step11_rc0031_render_semantic_clause,
    _step11_rc0036_cycle001_product_quality_candidate_identity,
    project_step11_current_input,
)
from emlis_ai_step11_rc0029_experiment_surface_catalog_v3 import (
    STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG,
    STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256,
    validate_step11_rc0029_experiment_surface_catalog,
)
from emlis_ai_step11_semantic_overlay_v3 import (
    Step11SemanticOverlay,
    build_step11_semantic_overlay,
)
from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG


STEP11_CYCLE001_PRODUCT_RECOVERY_SOURCE_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_source.rc0036.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_OWNER_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_owner.rc0036.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_PLAN_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_plan.rc0036.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_RENDERED_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.cycle001_product_recovery_rendered.rc0036.v1"
)
STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_VERSION_ID: Final = (
    _STEP11_RC0036_CYCLE001_PRODUCT_QUALITY_CANDIDATE_VERSION_ID
)
STEP11_CYCLE001_PRODUCT_RECOVERY_CANDIDATE_SCHEMA: Final = (
    _STEP11_RC0036_CYCLE001_PRODUCT_QUALITY_CANDIDATE_SCHEMA
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
    "rc0036_source_envelope_visible_inverse_replay"
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
    source_grounding_kind: str
    source_relation_ids: tuple[str, ...]
    authority_basis: str
    source_retention: str
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


@dataclass(frozen=True, slots=True, repr=False)
class _RecoveryProductProjection:
    """Request-local product plan; never serialized as coverage authority."""

    active_discourse_plan: Mapping[str, Any]
    semantic_overlay: Step11SemanticOverlay
    ordered_active_nucleus_ids: tuple[str, ...]
    observation_owner_groups: tuple[tuple[str, ...], ...]
    actual_owner_by_nucleus_id: Mapping[str, str]
    grounded_spec_by_actual_owner: Mapping[str, Step11GroundedPhraseSpec]
    grounded_referent_by_actual_owner: Mapping[str, str]
    first_mention_by_actual_owner: Mapping[str, str]
    visible_anchor_by_actual_owner: Mapping[
        str, Step11VisibleSourceAnchorUse
    ]
    specificity_companion_phrase: str | None
    selected_anchor_owner_id: str | None
    antecedent_evidence_by_actual_owner: Mapping[
        str, "_RecoveryAntecedentEvidence"
    ]
    credit_only_actual_owner_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _RecoveryAntecedentEvidence:
    owner_id: str
    source_nucleus_id: str
    source_evidence_ids: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    phrase_profile_id: str


@dataclass(frozen=True, slots=True)
class _RecoveryObservationAntecedent:
    owner_id: str
    source_unit_id: str
    source_fragment_ids: tuple[str, ...]
    evidence: _RecoveryAntecedentEvidence
    reference_text: str


@dataclass(frozen=True, slots=True)
class _RecoveryTargetSemanticProfile:
    semantic_kind: str
    predicate_kind: str
    source_modality: str
    modality: str
    polarity: str
    source_time_scope: str
    referent_scope: str
    clause_roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _RecoveryTaggedMorpheme:
    text: str
    surface_claim_tags: frozenset[str]


@dataclass(frozen=True, slots=True)
class _RecoveryReceptionMove:
    target_owner_ids: tuple[str, ...]
    target_references: tuple[str, ...]
    support_owner_ids: tuple[str, ...]
    support_references: tuple[str, ...]
    target_semantic_profiles: tuple[_RecoveryTargetSemanticProfile, ...]
    effective_act: str
    action_lifecycle: str
    relation_roles: tuple[tuple[str, str, str], ...]
    unknown_roles: tuple[tuple[str, str], ...]
    self_denial_required: bool


def _relation_surface_mode(
    binding: Step11Cycle001ProductRecoveryAtomBinding,
) -> str:
    """Classify one active relation atom from its frozen source authority."""

    if binding.semantic_family not in {"relation", "semantic_link"}:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RELATION_GRAMMAR_INVALID"
        )
    explicit_user_relation = (
        binding.semantic_family == "relation"
        and binding.source_grounding_kind == "user_stated_relation"
        and binding.source_retention == "required"
    )
    explicit_semantic_link = (
        binding.semantic_family == "semantic_link"
        and binding.source_grounding_kind == "explicit_semantic_link"
        and binding.source_retention == "required"
    )
    if explicit_user_relation or explicit_semantic_link:
        return "junction"
    source_order_only = bool(binding.source_relation_ids) and all(
        relation_id == "whole_input_source_order"
        or relation_id.startswith("source_field_transition:")
        for relation_id in binding.source_relation_ids
    )
    if (
        binding.semantic_key == "uncertain_connection"
        or binding.source_grounding_kind
        == "bounded_structural_inference"
        or source_order_only
    ):
        return "suppressed"
    # No other active relation authority is licensed to add a visible claim.
    return "suppressed"


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


def _active_discourse_plan(
    discourse_plans: Sequence[Mapping[str, Any]],
    inventory_result: SemanticObligationInventoryResult,
) -> Mapping[str, Any]:
    """Choose one body-free topology without consulting ids or request text."""

    obligations = tuple(inventory_result.ledger["obligations"])
    obligation_rank = {
        str(row["obligation_id"]): ordinal
        for ordinal, row in enumerate(obligations)
    }

    def topology_key(plan: Mapping[str, Any]) -> tuple[Any, ...]:
        nodes = tuple(plan.get("nodes", ()))
        groups = tuple(plan.get("sentence_groups", ()))
        edges = tuple(plan.get("edges", ()))
        node_obligation = {
            str(row["node_id"]): str(row["obligation_id"])
            for row in nodes
        }
        if (
            len(node_obligation) != len(nodes)
            or not set(node_obligation.values()) <= set(obligation_rank)
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_DISCOURSE_INVALID"
            )
        group_topology = tuple(
            (
                0 if str(group["section_role"]) == "observation" else 1,
                tuple(
                    obligation_rank[node_obligation[str(node_id)]]
                    for node_id in group["node_ids"]
                ),
            )
            for group in groups
        )
        observation_widths = tuple(
            len(group["node_ids"])
            for group in groups
            if str(group["section_role"]) == "observation"
        )
        reception_widths = tuple(
            len(group["node_ids"])
            for group in groups
            if str(group["section_role"]) == "reception"
        )
        edge_topology = tuple(
            sorted(
                (
                    str(edge["type"]),
                    obligation_rank[
                        node_obligation[str(edge["from"])]
                    ],
                    obligation_rank[
                        node_obligation[str(edge["to"])]
                    ],
                )
                for edge in edges
            )
        )
        return (
            max(observation_widths, default=0),
            max(reception_widths, default=0),
            -len(observation_widths),
            -len(reception_widths),
            group_topology,
            edge_topology,
        )

    return min(tuple(discourse_plans), key=topology_key)


def _grounded_visible_features(
    overlay: Step11SemanticOverlay,
) -> dict[str, dict[str, str]]:
    """Project only the two additional fields accepted by official authority."""

    strength_by_anchor = {
        row.label_anchor_id: row.strength for row in overlay.label_anchors
    }
    allowed_lifecycles = frozenset(
        STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["lifecycle_authority_policy"]["action_projection"]
    )
    result: dict[str, dict[str, str]] = {}
    for binding in overlay.nucleus_anchor_bindings:
        strengths = {
            strength_by_anchor[anchor_id]
            for anchor_id in binding.source_label_anchor_ids
            if anchor_id in strength_by_anchor
            and strength_by_anchor[anchor_id] is not None
        }
        if len(strengths) > 1:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_LABEL_STRENGTH_AMBIGUOUS"
            )
        if strengths:
            result.setdefault(binding.nucleus_id, {})[
                "label_strength"
            ] = next(iter(strengths))  # type: ignore[assignment]
        if binding.realization_status in allowed_lifecycles:
            result.setdefault(binding.nucleus_id, {})[
                "realization_lifecycle"
            ] = binding.realization_status
    return result


def _build_product_projection(
    *,
    discourse_plans: Sequence[Mapping[str, Any]],
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> _RecoveryProductProjection:
    """Build active grounded phrases and the sole visible specificity anchor."""

    active_plan = _active_discourse_plan(discourse_plans, inventory_result)
    normalized_overlay_input = normalize_emlis_current_input(current_input)
    overlay_input = {
        "thought_text": normalized_overlay_input["thought_text"],
        "action_text": normalized_overlay_input["action_text"],
        "emotions": [
            dict(row) for row in normalized_overlay_input["emotion_details"]
        ],
        "categories": list(normalized_overlay_input["categories"]),
    }
    obligations = tuple(inventory_result.ledger["obligations"])
    obligation_by_id = {
        str(row["obligation_id"]): row for row in obligations
    }
    node_by_id = {
        str(row["node_id"]): row for row in active_plan["nodes"]
    }
    # Rebuild every active clause so the product path remains owned by the
    # validated Content/Discourse plan rather than by a renderer-local list.
    active_clause_groups = tuple(
        tuple(
            _clause_from_node(
                node_by_id[str(node_id)],
                by_id=obligation_by_id,
                inventory_result=inventory_result,
            )
            for node_id in group["node_ids"]
        )
        for group in active_plan["sentence_groups"]
    )
    active_clauses = tuple(
        clause for group in active_clause_groups for clause in group
    )
    overlay = build_step11_semantic_overlay(
        overlay_input,
        inventory_result=inventory_result,
        content_plan=content_plan,
        discourse_plan=active_plan,
    )
    snapshot = inventory_result.source_snapshot
    nucleus_by_source = {
        str(row.source_id): row for row in snapshot.nuclei
    }
    source_by_actual = {
        str(row.actual_source_id): str(row.source_id)
        for row in snapshot.nuclei
    }

    def canonical_nucleus_id(value: Any) -> str:
        key = str(value)
        return key if key in nucleus_by_source else source_by_actual.get(key, key)

    source_order = {
        str(row.source_id): ordinal
        for ordinal, row in enumerate(snapshot.nuclei)
    }
    discourse_nucleus_ids = tuple(
        canonical_nucleus_id(nucleus_id)
        for clause in active_clauses
        for nucleus_id in clause.source_nucleus_ids
    )
    # A discourse plan may legitimately omit an optional clause, but Product
    # Observation must not thereby lose a source-explicit semantic unit.  Keep
    # every text-owned nucleus in source order; labels remain downstream-only
    # companions unless selected by the active typed authorities below.
    source_text_nucleus_ids = tuple(
        str(row.source_id)
        for row in snapshot.nuclei
        if str(row.allowed_claim_scope)
        in {"explicit_current_input", "source_bounded_relation"}
    )
    authority_nucleus_ids = (
        *overlay.planning_frontier.active_nucleus_ids,
        *(
            nucleus_id
            for relation in overlay.relations
            for nucleus_id in (
                relation.from_nucleus_id,
                relation.to_nucleus_id,
            )
        ),
        *(
            nucleus_id
            for unknown in overlay.unknowns
            for nucleus_id in (
                *unknown.target_nucleus_ids,
                *unknown.context_nucleus_ids,
            )
        ),
        *(
            nucleus_id
            for binding in overlay.reception_antecedent_bindings
            for nucleus_id in (
                *binding.antecedent_nucleus_ids,
                *binding.supporting_nucleus_ids,
                *binding.source_target_nucleus_ids,
            )
        ),
    )
    ordered_nucleus_ids = _ordered_unique(
        (
            *sorted(
                source_text_nucleus_ids,
                key=lambda value: source_order.get(value, len(source_order)),
            ),
            *discourse_nucleus_ids,
            *sorted(
                (
                    canonical_nucleus_id(value)
                    for value in authority_nucleus_ids
                ),
                key=lambda value: source_order.get(value, len(source_order)),
            ),
        )
    )
    if (
        not ordered_nucleus_ids
        or any(value not in nucleus_by_source for value in ordered_nucleus_ids)
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_ACTIVE_OWNER_UNRESOLVED"
        )
    semantic_authority_nucleus_ids = {
        canonical_nucleus_id(value)
        for value in (*discourse_nucleus_ids, *authority_nucleus_ids)
    }
    credit_only_source_ids = tuple(
        nucleus_id
        for nucleus_id in ordered_nucleus_ids
        if nucleus_by_source[nucleus_id].required is False
        and (
            str(nucleus_by_source[nucleus_id].allowed_claim_scope)
            == "selected_label_only"
            or (
                str(nucleus_by_source[nucleus_id].allowed_claim_scope)
                == "source_bounded_relation"
                and nucleus_id not in semantic_authority_nucleus_ids
            )
        )
    )
    participating_ids = set(
        overlay.planning_frontier.participating_obligation_ids
    )

    def owner_obligations(nucleus_id: str) -> tuple[str, ...]:
        selected = tuple(
            str(row["obligation_id"])
            for row in obligations
            if str(row["obligation_id"]) in participating_ids
            and nucleus_id
            in {canonical_nucleus_id(value) for value in row["nucleus_ids"]}
        )
        if selected:
            return selected
        fallback = tuple(
            str(row["obligation_id"])
            for row in obligations
            if nucleus_id
            in {canonical_nucleus_id(value) for value in row["nucleus_ids"]}
        )
        if not fallback:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_GROUNDED_OWNER_UNRESOLVED"
            )
        return fallback

    additional_features = _grounded_visible_features(overlay)
    specs_by_source: dict[str, Step11GroundedPhraseSpec] = {}
    for nucleus_id in ordered_nucleus_ids:
        try:
            specs = build_step11_grounded_phrase_specs(
                snapshot,
                (),
                additional_owner_obligation_ids={
                    nucleus_id: owner_obligations(nucleus_id)
                },
                additional_visible_feature_values=(
                    {nucleus_id: additional_features[nucleus_id]}
                    if nucleus_id in additional_features
                    else None
                ),
            )
        except Step11GroundedLexicalizationError as exc:
            raise Step11Cycle001ProductRecoveryError(exc.code) from None
        if len(specs) != 1 or specs[0].owner_nucleus_ids != (nucleus_id,):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_GROUNDED_OWNER_UNRESOLVED"
            )
        specs_by_source[nucleus_id] = specs[0]

    try:
        source_fragments = _source_fragments(overlay)
    except Exception as exc:
        code = getattr(exc, "code", None)
        raise Step11Cycle001ProductRecoveryError(
            code
            if type(code) is str
            else "STEP11_CYCLE001_RECOVERY_SOURCE_FRAGMENT_INVALID"
        ) from None
    # The one candidate-wide anchor belongs to the exact Reception target
    # whenever that target has an official safe segment.  Selecting over the
    # complete active candidate prevents renderer-local fragment preference;
    # ambiguous/unavailable candidates fall back to the label companion or a
    # typed target head downstream.
    reception_target_nucleus_ids = _ordered_unique(
        tuple(
            canonical_nucleus_id(nucleus_id)
            for binding in overlay.reception_antecedent_bindings
            for nucleus_id in (
                binding.antecedent_nucleus_ids
                or binding.source_target_nucleus_ids
            )
        )
    )
    preferred_anchor_nucleus_ids = reception_target_nucleus_ids
    candidate_fragments = tuple(
        row
        for row in source_fragments
        if row.fragment_role == "nucleus"
        and any(
            nucleus_id in row.source_nucleus_ids
            for nucleus_id in reception_target_nucleus_ids
        )
    )
    selected_anchor_by_source: dict[str, Step11VisibleSourceAnchorUse] = {}
    try:
        selected_anchor = select_step11_visible_source_anchor_use(
            tuple(
                specs_by_source[value]
                for value in reception_target_nucleus_ids
            ),
            candidate_fragments,
            preferred_owner_nucleus_ids=preferred_anchor_nucleus_ids,
            require_input_specific_binding=True,
        )
    except Step11GroundedLexicalizationError as exc:
        if exc.code not in {
            "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED",
            "STEP11_GROUNDED_PHRASE_AMBIGUOUS",
        }:
            raise Step11Cycle001ProductRecoveryError(exc.code) from None
        selected_anchor = None
    normalized_slot_text = {
        "thought": str(normalized_overlay_input["thought_text"]),
        "memo": str(normalized_overlay_input["thought_text"]),
        "action": str(normalized_overlay_input["action_text"]),
        "memo_action": str(normalized_overlay_input["action_text"]),
    }
    selected_slot_text = (
        normalized_slot_text.get(selected_anchor.source_slot)
        if selected_anchor is not None
        else None
    )
    selected_anchor_is_full_slot = bool(
        selected_anchor is not None
        and selected_slot_text is not None
        and selected_anchor.source_start == 0
        and selected_anchor.source_end == len(selected_slot_text)
        and selected_anchor.scalar_count == len(selected_slot_text)
    )
    if (
        selected_anchor is not None
        and not selected_anchor_is_full_slot
        and selected_anchor.owner_nucleus_id
        in set(reception_target_nucleus_ids)
    ):
        selected_anchor_by_source[
            selected_anchor.owner_nucleus_id
        ] = selected_anchor

    companion_phrase: str | None = None
    if not selected_anchor_by_source:
        evidence_alias_by_actual = {
            str(row.actual_source_id): str(row.alias_source_id)
            for row in snapshot.source_id_alias_bindings
            if str(row.source_kind) == "evidence"
        }
        label_candidates = sorted(
            overlay.label_anchors,
            key=lambda row: (
                0 if row.source_field == "category" else 1,
                row.source_ordinal,
            ),
        )
        for label_anchor in label_candidates:
            evidence_alias = evidence_alias_by_actual.get(
                label_anchor.evidence_span_id
            )
            matches = tuple(
                row
                for row in snapshot.nuclei
                if evidence_alias is not None
                and evidence_alias in row.evidence_ids
                and label_anchor.source_field in row.source_fields
            )
            if len(matches) != 1:
                continue
            label_nucleus = matches[0]
            label_nucleus_id = str(label_nucleus.source_id)
            label_features = (
                {
                    label_nucleus_id: {
                        "label_strength": str(label_anchor.strength)
                    }
                }
                if label_anchor.strength is not None
                else None
            )
            try:
                label_specs = build_step11_grounded_phrase_specs(
                    snapshot,
                    (),
                    additional_owner_obligation_ids={
                        label_nucleus_id: owner_obligations(label_nucleus_id)
                    },
                    additional_visible_feature_values=label_features,
                )
                if len(label_specs) != 1:
                    continue
                label_fragment = Step11SourceFragment(
                    source_slot=label_anchor.source_slot,
                    source_field=label_anchor.source_field,
                    source_ordinal=label_anchor.source_ordinal,
                    fragment_role="label",
                    text=label_anchor.label,
                    source_start=0,
                    source_end=len(label_anchor.label),
                    source_anchor_id=label_anchor.label_anchor_id,
                    source_nucleus_ids=(label_nucleus_id,),
                    source_role=label_anchor.source_slot,
                    modality="reported_content",
                    temporal_scope="current",
                    realization_status="reported_content",
                    label_strength=label_anchor.strength,
                    evidence_grade=label_anchor.evidence_grade,
                )
                label_anchor_use = select_step11_visible_source_anchor_use(
                    label_specs,
                    (label_fragment,),
                    preferred_owner_nucleus_ids=(label_nucleus_id,),
                    require_input_specific_binding=True,
                )
                companion_phrase = render_step11_grounded_phrase(
                    label_specs[0], label_anchor_use
                )
            except Step11GroundedLexicalizationError as exc:
                if exc.code == "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED":
                    continue
                raise Step11Cycle001ProductRecoveryError(exc.code) from None
            break
        if companion_phrase is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED"
            )

    actual_by_source = {
        str(row.source_id): str(row.actual_source_id)
        for row in snapshot.nuclei
    }
    spec_by_actual = {
        actual_by_source[source_id]: spec
        for source_id, spec in specs_by_source.items()
    }
    referent_by_actual = {
        actual_by_source[source_id]: render_step11_grounded_phrase(spec)
        for source_id, spec in specs_by_source.items()
    }
    first_mention_by_actual = dict(referent_by_actual)
    anchor_by_actual: dict[str, Step11VisibleSourceAnchorUse] = {}
    for source_id, selected_anchor in selected_anchor_by_source.items():
        actual_owner_id = actual_by_source[source_id]
        anchor_by_actual[actual_owner_id] = selected_anchor
        first_mention_by_actual[actual_owner_id] = (
            render_step11_grounded_phrase(
                specs_by_source[source_id], selected_anchor
            )
        )
    active_actual_owner_ids = tuple(
        actual_by_source[source_id] for source_id in ordered_nucleus_ids
    )
    antecedent_evidence_by_actual = {
        actual_by_source[source_id]: _RecoveryAntecedentEvidence(
            owner_id=actual_by_source[source_id],
            source_nucleus_id=source_id,
            source_evidence_ids=tuple(
                str(value) for value in nucleus_by_source[source_id].evidence_ids
            ),
            source_anchor_ids=tuple(
                str(value)
                for value in nucleus_by_source[source_id].source_anchor_ids
            ),
            phrase_profile_id=specs_by_source[source_id].phrase_profile_id,
        )
        for source_id in ordered_nucleus_ids
    }
    # Preserve the active Discourse sentence-group topology as the primary
    # Observation order.  A source-explicit owner omitted only because of the
    # Content budget remains a standalone source leaf; it is never attached by
    # textual adjacency.  Labels are rendered separately as companions.
    grouped_source_ids: list[tuple[str, ...]] = []
    grouped_seen: set[str] = set()
    ordered_source_id_set = set(ordered_nucleus_ids)
    for discourse_group, clause_group in zip(
        active_plan["sentence_groups"],
        active_clause_groups,
        strict=True,
    ):
        if str(discourse_group["section_role"]) != "observation":
            continue
        source_ids = tuple(
            nucleus_id
            for nucleus_id in _ordered_unique(
                tuple(
                    canonical_nucleus_id(source_id)
                    for clause in clause_group
                    for source_id in clause.source_nucleus_ids
                )
            )
            if nucleus_id in ordered_source_id_set
            and nucleus_id not in grouped_seen
        )
        if source_ids:
            grouped_source_ids.append(source_ids)
            grouped_seen.update(source_ids)
    grouped_source_ids.extend(
        (source_id,)
        for source_id in ordered_nucleus_ids
        if source_id not in grouped_seen
    )
    observation_owner_groups = tuple(
        tuple(actual_by_source[source_id] for source_id in group)
        for group in grouped_source_ids
    )
    return _RecoveryProductProjection(
        active_discourse_plan=active_plan,
        semantic_overlay=overlay,
        ordered_active_nucleus_ids=ordered_nucleus_ids,
        observation_owner_groups=observation_owner_groups,
        actual_owner_by_nucleus_id=actual_by_source,
        grounded_spec_by_actual_owner=spec_by_actual,
        grounded_referent_by_actual_owner=referent_by_actual,
        first_mention_by_actual_owner=first_mention_by_actual,
        visible_anchor_by_actual_owner=anchor_by_actual,
        specificity_companion_phrase=companion_phrase,
        selected_anchor_owner_id=(
            actual_by_source[next(iter(selected_anchor_by_source))]
            if selected_anchor_by_source
            else None
        ),
        antecedent_evidence_by_actual_owner=antecedent_evidence_by_actual,
        credit_only_actual_owner_ids=tuple(
            actual_by_source[source_id]
            for source_id in credit_only_source_ids
        ),
    )


def _reception_bindings(
    *,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    product_projection: _RecoveryProductProjection,
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

    opportunity_by_id = {
        identity: row
        for row in snapshot.reception_opportunities
        for identity in (str(row.source_id), str(row.actual_source_id))
    }
    overlay_bindings = tuple(
        product_projection.semantic_overlay.reception_antecedent_bindings
    )
    if not 1 <= len(overlay_bindings) <= _RECEPTION_MAX:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RECEPTION_BOUND_INVALID"
        )
    rows: list[Step11Cycle001ProductRecoveryReceptionBinding] = []
    for ordinal, overlay_binding in enumerate(overlay_bindings, start=1):
        opportunity_matches = tuple(
            dict.fromkeys(
                opportunity_by_id[value]
                for value in overlay_binding.source_reception_opportunity_ids
                if value in opportunity_by_id
            )
        )
        if len(opportunity_matches) != 1:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_INVALID"
            )
        opportunity = opportunity_matches[0]
        antecedents = (
            overlay_binding.antecedent_nucleus_ids
            or overlay_binding.source_target_nucleus_ids
        )
        targets = _ordered_unique(
            tuple(actual(value) for value in antecedents)
        )
        supports = _ordered_unique(
            tuple(
                actual(value)
                for value in overlay_binding.supporting_nucleus_ids
            )
        )
        focus_owner_ids = _ordered_unique((*targets, *supports))
        if (
            not targets
            or not focus_owner_ids
            or any(value not in nucleus_by_actual for value in targets)
            or any(value not in nucleus_by_actual for value in supports)
            or any(value not in nucleus_by_actual for value in focus_owner_ids)
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_OWNER_INVALID"
            )
        inventory_act = str(opportunity.reception_act)
        if (
            inventory_act not in _ALLOWED_RECEPTION_ACTS
            or inventory_act not in overlay_binding.allowed_response_acts
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        concrete_action = overlay_binding.action_lifecycle in {
            "reported_completed",
            "reported_ongoing",
        }
        if inventory_act == "honor_concrete_action" and not concrete_action:
            effective = "do_not_dismiss"
            basis = "nonactual_action_nonpromotion"
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
                source_focus_owner_ids=focus_owner_ids,
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
    grounded_referent_by_owner: Mapping[str, str],
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
    prepared: list[tuple[Any, Any, str, tuple[str, ...]]] = []
    for owner in owner_rows:
        nucleus = nucleus_by_actual.get(str(owner.source_owner_id))
        if nucleus is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_SOURCE_UNRESOLVED"
            )
        referent = grounded_referent_by_owner.get(str(owner.source_owner_id))
        if type(referent) is not str or not referent:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_GROUNDED_OWNER_UNRESOLVED"
            )
        prepared.append(
            (
                owner,
                nucleus,
                referent,
                role_tokens.get(str(owner.source_owner_id), ()),
            )
        )

    result: list[Step11Cycle001ProductRecoveryOwnerBinding] = []
    for owner, nucleus, referent, tokens in prepared:
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
                referent_basis="grounded_semantic_feature_phrase",
            )
        )
    return tuple(result)


def _root_bindings(
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    semantic_restatement_witness: Any,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    inventory_result: SemanticObligationInventoryResult,
    active_owner_ids: set[str],
    credit_only_owner_ids: set[str],
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
    semantic_units_by_parent: dict[str, tuple[Any, ...]] = {}
    for semantic_unit in semantic_restatement_witness.semantic_units:
        parent_id = str(semantic_unit.parent_nucleus_id)
        semantic_units_by_parent[parent_id] = (
            *semantic_units_by_parent.get(parent_id, ()),
            semantic_unit,
        )
    snapshot_nucleus_by_actual = {
        str(row.actual_source_id): row for row in snapshot.nuclei
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
                "nls3s11rc0036fragment_" + artifact_sha256(material)[:16]
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
        owner_id = str(nucleus.actual_source_id)
        if owner_id not in active_owner_ids:
            continue
        source_nucleus_id = str(nucleus.source_id)
        aliases = {source_nucleus_id, owner_id}
        owner_obligations = tuple(
            str(row["obligation_id"])
            for row in obligations
            if type(row) is dict
            and row.get("required") is True
            and aliases & {str(value) for value in row.get("nucleus_ids", ())}
        )
        if nucleus.required is True and not owner_obligations:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_OBLIGATION_INVALID"
            )
        semantic_unit = semantic_unit_by_id.get(owner_id)
        if semantic_unit is not None:
            parent_id = str(semantic_unit.parent_nucleus_id)
            parent = grounded_nucleus_by_id.get(parent_id)
            required_siblings = tuple(
                row
                for row in semantic_units_by_parent.get(parent_id, ())
                if row.required is True
            )
            if (
                semantic_unit.required is not True
                or parent is None
                or str(semantic_unit.source_span_id)
                not in set(parent.source_span_ids)
                or not required_siblings
                or any(
                    str(row.unit_id) not in active_owner_ids
                    for row in required_siblings
                )
            ):
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_REQUIRED_SEMANTIC_UNIT_UNRESOLVED"
                )
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
            claim_scope = str(nucleus.allowed_claim_scope)
            span_ids = _ordered_unique(tuple(grounded_nucleus.source_span_ids))
            if claim_scope in {
                "explicit_current_input",
                "source_bounded_relation",
            }:
                if semantic_units_by_parent.get(owner_id) or len(span_ids) != 1:
                    raise Step11Cycle001ProductRecoveryError(
                        "STEP11_CYCLE001_RECOVERY_REQUIRED_SEMANTIC_UNIT_UNRESOLVED"
                    )
                basis = (
                    "source_bounded_relation_credit_only_exact_range"
                    if claim_scope == "source_bounded_relation"
                    and owner_id in credit_only_owner_ids
                    else "grounded_single_semantic_unit_exact_range"
                )
            elif claim_scope == "selected_label_only":
                if not span_ids:
                    raise Step11Cycle001ProductRecoveryError(
                        "STEP11_CYCLE001_RECOVERY_ROOT_SOURCE_UNRESOLVED"
                    )
                basis = (
                    "selected_label_credit_only_exact_range"
                    if owner_id in credit_only_owner_ids
                    else "selected_label_companion_exact_range"
                )
            else:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_REQUIRED_SEMANTIC_UNIT_UNRESOLVED"
                )
            fragments = tuple(
                fragment_binding(
                    owner_id=owner_id,
                    nucleus_id=source_nucleus_id,
                    span_id=span_id,
                    relative_start=0,
                    relative_end=len(str(resolver.resolve(span_id).raw_text)),
                    basis=basis,
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
            "required": bool(nucleus.required),
        }
        rows.append(
            Step11Cycle001ProductRecoveryRootBinding(
                source_root_id=(
                    "nls3s11rc0036root_" + artifact_sha256(material)[:16]
                ),
                source_owner_id=owner_id,
                source_nucleus_id=source_nucleus_id,
                source_obligation_ids=owner_obligations,
                source_fragments=fragments,
                semantic_kind=str(nucleus.kind),
                dimensions=_nucleus_dimensions(nucleus),
                required=bool(nucleus.required),
            )
        )
    if not 1 <= len(rows) <= _ROOT_MAX:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_ROOT_BOUND_INVALID"
        )
    required_unit_ids = {
        str(row.unit_id)
        for row in semantic_restatement_witness.semantic_units
        if row.required is True
    }
    active_semantic_unit_ids = {
        owner_id
        for owner_id in active_owner_ids
        if owner_id in semantic_unit_by_id
    }
    if required_unit_ids != active_semantic_unit_ids or any(
        owner_id not in snapshot_nucleus_by_actual
        for owner_id in required_unit_ids
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_REQUIRED_SEMANTIC_UNIT_UNRESOLVED"
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
    relation_authority_by_id = {
        str(row.experiment_relation_id): row
        for row in successor_snapshot.lexical_role_witness.relation_authorities
    }
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
        source_grounding_kind: str = "",
        source_relation_ids: tuple[str, ...] = (),
        authority_basis: str = "",
        source_retention: str = "",
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
                source_grounding_kind=source_grounding_kind,
                source_relation_ids=source_relation_ids,
                authority_basis=authority_basis,
                source_retention=source_retention,
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
        authority = relation_authority_by_id.get(str(atom.experiment_relation_id))
        if (
            authority is None
            or str(authority.effective_relation_type)
            != str(atom.effective_relation_type)
            or str(authority.direction) != str(atom.direction)
            or len(relation_specs) != 2
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
            source_grounding_kind=str(authority.source_grounding_kind),
            source_relation_ids=tuple(
                str(value) for value in authority.source_relation_ids
            ),
            authority_basis=str(authority.authority_basis),
            source_retention=str(authority.source_retention),
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
            source_grounding_kind="explicit_semantic_link",
            source_relation_ids=(str(atom.source_semantic_link_id),),
            authority_basis="semantic_link_binding",
            source_retention="required" if bool(atom.required) else "optional",
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


def _active_atom_bindings(
    atoms: Sequence[Step11Cycle001ProductRecoveryAtomBinding],
    *,
    product_projection: _RecoveryProductProjection,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
) -> tuple[Step11Cycle001ProductRecoveryAtomBinding, ...]:
    """Keep only atoms owned by the active overlay, exactly once."""

    overlay = product_projection.semantic_overlay
    active_owner_ids = {
        product_projection.actual_owner_by_nucleus_id[value]
        for value in product_projection.ordered_active_nucleus_ids
    }
    alias_peers: dict[str, set[str]] = defaultdict(set)
    for binding in successor_snapshot.base_snapshot.source_id_alias_bindings:
        if str(binding.source_kind) not in {"relation", "unknown_boundary"}:
            continue
        actual = str(binding.actual_source_id)
        alias = str(binding.alias_source_id)
        alias_peers[actual].update((actual, alias))
        alias_peers[alias].update((actual, alias))

    def identities(values: Sequence[Any]) -> set[str]:
        result: set[str] = set()
        for value in values:
            key = str(value)
            result.add(key)
            result.update(alias_peers.get(key, ()))
        return result

    selected_ids: set[str] = set()
    selected: list[Step11Cycle001ProductRecoveryAtomBinding] = []
    for atom in atoms:
        if (
            atom.semantic_family == "construction"
            and set(atom.source_owner_ids) <= active_owner_ids
        ):
            selected.append(atom)
            selected_ids.add(atom.source_atom_id)

    for relation in overlay.relations:
        if not relation.required and not relation.explicit:
            # A selected uncertain topology edge is useful to the private
            # discourse plan, but it is not itself product-language
            # authority.  The source clauses already preserve both endpoints;
            # do not manufacture an extra visible co-presence claim.
            continue
        from_owner = product_projection.actual_owner_by_nucleus_id[
            relation.from_nucleus_id
        ]
        to_owner = product_projection.actual_owner_by_nucleus_id[
            relation.to_nucleus_id
        ]
        matches = tuple(
            atom
            for atom in atoms
            if atom.semantic_family in {"relation", "semantic_link"}
            and atom.source_atom_id not in selected_ids
            and tuple(atom.source_owner_ids[:2]) == (from_owner, to_owner)
        )
        if len(matches) != 1:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_RELATION_UNRESOLVED"
            )
        selected.append(matches[0])
        selected_ids.add(matches[0].source_atom_id)

    for unknown in overlay.unknowns:
        unknown_ids = identities(unknown.source_unknown_ids)
        owner_ids = {
            product_projection.actual_owner_by_nucleus_id[value]
            for value in (
                *unknown.target_nucleus_ids,
                *unknown.context_nucleus_ids,
            )
        }
        matches = tuple(
            atom
            for atom in atoms
            if atom.semantic_family == "explicit_unknown"
            and atom.source_atom_id not in selected_ids
            and identities((atom.source_atom_id,)) & unknown_ids
            and bool(set(atom.source_owner_ids) & owner_ids)
        )
        if not matches:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_UNKNOWN_UNRESOLVED"
            )
        selected.extend(matches)
        selected_ids.update(row.source_atom_id for row in matches)
    return tuple(sorted(selected, key=lambda row: row.source_order))


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


def _bounded_source_anchor(value: str, *, max_chars: int) -> str:
    """Keep one grammatical, contiguous source suffix within a visual budget."""

    candidate = re.sub(r"\s+", " ", value).strip(" \u3000、,。．.!?！？")
    if len(candidate) <= max_chars:
        return candidate
    safe_boundary = (
        r"[、,.!?！？？をへ]|"
        r"(?<=[㐀-鿿])の(?=[㐀-鿿])|"
        r"(?<=[㐀-鿿])と(?=[㐀-鿿])"
    )
    suffixes = tuple(
        suffix
        for match in re.finditer(safe_boundary, candidate)
        if 2
        <= len(
            suffix := candidate[match.end() :].strip(" \u3000、,。．.!?！？")
        )
        <= max_chars
    )
    return max(suffixes, key=len, default=candidate)


def _root_quote(
    root: Step11Cycle001ProductRecoveryRootBinding,
    *,
    max_chars: int = 4096,
) -> str:
    """Return the complete source phrase once, without quotation scaffolding."""

    values = _ordered_unique(
        tuple(
            re.sub(r"\s+", " ", row.source_fragment_text).strip(
                " \u3000、,。．.!?！？"
            )
            for row in root.source_fragments
        )
    )
    if not values:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
        )
    if any(not value or len(value) > max_chars for value in values):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
        )
    return "、".join(values)


def _root_clause(
    root: Step11Cycle001ProductRecoveryRootBinding,
) -> str:
    # A finite source clause is already the most faithful, least explanatory
    # observation.  It is introduced once here and never replayed in Reception.
    return _root_quote(root)


def _neutral_pair_clause(
    left: Step11Cycle001ProductRecoveryRootBinding,
    right: Step11Cycle001ProductRecoveryRootBinding,
) -> str:
    left_quote = _root_quote(left)
    right_quote = _root_quote(right)
    if left.semantic_kind == "action" or right.semantic_kind == "action":
        action = left if left.semantic_kind == "action" else right
        context = right if action is left else left
        action_quote = left_quote if action is left else right_quote
        context_quote = right_quote if action is left else left_quote
        if context.semantic_kind in {"reaction", "state"}:
            return (
                context_quote
                + "という今の感覚と、"
                + action_quote
                + "という行動の両方が記されています"
            )
        if context.semantic_kind in {"wish", "value"}:
            return (
                context_quote
                + "という思いと、"
                + action_quote
                + "という行動が並んでいます"
            )
        if context.semantic_kind in {"constraint", "self_evaluation"}:
            return (
                context_quote
                + "という言葉と、"
                + action_quote
                + "という行動が別々に記されています"
            )
        if context.semantic_kind in {"event", "change"}:
            return (
                context_quote
                + "ことに加えて、"
                + action_quote
                + "という行動も記されています"
            )
        return (
            "今の言葉には、"
            + context_quote
            + "という考えと、"
            + action_quote
            + "という行動があります"
        )
    kinds = {left.semantic_kind, right.semantic_kind}
    if kinds <= {"reaction", "state"}:
        return left_quote + "という感覚と、" + right_quote + "という感覚があります"
    if kinds <= {"event", "change"}:
        return left_quote + "ことと、" + right_quote + "ことが記されています"
    if kinds & {"wish", "value"}:
        return left_quote + "という思いと、" + right_quote + "という思いが並んでいます"
    return left_quote + "という言葉と、" + right_quote + "という言葉があります"


_PAIR_RELATION_PRIORITY: Final = {
    "wish_and_constraint": 0,
    "contrast": 1,
    "coexistence": 1,
    "coexists_with": 1,
    "preserves_despite": 2,
    "shift_from_to": 2,
    "precedes": 2,
    "continuation_or_refusal": 3,
    "attempt_and_block": 3,
    "action_supports_change": 4,
    "uncertain_connection": 5,
}


def _relation_is_surface_bearing(
    binding: Step11Cycle001ProductRecoveryAtomBinding,
    roots_by_owner: Mapping[str, Step11Cycle001ProductRecoveryRootBinding],
) -> bool:
    if binding.semantic_family == "semantic_link":
        return binding.source_retention == "required"
    if binding.semantic_key == "uncertain_connection":
        return False
    if binding.semantic_key == "action_supports_change":
        return _action_support_surface_licensed(binding, roots_by_owner)
    source_explicit = bool(
        binding.source_grounding_kind == "user_stated_relation"
        or binding.authority_basis == "source_explicit_refinement"
    )
    if binding.semantic_key == "shift_from_to":
        return bool(source_explicit and binding.source_retention == "required")
    return source_explicit


def _relation_clause(
    binding: Step11Cycle001ProductRecoveryAtomBinding,
    *,
    roots_by_owner: Mapping[str, Step11Cycle001ProductRecoveryRootBinding],
    referents: Mapping[str, str],
) -> str:
    def owner_text(owner_id: str) -> str:
        root = roots_by_owner.get(owner_id)
        return _root_quote(root) if root is not None else referents[owner_id]

    owners = tuple(binding.source_owner_ids)
    if len(owners) < 2:
        return owner_text(owners[0]) + "に含まれるつながりが見えています"
    left_id, right_id = owners[:2]

    def source_position(owner_id: str) -> tuple[int, int, int, str]:
        root = roots_by_owner.get(owner_id)
        if root is None or not root.source_fragments:
            return (2, 0, 0, owner_id)
        fragment = min(
            root.source_fragments,
            key=lambda row: (
                0 if row.source_field == "thought_text" else 1,
                row.span_relative_start_index,
                row.span_relative_end_index,
                row.source_fragment_id,
            ),
        )
        return (
            0 if fragment.source_field == "thought_text" else 1,
            fragment.span_relative_start_index,
            fragment.span_relative_end_index,
            owner_id,
        )

    def in_source_order() -> tuple[str, str, str, str]:
        first_id, second_id = sorted(
            (left_id, right_id), key=source_position
        )
        return (
            first_id,
            second_id,
            owner_text(first_id),
            owner_text(second_id),
        )

    def joined(first: str, connector: str, second: str) -> str:
        clean_second = re.sub(
            r"^(?:でも|ただ|一方で?|その一方で|それでも|で)[、,]?\s*",
            "",
            second,
        )
        separator = (
            "、"
            if re.search(r"(?:て|で|が|けれど|けど|ものの|ながら|のに)$", first)
            else "。"
        )
        return first + separator + connector + clean_second

    left = owner_text(left_id)
    right = owner_text(right_id)
    key = binding.semantic_key
    if key == "contrast":
        _first_id, _second_id, first, second = in_source_order()
        return joined(first, "一方で、", second)
    if key in {"coexistence", "coexists_with"}:
        _first_id, _second_id, first, second = in_source_order()
        return joined(first, "同時に、", second)
    if key == "wish_and_constraint":
        left_root = roots_by_owner.get(left_id)
        right_root = roots_by_owner.get(right_id)
        if (
            left_root is not None
            and right_root is not None
            and left_root.semantic_kind in {"wish", "value", "other_explicit"}
            and right_root.semantic_kind in {"constraint", "state", "reaction"}
            and right_root.dimensions[2] in {"negative", "mixed"}
        ):
            return joined(left, "その一方で、", right)
        _first_id, _second_id, first, second = in_source_order()
        return joined(first, "", second)
    if key == "preserves_despite":
        return joined(left, "それでも、", right)
    if key == "shift_from_to":
        return joined(left, "これに対して、", right)
    if key == "precedes":
        return joined(left, "そのあとに、", right)
    if key == "continuation_or_refusal":
        return joined(left, "そのうえで、", right)
    if key == "attempt_and_block":
        left_root = roots_by_owner.get(left_id)
        right_root = roots_by_owner.get(right_id)
        if (
            left_root is not None
            and right_root is not None
            and left_root.semantic_kind in {"wish", "action"}
            and right_root.semantic_kind in {"constraint", "state", "reaction"}
            and right_root.dimensions[2] in {"negative", "mixed"}
        ):
            return joined(left, "ただ、", right)
        _first_id, _second_id, first, second = in_source_order()
        return joined(first, "", second)
    if key == "action_supports_change":
        left_kind = roots_by_owner.get(left_id)
        if _action_support_surface_licensed(binding, roots_by_owner):
            if left_kind is not None and left_kind.semantic_kind == "change":
                return joined(left, "その変化に対応して、", right)
            return joined(left, "その向きに対応して、", right)
        return (
            left
            + "と"
            + right
            + "が同じ流れにありますが、前者を後者の原因とは決めません"
        )
    if key == "uncertain_connection":
        return left + "と" + right + "が、どちらも今の記録にあります"
    return left + "と" + right + "のつながりが見えています"


def _action_support_surface_licensed(
    binding: Step11Cycle001ProductRecoveryAtomBinding,
    roots_by_owner: Mapping[str, Step11Cycle001ProductRecoveryRootBinding],
) -> bool:
    if binding.semantic_key != "action_supports_change":
        return False
    if (
        len(binding.source_owner_ids) < 2
        or binding.direction != "source_to_target"
    ):
        return False
    left = roots_by_owner.get(binding.source_owner_ids[0])
    right = roots_by_owner.get(binding.source_owner_ids[1])
    if left is None or right is None or right.semantic_kind != "action":
        return False
    if left.semantic_kind == "change":
        return True
    return bool(
        left.semantic_kind in {"wish", "value", "other_explicit"}
        and left.dimensions[2] not in {"negative", "mixed"}
    )


def _relation_noun_phrase(
    binding: Step11Cycle001ProductRecoveryAtomBinding,
    *,
    roots_by_owner: Mapping[str, Step11Cycle001ProductRecoveryRootBinding],
    referents: Mapping[str, str],
    anaphors: Mapping[str, str],
) -> str:
    def owner_text(owner_id: str) -> str:
        if owner_id in anaphors:
            return anaphors[owner_id]
        root = roots_by_owner.get(owner_id)
        return _root_quote(root) if root is not None else referents[owner_id]

    owners = tuple(binding.source_owner_ids)
    if len(owners) < 2:
        return owner_text(owners[0]) + "に含まれるつながり"
    left_id, right_id = owners[:2]
    left = owner_text(left_id)
    right = owner_text(right_id)
    key = binding.semantic_key
    if key == "contrast":
        return left + "と" + right + "が異なるまま並ぶこと"
    if key in {"coexistence", "coexists_with"}:
        return left + "と" + right + "が同じ今にあること"
    if key == "wish_and_constraint":
        return left + "と" + right + "が異なる事情として並ぶこと"
    if key == "preserves_despite":
        return left + "があっても" + right + "が残ること"
    if key == "shift_from_to":
        return left + "から" + right + "への移り"
    if key == "precedes":
        return left + "から" + right + "への前後"
    if key == "continuation_or_refusal":
        return left + "に対して" + right + "という別の向きがあること"
    if key == "attempt_and_block":
        return left + "と" + right + "が異なる事情として並ぶこと"
    if key == "action_supports_change":
        if _action_support_surface_licensed(binding, roots_by_owner):
            return left + "が" + right + "に表れていること"
        return left + "と" + right + "の原因を決めないこと"
    if key == "uncertain_connection":
        return left + "から" + right + "へという、因果を決めない順序"
    return left + "と" + right + "のつながり"


def _relation_summary_clause(
    bindings: Sequence[Step11Cycle001ProductRecoveryAtomBinding],
    *,
    roots_by_owner: Mapping[str, Step11Cycle001ProductRecoveryRootBinding],
    referents: Mapping[str, str],
) -> str:
    rows = tuple(bindings)
    if len(rows) == 1:
        return _relation_clause(
            rows[0], roots_by_owner=roots_by_owner, referents=referents
        )
    cautious_rows = tuple(
        row
        for row in rows
        if row.semantic_key == "uncertain_connection"
        or (
            row.semantic_key == "action_supports_change"
            and not _action_support_surface_licensed(row, roots_by_owner)
        )
    )
    by_key: dict[str, list[Step11Cycle001ProductRecoveryAtomBinding]] = defaultdict(list)
    for row in rows:
        if row in cautious_rows:
            continue
        by_key[row.semantic_key].append(row)
    phrases: list[str] = []
    if cautious_rows:
        phrases.append(
            "ここに並ぶ出来事・気持ち・行動の因果を決めないこと"
        )
    kind_nouns = {
        "event": "出来事",
        "state": "状態",
        "reaction": "気持ち",
        "wish": "望み",
        "constraint": "難しさ",
        "action": "行動",
        "change": "変化",
        "self_evaluation": "自分への見方",
        "value": "大事にしたい向き",
        "other_explicit": "考え",
    }
    kind_counts = Counter(
        root.semantic_kind for root in roots_by_owner.values()
    )
    kind_ordinals: Counter[str] = Counter()
    ordinal_prefixes = ("最初の", "次の", "三つ目の", "四つ目の", "五つ目の", "六つ目の")
    anaphors: dict[str, str] = {}
    for owner_id, root in roots_by_owner.items():
        noun = kind_nouns.get(root.semantic_kind, "こと")
        if kind_counts[root.semantic_kind] == 1:
            anaphors[owner_id] = "その" + noun
        else:
            ordinal = kind_ordinals[root.semantic_kind]
            kind_ordinals[root.semantic_kind] += 1
            prefix = (
                ordinal_prefixes[ordinal]
                if ordinal < len(ordinal_prefixes)
                else "別の"
            )
            anaphors[owner_id] = prefix + noun
    for key, grouped in by_key.items():
        phrases.extend(
            _relation_noun_phrase(
                row,
                roots_by_owner=roots_by_owner,
                referents=referents,
                anaphors=anaphors,
            )
            for row in grouped
        )
    if len(phrases) == 1:
        return "この流れには、" + phrases[0] + "があります"
    return (
        "この流れには、"
        + "、".join(phrases[:-1])
        + "、そして"
        + phrases[-1]
        + "が含まれています"
    )


def _unknown_limit(key: str) -> str:
    return {
        "explicit_choice_decision_unknown": (
            "どれを選ぶかは、まだ決まっていません"
        ),
        "explicit_unverbalized_unknown": (
            "まだ言葉になっていない部分も残っています"
        ),
        "explicit_cause_unknown": "理由はまだ決められません",
        "explicit_temporal_referent_unknown": (
            "いつのことかは、まだ決めません"
        ),
    }.get(key, "まだ決められない部分も残っています")


def _unknown_limit_for_atom(
    atom: Step11Cycle001ProductRecoveryAtomBinding,
    roots_by_owner: Mapping[str, Step11Cycle001ProductRecoveryRootBinding],
) -> str:
    if atom.semantic_key == "explicit_temporal_referent_unknown":
        roots = tuple(
            roots_by_owner[value]
            for value in atom.source_owner_ids
            if value in roots_by_owner
        )
        if roots and all(root.dimensions[0] != "unknown" for root in roots):
            return ""
    return _unknown_limit(atom.semantic_key)


def _source_segments(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(
        row.strip()
        for row in re.split(r"(?<=[。！？!?])", value)
        if row.strip()
    )


def _residual_source_segments(
    envelope: Step11Cycle001ProductRecoverySourceEnvelope,
) -> tuple[tuple[str, str], ...]:
    fragments = tuple(
        fragment.source_fragment_text
        for root in envelope.root_bindings
        for fragment in root.source_fragments
    )

    def normalized(value: str) -> str:
        return re.sub(r"[\s。！？!?]", "", value)

    normalized_fragments = tuple(normalized(value) for value in fragments)
    rows: list[tuple[str, str]] = []
    for field, value in (
        ("thought_text", envelope.current_input_binding.thought_text),
        ("action_text", envelope.current_input_binding.action_text),
    ):
        for segment in _source_segments(value):
            material = normalized(segment)
            if material and not any(
                fragment in material or material in fragment
                for fragment in normalized_fragments
                if fragment
            ):
                rows.append((field, segment))
    return tuple(rows)


def _cluster_id(
    *,
    roots: Sequence[Step11Cycle001ProductRecoveryRootBinding],
    atom_ids: Sequence[str],
    residual_fields: Sequence[str] = (),
) -> str:
    return "nls3s11rc0036cluster_" + artifact_sha256(
        {
            "root_ids": [row.source_root_id for row in roots],
            "atom_ids": list(atom_ids),
            "residual_fields": list(residual_fields),
        }
    )[:16]


def _reception_clause(
    binding: Step11Cycle001ProductRecoveryReceptionBinding,
    *,
    roots_by_owner: Mapping[str, Step11Cycle001ProductRecoveryRootBinding],
    atoms: Sequence[Step11Cycle001ProductRecoveryAtomBinding],
    allow_anchor: bool,
) -> tuple[str, bool]:
    base_visible_ids = _ordered_unique(
        (
            *binding.source_focus_owner_ids,
            *binding.source_target_owner_ids,
            *binding.visible_support_owner_ids,
        )
    )
    base_visible_set = set(base_visible_ids)
    visible_ids = _ordered_unique(
        (
            *base_visible_ids,
            *(
                owner_id
                for row in atoms
                if row.semantic_family in {"relation", "semantic_link"}
                and base_visible_set & set(row.source_owner_ids)
                for owner_id in row.source_owner_ids
            ),
        )
    )
    visible_set = set(visible_ids)
    visible_roots = tuple(
        roots_by_owner[value]
        for value in visible_ids
        if value in roots_by_owner
    )
    target_roots = tuple(
        roots_by_owner[value]
        for value in binding.source_target_owner_ids
        if value in roots_by_owner
    )
    all_related = tuple(
        row
        for row in atoms
        if visible_set & set(row.source_owner_ids)
    )
    related = tuple(
        row
        for row in all_related
        if row.semantic_family not in {"relation", "semantic_link"}
        or _relation_is_surface_bearing(row, roots_by_owner)
    )
    target_set = set(binding.source_target_owner_ids)
    all_target_related = tuple(
        row for row in all_related if target_set & set(row.source_owner_ids)
    )
    target_related = tuple(
        row for row in related if target_set & set(row.source_owner_ids)
    )
    keys = {
        row.semantic_key
        for row in (
            target_related
            if binding.source_scope == "concrete_effort"
            else related
        )
    }
    has_unknown = any(
        row.semantic_family == "explicit_unknown" for row in related
    )
    polarities = {row.dimensions[2] for row in visible_roots}
    mixed_view = bool(
        "mixed" in polarities
        or ({"positive", "negative"} <= polarities)
    )
    unsafe_support = any(
        row.semantic_key == "action_supports_change"
        and not _action_support_surface_licensed(row, roots_by_owner)
        for row in all_target_related
    )
    safe_support = any(
        row.semantic_key == "action_supports_change"
        and _action_support_surface_licensed(row, roots_by_owner)
        for row in target_related
    )
    source_kinds = {
        roots_by_owner[owner_id].semantic_kind
        for row in all_target_related
        for owner_id in row.source_owner_ids[:1]
        if owner_id in roots_by_owner and owner_id not in target_set
    }
    global_action_present = any(
        fragment.source_field == "action_text"
        for row in roots_by_owner.values()
        for fragment in row.source_fragments
    )
    target_has_action = any(
        fragment.source_field == "action_text"
        for row in target_roots
        for fragment in row.source_fragments
    )
    target_kinds = {row.semantic_kind for row in target_roots}
    visible_kinds = {row.semantic_kind for row in visible_roots}
    target_source_chars = sum(
        len(fragment.source_fragment_text)
        for row in target_roots
        for fragment in row.source_fragments
    )
    _ = allow_anchor
    lead = (
        "Emlisは、"
        if binding.sentence_group_ordinal == 1
        else "また、"
        if binding.sentence_group_ordinal == 2
        else "そのうえで、"
    )

    scope = binding.source_scope
    if scope == "current_burden":
        if global_action_present and not target_has_action:
            if has_unknown:
                text = (
                    lead
                    + "まだ言い切れない今の感覚と、同じ入力にある行動の記録を、"
                    "どちらも先回りせず受け取っています"
                )
            else:
                text = (
                    lead
                    + "いま言葉になった感覚と、同じ入力にある行動の記録の両方を"
                    "受け取っています"
                )
        elif has_unknown:
            text = (
                lead
                + "まだ言い切れない部分を残した今の感覚を、"
                "結論に変えず受け取っています"
            )
        elif mixed_view:
            text = (
                lead
                + "明るさと重さのどちらもある今の感覚を、"
                "片方へ寄せず受け取っています"
            )
        elif "self_evaluation" in visible_kinds:
            text = (
                lead
                + "自分についての見方を事実に固定せず、"
                "そこに書かれた感覚と分けて受け取っています"
            )
        elif visible_roots and polarities <= {"positive", "neutral"}:
            text = (
                lead
                + "今ここにある穏やかさや明るさを、"
                "小さく扱わず受け取っています"
            )
        elif visible_kinds & {"event", "change"}:
            text = lead + "ここに記された出来事と、その時に残った重さを受け取っています"
        else:
            text = lead + "いま言葉になった重さを、軽く流さず受け取っています"
    elif scope == "retained_intention":
        if unsafe_support:
            text = (
                lead
                + "行動の理由や証明には置き換えず、"
                "なお残っている意向を受け取ります"
            )
        elif has_unknown:
            text = (
                lead
                + "まだ決めきらない中にも残っている意向を、"
                "結論に急がず受け取ります"
            )
        elif keys & {"contrast", "coexistence", "coexists_with"}:
            text = (
                lead
                + "ほかの感覚と並んでも消えずにいる意向を、"
                "片方へ寄せず受け取ります"
            )
        elif "value" in target_kinds:
            text = (
                lead
                + "今も手放したくない考えを、"
                "実行済みの結論にはせず受け取ります"
            )
        elif "wish" in target_kinds:
            text = (
                lead
                + "これからへ向いている思いを、"
                "今ここに残る意向として受け取ります"
            )
        elif len(visible_roots) >= 3:
            text = lead + "いくつかの事情の中にも残る意向を、見失わず受け取ります"
        else:
            text = lead + "迷いの中にも残っている意向を、そのまま受け取ります"
    elif scope == "concrete_effort":
        if "shift_from_to" in keys:
            text = (
                lead
                + "前と今の行動の違いを、この記録の範囲に限って受け取ります"
            )
        elif unsafe_support and source_kinds & {"self_evaluation"}:
            text = (
                lead
                + "ここに記された行動を、自分についての見方の証明にはせず、"
                "一つの記録として受け取ります"
            )
        elif unsafe_support and source_kinds & {"constraint"}:
            text = (
                lead
                + "ここに記された行動を、先にある難しさとは分けながら受け取ります"
            )
        elif unsafe_support:
            text = (
                lead
                + "ここに記された行動を、ほかの言葉の証明にはせず受け取ります"
            )
        elif safe_support:
            if "change" in source_kinds:
                text = lead + "言葉に表れた変化と、そこに結び付いた行動の両方を受け取ります"
            elif source_kinds & {"wish", "value"}:
                text = lead + "残っている思いと、それが表れた行動の両方を受け取ります"
            else:
                text = lead + "言葉に残った向きと、そこに結び付いた行動を受け取ります"
        elif has_unknown:
            text = (
                lead
                + "まだ決まっていない部分と、ここに記された行動を、"
                "どちらも先回りせず受け取ります"
            )
        elif keys & {"contrast", "coexistence", "coexists_with"}:
            text = (
                lead
                + "並んでいる感覚と行動を、どちらか一方へまとめず受け取ります"
            )
        elif source_kinds & {"reaction", "state"}:
            text = lead + "その感覚と、同じ入力にある行動を、別々の事実として受け取ります"
        elif source_kinds & {"wish", "value"}:
            text = lead + "残っている思いと、ここに記された行動の両方を受け取ります"
        elif source_kinds & {"event", "change"}:
            text = lead + "起きたことと、ここに記された行動を、どちらも見落とさず受け取ります"
        elif len(target_roots) >= 2:
            text = lead + "ここに並ぶ複数の行動を、それぞれの記載どおり受け取ります"
        elif target_source_chars >= 32:
            text = lead + "手順や範囲まで書かれた行動を、その記載どおり受け取ります"
        elif target_source_chars <= 14:
            text = lead + "ここに短く記された行動を、その記載どおり受け取ります"
        else:
            text = lead + "ここに書かれた行動を、その記載どおり受け取ります"
    elif scope == "lived_change":
        if mixed_view or keys & {"contrast", "coexistence", "coexists_with"}:
            text = (
                lead
                + "異なる感覚が並んだままの変化を、片方へまとめず受け取ります"
            )
        elif has_unknown:
            text = (
                lead
                + "まだ結論を置けないまま表れている違いを、"
                "完成した変化にはせず受け取ります"
            )
        else:
            text = lead + "ここまでの記録に表れた違いを、その範囲に限って受け取ります"
    elif scope == "help_seeking":
        text = (
            lead
            + "支えになった部分と、まだ残っている困りごとの両方を受け取ります"
        )
    elif scope == "counterdirection":
        text = (
            lead
            + "一つの見方だけでまとめず、同時に書かれた別の向きも受け取ります"
        )
    else:
        text = lead + "今ここに置かれた言葉を、軽く扱わず受け取ります"
    predicate = {
        "hold_in_attention": "心に留めています",
        "do_not_dismiss": "見過ごさずにいます",
        "honor_concrete_action": "確かに受け止めています",
    }[binding.effective_reception_act]
    text = re.sub(r"受け取(?:ってい)?ます$", predicate, text)
    return text, False


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
    roots = tuple(envelope.root_bindings)
    roots_by_owner = {row.source_owner_id: row for row in roots}
    root_index = {
        row.source_owner_id: ordinal for ordinal, row in enumerate(roots)
    }
    relational_atoms = tuple(
        row
        for row in envelope.atom_bindings
        if row.semantic_family in {"relation", "semantic_link"}
        and len(row.source_owner_ids) >= 2
        and row.source_owner_ids[0] != row.source_owner_ids[1]
        and all(value in roots_by_owner for value in row.source_owner_ids[:2])
    )
    paired_owner_ids: set[str] = set()
    cluster_specs: list[
        tuple[
            tuple[Step11Cycle001ProductRecoveryRootBinding, ...],
            Step11Cycle001ProductRecoveryAtomBinding | None,
        ]
    ] = []
    for atom in sorted(
        tuple(
            row
            for row in relational_atoms
            if _relation_is_surface_bearing(row, roots_by_owner)
        ),
        key=lambda row: (
            _PAIR_RELATION_PRIORITY.get(row.semantic_key, 99),
            row.source_order,
        ),
    ):
        left_id, right_id = atom.source_owner_ids[:2]
        if left_id in paired_owner_ids or right_id in paired_owner_ids:
            continue
        cluster_specs.append(
            ((roots_by_owner[left_id], roots_by_owner[right_id]), atom)
        )
        paired_owner_ids.update((left_id, right_id))
    remaining_roots = tuple(
        row for row in roots if row.source_owner_id not in paired_owner_ids
    )
    for root in remaining_roots:
        cluster_specs.append(((root,), None))
    cluster_specs.sort(
        key=lambda row: min(
            root_index[root.source_owner_id] for root in row[0]
        )
    )

    atom_order = {
        row.source_atom_id: ordinal
        for ordinal, row in enumerate(envelope.atom_bindings)
    }
    assigned_atom_ids: set[str] = set()
    cluster_atom_ids: list[list[str]] = [[] for _row in cluster_specs]
    cluster_limits: list[list[str]] = [[] for _row in cluster_specs]
    cluster_by_owner: dict[str, int] = {}
    for cluster_ordinal, (cluster_roots, primary_relation) in enumerate(
        cluster_specs
    ):
        for root in cluster_roots:
            cluster_by_owner[root.source_owner_id] = cluster_ordinal
        if primary_relation is not None:
            cluster_atom_ids[cluster_ordinal].append(
                primary_relation.source_atom_id
            )
            assigned_atom_ids.add(primary_relation.source_atom_id)
    for atom in envelope.atom_bindings:
        if atom.source_atom_id in assigned_atom_ids:
            continue
        owner_clusters = tuple(
            dict.fromkeys(
                cluster_by_owner[value]
                for value in atom.source_owner_ids
                if value in cluster_by_owner
            )
        )
        if atom.semantic_family == "construction" and owner_clusters:
            target = owner_clusters[0]
            cluster_atom_ids[target].append(atom.source_atom_id)
            assigned_atom_ids.add(atom.source_atom_id)
        elif atom.semantic_family == "explicit_unknown" and owner_clusters:
            target = owner_clusters[0]
            cluster_atom_ids[target].append(atom.source_atom_id)
            limit = _unknown_limit_for_atom(atom, roots_by_owner)
            if limit:
                cluster_limits[target].append(limit)
            assigned_atom_ids.add(atom.source_atom_id)
    for atom in relational_atoms:
        if atom.source_atom_id in assigned_atom_ids:
            continue
        owner_clusters = tuple(
            dict.fromkeys(
                cluster_by_owner[value]
                for value in atom.source_owner_ids
                if value in cluster_by_owner
            )
        )
        if not owner_clusters:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RENDER_SOURCE_MISMATCH"
            )
        cluster_atom_ids[owner_clusters[0]].append(atom.source_atom_id)
        assigned_atom_ids.add(atom.source_atom_id)

    observation_lines: list[str] = []
    units: list[Step11Cycle001ProductRecoveryRealizationUnit] = []
    for cluster_ordinal, (cluster_roots, primary_relation) in enumerate(
        cluster_specs
    ):
        if primary_relation is not None:
            text = _relation_clause(
                primary_relation,
                roots_by_owner=roots_by_owner,
                referents=referents,
            )
        elif len(cluster_roots) == 1:
            text = _root_clause(cluster_roots[0])
        else:
            left, right = cluster_roots
            text = _neutral_pair_clause(left, right)
        limits = tuple(dict.fromkeys(cluster_limits[cluster_ordinal]))
        if limits:
            text += "。" + "。また、".join(limits)
        atom_ids = tuple(
            sorted(
                cluster_atom_ids[cluster_ordinal],
                key=atom_order.__getitem__,
            )
        )
        owner_ids = _ordered_unique(
            tuple(root.source_owner_id for root in cluster_roots)
        )
        observation_lines.append(text)
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="observation",
                source_unit_id=_cluster_id(
                    roots=cluster_roots,
                    atom_ids=atom_ids,
                ),
                source_atom_ids=atom_ids,
                source_owner_ids=owner_ids,
                source_owner_dimensions=tuple(
                    (owner_id, dimensions_by_owner[owner_id])
                    for owner_id in owner_ids
                ),
                source_obligation_ids=_ordered_unique(
                    tuple(
                        obligation_id
                        for root in cluster_roots
                        for obligation_id in root.source_obligation_ids
                    )
                ),
                source_fragment_ids=tuple(
                    fragment.source_fragment_id
                    for root in cluster_roots
                    for fragment in root.source_fragments
                ),
                dimensions=_aggregate_dimensions(
                    tuple(root.dimensions for root in cluster_roots)
                ),
                visible_clause_count=1,
            )
        )

    for field, segments in (
        (
            candidate_field,
            tuple(
                value
                for source_field, value in _residual_source_segments(envelope)
                if source_field == candidate_field
            ),
        )
        for candidate_field in ("thought_text", "action_text")
    ):
        if not segments:
            continue
        joined = "、".join(segments)
        clause = (
            "背景として、" + joined + "ことも書かれています"
            if field == "thought_text"
            else "行動については、" + joined + "ことも記されています"
        )
        observation_lines.append(clause)
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="observation",
                source_unit_id=_cluster_id(
                    roots=(), atom_ids=(), residual_fields=(field,)
                ),
                source_atom_ids=(),
                source_owner_ids=(),
                source_owner_dimensions=(),
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=("unknown", "unknown", "unknown", "unknown"),
                visible_clause_count=1,
            )
        )

    remaining_relations = tuple(
        binding
        for binding in envelope.atom_bindings
        if binding.source_atom_id not in assigned_atom_ids
    )
    if any(
        binding.semantic_family not in {"relation", "semantic_link"}
        for binding in remaining_relations
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RENDER_SOURCE_MISMATCH"
        )
    if remaining_relations:
        clause = _relation_summary_clause(
            remaining_relations,
            roots_by_owner=roots_by_owner,
            referents=referents,
        )
        relation_atom_ids = tuple(
            row.source_atom_id for row in remaining_relations
        )
        relation_owner_ids = _ordered_unique(
            tuple(
                owner_id
                for row in remaining_relations
                for owner_id in row.source_owner_ids
            )
        )
        observation_lines.append(clause)
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="observation",
                source_unit_id=_cluster_id(
                    roots=(), atom_ids=relation_atom_ids
                ),
                source_atom_ids=relation_atom_ids,
                source_owner_ids=relation_owner_ids,
                source_owner_dimensions=tuple(
                    (owner_id, dimensions_by_owner[owner_id])
                    for owner_id in relation_owner_ids
                ),
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=_aggregate_dimensions(
                    tuple(row.dimensions for row in remaining_relations)
                ),
                visible_clause_count=1,
            )
        )
        assigned_atom_ids.update(relation_atom_ids)
    if assigned_atom_ids != {
        row.source_atom_id for row in envelope.atom_bindings
    }:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RENDER_SOURCE_MISMATCH"
        )

    morphology = catalog["clause_morphology"]
    reception_lines: list[str] = []
    reception_anchor_used = False
    for binding in envelope.reception_bindings:
        target_roots = tuple(
            roots_by_owner.get(value)
            for value in binding.source_target_owner_ids
        )
        if any(row is None for row in target_roots):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_UNRESOLVED"
            )
        reception, used_anchor = _reception_clause(
            binding,
            roots_by_owner=roots_by_owner,
            atoms=envelope.atom_bindings,
            allow_anchor=not reception_anchor_used,
        )
        reception_anchor_used = reception_anchor_used or used_anchor
        reception_lines.append(reception)
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


def _render_product(
    *,
    envelope: Step11Cycle001ProductRecoverySourceEnvelope,
    product_projection: _RecoveryProductProjection,
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    resolver: EvidenceSpanResolver,
) -> tuple[bytes, tuple[Step11Cycle001ProductRecoveryRealizationUnit, ...]]:
    """Render only active grounded phrases and typed owner-bearing moves."""

    overlay = product_projection.semantic_overlay
    roots_by_owner = {
        row.source_owner_id: row for row in envelope.root_bindings
    }
    dimensions_by_owner = {
        row.source_owner_id: row.dimensions for row in envelope.owner_bindings
    }
    ordered_owner_ids = tuple(
        product_projection.actual_owner_by_nucleus_id[source_id]
        for source_id in product_projection.ordered_active_nucleus_ids
    )
    if (
        set(ordered_owner_ids) != set(roots_by_owner)
        or set(ordered_owner_ids) != set(dimensions_by_owner)
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RENDER_OWNER_MISMATCH"
        )

    snapshot = successor_snapshot.base_snapshot
    nucleus_by_actual = {
        str(row.actual_source_id): row for row in snapshot.nuclei
    }
    if any(owner_id not in nucleus_by_actual for owner_id in ordered_owner_ids):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RENDER_OWNER_MISMATCH"
        )

    # Exact downstream references use a typed safe head.  The head comes from
    # the semantic-unit predicate and the exact overlay target state, never
    # from a generic "content" fallback that erases event/action distinctions.
    self_evaluation_owner_ids: set[str] = set()
    for evaluation in overlay.reported_self_evaluations:
        source_ids = _ordered_unique(
            tuple(
                binding.nucleus_id
                for binding in overlay.nucleus_anchor_bindings
                if evaluation.source_anchor_id in binding.source_anchor_ids
            )
        )
        if len(source_ids) != 1 or source_ids[0] not in (
            product_projection.actual_owner_by_nucleus_id
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_SELF_DENIAL_OWNER_UNRESOLVED"
            )
        self_evaluation_owner_ids.add(
            product_projection.actual_owner_by_nucleus_id[source_ids[0]]
        )
    reception_lifecycles_by_owner: dict[str, set[str]] = defaultdict(set)
    for reception in overlay.reception_antecedent_bindings:
        for source_id in (
            reception.antecedent_nucleus_ids
            or reception.source_target_nucleus_ids
        ):
            owner_id = product_projection.actual_owner_by_nucleus_id.get(
                source_id
            )
            if owner_id is not None:
                reception_lifecycles_by_owner[owner_id].add(
                    str(reception.action_lifecycle)
                )
    def owner_head(owner_id: str) -> str:
        nucleus = nucleus_by_actual[owner_id]
        semantic_kind = str(nucleus.kind)
        predicate_kind = str(nucleus.source_predicate_kind)
        if owner_id in self_evaluation_owner_ids or (
            semantic_kind == "self_evaluation"
            or predicate_kind == "self_evaluation"
        ):
            return "自己評価"
        predicate_heads = {
            "action": "行動",
            "feeling": "反応",
            "state": "状態",
            "event": "出来事",
            "change": "変化",
            "wish": "願い",
            "constraint": "制約",
            "other_explicit": "内容",
        }
        kind_heads = {
            "action": "行動",
            "reaction": "反応",
            "state": "状態",
            "event": "出来事",
            "change": "変化",
            "wish": "願い",
            "value": "願い",
            "constraint": "制約",
            "uncertainty": "内容",
            "conclusion": "内容",
            "other_explicit": "内容",
        }
        head = kind_heads.get(semantic_kind) or predicate_heads.get(
            predicate_kind
        )
        if head is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_REFERENCE_COLLISION"
            )
        return head

    head_by_owner = {
        owner_id: owner_head(owner_id) for owner_id in ordered_owner_ids
    }
    referenced_owner_ids = set(self_evaluation_owner_ids)
    referenced_owner_ids.update(
        owner_id
        for binding in envelope.reception_bindings
        for owner_id in (
            *binding.source_target_owner_ids,
            *binding.visible_support_owner_ids,
        )
    )
    referenced_owner_ids.update(
        product_projection.actual_owner_by_nucleus_id[nucleus_id]
        for unknown in overlay.unknowns
        for nucleus_id in unknown.target_nucleus_ids
        if nucleus_id in product_projection.actual_owner_by_nucleus_id
    )
    if not referenced_owner_ids <= set(ordered_owner_ids):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_OWNER_REFERENCE_COLLISION"
        )

    clause_role_by_obligation = {
        str(node["obligation_id"]): str(node["clause_role"])
        for node in product_projection.active_discourse_plan["nodes"]
    }
    def reference_candidates(owner_id: str) -> tuple[str, ...]:
        nucleus = nucleus_by_actual[owner_id]
        head = head_by_owner[owner_id]
        lifecycles = reception_lifecycles_by_owner.get(owner_id, set())
        lifecycle = next(iter(lifecycles)) if len(lifecycles) == 1 else ""
        semantic_kind = str(nucleus.kind)
        predicate_kind = str(nucleus.source_predicate_kind)
        source_modality = str(nucleus.source_modality)
        polarity = str(nucleus.polarity)
        if owner_id in self_evaluation_owner_ids:
            canonical = "その自己評価"
        elif semantic_kind == "action":
            canonical = {
                "intended": "これからの行動",
                "reported_ongoing": "続いている行動",
                "reported_not_completed": "まだ終えていない行動",
                "undetermined": "進み方の定まらない行動",
            }.get(lifecycle, "")
            if not canonical and lifecycle == "reported_completed":
                canonical = (
                    "起きた行動"
                    if source_modality in {"fact", "observed"}
                    else "いまの行動"
                )
            if not canonical:
                canonical = (
                    "これからの行動"
                    if source_modality == "intention"
                    else "まだ定まらない行動"
                    if source_modality == "uncertain"
                    else "いまの行動"
                )
        elif semantic_kind == "reaction" or predicate_kind == "feeling":
            canonical = "感じられている反応"
        elif semantic_kind == "state":
            canonical = "いまある状態"
        elif semantic_kind == "event":
            canonical = (
                "いま起きている出来事"
                if str(nucleus.source_time_scope) == "present"
                else "振り返った出来事"
                if str(nucleus.source_time_scope) == "reported_past"
                else "否定を含む出来事"
                if polarity == "negative"
                else "起きた出来事"
            )
        elif semantic_kind == "change":
            canonical = "起きている変化"
        elif semantic_kind in {"wish", "value"}:
            canonical = (
                "まだ定まらない向き"
                if source_modality in {"wish", "uncertain"}
                or polarity in {"negative", "mixed"}
                else "大切にしている向き"
            )
        elif semantic_kind == "constraint":
            canonical = "いまある制約"
        else:
            canonical = "その" + head
        second_qualifier = {
            "negative": "否定を含む",
            "positive": "肯定的な",
            "mixed": "異なる向きを含む",
        }.get(polarity, "")
        if not second_qualifier:
            second_qualifier = {
                "action": "動きにかかわる",
                "feeling": "感覚にかかわる",
                "state": "状態にかかわる",
                "event": "出来事にかかわる",
                "change": "変化にかかわる",
                "constraint": "制約にかかわる",
            }.get(predicate_kind, "")
        return _ordered_unique(
            (
                canonical,
                second_qualifier + canonical,
                "その" + head,
            )
        )

    candidate_rows = {
        owner_id: reference_candidates(owner_id)
        for owner_id in ordered_owner_ids
    }
    reference_competitor_owner_ids = (
        set(ordered_owner_ids)
        - set(product_projection.credit_only_actual_owner_ids)
    ) | referenced_owner_ids
    owner_reference: dict[str, str] = {}
    for owner_id in referenced_owner_ids:
        for candidate in candidate_rows[owner_id]:
            if all(
                candidate not in candidate_rows[other_id]
                for other_id in reference_competitor_owner_ids
                if other_id != owner_id
            ):
                owner_reference[owner_id] = candidate
                break
    if (
        set(owner_reference) != referenced_owner_ids
        or len(set(owner_reference.values())) != len(owner_reference)
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_OWNER_REFERENCE_COLLISION"
        )

    alias_peers: dict[str, set[str]] = defaultdict(set)
    for binding in successor_snapshot.base_snapshot.source_id_alias_bindings:
        if str(binding.source_kind) not in {"relation", "unknown_boundary"}:
            continue
        actual = str(binding.actual_source_id)
        alias = str(binding.alias_source_id)
        alias_peers[actual].update((actual, alias))
        alias_peers[alias].update((actual, alias))

    def identities(values: Sequence[Any]) -> set[str]:
        result: set[str] = set()
        for value in values:
            key = str(value)
            result.add(key)
            result.update(alias_peers.get(key, ()))
        return result

    atoms = tuple(envelope.atom_bindings)
    assigned_atom_ids: set[str] = set()
    construction_by_owner: dict[str, list[str]] = defaultdict(list)
    for atom in atoms:
        if atom.semantic_family != "construction":
            continue
        owner_id = next(
            (
                value
                for value in ordered_owner_ids
                if value in atom.source_owner_ids
            ),
            None,
        )
        if owner_id is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RENDER_SOURCE_MISMATCH"
            )
        construction_by_owner[owner_id].append(atom.source_atom_id)
        assigned_atom_ids.add(atom.source_atom_id)

    units: list[Step11Cycle001ProductRecoveryRealizationUnit] = []
    observation_lines: list[str] = []
    def append_observation(
        text: str,
        *,
        source_unit_id: str,
        atom_ids: Sequence[str] = (),
        owner_ids: Sequence[str] = (),
        obligation_ids: Sequence[str] = (),
        fragment_ids: Sequence[str] = (),
        dimensions: tuple[str, str, str, str] = (
            "unknown",
            "unknown",
            "unknown",
            "unknown",
        ),
    ) -> None:
        if not text or any(value in text for value in ("\r", "\n")):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RENDER_TEXT_INVALID"
            )
        normalized_owners = _ordered_unique(tuple(owner_ids))
        observation_lines.append(text)
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="observation",
                source_unit_id=source_unit_id,
                source_atom_ids=tuple(atom_ids),
                source_owner_ids=normalized_owners,
                source_owner_dimensions=tuple(
                    (owner_id, dimensions_by_owner[owner_id])
                    for owner_id in normalized_owners
                ),
                source_obligation_ids=tuple(obligation_ids),
                source_fragment_ids=tuple(fragment_ids),
                dimensions=dimensions,
                visible_clause_count=1,
            )
        )

    # Introduce every exact source range once, without a quotation wrapper or
    # a trailing type gloss.  Semantic-decomposition siblings are rejoined in
    # their source order; all later semantic moves use owner-ID anaphors.
    grouped_owner_order = _ordered_unique(
        tuple(
            owner_id
            for group in product_projection.observation_owner_groups
            for owner_id in group
            if owner_id in roots_by_owner
        )
    )
    source_owner_order = _ordered_unique(
        (*grouped_owner_order, *ordered_owner_ids)
    )
    owner_rank = {
        owner_id: ordinal
        for ordinal, owner_id in enumerate(source_owner_order)
    }
    discourse_group_by_owner: dict[str, int] = {}
    for group_ordinal, owner_group in enumerate(
        product_projection.observation_owner_groups
    ):
        for owner_id in owner_group:
            if owner_id in discourse_group_by_owner:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_RENDER_OWNER_MISMATCH"
                )
            discourse_group_by_owner[owner_id] = group_ordinal
    label_owner_ids = {
        owner_id
        for owner_id in ordered_owner_ids
        if str(nucleus_by_actual[owner_id].allowed_claim_scope)
        == "selected_label_only"
    }
    nonvisible_evidence_owner_ids = set(
        product_projection.credit_only_actual_owner_ids
    )
    if any(
        owner_id not in roots_by_owner
        or roots_by_owner[owner_id].required is not False
        or str(nucleus_by_actual[owner_id].allowed_claim_scope)
        not in {"source_bounded_relation", "selected_label_only"}
        for owner_id in nonvisible_evidence_owner_ids
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RENDER_OWNER_MISMATCH"
        )
    if referenced_owner_ids & nonvisible_evidence_owner_ids:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_UNRESOLVED"
        )

    range_rows: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    for owner_id in source_owner_order:
        root = roots_by_owner[owner_id]
        if not root.source_fragments:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
            )
        for fragment in root.source_fragments:
            span = resolver.resolve(fragment.source_span_id)
            span_start = getattr(span, "start_index", None)
            span_end = getattr(span, "end_index", None)
            label_coordinate = fragment.source_field in {
                "emotion_details",
                "emotions",
                "category",
                "categories",
            }
            if label_coordinate:
                absolute_start = owner_rank[owner_id]
                absolute_end = absolute_start
            elif (
                type(span_start) is not int
                or type(span_end) is not int
                or span_start < 0
                or span_end < span_start
            ):
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
                )
            else:
                absolute_start = (
                    span_start + fragment.span_relative_start_index
                )
                absolute_end = span_start + fragment.span_relative_end_index
            range_key = (
                fragment.source_span_id,
                fragment.span_relative_start_index,
                fragment.span_relative_end_index,
                fragment.source_fragment_text_sha256,
            )
            row = range_rows.setdefault(
                range_key,
                {
                    "source_span_id": fragment.source_span_id,
                    "source_field": fragment.source_field,
                    "start": fragment.span_relative_start_index,
                    "end": fragment.span_relative_end_index,
                    "absolute_start": absolute_start,
                    "absolute_end": absolute_end,
                    "text": fragment.source_fragment_text,
                    "text_sha256": fragment.source_fragment_text_sha256,
                    "owner_ids": [],
                    "root_ids": [],
                    "obligation_ids": [],
                    "fragment_ids": [],
                    "dimensions": [],
                },
            )
            if (
                row["source_field"] != fragment.source_field
                or row["text"] != fragment.source_fragment_text
                or row["text_sha256"]
                != fragment.source_fragment_text_sha256
                or (
                    not label_coordinate
                    and row["absolute_end"] > span_end
                )
            ):
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
                )
            row["owner_ids"].append(owner_id)
            row["root_ids"].append(root.source_root_id)
            row["obligation_ids"].extend(root.source_obligation_ids)
            row["fragment_ids"].append(fragment.source_fragment_id)
            row["dimensions"].append(root.dimensions)

    rows_by_span: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    for row in range_rows.values():
        rows_by_span[(row["source_span_id"], row["source_field"])].append(row)
    for span_rows in rows_by_span.values():
        sorted_rows = sorted(span_rows, key=lambda row: (row["start"], row["end"]))
        if any(
            left["end"] > right["start"]
            for left, right in zip(sorted_rows, sorted_rows[1:])
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
            )

    def source_group_rank(
        rows: Sequence[Mapping[str, Any]],
    ) -> tuple[int, int, int]:
        field_rank = {
            "thought_text": 0,
            "memo": 0,
            "action_text": 1,
            "memo_action": 1,
        }
        return (
            min(
                discourse_group_by_owner[owner_id]
                for row in rows
                for owner_id in row["owner_ids"]
            ),
            min(field_rank.get(str(row["source_field"]), 2) for row in rows),
            min(int(row["absolute_start"]) for row in rows),
        )

    main_groups: list[tuple[dict[str, Any], ...]] = []
    for span_rows in rows_by_span.values():
        normal_rows = tuple(
            sorted(
                (
                    row
                    for row in span_rows
                    if not set(row["owner_ids"]) <= label_owner_ids
                    and not set(row["owner_ids"])
                    <= nonvisible_evidence_owner_ids
                ),
                key=lambda row: (row["start"], row["end"]),
            )
        )
        if not normal_rows:
            continue
        decomposition_owned = all(
            "adapter:semantic_decomposition_v3"
            in {
                str(code)
                for owner_id in row["owner_ids"]
                for code in nucleus_by_actual[owner_id].source_attribute_codes
            }
            for row in normal_rows
        )
        if decomposition_owned:
            main_groups.append(normal_rows)
        else:
            main_groups.extend((row,) for row in normal_rows)
    main_groups.sort(key=source_group_rank)

    def attribute_values(owner_id: str, prefix: str) -> tuple[str, ...]:
        return tuple(
            str(code).removeprefix(prefix)
            for code in nucleus_by_actual[owner_id].source_attribute_codes
            if str(code).startswith(prefix)
        )

    def typed_row_joiner(
        left: Mapping[str, Any], right: Mapping[str, Any]
    ) -> str | None:
        if left["source_field"] != right["source_field"]:
            return None
        left_owner_ids = _ordered_unique(tuple(left["owner_ids"]))
        right_owner_ids = _ordered_unique(tuple(right["owner_ids"]))
        marker_owned = bool(left_owner_ids) and all(
            str(nucleus_by_actual[owner_id].allowed_claim_scope)
            == "source_bounded_relation"
            and "relation_marker"
            in attribute_values(owner_id, "detected_type:")
            for owner_id in left_owner_ids
        )
        right_roles = {
            value
            for owner_id in right_owner_ids
            for value in attribute_values(owner_id, "semantic_role:")
        }
        if marker_owned:
            if int(left["absolute_end"]) == int(right["absolute_start"]):
                return ""
            if "contrast_after" in right_roles:
                return "、"
        return None

    rendered_fragment_ids: set[str] = {
        fragment.source_fragment_id
        for owner_id in nonvisible_evidence_owner_ids
        for fragment in roots_by_owner[owner_id].source_fragments
    }
    rendered_semantic_owner_ids: set[str] = set(
        nonvisible_evidence_owner_ids
    )

    def append_source_group(
        rows: Sequence[Mapping[str, Any]],
        *,
        text: str,
        unit_family: str,
        extra_atom_ids: Sequence[str] = (),
    ) -> None:
        owner_ids = _ordered_unique(
            tuple(
                owner_id for row in rows for owner_id in row["owner_ids"]
            )
        )
        newly_semantic_owner_ids = tuple(
            owner_id
            for owner_id in owner_ids
            if owner_id not in rendered_semantic_owner_ids
        )
        atom_ids = _ordered_unique(
            tuple(extra_atom_ids)
            + tuple(
                atom_id
                for owner_id in newly_semantic_owner_ids
                for atom_id in construction_by_owner.get(owner_id, ())
            )
        )
        obligation_ids = _ordered_unique(
            tuple(
                obligation_id
                for owner_id in newly_semantic_owner_ids
                for obligation_id in roots_by_owner[
                    owner_id
                ].source_obligation_ids
            )
        )
        fragment_ids = tuple(
            fragment_id
            for row in rows
            for fragment_id in row["fragment_ids"]
        )
        if set(fragment_ids) & rendered_fragment_ids:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ROOT_FRAGMENT_INVALID"
            )
        append_observation(
            text,
            source_unit_id=(
                "nls3s11rc0036"
                + unit_family
                + "_"
                + artifact_sha256(
                    {
                        "source_root_ids": list(
                            _ordered_unique(
                                tuple(
                                    root_id
                                    for row in rows
                                    for root_id in row["root_ids"]
                                )
                            )
                        ),
                        "source_fragment_ids": list(fragment_ids),
                    }
                )[:16]
            ),
            atom_ids=atom_ids,
            owner_ids=owner_ids,
            obligation_ids=obligation_ids,
            fragment_ids=fragment_ids,
            dimensions=_aggregate_dimensions(
                tuple(
                    roots_by_owner[owner_id].dimensions
                    for owner_id in owner_ids
                )
            ),
        )
        assigned_atom_ids.update(atom_ids)
        rendered_fragment_ids.update(fragment_ids)
        rendered_semantic_owner_ids.update(newly_semantic_owner_ids)

    def compose_source_group(rows: Sequence[Mapping[str, Any]]) -> str:
        if len(rows) == 1:
            return str(rows[0]["text"])
        owners = _ordered_unique(
            tuple(owner_id for row in rows for owner_id in row["owner_ids"])
        )
        decomposition_owned = all(
            "adapter:semantic_decomposition_v3"
            in {
                str(code)
                for code in nucleus_by_actual[owner_id].source_attribute_codes
            }
            for owner_id in owners
        )
        if decomposition_owned:
            unit_rows: dict[str, Mapping[str, Any]] = {}
            connective_codes: set[str] = set()
            typed_dimensions: list[tuple[str, str, str, str]] = []
            for row in rows:
                row_owners = _ordered_unique(tuple(row["owner_ids"]))
                if len(row_owners) != 1:
                    raise Step11Cycle001ProductRecoveryError(
                        "STEP11_CYCLE001_RECOVERY_SEMANTIC_UNIT_COMPOSITION_INVALID"
                    )
                nucleus = nucleus_by_actual[row_owners[0]]
                roles = attribute_values(row_owners[0], "unit_role:")
                connectives = attribute_values(row_owners[0], "connective:")
                typed = (
                    str(nucleus.source_predicate_kind),
                    str(nucleus.source_modality),
                    str(nucleus.polarity),
                    str(nucleus.source_time_scope),
                )
                if (
                    len(roles) != 1
                    or roles[0] not in {"antecedent", "consequent"}
                    or roles[0] in unit_rows
                    or len(connectives) != 1
                    or not all(typed)
                ):
                    raise Step11Cycle001ProductRecoveryError(
                        "STEP11_CYCLE001_RECOVERY_SEMANTIC_UNIT_COMPOSITION_INVALID"
                    )
                unit_rows[roles[0]] = row
                connective_codes.add(connectives[0])
                typed_dimensions.append(typed)
            separator_by_connective = {
                "contrast_despite": "、",
                "contrast_but": "、",
                "post_event_when": "、",
                "explicit_conjunctive_te": "、",
                "explicit_conjunctive_de": "、",
            }
            if (
                set(unit_rows) != {"antecedent", "consequent"}
                or len(connective_codes) != 1
                or len(typed_dimensions) != 2
            ):
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_SEMANTIC_UNIT_COMPOSITION_INVALID"
                )
            connective = next(iter(connective_codes))
            separator = separator_by_connective.get(connective)
            if separator is None:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_SEMANTIC_UNIT_COMPOSITION_INVALID"
                )
            return (
                str(unit_rows["antecedent"]["text"])
                + separator
                + str(unit_rows["consequent"]["text"])
            )
        composed = str(rows[0]["text"])
        for left, right in zip(rows, rows[1:]):
            joiner = typed_row_joiner(left, right)
            if joiner is None:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_SEMANTIC_UNIT_COMPOSITION_INVALID"
                )
            composed += joiner + str(right["text"])
        return composed

    group_index_by_owner: dict[str, int] = {}
    for group_index, rows in enumerate(main_groups):
        for owner_id in _ordered_unique(
            tuple(
                owner_id for row in rows for owner_id in row["owner_ids"]
            )
        ):
            if owner_id in group_index_by_owner:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_RENDER_OWNER_MISMATCH"
                )
            group_index_by_owner[owner_id] = group_index
    relation_atom_ids_by_group: dict[int, list[str]] = defaultdict(list)
    suppressed_relation_atom_ids: set[str] = set()
    relation_rows_by_group_pair: dict[
        tuple[int, int], list[tuple[Any, Any, str, str]]
    ] = defaultdict(list)
    for relation in overlay.relations:
        if not relation.required and not relation.explicit:
            continue
        from_owner = product_projection.actual_owner_by_nucleus_id[
            relation.from_nucleus_id
        ]
        to_owner = product_projection.actual_owner_by_nucleus_id[
            relation.to_nucleus_id
        ]
        matches = tuple(
            atom
            for atom in atoms
            if atom.semantic_family in {"relation", "semantic_link"}
            and tuple(atom.source_owner_ids[:2]) == (from_owner, to_owner)
        )
        if len(matches) != 1:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_RELATION_UNRESOLVED"
            )
        atom = matches[0]
        if _relation_surface_mode(atom) == "suppressed":
            suppressed_relation_atom_ids.add(atom.source_atom_id)
            continue
        from_group = group_index_by_owner.get(from_owner)
        to_group = group_index_by_owner.get(to_owner)
        if from_group is None or to_group is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_RELATION_UNRESOLVED"
            )
        if from_group == to_group:
            relation_atom_ids_by_group[from_group].append(
                atom.source_atom_id
            )
            continue
        relation_rows_by_group_pair[
            tuple(sorted((from_group, to_group)))
        ].append(
            (relation, atom, from_owner, to_owner)
        )

    relation_connector_by_key = {
        "contrast": "一方で、",
        "coexistence": "同時に、",
        "coexists_with": "同時に、",
        "wish_and_constraint": "その一方で、",
        "preserves_despite": "それでも、",
        "shift_from_to": "これに対して、",
        "precedes": "そのあとに、",
        "continuation_or_refusal": "そのうえで、",
        "attempt_and_block": "ただ、",
    }
    compatible_relation_key_sets = (
        frozenset({"wish_and_constraint", "preserves_despite"}),
        frozenset({"contrast", "coexistence"}),
        frozenset({"contrast", "coexists_with"}),
    )
    relation_merge_by_group: dict[
        int, tuple[int, tuple[tuple[Any, Any, str, str], ...], int, int, str]
    ] = {}
    consumed_relation_groups: set[int] = set()
    for group_pair, relation_rows in relation_rows_by_group_pair.items():
        keys = frozenset(str(row[1].semantic_key) for row in relation_rows)
        if (
            not keys
            or any(key not in relation_connector_by_key for key in keys)
            or (
                len(keys) > 1
                and keys not in compatible_relation_key_sets
            )
            or bool(set(group_pair) & consumed_relation_groups)
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RELATION_GRAMMAR_INVALID"
            )
        primary = next(
            (
                row
                for key in (
                    "preserves_despite",
                    "precedes",
                    "shift_from_to",
                    "continuation_or_refusal",
                    "attempt_and_block",
                    "wish_and_constraint",
                    "contrast",
                    "coexistence",
                    "coexists_with",
                )
                for row in relation_rows
                if str(row[1].semantic_key) == key
            ),
            None,
        )
        if primary is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RELATION_GRAMMAR_INVALID"
            )
        _primary_relation, primary_atom, primary_from, primary_to = primary
        if str(primary_atom.direction) == "bidirectional":
            left_group, right_group = group_pair
        elif str(primary_atom.direction) == "source_to_target":
            left_group = group_index_by_owner[primary_from]
            right_group = group_index_by_owner[primary_to]
        else:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RELATION_GRAMMAR_INVALID"
            )
        connector = (
            ""
            if any(row[1].source_marker_span_ids for row in relation_rows)
            else relation_connector_by_key[str(primary_atom.semantic_key)]
        )
        first_group = min(group_pair)
        second_group = max(group_pair)
        relation_merge_by_group[first_group] = (
            second_group,
            tuple(relation_rows),
            left_group,
            right_group,
            connector,
        )
        consumed_relation_groups.update(group_pair)

    for group_index, rows in enumerate(main_groups):
        if group_index in {
            value[0] for value in relation_merge_by_group.values()
        }:
            continue
        merged = relation_merge_by_group.get(group_index)
        if merged is not None:
            (
                second_group,
                relation_rows,
                left_group,
                right_group,
                connector,
            ) = merged
            second_rows = main_groups[second_group]
            rows_by_group = {
                group_index: rows,
                second_group: second_rows,
            }
            left_rows = rows_by_group[left_group]
            right_rows = rows_by_group[right_group]
            merged_rows = (*rows, *second_rows)
            left_text = compose_source_group(left_rows)
            junction_boundary = (
                ""
                if left_text.endswith(("。", "！", "？", "!", "?"))
                else "。"
            )
            append_source_group(
                merged_rows,
                text=(
                    left_text
                    + junction_boundary
                    + connector
                    + compose_source_group(right_rows)
                ),
                unit_family="relationmeaning",
                extra_atom_ids=tuple(
                    row[1].source_atom_id for row in relation_rows
                ),
            )
            continue
        source_group_owner_ids = _ordered_unique(
            tuple(
                owner_id for row in rows for owner_id in row["owner_ids"]
            )
        )
        append_source_group(
            rows,
            text=compose_source_group(rows),
            unit_family="meaning",
            extra_atom_ids=tuple(
                relation_atom_ids_by_group.get(group_index, ())
            ),
        )

    label_rows_by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in range_rows.values():
        row_owner_ids = set(row["owner_ids"])
        if (
            not row_owner_ids <= label_owner_ids
            or row_owner_ids <= nonvisible_evidence_owner_ids
        ):
            continue
        source_field = str(row["source_field"])
        if source_field in {"emotion_details", "emotions"}:
            label_kind = "emotion"
        elif source_field in {"category", "categories"}:
            label_kind = "category"
        else:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_LABEL_SOURCE_INVALID"
            )
        label_rows_by_kind[label_kind].append(row)
    for label_kind in ("emotion", "category"):
        rows = tuple(
            sorted(
                label_rows_by_kind.get(label_kind, ()),
                key=lambda row: source_group_rank((row,)),
            )
        )
        if not rows:
            continue
        labels = tuple(str(row["text"]) for row in rows)
        subject = (
            "選ばれている感情"
            if label_kind == "emotion"
            else "選ばれている話題"
        )
        companion_text = (
            subject + "は、" + labels[0] + "です"
            if len(labels) == 1
            else subject + "には、" + "と".join(labels) + "があります"
        )
        append_source_group(
            rows,
            text=companion_text,
            unit_family="labelcompanion",
        )

    expected_fragment_ids = {
        fragment.source_fragment_id
        for root in envelope.root_bindings
        for fragment in root.source_fragments
    }
    if (
        rendered_fragment_ids != expected_fragment_ids
        or rendered_semantic_owner_ids != set(ordered_owner_ids)
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RENDER_OWNER_MISMATCH"
        )

    active_source_ids = set(product_projection.ordered_active_nucleus_ids)
    required_self_evaluations = tuple(
        evaluation
        for evaluation in overlay.reported_self_evaluations
        if evaluation.identity_fact_denial_required is True
    )
    if len(required_self_evaluations) != len(
        overlay.reported_self_evaluations
    ) or any(
        evaluation.bounded_counterposition_required is not True
        for evaluation in required_self_evaluations
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_SELF_DENIAL_OWNER_UNRESOLVED"
        )
    rendered_self_evaluation_ids: set[str] = set()
    rendered_self_evaluation_owner_ids: set[str] = set()
    for evaluation in required_self_evaluations:
        source_ids = _ordered_unique(
            tuple(
                binding.nucleus_id
                for binding in overlay.nucleus_anchor_bindings
                if evaluation.source_anchor_id in binding.source_anchor_ids
                and binding.nucleus_id in active_source_ids
            )
        )
        if len(source_ids) != 1:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_SELF_DENIAL_OWNER_UNRESOLVED"
            )
        owner_id = product_projection.actual_owner_by_nucleus_id[
            source_ids[0]
        ]
        if (
            evaluation.self_evaluation_id in rendered_self_evaluation_ids
            or owner_id in rendered_self_evaluation_owner_ids
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_SELF_DENIAL_OWNER_UNRESOLVED"
            )
        append_observation(
            owner_reference[owner_id]
            + "を、あなた自身についての事実とは決めません",
            source_unit_id=evaluation.self_evaluation_id,
            owner_ids=(owner_id,),
            dimensions=dimensions_by_owner[owner_id],
        )
        rendered_self_evaluation_ids.add(evaluation.self_evaluation_id)
        rendered_self_evaluation_owner_ids.add(owner_id)
    if rendered_self_evaluation_ids != {
        row.self_evaluation_id for row in required_self_evaluations
    }:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_SELF_DENIAL_OWNER_UNRESOLVED"
        )

    unknown_atoms = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "unknown_dimension_atoms"
    ]
    unknown_predicate = str(
        STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["unknown_predicate"]
    )

    unknown_dimension_by_type = {
        "cause": "cause",
        "future_outcome": "outcome",
        "omitted_referent": "referent",
        "unresolved_intention": "future",
        "decision_state": "decision_state",
        "post_decision_comparative_merit": (
            "post_decision_comparative_merit"
        ),
        "other_person": "other_person_awareness",
        "relation": "relation",
        "unspecified": "generic",
    }

    for unknown in overlay.unknowns:
        unknown_ids = identities(unknown.source_unknown_ids)
        source_ids = _ordered_unique(tuple(unknown.target_nucleus_ids))
        owner_ids = _ordered_unique(
            tuple(
                product_projection.actual_owner_by_nucleus_id[value]
                for value in source_ids
                if value in product_projection.actual_owner_by_nucleus_id
            )
        )
        if not owner_ids:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_UNKNOWN_UNRESOLVED"
            )
        matches = tuple(
            atom
            for atom in atoms
            if atom.semantic_family == "explicit_unknown"
            and identities((atom.source_atom_id,)) & unknown_ids
            and bool(set(atom.source_owner_ids) & set(owner_ids))
        )
        if not matches:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_UNKNOWN_UNRESOLVED"
            )
        assigned_matches = tuple(
            atom.source_atom_id in assigned_atom_ids for atom in matches
        )
        if all(assigned_matches):
            continue
        if any(assigned_matches):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_UNKNOWN_UNRESOLVED"
            )
        dimension_key = unknown_dimension_by_type.get(unknown.unknown_type)
        if dimension_key is None:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_UNKNOWN_GRAMMAR_INVALID"
            )
        owner_text = "と".join(
            owner_reference[value] for value in owner_ids
        )
        boundary_by_dimension = {
            "decision_state": "で選ぶ先は、まだ確定したことにしません",
            "post_decision_comparative_merit": (
                "を決めた後の比べ方は、まだ補いません"
            ),
            "other_person_awareness": (
                "が相手からどう見えるかは、まだ決めつけません"
            ),
            "cause": "の理由や背景は、まだ一つに決めません",
            "referent": "が何を指すかは、こちらで補いません",
            "future": "の先の展開は、まだ決まったことにしません",
            "outcome": "の結果は、まだ確定したことにしません",
            "relation": "の間の関係は、まだ一つに決めません",
            "generic": "に残る不明な部分は、そのまま開いておきます",
        }
        if not str(unknown_atoms[dimension_key]) or not unknown_predicate:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_UNKNOWN_GRAMMAR_INVALID"
            )
        text = owner_text + boundary_by_dimension[dimension_key]
        atom_ids = tuple(row.source_atom_id for row in matches)
        append_observation(
            text,
            source_unit_id=unknown.unknown_id,
            atom_ids=atom_ids,
            owner_ids=owner_ids,
            dimensions=("unknown", "unknown", "unknown", "unknown"),
        )
        assigned_atom_ids.update(atom_ids)

    if (
        assigned_atom_ids & suppressed_relation_atom_ids
        or assigned_atom_ids | suppressed_relation_atom_ids
        != {row.source_atom_id for row in atoms}
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RENDER_SOURCE_MISMATCH"
        )

    antecedent_registry: dict[str, _RecoveryObservationAntecedent] = {}
    for owner_id in referenced_owner_ids:
        evidence = product_projection.antecedent_evidence_by_actual_owner.get(
            owner_id
        )
        source_units = tuple(
            unit
            for unit in units
            if unit.section_role == "observation"
            and bool(unit.source_fragment_ids)
            and owner_id in unit.source_owner_ids
        )
        if evidence is None or len(source_units) != 1:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_UNRESOLVED"
            )
        source_unit = source_units[0]
        antecedent_registry[owner_id] = _RecoveryObservationAntecedent(
            owner_id=owner_id,
            source_unit_id=source_unit.source_unit_id,
            source_fragment_ids=source_unit.source_fragment_ids,
            evidence=evidence,
            reference_text=owner_reference[owner_id],
        )
    if set(antecedent_registry) != referenced_owner_ids:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_UNRESOLVED"
        )

    morphology = catalog["clause_morphology"]
    act_fragments = catalog["reception_act_predicate_fragments"]
    overlay_reception_by_opportunity: dict[str, Any] = {}
    for overlay_binding in overlay.reception_antecedent_bindings:
        for opportunity_id in overlay_binding.source_reception_opportunity_ids:
            if opportunity_id in overlay_reception_by_opportunity:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_INVALID"
                )
            overlay_reception_by_opportunity[opportunity_id] = overlay_binding
    if len(product_projection.visible_anchor_by_actual_owner) > 1:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_INVALID"
        )

    def antecedent_reference(owner_id: str) -> str:
        row = antecedent_registry.get(owner_id)
        if row is None or not row.reference_text:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_UNRESOLVED"
            )
        return row.reference_text

    unknown_modifier_by_type = {
        "cause": "理由を補わず",
        "future_outcome": "先の結果を決めず",
        "omitted_referent": "指すものを補わず",
        "unresolved_intention": "意図の先を閉じず",
        "decision_state": "選ぶ先を決めず",
        "post_decision_comparative_merit": "後の比較を補わず",
        "other_person": "相手の受け取り方を決めつけず",
        "relation": "未確定な結びつきを補わず",
        "unspecified": "未確定な部分を補わず",
    }
    def reception_authority_tags(
        move: _RecoveryReceptionMove,
    ) -> tuple[frozenset[str], bool]:
        if not move.target_semantic_profiles:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        tags = {
            "target_reference",
            "neutral_acknowledgement",
            "act:" + move.effective_act,
            "lifecycle:" + move.action_lifecycle,
        }
        for profile in move.target_semantic_profiles:
            tags.update(
                {
                    "kind:" + profile.semantic_kind,
                    "predicate:" + profile.predicate_kind,
                    "source_modality:" + profile.source_modality,
                    "modality:" + profile.modality,
                    "polarity:" + profile.polarity,
                }
            )
        if move.support_references:
            tags.update({"support_reference", "support_subordinate"})
        for unknown_type, role in move.unknown_roles:
            tags.add("unknown:" + role + ":" + unknown_type)
        if move.self_denial_required:
            tags.add("self_denial_boundary")
        if move.unknown_roles or move.self_denial_required:
            tags.add("boundary_preservation")
        if move.action_lifecycle in {
            "intended",
            "reported_not_completed",
            "undetermined",
        }:
            tags.add("nonperformed")
        if (
            move.action_lifecycle
            in {"reported_completed", "reported_ongoing"}
            and any(
                profile.source_modality not in {"fact", "observed"}
                for profile in move.target_semantic_profiles
            )
        ):
            tags.add("lifecycle_conflict")
        if any(
            profile.polarity in {"negative", "mixed"}
            for profile in move.target_semantic_profiles
        ):
            tags.add("nonpositive")
        has_conflict = any(
            relation_type == "contrasts_with"
            for relation_type, _direction, _target_role in move.relation_roles
        )
        honor_performed = bool(
            move.effective_act == "honor_concrete_action"
            and move.action_lifecycle
            in {"reported_completed", "reported_ongoing"}
            and all(
                profile.semantic_kind == "action"
                and profile.predicate_kind == "action"
                and profile.source_modality in {"fact", "observed"}
                and profile.polarity in {"neutral", "positive"}
                for profile in move.target_semantic_profiles
            )
            and not move.unknown_roles
            and not move.self_denial_required
            and not has_conflict
        )
        if honor_performed:
            tags.add("performed")
        return frozenset(tags), honor_performed

    def target_predicate_morpheme(
        move: _RecoveryReceptionMove,
        *,
        honor_performed: bool,
    ) -> _RecoveryTaggedMorpheme:
        profiles = move.target_semantic_profiles
        semantic_kinds = {profile.semantic_kind for profile in profiles}
        predicate_kinds = {profile.predicate_kind for profile in profiles}
        target = str(morphology["target_owner_join"]).join(
            move.target_references
        )
        if semantic_kinds == {"action"}:
            predicate = (
                "がまだ実行済みではないこと"
                if move.action_lifecycle == "intended"
                else ""
            )
            tags = {"target_reference", "kind:action"}
            if move.action_lifecycle in {
                "intended",
                "reported_ongoing",
                "reported_not_completed",
                "reported_completed",
                "undetermined",
            }:
                tags.add("lifecycle:" + move.action_lifecycle)
            if move.action_lifecycle in {
                "intended",
                "reported_not_completed",
                "undetermined",
            }:
                tags.add("nonperformed")
            if honor_performed:
                tags.add("performed")
            tags.update("predicate:" + value for value in predicate_kinds)
            return _RecoveryTaggedMorpheme(
                text=target + predicate,
                surface_claim_tags=frozenset(tags),
            )
        if len(semantic_kinds) == 1:
            semantic_kind = next(iter(semantic_kinds))
            if semantic_kind == "self_evaluation" and not (
                move.self_denial_required
            ):
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
                )
            if semantic_kind == "self_evaluation":
                return _RecoveryTaggedMorpheme(
                    text="",
                    surface_claim_tags=frozenset(),
                )
            if semantic_kind in {
                "reaction",
                "state",
                "event",
                "change",
                "wish",
                "value",
                "constraint",
                "self_evaluation",
                "uncertainty",
                "conclusion",
                "other_explicit",
            }:
                return _RecoveryTaggedMorpheme(
                    text=target,
                    surface_claim_tags=frozenset(
                        {"target_reference", "kind:" + semantic_kind}
                    ),
                )
        if predicate_kinds == {"feeling"}:
            return _RecoveryTaggedMorpheme(
                text=target + "が感じられていること",
                surface_claim_tags=frozenset(
                    {"target_reference", "predicate:feeling"}
                ),
            )
        return _RecoveryTaggedMorpheme(
            text=target,
            surface_claim_tags=frozenset({"target_reference"}),
        )

    def render_reception_move(move: _RecoveryReceptionMove) -> str:
        authority_tags, honor_performed = reception_authority_tags(move)
        target_text = str(morphology["target_owner_join"]).join(
            move.target_references
        )
        target_unknowns = _ordered_unique(tuple(
            unknown_type
            for unknown_type, role in move.unknown_roles
            if role == "target"
        ))
        context_unknowns = _ordered_unique(tuple(
            unknown_type
            for unknown_type, role in move.unknown_roles
            if role == "context"
        ))
        boundary_morphemes: list[_RecoveryTaggedMorpheme] = []
        if move.self_denial_required:
            if {
                profile.semantic_kind
                for profile in move.target_semantic_profiles
            } != {"self_evaluation"}:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
                )
            boundary_morphemes.append(
                _RecoveryTaggedMorpheme(
                    text=target_text + "を事実とは決めず",
                    surface_claim_tags=frozenset(
                        {"self_denial_boundary", "target_reference"}
                    ),
                )
            )
        if target_unknowns:
            boundary_morphemes.append(
                _RecoveryTaggedMorpheme(
                    text=(
                        unknown_modifier_by_type[target_unknowns[0]]
                        if len(target_unknowns) == 1
                        and target_unknowns[0] in unknown_modifier_by_type
                        else "対象の未確定な部分を補わず"
                    ),
                    surface_claim_tags=frozenset(
                        "unknown:target:" + value
                        for value in target_unknowns
                    ),
                )
            )
        if context_unknowns:
            boundary_morphemes.append(
                _RecoveryTaggedMorpheme(
                    text="背景の未確定な部分を補わず",
                    surface_claim_tags=frozenset(
                        "unknown:context:" + value
                        for value in context_unknowns
                    ),
                )
            )
        prefix_morphemes: list[_RecoveryTaggedMorpheme] = []
        if move.support_references:
            prefix_morphemes.append(
                _RecoveryTaggedMorpheme(
                    text=(
                        str(morphology["support_owner_join"]).join(
                            move.support_references
                        )
                        + "も含めながら"
                    ),
                    surface_claim_tags=frozenset({"support_reference"}),
                )
            )
        target_morpheme = target_predicate_morpheme(
            move, honor_performed=honor_performed
        )
        clause_roles = {
            role
            for profile in move.target_semantic_profiles
            for role in profile.clause_roles
        }
        topology = (
            "boundary_first"
            if boundary_morphemes or "unknown_boundary" in clause_roles
            else "support_subordinate"
            if prefix_morphemes
            else "aspective_action"
            if any(
                profile.semantic_kind == "action"
                for profile in move.target_semantic_profiles
            )
            or bool(clause_roles & {"next_action", "shift_notice"})
            else "simple_state"
        )
        completion_authority_conflict = bool(
            move.action_lifecycle
            in {"reported_completed", "reported_ongoing"}
            and any(
                profile.source_modality not in {"fact", "observed"}
                for profile in move.target_semantic_profiles
            )
        )
        if move.effective_act == "hold_in_attention":
            if topology == "boundary_first":
                stance_text = "急いで結論にせず心に留めています"
                stance_effects = {"boundary_preservation"}
            elif topology == "support_subordinate":
                stance_text = "ともに心に留めています"
                stance_effects = {"support_subordinate"}
            elif completion_authority_conflict:
                stance_text = "進み方まで決めつけず心に留めています"
                stance_effects = {"lifecycle_conflict"}
            elif move.action_lifecycle in {
                "intended",
                "reported_not_completed",
                "undetermined",
            }:
                stance_text = "先走らず心に留めています"
                stance_effects = {"nonperformed"}
            else:
                stance_text = "心に留めています"
                stance_effects = set()
            stance = _RecoveryTaggedMorpheme(
                text=stance_text,
                surface_claim_tags=frozenset(
                    {
                        "act:hold_in_attention",
                        "neutral_acknowledgement",
                        *stance_effects,
                    }
                ),
            )
        elif move.effective_act == "do_not_dismiss":
            if topology == "boundary_first":
                stance_text = "決めつけずに受け止めています"
                stance_effects = {"boundary_preservation"}
            elif topology == "support_subordinate":
                stance_text = "切り離さず受け止めています"
                stance_effects = {"support_subordinate"}
            elif completion_authority_conflict:
                stance_text = "進み方まで決めつけず受け止めています"
                stance_effects = {"lifecycle_conflict"}
            elif move.action_lifecycle == "reported_not_completed":
                stance_text = "終わったものとはせず受け止めています"
                stance_effects = {"nonperformed"}
            elif move.action_lifecycle == "undetermined":
                stance_text = "進み方を決めず受け止めています"
                stance_effects = {"nonperformed"}
            elif move.action_lifecycle == "intended":
                stance_text = "先を急がず受け止めています"
                stance_effects = {"nonperformed"}
            else:
                stance_text = "軽く扱わず受け止めています"
                stance_effects = set()
            stance = _RecoveryTaggedMorpheme(
                text=stance_text,
                surface_claim_tags=frozenset(
                    {
                        "act:do_not_dismiss",
                        "neutral_acknowledgement",
                        *stance_effects,
                    }
                ),
            )
        elif move.effective_act == "honor_concrete_action":
            if honor_performed:
                stance_text = (
                    "続く動きとして受け止めています"
                    if move.action_lifecycle == "reported_ongoing"
                    else "確かな動きとして受け止めています"
                )
                stance_effects = {
                    "act:honor_concrete_action",
                    "performed",
                }
            elif topology == "boundary_first":
                stance_text = "急いで結論にせず受け止めています"
                stance_effects = {"boundary_preservation"}
            elif topology == "support_subordinate":
                stance_text = "切り離さず受け止めています"
                stance_effects = {"support_subordinate"}
            elif completion_authority_conflict:
                stance_text = "進み方まで決めつけず受け止めています"
                stance_effects = {"lifecycle_conflict"}
            elif move.action_lifecycle == "intended":
                stance_text = "先を急がず受け止めています"
                stance_effects = {"nonperformed"}
            elif move.action_lifecycle == "reported_not_completed":
                stance_text = "終わったものとはせず受け止めています"
                stance_effects = {"nonperformed"}
            elif move.action_lifecycle == "undetermined":
                stance_text = "進み方を決めず受け止めています"
                stance_effects = {"nonperformed"}
            elif any(
                profile.polarity in {"negative", "mixed"}
                for profile in move.target_semantic_profiles
            ):
                stance_text = "余分に評価せず受け止めています"
                stance_effects = {"nonpositive"}
            else:
                stance_text = "受け止めています"
                stance_effects = set()
            stance = _RecoveryTaggedMorpheme(
                text=stance_text,
                surface_claim_tags=frozenset(
                    {"neutral_acknowledgement", *stance_effects}
                ),
            )
        else:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        ordered_morphemes = (
            (*boundary_morphemes, *prefix_morphemes)
            if topology == "boundary_first"
            else (*prefix_morphemes, *boundary_morphemes)
        )
        prefix = "、".join(row.text for row in ordered_morphemes)
        core = (
            target_morpheme.text + "を" if target_morpheme.text else ""
        ) + stance.text
        text = prefix + ("、" if prefix else "") + core
        surface_tags = frozenset(
            tag
            for row in (*ordered_morphemes, target_morpheme, stance)
            for tag in row.surface_claim_tags
        )
        risk_context = bool(
            move.action_lifecycle
            in {"intended", "reported_not_completed", "undetermined"}
            or completion_authority_conflict
            or any(
                profile.polarity in {"negative", "mixed"}
                for profile in move.target_semantic_profiles
            )
            or move.unknown_roles
            or move.self_denial_required
        )
        if (
            not surface_tags <= authority_tags
            or (
                risk_context
                and surface_tags
                & {"complete", "achievement", "value", "weight"}
            )
            or text.count(target_text) != 1
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        return text

    forbidden_reception_replays = _ordered_unique(
        tuple(
            fragment.source_fragment_text
            for root in envelope.root_bindings
            for fragment in root.source_fragments
            if fragment.source_fragment_text
        )
        + tuple(
            anchor.anchor_text
            for anchor in product_projection.visible_anchor_by_actual_owner.values()
            if anchor.anchor_text
        )
        + tuple(
            label.label for label in overlay.label_anchors if label.label
        )
        + (
            (product_projection.specificity_companion_phrase,)
            if product_projection.specificity_companion_phrase
            else ()
        )
    )

    reception_lines: list[str] = []
    for binding in envelope.reception_bindings:
        target_ids = tuple(binding.source_target_owner_ids)
        support_ids = tuple(
            value
            for value in binding.visible_support_owner_ids
            if value not in set(target_ids)
        )
        if (
            not target_ids
            or any(value not in owner_reference for value in target_ids)
            or any(value not in owner_reference for value in support_ids)
            or binding.effective_reception_act not in act_fragments
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_UNRESOLVED"
            )
        overlay_binding = overlay_reception_by_opportunity.get(
            binding.source_reception_opportunity_id
        )
        if overlay_binding is None:
            matches = tuple(
                row
                for row in overlay.reception_antecedent_bindings
                if binding.source_reception_opportunity_id
                in row.source_reception_opportunity_ids
            )
            if len(matches) != 1:
                raise Step11Cycle001ProductRecoveryError(
                    "STEP11_CYCLE001_RECOVERY_RECEPTION_SOURCE_INVALID"
                )
            overlay_binding = matches[0]
        lifecycle = str(overlay_binding.action_lifecycle)
        if lifecycle not in {
            "not_applicable",
            "reported_content",
            "undetermined",
            "intended",
            "reported_ongoing",
            "reported_not_completed",
            "reported_completed",
        }:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        action_target_ids = tuple(
            owner_id
            for owner_id in target_ids
            if str(nucleus_by_actual[owner_id].kind) == "action"
        )
        if lifecycle in {
            "intended",
            "reported_ongoing",
            "reported_not_completed",
            "reported_completed",
        } and not action_target_ids:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        target_handles = [
            antecedent_reference(owner_id) for owner_id in target_ids
        ]
        support_handles = [
            antecedent_reference(owner_id) for owner_id in support_ids
        ]
        scoped_owner_ids = {*target_ids, *support_ids}
        if binding.effective_reception_act not in {
            "hold_in_attention",
            "do_not_dismiss",
            "honor_concrete_action",
        }:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        if not str(act_fragments[binding.effective_reception_act]):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        support_role = str(overlay_binding.support_role)
        if support_role not in {
            "none",
            "source_opportunity_support",
            "source_progressive_concrete_action",
            "legacy_purpose_negation_scope_corrected_action",
        } or (support_role == "none") != (not support_ids):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_ACT_INVALID"
            )
        relation_roles: list[tuple[str, str, str]] = []
        for relation in overlay.relations:
            if not relation.required and not relation.explicit:
                continue
            from_owner = product_projection.actual_owner_by_nucleus_id[
                relation.from_nucleus_id
            ]
            to_owner = product_projection.actual_owner_by_nucleus_id[
                relation.to_nucleus_id
            ]
            if not {from_owner, to_owner} <= scoped_owner_ids:
                continue
            target_endpoints = set(target_ids) & {from_owner, to_owner}
            if not target_endpoints:
                continue
            target_role = (
                "both"
                if target_endpoints == {from_owner, to_owner}
                else "from"
                if from_owner in target_endpoints
                else "to"
            )
            relation_roles.append(
                (
                    str(relation.relation_type),
                    str(relation.relation_direction),
                    target_role,
                )
            )
        unknown_roles: list[tuple[str, str]] = []
        for unknown in overlay.unknowns:
            unknown_target_owners = {
                product_projection.actual_owner_by_nucleus_id[value]
                for value in unknown.target_nucleus_ids
                if value in product_projection.actual_owner_by_nucleus_id
            }
            unknown_context_owners = {
                product_projection.actual_owner_by_nucleus_id[value]
                for value in unknown.context_nucleus_ids
                if value in product_projection.actual_owner_by_nucleus_id
            }
            if set(target_ids) & unknown_target_owners:
                unknown_roles.append((str(unknown.unknown_type), "target"))
            elif scoped_owner_ids & unknown_context_owners:
                unknown_roles.append((str(unknown.unknown_type), "context"))
        move = _RecoveryReceptionMove(
            target_owner_ids=target_ids,
            target_references=tuple(target_handles),
            support_owner_ids=support_ids,
            support_references=tuple(support_handles),
            target_semantic_profiles=tuple(
                _RecoveryTargetSemanticProfile(
                    semantic_kind=str(nucleus_by_actual[owner_id].kind),
                    predicate_kind=str(
                        nucleus_by_actual[owner_id].source_predicate_kind
                    ),
                    source_modality=str(
                        nucleus_by_actual[owner_id].source_modality
                    ),
                    modality=str(nucleus_by_actual[owner_id].modality),
                    polarity=str(nucleus_by_actual[owner_id].polarity),
                    source_time_scope=str(
                        nucleus_by_actual[owner_id].source_time_scope
                    ),
                    referent_scope=str(
                        nucleus_by_actual[owner_id].referent_scope
                    ),
                    clause_roles=_ordered_unique(
                        tuple(
                            clause_role_by_obligation[obligation_id]
                            for obligation_id in roots_by_owner[
                                owner_id
                            ].source_obligation_ids
                            if obligation_id in clause_role_by_obligation
                        )
                    ),
                )
                for owner_id in target_ids
            ),
            effective_act=str(binding.effective_reception_act),
            action_lifecycle=lifecycle,
            relation_roles=tuple(relation_roles),
            unknown_roles=tuple(unknown_roles),
            self_denial_required=bool(
                set(target_ids) & self_evaluation_owner_ids
            ),
        )
        text = render_reception_move(move)
        if (
            any(value in text for value in ("\r", "\n"))
            or any(value in text for value in forbidden_reception_replays)
            or any(text.count(value) != 1 for value in target_handles)
            or any(text.count(value) != 1 for value in support_handles)
        ):
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_RECEPTION_TEXT_INVALID"
            )
        reception_lines.append(text)
        normalized_owners = _ordered_unique((*target_ids, *support_ids))
        units.append(
            Step11Cycle001ProductRecoveryRealizationUnit(
                line_ordinal=len(units) + 1,
                section_role="reception",
                source_unit_id=binding.source_reception_opportunity_id,
                source_atom_ids=(),
                source_owner_ids=normalized_owners,
                source_owner_dimensions=tuple(
                    (owner_id, dimensions_by_owner[owner_id])
                    for owner_id in normalized_owners
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
    roots = tuple(value.source_envelope.root_bindings)
    receptions = tuple(
        row.source_reception_opportunity_id
        for row in value.source_envelope.reception_bindings
    )
    observation_visible = result[: len(observation_units)]
    visible_root_owners = {
        owner_id
        for binding in observation_visible
        for owner_id in binding.source_owner_ids
    }
    suppressed_roots = tuple(
        root
        for root in roots
        if root.required is False
        and not root.source_obligation_ids
        and bool(root.source_fragments)
        and all(
            fragment.binding_basis
            in {
                "source_bounded_relation_credit_only_exact_range",
                "selected_label_credit_only_exact_range",
            }
            for fragment in root.source_fragments
        )
    )
    hidden_roots = tuple(
        root for root in roots if root.source_owner_id not in visible_root_owners
    )
    if {
        root.source_owner_id for root in hidden_roots
    } != {
        root.source_owner_id for root in suppressed_roots
    }:
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_VISIBLE_ROOT_COVERAGE_INVALID"
        )
    hidden_owner_ids = {root.source_owner_id for root in hidden_roots}
    visible_roots = tuple(
        root for root in roots if root.source_owner_id not in hidden_owner_ids
    )
    expected_obligations = _ordered_unique(
        tuple(
            obligation_id
            for root in visible_roots
            for obligation_id in root.source_obligation_ids
        )
    )
    expected_fragments = tuple(
        fragment.source_fragment_id
        for root in visible_roots
        for fragment in root.source_fragments
    )
    visible_obligations = _ordered_unique(
        tuple(
            obligation_id
            for binding in observation_visible
            for obligation_id in binding.source_obligation_ids
        )
    )
    visible_fragments = tuple(
        fragment_id
        for binding in observation_visible
        for fragment_id in binding.source_fragment_ids
    )
    if (
        len(visible_obligations) != len(expected_obligations)
        or set(visible_obligations) != set(expected_obligations)
        or len(visible_fragments) != len(expected_fragments)
        or set(visible_fragments) != set(expected_fragments)
        or not {root.source_owner_id for root in visible_roots}
        <= visible_root_owners
    ):
        raise Step11Cycle001ProductRecoveryError(
            "STEP11_CYCLE001_RECOVERY_VISIBLE_ROOT_COVERAGE_INVALID"
        )
    suppressed_relation_atoms = {
        row.source_atom_id
        for row in value.source_envelope.atom_bindings
        if row.semantic_family in {"relation", "semantic_link"}
        and _relation_surface_mode(row) == "suppressed"
    }
    expected_atoms = tuple(
        row.source_atom_id
        for row in value.source_envelope.atom_bindings
        if row.source_atom_id not in suppressed_relation_atoms
        and not (
            row.semantic_family == "construction"
            and set(row.source_owner_ids) <= hidden_owner_ids
        )
    )
    visible_atoms = tuple(
        atom_id
        for row in observation_visible
        for atom_id in row.source_atom_ids
    )
    if (
        tuple(row.source_unit_id for row in result[-len(receptions) :])
        != receptions
        or bool(set(visible_atoms) & suppressed_relation_atoms)
        or len(visible_atoms) != len(expected_atoms)
        or set(visible_atoms) != set(expected_atoms)
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
        product_projection = _build_product_projection(
            discourse_plans=discourse_rows,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        receptions = _reception_bindings(
            successor_snapshot=successor_snapshot,
            product_projection=product_projection,
        )
        all_atoms = _atom_bindings(
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            owner_registry=owner_registry,
            constructions=constructions,
            relations=relations,
            links=links,
            unknowns=unknowns,
        )
        atoms = _active_atom_bindings(
            all_atoms,
            product_projection=product_projection,
            successor_snapshot=successor_snapshot,
        )
        selected_atom_ids = {row.source_atom_id for row in atoms}
        constructions = tuple(
            row
            for row in constructions
            if str(row.construction_instance_id) in selected_atom_ids
        )
        relations = tuple(
            row
            for row in relations
            if str(row.experiment_relation_id) in selected_atom_ids
        )
        links = tuple(
            row
            for row in links
            if str(row.source_semantic_link_id) in selected_atom_ids
        )
        unknowns = tuple(
            row
            for row in unknowns
            if str(row.source_unknown_id) in selected_atom_ids
        )
        available_owner_ids = set(owner_registry)
        resolvable_owner_ids = {
            str(row.actual_source_id)
            for row in successor_snapshot.base_snapshot.nuclei
        }
        root_owner_ids = {
            product_projection.actual_owner_by_nucleus_id[value]
            for value in product_projection.ordered_active_nucleus_ids
        }
        if not root_owner_ids <= resolvable_owner_ids:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_ACTIVE_OWNER_UNRESOLVED"
            )
        roots = _root_bindings(
            plan=plan,
            resolver=resolver,
            semantic_restatement_witness=witness,
            successor_snapshot=successor_snapshot,
            inventory_result=inventory_result,
            active_owner_ids=root_owner_ids,
            credit_only_owner_ids=set(
                product_projection.credit_only_actual_owner_ids
            ),
        )
        essential_owner_ids = set(root_owner_ids)
        referenced_owner_ids = {
            *(owner for row in atoms for owner in row.source_owner_ids),
            *(
                owner
                for row in receptions
                for owner in (
                    *row.source_focus_owner_ids,
                    *row.source_target_owner_ids,
                    *row.visible_support_owner_ids,
                )
            ),
        }
        if not referenced_owner_ids <= essential_owner_ids:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_COVERAGE_INVALID"
            )
        if not essential_owner_ids <= available_owner_ids:
            raise Step11Cycle001ProductRecoveryError(
                "STEP11_CYCLE001_RECOVERY_OWNER_SOURCE_UNRESOLVED"
            )
        active_owner_ids = essential_owner_ids
        owners = _owner_bindings(
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
            active_owner_ids=active_owner_ids,
            role_tokens=_role_tokens(
                lexical_atom_specs=lexical_atom_specs,
                reception_bindings=receptions,
            ),
            grounded_referent_by_owner=(
                product_projection.grounded_referent_by_actual_owner
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
            source_candidate_id="nls3s11rc0036source_0000000000000000",
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
                "nls3s11rc0036source_" + source_sha256[:16]
            ),
            source_envelope_sha256=source_sha256,
        )
        final_bytes, units = _render_product(
            envelope=source,
            product_projection=product_projection,
            catalog=catalog,
            grammar=grammar,
            successor_snapshot=successor_snapshot,
            resolver=resolver,
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
            realization_plan_id="nls3s11rc0036plan_0000000000000000",
            ast_id="nls3s11rc0036ast_0000000000000000",
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
            realization_plan_id="nls3s11rc0036plan_" + plan_sha256[:16],
            ast_id=(
                "nls3s11rc0036ast_"
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
        candidate_id = _step11_rc0036_cycle001_product_quality_candidate_identity(
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
        != "nls3s11rc0036source_" + source.source_envelope_sha256[:16]
    ):
        issues.add("STEP11_CYCLE001_RECOVERY_SOURCE_ENVELOPE_INVALID")
    rendered = value.rendered_surface
    recovery_plan = value.realization_plan
    plan_sha256 = artifact_sha256(
        _plan_material(recovery_plan, include_identity=False)
    )
    expected_plan_id = "nls3s11rc0036plan_" + plan_sha256[:16]
    expected_ast_id = (
        "nls3s11rc0036ast_"
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
    expected_id = _step11_rc0036_cycle001_product_quality_candidate_identity(
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
        if not visible:
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
