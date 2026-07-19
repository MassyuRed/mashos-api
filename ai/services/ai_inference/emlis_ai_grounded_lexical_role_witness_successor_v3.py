# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free lexical-role successor for the rc0028 E1b experiment.

The witness consumes only the frozen Grounded Plan, request-local evidence
resolver, and the separate relation/construction authority successor.  Facet
presence is deliberately not semantic coverage and cannot certify it.
"""

from dataclasses import dataclass, replace
import re
from typing import Any, Final, Literal

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import GroundedObservationPlan
from emlis_ai_grounded_relation_construction_authority_successor_v3 import (
    GroundedRelationConstructionAuthoritySuccessorError,
    build_grounded_relation_construction_authority_successor,
    validate_grounded_relation_construction_authority_successor,
)
from emlis_ai_nls_v3_artifact_contract import artifact_sha256


GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_witness."
    "rc0028.experiment.v2"
)
GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_adapter.20260719.v2"
)
MAX_LEXICAL_ROLES_PER_REQUIRED_TEXT_NUCLEUS: Final = 6

_TEXT_SOURCE_FIELDS: Final = frozenset({"memo", "memo_action"})
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_INTERNAL_LINK_BY_CONSTRUCTION: Final = {
    "comparative_assessment": "qualifies",
    "particle_object": "qualifies",
    "choice_uncertainty": "limits",
    "decision_timing": "limits",
    "purpose_action": "qualifies",
    "explicit_contrast": "contrast",
    "ordered_sequence": "precedes",
    "reported_self_assessment": "qualifies",
    "explicit_coexistence": "coexistence",
    "parallel_addition": "coexistence",
    "nonreduction_boundary": "limits",
    "withheld_action": "precedes",
    "balanced_consideration": "coexistence",
}


class GroundedLexicalRoleSuccessorError(ValueError):
    """Fail-closed error whose message is a body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class GroundedLexicalRoleFacetSuccessor:
    facet_id: str
    construction_slot_id: str
    source_owner_id: str
    parent_nucleus_id: str
    source_span_id: str
    source_field_role: Literal["thought", "action"]
    start_index: int
    end_index: int
    lexical_role_kind: str
    construction_code: str
    construction_position: str
    lexical_internal_link: str
    participation_ids: tuple[str, ...]
    visible_authority: Literal["feature_only"] = "feature_only"
    required: bool = True


@dataclass(frozen=True)
class GroundedLexicalRelationEndpointBindingSuccessor:
    relation_id: str
    source_relation_id: str
    relation_endpoint_role: Literal["from", "to"]
    source_owner_id: str
    relation_direction: Literal["source_to_target", "bidirectional"]
    effective_relation_type: str
    required: bool


@dataclass(frozen=True)
class GroundedLexicalRoleWitnessSuccessor:
    schema_version: str
    adapter_version: str
    source_relation_construction_authority_sha256: str
    facets: tuple[GroundedLexicalRoleFacetSuccessor, ...]
    required_text_parent_count: int
    adapted_source_owner_ids: tuple[str, ...]
    relation_authorities: tuple[Any, ...]
    relation_endpoint_bindings: tuple[
        GroundedLexicalRelationEndpointBindingSuccessor, ...
    ]
    semantic_link_bindings: tuple[Any, ...]
    explicit_unknown_bindings: tuple[Any, ...]
    facet_present_required_nucleus_ids: tuple[str, ...]
    facet_absent_required_nucleus_ids: tuple[str, ...]
    unresolved_owner_reasons: tuple[tuple[str, str], ...]
    semantic_coverage_authority: Literal["none"]
    resource_bound: int
    witness_sha256: str
    experimental_only: bool = True
    body_free: bool = True
    runtime_connected: bool = False


def _required_text_nucleus_ids(plan: GroundedObservationPlan) -> tuple[str, ...]:
    required = frozenset(plan.coverage_requirements.required_nucleus_ids)
    return tuple(
        row.nucleus_id
        for row in plan.nuclei
        if row.nucleus_id in required
        and set(row.source_fields) <= _TEXT_SOURCE_FIELDS
    )


