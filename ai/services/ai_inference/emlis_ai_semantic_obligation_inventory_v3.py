# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free Step 4 Semantic Obligation Inventory for NLS v3.

The adapter reads only already validated GroundedObservationPlan owners.  It
first freezes an independent, body-free source snapshot and only then derives
the obligation ledger.  No surface text, question decision, expected answer,
case id, or runtime reply path is consumed here.
"""

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence
import weakref

from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver,
    build_evidence_ledger,
    validate_evidence_ledger,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    GroundedReceptionOpportunity,
    GroundedSemanticNucleus,
    GroundedSemanticRelation,
    GroundedUnknownBoundary,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION,
    GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA,
    GroundedSemanticRestatementError,
    GroundedExplicitUnknownWitness,
    GroundedSemanticLinkWitness,
    GroundedSemanticRestatementRelationWitness,
    GroundedSemanticUnitWitness,
    build_grounded_semantic_restatement_witness,
    validate_grounded_semantic_restatement_witness,
)
from emlis_ai_nls_v3_artifact_contract import (
    ALLOWED_SOURCE_OWNERS,
    LEDGER_SCHEMA,
    STAGE_SCHEMA,
    LedgerSourceAuthority,
    TrustedFutureStageAuthority,
    TrustedSourceSemantic,
    artifact_sha256,
    canonical_json_bytes,
    derive_content_id,
    derive_obligation_id,
    load_canonical_json_bytes,
    validate_observation_stage_context,
    validate_semantic_obligation_ledger,
)


SOURCE_POLICY_SCHEMA = "cocolon.emlis.nls_v3.semantic_inventory_source_policy.v1"
SOURCE_SNAPSHOT_SCHEMA = "cocolon.emlis.nls_v3.grounded_source_snapshot.v1"
ELIGIBILITY_SOURCE_SCHEMA = "cocolon.emlis.nls_v3.response_eligibility_source.v1"
RECEPTION_SOURCE_SCHEMA = "cocolon.emlis.nls_v3.reception_opportunity_source.v1"
SOURCE_ID_ALIAS_SCHEMA = "cocolon.emlis.nls_v3.source_id_alias.v1"
RESPONSE_ELIGIBILITY_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.response_eligibility_adapter.v1"
)

_VISIBLE_ELIGIBILITIES = frozenset({"normal_surface", "source_unavailable"})
_SPECIAL_KIND_ORDER = {
    "grounded_nucleus_notice": 0,
    "grounded_relation_preservation": 1,
    "unknown_boundary_preservation": 2,
    "significance_or_shift": 3,
    "intention_or_next_action": 4,
    "self_denial_boundary": 5,
    "bounded_counterposition": 6,
    "bound_emlis_reception": 7,
}
_RELATION_DESCRIPTOR = {
    "temporal_before_after": ("precedes", "source_to_target"),
    "shift_from_to": ("precedes", "source_to_target"),
    "contrast": ("contrasts_with", "source_to_target"),
    "attempt_and_block": ("contrasts_with", "source_to_target"),
    "wish_and_constraint": ("contrasts_with", "source_to_target"),
    "continuation_or_refusal": ("contrasts_with", "source_to_target"),
    "coexistence": ("coexists_with", "bidirectional"),
    # The source meaning survives despite the target; this is asymmetric.
    "preserves_despite": ("coexists_with", "source_to_target"),
    "evaluation_about_event": ("qualifies", "source_to_target"),
    "self_evaluation_about_state": ("qualifies", "source_to_target"),
    "uncertain_connection": ("qualifies", "source_to_target"),
    "user_stated_cause": ("supports_without_guarantee", "source_to_target"),
    "user_stated_result": ("supports_without_guarantee", "source_to_target"),
    "action_supports_change": (
        "supports_without_guarantee",
        "source_to_target",
    ),
}
_RECEPTION_ACT = {
    "stay_with_current_burden": "hold_in_attention",
    "honor_concrete_effort": "honor_concrete_action",
    "protect_retained_intention": "do_not_dismiss",
    "recognize_lived_change": "hold_in_attention",
    "hold_help_seeking": "do_not_dismiss",
    "bounded_counter_self_denial": "do_not_dismiss",
    "respect_words_placed": "hold_in_attention",
}
_RETENTION_RANK = {"required": 0, "should": 1, "optional": 2}
_ALIAS_PREFIX = {
    "evidence": "evidence",
    "nucleus": "nucleus",
    "relation": "relation",
    "unknown_boundary": "unknown",
    "reception_opportunity": "reception",
}
_SOURCE_OWNER = {
    "evidence": "evidence_ledger",
    "nucleus": "nuclei",
    "relation": "relations",
    "unknown_boundary": "unknown_boundaries",
    "reception_opportunity": "human_reception_plan.opportunities",
}
_MACHINE_CODE_RE = re.compile(r"[^A-Z0-9_]+")
_BODY_FREE_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_MACHINE_SOURCE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_NUCLEUS_KINDS = frozenset(
    {
        "event",
        "state",
        "reaction",
        "wish",
        "constraint",
        "action",
        "change",
        "self_evaluation",
        "value",
        "uncertainty",
        "conclusion",
        "other_explicit",
    }
)
_ALLOWED_SOURCE_MODALITIES = frozenset(
    {"fact", "feeling", "refusal", "wish", "intention", "possibility", "uncertain"}
)
_ALLOWED_SOURCE_POLARITIES = frozenset(
    {"positive", "negative", "mixed", "neutral"}
)
_ALLOWED_SOURCE_TIME_SCOPES = frozenset(
    {
        "current_input",
        "present",
        "current",
        "continuing",
        "past",
        "reported_past",
        "past_to_present",
        "future",
        "present_to_future",
        "intended_future",
        "atemporal",
        "general",
        "unknown",
    }
)
_ALLOWED_RETENTIONS = frozenset({"required", "should", "optional"})
_ALLOWED_GROUNDING_KINDS = frozenset(
    {"explicit", "user_stated_relation", "bounded_structural_inference"}
)
_ALLOWED_SOURCE_FIELDS = frozenset(
    {"memo", "memo_action", "emotion_details", "emotions", "category"}
)
_ALLOWED_CLAIM_SCOPES = frozenset(
    {"explicit_current_input", "source_bounded_relation", "selected_label_only"}
)
_ALLOWED_UNKNOWN_POLICIES = frozenset({"do_not_claim", "hedge_only", "omit"})
_ALLOWED_ENDPOINT_SEMANTICS = frozenset(
    {"distinct_meanings", "semantic_restatement"}
)
_SAFE_OBSERVATION = "safe_observation"
_SELF_DENIAL_SAFE = "self_denial_safe_state_answer"
_SEPARATE_SAFETY_KINDS = frozenset(
    {"safety_support_required", "safety_blocked_emergency"}
)

SOURCE_POLICY_ARTIFACT = {
    "schema_version": SOURCE_POLICY_SCHEMA,
    "policy_version": "cocolon.emlis.nls_v3.semantic_inventory.v3_adapter_expansion.20260715.v2",
    "source_id_alias_schema": SOURCE_ID_ALIAS_SCHEMA,
    "response_eligibility_adapter_version": RESPONSE_ELIGIBILITY_ADAPTER_VERSION,
    "source_component_bounds": {
        "text_evidence_span_count": "T<=E",
        "nucleus_count": "N<=E",
        "relation_count": "R<=min(N*(N-1),T+9)",
        "unknown_boundary_count": "U<=11",
        "safety_policy_count": "S==1",
        "safety_required_boundary_code_count": "K<=9",
        "reception_opportunity_count": "O<=4",
        "semantic_unit_count": "D<=4*N and 2<=D_parent<=4",
        "semantic_link_count": "L<=N",
        "explicit_unknown_count": "X<=2*T+N",
    },
    "inventory_upper_bound_formula": "(4*N+R+U)*(S+K+1)*(O+2)",
    "candidate_limit_is_inventory_limit": False,
    "truncate_on_overflow": False,
    "question_need_decision_is_semantic_source": False,
    "relation_descriptor": {
        key: {"relation_type": value[0], "direction": value[1]}
        for key, value in sorted(_RELATION_DESCRIPTOR.items())
    },
    "endpoint_semantics": list(sorted(_ALLOWED_ENDPOINT_SEMANTICS)),
    "semantic_restatement_witness_schema": (
        GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA
    ),
    "semantic_restatement_adapter_version": (
        GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
    ),
    "semantic_restatement_unit_membership_source": (
        "GroundedSemanticRestatementWitness.relations[*]."
        "semantic_restatement_unit_nucleus_ids"
    ),
    "semantic_decomposition_source": (
        "GroundedSemanticRestatementWitness.semantic_units/semantic_links/"
        "explicit_unknowns"
    ),
    "semantic_decomposition_replaces_parent_nucleus": True,
    "semantic_decomposition_uses_existing_step1_capacity": True,
    "allowed_source_owners": list(ALLOWED_SOURCE_OWNERS),
    "obligation_kinds": list(sorted(_SPECIAL_KIND_ORDER)),
    "body_free": True,
}
SOURCE_POLICY_SHA256 = artifact_sha256(SOURCE_POLICY_ARTIFACT)
# Release-bound identity: editing the policy artifact must fail validation
# until this explicit version boundary is intentionally re-frozen.
FROZEN_SOURCE_POLICY_SHA256 = (
    "de77b13a27e08ae3337d3ea8c11e1ba18ff24fb3f601d7639fe38c3948b8ff8c"
)


class SemanticObligationInventoryError(ValueError):
    """Stable, fail-closed Step 4 planning error."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        self.code = code
        self.detail = detail
        super().__init__(code if not detail else f"{code}:{detail}")


@dataclass(frozen=True)
class TrustedResponseEligibilityAuthority:
    """Closed projection of the already validated upstream routing owner."""

    response_eligibility: str
    source_content_policy: str
    source_material_quality: str
    source_response_kind: str
    source_safety_kind: str
    source_commitment_sha256: str
    authority_owner: str = "upstream_grounded_observation_router"
    adapter_version: str = RESPONSE_ELIGIBILITY_ADAPTER_VERSION


@dataclass(frozen=True)
class SourceIdAliasBinding:
    """One deterministic binding from an upstream id to a Step 3 machine id."""

    source_kind: str
    source_owner: str
    actual_source_id: str
    alias_source_id: str


@dataclass(frozen=True)
class ObservationStageSourceBinding:
    """Immutable copy of the validated, body-free stage lineage fields."""

    schema_version: str
    stage: str
    original_input_bundle_sha256: str
    question_need_decision_sha256: str | None
    supplemental_answer_bundle_sha256: str | None
    allowed_source_roles: tuple[str, ...]
    body_free: bool


@dataclass(frozen=True)
class InventoryNucleusSource:
    source_id: str
    actual_source_id: str
    source_role: str
    kind: str
    evidence_ids: tuple[str, ...]
    source_fields: tuple[str, ...]
    surface_anchor_ids: tuple[str, ...]
    source_anchor_ids: tuple[str, ...]
    source_meaning_block_keys: tuple[str, ...]
    source_claim_ids: tuple[str, ...]
    allowed_claim_scope: str
    grounding_kind: str
    source_actor: str
    source_predicate_kind: str
    source_modality: str
    source_time_scope: str
    source_degree: str
    source_attribute_codes: tuple[str, ...]
    polarity: str
    modality: str
    temporal_scope: str
    topic_scope_ids: tuple[str, ...]
    referent_scope: str
    retention: str
    required: bool
    forbidden_claim_codes: tuple[str, ...]
    fact_boundary: bool


@dataclass(frozen=True)
class InventoryRelationSource:
    source_id: str
    actual_source_id: str
    source_role: str
    source_relation_kind: str
    grounding_kind: str
    endpoint_semantic_relation: str
    semantic_restatement_unit_nucleus_ids: tuple[str, ...]
    relation_type: str
    relation_direction: str
    from_nucleus_id: str
    to_nucleus_id: str
    source_evidence_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    source_relation_ids: tuple[str, ...]
    source_meaning_arc_keys: tuple[str, ...]
    polarity: str
    modality: str
    temporal_scope: str
    topic_scope_ids: tuple[str, ...]
    retention: str
    required: bool
    forbidden_claim_codes: tuple[str, ...]


@dataclass(frozen=True)
class InventoryUnknownSource:
    source_id: str
    actual_source_id: str
    source_role: str
    source_dimension: str
    dimension_code: str
    affected_nucleus_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    topic_scope_ids: tuple[str, ...]
    surface_policy: str
    required: bool


@dataclass(frozen=True)
class InventoryReceptionSource:
    source_id: str
    actual_source_id: str
    source_role: str
    family: str
    source_reception_act: str
    reception_act: str
    target_nucleus_ids: tuple[str, ...]
    support_nucleus_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    retention: str
    priority: int
    source_field_count: int
    safety_required: bool


