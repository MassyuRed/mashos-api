# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free refined-observation source partition authority for NLS v3.

The public artifact contains commitments and source-role bindings only.  The
two validated plans and resolvers are retained in a private process-local
capability so Step 4 can rebuild the semantic inventory without serialising
either input bundle into the artifact.
"""

from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
import re
from typing import Any

from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver,
    build_evidence_ledger,
    validate_evidence_ledger,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    validate_grounded_observation_plan,
)
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
    validate_observation_stage_context,
)


REFINED_SOURCE_PARTITION_SCHEMA = (
    "cocolon.emlis.nls_v3.refined_source_partition.v1"
)

REFINED_SOURCE_PARTITION_NEGATIVE_CODES = frozenset(
    {
        "REFINED_SOURCE_PARTITION_REQUIRED",
        "REFINED_SOURCE_ROLE_BINDING_INVALID",
        "REFINED_ORIGINAL_SOURCE_PRESERVATION_FAILED",
        "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH",
        "REFINED_SOURCE_ID_ALIAS_COLLISION",
        "REFINED_CROSS_SOURCE_BINDING_UNAUTHORIZED",
        "QUESTION_DECISION_SEMANTIC_SOURCE_FORBIDDEN",
        "REFINED_SOURCE_PARTITION_BODY_FREE_REQUIRED",
        "REFINED_CONTROL_PLANE_OWNER_DRIFT",
        "REFINED_RESOURCE_BOUND_POLICY_DRIFT",
    }
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "stage",
        "source_partitions",
        "original_source_commitment_sha256",
        "supplemental_source_commitment_sha256",
        "semantic_source_roles",
        "stage_lineage_roles",
        "question_need_decision_is_semantic_source",
        "control_plane_owner_role",
        "trusted_future_authority",
        "cross_source_bindings",
        "resource_bound_policy",
        "body_free",
    }
)
_PARTITION_KEYS = frozenset(
    {
        "source_role",
        "source_id_namespace",
        "source_ids",
        "plan_commitment_sha256",
        "resolver_commitment_sha256",
        "bundle_commitment_sha256",
        "partition_commitment_sha256",
        "obligation_kinds",
        "owns_control_plane",
        "body_free",
    }
)
_AUTHORITY_KEYS = frozenset(
    {
        "permitted_stage",
        "question_decision_commitment_sha256",
        "original_input_bundle_sha256",
        "supplemental_answer_bundle_sha256",
    }
)
_RESOURCE_POLICY_KEYS = frozenset(
    {
        "combined_obligations_must_satisfy_current_step1_bound",
        "implicit_bound_doubling_permitted",
    }
)
_ORIGINAL_KINDS = (
    "eligibility",
    "evidence",
    "nucleus",
    "opportunity",
    "reception",
    "relation",
    "safety_boundary",
    "unknown",
)
_SUPPLEMENTAL_KINDS = ("evidence", "nucleus", "relation", "unknown")


class RefinedSourcePartitionError(ValueError):
    """Stable body-free failure raised by the partition owner."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True, repr=False)
class _RefinedSourceOrigin:
    original_plan: GroundedObservationPlan
    original_spans: tuple[Any, ...]
    supplemental_plan: GroundedObservationPlan
    supplemental_spans: tuple[Any, ...]
    observation_stage_context: Mapping[str, Any]
    original_input_bundle: Mapping[str, Any]
    supplemental_answer_bundle: Mapping[str, Any]
    trusted_future_authority: TrustedFutureStageAuthority

    def __repr__(self) -> str:
        return "<_RefinedSourceOrigin body_free_validation_context>"


@dataclass(frozen=True, slots=True, repr=False)
class RefinedSourcePartition(Mapping[str, Any]):
    """Mapping-compatible body-free artifact plus private source capability."""

    _artifact: dict[str, Any]
    _origin: _RefinedSourceOrigin

    def __getitem__(self, key: str) -> Any:
        return self._artifact[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._artifact)

    def __len__(self) -> int:
        return len(self._artifact)

    def __repr__(self) -> str:
        return repr(self._artifact)

    def as_body_free_artifact(self) -> dict[str, Any]:
        return {
            key: _copy_json_value(value)
            for key, value in self._artifact.items()
        }


