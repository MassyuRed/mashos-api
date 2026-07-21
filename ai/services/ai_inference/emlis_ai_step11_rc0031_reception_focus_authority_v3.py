# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free, runtime-disconnected Reception focus authority for rc0031 B6.

The authority joins the existing Grounded response focus, the validated
experiment snapshot Reception opportunity, and the already-selected base AST
binding.  It does not render text, alter the Catalog, or connect to runtime.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any, Final, Literal

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3 import (
    GroundedLexicalRoleExperimentSnapshotSuccessor,
    validate_grounded_lexical_role_experiment_snapshot_successor,
)
from emlis_ai_grounded_observation_plan import GroundedObservationPlan
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    GroundedSemanticRestatementError,
    build_grounded_semantic_restatement_witness,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryResult,
)
from emlis_ai_step11_natural_surface_v3 import (
    Step11IntegratedReceptionAntecedentBinding,
    Step11NaturalSurfaceCandidate,
    validate_step11_natural_surface_candidate,
)


STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.rc0031_reception_focus_authority.v1"
)
STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3.step11.rc0031_reception_focus_authority."
    "20260722.v1"
)
STEP11_RC0031_RECEPTION_FOCUS_OWNER_MAX: Final = 4
_STEP11_RC0031_RECEPTION_BASE_BINDING_MAX: Final = 4

_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_RECEPTION_ACTS: Final = frozenset(
    {"do_not_dismiss", "hold_in_attention", "honor_concrete_action"}
)
_INTENDED_MODALITIES: Final = frozenset({"intended"})
_FUTURE_TEMPORAL_SCOPES: Final = frozenset(
    {"future", "present_to_future"}
)