@dataclass(frozen=True, slots=True, repr=False)
class _GroundedSourceOrigin:
    """Request-local source owner retained only for independent revalidation.

    The snapshot and ledger remain body-free artifacts.  This private context
    is deliberately excluded from dataclass repr/equality and is never copied
    into either artifact; it lets Step 4/5 rebuild from the original plan,
    resolver evidence, stage authority, and input instead of trusting a
    coherently re-signed snapshot.
    """

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
    ) -> "_GroundedSourceOrigin":
        return cls(
            plan=plan,
            evidence_spans=tuple(
                resolver.resolve(item) for item in resolver.span_ids
            ),
            observation_stage_context_bytes=(
                canonical_json_bytes(dict(observation_stage_context))
                + b"\n"
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
        return "<_GroundedSourceOrigin body_free_validation_context>"

    def rebuild(self) -> "GroundedSourceSnapshot":
        resolver = EvidenceSpanResolver(self.evidence_spans)
        return build_grounded_source_snapshot(
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


@dataclass(frozen=True)
class GroundedSourceSnapshot:
    """Body-free source authority independently adapted before discovery."""

    plan_schema_version: str
    plan_adapter_version: str
    plan_generation_path: str
    observation_stage: str
    observation_stage_source_binding: ObservationStageSourceBinding
    semantic_source_roles: tuple[str, ...]
    semantic_restatement_witness_schema_version: str
    semantic_restatement_witness_adapter_version: str
    semantic_restatement_plan_binding_sha256: str
    source_semantic_restatement_witness_sha256: str
    source_observation_plan_sha256: str
    source_observation_stage_context_sha256: str
    source_reception_opportunity_plan_sha256: str | None
    response_eligibility_source_sha256: str
    response_eligibility: str
    response_eligibility_authority: TrustedResponseEligibilityAuthority
    source_policy_sha256: str
    source_id_alias_bindings: tuple[SourceIdAliasBinding, ...]
    grounded_parent_nucleus_count: int
    grounded_parent_relation_count: int
    grounded_parent_unknown_boundary_count: int
    evidence_ids: tuple[str, ...]
    text_evidence_ids: tuple[str, ...]
    nuclei: tuple[InventoryNucleusSource, ...]
    relations: tuple[InventoryRelationSource, ...]
    unknowns: tuple[InventoryUnknownSource, ...]
    reception_opportunities: tuple[InventoryReceptionSource, ...]
    safety_required_boundary_codes: tuple[str, ...]
    identity_claim_must_not_be_accepted_as_fact: bool
    preserved_unknown_boundary_ids: frozenset[str]
    answered_unknown_boundary_ids: frozenset[str]
    source_role_bindings: tuple[tuple[str, str], ...]
    resource_counts: tuple[tuple[str, int], ...]
    obligation_inventory_upper_bound: int
    ledger_source_authority: LedgerSourceAuthority

    def __deepcopy__(self, memo: dict[int, Any]) -> "GroundedSourceSnapshot":
        # The snapshot is frozen.  Keeping identity on deepcopy preserves its
        # module-owned request-local provenance capability without copying any
        # source body onto the artifact.
        return self


def _source_origin_capability_store():
    """Create the sole module-owned provenance store.

    The backing registry stays inside this closure.  Registration accepts only
    the exact internal origin type and independently rebuilds the proposed
    snapshot before issuing a capability, so an arbitrary object with a
    caller-defined ``rebuild`` method cannot become an authority.
    """

    registry: dict[
        int,
        tuple[
            weakref.ReferenceType[GroundedSourceSnapshot],
            _GroundedSourceOrigin,
        ],
    ] = {}

    def register(
        snapshot: GroundedSourceSnapshot,
        origin: _GroundedSourceOrigin,
    ) -> None:
        if type(snapshot) is not GroundedSourceSnapshot or type(
            origin
        ) is not _GroundedSourceOrigin:
            raise SemanticObligationInventoryError(
                "SOURCE_ORIGIN_REGISTRATION_INVALID"
            )
        try:
            expected = origin.rebuild()
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
            UnicodeError,
            RecursionError,
        ) as exc:
            raise SemanticObligationInventoryError(
                "SOURCE_ORIGIN_REGISTRATION_INVALID"
            ) from exc
        if snapshot != expected:
            raise SemanticObligationInventoryError(
                "SOURCE_ORIGIN_REGISTRATION_MISMATCH"
            )

        key = id(snapshot)

        def remove(
            reference: weakref.ReferenceType[GroundedSourceSnapshot],
            *,
            registry_key: int = key,
        ) -> None:
            current = registry.get(registry_key)
            if current is not None and current[0] is reference:
                registry.pop(registry_key, None)

        reference = weakref.ref(snapshot, remove)
        registry[key] = (reference, origin)

    def validate(
        snapshot: GroundedSourceSnapshot,
    ) -> tuple[str, ...]:
        current = registry.get(id(snapshot))
        if (
            current is None
            or current[0]() is not snapshot
            or type(current[1]) is not _GroundedSourceOrigin
        ):
            return ("SOURCE_ORIGIN_AUTHORITY_REQUIRED",)
        try:
            expected = current[1].rebuild()
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
            UnicodeError,
            RecursionError,
        ):
            return ("SOURCE_ORIGIN_REVALIDATION_FAILED",)
        if snapshot != expected:
            return ("SOURCE_ORIGIN_REBIND_MISMATCH",)
        return ()

    return register, validate


(
    _register_source_origin,
    _validate_source_origin_capability,
) = _source_origin_capability_store()


@dataclass(frozen=True)
class SemanticObligationInventoryResult:
    ledger: dict[str, Any]
    source_snapshot: GroundedSourceSnapshot
    resource_counts: dict[str, int]
    inventory_upper_bound: int


def _ordered_unique(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


def _machine_code(value: Any, *, fallback: str) -> str:
    text = _MACHINE_CODE_RE.sub("_", str(value or "").upper()).strip("_")
    if len(text) < 3:
        text = fallback
    return text[:64]


def _source_modality(value: Any) -> str:
    source = str(value or "").strip()
    if source not in _ALLOWED_SOURCE_MODALITIES:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"modality:{source or '<empty>'}"
        )
    return {
        "fact": "observed",
        "feeling": "reported",
        "refusal": "reported",
        "wish": "intended",
        "intention": "intended",
        "possibility": "possible",
        "uncertain": "unknown",
    }[source]


def _source_temporal_scope(value: Any) -> str:
    source = str(value or "").strip().lower()
    if source not in _ALLOWED_SOURCE_TIME_SCOPES:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"time_scope:{source or '<empty>'}"
        )
    if source in {"past", "reported_past"}:
        return "reported_past"
    if source in {"future", "present_to_future", "intended_future"}:
        return "intended_future"
    if source in {
        "current_input",
        "present",
        "continuing",
        "past_to_present",
        "current",
    }:
        return "current_input"
    if source in {"atemporal", "general"}:
        return "atemporal"
    return "unknown"


def _referent_scope(kind: str) -> str:
    if kind == "action":
        return "action"
    if kind in {"event", "change"}:
        return "event"
    if kind in _ALLOWED_NUCLEUS_KINDS:
        return "state"
    raise SemanticObligationInventoryError(
        "UNSUPPORTED_SOURCE_SEMANTIC", f"nucleus_kind:{kind}"
    )


def _topic_ids(role: str, anchors: Sequence[str]) -> tuple[str, ...]:
    material = _ordered_unique(anchors) or ("source_scope",)
    return tuple(
        "topic_" + artifact_sha256({"source_role": role, "anchor_id": item})[:16]
        for item in material
    )


def _relation_descriptor(relation_kind: str) -> tuple[str, str]:
    descriptor = _RELATION_DESCRIPTOR.get(relation_kind)
    if descriptor is None:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"relation:{relation_kind}"
        )
    return descriptor


def _source_ids(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    nucleus_ids: Sequence[str] | None = None,
    relation_ids: Sequence[str] | None = None,
    unknown_ids: Sequence[str] | None = None,
) -> tuple[tuple[str, str], ...]:
    reception = plan.response_plan.human_reception_plan
    opportunities = reception.opportunities if reception is not None else ()
    values = (
        *(("evidence", item) for item in resolver.span_ids),
        *(("nucleus", item) for item in (
            nucleus_ids
            if nucleus_ids is not None
            else tuple(row.nucleus_id for row in plan.nuclei)
        )),
        *(("relation", item) for item in (
            relation_ids
            if relation_ids is not None
            else tuple(row.relation_id for row in plan.relations)
        )),
        *(("unknown_boundary", item) for item in (
            unknown_ids
            if unknown_ids is not None
            else tuple(row.unknown_id for row in plan.unknown_boundaries)
        )),
        *(("reception_opportunity", item.opportunity_id) for item in opportunities),
    )
    pairs = tuple((kind, str(source_id).strip()) for kind, source_id in values)
    if len(pairs) != len(set(pairs)):
        raise SemanticObligationInventoryError("SOURCE_ID_DUPLICATE")
    if any(
        kind not in _ALIAS_PREFIX or not _BODY_FREE_SOURCE_ID_RE.fullmatch(source_id)
        for kind, source_id in pairs
    ):
        raise SemanticObligationInventoryError("SOURCE_ID_INVALID")
    return tuple(sorted(pairs))


def _alias_for(source_kind: str, actual_source_id: str) -> str:
    prefix = _ALIAS_PREFIX[source_kind]
    digest = artifact_sha256(
        {
            "schema_version": SOURCE_ID_ALIAS_SCHEMA,
            "source_kind": source_kind,
            "actual_source_id": actual_source_id,
        }
    )[:20]
    return f"{prefix}_{digest}"


def _alias_bindings(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    nucleus_ids: Sequence[str] | None = None,
    relation_ids: Sequence[str] | None = None,
    unknown_ids: Sequence[str] | None = None,
) -> tuple[SourceIdAliasBinding, ...]:
    bindings = tuple(
        SourceIdAliasBinding(
            source_kind=kind,
            source_owner=_SOURCE_OWNER[kind],
            actual_source_id=source_id,
            alias_source_id=_alias_for(kind, source_id),
        )
        for kind, source_id in _source_ids(
            plan,
            resolver,
            nucleus_ids=nucleus_ids,
            relation_ids=relation_ids,
            unknown_ids=unknown_ids,
        )
    )
    aliases = tuple(item.alias_source_id for item in bindings)
    if len(aliases) != len(set(aliases)) or any(
        not _MACHINE_SOURCE_ID_RE.fullmatch(alias) for alias in aliases
    ):
        raise SemanticObligationInventoryError("SOURCE_ID_ALIAS_COLLISION")
    return bindings


def _alias_index(
    bindings: Sequence[SourceIdAliasBinding],
) -> dict[tuple[str, str], str]:
    return {
        (item.source_kind, item.actual_source_id): item.alias_source_id
        for item in bindings
    }


def _actual_index(
    bindings: Sequence[SourceIdAliasBinding],
) -> dict[str, tuple[str, str]]:
    return {
        item.alias_source_id: (item.source_kind, item.actual_source_id)
        for item in bindings
    }


def _resource_counts(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> dict[str, int]:
    reception = plan.response_plan.human_reception_plan
    opportunities = reception.opportunities if reception is not None else ()
    counts = {
        "evidence_span_count": len(resolver.span_ids),
        "text_evidence_span_count": sum(
            resolver.resolve(span_id).source_field in {"memo", "memo_action"}
            for span_id in resolver.span_ids
        ),
        "nucleus_count": len(plan.nuclei),
        "relation_count": len(plan.relations),
        "unknown_boundary_count": len(plan.unknown_boundaries),
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": len(
            set(plan.safety_policy.required_boundary_codes)
        ),
        "reception_opportunity_count": len(opportunities),
    }
    obligation_inventory_upper_bound(counts)
    return counts


def obligation_inventory_upper_bound(source_counts: Mapping[str, int]) -> int:
    """Return the exact Step 1 request-relative, lossless inventory bound."""

    keys = {
        "evidence_span_count",
        "text_evidence_span_count",
        "nucleus_count",
        "relation_count",
        "unknown_boundary_count",
        "safety_policy_count",
        "safety_required_boundary_code_count",
        "reception_opportunity_count",
    }
    if set(source_counts) != keys or any(
        type(source_counts[key]) is not int or source_counts[key] < 0
        for key in keys
    ):
        raise SemanticObligationInventoryError("SOURCE_RESOURCE_COUNTS_INVALID")
    evidence = source_counts["evidence_span_count"]
    text = source_counts["text_evidence_span_count"]
    nuclei = source_counts["nucleus_count"]
    relations = source_counts["relation_count"]
    unknowns = source_counts["unknown_boundary_count"]
    safety = source_counts["safety_policy_count"]
    boundaries = source_counts["safety_required_boundary_code_count"]
    opportunities = source_counts["reception_opportunity_count"]
    relation_bound = min(nuclei * max(0, nuclei - 1), text + 9)
    if (
        text > evidence
        or nuclei > evidence
        or relations > relation_bound
        or unknowns > 11
        or safety != 1
        or boundaries > 9
        or opportunities > 4
    ):
        raise SemanticObligationInventoryError("SOURCE_RESOURCE_COUNTS_INVALID")
    return (
        (4 * nuclei + relations + unknowns)
        * (safety + boundaries + 1)
        * (opportunities + 2)
    )


def validate_obligation_inventory_count(
    source_counts: Mapping[str, int], obligation_count: Any
) -> tuple[str, ...]:
    if type(obligation_count) is not int or obligation_count < 0:
        return ("OBLIGATION_INVENTORY_COUNT_INVALID",)
    try:
        upper_bound = obligation_inventory_upper_bound(source_counts)
    except SemanticObligationInventoryError:
        return ("SOURCE_RESOURCE_COUNTS_INVALID",)
    return (
        ("OBLIGATION_INVENTORY_OVERFLOW",)
        if obligation_count > upper_bound
        else ()
    )


