# -*- coding: utf-8 -*-
from __future__ import annotations

"""Emlis V1-A text-grounded graph, plan, realization and trace sealer."""

from dataclasses import dataclass, replace
import hashlib
import re
from typing import Any, Iterable, Sequence

from emlis_ai_conversation_composer_service import compose_emlis_conversation_candidate
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_human_reception import (
    realize_grounded_human_reception,
    validate_grounded_human_reception_surface,
)
from emlis_ai_grounded_observation_plan import (
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_safety_triage import TRIAGE_SAFE_OBSERVATION
from emlis_ai_types import (
    AddresseeNotes,
    GraphClaim,
    LimitedObservationScope,
    ObservationGraph,
    RelationEdge,
)

from .contracts import (
    CMEE_OBLIGATION_VERSION,
    EpistemicState,
    ExperiencePlan,
    GenerationArtifactBundle,
    GroundedMeaningGraph,
    MeaningEdge,
    MeaningNode,
    OwnerDisposition,
    RouteBDisposition,
    VisibleUnitTrace,
)
from .source_kernel import AdmittedTextSource


OBSERVATION_DUTY_ID = "OBSERVE_SOURCE_EXPLICIT_CURRENT_MEANING"
RECEPTION_DUTY_ID = "BOUND_HUMAN_RECEPTION_TO_VISIBLE_OBSERVATION"
REALIZER_CONTRACT_IDS = (
    "cocolon.cmee.emlis.plan_bound_limited_composer_adapter.v1",
    "cocolon.emlis.grounded_human_reception_surface.v1",
)
ADMISSIBLE_NUCLEUS_GROUNDING = frozenset({"explicit", "user_stated_relation"})
ADMISSIBLE_RELATION_GROUNDING = frozenset({"user_stated_relation"})
NEGATIVE_RECEPTION_RE = re.compile(r"(?:苦しさ|つらさ|負担|痛み|しんどさ)")
SOURCE_BURDEN_CUE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|嫌|限界|痛|しんど|迷惑|ダメ|悪化|不便|動けない|できない|何もしたくない)"
)
EXPECTED_COMMON_GUARDS = frozenset(
    {
        "cocolon_text_generation_core.guards.japanese_coherence.v1",
        "cocolon_text_generation_core.guards.template_echo.v1",
        "cocolon_text_generation_core.guards.overclaim_diagnosis.v1",
        "cocolon_text_generation_core.guards.grounding.v1",
        "cocolon_text_generation_core.guards.must_keep_coverage.v1",
    }
)
TRUST_POLICY_IDS = (
    *tuple(sorted(EXPECTED_COMMON_GUARDS)),
    "cocolon.emlis.grounded_human_reception_surface_validation.v1",
    "cocolon.cmee.route_b.positive_realization_trace.v1",
)


class CMEEVerticalError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = str(reason_code or "cmee_vertical_failed")
        super().__init__(self.reason_code)


@dataclass(frozen=True, slots=True)
class _CMEEVisibleBinding:
    line_role: str
    nucleus_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    evidence_span_ids: tuple[str, ...]
    claim_scope: str = "cmee_source_explicit_plan"
    contains_question: bool = False
    required: bool = True


@dataclass(frozen=True, slots=True)
class _CMEEVisibleLine:
    sentence_id: str
    text: str
    binding: _CMEEVisibleBinding


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}-{_sha256_text('|'.join(values))[:24]}"


def _graph_id(
    source_envelope_id: str,
    owner_universe_digest: str,
    nodes: Sequence[MeaningNode],
    edges: Sequence[MeaningEdge],
    dispositions: Sequence[OwnerDisposition],
) -> str:
    node_parts = tuple(
        "\x1f".join(
            (
                row.node_id,
                row.owner_id,
                row.node_kind,
                row.grounding_kind,
                _sha256_text(row.value),
                row.epistemic_state.value,
                *row.evidence_ids,
            )
        )
        for row in nodes
    )
    edge_parts = tuple(
        "\x1f".join(
            (
                row.edge_id,
                row.owner_id,
                row.relation,
                row.source_node_id,
                row.target_node_id,
                row.grounding_kind,
                row.epistemic_state.value,
                *row.evidence_ids,
            )
        )
        for row in edges
    )
    disposition_parts = tuple(
        "\x1f".join((row.owner_id, row.disposition.value, *row.evidence_ids))
        for row in dispositions
    )
    return _stable_id(
        "graph",
        source_envelope_id,
        owner_universe_digest,
        *node_parts,
        *edge_parts,
        *disposition_parts,
    )


def _plan_id(
    source_envelope_id: str,
    graph_id: str,
    plan: ExperiencePlan,
    visible_line_ids: Sequence[str],
) -> str:
    return _stable_id(
        "plan",
        source_envelope_id,
        graph_id,
        plan.source_plan_version,
        plan.observation_duty_id,
        plan.reception_duty_id,
        plan.reception_plan_digest,
        *plan.allowed_reception_act_ids,
        *plan.required_observation_owner_ids,
        *plan.reception_target_owner_ids,
        *plan.visible_owner_ids,
        *plan.unresolved_owner_ids,
        *visible_line_ids,
    )


