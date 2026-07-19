# -*- coding: utf-8 -*-
from __future__ import annotations

"""Runtime-disconnected rc0028 successor experiment snapshot.

The active Step 4 snapshot and every Step 9 owner remain unchanged.  This
module binds their ordinary body-free snapshot to the experiment-only
relation/construction authority and lexical-role successor.  A private,
request-local origin capability is required for validation; it is never
serialized into the returned material.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
import re
from typing import Any, Final
import weakref

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_lexical_role_witness_successor_v3 import (
    GroundedLexicalRoleSuccessorError,
    GroundedLexicalRoleWitnessSuccessor,
    build_grounded_lexical_role_witness_successor,
    validate_grounded_lexical_role_witness_successor,
)
from emlis_ai_grounded_observation_plan import GroundedObservationPlan
from emlis_ai_grounded_relation_construction_authority_successor_v3 import (
    GroundedRelationConstructionAuthoritySuccessor,
    GroundedRelationConstructionAuthoritySuccessorError,
    build_grounded_relation_construction_authority_successor,
    validate_grounded_relation_construction_authority_successor,
)
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
    canonical_json_bytes,
    load_canonical_json_bytes,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    GroundedSourceSnapshot,
    SemanticObligationInventoryError,
    build_grounded_source_snapshot,
)


GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_experiment_snapshot."
    "rc0028.experiment.v2"
)
GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_experiment_snapshot_adapter."
    "20260719.v2"
)

_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_BASE_COMMITMENT_FIELDS: Final = (
    "source_observation_plan_sha256",
    "source_observation_stage_context_sha256",
    "source_reception_opportunity_plan_sha256",
    "response_eligibility_source_sha256",
    "source_policy_sha256",
    "source_semantic_restatement_witness_sha256",
)


class GroundedLexicalRoleExperimentSnapshotSuccessorError(ValueError):
    """Fail-closed error whose message is a body-free machine code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _body_free_projection(value: Any) -> Any:
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        return format(value, ".17g")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "dataclass_type": type(value).__name__,
            "fields": {
                row.name: _body_free_projection(getattr(value, row.name))
                for row in fields(value)
            },
        }
    if type(value) in {tuple, list}:
        return [_body_free_projection(item) for item in value]
    if type(value) in {set, frozenset}:
        return sorted(
            (_body_free_projection(item) for item in value),
            key=canonical_json_bytes,
        )
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
                "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_PROJECTION_INVALID"
            )
        return {
            key: _body_free_projection(value[key])
            for key in sorted(value)
        }
    raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
        "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_PROJECTION_INVALID"
    )


def _base_commitments(
    snapshot: GroundedSourceSnapshot,
) -> tuple[tuple[str, str | None], ...]:
    if type(snapshot) is not GroundedSourceSnapshot:
        raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
            "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_BASE_SNAPSHOT_INVALID"
        )
    return tuple((name, getattr(snapshot, name)) for name in _BASE_COMMITMENT_FIELDS)


def _base_snapshot_sha256(snapshot: GroundedSourceSnapshot) -> str:
    return artifact_sha256(
        {
            "commitment_kind": "unchanged_grounded_source_snapshot",
            "snapshot": _body_free_projection(snapshot),
        }
    )


@dataclass(frozen=True)
class GroundedLexicalRoleExperimentSnapshotSuccessor:
    """Separate v2 experiment wrapper; never an active Step 4 owner."""

    schema_version: str
    adapter_version: str
    base_snapshot: GroundedSourceSnapshot
    base_snapshot_sha256: str
    base_source_commitments: tuple[tuple[str, str | None], ...]
    relation_construction_authority: GroundedRelationConstructionAuthoritySuccessor
    source_relation_construction_authority_sha256: str
    lexical_role_witness: GroundedLexicalRoleWitnessSuccessor
    source_lexical_role_witness_sha256: str
    semantic_coverage_authorized: bool
    runtime_connected: bool
    experiment_snapshot_sha256: str
    experimental_only: bool = True
    body_free: bool = True

    def __deepcopy__(
        self,
        memo: dict[int, Any],
    ) -> "GroundedLexicalRoleExperimentSnapshotSuccessor":
        # Identity preserves the module-owned request-local origin capability.
        return self