def _facet_material(row: GroundedLexicalRoleFacetSuccessor) -> dict[str, Any]:
    return {
        "facet_id": row.facet_id,
        "construction_slot_id": row.construction_slot_id,
        "source_owner_id": row.source_owner_id,
        "parent_nucleus_id": row.parent_nucleus_id,
        "source_span_id": row.source_span_id,
        "source_field_role": row.source_field_role,
        "lexical_role_kind": row.lexical_role_kind,
        "construction_code": row.construction_code,
        "construction_position": row.construction_position,
        "lexical_internal_link": row.lexical_internal_link,
        "participation_ids": list(row.participation_ids),
        "visible_authority": row.visible_authority,
        "required": row.required,
    }


def _relation_material(row: Any) -> dict[str, Any]:
    # Marker offsets remain request-local inside the authority owner.  The
    # witness exposes only its commitment and semantic topology.
    return {
        "experiment_relation_id": row.experiment_relation_id,
        "authority_basis": row.authority_basis,
        "source_relation_id": row.source_relation_id,
        "refines_source_relation_id": row.refines_source_relation_id,
        "source_relation_type": row.source_relation_type,
        "effective_relation_type": row.effective_relation_type,
        "source_grounding_kind": row.source_grounding_kind,
        "source_retention": row.source_retention,
        "from_source_owner_id": row.from_source_owner_id,
        "to_source_owner_id": row.to_source_owner_id,
        "direction": row.direction,
        "experiment_retention": row.experiment_retention,
        "evidence_alias_ids": list(row.evidence_alias_ids),
        "marker_code": row.marker_code,
    }


def _endpoint_material(
    row: GroundedLexicalRelationEndpointBindingSuccessor,
) -> dict[str, Any]:
    return {
        "relation_id": row.relation_id,
        "source_relation_id": row.source_relation_id,
        "relation_endpoint_role": row.relation_endpoint_role,
        "source_owner_id": row.source_owner_id,
        "relation_direction": row.relation_direction,
        "effective_relation_type": row.effective_relation_type,
        "required": row.required,
    }


def _semantic_link_material(row: Any) -> dict[str, Any]:
    return {
        "source_semantic_link_id": row.source_semantic_link_id,
        "source_span_id": row.source_span_id,
        "relation_type": row.relation_type,
        "direction": row.direction,
        "from_semantic_unit_id": row.from_semantic_unit_id,
        "to_semantic_unit_id": row.to_semantic_unit_id,
        "required": row.required,
    }


def _unknown_material(row: Any) -> dict[str, Any]:
    return {
        "source_unknown_id": row.source_unknown_id,
        "dimension": row.dimension,
        "source_span_id": row.source_span_id,
        "affected_source_owner_ids": [
            item.owner_id for item in row.affected_source_owners
        ],
        "lexical_role_kind": row.lexical_role_kind,
        "required": row.required,
    }