def _copy_json_value(value: Any) -> Any:
    if type(value) is dict:
        return {key: _copy_json_value(child) for key, child in value.items()}
    if type(value) is list:
        return [_copy_json_value(child) for child in value]
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if type(value) in {tuple, list}:
        return [_jsonable(child) for child in value]
    if type(value) in {set, frozenset}:
        return sorted(_jsonable(child) for child in value)
    if type(value) is float:
        return {"float_hex": value.hex()}
    return value


def _artifact_mapping(value: Any) -> Mapping[str, Any] | None:
    if type(value) is RefinedSourcePartition:
        return value._artifact
    return value if isinstance(value, Mapping) else None


def _source_rows(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    role: str,
) -> tuple[str, ...]:
    reception = plan.response_plan.human_reception_plan
    opportunities = reception.opportunities if reception is not None else ()
    rows = (
        *(("evidence", item) for item in resolver.span_ids),
        *(("nucleus", item.nucleus_id) for item in plan.nuclei),
        *(("relation", item.relation_id) for item in plan.relations),
        *(("unknown", item.unknown_id) for item in plan.unknown_boundaries),
        *(("opportunity", item.opportunity_id) for item in opportunities),
    )
    return tuple(
        sorted(
            f"{role}:{kind}:{artifact_sha256({'kind': kind, 'id': str(source_id)})[:32]}"
            for kind, source_id in rows
        )
    )


def _resolver_commitment(resolver: EvidenceSpanResolver) -> str:
    return artifact_sha256(
        [_jsonable(asdict(resolver.resolve(item))) for item in resolver.span_ids]
    )


def _plan_commitment(plan: GroundedObservationPlan) -> str:
    return artifact_sha256(_jsonable(asdict(plan)))


def _validate_source(
    plan: Any,
    resolver: Any,
    bundle: Any,
) -> None:
    if type(plan) is not GroundedObservationPlan or type(
        resolver
    ) is not EvidenceSpanResolver or not isinstance(bundle, Mapping):
        raise RefinedSourcePartitionError(
            "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH"
        )
    if validate_grounded_observation_plan(plan, resolver):
        raise RefinedSourcePartitionError(
            "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH"
        )
    spans = tuple(resolver.resolve(item) for item in resolver.span_ids)
    report = validate_evidence_ledger(spans, current_input=bundle)
    if not report.valid or spans != tuple(build_evidence_ledger(bundle)):
        raise RefinedSourcePartitionError(
            "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH"
        )


def _partition_row(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    bundle: Mapping[str, Any],
    *,
    role: str,
) -> dict[str, Any]:
    source_ids = list(_source_rows(plan, resolver, role=role))
    plan_hash = _plan_commitment(plan)
    resolver_hash = _resolver_commitment(resolver)
    bundle_hash = artifact_sha256(bundle)
    obligation_kinds = (
        list(_ORIGINAL_KINDS)
        if role == "original_input"
        else list(_SUPPLEMENTAL_KINDS)
    )
    material = {
        "source_role": role,
        "source_id_namespace": role,
        "source_ids": source_ids,
        "plan_commitment_sha256": plan_hash,
        "resolver_commitment_sha256": resolver_hash,
        "bundle_commitment_sha256": bundle_hash,
        "obligation_kinds": obligation_kinds,
        "owns_control_plane": role == "original_input",
        "body_free": True,
    }
    return {
        **material,
        "partition_commitment_sha256": artifact_sha256(material),
    }