def _eligibility_from_route(
    *,
    content_policy: str,
    material_quality: str,
    response_kind: str,
    safety_kind: str,
) -> str:
    if content_policy == "separate_safety_owner":
        if safety_kind not in _SEPARATE_SAFETY_KINDS:
            raise SemanticObligationInventoryError(
                "RESPONSE_ELIGIBILITY_SOURCE_MISMATCH"
            )
        return "separate_safety_owner"
    if content_policy != "grounded_plan_only":
        raise SemanticObligationInventoryError("RESPONSE_ELIGIBILITY_SOURCE_MISMATCH")
    if safety_kind == _SELF_DENIAL_SAFE:
        expected_response_kind = _SELF_DENIAL_SAFE
    elif safety_kind == _SAFE_OBSERVATION:
        expected_response_kind = {
            "grounded": "normal_observation",
            "short_state_sufficient": "short_state_observation",
            "limited_grounding": "limited_grounding_observation",
            "labels_only_limited": "labels_only_limited_observation",
            "empty": "unavailable",
        }.get(material_quality)
    else:
        expected_response_kind = None
    if expected_response_kind is None or response_kind != expected_response_kind:
        raise SemanticObligationInventoryError("RESPONSE_ELIGIBILITY_SOURCE_MISMATCH")
    # The existing Grounded owner distinguishes a short but sufficient state
    # from genuinely limited/label-only/unavailable material.  NLS v3 maps
    # that upstream boundary; it does not infer availability from text length.
    return (
        "source_unavailable"
        if material_quality in {"limited_grounding", "labels_only_limited", "empty"}
        else "normal_surface"
    )


def _eligibility_authority(plan: GroundedObservationPlan) -> TrustedResponseEligibilityAuthority:
    content_policy = str(plan.surface_policy.content_source)
    material_quality = str(plan.input_profile.material_quality)
    response_kind = str(plan.response_plan.response_kind)
    safety_kind = str(plan.safety_policy.safety_kind)
    eligibility = _eligibility_from_route(
        content_policy=content_policy,
        material_quality=material_quality,
        response_kind=response_kind,
        safety_kind=safety_kind,
    )
    artifact = {
        "schema_version": ELIGIBILITY_SOURCE_SCHEMA,
        "adapter_version": RESPONSE_ELIGIBILITY_ADAPTER_VERSION,
        "authority_owner": "upstream_grounded_observation_router",
        "source_content_policy": content_policy,
        "source_material_quality": material_quality,
        "source_response_kind": response_kind,
        "source_safety_kind": safety_kind,
        "response_eligibility": eligibility,
        "body_free": True,
    }
    return TrustedResponseEligibilityAuthority(
        response_eligibility=eligibility,
        source_content_policy=content_policy,
        source_material_quality=material_quality,
        source_response_kind=response_kind,
        source_safety_kind=safety_kind,
        source_commitment_sha256=artifact_sha256(artifact),
    )


def _eligibility_authority_from_snapshot(
    snapshot: GroundedSourceSnapshot,
) -> TrustedResponseEligibilityAuthority:
    source = snapshot.response_eligibility_authority
    eligibility = _eligibility_from_route(
        content_policy=source.source_content_policy,
        material_quality=source.source_material_quality,
        response_kind=source.source_response_kind,
        safety_kind=source.source_safety_kind,
    )
    artifact = {
        "schema_version": ELIGIBILITY_SOURCE_SCHEMA,
        "adapter_version": RESPONSE_ELIGIBILITY_ADAPTER_VERSION,
        "authority_owner": "upstream_grounded_observation_router",
        "source_content_policy": source.source_content_policy,
        "source_material_quality": source.source_material_quality,
        "source_response_kind": source.source_response_kind,
        "source_safety_kind": source.source_safety_kind,
        "response_eligibility": eligibility,
        "body_free": True,
    }
    return TrustedResponseEligibilityAuthority(
        response_eligibility=eligibility,
        source_content_policy=source.source_content_policy,
        source_material_quality=source.source_material_quality,
        source_response_kind=source.source_response_kind,
        source_safety_kind=source.source_safety_kind,
        source_commitment_sha256=artifact_sha256(artifact),
    )


def _nucleus_source(
    row: GroundedSemanticNucleus,
    *,
    alias_by_source: Mapping[tuple[str, str], str],
    required_ids: frozenset[str],
    fact_boundary_ids: frozenset[str],
) -> InventoryNucleusSource:
    kind = str(row.kind)
    if kind not in _ALLOWED_NUCLEUS_KINDS:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"nucleus_kind:{kind}"
        )
    polarity = str(row.semantic_frame.polarity)
    source_fields = _ordered_unique(row.source_fields)
    grounding_kind = str(row.grounding_kind)
    claim_scope = str(row.allowed_claim_scope)
    retention = str(row.retention)
    if (
        polarity not in _ALLOWED_SOURCE_POLARITIES
        or not set(source_fields) <= _ALLOWED_SOURCE_FIELDS
        or grounding_kind not in _ALLOWED_GROUNDING_KINDS
        or claim_scope not in _ALLOWED_CLAIM_SCOPES
        or retention not in _ALLOWED_RETENTIONS
    ):
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"nucleus:{row.nucleus_id}"
        )
    source_modality = str(row.semantic_frame.modality)
    source_time_scope = str(row.semantic_frame.time_scope)
    modality = _source_modality(source_modality)
    if kind == "self_evaluation" and row.nucleus_id in fact_boundary_ids:
        modality = "reported"
    topic_anchors = (
        row.source_meaning_block_keys
        or row.semantic_frame.target_anchor_ids
        or row.source_span_ids
        or (row.nucleus_id,)
    )
    forbidden = list(row.forbidden_inference_codes)
    if grounding_kind == "bounded_structural_inference":
        forbidden.append("NO_BOUNDED_INFERENCE_UPGRADE")
    if claim_scope == "selected_label_only":
        forbidden.append("NO_LABEL_TO_EVENT_INFERENCE")
    return InventoryNucleusSource(
        source_id=alias_by_source[("nucleus", row.nucleus_id)],
        actual_source_id=row.nucleus_id,
        source_role="original_input",
        kind=kind,
        evidence_ids=_ordered_unique(
            alias_by_source[("evidence", item)] for item in row.source_span_ids
        ),
        source_fields=source_fields,
        surface_anchor_ids=_ordered_unique(row.surface_anchor_ids),
        source_anchor_ids=_ordered_unique(row.semantic_frame.target_anchor_ids),
        source_meaning_block_keys=_ordered_unique(row.source_meaning_block_keys),
        source_claim_ids=_ordered_unique(row.source_claim_ids),
        allowed_claim_scope=claim_scope,
        grounding_kind=grounding_kind,
        source_actor=str(row.semantic_frame.actor),
        source_predicate_kind=str(row.semantic_frame.predicate_kind),
        source_modality=source_modality,
        source_time_scope=source_time_scope,
        source_degree=str(row.semantic_frame.degree),
        source_attribute_codes=_ordered_unique(row.semantic_frame.attribute_codes),
        polarity=polarity,
        modality=modality,
        temporal_scope=_source_temporal_scope(source_time_scope),
        topic_scope_ids=_topic_ids("original_input", topic_anchors),
        referent_scope=_referent_scope(kind),
        retention=retention,
        required=row.nucleus_id in required_ids or retention == "required",
        forbidden_claim_codes=_ordered_unique(
            _machine_code(code, fallback="SOURCE_BOUNDED") for code in forbidden
        ),
        fact_boundary=row.nucleus_id in fact_boundary_ids,
    )


def _semantic_unit_source(
    row: GroundedSemanticUnitWitness,
    *,
    parent: GroundedSemanticNucleus,
    alias_by_source: Mapping[tuple[str, str], str],
    fact_boundary_ids: frozenset[str],
) -> InventoryNucleusSource:
    if (
        row.parent_nucleus_id != parent.nucleus_id
        or row.source_span_id not in parent.source_span_ids
        or row.kind not in _ALLOWED_NUCLEUS_KINDS
        or row.required is not True
    ):
        raise SemanticObligationInventoryError(
            "SEMANTIC_UNIT_SOURCE_INVALID", row.unit_id
        )
    source_modality = str(row.source_modality)
    source_time_scope = str(row.source_time_scope)
    return InventoryNucleusSource(
        source_id=alias_by_source[("nucleus", row.unit_id)],
        actual_source_id=row.unit_id,
        source_role="original_input",
        kind=str(row.kind),
        evidence_ids=(alias_by_source[("evidence", row.source_span_id)],),
        source_fields=_ordered_unique(parent.source_fields),
        surface_anchor_ids=(row.unit_id,),
        source_anchor_ids=(row.unit_id,),
        source_meaning_block_keys=(
            f"semantic_decomposition:{row.connective_code.lower()}:{row.unit_role}",
        ),
        source_claim_ids=(
            f"semantic_decomposition:{row.unit_role}",
        ),
        allowed_claim_scope="explicit_current_input",
        grounding_kind="explicit",
        source_actor=str(parent.semantic_frame.actor),
        source_predicate_kind=str(row.source_predicate_kind),
        source_modality=source_modality,
        source_time_scope=source_time_scope,
        source_degree="source_bounded",
        source_attribute_codes=(
            "adapter:semantic_decomposition_v3",
            f"connective:{row.connective_code.lower()}",
            f"unit_role:{row.unit_role}",
        ),
        polarity=str(row.polarity),
        modality=_source_modality(source_modality),
        temporal_scope=_source_temporal_scope(source_time_scope),
        topic_scope_ids=_topic_ids("original_input", (row.unit_id,)),
        referent_scope=_referent_scope(str(row.kind)),
        retention="required",
        required=True,
        forbidden_claim_codes=_ordered_unique(
            _machine_code(code, fallback="SOURCE_BOUNDED")
            for code in row.forbidden_claim_codes
        ),
        fact_boundary=parent.nucleus_id in fact_boundary_ids,
    )


def _combined_scalar(values: Sequence[str], *, default: str) -> str:
    unique = tuple(dict.fromkeys(value for value in values if value))
    return unique[0] if len(unique) == 1 else default


def _relation_source(
    row: GroundedSemanticRelation,
    *,
    semantic_witness: GroundedSemanticRestatementRelationWitness,
    alias_by_source: Mapping[tuple[str, str], str],
    nucleus_by_actual_id: Mapping[str, InventoryNucleusSource],
    required_ids: frozenset[str],
) -> InventoryRelationSource:
    if (
        row.from_nucleus_id not in nucleus_by_actual_id
        or row.to_nucleus_id not in nucleus_by_actual_id
    ):
        raise SemanticObligationInventoryError(
            "OBLIGATION_SOURCE_REFERENCE_UNRESOLVED", row.relation_id
        )
    relation_kind = str(row.type)
    relation_type, direction = _relation_descriptor(relation_kind)
    grounding_kind = str(row.grounding_kind)
    retention = str(row.retention)
    if semantic_witness.relation_id != row.relation_id:
        raise SemanticObligationInventoryError(
            "SEMANTIC_RESTATEMENT_WITNESS_RELATION_MISMATCH", row.relation_id
        )
    endpoint_semantics = str(semantic_witness.endpoint_semantic_relation)
    unit_actual_ids = tuple(
        str(item).strip()
        for item in semantic_witness.semantic_restatement_unit_nucleus_ids
    )
    if (
        grounding_kind not in _ALLOWED_GROUNDING_KINDS
        or retention not in _ALLOWED_RETENTIONS
        or endpoint_semantics not in _ALLOWED_ENDPOINT_SEMANTICS
        or len(unit_actual_ids) != len(set(unit_actual_ids))
        or not set(unit_actual_ids) <= set(nucleus_by_actual_id)
        or (
            endpoint_semantics == "semantic_restatement"
            and (
                len(unit_actual_ids) < 2
                or not {row.from_nucleus_id, row.to_nucleus_id}
                <= set(unit_actual_ids)
            )
        )
        or (
            endpoint_semantics == "distinct_meanings"
            and bool(unit_actual_ids)
        )
    ):
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"relation:{row.relation_id}"
        )
    endpoints = (
        nucleus_by_actual_id[row.from_nucleus_id],
        nucleus_by_actual_id[row.to_nucleus_id],
    )
    semantic_unit_sources = (
        tuple(nucleus_by_actual_id[item] for item in unit_actual_ids)
        if unit_actual_ids
        else endpoints
    )
    polarities = [item.polarity for item in endpoints]
    polarity = _combined_scalar(polarities, default="mixed")
    if relation_type in {"contrasts_with", "coexists_with"} and len(set(polarities)) > 1:
        polarity = "mixed"
    if relation_kind == "uncertain_connection":
        modality = "unknown"
    elif grounding_kind == "bounded_structural_inference":
        modality = "possible"
    elif grounding_kind == "user_stated_relation":
        modality = "reported"
    else:
        modality = _combined_scalar(
            [item.modality for item in endpoints], default="unknown"
        )
    temporal_scope = _combined_scalar(
        [item.temporal_scope for item in endpoints], default="unknown"
    )
    forbidden = ["NO_RELATION_DIRECTION_REVERSAL"]
    if relation_kind == "uncertain_connection":
        forbidden.append("NO_UNCERTAIN_CONNECTION_UPGRADE")
    if grounding_kind == "bounded_structural_inference":
        forbidden.append("NO_BOUNDED_INFERENCE_UPGRADE")
    if relation_type == "supports_without_guarantee":
        forbidden.append("NO_CAUSAL_GUARANTEE")
    if endpoint_semantics == "semantic_restatement":
        forbidden.append("NO_SEMANTIC_RESTATEMENT_DEPTH_INFLATION")
    evidence_actual_ids = _ordered_unique(
        (
            *row.source_span_ids,
            *(item for endpoint in semantic_unit_sources for item in (
                _actual_evidence_ids(endpoint, alias_by_source)
            )),
        )
    )
    return InventoryRelationSource(
        source_id=alias_by_source[("relation", row.relation_id)],
        actual_source_id=row.relation_id,
        source_role="original_input",
        source_relation_kind=relation_kind,
        grounding_kind=grounding_kind,
        endpoint_semantic_relation=endpoint_semantics,
        semantic_restatement_unit_nucleus_ids=tuple(
            alias_by_source[("nucleus", item)] for item in unit_actual_ids
        ),
        relation_type=relation_type,
        relation_direction=direction,
        from_nucleus_id=alias_by_source[("nucleus", row.from_nucleus_id)],
        to_nucleus_id=alias_by_source[("nucleus", row.to_nucleus_id)],
        source_evidence_ids=_ordered_unique(
            alias_by_source[("evidence", item)] for item in row.source_span_ids
        ),
        evidence_ids=_ordered_unique(
            alias_by_source[("evidence", item)] for item in evidence_actual_ids
        ),
        source_relation_ids=_ordered_unique(row.source_relation_ids),
        source_meaning_arc_keys=_ordered_unique(row.source_meaning_arc_keys),
        polarity=polarity,
        modality=modality,
        temporal_scope=temporal_scope,
        topic_scope_ids=_ordered_unique(
            item
            for endpoint in semantic_unit_sources
            for item in endpoint.topic_scope_ids
        ),
        retention=retention,
        required=row.relation_id in required_ids or retention == "required",
        forbidden_claim_codes=_ordered_unique(forbidden),
    )