class Step11Rc0031ReceptionFocusAuthorityError(ValueError):
    """Fail-closed error containing only a body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Step11Rc0031ReceptionFocusBinding:
    source_reception_opportunity_id: str
    source_base_binding_id: str | None
    association_basis: Literal[
        "selected_base_ast_binding",
        "unmatched_required_opportunity",
    ]
    focus_basis: Literal["grounded_response_primary_meaning"]
    source_scope: str
    source_focus_owner_ids: tuple[str, ...]
    source_target_owner_ids: tuple[str, ...]
    supporting_source_owner_ids: tuple[str, ...]
    visible_support_owner_ids: tuple[str, ...]
    grounded_reception_act: str
    inventory_reception_act: str
    effective_reception_act: str
    act_refinement_basis: Literal[
        "source_reception_act_projection",
        "intended_or_future_action_nonpromotion",
    ]
    product_rebuild_required: bool
    focus_modality_codes: tuple[str, ...]
    focus_temporal_scope_codes: tuple[str, ...]
    focus_referent_scope_codes: tuple[str, ...]
    target_modality_codes: tuple[str, ...]
    target_temporal_scope_codes: tuple[str, ...]
    target_referent_scope_codes: tuple[str, ...]
    aspect_congruent: bool
    owner_count: int


@dataclass(frozen=True, slots=True)
class Step11Rc0031ReceptionFocusAuthority:
    schema_version: str
    adapter_version: str
    source_observation_plan_sha256: str
    source_successor_snapshot_sha256: str
    bindings: tuple[Step11Rc0031ReceptionFocusBinding, ...]
    binding_count: int
    distinct_focus_binding_count: int
    aspect_refinement_count: int
    maximum_owner_count: int
    authority_sha256: str
    experimental_only: bool = True
    body_free: bool = True
    runtime_connected: bool = False


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values))


def _binding_material(
    value: Step11Rc0031ReceptionFocusBinding,
) -> dict[str, Any]:
    return {
        "source_reception_opportunity_id": (
            value.source_reception_opportunity_id
        ),
        "source_base_binding_id": value.source_base_binding_id,
        "association_basis": value.association_basis,
        "focus_basis": value.focus_basis,
        "source_scope": value.source_scope,
        "source_focus_owner_ids": list(value.source_focus_owner_ids),
        "source_target_owner_ids": list(value.source_target_owner_ids),
        "supporting_source_owner_ids": list(
            value.supporting_source_owner_ids
        ),
        "visible_support_owner_ids": list(value.visible_support_owner_ids),
        "grounded_reception_act": value.grounded_reception_act,
        "inventory_reception_act": value.inventory_reception_act,
        "effective_reception_act": value.effective_reception_act,
        "act_refinement_basis": value.act_refinement_basis,
        "product_rebuild_required": value.product_rebuild_required,
        "focus_modality_codes": list(value.focus_modality_codes),
        "focus_temporal_scope_codes": list(
            value.focus_temporal_scope_codes
        ),
        "focus_referent_scope_codes": list(
            value.focus_referent_scope_codes
        ),
        "target_modality_codes": list(value.target_modality_codes),
        "target_temporal_scope_codes": list(
            value.target_temporal_scope_codes
        ),
        "target_referent_scope_codes": list(
            value.target_referent_scope_codes
        ),
        "aspect_congruent": value.aspect_congruent,
        "owner_count": value.owner_count,
    }


def _payload(
    *,
    schema_version: str,
    adapter_version: str,
    source_observation_plan_sha256: str,
    source_successor_snapshot_sha256: str,
    bindings: Sequence[Step11Rc0031ReceptionFocusBinding],
    binding_count: int,
    distinct_focus_binding_count: int,
    aspect_refinement_count: int,
    maximum_owner_count: int,
    experimental_only: bool,
    body_free: bool,
    runtime_connected: bool,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "adapter_version": adapter_version,
        "source_observation_plan_sha256": source_observation_plan_sha256,
        "source_successor_snapshot_sha256": (
            source_successor_snapshot_sha256
        ),
        "bindings": [_binding_material(row) for row in bindings],
        "binding_count": binding_count,
        "distinct_focus_binding_count": distinct_focus_binding_count,
        "aspect_refinement_count": aspect_refinement_count,
        "maximum_owner_count": maximum_owner_count,
        "experimental_only": experimental_only,
        "body_free": body_free,
        "runtime_connected": runtime_connected,
    }


def _nucleus_aspects(
    owner_ids: Sequence[str],
    *,
    nucleus_by_actual_id: Mapping[str, Any],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    rows = tuple(nucleus_by_actual_id[owner_id] for owner_id in owner_ids)
    return (
        _ordered_unique(tuple(str(row.modality) for row in rows)),
        _ordered_unique(tuple(str(row.temporal_scope) for row in rows)),
        _ordered_unique(tuple(str(row.referent_scope) for row in rows)),
    )


def _build_step11_rc0031_reception_focus_authority(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    base_candidate: Step11NaturalSurfaceCandidate,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11Rc0031ReceptionFocusAuthority:
    base_snapshot = successor_snapshot.base_snapshot
    nuclei = tuple(base_snapshot.nuclei)
    nucleus_by_actual_id = {
        str(row.actual_source_id): row for row in nuclei
    }
    actual_by_source_id = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    if (
        len(nucleus_by_actual_id) != len(nuclei)
        or len(actual_by_source_id) != len(nuclei)
    ):
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_NUCLEUS_AUTHORITY_INVALID"
        )

    def actual_owner_id(value: Any) -> str:
        key = str(value)
        return actual_by_source_id.get(key, key)

    try:
        semantic_restatement = build_grounded_semantic_restatement_witness(
            plan, resolver
        )
    except GroundedSemanticRestatementError as exc:
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_RESTATEMENT_INVALID"
        ) from exc
    if (
        semantic_restatement.plan_binding_sha256
        != base_snapshot.semantic_restatement_plan_binding_sha256
        or semantic_restatement.witness_sha256
        != base_snapshot.source_semantic_restatement_witness_sha256
    ):
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_SOURCE_BINDING_INVALID"
        )
    units_by_parent: dict[str, tuple[str, ...]] = {}
    for unit in semantic_restatement.semantic_units:
        units_by_parent[unit.parent_nucleus_id] = (
            *units_by_parent.get(unit.parent_nucleus_id, ()),
            unit.unit_id,
        )
    focus_owner_ids = _ordered_unique(
        tuple(
            actual_owner_id(expanded_owner_id)
            for parent_owner_id in plan.response_plan.primary_nucleus_ids
            for expanded_owner_id in units_by_parent.get(
                str(parent_owner_id), (str(parent_owner_id),)
            )
        )
    )
    if (
        not focus_owner_ids
        or not set(focus_owner_ids) <= set(nucleus_by_actual_id)
    ):
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_SOURCE_UNRESOLVED"
        )

    try:
        base_bindings = base_candidate.surface_ast.reception_antecedent_bindings
    except AttributeError as exc:
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_BASE_AST_INVALID"
        ) from exc
    if (
        type(base_bindings) is not tuple
        or len(base_bindings) > _STEP11_RC0031_RECEPTION_BASE_BINDING_MAX
        or any(
            type(row) is not Step11IntegratedReceptionAntecedentBinding
            for row in base_bindings
        )
    ):
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_BASE_BINDING_INVALID"
        )
    all_opportunity_ids = {
        str(row.source_id) for row in base_snapshot.reception_opportunities
    }
    binding_by_opportunity_id: dict[str, Any] = {}
    binding_ids: set[str] = set()
    for base_binding in base_bindings:
        opportunity_ids = base_binding.source_reception_opportunity_ids
        allowed_acts = base_binding.allowed_response_acts
        binding_id = base_binding.binding_id
        if (
            type(binding_id) is not str
            or not binding_id
            or binding_id in binding_ids
            or type(opportunity_ids) is not tuple
            or len(opportunity_ids) > 1
            or any(type(value) is not str or not value for value in opportunity_ids)
            or type(allowed_acts) is not tuple
            or not allowed_acts
            or any(
                type(value) is not str or value not in _ALLOWED_RECEPTION_ACTS
                for value in allowed_acts
            )
        ):
            raise Step11Rc0031ReceptionFocusAuthorityError(
                "STEP11_RC0031_RECEPTION_FOCUS_BASE_BINDING_INVALID"
            )
        binding_ids.add(binding_id)
        for opportunity_id in opportunity_ids:
            key = str(opportunity_id)
            if key not in all_opportunity_ids:
                raise Step11Rc0031ReceptionFocusAuthorityError(
                    "STEP11_RC0031_RECEPTION_FOCUS_OPPORTUNITY_ORPHANED"
                )
            if key in binding_by_opportunity_id:
                raise Step11Rc0031ReceptionFocusAuthorityError(
                    "STEP11_RC0031_RECEPTION_FOCUS_ASSOCIATION_AMBIGUOUS"
                )
            binding_by_opportunity_id[key] = base_binding

    opportunities = tuple(
        row
        for row in base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    if not opportunities:
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_OPPORTUNITY_MISSING"
        )
    rows: list[Step11Rc0031ReceptionFocusBinding] = []
    for opportunity in opportunities:
        opportunity_id = str(opportunity.source_id)
        base_binding = binding_by_opportunity_id.get(opportunity_id)
        if base_binding is None:
            target_owner_ids = _ordered_unique(
                tuple(
                    actual_owner_id(value)
                    for value in opportunity.target_nucleus_ids
                )
            )
            supporting_owner_ids = _ordered_unique(
                tuple(
                    actual_owner_id(value)
                    for value in opportunity.support_nucleus_ids
                )
            )
            source_base_binding_id = None
            association_basis: Literal[
                "selected_base_ast_binding",
                "unmatched_required_opportunity",
            ] = "unmatched_required_opportunity"
        else:
            target_owner_ids = _ordered_unique(
                tuple(
                    actual_owner_id(value)
                    for value in base_binding.source_target_nucleus_ids
                )
            )
            supporting_owner_ids = _ordered_unique(
                tuple(
                    actual_owner_id(value)
                    for value in (
                        *base_binding.antecedent_nucleus_ids,
                        *base_binding.supporting_nucleus_ids,
                    )
                )
            )
            source_base_binding_id = str(base_binding.binding_id)
            association_basis = "selected_base_ast_binding"
        owner_ids = _ordered_unique(
            (*focus_owner_ids, *target_owner_ids, *supporting_owner_ids)
        )
        if (
            not target_owner_ids
            or not set(owner_ids) <= set(nucleus_by_actual_id)
            or len(owner_ids) > STEP11_RC0031_RECEPTION_FOCUS_OWNER_MAX
        ):
            raise Step11Rc0031ReceptionFocusAuthorityError(
                "STEP11_RC0031_RECEPTION_FOCUS_OWNER_BOUND_INVALID"
            )
        visible_support_owner_ids = tuple(
            owner_id
            for owner_id in supporting_owner_ids
            if owner_id not in set(target_owner_ids)
        )
        focus_modalities, focus_temporal, focus_referents = _nucleus_aspects(
            focus_owner_ids,
            nucleus_by_actual_id=nucleus_by_actual_id,
        )
        target_modalities, target_temporal, target_referents = (
            _nucleus_aspects(
                target_owner_ids,
                nucleus_by_actual_id=nucleus_by_actual_id,
            )
        )
        grounded_act = str(opportunity.source_reception_act)
        inventory_act = str(opportunity.reception_act)
        if (
            inventory_act not in _ALLOWED_RECEPTION_ACTS
            or not grounded_act
            or (
                base_binding is not None
                and inventory_act
                not in set(base_binding.allowed_response_acts)
            )
        ):
            raise Step11Rc0031ReceptionFocusAuthorityError(
                "STEP11_RC0031_RECEPTION_FOCUS_ACT_INVALID"
            )
        intention_aspect = bool(
            set(target_modalities) & _INTENDED_MODALITIES
            or set(target_temporal) & _FUTURE_TEMPORAL_SCOPES
        )
        if inventory_act == "honor_concrete_action" and intention_aspect:
            effective_act = "do_not_dismiss"
            act_refinement_basis: Literal[
                "source_reception_act_projection",
                "intended_or_future_action_nonpromotion",
            ] = "intended_or_future_action_nonpromotion"
        else:
            effective_act = inventory_act
            act_refinement_basis = "source_reception_act_projection"
        aspect_congruent = not (
            effective_act == "honor_concrete_action" and intention_aspect
        )
        rows.append(
            Step11Rc0031ReceptionFocusBinding(
                source_reception_opportunity_id=opportunity_id,
                source_base_binding_id=source_base_binding_id,
                association_basis=association_basis,
                focus_basis="grounded_response_primary_meaning",
                source_scope=str(opportunity.family),
                source_focus_owner_ids=focus_owner_ids,
                source_target_owner_ids=target_owner_ids,
                supporting_source_owner_ids=supporting_owner_ids,
                visible_support_owner_ids=visible_support_owner_ids,
                grounded_reception_act=grounded_act,
                inventory_reception_act=inventory_act,
                effective_reception_act=effective_act,
                act_refinement_basis=act_refinement_basis,
                product_rebuild_required=(effective_act != inventory_act),
                focus_modality_codes=focus_modalities,
                focus_temporal_scope_codes=focus_temporal,
                focus_referent_scope_codes=focus_referents,
                target_modality_codes=target_modalities,
                target_temporal_scope_codes=target_temporal,
                target_referent_scope_codes=target_referents,
                aspect_congruent=aspect_congruent,
                owner_count=len(owner_ids),
            )
        )
    bindings = tuple(
        sorted(rows, key=lambda row: row.source_reception_opportunity_id)
    )
    if (
        len(bindings) != len(opportunities)
        or len({row.source_reception_opportunity_id for row in bindings})
        != len(bindings)
        or any(not row.aspect_congruent for row in bindings)
    ):
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_INVALID"
        )
    distinct_focus_count = sum(
        bool(
            set(row.source_focus_owner_ids)
            - set(
                (
                    *row.source_target_owner_ids,
                    *row.supporting_source_owner_ids,
                )
            )
        )
        for row in bindings
    )
    aspect_refinement_count = sum(
        row.act_refinement_basis
        == "intended_or_future_action_nonpromotion"
        for row in bindings
    )
    maximum_owner_count = max((row.owner_count for row in bindings), default=0)
    payload = _payload(
        schema_version=STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_SCHEMA,
        adapter_version=(
            STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_ADAPTER_VERSION
        ),
        source_observation_plan_sha256=(
            base_snapshot.source_observation_plan_sha256
        ),
        source_successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        bindings=bindings,
        binding_count=len(bindings),
        distinct_focus_binding_count=distinct_focus_count,
        aspect_refinement_count=aspect_refinement_count,
        maximum_owner_count=maximum_owner_count,
        experimental_only=True,
        body_free=True,
        runtime_connected=False,
    )
    return Step11Rc0031ReceptionFocusAuthority(
        schema_version=STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_SCHEMA,
        adapter_version=(
            STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_ADAPTER_VERSION
        ),
        source_observation_plan_sha256=(
            base_snapshot.source_observation_plan_sha256
        ),
        source_successor_snapshot_sha256=(
            successor_snapshot.experiment_snapshot_sha256
        ),
        bindings=bindings,
        binding_count=len(bindings),
        distinct_focus_binding_count=distinct_focus_count,
        aspect_refinement_count=aspect_refinement_count,
        maximum_owner_count=maximum_owner_count,
        authority_sha256=artifact_sha256(payload),
        experimental_only=True,
        body_free=True,
        runtime_connected=False,
    )


def build_step11_rc0031_reception_focus_authority(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    base_candidate: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> Step11Rc0031ReceptionFocusAuthority:
    if type(plan) is not GroundedObservationPlan:
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_PLAN_INVALID"
        )
    if type(resolver) is not EvidenceSpanResolver:
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_RESOLVER_INVALID"
        )
    if (
        type(successor_snapshot)
        is not GroundedLexicalRoleExperimentSnapshotSuccessor
        or validate_grounded_lexical_role_experiment_snapshot_successor(
            successor_snapshot
        )
        != ()
    ):
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_SUCCESSOR_INVALID"
        )
    if (
        type(inventory_result) is not SemanticObligationInventoryResult
        or inventory_result.source_snapshot != successor_snapshot.base_snapshot
        or type(base_candidate) is not Step11NaturalSurfaceCandidate
        or validate_step11_natural_surface_candidate(
            base_candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        != ()
    ):
        raise Step11Rc0031ReceptionFocusAuthorityError(
            "STEP11_RC0031_RECEPTION_FOCUS_BASE_CANDIDATE_INVALID"
        )
    return _build_step11_rc0031_reception_focus_authority(
        plan,
        resolver,
        successor_snapshot=successor_snapshot,
        base_candidate=base_candidate,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )


def validate_step11_rc0031_reception_focus_authority(
    value: Any,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    base_candidate: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not Step11Rc0031ReceptionFocusAuthority:
        return ("STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_TYPE_INVALID",)
    try:
        expected = build_step11_rc0031_reception_focus_authority(
            plan,
            resolver,
            successor_snapshot=successor_snapshot,
            base_candidate=base_candidate,
            inventory_result=inventory_result,
            content_plan=content_plan,
            current_input=current_input,
        )
        presented_payload = _payload(
            schema_version=value.schema_version,
            adapter_version=value.adapter_version,
            source_observation_plan_sha256=(
                value.source_observation_plan_sha256
            ),
            source_successor_snapshot_sha256=(
                value.source_successor_snapshot_sha256
            ),
            bindings=value.bindings,
            binding_count=value.binding_count,
            distinct_focus_binding_count=(
                value.distinct_focus_binding_count
            ),
            aspect_refinement_count=value.aspect_refinement_count,
            maximum_owner_count=value.maximum_owner_count,
            experimental_only=value.experimental_only,
            body_free=value.body_free,
            runtime_connected=value.runtime_connected,
        )
    except (
        AttributeError,
        KeyError,
        Step11Rc0031ReceptionFocusAuthorityError,
        TypeError,
        ValueError,
    ):
        return ("STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_REBUILD_FAILED",)
    issues: set[str] = set()
    if value != expected:
        issues.add("STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_MISMATCH")
    if (
        type(value.authority_sha256) is not str
        or not _SHA256_RE.fullmatch(value.authority_sha256)
        or value.authority_sha256 != artifact_sha256(presented_payload)
    ):
        issues.add("STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_HASH_MISMATCH")
    if (
        value.experimental_only is not True
        or value.body_free is not True
        or value.runtime_connected is not False
    ):
        issues.add("STEP11_RC0031_RECEPTION_FOCUS_BOUNDARY_INVALID")
    return tuple(sorted(issues))


def step11_rc0031_reception_focus_authority_material(
    value: Step11Rc0031ReceptionFocusAuthority,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    successor_snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    base_candidate: Any,
    inventory_result: SemanticObligationInventoryResult,
    content_plan: Mapping[str, Any],
    current_input: Mapping[str, Any],
) -> dict[str, Any]:
    issues = validate_step11_rc0031_reception_focus_authority(
        value,
        plan=plan,
        resolver=resolver,
        successor_snapshot=successor_snapshot,
        base_candidate=base_candidate,
        inventory_result=inventory_result,
        content_plan=content_plan,
        current_input=current_input,
    )
    if issues:
        raise Step11Rc0031ReceptionFocusAuthorityError(issues[0])
    return {
        **_payload(
            schema_version=value.schema_version,
            adapter_version=value.adapter_version,
            source_observation_plan_sha256=(
                value.source_observation_plan_sha256
            ),
            source_successor_snapshot_sha256=(
                value.source_successor_snapshot_sha256
            ),
            bindings=value.bindings,
            binding_count=value.binding_count,
            distinct_focus_binding_count=(
                value.distinct_focus_binding_count
            ),
            aspect_refinement_count=value.aspect_refinement_count,
            maximum_owner_count=value.maximum_owner_count,
            experimental_only=value.experimental_only,
            body_free=value.body_free,
            runtime_connected=value.runtime_connected,
        ),
        "authority_sha256": value.authority_sha256,
    }


__all__ = [
    "STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_ADAPTER_VERSION",
    "STEP11_RC0031_RECEPTION_FOCUS_AUTHORITY_SCHEMA",
    "STEP11_RC0031_RECEPTION_FOCUS_OWNER_MAX",
    "Step11Rc0031ReceptionFocusAuthority",
    "Step11Rc0031ReceptionFocusAuthorityError",
    "Step11Rc0031ReceptionFocusBinding",
    "build_step11_rc0031_reception_focus_authority",
    "step11_rc0031_reception_focus_authority_material",
    "validate_step11_rc0031_reception_focus_authority",
]