def _payload(
    *,
    schema_version: str,
    adapter_version: str,
    base_snapshot_sha256: str,
    base_source_commitments: tuple[tuple[str, str | None], ...],
    source_relation_construction_authority_sha256: str,
    source_lexical_role_witness_sha256: str,
    semantic_coverage_authorized: bool,
    runtime_connected: bool,
    experimental_only: bool,
    body_free: bool,
) -> dict[str, Any]:
    # Only commitments cross the material boundary.  In particular, the
    # authority's request-local marker ranges are intentionally absent.
    return {
        "schema_version": schema_version,
        "adapter_version": adapter_version,
        "base_snapshot_sha256": base_snapshot_sha256,
        "base_source_commitments": [
            [name, value] for name, value in base_source_commitments
        ],
        "source_relation_construction_authority_sha256": (
            source_relation_construction_authority_sha256
        ),
        "source_lexical_role_witness_sha256": source_lexical_role_witness_sha256,
        "semantic_coverage_authorized": semantic_coverage_authorized,
        "runtime_connected": runtime_connected,
        "experimental_only": experimental_only,
        "body_free": body_free,
    }


def _presented_payload(
    value: GroundedLexicalRoleExperimentSnapshotSuccessor,
) -> dict[str, Any]:
    return _payload(
        schema_version=value.schema_version,
        adapter_version=value.adapter_version,
        base_snapshot_sha256=value.base_snapshot_sha256,
        base_source_commitments=value.base_source_commitments,
        source_relation_construction_authority_sha256=(
            value.source_relation_construction_authority_sha256
        ),
        source_lexical_role_witness_sha256=(
            value.source_lexical_role_witness_sha256
        ),
        semantic_coverage_authorized=value.semantic_coverage_authorized,
        runtime_connected=value.runtime_connected,
        experimental_only=value.experimental_only,
        body_free=value.body_free,
    )


@dataclass(frozen=True, slots=True, repr=False)
class _SuccessorExperimentOrigin:
    plan: GroundedObservationPlan
    evidence_spans: tuple[Any, ...]
    observation_stage_context_bytes: bytes
    original_input_bundle_bytes: bytes
    trusted_future_authority: TrustedFutureStageAuthority | None
    supplemental_answer_bundle_bytes: bytes

    @classmethod
    def from_sources(
        cls,
        *,
        plan: GroundedObservationPlan,
        resolver: EvidenceSpanResolver,
        observation_stage_context: Mapping[str, Any],
        original_input_bundle: Any,
        trusted_future_authority: TrustedFutureStageAuthority | None,
        supplemental_answer_bundle: Any | None,
    ) -> "_SuccessorExperimentOrigin":
        return cls(
            plan=plan,
            evidence_spans=tuple(
                resolver.resolve(span_id) for span_id in resolver.span_ids
            ),
            observation_stage_context_bytes=(
                canonical_json_bytes(dict(observation_stage_context)) + b"\n"
            ),
            original_input_bundle_bytes=(
                canonical_json_bytes(original_input_bundle) + b"\n"
            ),
            trusted_future_authority=trusted_future_authority,
            supplemental_answer_bundle_bytes=(
                canonical_json_bytes(supplemental_answer_bundle) + b"\n"
            ),
        )

    def __repr__(self) -> str:
        return "<_SuccessorExperimentOrigin request_local>"

    def rebuild(self) -> "GroundedLexicalRoleExperimentSnapshotSuccessor":
        return build_grounded_lexical_role_experiment_snapshot_successor(
            self.plan,
            EvidenceSpanResolver(self.evidence_spans),
            observation_stage_context=load_canonical_json_bytes(
                self.observation_stage_context_bytes
            ),
            original_input_bundle=load_canonical_json_bytes(
                self.original_input_bundle_bytes
            ),
            trusted_future_authority=self.trusted_future_authority,
            supplemental_answer_bundle=load_canonical_json_bytes(
                self.supplemental_answer_bundle_bytes
            ),
            _register_origin=False,
        )