def _semantic_link_source(
    row: GroundedSemanticLinkWitness,
    *,
    alias_by_source: Mapping[tuple[str, str], str],
    nucleus_by_actual_id: Mapping[str, InventoryNucleusSource],
) -> InventoryRelationSource:
    if (
        row.from_unit_id not in nucleus_by_actual_id
        or row.to_unit_id not in nucleus_by_actual_id
        or row.from_unit_id == row.to_unit_id
        or row.required is not True
    ):
        raise SemanticObligationInventoryError(
            "SEMANTIC_LINK_SOURCE_INVALID", row.link_id
        )
    endpoints = (
        nucleus_by_actual_id[row.from_unit_id],
        nucleus_by_actual_id[row.to_unit_id],
    )
    polarities = [item.polarity for item in endpoints]
    polarity = _combined_scalar(polarities, default="mixed")
    if row.relation_type in {"contrasts_with", "coexists_with"} and len(
        set(polarities)
    ) > 1:
        polarity = "mixed"
    evidence_ids = _ordered_unique(
        item for endpoint in endpoints for item in endpoint.evidence_ids
    )
    return InventoryRelationSource(
        source_id=alias_by_source[("relation", row.link_id)],
        actual_source_id=row.link_id,
        source_role="original_input",
        source_relation_kind=f"v3_{row.connective_code.lower()}",
        grounding_kind="user_stated_relation",
        endpoint_semantic_relation="distinct_meanings",
        semantic_restatement_unit_nucleus_ids=(),
        relation_type=str(row.relation_type),
        relation_direction=str(row.relation_direction),
        from_nucleus_id=alias_by_source[("nucleus", row.from_unit_id)],
        to_nucleus_id=alias_by_source[("nucleus", row.to_unit_id)],
        source_evidence_ids=(
            alias_by_source[("evidence", row.source_span_id)],
        ),
        evidence_ids=evidence_ids,
        source_relation_ids=(f"adapter:{row.connective_code.lower()}",),
        source_meaning_arc_keys=(row.link_id,),
        polarity=polarity,
        modality="reported",
        temporal_scope=_combined_scalar(
            [item.temporal_scope for item in endpoints], default="unknown"
        ),
        topic_scope_ids=_ordered_unique(
            item for endpoint in endpoints for item in endpoint.topic_scope_ids
        ),
        retention="required",
        required=True,
        forbidden_claim_codes=_ordered_unique(row.forbidden_claim_codes),
    )


def _actual_evidence_ids(
    source: InventoryNucleusSource,
    alias_by_source: Mapping[tuple[str, str], str],
) -> tuple[str, ...]:
    reverse = {alias: actual for (kind, actual), alias in alias_by_source.items() if kind == "evidence"}
    return tuple(reverse[item] for item in source.evidence_ids)


def _unknown_source(
    row: GroundedUnknownBoundary,
    *,
    alias_by_source: Mapping[tuple[str, str], str],
    nucleus_by_actual_id: Mapping[str, InventoryNucleusSource],
    actual_nucleus_expansion: Mapping[str, tuple[str, ...]],
    required: bool,
) -> InventoryUnknownSource:
    expanded_actual_ids = _ordered_unique(
        expanded
        for source_id in row.affected_nucleus_ids
        for expanded in actual_nucleus_expansion.get(source_id, (source_id,))
    )
    if not set(expanded_actual_ids) <= set(nucleus_by_actual_id):
        raise SemanticObligationInventoryError(
            "OBLIGATION_SOURCE_REFERENCE_UNRESOLVED", row.unknown_id
        )
    surface_policy = str(row.surface_policy)
    if surface_policy not in _ALLOWED_UNKNOWN_POLICIES:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"unknown:{row.unknown_id}"
        )
    affected = tuple(
        alias_by_source[("nucleus", item)] for item in expanded_actual_ids
    )
    topics = _ordered_unique(
        item
        for nucleus_id in expanded_actual_ids
        for item in nucleus_by_actual_id[nucleus_id].topic_scope_ids
    ) or _topic_ids("original_input", (row.unknown_id,))
    return InventoryUnknownSource(
        source_id=alias_by_source[("unknown_boundary", row.unknown_id)],
        actual_source_id=row.unknown_id,
        source_role="original_input",
        source_dimension=str(row.dimension),
        dimension_code=_machine_code(row.dimension, fallback="UNKNOWN_DIMENSION"),
        affected_nucleus_ids=_ordered_unique(affected),
        evidence_ids=_ordered_unique(
            alias_by_source[("evidence", item)] for item in row.evidence_span_ids
        ),
        topic_scope_ids=topics,
        surface_policy=surface_policy,
        required=required,
    )


def _explicit_unknown_source(
    row: GroundedExplicitUnknownWitness,
    *,
    alias_by_source: Mapping[tuple[str, str], str],
    nucleus_by_actual_id: Mapping[str, InventoryNucleusSource],
) -> InventoryUnknownSource:
    if (
        row.required is not True
        or not row.affected_unit_ids
        or not set(row.affected_unit_ids) <= set(nucleus_by_actual_id)
    ):
        raise SemanticObligationInventoryError(
            "EXPLICIT_UNKNOWN_SOURCE_INVALID", row.unknown_id
        )
    affected = tuple(
        alias_by_source[("nucleus", item)] for item in row.affected_unit_ids
    )
    return InventoryUnknownSource(
        source_id=alias_by_source[("unknown_boundary", row.unknown_id)],
        actual_source_id=row.unknown_id,
        source_role="original_input",
        source_dimension=row.dimension,
        dimension_code=_machine_code(
            row.dimension, fallback="EXPLICIT_UNKNOWN"
        ),
        affected_nucleus_ids=_ordered_unique(affected),
        evidence_ids=(
            alias_by_source[("evidence", row.source_span_id)],
        ),
        topic_scope_ids=_ordered_unique(
            topic
            for item in row.affected_unit_ids
            for topic in nucleus_by_actual_id[item].topic_scope_ids
        ),
        surface_policy="do_not_claim",
        required=True,
    )


def _reception_source(
    row: GroundedReceptionOpportunity,
    *,
    alias_by_source: Mapping[tuple[str, str], str],
    nucleus_by_actual_id: Mapping[str, InventoryNucleusSource],
    actual_nucleus_expansion: Mapping[str, tuple[str, ...]],
) -> InventoryReceptionSource:
    expanded_targets = _ordered_unique(
        expanded
        for source_id in row.target_nucleus_ids
        for expanded in actual_nucleus_expansion.get(source_id, (source_id,))
    )
    expanded_supports = _ordered_unique(
        expanded
        for source_id in row.support_nucleus_ids
        for expanded in actual_nucleus_expansion.get(source_id, (source_id,))
    )
    if not set((*expanded_targets, *expanded_supports)) <= set(
        nucleus_by_actual_id
    ):
        raise SemanticObligationInventoryError(
            "OBLIGATION_SOURCE_REFERENCE_UNRESOLVED", row.opportunity_id
        )
    if row.reception_act not in _RECEPTION_ACT or row.retention not in _ALLOWED_RETENTIONS:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"reception:{row.opportunity_id}"
        )
    if type(row.priority) is not int or row.priority <= 0:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"reception_priority:{row.opportunity_id}"
        )
    if type(row.source_field_count) is not int or row.source_field_count < 0:
        raise SemanticObligationInventoryError(
            "UNSUPPORTED_SOURCE_SEMANTIC", f"reception_fields:{row.opportunity_id}"
        )
    return InventoryReceptionSource(
        source_id=alias_by_source[("reception_opportunity", row.opportunity_id)],
        actual_source_id=row.opportunity_id,
        source_role="original_input",
        family=str(row.family),
        source_reception_act=str(row.reception_act),
        reception_act=_RECEPTION_ACT[row.reception_act],
        target_nucleus_ids=_ordered_unique(
            alias_by_source[("nucleus", item)] for item in expanded_targets
        ),
        support_nucleus_ids=_ordered_unique(
            alias_by_source[("nucleus", item)] for item in expanded_supports
        ),
        evidence_ids=_ordered_unique(
            alias_by_source[("evidence", item)]
            for item in row.source_evidence_span_ids
        ),
        retention=str(row.retention),
        priority=row.priority,
        source_field_count=row.source_field_count,
        safety_required=bool(row.safety_required),
    )


def _plan_native_artifact(
    *,
    plan_schema_version: str,
    plan_adapter_version: str,
    plan_generation_path: str,
    semantic_restatement_witness_schema_version: str,
    semantic_restatement_witness_adapter_version: str,
    semantic_restatement_plan_binding_sha256: str,
    source_semantic_restatement_witness_sha256: str,
    bindings: Sequence[SourceIdAliasBinding],
    evidence_ids: Sequence[str],
    nuclei: Sequence[InventoryNucleusSource],
    relations: Sequence[InventoryRelationSource],
    unknowns: Sequence[InventoryUnknownSource],
    safety_required_boundary_codes: Sequence[str],
    identity_claim_must_not_be_accepted_as_fact: bool,
    eligibility: TrustedResponseEligibilityAuthority,
) -> dict[str, Any]:
    actual_by_alias = _actual_index(bindings)

    def actual(alias: str, expected_kind: str) -> str:
        kind, source_id = actual_by_alias[alias]
        if kind != expected_kind:
            raise SemanticObligationInventoryError("SOURCE_ID_ALIAS_KIND_MISMATCH")
        return source_id

    return {
        "schema_version": SOURCE_SNAPSHOT_SCHEMA,
        "plan_schema_version": plan_schema_version,
        "plan_adapter_version": plan_adapter_version,
        "plan_generation_path": plan_generation_path,
        "semantic_restatement_witness": {
            "schema_version": semantic_restatement_witness_schema_version,
            "adapter_version": semantic_restatement_witness_adapter_version,
            "plan_binding_sha256": semantic_restatement_plan_binding_sha256,
            "witness_sha256": source_semantic_restatement_witness_sha256,
        },
        "evidence_ids": [actual(item, "evidence") for item in evidence_ids],
        "nuclei": [
            {
                "nucleus_id": row.actual_source_id,
                "kind": row.kind,
                "source_span_ids": [
                    actual(item, "evidence") for item in row.evidence_ids
                ],
                "source_fields": list(row.source_fields),
                "surface_anchor_ids": list(row.surface_anchor_ids),
                "target_anchor_ids": list(row.source_anchor_ids),
                "source_meaning_block_keys": list(row.source_meaning_block_keys),
                "source_claim_ids": list(row.source_claim_ids),
                "allowed_claim_scope": row.allowed_claim_scope,
                "grounding_kind": row.grounding_kind,
                "semantic_frame": {
                    "actor": row.source_actor,
                    "predicate_kind": row.source_predicate_kind,
                    "polarity": row.polarity,
                    "modality": row.source_modality,
                    "time_scope": row.source_time_scope,
                    "degree": row.source_degree,
                    "attribute_codes": list(row.source_attribute_codes),
                },
                "retention": row.retention,
                "required": row.required,
                "forbidden_claim_codes": list(row.forbidden_claim_codes),
                "fact_boundary": row.fact_boundary,
            }
            for row in nuclei
        ],
        "relations": [
            {
                "relation_id": row.actual_source_id,
                "type": row.source_relation_kind,
                "grounding_kind": row.grounding_kind,
                "endpoint_semantic_relation": row.endpoint_semantic_relation,
                "semantic_restatement_unit_nucleus_ids": [
                    actual(item, "nucleus")
                    for item in row.semantic_restatement_unit_nucleus_ids
                ],
                "from_nucleus_id": actual(row.from_nucleus_id, "nucleus"),
                "to_nucleus_id": actual(row.to_nucleus_id, "nucleus"),
                "source_span_ids": [
                    actual(item, "evidence") for item in row.source_evidence_ids
                ],
                "source_relation_ids": list(row.source_relation_ids),
                "source_meaning_arc_keys": list(row.source_meaning_arc_keys),
                "retention": row.retention,
                "required": row.required,
            }
            for row in relations
        ],
        "unknown_boundaries": [
            {
                "unknown_id": row.actual_source_id,
                "dimension": row.source_dimension,
                "affected_nucleus_ids": [
                    actual(item, "nucleus") for item in row.affected_nucleus_ids
                ],
                "evidence_span_ids": [
                    actual(item, "evidence") for item in row.evidence_ids
                ],
                "surface_policy": row.surface_policy,
            }
            for row in unknowns
        ],
        "routing": {
            "content_policy": eligibility.source_content_policy,
            "material_quality": eligibility.source_material_quality,
            "response_kind": eligibility.source_response_kind,
            "safety_kind": eligibility.source_safety_kind,
        },
        "safety": {
            "identity_claim_must_not_be_accepted_as_fact": (
                identity_claim_must_not_be_accepted_as_fact
            ),
            "required_boundary_codes": list(safety_required_boundary_codes),
        },
        "float_fields_consumed": False,
        "observation_stage_consumed": False,
        "source_role_consumed": False,
        "body_free": True,
    }