def _payload(
    *,
    schema_version: str,
    adapter_version: str,
    source_relation_construction_authority_sha256: str,
    facets: tuple[GroundedLexicalRoleFacetSuccessor, ...],
    required_text_parent_count: int,
    adapted_source_owner_ids: tuple[str, ...],
    relation_authorities: tuple[Any, ...],
    relation_endpoint_bindings: tuple[
        GroundedLexicalRelationEndpointBindingSuccessor, ...
    ],
    semantic_link_bindings: tuple[Any, ...],
    explicit_unknown_bindings: tuple[Any, ...],
    facet_present_required_nucleus_ids: tuple[str, ...],
    facet_absent_required_nucleus_ids: tuple[str, ...],
    unresolved_owner_reasons: tuple[tuple[str, str], ...],
    semantic_coverage_authority: str,
    resource_bound: int,
    experimental_only: bool,
    body_free: bool,
    runtime_connected: bool,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "adapter_version": adapter_version,
        "source_relation_construction_authority_sha256": (
            source_relation_construction_authority_sha256
        ),
        "facets": [_facet_material(row) for row in facets],
        "required_text_parent_count": required_text_parent_count,
        "adapted_source_owner_ids": list(adapted_source_owner_ids),
        "relation_authorities": [
            _relation_material(row) for row in relation_authorities
        ],
        "relation_endpoint_bindings": [
            _endpoint_material(row) for row in relation_endpoint_bindings
        ],
        "semantic_link_bindings": [
            _semantic_link_material(row) for row in semantic_link_bindings
        ],
        "explicit_unknown_bindings": [
            _unknown_material(row) for row in explicit_unknown_bindings
        ],
        "facet_present_required_nucleus_ids": list(
            facet_present_required_nucleus_ids
        ),
        "facet_absent_required_nucleus_ids": list(
            facet_absent_required_nucleus_ids
        ),
        "unresolved_owner_reasons": [
            [owner_id, reason] for owner_id, reason in unresolved_owner_reasons
        ],
        "semantic_coverage_authority": semantic_coverage_authority,
        "resource_bound": resource_bound,
        "experimental_only": experimental_only,
        "body_free": body_free,
        "runtime_connected": runtime_connected,
    }


def _presented_payload(value: GroundedLexicalRoleWitnessSuccessor) -> dict[str, Any]:
    return _payload(
        schema_version=value.schema_version,
        adapter_version=value.adapter_version,
        source_relation_construction_authority_sha256=(
            value.source_relation_construction_authority_sha256
        ),
        facets=value.facets,
        required_text_parent_count=value.required_text_parent_count,
        adapted_source_owner_ids=value.adapted_source_owner_ids,
        relation_authorities=value.relation_authorities,
        relation_endpoint_bindings=value.relation_endpoint_bindings,
        semantic_link_bindings=value.semantic_link_bindings,
        explicit_unknown_bindings=value.explicit_unknown_bindings,
        facet_present_required_nucleus_ids=(
            value.facet_present_required_nucleus_ids
        ),
        facet_absent_required_nucleus_ids=(
            value.facet_absent_required_nucleus_ids
        ),
        unresolved_owner_reasons=value.unresolved_owner_reasons,
        semantic_coverage_authority=value.semantic_coverage_authority,
        resource_bound=value.resource_bound,
        experimental_only=value.experimental_only,
        body_free=value.body_free,
        runtime_connected=value.runtime_connected,
    )


def _hash_payload(
    value: GroundedLexicalRoleWitnessSuccessor,
) -> dict[str, Any]:
    """Private commitment payload; exact ranges are not materialized."""

    return {
        **_presented_payload(value),
        "private_facet_range_commitments": [
            artifact_sha256(
                {
                    "domain": "rc0028.successor.facet.range.v1",
                    "construction_slot_id": row.construction_slot_id,
                    "source_owner_id": row.source_owner_id,
                    "source_span_id": row.source_span_id,
                    "start": row.start_index,
                    "end": row.end_index,
                }
            )
            for row in value.facets
        ],
    }