def _origin_capability_store():
    registry: dict[
        int,
        tuple[
            weakref.ReferenceType[GroundedLexicalRoleExperimentSnapshotSuccessor],
            _SuccessorExperimentOrigin,
        ],
    ] = {}

    def register(
        snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
        origin: _SuccessorExperimentOrigin,
    ) -> None:
        try:
            expected = origin.rebuild()
        except (
            AttributeError,
            GroundedLexicalRoleSuccessorError,
            GroundedRelationConstructionAuthoritySuccessorError,
            KeyError,
            SemanticObligationInventoryError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as exc:
            raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
                "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_ORIGIN_REGISTRATION_INVALID"
            ) from exc
        if snapshot != expected:
            raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
                "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_ORIGIN_REGISTRATION_MISMATCH"
            )
        key = id(snapshot)

        def remove(reference: Any, *, registry_key: int = key) -> None:
            current = registry.get(registry_key)
            if current is not None and current[0] is reference:
                registry.pop(registry_key, None)

        reference = weakref.ref(snapshot, remove)
        registry[key] = (reference, origin)

    def validate(
        snapshot: GroundedLexicalRoleExperimentSnapshotSuccessor,
    ) -> tuple[str, ...]:
        current = registry.get(id(snapshot))
        if current is None or current[0]() is not snapshot:
            return ("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_ORIGIN_AUTHORITY_REQUIRED",)
        try:
            expected = current[1].rebuild()
        except (
            AttributeError,
            GroundedLexicalRoleSuccessorError,
            GroundedRelationConstructionAuthoritySuccessorError,
            KeyError,
            SemanticObligationInventoryError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            return ("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_ORIGIN_REVALIDATION_FAILED",)
        if snapshot != expected:
            return ("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_ORIGIN_REBIND_MISMATCH",)
        return ()

    return register, validate


_register_experiment_origin, _validate_experiment_origin = (
    _origin_capability_store()
)


def _structural_issues(
    value: GroundedLexicalRoleExperimentSnapshotSuccessor,
) -> tuple[str, ...]:
    issues: list[str] = []
    if (
        value.schema_version
        != GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_SCHEMA
        or value.adapter_version
        != GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_ADAPTER_VERSION
        or value.experimental_only is not True
        or value.body_free is not True
    ):
        issues.append("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_CONTRACT_MISMATCH")
    if value.semantic_coverage_authorized is not False:
        issues.append("LEXICAL_ROLE_SEMANTIC_COVERAGE_SELF_CLAIM_FORBIDDEN")
    if value.runtime_connected is not False:
        issues.append("LEXICAL_ROLE_SUCCESSOR_RUNTIME_CONNECTION_FORBIDDEN")

    if type(value.base_snapshot) is not GroundedSourceSnapshot:
        issues.append("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_BASE_SNAPSHOT_INVALID")
    else:
        try:
            expected_base_hash = _base_snapshot_sha256(value.base_snapshot)
            expected_commitments = _base_commitments(value.base_snapshot)
        except (AttributeError, TypeError, ValueError):
            expected_base_hash = ""
            expected_commitments = ()
        if value.base_snapshot_sha256 != expected_base_hash:
            issues.append("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_BASE_HASH_MISMATCH")
        if value.base_source_commitments != expected_commitments:
            issues.append(
                "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_BASE_COMMITMENTS_MISMATCH"
            )

    authority = value.relation_construction_authority
    if type(authority) is not GroundedRelationConstructionAuthoritySuccessor:
        issues.append("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_AUTHORITY_INVALID")
    elif (
        type(value.source_relation_construction_authority_sha256) is not str
        or not _SHA256_RE.fullmatch(
            value.source_relation_construction_authority_sha256
        )
        or value.source_relation_construction_authority_sha256
        != authority.authority_sha256
    ):
        issues.append(
            "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_AUTHORITY_COMMITMENT_MISMATCH"
        )

    witness = value.lexical_role_witness
    if type(witness) is not GroundedLexicalRoleWitnessSuccessor:
        issues.append("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_WITNESS_INVALID")
    elif (
        type(value.source_lexical_role_witness_sha256) is not str
        or not _SHA256_RE.fullmatch(value.source_lexical_role_witness_sha256)
        or value.source_lexical_role_witness_sha256 != witness.witness_sha256
    ):
        issues.append(
            "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_WITNESS_COMMITMENT_MISMATCH"
        )

    try:
        expected_hash = artifact_sha256(_presented_payload(value))
    except (AttributeError, TypeError, ValueError):
        expected_hash = ""
    if (
        type(value.experiment_snapshot_sha256) is not str
        or not _SHA256_RE.fullmatch(value.experiment_snapshot_sha256)
        or value.experiment_snapshot_sha256 != expected_hash
    ):
        issues.append("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_HASH_MISMATCH")
    return tuple(sorted(set(issues)))


def build_grounded_lexical_role_experiment_snapshot_successor(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    observation_stage_context: Mapping[str, Any],
    original_input_bundle: Any,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
    _register_origin: bool = True,
) -> GroundedLexicalRoleExperimentSnapshotSuccessor:
    if type(resolver) is not EvidenceSpanResolver:
        raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
            "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_RESOLVER_INVALID"
        )
    try:
        base_snapshot = build_grounded_source_snapshot(
            plan,
            resolver,
            observation_stage_context=observation_stage_context,
            original_input_bundle=original_input_bundle,
            trusted_future_authority=trusted_future_authority,
            supplemental_answer_bundle=supplemental_answer_bundle,
            _register_origin=_register_origin,
        )
        authority = build_grounded_relation_construction_authority_successor(
            plan, resolver
        )
        authority_issues = validate_grounded_relation_construction_authority_successor(
            authority, plan=plan, resolver=resolver
        )
        witness = build_grounded_lexical_role_witness_successor(plan, resolver)
        witness_issues = validate_grounded_lexical_role_witness_successor(
            witness, plan=plan, resolver=resolver
        )
    except (
        GroundedLexicalRoleSuccessorError,
        GroundedRelationConstructionAuthoritySuccessorError,
        SemanticObligationInventoryError,
    ) as exc:
        raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
            "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_BUILD_FAILED"
        ) from exc
    if authority_issues or witness_issues:
        raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
            "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_BUILD_FAILED"
        )

    base_hash = _base_snapshot_sha256(base_snapshot)
    commitments = _base_commitments(base_snapshot)
    payload = _payload(
        schema_version=GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_SCHEMA,
        adapter_version=(
            GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_ADAPTER_VERSION
        ),
        base_snapshot_sha256=base_hash,
        base_source_commitments=commitments,
        source_relation_construction_authority_sha256=authority.authority_sha256,
        source_lexical_role_witness_sha256=witness.witness_sha256,
        semantic_coverage_authorized=False,
        runtime_connected=False,
        experimental_only=True,
        body_free=True,
    )
    snapshot = GroundedLexicalRoleExperimentSnapshotSuccessor(
        schema_version=GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_SCHEMA,
        adapter_version=(
            GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_ADAPTER_VERSION
        ),
        base_snapshot=base_snapshot,
        base_snapshot_sha256=base_hash,
        base_source_commitments=commitments,
        relation_construction_authority=authority,
        source_relation_construction_authority_sha256=authority.authority_sha256,
        lexical_role_witness=witness,
        source_lexical_role_witness_sha256=witness.witness_sha256,
        semantic_coverage_authorized=False,
        runtime_connected=False,
        experiment_snapshot_sha256=artifact_sha256(payload),
        experimental_only=True,
        body_free=True,
    )
    if _register_origin:
        try:
            origin = _SuccessorExperimentOrigin.from_sources(
                plan=plan,
                resolver=resolver,
                observation_stage_context=observation_stage_context,
                original_input_bundle=original_input_bundle,
                trusted_future_authority=trusted_future_authority,
                supplemental_answer_bundle=supplemental_answer_bundle,
            )
            _register_experiment_origin(snapshot, origin)
        except (AttributeError, KeyError, TypeError, UnicodeError, ValueError) as exc:
            raise GroundedLexicalRoleExperimentSnapshotSuccessorError(
                "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_ORIGIN_REGISTRATION_INVALID"
            ) from exc
    return snapshot