def _reception_native_artifact(
    opportunities: Sequence[InventoryReceptionSource],
    bindings: Sequence[SourceIdAliasBinding],
) -> dict[str, Any] | None:
    if not opportunities:
        return None
    actual_by_alias = _actual_index(bindings)

    def actual(alias: str, expected_kind: str) -> str:
        kind, source_id = actual_by_alias[alias]
        if kind != expected_kind:
            raise SemanticObligationInventoryError("SOURCE_ID_ALIAS_KIND_MISMATCH")
        return source_id

    return {
        "schema_version": RECEPTION_SOURCE_SCHEMA,
        "opportunities": [
            {
                "opportunity_id": row.actual_source_id,
                "family": row.family,
                "reception_act": row.source_reception_act,
                "target_nucleus_ids": [
                    actual(item, "nucleus") for item in row.target_nucleus_ids
                ],
                "support_nucleus_ids": [
                    actual(item, "nucleus") for item in row.support_nucleus_ids
                ],
                "source_evidence_span_ids": [
                    actual(item, "evidence") for item in row.evidence_ids
                ],
                "retention": row.retention,
                "priority": row.priority,
                "source_field_count": row.source_field_count,
                "safety_required": row.safety_required,
            }
            for row in opportunities
        ],
        "moves_consumed_as_authority": False,
        "primary_act_consumed_as_authority": False,
        "secondary_act_consumed_as_authority": False,
        "body_free": True,
    }


def _source_semantics(
    nuclei: Sequence[InventoryNucleusSource],
    relations: Sequence[InventoryRelationSource],
    unknowns: Sequence[InventoryUnknownSource],
) -> tuple[TrustedSourceSemantic, ...]:
    return tuple(
        [
            TrustedSourceSemantic(
                source_id=row.source_id,
                source_authority_code="nucleus",
                source_role=row.source_role,
                polarity=row.polarity,
                modality=row.modality,
                temporal_scope=row.temporal_scope,
                topic_scope_ids=row.topic_scope_ids,
                referent_scope=row.referent_scope,
                relation_type=None,
                relation_direction=None,
            )
            for row in nuclei
        ]
        + [
            TrustedSourceSemantic(
                source_id=row.source_id,
                source_authority_code="relation",
                source_role=row.source_role,
                polarity=row.polarity,
                modality=row.modality,
                temporal_scope=row.temporal_scope,
                topic_scope_ids=row.topic_scope_ids,
                referent_scope="relation",
                relation_type=row.relation_type,
                relation_direction=row.relation_direction,
            )
            for row in relations
        ]
        + [
            TrustedSourceSemantic(
                source_id=row.source_id,
                source_authority_code="unknown_boundary",
                source_role=row.source_role,
                polarity="unknown",
                modality="unknown",
                temporal_scope="unknown",
                topic_scope_ids=row.topic_scope_ids,
                referent_scope="unknown",
                relation_type=None,
                relation_direction=None,
            )
            for row in unknowns
        ]
    )


def _ledger_authority(
    *,
    plan_hash: str,
    stage_hash: str,
    reception_hash: str | None,
    eligibility: TrustedResponseEligibilityAuthority,
    evidence_ids: Sequence[str],
    nuclei: Sequence[InventoryNucleusSource],
    relations: Sequence[InventoryRelationSource],
    unknowns: Sequence[InventoryUnknownSource],
    opportunities: Sequence[InventoryReceptionSource],
    role_bindings: Sequence[tuple[str, str]],
    inventory_bound: int,
) -> LedgerSourceAuthority:
    return LedgerSourceAuthority(
        source_observation_plan_sha256=plan_hash,
        source_observation_stage_context_sha256=stage_hash,
        source_reception_opportunity_plan_sha256=reception_hash,
        response_eligibility_source_sha256=eligibility.source_commitment_sha256,
        response_eligibility=eligibility.response_eligibility,
        source_policy_sha256=FROZEN_SOURCE_POLICY_SHA256,
        allowed_source_owners=tuple(ALLOWED_SOURCE_OWNERS),
        evidence_ids=frozenset(evidence_ids),
        nucleus_ids=frozenset(row.source_id for row in nuclei),
        relation_ids=frozenset(row.source_id for row in relations),
        unknown_boundary_ids=frozenset(row.source_id for row in unknowns),
        reception_opportunity_ids=frozenset(row.source_id for row in opportunities),
        topic_scope_ids=frozenset(
            item
            for row in (*nuclei, *relations, *unknowns)
            for item in row.topic_scope_ids
        ),
        allowed_source_roles=("original_input",),
        source_role_bindings=tuple(role_bindings),
        source_semantics=_source_semantics(nuclei, relations, unknowns),
        obligation_inventory_max=inventory_bound,
    )


def _stage_binding_artifact(
    binding: ObservationStageSourceBinding,
) -> dict[str, Any]:
    return {
        "schema_version": binding.schema_version,
        "stage": binding.stage,
        "original_input_bundle_sha256": binding.original_input_bundle_sha256,
        "question_need_decision_sha256": binding.question_need_decision_sha256,
        "supplemental_answer_bundle_sha256": (
            binding.supplemental_answer_bundle_sha256
        ),
        "allowed_source_roles": list(binding.allowed_source_roles),
        "body_free": binding.body_free,
    }