def _reception_plan_contract(grounded_plan: Any) -> tuple[str, tuple[str, ...]]:
    reception_plan = grounded_plan.response_plan.human_reception_plan
    if reception_plan is None or not reception_plan.required:
        raise CMEEVerticalError("bound_human_reception_plan_missing")
    move_parts = tuple(
        "\x1f".join(
            (
                str(move.move_id),
                str(move.reception_act),
                str(move.move_role),
                *(str(value) for value in move.target_nucleus_ids),
                *(str(value) for value in move.support_nucleus_ids),
                *(str(value) for value in move.source_evidence_span_ids),
            )
        )
        for move in reception_plan.moves
    )
    digest = _sha256_text(
        "|".join(
            (
                str(reception_plan.schema_version),
                *(str(value) for value in reception_plan.target_nucleus_ids),
                *(str(value) for value in reception_plan.support_nucleus_ids),
                *(str(value) for value in reception_plan.source_evidence_span_ids),
                *move_parts,
            )
        )
    )
    return digest, _ordered(move.reception_act for move in reception_plan.moves)


def _artifact_id(
    source_envelope_id: str,
    graph_id: str,
    plan_id: str,
    observation: str,
    reception: str,
) -> str:
    return _stable_id(
        "artifact",
        source_envelope_id,
        graph_id,
        plan_id,
        *REALIZER_CONTRACT_IDS,
        *TRUST_POLICY_IDS,
        _sha256_text(observation),
        _sha256_text(reception),
    )


def _ordered(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _owner_for_nucleus(nucleus_id: str) -> str:
    return f"nucleus:{nucleus_id}"


def _owner_for_relation(relation_id: str) -> str:
    return f"relation:{relation_id}"


def _owner_for_unknown(unknown_id: str) -> str:
    return f"unknown:{unknown_id}"


def _build_graph(
    source: AdmittedTextSource,
    grounded_plan: Any,
    planned_visible_nucleus_ids: Sequence[str],
    planned_visible_relation_ids: Sequence[str],
) -> GroundedMeaningGraph:
    visible_nuclei = set(planned_visible_nucleus_ids)
    visible_relations = set(planned_visible_relation_ids)
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}

    nodes: list[MeaningNode] = []
    dispositions: list[OwnerDisposition] = []
    node_id_by_source: dict[str, str] = {}
    for nucleus in grounded_plan.nuclei:
        owner = _owner_for_nucleus(nucleus.nucleus_id)
        evidence = tuple(
            ref_by_span[span_id].evidence_id
            for span_id in nucleus.source_span_ids
            if span_id in ref_by_span
        )
        is_visible = nucleus.nucleus_id in visible_nuclei
        if is_visible and nucleus.grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING:
            raise CMEEVerticalError("provisional_nucleus_visible_authority_forbidden")
        node_id = _stable_id("mn", source.envelope.envelope_id, nucleus.nucleus_id)
        node_id_by_source[nucleus.nucleus_id] = node_id
        value = "\n".join(
            str(getattr(span, "raw_text", "") or "")
            for span in source.evidence_spans
            if str(getattr(span, "span_id", "") or "") in set(nucleus.source_span_ids)
        )
        nodes.append(
            MeaningNode(
                node_id=node_id,
                owner_id=owner,
                node_kind=str(nucleus.kind),
                grounding_kind=str(nucleus.grounding_kind),
                value=value,
                epistemic_state=(
                    EpistemicState.SOURCE_EXPLICIT
                    if nucleus.grounding_kind in ADMISSIBLE_NUCLEUS_GROUNDING
                    else EpistemicState.UNKNOWN
                ),
                evidence_ids=evidence,
            )
        )
        dispositions.append(
            OwnerDisposition(
                owner_id=owner,
                disposition=(
                    RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                    if is_visible
                    else RouteBDisposition.UNKNOWN_PRESERVED_LIMITED
                ),
                evidence_ids=evidence,
            )
        )

    edges: list[MeaningEdge] = []
    for relation in grounded_plan.relations:
        owner = _owner_for_relation(relation.relation_id)
        evidence = tuple(
            ref_by_span[span_id].evidence_id
            for span_id in relation.source_span_ids
            if span_id in ref_by_span
        )
        is_visible = relation.relation_id in visible_relations
        if is_visible and relation.grounding_kind not in ADMISSIBLE_RELATION_GROUNDING:
            raise CMEEVerticalError("provisional_relation_visible_authority_forbidden")
        if relation.from_nucleus_id not in node_id_by_source or relation.to_nucleus_id not in node_id_by_source:
            raise CMEEVerticalError("relation_endpoint_unknown")
        edge_id = _stable_id("me", source.envelope.envelope_id, relation.relation_id)
        edges.append(
            MeaningEdge(
                edge_id=edge_id,
                owner_id=owner,
                relation=str(relation.type),
                source_node_id=node_id_by_source[relation.from_nucleus_id],
                target_node_id=node_id_by_source[relation.to_nucleus_id],
                grounding_kind=str(relation.grounding_kind),
                epistemic_state=(
                    EpistemicState.SOURCE_EXPLICIT
                    if relation.grounding_kind in ADMISSIBLE_RELATION_GROUNDING
                    else EpistemicState.UNKNOWN
                ),
                evidence_ids=evidence,
            )
        )
        dispositions.append(
            OwnerDisposition(
                owner_id=owner,
                disposition=(
                    RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                    if is_visible
                    else RouteBDisposition.UNKNOWN_PRESERVED_LIMITED
                ),
                evidence_ids=evidence,
            )
        )

    for unknown in grounded_plan.unknown_boundaries:
        owner = _owner_for_unknown(unknown.unknown_id)
        evidence = tuple(
            ref_by_span[span_id].evidence_id
            for span_id in unknown.evidence_span_ids
            if span_id in ref_by_span
        )
        nodes.append(
            MeaningNode(
                node_id=_stable_id("mn", source.envelope.envelope_id, unknown.unknown_id),
                owner_id=owner,
                node_kind=f"UNKNOWN:{unknown.dimension}",
                grounding_kind="unknown_boundary",
                value="",
                epistemic_state=EpistemicState.UNKNOWN,
                evidence_ids=evidence,
            )
        )
        dispositions.append(
            OwnerDisposition(
                owner_id=owner,
                disposition=RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
                evidence_ids=evidence,
            )
        )

    # Strength is part of the admitted structured source but this slice does
    # not realize it. Keep it in the owner denominator as an explicit unknown
    # instead of silently dropping the source field.
    strength_ref = source.evidence_ref("structured:emotion_strength")
    strength_owner = "source:emotion_strength"
    nodes.append(
        MeaningNode(
            node_id=_stable_id("mn", source.envelope.envelope_id, strength_owner),
            owner_id=strength_owner,
            node_kind="STRUCTURED_EMOTION_STRENGTH",
            grounding_kind="source_explicit_not_realized",
            value=source.strength,
            epistemic_state=EpistemicState.UNKNOWN,
            evidence_ids=(strength_ref.evidence_id,),
        )
    )
    dispositions.append(
        OwnerDisposition(
            owner_id=strength_owner,
            disposition=RouteBDisposition.UNKNOWN_PRESERVED_LIMITED,
            evidence_ids=(strength_ref.evidence_id,),
        )
    )

    owner_refs = tuple(row.owner_id for row in dispositions)
    if len(owner_refs) != len(set(owner_refs)):
        raise CMEEVerticalError("route_b_owner_duplicate")
    owner_digest = _sha256_text(
        "|".join((source.envelope.source_contract_version, CMEE_OBLIGATION_VERSION, *owner_refs))
    )
    graph_id = _graph_id(
        source.envelope.envelope_id,
        owner_digest,
        nodes,
        edges,
        dispositions,
    )
    graph = GroundedMeaningGraph(
        graph_id=graph_id,
        source_envelope_id=source.envelope.envelope_id,
        nodes=tuple(nodes),
        edges=tuple(edges),
        owner_dispositions=tuple(dispositions),
        required_owner_refs=owner_refs,
        active_optional_owner_refs=(),
        source_version=source.envelope.source_contract_version,
        obligation_version=CMEE_OBLIGATION_VERSION,
        owner_universe_digest=owner_digest,
    )
    if set(row.owner_id for row in graph.owner_dispositions) != set(graph.required_owner_refs):
        raise CMEEVerticalError("route_b_owner_denominator_mismatch")
    return graph