def build_refined_source_partition(
    original_plan: GroundedObservationPlan,
    original_resolver: EvidenceSpanResolver,
    supplemental_plan: GroundedObservationPlan,
    supplemental_resolver: EvidenceSpanResolver,
    observation_stage_context: Mapping[str, Any],
    original_input_bundle: Mapping[str, Any],
    supplemental_answer_bundle: Mapping[str, Any],
    trusted_future_authority: TrustedFutureStageAuthority,
) -> RefinedSourcePartition:
    """Build the only source-bound refined partition accepted by Step 4."""

    _validate_source(original_plan, original_resolver, original_input_bundle)
    _validate_source(
        supplemental_plan,
        supplemental_resolver,
        supplemental_answer_bundle,
    )
    if type(trusted_future_authority) is not TrustedFutureStageAuthority:
        raise RefinedSourcePartitionError(
            "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH"
        )
    stage_issues = validate_observation_stage_context(
        observation_stage_context,
        original_input_bundle=original_input_bundle,
        trusted_future_authority=trusted_future_authority,
        supplemental_answer_bundle=supplemental_answer_bundle,
    )
    if stage_issues or observation_stage_context.get("stage") != "refined_observation":
        raise RefinedSourcePartitionError(
            "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH"
        )
    original = _partition_row(
        original_plan,
        original_resolver,
        original_input_bundle,
        role="original_input",
    )
    supplemental = _partition_row(
        supplemental_plan,
        supplemental_resolver,
        supplemental_answer_bundle,
        role="supplemental_answer",
    )
    artifact = {
        "schema_version": REFINED_SOURCE_PARTITION_SCHEMA,
        "stage": "refined_observation",
        "source_partitions": [original, supplemental],
        "original_source_commitment_sha256": original[
            "partition_commitment_sha256"
        ],
        "supplemental_source_commitment_sha256": supplemental[
            "partition_commitment_sha256"
        ],
        "semantic_source_roles": ["original_input", "supplemental_answer"],
        "stage_lineage_roles": [
            "original_input",
            "question_need_decision",
            "supplemental_answer",
        ],
        "question_need_decision_is_semantic_source": False,
        "control_plane_owner_role": "original_input",
        "trusted_future_authority": {
            "permitted_stage": "refined_observation",
            "question_decision_commitment_sha256": (
                trusted_future_authority.question_need_decision_sha256
            ),
            "original_input_bundle_sha256": artifact_sha256(
                original_input_bundle
            ),
            "supplemental_answer_bundle_sha256": artifact_sha256(
                supplemental_answer_bundle
            ),
        },
        "cross_source_bindings": [],
        "resource_bound_policy": {
            "combined_obligations_must_satisfy_current_step1_bound": True,
            "implicit_bound_doubling_permitted": False,
        },
        "body_free": True,
    }
    issues = validate_refined_source_partition_shape(artifact)
    if issues:
        raise RefinedSourcePartitionError(issues[0])
    return RefinedSourcePartition(
        artifact,
        _RefinedSourceOrigin(
            original_plan=original_plan,
            original_spans=tuple(
                original_resolver.resolve(item)
                for item in original_resolver.span_ids
            ),
            supplemental_plan=supplemental_plan,
            supplemental_spans=tuple(
                supplemental_resolver.resolve(item)
                for item in supplemental_resolver.span_ids
            ),
            observation_stage_context=dict(observation_stage_context),
            original_input_bundle=dict(original_input_bundle),
            supplemental_answer_bundle=dict(supplemental_answer_bundle),
            trusted_future_authority=trusted_future_authority,
        ),
    )


def _has_body_leak(value: Any, *, path: tuple[str, ...] = ()) -> bool:
    if type(value) is dict:
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text != "body_free" and any(
                marker in key_text
                for marker in (
                    "raw_body",
                    "raw_input",
                    "private_note",
                    "comment_text",
                    "candidate_body",
                )
            ):
                return True
            if _has_body_leak(child, path=(*path, str(key))):
                return True
    elif type(value) is list:
        return any(_has_body_leak(child, path=path) for child in value)
    return False