def build_grounded_source_snapshot(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    observation_stage_context: Mapping[str, Any],
    original_input_bundle: Any,
    trusted_future_authority: TrustedFutureStageAuthority | None = None,
    supplemental_answer_bundle: Any | None = None,
    _register_origin: bool = True,
) -> GroundedSourceSnapshot:
    """Adapt source owners; no caller may declare roles, unknowns, or eligibility."""

    plan_issues = validate_grounded_observation_plan(plan, resolver)
    if plan_issues:
        raise SemanticObligationInventoryError(
            "SOURCE_OBSERVATION_PLAN_INVALID", ",".join(plan_issues)
        )
    try:
        semantic_restatement_witness = (
            build_grounded_semantic_restatement_witness(plan, resolver)
        )
    except GroundedSemanticRestatementError as exc:
        raise SemanticObligationInventoryError(
            "SEMANTIC_RESTATEMENT_WITNESS_INVALID", str(exc)
        ) from exc
    semantic_restatement_issues = validate_grounded_semantic_restatement_witness(
        semantic_restatement_witness,
        plan=plan,
        resolver=resolver,
    )
    if semantic_restatement_issues:
        raise SemanticObligationInventoryError(
            "SEMANTIC_RESTATEMENT_WITNESS_INVALID",
            ",".join(semantic_restatement_issues),
        )
    semantic_witness_by_relation_id = {
        row.relation_id: row for row in semantic_restatement_witness.relations
    }
    plan_relation_ids = {row.relation_id for row in plan.relations}
    if (
        len(semantic_witness_by_relation_id)
        != len(semantic_restatement_witness.relations)
        or set(semantic_witness_by_relation_id) != plan_relation_ids
    ):
        raise SemanticObligationInventoryError(
            "SEMANTIC_RESTATEMENT_WITNESS_RELATION_SET_MISMATCH"
        )
    if not isinstance(original_input_bundle, Mapping):
        raise SemanticObligationInventoryError("SOURCE_INPUT_BUNDLE_INVALID")
    evidence_report = validate_evidence_ledger(
        tuple(resolver.resolve(item) for item in resolver.span_ids),
        current_input=original_input_bundle,
    )
    if not evidence_report.valid:
        code = (
            "SOURCE_INPUT_BUNDLE_MISMATCH"
            if {
                "source_slice_mismatch",
                "invalid_source_offset",
            }
            & set(evidence_report.issue_codes)
            else "SOURCE_EVIDENCE_LEDGER_INVALID"
        )
        raise SemanticObligationInventoryError(
            code, ",".join(evidence_report.issue_codes)
        )
    # ``validate_evidence_ledger`` verifies text offsets.  Rebuilding the
    # canonical current-input ledger additionally binds list-backed emotion
    # and category evidence, whose offset contract is intentionally (-1,-1).
    if tuple(resolver.resolve(item) for item in resolver.span_ids) != tuple(
        build_evidence_ledger(original_input_bundle)
    ):
        raise SemanticObligationInventoryError("SOURCE_INPUT_BUNDLE_MISMATCH")
    stage_issues = validate_observation_stage_context(
        observation_stage_context,
        original_input_bundle=original_input_bundle,
        trusted_future_authority=trusted_future_authority,
        supplemental_answer_bundle=supplemental_answer_bundle,
    )
    if stage_issues:
        raise SemanticObligationInventoryError(
            stage_issues[0].code, stage_issues[0].path
        )
    stage = observation_stage_context["stage"]
    if stage == "refined_observation":
        # The current GroundedObservationPlan has no independently owned
        # original/supplemental partition.  Relabelling one source here would
        # violate the Step 4 STOP boundary.
        raise SemanticObligationInventoryError(
            "REFINED_SOURCE_PARTITION_OWNER_UNAVAILABLE"
        )
    if stage not in {"normal_observation", "pre_question_observation"}:
        raise SemanticObligationInventoryError("OBSERVATION_STAGE_INVALID")

    units_by_parent: dict[str, tuple[GroundedSemanticUnitWitness, ...]] = {}
    for unit in semantic_restatement_witness.semantic_units:
        units_by_parent.setdefault(unit.parent_nucleus_id, tuple())
        units_by_parent[unit.parent_nucleus_id] = (
            *units_by_parent[unit.parent_nucleus_id],
            unit,
        )
    if any(
        len(rows) < 2 or len(rows) > 4
        for rows in units_by_parent.values()
    ) or len(semantic_restatement_witness.semantic_units) > 4 * len(plan.nuclei):
        raise SemanticObligationInventoryError("SEMANTIC_UNIT_BOUND_EXCEEDED")
    parent_by_id = {row.nucleus_id: row for row in plan.nuclei}
    if not set(units_by_parent) <= set(parent_by_id):
        raise SemanticObligationInventoryError("SEMANTIC_UNIT_PARENT_UNRESOLVED")
    actual_nucleus_expansion = {
        row.nucleus_id: tuple(
            unit.unit_id for unit in units_by_parent.get(row.nucleus_id, ())
        ) or (row.nucleus_id,)
        for row in plan.nuclei
    }
    adapted_nucleus_ids = tuple(
        source_id
        for row in plan.nuclei
        for source_id in actual_nucleus_expansion[row.nucleus_id]
    )
    adapted_relation_ids = (
        *(row.relation_id for row in plan.relations),
        *(row.link_id for row in semantic_restatement_witness.semantic_links),
    )
    adapted_unknown_ids = (
        *(row.unknown_id for row in plan.unknown_boundaries),
        *(row.unknown_id for row in semantic_restatement_witness.explicit_unknowns),
    )
    bindings = _alias_bindings(
        plan,
        resolver,
        nucleus_ids=adapted_nucleus_ids,
        relation_ids=adapted_relation_ids,
        unknown_ids=adapted_unknown_ids,
    )
    alias_by_source = _alias_index(bindings)
    required_nucleus_ids = frozenset(plan.coverage_requirements.required_nucleus_ids)
    required_relation_ids = frozenset(plan.coverage_requirements.required_relation_ids)
    fact_boundary_ids = frozenset(plan.response_plan.fact_boundary_nucleus_ids)
    nucleus_rows: list[InventoryNucleusSource] = []
    for row in sorted(plan.nuclei, key=lambda item: item.nucleus_id):
        derived = units_by_parent.get(row.nucleus_id, ())
        if derived:
            nucleus_rows.extend(
                _semantic_unit_source(
                    unit,
                    parent=row,
                    alias_by_source=alias_by_source,
                    fact_boundary_ids=fact_boundary_ids,
                )
                for unit in sorted(derived, key=lambda item: item.unit_id)
            )
        else:
            nucleus_rows.append(
                _nucleus_source(
                    row,
                    alias_by_source=alias_by_source,
                    required_ids=required_nucleus_ids,
                    fact_boundary_ids=fact_boundary_ids,
                )
            )
    nuclei = tuple(sorted(nucleus_rows, key=lambda item: item.actual_source_id))
    nucleus_by_actual_id = {row.actual_source_id: row for row in nuclei}
    relation_rows = [
        _relation_source(
            row,
            semantic_witness=semantic_witness_by_relation_id[row.relation_id],
            alias_by_source=alias_by_source,
            nucleus_by_actual_id=nucleus_by_actual_id,
            required_ids=required_relation_ids,
        )
        for row in sorted(plan.relations, key=lambda item: item.relation_id)
    ]
    relation_rows.extend(
        _semantic_link_source(
            row,
            alias_by_source=alias_by_source,
            nucleus_by_actual_id=nucleus_by_actual_id,
        )
        for row in semantic_restatement_witness.semantic_links
    )
    relations = tuple(sorted(relation_rows, key=lambda item: item.actual_source_id))
    pre_question = stage == "pre_question_observation"
    unknown_rows = [
        _unknown_source(
            row,
            alias_by_source=alias_by_source,
            nucleus_by_actual_id=nucleus_by_actual_id,
            actual_nucleus_expansion=actual_nucleus_expansion,
            required=pre_question,
        )
        for row in sorted(plan.unknown_boundaries, key=lambda item: item.unknown_id)
    ]
    unknown_rows.extend(
        _explicit_unknown_source(
            row,
            alias_by_source=alias_by_source,
            nucleus_by_actual_id=nucleus_by_actual_id,
        )
        for row in semantic_restatement_witness.explicit_unknowns
    )
    unknowns = tuple(sorted(unknown_rows, key=lambda item: item.actual_source_id))
    reception_plan = plan.response_plan.human_reception_plan
    opportunities = tuple(
        _reception_source(
            row,
            alias_by_source=alias_by_source,
            nucleus_by_actual_id=nucleus_by_actual_id,
            actual_nucleus_expansion=actual_nucleus_expansion,
        )
        for row in sorted(
            reception_plan.opportunities if reception_plan is not None else (),
            key=lambda item: item.opportunity_id,
        )
    )
    eligibility = _eligibility_authority(plan)
    if eligibility.response_eligibility == "separate_safety_owner":
        raise SemanticObligationInventoryError("SEPARATE_SAFETY_OWNER")
    counts = _resource_counts(plan, resolver)
    inventory_bound = obligation_inventory_upper_bound(counts)
    evidence_ids = tuple(
        alias_by_source[("evidence", item)] for item in resolver.span_ids
    )
    text_evidence_ids = tuple(
        alias_by_source[("evidence", item)]
        for item in resolver.span_ids
        if resolver.resolve(item).source_field in {"memo", "memo_action"}
    )
    all_aliases = tuple(sorted(item.alias_source_id for item in bindings))
    role_bindings = tuple((item, "original_input") for item in all_aliases)
    safety_codes = _ordered_unique(plan.safety_policy.required_boundary_codes)
    plan_artifact = _plan_native_artifact(
        plan_schema_version=plan.schema_version,
        plan_adapter_version=plan.adapter_version,
        plan_generation_path=plan.generation_path,
        semantic_restatement_witness_schema_version=(
            semantic_restatement_witness.schema_version
        ),
        semantic_restatement_witness_adapter_version=(
            semantic_restatement_witness.adapter_version
        ),
        semantic_restatement_plan_binding_sha256=(
            semantic_restatement_witness.plan_binding_sha256
        ),
        source_semantic_restatement_witness_sha256=(
            semantic_restatement_witness.witness_sha256
        ),
        bindings=bindings,
        evidence_ids=evidence_ids,
        nuclei=nuclei,
        relations=relations,
        unknowns=unknowns,
        safety_required_boundary_codes=safety_codes,
        identity_claim_must_not_be_accepted_as_fact=(
            plan.safety_policy.identity_claim_must_not_be_accepted_as_fact
        ),
        eligibility=eligibility,
    )
    reception_artifact = _reception_native_artifact(opportunities, bindings)
    stage_binding = ObservationStageSourceBinding(
        schema_version=observation_stage_context["schema_version"],
        stage=observation_stage_context["stage"],
        original_input_bundle_sha256=(
            observation_stage_context["original_input_bundle_sha256"]
        ),
        question_need_decision_sha256=(
            observation_stage_context["question_need_decision_sha256"]
        ),
        supplemental_answer_bundle_sha256=(
            observation_stage_context["supplemental_answer_bundle_sha256"]
        ),
        allowed_source_roles=tuple(observation_stage_context["allowed_source_roles"]),
        body_free=observation_stage_context["body_free"],
    )
    plan_hash = artifact_sha256(plan_artifact)
    stage_hash = artifact_sha256(_stage_binding_artifact(stage_binding))
    reception_hash = (
        artifact_sha256(reception_artifact) if reception_artifact is not None else None
    )
    authority = _ledger_authority(
        plan_hash=plan_hash,
        stage_hash=stage_hash,
        reception_hash=reception_hash,
        eligibility=eligibility,
        evidence_ids=evidence_ids,
        nuclei=nuclei,
        relations=relations,
        unknowns=unknowns,
        opportunities=opportunities,
        role_bindings=role_bindings,
        inventory_bound=inventory_bound,
    )
    preserved = frozenset(row.source_id for row in unknowns) if pre_question else frozenset()
    snapshot = GroundedSourceSnapshot(
        plan_schema_version=plan.schema_version,
        plan_adapter_version=plan.adapter_version,
        plan_generation_path=plan.generation_path,
        observation_stage=stage,
        observation_stage_source_binding=stage_binding,
        semantic_source_roles=("original_input",),
        semantic_restatement_witness_schema_version=(
            semantic_restatement_witness.schema_version
        ),
        semantic_restatement_witness_adapter_version=(
            semantic_restatement_witness.adapter_version
        ),
        semantic_restatement_plan_binding_sha256=(
            semantic_restatement_witness.plan_binding_sha256
        ),
        source_semantic_restatement_witness_sha256=(
            semantic_restatement_witness.witness_sha256
        ),
        source_observation_plan_sha256=plan_hash,
        source_observation_stage_context_sha256=stage_hash,
        source_reception_opportunity_plan_sha256=reception_hash,
        response_eligibility_source_sha256=eligibility.source_commitment_sha256,
        response_eligibility=eligibility.response_eligibility,
        response_eligibility_authority=eligibility,
        source_policy_sha256=FROZEN_SOURCE_POLICY_SHA256,
        source_id_alias_bindings=bindings,
        grounded_parent_nucleus_count=len(plan.nuclei),
        grounded_parent_relation_count=len(plan.relations),
        grounded_parent_unknown_boundary_count=len(plan.unknown_boundaries),
        evidence_ids=evidence_ids,
        text_evidence_ids=text_evidence_ids,
        nuclei=nuclei,
        relations=relations,
        unknowns=unknowns,
        reception_opportunities=opportunities,
        safety_required_boundary_codes=safety_codes,
        identity_claim_must_not_be_accepted_as_fact=(
            plan.safety_policy.identity_claim_must_not_be_accepted_as_fact
        ),
        preserved_unknown_boundary_ids=preserved,
        answered_unknown_boundary_ids=frozenset(),
        source_role_bindings=role_bindings,
        resource_counts=tuple(sorted(counts.items())),
        obligation_inventory_upper_bound=inventory_bound,
        ledger_source_authority=authority,
    )
    if _register_origin:
        _register_source_origin(
            snapshot,
            _GroundedSourceOrigin.from_sources(
                plan=plan,
                resolver=resolver,
                observation_stage_context=observation_stage_context,
                original_input_bundle=original_input_bundle,
                trusted_future_authority=trusted_future_authority,
                supplemental_answer_bundle=supplemental_answer_bundle,
            ),
        )
    return snapshot


def _source_refs(
    *,
    role_by_id: Mapping[str, str],
    evidence_ids: Sequence[str] = (),
    nucleus_ids: Sequence[str] = (),
    relation_ids: Sequence[str] = (),
    unknown_ids: Sequence[str] = (),
    opportunity_ids: Sequence[str] = (),
) -> list[dict[str, Any]]:
    fields = {
        "evidence_ids": _ordered_unique(evidence_ids),
        "nucleus_ids": _ordered_unique(nucleus_ids),
        "relation_ids": _ordered_unique(relation_ids),
        "unknown_boundary_ids": _ordered_unique(unknown_ids),
        "reception_opportunity_ids": _ordered_unique(opportunity_ids),
    }
    roles = sorted(
        {role_by_id[item] for values in fields.values() for item in values}
    )
    return [
        {
            "source_role": role,
            **{
                field: [item for item in values if role_by_id[item] == role]
                for field, values in fields.items()
            },
        }
        for role in roles
    ]


def _obligation_row(
    *,
    kind: str,
    required: bool,
    evidence_ids: Sequence[str],
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    unknown_ids: Sequence[str],
    opportunity_ids: Sequence[str],
    polarity: str,
    modality: str,
    temporal_scope: str,
    topic_scope_ids: Sequence[str],
    referent_scope: str,
    allowed_response_acts: Sequence[str],
    forbidden_claim_codes: Sequence[str],
    source_authority_codes: Sequence[str],
    role_by_id: Mapping[str, str],
    relation_directions: Sequence[Mapping[str, str]] = (),
    target_obligation_ids: Sequence[str] = (),
) -> dict[str, Any]:
    primary = (
        tuple(relation_ids)
        or tuple(unknown_ids)
        or tuple(nucleus_ids)
        or tuple(evidence_ids)
    )
    distinctness_group = "dg_" + artifact_sha256(
        {
            "kind": kind,
            "primary_source_ids": list(primary),
            "source_roles": sorted({role_by_id[item] for item in primary}),
        }
    )[:16]
    row: dict[str, Any] = {
        "obligation_id": "obl_0000000000000000",
        "kind": kind,
        "required": required,
        "evidence_ids": list(_ordered_unique(evidence_ids)),
        "nucleus_ids": list(_ordered_unique(nucleus_ids)),
        "relation_ids": list(_ordered_unique(relation_ids)),
        "unknown_boundary_ids": list(_ordered_unique(unknown_ids)),
        "target_obligation_ids": list(_ordered_unique(target_obligation_ids)),
        "polarity": polarity,
        "modality": modality,
        "temporal_scope": temporal_scope,
        "topic_scope_ids": list(_ordered_unique(topic_scope_ids)),
        "referent_scope": referent_scope,
        "distinctness_group": distinctness_group,
        "must_not_merge_with": [],
        "allowed_response_acts": list(_ordered_unique(allowed_response_acts)),
        "forbidden_claim_codes": list(_ordered_unique(forbidden_claim_codes)),
        "source_authority_codes": list(_ordered_unique(source_authority_codes)),
        "reception_opportunity_ids": list(_ordered_unique(opportunity_ids)),
        "source_refs": _source_refs(
            role_by_id=role_by_id,
            evidence_ids=evidence_ids,
            nucleus_ids=nucleus_ids,
            relation_ids=relation_ids,
            unknown_ids=unknown_ids,
            opportunity_ids=opportunity_ids,
        ),
        "relation_directions": [dict(item) for item in relation_directions],
    }
    row["obligation_id"] = derive_obligation_id(row)
    return row


def _specialized_kinds(source: InventoryNucleusSource) -> tuple[str, ...]:
    kinds: list[str] = []
    if source.kind in {"change", "value"}:
        kinds.append("significance_or_shift")
    if source.kind in {"action", "wish"} or source.modality == "intended":
        kinds.append("intention_or_next_action")
    if source.kind == "self_evaluation" and source.fact_boundary:
        kinds.append("self_denial_boundary")
    return tuple(kinds)


def _kind_act(kind: str) -> str:
    return {
        "grounded_nucleus_notice": "notice",
        "significance_or_shift": "mark_shift",
        "intention_or_next_action": "honor_action",
        "self_denial_boundary": "separate_self_denial",
        "bounded_counterposition": "bounded_counterposition",
    }[kind]


def _sort_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            _SPECIAL_KIND_ORDER[row["kind"]],
            tuple(row["reception_opportunity_ids"]),
            tuple(row["relation_ids"]),
            tuple(row["unknown_boundary_ids"]),
            tuple(row["nucleus_ids"]),
            row["obligation_id"],
        ),
    )


def _target_rank(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        0 if row["required"] is True else 1,
        0 if row["kind"] == "grounded_relation_preservation" else 1,
        0
        if row["kind"]
        in {
            "self_denial_boundary",
            "intention_or_next_action",
            "significance_or_shift",
        }
        else 1,
        _SPECIAL_KIND_ORDER[row["kind"]],
        row["obligation_id"],
    )