def _planned_visible_source_ids(grounded_plan: Any) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    required_nuclei = tuple(grounded_plan.coverage_requirements.required_nucleus_ids)
    required_relations = tuple(grounded_plan.coverage_requirements.required_relation_ids)
    if any(
        row_id not in nucleus_index
        or nucleus_index[row_id].grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING
        for row_id in required_nuclei
    ):
        raise CMEEVerticalError("required_nucleus_visible_authority_unavailable")
    if any(
        row_id not in relation_index
        or relation_index[row_id].grounding_kind not in ADMISSIBLE_RELATION_GROUNDING
        for row_id in required_relations
    ):
        raise CMEEVerticalError("required_relation_visible_authority_unavailable")
    reception_targets = tuple(
        row_id
        for row_id in grounded_plan.response_plan.human_follow_target_ids
        if row_id in nucleus_index
        and nucleus_index[row_id].grounding_kind in ADMISSIBLE_NUCLEUS_GROUNDING
    )
    if not required_nuclei or not reception_targets:
        raise CMEEVerticalError("experience_plan_required_owner_missing")
    if not set(reception_targets).issubset(set(required_nuclei)):
        raise CMEEVerticalError("reception_target_not_in_observation_plan")
    return required_nuclei, required_relations, reception_targets


def _build_experience_plan(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: Any,
    required_nucleus_ids: Sequence[str],
    required_relation_ids: Sequence[str],
    reception_target_ids: Sequence[str],
) -> ExperiencePlan:
    visible = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition is RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
    )
    unresolved = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
    )
    source_plan_version = f"{grounded_plan.schema_version}|{grounded_plan.generation_path}"
    required_observation_owners = tuple(
        (*(_owner_for_nucleus(row_id) for row_id in required_nucleus_ids),
         *(_owner_for_relation(row_id) for row_id in required_relation_ids))
    )
    reception_target_owners = tuple(_owner_for_nucleus(row_id) for row_id in reception_target_ids)
    if not set(required_observation_owners + reception_target_owners).issubset(set(visible)):
        raise CMEEVerticalError("experience_plan_visible_owner_mismatch")
    reception_plan_digest, allowed_reception_act_ids = _reception_plan_contract(grounded_plan)
    return ExperiencePlan(
        plan_id=_stable_id(
            "plan",
            source.envelope.envelope_id,
            graph.graph_id,
            source_plan_version,
            *required_observation_owners,
            *reception_target_owners,
        ),
        source_plan_version=source_plan_version,
        observation_duty_id=OBSERVATION_DUTY_ID,
        reception_duty_id=RECEPTION_DUTY_ID,
        reception_plan_digest=reception_plan_digest,
        allowed_reception_act_ids=allowed_reception_act_ids,
        required_observation_owner_ids=required_observation_owners,
        reception_target_owner_ids=reception_target_owners,
        visible_owner_ids=visible,
        unresolved_owner_ids=unresolved,
        visible_line_ids=(),
    )