def validate_refined_source_partition_shape(value: Any) -> tuple[str, ...]:
    """Validate the body-free artifact without trusting its builder."""

    artifact = _artifact_mapping(value)
    if artifact is None:
        return ("REFINED_SOURCE_PARTITION_REQUIRED",)
    issues: set[str] = set()
    if set(artifact) != _TOP_LEVEL_KEYS:
        if "source_partitions" not in artifact:
            issues.add("REFINED_SOURCE_PARTITION_REQUIRED")
        if set(artifact) - _TOP_LEVEL_KEYS or _has_body_leak(dict(artifact)):
            issues.add("REFINED_SOURCE_PARTITION_BODY_FREE_REQUIRED")
        issues.add("REFINED_SOURCE_ROLE_BINDING_INVALID")
    if (
        artifact.get("schema_version") != REFINED_SOURCE_PARTITION_SCHEMA
        or artifact.get("stage") != "refined_observation"
    ):
        issues.add("REFINED_SOURCE_ROLE_BINDING_INVALID")
    partitions = artifact.get("source_partitions")
    if type(partitions) is not list or len(partitions) != 2:
        issues.add("REFINED_SOURCE_PARTITION_REQUIRED")
        partitions = []
    valid_rows: list[dict[str, Any]] = []
    for index, row in enumerate(partitions):
        if type(row) is not dict or set(row) != _PARTITION_KEYS:
            issues.add("REFINED_SOURCE_ROLE_BINDING_INVALID")
            if type(row) is dict and _has_body_leak(row):
                issues.add("REFINED_SOURCE_PARTITION_BODY_FREE_REQUIRED")
            continue
        valid_rows.append(row)
        expected_role = ("original_input", "supplemental_answer")[index]
        expected_kinds = (_ORIGINAL_KINDS, _SUPPLEMENTAL_KINDS)[index]
        source_ids = row.get("source_ids")
        if (
            row.get("source_role") != expected_role
            or row.get("source_id_namespace") != expected_role
            or row.get("obligation_kinds") != list(expected_kinds)
            or row.get("owns_control_plane") is not (index == 0)
            or row.get("body_free") is not True
            or type(source_ids) is not list
            or not source_ids
            or len(source_ids) != len(set(source_ids))
            or any(
                type(item) is not str or _SOURCE_ID_RE.fullmatch(item) is None
                for item in source_ids
            )
            or any(
                type(row.get(field)) is not str
                or _SHA_RE.fullmatch(row[field]) is None
                for field in (
                    "plan_commitment_sha256",
                    "resolver_commitment_sha256",
                    "bundle_commitment_sha256",
                    "partition_commitment_sha256",
                )
            )
        ):
            issues.add("REFINED_SOURCE_ROLE_BINDING_INVALID")
    if len(valid_rows) == 2:
        original, supplemental = valid_rows
        if (
            artifact.get("original_source_commitment_sha256")
            != original.get("partition_commitment_sha256")
            or original.get("partition_commitment_sha256")
            == supplemental.get("partition_commitment_sha256")
        ):
            issues.add("REFINED_ORIGINAL_SOURCE_PRESERVATION_FAILED")
        if (
            artifact.get("supplemental_source_commitment_sha256")
            != supplemental.get("partition_commitment_sha256")
        ):
            issues.add("REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH")
        if set(original.get("source_ids") or ()) & set(
            supplemental.get("source_ids") or ()
        ):
            issues.add("REFINED_SOURCE_ID_ALIAS_COLLISION")
    if artifact.get("semantic_source_roles") != [
        "original_input",
        "supplemental_answer",
    ] or artifact.get("stage_lineage_roles") != [
        "original_input",
        "question_need_decision",
        "supplemental_answer",
    ]:
        issues.add("REFINED_SOURCE_ROLE_BINDING_INVALID")
    if artifact.get("question_need_decision_is_semantic_source") is not False:
        issues.add("QUESTION_DECISION_SEMANTIC_SOURCE_FORBIDDEN")
    if artifact.get("control_plane_owner_role") != "original_input":
        issues.add("REFINED_CONTROL_PLANE_OWNER_DRIFT")
    if artifact.get("cross_source_bindings") != []:
        issues.add("REFINED_CROSS_SOURCE_BINDING_UNAUTHORIZED")
    authority = artifact.get("trusted_future_authority")
    if type(authority) is not dict or set(authority) != _AUTHORITY_KEYS:
        issues.add("REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH")
    elif (
        authority.get("permitted_stage") != "refined_observation"
        or any(
            type(authority.get(field)) is not str
            or _SHA_RE.fullmatch(authority[field]) is None
            for field in (
                "question_decision_commitment_sha256",
                "original_input_bundle_sha256",
                "supplemental_answer_bundle_sha256",
            )
        )
        or (
            len(valid_rows) == 2
            and (
                authority.get("original_input_bundle_sha256")
                != valid_rows[0].get("bundle_commitment_sha256")
                or authority.get("supplemental_answer_bundle_sha256")
                != valid_rows[1].get("bundle_commitment_sha256")
            )
        )
    ):
        issues.add("REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH")
    policy = artifact.get("resource_bound_policy")
    if (
        type(policy) is not dict
        or set(policy) != _RESOURCE_POLICY_KEYS
        or policy.get("combined_obligations_must_satisfy_current_step1_bound")
        is not True
        or policy.get("implicit_bound_doubling_permitted") is not False
    ):
        issues.add("REFINED_RESOURCE_BOUND_POLICY_DRIFT")
    if artifact.get("body_free") is not True or _has_body_leak(dict(artifact)):
        issues.add("REFINED_SOURCE_PARTITION_BODY_FREE_REQUIRED")
    return tuple(sorted(issues))


