# -*- coding: utf-8 -*-
from __future__ import annotations

"""Experiment-only propagation boundary for the rc0028 lexical witness.

The active Step 4 source snapshot is deliberately left unchanged.  This
module wraps a normally built ``GroundedSourceSnapshot`` and the independent
lexical-role witness in a separate, body-free experiment artifact.  A private
request-local capability retains the source bodies solely to rebuild both
owners during validation; neither body nor capability is serialized into the
artifact.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
import re
import weakref
from typing import Any, Final

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_lexical_role_witness_v3 import (
    GROUNDED_LEXICAL_ROLE_UNRESOLVED_REASON_CODES,
    GroundedLexicalRoleError,
    GroundedLexicalRoleWitness,
    build_grounded_lexical_role_witness,
    validate_grounded_lexical_role_witness,
)
from emlis_ai_grounded_observation_plan import GroundedObservationPlan
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


GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_experiment_snapshot."
    "rc0028.experiment.v1"
)
GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_ADAPTER_VERSION: Final = (
    "cocolon.emlis.nls_v3.grounded_lexical_role_experiment_snapshot_adapter."
    "20260719.v1"
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


class GroundedLexicalRoleExperimentSnapshotError(ValueError):
    """Fail-closed error whose message never contains a source body."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _body_free_projection(value: Any) -> Any:
    """Project closed dataclasses into deterministic JSON-safe material."""

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
        projected = [_body_free_projection(item) for item in value]
        return sorted(projected, key=canonical_json_bytes)
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise GroundedLexicalRoleExperimentSnapshotError(
                "LEXICAL_ROLE_EXPERIMENT_PROJECTION_INVALID"
            )
        return {
            key: _body_free_projection(value[key])
            for key in sorted(value)
        }
    raise GroundedLexicalRoleExperimentSnapshotError(
        "LEXICAL_ROLE_EXPERIMENT_PROJECTION_INVALID"
    )


def _base_commitments(
    snapshot: GroundedSourceSnapshot,
) -> tuple[tuple[str, str | None], ...]:
    if type(snapshot) is not GroundedSourceSnapshot:
        raise GroundedLexicalRoleExperimentSnapshotError(
            "LEXICAL_ROLE_EXPERIMENT_BASE_SNAPSHOT_INVALID"
        )
    return tuple(
        (name, getattr(snapshot, name))
        for name in _BASE_COMMITMENT_FIELDS
    )


def _base_snapshot_sha256(snapshot: GroundedSourceSnapshot) -> str:
    return artifact_sha256(
        {
            "commitment_kind": "unchanged_grounded_source_snapshot",
            "snapshot": _body_free_projection(snapshot),
        }
    )


@dataclass(frozen=True)
class GroundedLexicalRoleExperimentSnapshot:
    """Body-free rc0028 wrapper; it is not an active Step 4 source owner."""

    schema_version: str
    adapter_version: str
    base_snapshot: GroundedSourceSnapshot
    base_snapshot_sha256: str
    base_source_commitments: tuple[tuple[str, str | None], ...]
    lexical_role_witness: GroundedLexicalRoleWitness
    source_lexical_role_witness_sha256: str
    experiment_snapshot_sha256: str
    experimental_only: bool = True
    body_free: bool = True

    def __deepcopy__(
        self,
        memo: dict[int, Any],
    ) -> "GroundedLexicalRoleExperimentSnapshot":
        # Retain the module-owned request-local origin capability.
        return self


def _experiment_payload(
    *,
    schema_version: str,
    adapter_version: str,
    base_snapshot_sha256: str,
    base_source_commitments: tuple[tuple[str, str | None], ...],
    lexical_role_witness: GroundedLexicalRoleWitness,
    source_lexical_role_witness_sha256: str,
    experimental_only: bool,
    body_free: bool,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "adapter_version": adapter_version,
        "base_snapshot_sha256": base_snapshot_sha256,
        "base_source_commitments": [
            [name, value]
            for name, value in base_source_commitments
        ],
        "lexical_role_witness": _body_free_projection(
            lexical_role_witness
        ),
        "source_lexical_role_witness_sha256": (
            source_lexical_role_witness_sha256
        ),
        "experimental_only": experimental_only,
        "body_free": body_free,
    }