def build_grounded_lexical_role_witness_successor(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> GroundedLexicalRoleWitnessSuccessor:
    try:
        authority = build_grounded_relation_construction_authority_successor(
            plan, resolver
        )
        authority_issues = validate_grounded_relation_construction_authority_successor(
            authority, plan=plan, resolver=resolver
        )
    except GroundedRelationConstructionAuthoritySuccessorError as exc:
        raise GroundedLexicalRoleSuccessorError(
            "LEXICAL_ROLE_SUCCESSOR_AUTHORITY_BUILD_FAILED"
        ) from exc
    if authority_issues:
        raise GroundedLexicalRoleSuccessorError(
            "LEXICAL_ROLE_SUCCESSOR_AUTHORITY_BUILD_FAILED"
        )

    instance_by_id = {
        row.construction_instance_id: row
        for row in authority.construction_instances
    }
    facets = tuple(
        GroundedLexicalRoleFacetSuccessor(
            facet_id="lexical_successor_facet:" + row.construction_slot_id,
            construction_slot_id=row.construction_slot_id,
            source_owner_id=row.construction_instance_id,
            parent_nucleus_id=(
                instance_by_id[row.construction_instance_id].parent_nucleus_id
            ),
            source_span_id=row.source_span_id,
            source_field_role=row.source_field_role,
            start_index=row.slot_start_index,
            end_index=row.slot_end_index,
            lexical_role_kind=row.lexical_role_kind,
            construction_code=(
                instance_by_id[row.construction_instance_id].construction_code
            ),
            construction_position=row.construction_position,
            lexical_internal_link=_INTERNAL_LINK_BY_CONSTRUCTION[
                instance_by_id[row.construction_instance_id].construction_code
            ],
            participation_ids=row.participation_ids,
        )
        for row in authority.construction_slots
    )
    endpoint_bindings = tuple(
        binding
        for relation in authority.relation_authorities
        for binding in (
            GroundedLexicalRelationEndpointBindingSuccessor(
                relation_id=relation.experiment_relation_id,
                source_relation_id=relation.source_relation_id,
                relation_endpoint_role="from",
                source_owner_id=relation.from_source_owner_id,
                relation_direction=relation.direction,
                effective_relation_type=relation.effective_relation_type,
                required=relation.source_retention == "required",
            ),
            GroundedLexicalRelationEndpointBindingSuccessor(
                relation_id=relation.experiment_relation_id,
                source_relation_id=relation.source_relation_id,
                relation_endpoint_role="to",
                source_owner_id=relation.to_source_owner_id,
                relation_direction=relation.direction,
                effective_relation_type=relation.effective_relation_type,
                required=relation.source_retention == "required",
            ),
        )
    )
    required_ids = _required_text_nucleus_ids(plan)
    present_set = {
        row.parent_nucleus_id for row in authority.construction_instances
    } & set(required_ids)
    present = tuple(row for row in required_ids if row in present_set)
    absent = tuple(row for row in required_ids if row not in present_set)
    unresolved = tuple(
        (owner_id, "LEXICAL_ROLE_NO_CLOSED_CONSTRUCTION")
        for owner_id in absent
    )
    adapted_owner_ids = tuple(
        sorted(
            {
                row.target_owner_id
                for row in authority.source_owner_participations
            }
        )
    )
    resource_bound = (
        MAX_LEXICAL_ROLES_PER_REQUIRED_TEXT_NUCLEUS * len(required_ids)
    )
    provisional = GroundedLexicalRoleWitnessSuccessor(
        schema_version=GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_SCHEMA,
        adapter_version=GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_ADAPTER_VERSION,
        source_relation_construction_authority_sha256=authority.authority_sha256,
        facets=facets,
        required_text_parent_count=len(required_ids),
        adapted_source_owner_ids=adapted_owner_ids,
        relation_authorities=authority.relation_authorities,
        relation_endpoint_bindings=endpoint_bindings,
        semantic_link_bindings=authority.semantic_link_bindings,
        explicit_unknown_bindings=authority.explicit_unknown_authorities,
        facet_present_required_nucleus_ids=present,
        facet_absent_required_nucleus_ids=absent,
        unresolved_owner_reasons=unresolved,
        semantic_coverage_authority="none",
        resource_bound=resource_bound,
        witness_sha256="0" * 64,
        experimental_only=True,
        body_free=True,
        runtime_connected=False,
    )
    # The published material contains only the final witness commitment; the
    # private range commitments used here never cross the material boundary.
    return replace(
        provisional,
        witness_sha256=artifact_sha256(_hash_payload(provisional)),
    )


def validate_grounded_lexical_role_witness_successor(
    value: Any,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    if type(value) is not GroundedLexicalRoleWitnessSuccessor:
        return ("LEXICAL_ROLE_SUCCESSOR_TYPE_INVALID",)
    try:
        expected = build_grounded_lexical_role_witness_successor(plan, resolver)
    except (AttributeError, GroundedLexicalRoleSuccessorError, TypeError, ValueError):
        return ("LEXICAL_ROLE_SUCCESSOR_REBUILD_FAILED",)

    issues: list[str] = []
    if (
        value.schema_version != expected.schema_version
        or value.adapter_version != expected.adapter_version
        or value.experimental_only is not True
        or value.body_free is not True
        or value.runtime_connected is not False
    ):
        issues.append("LEXICAL_ROLE_SUCCESSOR_CONTRACT_MISMATCH")
    if value.relation_authorities != expected.relation_authorities:
        issues.append("LEXICAL_ROLE_RELATION_AUTHORITIES_MISMATCH")
    if value.relation_endpoint_bindings != expected.relation_endpoint_bindings:
        issues.append("LEXICAL_ROLE_RELATION_ENDPOINT_BINDINGS_MISMATCH")
    if value.semantic_link_bindings != expected.semantic_link_bindings:
        issues.append("LEXICAL_ROLE_SEMANTIC_LINK_BINDINGS_MISMATCH")
    if value.explicit_unknown_bindings != expected.explicit_unknown_bindings:
        issues.append("LEXICAL_ROLE_EXPLICIT_UNKNOWN_BINDINGS_MISMATCH")
    if value.facets != expected.facets:
        issues.append("LEXICAL_ROLE_SUCCESSOR_FACETS_MISMATCH")
    if (
        value.facet_present_required_nucleus_ids
        != expected.facet_present_required_nucleus_ids
        or value.facet_absent_required_nucleus_ids
        != expected.facet_absent_required_nucleus_ids
    ):
        issues.append("LEXICAL_ROLE_FACET_PARTITION_MISMATCH")
    if value.semantic_coverage_authority != "none":
        issues.append("LEXICAL_ROLE_SEMANTIC_COVERAGE_SELF_CLAIM_FORBIDDEN")
    if (
        value.required_text_parent_count != expected.required_text_parent_count
        or value.resource_bound != expected.resource_bound
        or len(value.facets) > value.resource_bound
    ):
        issues.append("LEXICAL_ROLE_SUCCESSOR_RESOURCE_BOUND_MISMATCH")
    if (
        value.adapted_source_owner_ids != expected.adapted_source_owner_ids
        or value.unresolved_owner_reasons != expected.unresolved_owner_reasons
        or value.source_relation_construction_authority_sha256
        != expected.source_relation_construction_authority_sha256
    ):
        issues.append("LEXICAL_ROLE_SUCCESSOR_OWNER_BINDINGS_MISMATCH")
    try:
        presented_hash = artifact_sha256(_hash_payload(value))
    except (AttributeError, TypeError, ValueError):
        presented_hash = ""
    if (
        type(value.witness_sha256) is not str
        or not _SHA256_RE.fullmatch(value.witness_sha256)
        or value.witness_sha256 != presented_hash
        or value.witness_sha256 != expected.witness_sha256
    ):
        issues.append("LEXICAL_ROLE_SUCCESSOR_WITNESS_HASH_MISMATCH")
    return tuple(sorted(set(issues)))


def grounded_lexical_role_witness_successor_material(
    value: GroundedLexicalRoleWitnessSuccessor,
    *,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> dict[str, Any]:
    issues = validate_grounded_lexical_role_witness_successor(
        value, plan=plan, resolver=resolver
    )
    if issues:
        raise GroundedLexicalRoleSuccessorError(issues[0])
    return {**_presented_payload(value), "witness_sha256": value.witness_sha256}


__all__ = [
    "GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_ADAPTER_VERSION",
    "GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_SCHEMA",
    "MAX_LEXICAL_ROLES_PER_REQUIRED_TEXT_NUCLEUS",
    "GroundedLexicalRelationEndpointBindingSuccessor",
    "GroundedLexicalRoleFacetSuccessor",
    "GroundedLexicalRoleSuccessorError",
    "GroundedLexicalRoleWitnessSuccessor",
    "build_grounded_lexical_role_witness_successor",
    "grounded_lexical_role_witness_successor_material",
    "validate_grounded_lexical_role_witness_successor",
]