def _discover_obligation_rows(
    source_snapshot: GroundedSourceSnapshot,
) -> list[dict[str, Any]]:
    role_by_id = dict(source_snapshot.source_role_bindings)
    rows: list[dict[str, Any]] = []
    for source in source_snapshot.nuclei:
        specialized = _specialized_kinds(source)
        rows.append(
            _obligation_row(
                kind="grounded_nucleus_notice",
                required=source.required and not specialized,
                evidence_ids=source.evidence_ids,
                nucleus_ids=(source.source_id,),
                relation_ids=(),
                unknown_ids=(),
                opportunity_ids=(),
                polarity=source.polarity,
                modality=source.modality,
                temporal_scope=source.temporal_scope,
                topic_scope_ids=source.topic_scope_ids,
                referent_scope=source.referent_scope,
                allowed_response_acts=("notice",),
                forbidden_claim_codes=source.forbidden_claim_codes,
                source_authority_codes=("nucleus",),
                role_by_id=role_by_id,
            )
        )
        for kind in specialized:
            forbidden = list(source.forbidden_claim_codes)
            if kind == "intention_or_next_action":
                forbidden.append("NO_FUTURE_GUARANTEE")
            if kind == "self_denial_boundary":
                forbidden.append("IDENTITY_CLAIM_NOT_FACT")
            rows.append(
                _obligation_row(
                    kind=kind,
                    required=source.required,
                    evidence_ids=source.evidence_ids,
                    nucleus_ids=(source.source_id,),
                    relation_ids=(),
                    unknown_ids=(),
                    opportunity_ids=(),
                    polarity=source.polarity,
                    modality=(
                        "reported" if kind == "self_denial_boundary" else source.modality
                    ),
                    temporal_scope=source.temporal_scope,
                    topic_scope_ids=source.topic_scope_ids,
                    referent_scope=source.referent_scope,
                    allowed_response_acts=(_kind_act(kind),),
                    forbidden_claim_codes=forbidden,
                    source_authority_codes=("nucleus", "safety_policy")
                    if kind == "self_denial_boundary"
                    else ("nucleus",),
                    role_by_id=role_by_id,
                )
            )

    for source in source_snapshot.relations:
        rows.append(
            _obligation_row(
                kind="grounded_relation_preservation",
                required=source.required,
                evidence_ids=source.evidence_ids,
                nucleus_ids=(
                    source.semantic_restatement_unit_nucleus_ids
                    or (source.from_nucleus_id, source.to_nucleus_id)
                ),
                relation_ids=(source.source_id,),
                unknown_ids=(),
                opportunity_ids=(),
                polarity=source.polarity,
                modality=source.modality,
                temporal_scope=source.temporal_scope,
                topic_scope_ids=source.topic_scope_ids,
                referent_scope="relation",
                allowed_response_acts=("preserve_relation",),
                forbidden_claim_codes=source.forbidden_claim_codes,
                source_authority_codes=("nucleus", "relation"),
                role_by_id=role_by_id,
                relation_directions=(
                    {
                        "relation_id": source.source_id,
                        "relation_type": source.relation_type,
                        "direction": source.relation_direction,
                    },
                ),
            )
        )

    for source in source_snapshot.unknowns:
        rows.append(
            _obligation_row(
                kind="unknown_boundary_preservation",
                required=source.required,
                evidence_ids=source.evidence_ids,
                nucleus_ids=source.affected_nucleus_ids,
                relation_ids=(),
                unknown_ids=(source.source_id,),
                opportunity_ids=(),
                polarity="unknown",
                modality="unknown",
                temporal_scope="unknown",
                topic_scope_ids=source.topic_scope_ids,
                referent_scope="unknown",
                allowed_response_acts=("preserve_unknown",),
                forbidden_claim_codes=(source.dimension_code, "NO_UNKNOWN_COMPLETION"),
                source_authority_codes=("nucleus", "unknown_boundary")
                if source.affected_nucleus_ids
                else ("unknown_boundary",),
                role_by_id=role_by_id,
            )
        )

    self_denial_rows = [row for row in rows if row["kind"] == "self_denial_boundary"]
    if source_snapshot.identity_claim_must_not_be_accepted_as_fact:
        boundary_codes = source_snapshot.safety_required_boundary_codes or (
            "IDENTITY_CLAIM_NOT_FACT",
        )
        counter_rows: list[dict[str, Any]] = []
        for source_row in self_denial_rows:
            counter = _obligation_row(
                kind="bounded_counterposition",
                required=source_row["required"],
                evidence_ids=source_row["evidence_ids"],
                nucleus_ids=source_row["nucleus_ids"],
                relation_ids=(),
                unknown_ids=(),
                opportunity_ids=(),
                polarity=source_row["polarity"],
                modality="reported",
                temporal_scope=source_row["temporal_scope"],
                topic_scope_ids=source_row["topic_scope_ids"],
                referent_scope=source_row["referent_scope"],
                allowed_response_acts=("bounded_counterposition",),
                forbidden_claim_codes=tuple(
                    _machine_code(code, fallback="IDENTITY_CLAIM_NOT_FACT")
                    for code in boundary_codes
                ),
                source_authority_codes=("nucleus", "safety_policy"),
                role_by_id=role_by_id,
            )
            source_row["must_not_merge_with"] = [counter["obligation_id"]]
            counter["must_not_merge_with"] = [source_row["obligation_id"]]
            counter_rows.append(counter)
        rows.extend(counter_rows)

    if source_snapshot.response_eligibility in _VISIBLE_ELIGIBILITIES:
        bindable = [
            row
            for row in rows
            if row["evidence_ids"] and row["kind"] != "bounded_counterposition"
        ]
        if not bindable:
            raise SemanticObligationInventoryError("OBLIGATION_SOURCE_UNAVAILABLE")
        opportunities = source_snapshot.reception_opportunities
        if not opportunities:
            target = sorted(bindable, key=_target_rank)[0]
            default_act = (
                "receive_without_deciding"
                if target["kind"] == "unknown_boundary_preservation"
                else "hold_in_attention"
            )
            rows.append(
                _obligation_row(
                    kind="bound_emlis_reception",
                    required=True,
                    evidence_ids=target["evidence_ids"],
                    nucleus_ids=target["nucleus_ids"],
                    relation_ids=target["relation_ids"],
                    unknown_ids=target["unknown_boundary_ids"],
                    opportunity_ids=(),
                    polarity=target["polarity"],
                    modality=target["modality"],
                    temporal_scope=target["temporal_scope"],
                    topic_scope_ids=target["topic_scope_ids"],
                    referent_scope=target["referent_scope"],
                    allowed_response_acts=(default_act,),
                    forbidden_claim_codes=("NO_GENERIC_RECEPTION",),
                    source_authority_codes=target["source_authority_codes"],
                    role_by_id=role_by_id,
                    relation_directions=target["relation_directions"],
                    target_obligation_ids=(target["obligation_id"],),
                )
            )
        else:
            stance_specs: list[tuple[InventoryReceptionSource, dict[str, Any]]] = []
            for opportunity in opportunities:
                matching = [
                    row
                    for row in bindable
                    if set(row["nucleus_ids"]) & set(opportunity.target_nucleus_ids)
                ]
                if not matching:
                    raise SemanticObligationInventoryError(
                        "RECEPTION_TARGET_UNRESOLVED", opportunity.actual_source_id
                    )
                stance_specs.append(
                    (opportunity, sorted(matching, key=_target_rank)[0])
                )
            safety_present = any(item.safety_required for item, _ in stance_specs)
            best_opportunity_id = None
            if not safety_present:
                best_opportunity_id = sorted(
                    stance_specs,
                    key=lambda pair: (
                        *_target_rank(pair[1]),
                        _RETENTION_RANK[pair[0].retention],
                        -pair[0].priority,
                        pair[0].family,
                        pair[0].source_id,
                    ),
                )[0][0].source_id
            for opportunity, target in stance_specs:
                required = (
                    opportunity.safety_required
                    if safety_present
                    else opportunity.source_id == best_opportunity_id
                )
                rows.append(
                    _obligation_row(
                        kind="bound_emlis_reception",
                        required=required,
                        evidence_ids=_ordered_unique(
                            (*target["evidence_ids"], *opportunity.evidence_ids)
                        ),
                        nucleus_ids=target["nucleus_ids"],
                        relation_ids=target["relation_ids"],
                        unknown_ids=target["unknown_boundary_ids"],
                        opportunity_ids=(opportunity.source_id,),
                        polarity=target["polarity"],
                        modality=target["modality"],
                        temporal_scope=target["temporal_scope"],
                        topic_scope_ids=target["topic_scope_ids"],
                        referent_scope=target["referent_scope"],
                        allowed_response_acts=(opportunity.reception_act,),
                        forbidden_claim_codes=("NO_GENERIC_RECEPTION",),
                        source_authority_codes=tuple(
                            dict.fromkeys(
                                [
                                    *target["source_authority_codes"],
                                    "reception_opportunity",
                                ]
                            )
                        ),
                        role_by_id=role_by_id,
                        relation_directions=target["relation_directions"],
                        target_obligation_ids=(target["obligation_id"],),
                    )
                )
    return _sort_rows(rows)


def _source_origin_authority_issues(
    snapshot: GroundedSourceSnapshot,
) -> tuple[str, ...]:
    return _validate_source_origin_capability(snapshot)