def _experience_plan_projection(
    source: AdmittedTextSource,
    plan: ExperiencePlan,
    grounded_plan: Any,
) -> LimitedObservationScope:
    """Project the exact CMEE visible-owner plan into the existing realizer port.

    This projection is intentionally not built from a second perspective
    observer graph. Claim and relation identities are the CMEE owner IDs, and
    only required visible owners enter the bounded composer.
    """

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    span_text = {
        str(getattr(row, "span_id", "") or ""): str(getattr(row, "raw_text", "") or "")
        for row in source.evidence_spans
    }
    required_nucleus_ids = tuple(
        owner_id.removeprefix("nucleus:")
        for owner_id in plan.required_observation_owner_ids
        if owner_id.startswith("nucleus:")
    )
    required_relation_ids = tuple(
        owner_id.removeprefix("relation:")
        for owner_id in plan.required_observation_owner_ids
        if owner_id.startswith("relation:")
    )
    if required_relation_ids:
        # The existing bounded composer binding has a relation type but no
        # endpoint/direction commitment. This first slice therefore refuses
        # relation-required inputs rather than granting false edge credit.
        raise CMEEVerticalError("relation_endpoint_binding_not_supported")
    claims: list[GraphClaim] = []
    for row_id in required_nucleus_ids:
        row = nucleus_index[row_id]
        evidence_ids = list(row.source_span_ids)
        text = " / ".join(span_text[span_id] for span_id in evidence_ids if span_id in span_text).strip()
        if not text or row.grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING:
            raise CMEEVerticalError("experience_plan_projection_nucleus_invalid")
        claims.append(
            GraphClaim(
                claim_id=_owner_for_nucleus(row_id),
                claim_type=str(row.kind),
                text=text,
                evidence_span_ids=evidence_ids,
                confidence=1.0,
            )
        )
    if not claims:
        raise CMEEVerticalError("experience_plan_projection_empty")

    relations: list[RelationEdge] = []
    claim_ids = {row.claim_id for row in claims}
    if any(
        row.from_claim_id not in claim_ids or row.to_claim_id not in claim_ids
        for row in relations
    ):
        raise CMEEVerticalError("experience_plan_projection_relation_endpoint_missing")

    primary = claims[0]
    remainder = claims[1:]
    projected_graph = ObservationGraph(
        primary_state=primary,
        core_tensions=relations,
        pressure_sources=[row for row in remainder if row.claim_type in {"state", "reaction"}],
        limit_signals=[row for row in remainder if row.claim_type in {"limit", "constraint"}],
        self_awareness=[row for row in remainder if row.claim_type == "self_awareness"],
        value_or_strength_signals=[
            row
            for row in remainder
            if row.claim_type not in {"state", "reaction", "limit", "constraint", "self_awareness"}
        ],
        addressee_notes=AddresseeNotes(sentence_target=max(2, min(4, len(claims) + 1))),
        safety_boundaries=[],
        forbidden_claims=[],
        missing_information=[],
    )
    return LimitedObservationScope(
        scope_status="eligible",
        scoped_graph=projected_graph,
        included_claim_ids=[row.claim_id for row in claims],
        included_relation_ids=[row.edge_id for row in relations],
        excluded_claims=[],
        min_reply_sentence_count=2,
        max_reply_sentence_count=4,
        coverage_scope="current_input_core",
        rejection_reasons=[],
        coverage_groups=["cmee_required_visible_owner_exact"],
        scope_expansion={"enabled": False, "owner": "CMEEExperiencePlan"},
        safety_boundary={},
        safety_boundary_policy={},
    )