def validate_refined_source_partition(
    value: Any,
    original_plan: GroundedObservationPlan,
    original_resolver: EvidenceSpanResolver,
    supplemental_plan: GroundedObservationPlan,
    supplemental_resolver: EvidenceSpanResolver,
    observation_stage_context: Mapping[str, Any],
    original_input_bundle: Mapping[str, Any],
    supplemental_answer_bundle: Mapping[str, Any],
    trusted_future_authority: TrustedFutureStageAuthority,
) -> tuple[str, ...]:
    """Bind a proposed artifact to the exact two source owners."""

    issues = set(validate_refined_source_partition_shape(value))
    try:
        expected = build_refined_source_partition(
            original_plan,
            original_resolver,
            supplemental_plan,
            supplemental_resolver,
            observation_stage_context,
            original_input_bundle,
            supplemental_answer_bundle,
            trusted_future_authority,
        )
    except RefinedSourcePartitionError as exc:
        issues.add(exc.code)
        return tuple(sorted(issues))
    artifact = _artifact_mapping(value)
    if artifact is None or dict(artifact) != expected.as_body_free_artifact():
        issues.add("REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH")
    if type(value) is RefinedSourcePartition:
        origin = value._origin
        if (
            origin.original_plan is not original_plan
            or origin.supplemental_plan is not supplemental_plan
            or tuple(original_resolver.resolve(item) for item in original_resolver.span_ids)
            != origin.original_spans
            or tuple(
                supplemental_resolver.resolve(item)
                for item in supplemental_resolver.span_ids
            )
            != origin.supplemental_spans
        ):
            issues.add("REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH")
    return tuple(sorted(issues))


def refined_source_partition_sources(
    value: Any,
) -> tuple[
    GroundedObservationPlan,
    EvidenceSpanResolver,
    GroundedObservationPlan,
    EvidenceSpanResolver,
    Mapping[str, Any],
    Mapping[str, Any],
    Mapping[str, Any],
    TrustedFutureStageAuthority,
]:
    """Open the private capability after independently revalidating it."""

    if type(value) is not RefinedSourcePartition:
        raise RefinedSourcePartitionError("REFINED_SOURCE_PARTITION_REQUIRED")
    origin = value._origin
    original_resolver = EvidenceSpanResolver(origin.original_spans)
    supplemental_resolver = EvidenceSpanResolver(origin.supplemental_spans)
    issues = validate_refined_source_partition(
        value,
        origin.original_plan,
        original_resolver,
        origin.supplemental_plan,
        supplemental_resolver,
        origin.observation_stage_context,
        origin.original_input_bundle,
        origin.supplemental_answer_bundle,
        origin.trusted_future_authority,
    )
    if issues:
        raise RefinedSourcePartitionError(issues[0])
    return (
        origin.original_plan,
        original_resolver,
        origin.supplemental_plan,
        supplemental_resolver,
        origin.observation_stage_context,
        origin.original_input_bundle,
        origin.supplemental_answer_bundle,
        origin.trusted_future_authority,
    )


__all__ = [
    "REFINED_SOURCE_PARTITION_NEGATIVE_CODES",
    "REFINED_SOURCE_PARTITION_SCHEMA",
    "RefinedSourcePartition",
    "RefinedSourcePartitionError",
    "build_refined_source_partition",
    "refined_source_partition_sources",
    "validate_refined_source_partition",
    "validate_refined_source_partition_shape",
]