def _snapshot_authority_issues(snapshot: GroundedSourceSnapshot) -> tuple[str, ...]:
    if type(snapshot) is not GroundedSourceSnapshot:
        return ("SOURCE_SNAPSHOT_TYPE_INVALID",)
    issues: list[str] = list(_source_origin_authority_issues(snapshot))
    bindings = snapshot.source_id_alias_bindings
    if type(bindings) is not tuple:
        return ("SOURCE_ID_ALIAS_BINDING_INVALID",)
    aliases: list[str] = []
    binding_keys: list[tuple[str, str]] = []
    for item in bindings:
        if type(item) is not SourceIdAliasBinding:
            issues.append("SOURCE_ID_ALIAS_BINDING_INVALID")
            continue
        binding_keys.append((item.source_kind, item.actual_source_id))
        aliases.append(item.alias_source_id)
        if (
            item.source_kind not in _ALIAS_PREFIX
            or item.source_owner != _SOURCE_OWNER.get(item.source_kind)
            or not _BODY_FREE_SOURCE_ID_RE.fullmatch(item.actual_source_id)
            or not _MACHINE_SOURCE_ID_RE.fullmatch(item.alias_source_id)
            or item.alias_source_id
            != _alias_for(item.source_kind, item.actual_source_id)
        ):
            issues.append("SOURCE_ID_ALIAS_BINDING_INVALID")
    if len(binding_keys) != len(set(binding_keys)) or len(aliases) != len(set(aliases)):
        issues.append("SOURCE_ID_ALIAS_BIJECTION_INVALID")
    expected_alias_sets = {
        "evidence": set(snapshot.evidence_ids),
        "nucleus": {row.source_id for row in snapshot.nuclei},
        "relation": {row.source_id for row in snapshot.relations},
        "unknown_boundary": {row.source_id for row in snapshot.unknowns},
        "reception_opportunity": {
            row.source_id for row in snapshot.reception_opportunities
        },
    }
    actual_alias_sets = {
        kind: {item.alias_source_id for item in bindings if item.source_kind == kind}
        for kind in _ALIAS_PREFIX
    }
    if expected_alias_sets != actual_alias_sets:
        issues.append("SOURCE_ID_ALIAS_COVERAGE_MISMATCH")
    if not set(snapshot.text_evidence_ids) <= set(snapshot.evidence_ids):
        issues.append("SOURCE_RESOURCE_COUNTS_INVALID")
    expected_roles = tuple((item, "original_input") for item in sorted(aliases))
    stage_binding = snapshot.observation_stage_source_binding
    expected_stage_roles = (
        ("original_input",)
        if snapshot.observation_stage == "normal_observation"
        else ("original_input", "question_need_decision")
    )
    stage_hash_fields_valid = bool(
        type(stage_binding) is ObservationStageSourceBinding
        and _SHA256_RE.fullmatch(stage_binding.original_input_bundle_sha256)
        and (
            stage_binding.question_need_decision_sha256 is None
            if snapshot.observation_stage == "normal_observation"
            else type(stage_binding.question_need_decision_sha256) is str
            and bool(_SHA256_RE.fullmatch(stage_binding.question_need_decision_sha256))
        )
        and stage_binding.supplemental_answer_bundle_sha256 is None
    )
    if (
        type(stage_binding) is not ObservationStageSourceBinding
        or stage_binding.schema_version != STAGE_SCHEMA
        or stage_binding.stage != snapshot.observation_stage
        or stage_binding.body_free is not True
        or stage_binding.allowed_source_roles != expected_stage_roles
        or not stage_hash_fields_valid
        or artifact_sha256(_stage_binding_artifact(stage_binding))
        != snapshot.source_observation_stage_context_sha256
    ):
        issues.append("OBSERVATION_STAGE_CONTEXT_COMMITMENT_MISMATCH")
    if (
        snapshot.semantic_source_roles != ("original_input",)
        or snapshot.source_role_bindings != expected_roles
        or snapshot.observation_stage not in {
            "normal_observation",
            "pre_question_observation",
        }
        or snapshot.answered_unknown_boundary_ids
    ):
        issues.append("SOURCE_ROLE_BINDING_MISMATCH")
    if (
        snapshot.semantic_restatement_witness_schema_version
        != GROUND_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA
        or snapshot.semantic_restatement_witness_adapter_version
        != GROUND_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
        or type(snapshot.semantic_restatement_plan_binding_sha256) is not str
        or not _SHA256_RE.fullmatch(
            snapshot.semantic_restatement_plan_binding_sha256
        )
        or type(snapshot.source_semantic_restatement_witness_sha256) is not str
        or not _SHA256_RE.fullmatch(
            snapshot.source_semantic_restatement_witness_sha256
        )
    ):
        issues.append("SEMANTIC_RESTATEMENT_WITNESS_COMMITMENT_INVALID")
    all_unknown_ids = frozenset(row.source_id for row in snapshot.unknowns)
    expected_preserved = (
        all_unknown_ids
        if snapshot.observation_stage == "pre_question_observation"
        else frozenset()
    )
    if snapshot.preserved_unknown_boundary_ids != expected_preserved:
        issues.append("PRESERVED_UNKNOWN_AUTHORITY_MISMATCH")
    try:
        eligibility = _eligibility_authority_from_snapshot(snapshot)
    except SemanticObligationInventoryError:
        eligibility = snapshot.response_eligibility_authority
        issues.append("RESPONSE_ELIGIBILITY_SOURCE_MISMATCH")
    if (
        eligibility != snapshot.response_eligibility_authority
        or snapshot.response_eligibility != eligibility.response_eligibility
        or snapshot.response_eligibility_source_sha256
        != eligibility.source_commitment_sha256
    ):
        issues.append("RESPONSE_ELIGIBILITY_SOURCE_MISMATCH")
    counts = {
        "evidence_span_count": len(snapshot.evidence_ids),
        "text_evidence_span_count": len(snapshot.text_evidence_ids),
        "nucleus_count": snapshot.grounded_parent_nucleus_count,
        "relation_count": snapshot.grounded_parent_relation_count,
        "unknown_boundary_count": snapshot.grounded_parent_unknown_boundary_count,
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": len(
            set(snapshot.safety_required_boundary_codes)
        ),
        "reception_opportunity_count": len(snapshot.reception_opportunities),
    }
    parent_counts_valid = all(
        type(value) is int and value >= 0
        for value in (
            snapshot.grounded_parent_nucleus_count,
            snapshot.grounded_parent_relation_count,
            snapshot.grounded_parent_unknown_boundary_count,
        )
    )
    if (
        not parent_counts_valid
        or len(snapshot.nuclei)
        > 4 * snapshot.grounded_parent_nucleus_count
        or len(snapshot.relations)
        > snapshot.grounded_parent_relation_count
        + snapshot.grounded_parent_nucleus_count
        or len(snapshot.unknowns)
        > snapshot.grounded_parent_unknown_boundary_count
        + 2 * len(snapshot.text_evidence_ids)
        + snapshot.grounded_parent_nucleus_count
    ):
        issues.append("SEMANTIC_ADAPTER_RESOURCE_BOUND_INVALID")
    try:
        bound = obligation_inventory_upper_bound(counts)
    except SemanticObligationInventoryError:
        bound = -1
        issues.append("SOURCE_RESOURCE_COUNTS_INVALID")
    if (
        snapshot.resource_counts != tuple(sorted(counts.items()))
        or snapshot.obligation_inventory_upper_bound != bound
    ):
        issues.append("SOURCE_RESOURCE_COUNTS_INVALID")
    try:
        plan_artifact = _plan_native_artifact(
            plan_schema_version=snapshot.plan_schema_version,
            plan_adapter_version=snapshot.plan_adapter_version,
            plan_generation_path=snapshot.plan_generation_path,
            semantic_restatement_witness_schema_version=(
                snapshot.semantic_restatement_witness_schema_version
            ),
            semantic_restatement_witness_adapter_version=(
                snapshot.semantic_restatement_witness_adapter_version
            ),
            semantic_restatement_plan_binding_sha256=(
                snapshot.semantic_restatement_plan_binding_sha256
            ),
            source_semantic_restatement_witness_sha256=(
                snapshot.source_semantic_restatement_witness_sha256
            ),
            bindings=bindings,
            evidence_ids=snapshot.evidence_ids,
            nuclei=snapshot.nuclei,
            relations=snapshot.relations,
            unknowns=snapshot.unknowns,
            safety_required_boundary_codes=snapshot.safety_required_boundary_codes,
            identity_claim_must_not_be_accepted_as_fact=(
                snapshot.identity_claim_must_not_be_accepted_as_fact
            ),
            eligibility=eligibility,
        )
        plan_hash = artifact_sha256(plan_artifact)
        reception_artifact = _reception_native_artifact(
            snapshot.reception_opportunities, bindings
        )
        reception_hash = (
            artifact_sha256(reception_artifact)
            if reception_artifact is not None
            else None
        )
    except (KeyError, SemanticObligationInventoryError):
        plan_hash = ""
        reception_hash = None
        issues.append("SOURCE_ID_ALIAS_BINDING_INVALID")
    if snapshot.source_observation_plan_sha256 != plan_hash:
        issues.append("SOURCE_OBSERVATION_PLAN_COMMITMENT_MISMATCH")
    if snapshot.source_reception_opportunity_plan_sha256 != reception_hash:
        issues.append("RECEPTION_PLAN_LINEAGE_MISMATCH")
    if (
        artifact_sha256(SOURCE_POLICY_ARTIFACT) != FROZEN_SOURCE_POLICY_SHA256
        or SOURCE_POLICY_SHA256 != FROZEN_SOURCE_POLICY_SHA256
        or snapshot.source_policy_sha256 != FROZEN_SOURCE_POLICY_SHA256
    ):
        issues.append("SOURCE_POLICY_MISMATCH")
    expected_authority = _ledger_authority(
        plan_hash=plan_hash,
        stage_hash=snapshot.source_observation_stage_context_sha256,
        reception_hash=reception_hash,
        eligibility=eligibility,
        evidence_ids=snapshot.evidence_ids,
        nuclei=snapshot.nuclei,
        relations=snapshot.relations,
        unknowns=snapshot.unknowns,
        opportunities=snapshot.reception_opportunities,
        role_bindings=snapshot.source_role_bindings,
        inventory_bound=bound,
    )
    if snapshot.ledger_source_authority != expected_authority:
        issues.append("SNAPSHOT_AUTHORITY_COMMITMENT_MISMATCH")
    return tuple(sorted(set(issues)))


def build_semantic_obligation_inventory(
    source_snapshot: GroundedSourceSnapshot,
) -> SemanticObligationInventoryResult:
    """Discover a deterministic, lossless, body-free Step 4 ledger."""

    snapshot_issues = _snapshot_authority_issues(source_snapshot)
    if snapshot_issues:
        raise SemanticObligationInventoryError(snapshot_issues[0])
    if source_snapshot.response_eligibility == "separate_safety_owner":
        raise SemanticObligationInventoryError("SEPARATE_SAFETY_OWNER")
    rows = _discover_obligation_rows(source_snapshot)
    if validate_obligation_inventory_count(
        dict(source_snapshot.resource_counts), len(rows)
    ):
        raise SemanticObligationInventoryError("OBLIGATION_INVENTORY_OVERFLOW")
    ledger: dict[str, Any] = {
        "schema_version": LEDGER_SCHEMA,
        "ledger_id": "nls3obl_0000000000000000",
        "source_observation_plan_sha256": source_snapshot.source_observation_plan_sha256,
        "source_observation_stage_context_sha256": (
            source_snapshot.source_observation_stage_context_sha256
        ),
        "source_reception_opportunity_plan_sha256": (
            source_snapshot.source_reception_opportunity_plan_sha256
        ),
        "response_eligibility_source_sha256": (
            source_snapshot.response_eligibility_source_sha256
        ),
        "response_eligibility": source_snapshot.response_eligibility,
        "source_policy_sha256": source_snapshot.source_policy_sha256,
        "allowed_source_owners": list(ALLOWED_SOURCE_OWNERS),
        "obligations": rows,
        "required_obligation_ids": sorted(
            row["obligation_id"] for row in rows if row["required"] is True
        ),
        "body_free": True,
    }
    ledger["ledger_id"] = derive_content_id("nls3obl_", ledger, "ledger_id")
    issues = validate_semantic_obligation_inventory(
        ledger, source_snapshot=source_snapshot
    )
    if issues:
        raise SemanticObligationInventoryError(issues[0])
    return SemanticObligationInventoryResult(
        ledger=ledger,
        source_snapshot=source_snapshot,
        resource_counts=dict(source_snapshot.resource_counts),
        inventory_upper_bound=source_snapshot.obligation_inventory_upper_bound,
    )


def validate_semantic_obligation_inventory(
    value: Any,
    *,
    source_snapshot: GroundedSourceSnapshot,
) -> tuple[str, ...]:
    """Validate exact identity/content against the independent source snapshot."""

    issues = list(_snapshot_authority_issues(source_snapshot))
    contract_issues = validate_semantic_obligation_ledger(
        value, authority=source_snapshot.ledger_source_authority
    )
    issues.extend(f"CONTRACT_{item.code}:{item.path}" for item in contract_issues)
    if type(value) is not dict or type(value.get("obligations")) is not list:
        return tuple(sorted(set(issues or ["LEDGER_SHAPE_INVALID"])))
    try:
        expected_rows = _discover_obligation_rows(source_snapshot)
    except SemanticObligationInventoryError as exc:
        issues.append(exc.code)
        return tuple(sorted(set(issues)))
    rows = value["obligations"]
    actual_ids = [
        row.get("obligation_id") if type(row) is dict else None for row in rows
    ]
    expected_ids = [row["obligation_id"] for row in expected_rows]
    if actual_ids != expected_ids:
        issues.append("OBLIGATION_IDENTITY_SET_MISMATCH")
    if rows != expected_rows:
        issues.append("OBLIGATION_CONTENT_MISMATCH")
    expected_required = sorted(
        row["obligation_id"] for row in expected_rows if row["required"] is True
    )
    if value.get("required_obligation_ids") != expected_required:
        issues.append("REQUIRED_OBLIGATION_SET_MISMATCH")
    if len(rows) > source_snapshot.obligation_inventory_upper_bound:
        issues.append("OBLIGATION_INVENTORY_OVERFLOW")

    by_id = {
        row.get("obligation_id"): row
        for row in rows
        if type(row) is dict and type(row.get("obligation_id")) is str
    }
    stance_rows = [
        row
        for row in rows
        if type(row) is dict and row.get("kind") == "bound_emlis_reception"
    ]
    if source_snapshot.response_eligibility in _VISIBLE_ELIGIBILITIES:
        if not any(row.get("required") is True for row in stance_rows):
            issues.append("REQUIRED_BOUND_RECEPTION_MISSING")
        for row in stance_rows:
            targets = row.get("target_obligation_ids") or []
            if len(targets) != 1 or by_id.get(targets[0], {}).get("kind") in {
                None,
                "bound_emlis_reception",
                "bounded_counterposition",
            }:
                issues.append("RECEPTION_TARGET_UNRESOLVED")
    used_opportunities = {
        item
        for row in stance_rows
        for item in row.get("reception_opportunity_ids", [])
    }
    expected_opportunities = {
        row.source_id for row in source_snapshot.reception_opportunities
    }
    if used_opportunities != expected_opportunities:
        issues.append("RECEPTION_OPPORTUNITY_DISCOVERY_INCOMPLETE")
    if bool(used_opportunities) != bool(
        source_snapshot.source_reception_opportunity_plan_sha256
    ):
        issues.append("RECEPTION_PLAN_LINEAGE_REQUIRED")
    if source_snapshot.observation_stage == "pre_question_observation":
        active_unknowns = {
            unknown_id
            for row in rows
            if type(row) is dict and row.get("required") is True
            for unknown_id in row.get("unknown_boundary_ids", [])
        }
        if active_unknowns != source_snapshot.preserved_unknown_boundary_ids:
            issues.append("PRE_QUESTION_UNKNOWN_COMPLETION_FORBIDDEN")
        if not any(
            type(row) is dict
            and row.get("required") is True
            and row.get("kind") != "unknown_boundary_preservation"
            for row in rows
        ):
            issues.append("PRE_QUESTION_OBSERVATION_REQUIRED")
    return tuple(sorted(set(issues)))


__all__ = [
    "FROZEN_SOURCE_POLICY_SHA256",
    "GroundedSourceSnapshot",
    "InventoryNucleusSource",
    "InventoryReceptionSource",
    "InventoryRelationSource",
    "InventoryUnknownSource",
    "ObservationStageSourceBinding",
    "SemanticObligationInventoryError",
    "SemanticObligationInventoryResult",
    "SourceIdAliasBinding",
    "SOURCE_POLICY_ARTIFACT",
    "SOURCE_POLICY_SHA256",
    "TrustedResponseEligibilityAuthority",
    "build_grounded_source_snapshot",
    "build_semantic_obligation_inventory",
    "obligation_inventory_upper_bound",
    "validate_obligation_inventory_count",
    "validate_semantic_obligation_inventory",
]