def validate_grounded_lexical_role_experiment_snapshot_successor(
    value: Any,
) -> tuple[str, ...]:
    if type(value) is not GroundedLexicalRoleExperimentSnapshotSuccessor:
        return ("LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_SNAPSHOT_TYPE_INVALID",)
    return tuple(
        sorted(
            set((*_structural_issues(value), *_validate_experiment_origin(value)))
        )
    )


def grounded_lexical_role_experiment_snapshot_successor_material(
    value: GroundedLexicalRoleExperimentSnapshotSuccessor,
) -> dict[str, Any]:
    issues = validate_grounded_lexical_role_experiment_snapshot_successor(value)
    if issues:
        raise GroundedLexicalRoleExperimentSnapshotSuccessorError(issues[0])
    return {
        **_presented_payload(value),
        "experiment_snapshot_sha256": value.experiment_snapshot_sha256,
    }


__all__ = [
    "GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_ADAPTER_VERSION",
    "GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SUCCESSOR_SCHEMA",
    "GroundedLexicalRoleExperimentSnapshotSuccessor",
    "GroundedLexicalRoleExperimentSnapshotSuccessorError",
    "build_grounded_lexical_role_experiment_snapshot_successor",
    "grounded_lexical_role_experiment_snapshot_successor_material",
    "validate_grounded_lexical_role_experiment_snapshot_successor",
]