def _realize_cmee_experience(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    grounded_plan: Any,
) -> tuple[_CMEEVisibleLine, ...]:
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    scope = _experience_plan_projection(source, plan, grounded_plan)
    material = build_observation_structure_material(
        current_input=source.normalized_current_input,
        evidence_ledger=source.evidence_spans,
        observation_graph=scope.scoped_graph,
    )
    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=source.evidence_spans,
        composer_client=CocolonLimitedComposerClient(),
        trace_id=_stable_id("composer", source.envelope.envelope_id, plan.plan_id),
        limited_observation_scope=scope,
        observation_structure_material=material,
    )
    if candidate.status != "generated" or candidate.composer_source != "ai_generated":
        raise CMEEVerticalError("plan_bound_observation_realizer_unavailable")
    composer_meta = candidate.composer_meta if isinstance(candidate.composer_meta, dict) else {}
    core_meta = composer_meta.get("core_text_generation")
    if (
        not isinstance(core_meta, dict)
        or core_meta.get("core_id") != "emlis"
        or core_meta.get("status") != "generated"
        or not bool(core_meta.get("passed"))
    ):
        raise CMEEVerticalError("plan_bound_observation_common_core_rejected")
    binding_reflection = core_meta.get("step7_gate_binding_reflection")
    if not isinstance(binding_reflection, dict) or not bool(binding_reflection.get("binding_used")):
        raise CMEEVerticalError("plan_bound_observation_common_core_binding_unused")
    stabilization = core_meta.get("step15_common_core_stabilization")
    if not isinstance(stabilization, dict) or set(stabilization.get("guard_names") or ()) != set(
        EXPECTED_COMMON_GUARDS
    ):
        raise CMEEVerticalError("plan_bound_observation_guard_set_mismatch")
    core_bindings = core_meta.get("sentence_bindings")
    raw_bindings = composer_meta.get("sentence_bindings")
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise CMEEVerticalError("plan_bound_observation_binding_missing")
    if not isinstance(core_bindings, list) or len(core_bindings) != len(raw_bindings):
        raise CMEEVerticalError("plan_bound_observation_core_binding_mismatch")
    for core_binding, surface_binding in zip(core_bindings, raw_bindings, strict=True):
        if not isinstance(core_binding, dict) or not isinstance(surface_binding, dict):
            raise CMEEVerticalError("plan_bound_observation_binding_invalid")
        for key in ("sentence_id", "used_evidence_span_ids", "relation_type", "line_role"):
            if core_binding.get(key) != surface_binding.get(key):
                raise CMEEVerticalError("plan_bound_observation_core_binding_mismatch")

    required_nucleus_ids = tuple(
        owner_id.removeprefix("nucleus:")
        for owner_id in plan.required_observation_owner_ids
        if owner_id.startswith("nucleus:")
    )
    required_relation_ids = tuple(
        owner_id.removeprefix("relation:")
        for owner_id in plan.required_observation_owner_ids
        if owner_id.startswith("relation:")
    )
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    allowed_evidence_ids = {
        span_id
        for row_id in required_nucleus_ids
        for span_id in nucleus_index[row_id].source_span_ids
    } | {
        span_id
        for row_id in required_relation_ids
        for span_id in relation_index[row_id].source_span_ids
    }
    observation_lines: list[_CMEEVisibleLine] = []
    for ordinal, raw_binding in enumerate(raw_bindings, start=1):
        if not isinstance(raw_binding, dict):
            raise CMEEVerticalError("plan_bound_observation_binding_invalid")
        text = str(raw_binding.get("text") or "").strip()
        evidence_span_ids = _ordered(raw_binding.get("used_evidence_span_ids") or ())
        relation_type = str(raw_binding.get("relation_type") or "")
        binding_meta = raw_binding.get("meta") if isinstance(raw_binding.get("meta"), dict) else {}
        if (
            str(raw_binding.get("line_role") or "") == "human_follow"
            or str(binding_meta.get("state_answer_section_role") or "")
            not in {"", "state_answer_observation"}
        ):
            raise CMEEVerticalError("plan_bound_observation_non_observation_line")
        if not text or not evidence_span_ids or not set(evidence_span_ids).issubset(allowed_evidence_ids):
            raise CMEEVerticalError("plan_bound_observation_out_of_plan_evidence")
        nucleus_ids = tuple(
            row_id
            for row_id in required_nucleus_ids
            if set(nucleus_index[row_id].source_span_ids).issubset(set(evidence_span_ids))
        )
        relation_ids = tuple(
            row_id
            for row_id in required_relation_ids
            if relation_index[row_id].type == relation_type
            and set(relation_index[row_id].source_span_ids).issubset(set(evidence_span_ids))
        )
        if not nucleus_ids and not relation_ids:
            raise CMEEVerticalError("plan_bound_observation_owner_missing")
        observation_lines.append(
            _CMEEVisibleLine(
                sentence_id=f"cmee:observation:{ordinal}",
                text=text,
                binding=_CMEEVisibleBinding(
                    line_role="cmee_observation",
                    nucleus_ids=nucleus_ids,
                    relation_ids=relation_ids,
                    evidence_span_ids=evidence_span_ids,
                    claim_scope="cmee_plan_bound_existing_composer",
                    required=True,
                ),
            )
        )
    reception_plan = grounded_plan.response_plan.human_reception_plan
    if reception_plan is None or not reception_plan.required:
        raise CMEEVerticalError("bound_human_reception_plan_missing")
    reception_surface = realize_grounded_human_reception(
        reception_plan,
        nucleus_index,
        resolver,
    )
    reception_issues = validate_grounded_human_reception_surface(
        reception_surface,
        reception_plan,
        resolver,
    )
    if reception_issues:
        raise CMEEVerticalError("bound_human_reception_surface_rejected")
    expected_reception_digest, expected_reception_acts = _reception_plan_contract(grounded_plan)
    if (
        plan.reception_plan_digest != expected_reception_digest
        or plan.allowed_reception_act_ids != expected_reception_acts
        or tuple(reception_surface.realized_reception_acts) != expected_reception_acts
    ):
        raise CMEEVerticalError("bound_human_reception_act_contract_mismatch")
    reception_targets = tuple(
        owner_id.removeprefix("nucleus:") for owner_id in plan.reception_target_owner_ids
    )
    if tuple(reception_surface.grounded_nucleus_ids) != reception_targets:
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    target_polarities = {
        str(nucleus_index[row_id].semantic_frame.polarity) for row_id in reception_targets
    }
    burden_acts = {"stay_with_current_burden", "bounded_counter_self_denial"}
    if target_polarities == {"positive"} and burden_acts.intersection(expected_reception_acts):
        raise CMEEVerticalError("bound_human_reception_positive_burden_promotion")
    reception_line = _CMEEVisibleLine(
        sentence_id="cmee:reception:1",
        text=reception_surface.text,
        binding=_CMEEVisibleBinding(
            line_role="human_follow",
            nucleus_ids=reception_targets,
            relation_ids=(),
            evidence_span_ids=tuple(reception_surface.grounded_evidence_span_ids),
            claim_scope="cmee_grounded_human_reception",
            required=True,
        ),
    )
    lines = (*observation_lines, reception_line)
    observed_nuclei = {
        nucleus_id
        for line in observation_lines
        for nucleus_id in line.binding.nucleus_ids
    }
    observed_relations = {
        relation_id
        for line in observation_lines
        for relation_id in line.binding.relation_ids
    }
    if set(required_nucleus_ids) != observed_nuclei:
        raise CMEEVerticalError("post_realization_required_nucleus_mismatch")
    if set(required_relation_ids) != observed_relations:
        raise CMEEVerticalError("post_realization_required_relation_mismatch")
    if not set(reception_targets).issubset(observed_nuclei):
        raise CMEEVerticalError("bound_human_reception_target_not_observed")
    _validate_reception_semantic_compatibility(source, lines)
    return tuple(lines)