def _presented_payload(
    value: GroundedLexicalRoleExperimentSnapshot,
) -> dict[str, Any]:
    return _experiment_payload(
        schema_version=value.schema_version,
        adapter_version=value.adapter_version,
        base_snapshot_sha256=value.base_snapshot_sha256,
        base_source_commitments=value.base_source_commitments,
        lexical_role_witness=value.lexical_role_witness,
        source_lexical_role_witness_sha256=(
            value.source_lexical_role_witness_sha256
        ),
        experimental_only=value.experimental_only,
        body_free=value.body_free,
    )


@dataclass(frozen=True, slots=True, repr=False)
class _GroundedLexicalRoleExperimentOrigin:
    """Private current-request source authority used only for rebuilding."""

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
    ) -> "_GroundedLexicalRoleExperimentOrigin":
        return cls(
            plan=plan,
            evidence_spans=tuple(
                resolver.resolve(span_id)
                for span_id in resolver.span_ids
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
        return "<_GroundedLexicalRoleExperimentOrigin request_local>"

    def rebuild(self) -> "GroundedLexicalRoleExperimentSnapshot":
        resolver = EvidenceSpanResolver(self.evidence_spans)
        return build_grounded_lexical_role_experiment_snapshot(
            self.plan,
            resolver,
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
            weakref.ReferenceType[GroundedLexicalRoleExperimentSnapshot],
            _GroundedLexicalRoleExperimentOrigin,
        ],
    ] = {}

    def register(
        snapshot: GroundedLexicalRoleExperimentSnapshot,
        origin: _GroundedLexicalRoleExperimentOrigin,
    ) -> None:
        if type(snapshot) is not GroundedLexicalRoleExperimentSnapshot or type(
            origin
        ) is not _GroundedLexicalRoleExperimentOrigin:
            raise GroundedLexicalRoleExperimentSnapshotError(
                "LEXICAL_ROLE_EXPERIMENT_ORIGIN_REGISTRATION_INVALID"
            )
        try:
            expected = origin.rebuild()
        except (
            AttributeError,
            GroundedLexicalRoleError,
            GroundedLexicalRoleExperimentSnapshotError,
            KeyError,
            SemanticObligationInventoryError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as exc:
            raise GroundedLexicalRoleExperimentSnapshotError(
                "LEXICAL_ROLE_EXPERIMENT_ORIGIN_REGISTRATION_INVALID"
            ) from exc
        if snapshot != expected:
            raise GroundedLexicalRoleExperimentSnapshotError(
                "LEXICAL_ROLE_EXPERIMENT_ORIGIN_REGISTRATION_MISMATCH"
            )

        key = id(snapshot)

        def remove(
            reference: weakref.ReferenceType[
                GroundedLexicalRoleExperimentSnapshot
            ],
            *,
            registry_key: int = key,
        ) -> None:
            current = registry.get(registry_key)
            if current is not None and current[0] is reference:
                registry.pop(registry_key, None)

        reference = weakref.ref(snapshot, remove)
        registry[key] = (reference, origin)

    def validate(
        snapshot: GroundedLexicalRoleExperimentSnapshot,
    ) -> tuple[str, ...]:
        current = registry.get(id(snapshot))
        if (
            current is None
            or current[0]() is not snapshot
            or type(current[1]) is not _GroundedLexicalRoleExperimentOrigin
        ):
            return (
                "LEXICAL_ROLE_EXPERIMENT_ORIGIN_AUTHORITY_REQUIRED",
            )
        try:
            expected = current[1].rebuild()
        except (
            AttributeError,
            GroundedLexicalRoleError,
            GroundedLexicalRoleExperimentSnapshotError,
            KeyError,
            SemanticObligationInventoryError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            return ("LEXICAL_ROLE_EXPERIMENT_ORIGIN_REVALIDATION_FAILED",)
        if snapshot != expected:
            return ("LEXICAL_ROLE_EXPERIMENT_ORIGIN_REBIND_MISMATCH",)
        return ()

    return register, validate


(
    _register_experiment_origin,
    _validate_experiment_origin,
) = _origin_capability_store()


def _structural_issues(
    value: GroundedLexicalRoleExperimentSnapshot,
) -> tuple[str, ...]:
    issues: list[str] = []
    if (
        value.schema_version
        != GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SCHEMA
        or value.adapter_version
        != GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_ADAPTER_VERSION
        or value.experimental_only is not True
        or value.body_free is not True
    ):
        issues.append("LEXICAL_ROLE_EXPERIMENT_CONTRACT_MISMATCH")

    if type(value.base_snapshot) is not GroundedSourceSnapshot:
        issues.append("LEXICAL_ROLE_EXPERIMENT_BASE_SNAPSHOT_INVALID")
    else:
        try:
            expected_base_hash = _base_snapshot_sha256(value.base_snapshot)
            expected_commitments = _base_commitments(value.base_snapshot)
        except (
            AttributeError,
            GroundedLexicalRoleExperimentSnapshotError,
            TypeError,
            ValueError,
        ):
            expected_base_hash = ""
            expected_commitments = ()
            issues.append("LEXICAL_ROLE_EXPERIMENT_BASE_SNAPSHOT_INVALID")
        if (
            type(value.base_snapshot_sha256) is not str
            or not _SHA256_RE.fullmatch(value.base_snapshot_sha256)
            or value.base_snapshot_sha256 != expected_base_hash
        ):
            issues.append("LEXICAL_ROLE_EXPERIMENT_BASE_HASH_MISMATCH")
        if (
            type(value.base_source_commitments) is not tuple
            or value.base_source_commitments != expected_commitments
        ):
            issues.append(
                "LEXICAL_ROLE_EXPERIMENT_BASE_COMMITMENTS_MISMATCH"
            )

    witness = value.lexical_role_witness
    if type(witness) is not GroundedLexicalRoleWitness:
        issues.append("LEXICAL_ROLE_EXPERIMENT_WITNESS_INVALID")
    else:
        if (
            type(value.source_lexical_role_witness_sha256) is not str
            or not _SHA256_RE.fullmatch(
                value.source_lexical_role_witness_sha256
            )
            or value.source_lexical_role_witness_sha256
            != witness.witness_sha256
            or witness.body_free is not True
        ):
            issues.append(
                "LEXICAL_ROLE_EXPERIMENT_WITNESS_COMMITMENT_MISMATCH"
            )
        unresolved = witness.unresolved_required_nucleus_ids
        reasons = witness.unresolved_owner_reasons
        reasons_shape_valid = bool(
            type(reasons) is tuple
            and all(
                type(item) is tuple
                and len(item) == 2
                and type(item[0]) is str
                and type(item[1]) is str
                and item[1]
                in GROUNDED_LEXICAL_ROLE_UNRESOLVED_REASON_CODES
                for item in reasons
            )
        )
        if (
            type(unresolved) is not tuple
            or len(unresolved) != len(set(unresolved))
            or not reasons_shape_valid
            or len(reasons) != len(unresolved)
            or {item[0] for item in reasons}
            != set(unresolved)
        ):
            issues.append(
                "LEXICAL_ROLE_EXPERIMENT_UNRESOLVED_REASONS_INVALID"
            )

    try:
        presented_hash = artifact_sha256(_presented_payload(value))
    except (
        AttributeError,
        GroundedLexicalRoleExperimentSnapshotError,
        TypeError,
        ValueError,
    ):
        presented_hash = ""
    if (
        type(value.experiment_snapshot_sha256) is not str
        or not _SHA256_RE.fullmatch(value.experiment_snapshot_sha256)
        or value.experiment_snapshot_sha256 != presented_hash
    ):
        issues.append("LEXICAL_ROLE_EXPERIMENT_HASH_MISMATCH")
    return tuple(sorted(set(issues)))


def build_grounded_lexical_role_experiment_snapshot(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    observation_stage_context: Mapping[str, Any],
    original_input_bundle: Any,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
    _register_origin: bool = True,
) -> GroundedLexicalRoleExperimentSnapshot:
    """Build the separate diagnostic wrapper without changing Step 4."""

    if type(resolver) is not EvidenceSpanResolver:
        raise GroundedLexicalRoleExperimentSnapshotError(
            "LEXICAL_ROLE_EXPERIMENT_RESOLVER_INVALID"
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
    except SemanticObligationInventoryError as exc:
        raise GroundedLexicalRoleExperimentSnapshotError(
            "LEXICAL_ROLE_EXPERIMENT_BASE_BUILD_FAILED"
        ) from exc
    try:
        witness = build_grounded_lexical_role_witness(plan, resolver)
        witness_issues = validate_grounded_lexical_role_witness(
            witness,
            plan=plan,
            resolver=resolver,
        )
    except GroundedLexicalRoleError as exc:
        raise GroundedLexicalRoleExperimentSnapshotError(
            "LEXICAL_ROLE_EXPERIMENT_WITNESS_BUILD_FAILED"
        ) from exc
    if witness_issues:
        raise GroundedLexicalRoleExperimentSnapshotError(
            "LEXICAL_ROLE_EXPERIMENT_WITNESS_BUILD_FAILED"
        )

    base_hash = _base_snapshot_sha256(base_snapshot)
    commitments = _base_commitments(base_snapshot)
    payload = _experiment_payload(
        schema_version=GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SCHEMA,
        adapter_version=(
            GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_ADAPTER_VERSION
        ),
        base_snapshot_sha256=base_hash,
        base_source_commitments=commitments,
        lexical_role_witness=witness,
        source_lexical_role_witness_sha256=witness.witness_sha256,
        experimental_only=True,
        body_free=True,
    )
    snapshot = GroundedLexicalRoleExperimentSnapshot(
        schema_version=GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SCHEMA,
        adapter_version=(
            GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_ADAPTER_VERSION
        ),
        base_snapshot=base_snapshot,
        base_snapshot_sha256=base_hash,
        base_source_commitments=commitments,
        lexical_role_witness=witness,
        source_lexical_role_witness_sha256=witness.witness_sha256,
        experiment_snapshot_sha256=artifact_sha256(payload),
        experimental_only=True,
        body_free=True,
    )
    if _register_origin:
        try:
            origin = _GroundedLexicalRoleExperimentOrigin.from_sources(
                plan=plan,
                resolver=resolver,
                observation_stage_context=observation_stage_context,
                original_input_bundle=original_input_bundle,
                trusted_future_authority=trusted_future_authority,
                supplemental_answer_bundle=supplemental_answer_bundle,
            )
            _register_experiment_origin(snapshot, origin)
        except (
            AttributeError,
            KeyError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as exc:
            raise GroundedLexicalRoleExperimentSnapshotError(
                "LEXICAL_ROLE_EXPERIMENT_ORIGIN_REGISTRATION_INVALID"
            ) from exc
    return snapshot


def validate_grounded_lexical_role_experiment_snapshot(
    value: Any,
) -> tuple[str, ...]:
    """Rebuild both owners from the private request-local source authority."""

    if type(value) is not GroundedLexicalRoleExperimentSnapshot:
        return ("LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_TYPE_INVALID",)
    return tuple(
        sorted(
            set(
                (
                    *_structural_issues(value),
                    *_validate_experiment_origin(value),
                )
            )
        )
    )


def grounded_lexical_role_experiment_snapshot_material(
    value: GroundedLexicalRoleExperimentSnapshot,
) -> dict[str, Any]:
    """Return the bounded body-free experiment artifact projection."""

    issues = validate_grounded_lexical_role_experiment_snapshot(value)
    if issues:
        raise GroundedLexicalRoleExperimentSnapshotError(issues[0])
    return {
        **_presented_payload(value),
        "experiment_snapshot_sha256": value.experiment_snapshot_sha256,
    }


__all__ = [
    "GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_ADAPTER_VERSION",
    "GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SCHEMA",
    "GroundedLexicalRoleExperimentSnapshot",
    "GroundedLexicalRoleExperimentSnapshotError",
    "build_grounded_lexical_role_experiment_snapshot",
    "grounded_lexical_role_experiment_snapshot_material",
    "validate_grounded_lexical_role_experiment_snapshot",
]