def _validate_reception_semantic_compatibility(
    source: AdmittedTextSource,
    visible_lines: Sequence[Any],
) -> None:
    reception = tuple(line for line in visible_lines if line.binding.line_role == "human_follow")
    if len(reception) != 1:
        raise CMEEVerticalError("reception_semantic_cardinality_mismatch")
    observation_span_ids = {
        span_id
        for line in visible_lines
        if line.binding.line_role != "human_follow"
        for span_id in line.binding.evidence_span_ids
    }
    source_text = "\n".join(
        str(getattr(span, "raw_text", "") or "")
        for span in source.evidence_spans
        if str(getattr(span, "span_id", "") or "") in observation_span_ids
    )
    if NEGATIVE_RECEPTION_RE.search(reception[0].text) and not SOURCE_BURDEN_CUE_RE.search(source_text):
        raise CMEEVerticalError("reception_negative_meaning_promotion")


def _bind_plan_to_visible_lines(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    visible_lines: Sequence[Any],
) -> ExperiencePlan:
    line_ids = tuple(line.sentence_id for line in visible_lines)
    return replace(
        plan,
        plan_id=_plan_id(source.envelope.envelope_id, graph.graph_id, plan, line_ids),
        visible_line_ids=line_ids,
    )


def _trace_for_lines(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    safe_lines: Sequence[Any],
) -> tuple[VisibleUnitTrace, ...]:
    node_by_owner = {row.owner_id: row for row in graph.nodes}
    edge_by_owner = {row.owner_id: row for row in graph.edges}
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    traces: list[VisibleUnitTrace] = []
    for ordinal, line in enumerate(safe_lines, start=1):
        is_reception = line.binding.line_role == "human_follow"
        node_ids = tuple(
            node_by_owner[_owner_for_nucleus(source_id)].node_id
            for source_id in line.binding.nucleus_ids
        )
        edge_ids = tuple(
            edge_by_owner[_owner_for_relation(source_id)].edge_id
            for source_id in line.binding.relation_ids
        )
        evidence_ids = tuple(ref_by_span[source_id].evidence_id for source_id in line.binding.evidence_span_ids)
        traces.append(
            VisibleUnitTrace(
                visible_unit_id=f"visible:{ordinal}",
                source_sentence_id=line.sentence_id,
                role="RECEPTION" if is_reception else "OBSERVATION",
                operation="BOUND_HUMAN_RECEPTION" if is_reception else "SOURCE_EXPLICIT_GROUNDED_OBSERVATION",
                text_sha256=_sha256_text(line.text),
                duty_id=plan.reception_duty_id if is_reception else plan.observation_duty_id,
                meaning_node_ids=node_ids,
                meaning_edge_ids=edge_ids,
                evidence_ids=evidence_ids,
                constrained_by_owner_ids=plan.unresolved_owner_ids if is_reception else (),
            )
        )
    return tuple(traces)


def validate_positive_realization_trace(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    artifact: GenerationArtifactBundle,
    safe_lines: Sequence[Any],
) -> None:
    canonical_resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    canonical_grounded_plan = build_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    if validate_grounded_observation_plan(canonical_grounded_plan, canonical_resolver):
        raise CMEEVerticalError("canonical_grounded_meaning_plan_invalid")
    canonical_nuclei, canonical_relations, canonical_reception_targets = (
        _planned_visible_source_ids(canonical_grounded_plan)
    )
    canonical_graph = _build_graph(
        source,
        canonical_grounded_plan,
        _ordered((*canonical_nuclei, *canonical_reception_targets)),
        canonical_relations,
    )
    if graph != canonical_graph:
        raise CMEEVerticalError("grounded_meaning_graph_source_semantic_mismatch")
    canonical_plan = _build_experience_plan(
        source,
        canonical_graph,
        canonical_grounded_plan,
        canonical_nuclei,
        canonical_relations,
        canonical_reception_targets,
    )
    canonical_plan = _bind_plan_to_visible_lines(
        source,
        canonical_graph,
        canonical_plan,
        safe_lines,
    )
    if artifact.plan != canonical_plan:
        raise CMEEVerticalError("experience_plan_source_semantic_mismatch")
    if graph.source_envelope_id != source.envelope.envelope_id:
        raise CMEEVerticalError("graph_source_envelope_mismatch")
    owners = tuple(row.owner_id for row in graph.owner_dispositions)
    expected_owners = graph.required_owner_refs + graph.active_optional_owner_refs
    if owners != expected_owners or len(owners) != len(set(owners)):
        raise CMEEVerticalError("route_b_owner_denominator_mismatch")
    expected_digest = _sha256_text(
        "|".join((graph.source_version, graph.obligation_version, *expected_owners))
    )
    if graph.owner_universe_digest != expected_digest:
        raise CMEEVerticalError("route_b_owner_digest_mismatch")
    if graph.graph_id != _graph_id(
        source.envelope.envelope_id,
        graph.owner_universe_digest,
        graph.nodes,
        graph.edges,
        graph.owner_dispositions,
    ):
        raise CMEEVerticalError("grounded_meaning_graph_identity_mismatch")
    if artifact.plan.observation_duty_id != OBSERVATION_DUTY_ID:
        raise CMEEVerticalError("observation_duty_identity_mismatch")
    if artifact.plan.reception_duty_id != RECEPTION_DUTY_ID:
        raise CMEEVerticalError("reception_duty_identity_mismatch")
    if artifact.realizer_contract_ids != REALIZER_CONTRACT_IDS:
        raise CMEEVerticalError("realizer_contract_identity_mismatch")
    if artifact.trust_policy_ids != TRUST_POLICY_IDS:
        raise CMEEVerticalError("trust_policy_identity_mismatch")
    if artifact.plan.plan_id != _plan_id(
        source.envelope.envelope_id,
        graph.graph_id,
        artifact.plan,
        artifact.plan.visible_line_ids,
    ):
        raise CMEEVerticalError("experience_plan_identity_mismatch")
    if set(artifact.plan.visible_owner_ids).intersection(artifact.plan.unresolved_owner_ids):
        raise CMEEVerticalError("plan_owner_partition_overlap")
    if set(artifact.plan.visible_owner_ids + artifact.plan.unresolved_owner_ids) != set(owners):
        raise CMEEVerticalError("plan_owner_partition_mismatch")
    if artifact.plan.visible_line_ids != tuple(line.sentence_id for line in safe_lines):
        raise CMEEVerticalError("plan_visible_line_set_mismatch")
    if len(artifact.trace) != len(safe_lines):
        raise CMEEVerticalError("visible_trace_count_mismatch")
    expected_visible_unit_ids = tuple(
        f"visible:{ordinal}" for ordinal in range(1, len(safe_lines) + 1)
    )
    if tuple(row.visible_unit_id for row in artifact.trace) != expected_visible_unit_ids:
        raise CMEEVerticalError("visible_trace_unit_identity_mismatch")

    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    disposition = {row.owner_id: row.disposition for row in graph.owner_dispositions}
    refs = {row.source_span_id: row for row in source.evidence_refs}
    observation_text: list[str] = []
    reception_text: list[str] = []
    for trace, line in zip(artifact.trace, safe_lines, strict=True):
        is_reception = line.binding.line_role == "human_follow"
        expected_role = "RECEPTION" if is_reception else "OBSERVATION"
        expected_duty = artifact.plan.reception_duty_id if is_reception else artifact.plan.observation_duty_id
        expected_operation = "BOUND_HUMAN_RECEPTION" if is_reception else "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
        expected_nodes = tuple(
            next(row.node_id for row in graph.nodes if row.owner_id == _owner_for_nucleus(source_id))
            for source_id in line.binding.nucleus_ids
        )
        expected_edges = tuple(
            next(row.edge_id for row in graph.edges if row.owner_id == _owner_for_relation(source_id))
            for source_id in line.binding.relation_ids
        )
        expected_evidence = tuple(refs[source_id].evidence_id for source_id in line.binding.evidence_span_ids)
        expected_constraints = artifact.plan.unresolved_owner_ids if is_reception else ()
        if (
            trace.source_sentence_id != line.sentence_id
            or trace.role != expected_role
            or trace.duty_id != expected_duty
            or trace.operation != expected_operation
            or trace.text_sha256 != _sha256_text(line.text)
            or trace.meaning_node_ids != expected_nodes
            or trace.meaning_edge_ids != expected_edges
            or trace.evidence_ids != expected_evidence
            or trace.constrained_by_owner_ids != expected_constraints
        ):
            raise CMEEVerticalError("visible_trace_exact_binding_mismatch")
        for node_id in trace.meaning_node_ids:
            node = nodes.get(node_id)
            if (
                node is None
                or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or disposition.get(node.owner_id) is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
            ):
                raise CMEEVerticalError("visible_trace_node_authority_mismatch")
        for edge_id in trace.meaning_edge_ids:
            edge = edges.get(edge_id)
            if (
                edge is None
                or edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or disposition.get(edge.owner_id) is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
            ):
                raise CMEEVerticalError("visible_trace_edge_authority_mismatch")
        for source_id in line.binding.evidence_span_ids:
            ref = refs[source_id]
            selected_raw = source.envelope.raw_utf8[ref.utf8_start : ref.utf8_end]
            expected_normalized = next(
                str(getattr(span, "raw_text", "") or "")
                for span in source.evidence_spans
                if str(getattr(span, "span_id", "") or "") == source_id
            )
            if (
                ref.source_envelope_id != source.envelope.envelope_id
                or selected_raw.decode("utf-8").replace("\u3000", " ") != expected_normalized
                or _sha256_text(selected_raw.decode("utf-8")) != ref.literal_sha256
                or _sha256_text(
                    source.envelope.raw_utf8[
                        ref.field_utf8_start : ref.field_utf8_end
                    ].decode("utf-8")
                )
                != ref.field_sha256
            ):
                raise CMEEVerticalError("visible_trace_source_locator_mismatch")
        (reception_text if is_reception else observation_text).append(line.text)
    if artifact.observation != "\n".join(observation_text) or artifact.reception != "\n".join(reception_text):
        raise CMEEVerticalError("artifact_surface_trace_mismatch")
    if not observation_text or not reception_text:
        raise CMEEVerticalError("limited_artifact_duty_missing")
    realized_observation_owners = {
        *(nodes[node_id].owner_id for row in artifact.trace if row.role == "OBSERVATION" for node_id in row.meaning_node_ids),
        *(edges[edge_id].owner_id for row in artifact.trace if row.role == "OBSERVATION" for edge_id in row.meaning_edge_ids),
    }
    if realized_observation_owners != set(artifact.plan.required_observation_owner_ids):
        raise CMEEVerticalError("required_observation_owner_realization_mismatch")
    realized_reception_owners = {
        nodes[node_id].owner_id
        for row in artifact.trace
        if row.role == "RECEPTION"
        for node_id in row.meaning_node_ids
    }
    if realized_reception_owners != set(artifact.plan.reception_target_owner_ids):
        raise CMEEVerticalError("reception_target_owner_realization_mismatch")
    if artifact.artifact_id != _artifact_id(
        source.envelope.envelope_id,
        graph.graph_id,
        artifact.plan.plan_id,
        artifact.observation,
        artifact.reception,
    ):
        raise CMEEVerticalError("artifact_identity_mismatch")


def build_text_grounded_limited_artifact(
    source: AdmittedTextSource,
) -> tuple[GroundedMeaningGraph, ExperiencePlan, GenerationArtifactBundle]:
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    grounded_plan = build_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    if grounded_plan.input_profile.material_quality in {"labels_only_limited", "empty"}:
        raise CMEEVerticalError("text_grounded_material_unavailable")
    if grounded_plan.input_profile.safety_kind != TRIAGE_SAFE_OBSERVATION:
        raise CMEEVerticalError("separate_safety_owner_required")
    if validate_grounded_observation_plan(grounded_plan, resolver):
        raise CMEEVerticalError("grounded_meaning_plan_invalid")

    required_nucleus_ids, required_relation_ids, reception_target_ids = (
        _planned_visible_source_ids(grounded_plan)
    )
    planned_visible_nucleus_ids = _ordered((*required_nucleus_ids, *reception_target_ids))
    graph = _build_graph(
        source,
        grounded_plan,
        planned_visible_nucleus_ids,
        required_relation_ids,
    )
    plan = _build_experience_plan(
        source,
        graph,
        grounded_plan,
        required_nucleus_ids,
        required_relation_ids,
        reception_target_ids,
    )
    safe_lines = _realize_cmee_experience(source, graph, plan, grounded_plan)
    plan = _bind_plan_to_visible_lines(source, graph, plan, safe_lines)
    observation = "\n".join(
        line.text for line in safe_lines if line.binding.line_role != "human_follow"
    )
    reception = "\n".join(
        line.text for line in safe_lines if line.binding.line_role == "human_follow"
    )
    trace = _trace_for_lines(source, graph, plan, safe_lines)
    artifact = GenerationArtifactBundle(
        artifact_id=_artifact_id(
            source.envelope.envelope_id,
            graph.graph_id,
            plan.plan_id,
            observation,
            reception,
        ),
        realizer_contract_ids=REALIZER_CONTRACT_IDS,
        trust_policy_ids=TRUST_POLICY_IDS,
        observation=observation,
        reception=reception,
        plan=plan,
        trace=trace,
    )
    validate_positive_realization_trace(source, graph, artifact, safe_lines)
    return graph, plan, artifact


__all__ = [
    "ADMISSIBLE_NUCLEUS_GROUNDING",
    "ADMISSIBLE_RELATION_GROUNDING",
    "CMEEVerticalError",
    "OBSERVATION_DUTY_ID",
    "RECEPTION_DUTY_ID",
    "build_text_grounded_limited_artifact",
    "validate_positive_realization_trace",
]
