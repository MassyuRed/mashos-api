# -*- coding: utf-8 -*-
from __future__ import annotations

"""Emlis V1-A text-grounded graph, plan, realization and trace sealer."""

from dataclasses import dataclass, replace
import hashlib
import json
import re
from typing import Any, Iterable, Sequence

from emlis_ai_conversation_composer_service import compose_emlis_conversation_candidate
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_human_reception import (
    realize_grounded_human_reception,
    validate_grounded_human_reception_surface,
)
from emlis_ai_grounded_observation_plan import (
    build_grounded_human_reception_plan,
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    DIRECTIONAL_GROUNDED_RELATION_TYPES,
    build_grounded_sentence_plan,
)
from emlis_ai_safety_triage import TRIAGE_SAFE_OBSERVATION
from emlis_ai_types import (
    AddresseeNotes,
    GraphClaim,
    LimitedObservationScope,
    ObservationGraph,
    RelationEdge,
)
from cocolon_text_generation_core.guards.base import split_sentences
from cocolon_text_generation_core.adapters.emlis_observation_composer import (
    attach_core_evaluation_meta,
    core_rejection_reason,
    evaluate_emlis_observation_candidate,
)

from .contracts import (
    AttachmentAdmission,
    CMEE_COMMON_GUARD_PROOF_VERSION,
    CommonGuardProof,
    CommonGuardResultProof,
    EpistemicState,
    ExperiencePlan,
    GenerationArtifactBundle,
    GroundedMeaningGraph,
    MeaningEdge,
    MeaningNode,
    OwnerClass,
    OwnerDisposition,
    ProviderResolution,
    RouteBDisposition,
    VisibleAuthority,
    VisibleUnknownUnit,
    VisibleUnitTrace,
)
from .source_kernel import (
    AdmittedTextSource,
    build_source_owner_universe,
    normalize_evidence_literal,
)


OBSERVATION_DUTY_ID = "OBSERVE_SOURCE_EXPLICIT_CURRENT_MEANING"
UNKNOWN_DUTY_ID = "PRESERVE_EVIDENCE_BOUND_UNKNOWN"
RECEPTION_DUTY_ID = "BOUND_HUMAN_RECEPTION_TO_VISIBLE_OBSERVATION"
STRUCTURED_ATTACHMENT_UNKNOWN_TEXT = (
    "書かれた内容と、選択された気持ち・カテゴリのあいだに、"
    "どのような関係があるかまでは、この入力だけでは決められません。"
)
REALIZER_CONTRACT_IDS = (
    "cocolon.cmee.emlis.plan_bound_grounded_surface_adapter.v2",
    "cocolon.cmee.emlis.semantic_reception_projection.v1",
)
ADMISSIBLE_NUCLEUS_GROUNDING = frozenset({"explicit", "user_stated_relation"})
ADMISSIBLE_RELATION_GROUNDING = frozenset({"user_stated_relation"})
NEGATIVE_RECEPTION_RE = re.compile(r"(?:苦しさ|つらさ|負担|痛み|しんどさ)")
SOURCE_BURDEN_CUE_RE = re.compile(
    r"(?:不安|疲|つら|苦|悲|怒|怖|嫌|限界|痛|しんど|迷惑|ダメ|悪化|不便|動けない|できない|何もしたくない)"
)
CMEE_SOURCE_ANCHOR_LIMIT = 6
CMEE_RECEPTION_MATERIAL_MODE = "limited_grounding"
CMEE_POSITIVE_RECEPTION_ACTS = frozenset(
    {
        "honor_concrete_effort",
        "protect_retained_intention",
        "recognize_lived_change",
        "hold_help_seeking",
    }
)
CMEE_BURDEN_RECEPTION_ACTS = frozenset(
    {"stay_with_current_burden", "bounded_counter_self_denial"}
)
CMEE_RELATION_SURFACE_LABELS = {
    "temporal_before_after": "時間の順序",
    "shift_from_to": "変化の方向",
    "contrast": "異なる向きの対比",
    "coexistence": "並存する関係",
    "user_stated_cause": "入力内で明示された理由の関係",
    "user_stated_result": "入力内で明示された結果の関係",
    "attempt_and_block": "試みと制約の関係",
    "wish_and_constraint": "願いと制約の関係",
    "action_supports_change": "行動と変化の関係",
    "evaluation_about_event": "出来事と評価の関係",
    "self_evaluation_about_state": "状態と自己評価の関係",
    "preserves_despite": "負荷の中に残る方向",
    "uncertain_connection": "入力内の順序上の関係",
    "continuation_or_refusal": "継続と拒否の関係",
}
EXPECTED_COMMON_GUARD_IDS = (
    "cocolon_text_generation_core.guards.japanese_coherence.v1",
    "cocolon_text_generation_core.guards.template_echo.v1",
    "cocolon_text_generation_core.guards.overclaim_diagnosis.v1",
    "cocolon_text_generation_core.guards.grounding.v1",
    "cocolon_text_generation_core.guards.must_keep_coverage.v1",
)
EXPECTED_COMMON_GUARDS = frozenset(EXPECTED_COMMON_GUARD_IDS)
EXPECTED_COMMON_SHAPE_PART_IDS = (
    "SourceAnchor",
    "EvidenceSpanLike",
    "PhraseUnit",
    "SentencePlan",
    "TextGenerationResult",
    "GuardResult",
    "used_evidence_span_ids",
    "quality_flags",
)
COMMON_GUARD_STABILIZATION_REPORT_NAME = (
    "cocolon_text_generation_core.step15_stabilization.v1"
)
COMMON_GUARD_STABILIZATION_PHASE = "step15_common_core_stabilization"
COMMON_GUARD_STABILIZATION_CORE_ID = "emlis"
TRUST_POLICY_IDS = (
    *tuple(sorted(EXPECTED_COMMON_GUARDS)),
    "cocolon.emlis.grounded_human_reception_surface_validation.v1",
    "cocolon.cmee.route_b.positive_realization_trace.v1",
)
ROUTE_B_REASON_CODES = frozenset(
    {
        "PROVIDER_IDENTITY_MISMATCH",
        "RESOURCE_LOCK_MISMATCH",
        "PROVIDER_OUTPUT_INVALID",
        "REQUIRED_OWNER_MISSING",
        "ATTACHMENT_AMBIGUOUS",
        "ATTACHMENT_UNRESOLVED",
        "OOV_UNRESOLVED",
        "NO_MEANINGFUL_GROUNDED_CLAIM",
        "CLARIFICATION_BUDGET_CONSUMED",
        "SUPPLEMENTAL_LINEAGE_MISMATCH",
        "PRIVATE_BOUNDARY_VIOLATION",
    }
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
    constrained_owner_ids: tuple[str, ...] = ()
    claim_scope: str = "cmee_source_explicit_plan"
    contains_question: bool = False
    required: bool = True


@dataclass(frozen=True, slots=True)
class _CMEEVisibleLine:
    sentence_id: str
    text: str
    binding: _CMEEVisibleBinding


@dataclass(frozen=True, slots=True)
class _CMEECorePhraseUnit:
    phrase_unit_id: str
    evidence_span_id: str
    raw_text: str
    compressed_text: str
    role: str = "source_grounded_observation"
    polarity: str = "neutral"
    must_keep: bool = False
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _CMEECoreSentencePlan:
    sentence_plan_id: str
    line_role: str
    phrase_unit_ids: tuple[str, ...]
    relation_type: str
    max_chars: int = 240
    must_include: bool = True


@dataclass(frozen=True, slots=True)
class _CommonGuardSealMaterial:
    guard_results: tuple[CommonGuardResultProof, ...]
    stabilization_report_name: str
    stabilization_phase: str
    stabilization_core_id: str
    stabilization_passed: bool
    common_shapes_ready: bool
    stabilization_guard_names: tuple[str, ...]
    issue_codes: tuple[str, ...]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}-{_sha256_text('|'.join(values))[:24]}"


def _extract_common_guard_seal(
    core_meta: dict[str, Any],
) -> _CommonGuardSealMaterial:
    """Validate and project the actual one-shot common-core guard result."""

    result = core_meta.get("result")
    result_meta = result.get("meta") if type(result) is dict else None
    raw_rows = result_meta.get("guard_results") if type(result_meta) is dict else None
    if type(raw_rows) is not list or len(raw_rows) != len(EXPECTED_COMMON_GUARD_IDS):
        raise CMEEVerticalError("plan_bound_observation_guard_result_shape_mismatch")

    guard_results: list[CommonGuardResultProof] = []
    for expected_guard_id, raw_row in zip(
        EXPECTED_COMMON_GUARD_IDS,
        raw_rows,
        strict=True,
    ):
        if type(raw_row) is not dict:
            raise CMEEVerticalError("plan_bound_observation_guard_result_shape_mismatch")
        guard_id = raw_row.get("guard_name")
        passed = raw_row.get("passed")
        if type(guard_id) is not str or guard_id != expected_guard_id:
            raise CMEEVerticalError("plan_bound_observation_guard_set_mismatch")
        if type(passed) is not bool or passed is not True:
            raise CMEEVerticalError("plan_bound_observation_guard_failed")
        if (
            type(raw_row.get("rejection_reasons")) is not list
            or raw_row.get("rejection_reasons") != []
        ):
            raise CMEEVerticalError("plan_bound_observation_guard_result_mismatch")
        guard_results.append(CommonGuardResultProof(guard_id=guard_id, passed=passed))

    combined = result_meta.get("combined_guard_result")
    combined_meta = combined.get("meta") if type(combined) is dict else None
    combined_guard_rows = (
        combined_meta.get("guard_results") if type(combined_meta) is dict else None
    )
    if (
        type(combined) is not dict
        or combined.get("guard_name") != "combined_text_generation_guards"
        or type(combined.get("passed")) is not bool
        or combined.get("passed") is not True
        or type(combined.get("rejection_reasons")) is not list
        or combined.get("rejection_reasons") != []
        or type(combined_guard_rows) is not list
        or len(combined_guard_rows) != len(EXPECTED_COMMON_GUARD_IDS)
        or any(type(row) is not dict for row in combined_guard_rows)
        or combined_guard_rows != raw_rows
    ):
        raise CMEEVerticalError("plan_bound_observation_combined_guard_mismatch")

    stabilization = core_meta.get("step15_common_core_stabilization")
    if type(stabilization) is not dict:
        raise CMEEVerticalError("plan_bound_observation_stabilization_missing")
    if (
        stabilization.get("report_name") != COMMON_GUARD_STABILIZATION_REPORT_NAME
        or stabilization.get("phase") != COMMON_GUARD_STABILIZATION_PHASE
        or stabilization.get("core_id") != COMMON_GUARD_STABILIZATION_CORE_ID
    ):
        raise CMEEVerticalError("plan_bound_observation_stabilization_identity_mismatch")
    if (
        type(stabilization.get("passed")) is not bool
        or stabilization.get("passed") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_stabilization_failed")
    if (
        type(stabilization.get("common_shapes_ready")) is not bool
        or stabilization.get("common_shapes_ready") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_common_shapes_not_ready")

    raw_guard_names = stabilization.get("guard_names")
    if type(raw_guard_names) is not list or tuple(raw_guard_names) != EXPECTED_COMMON_GUARD_IDS:
        raise CMEEVerticalError("plan_bound_observation_stabilization_guard_set_mismatch")
    raw_issue_codes = stabilization.get("issue_codes")
    if type(raw_issue_codes) is not list or raw_issue_codes:
        raise CMEEVerticalError("plan_bound_observation_stabilization_issues")
    shared_parts = stabilization.get("shared_quality_parts")
    if (
        type(shared_parts) is not dict
        or tuple(shared_parts) != EXPECTED_COMMON_SHAPE_PART_IDS
        or any(type(shared_parts.get(key)) is not bool or shared_parts.get(key) is not True for key in EXPECTED_COMMON_SHAPE_PART_IDS)
    ):
        raise CMEEVerticalError("plan_bound_observation_common_shape_parts_mismatch")

    return _CommonGuardSealMaterial(
        guard_results=tuple(guard_results),
        stabilization_report_name=COMMON_GUARD_STABILIZATION_REPORT_NAME,
        stabilization_phase=COMMON_GUARD_STABILIZATION_PHASE,
        stabilization_core_id=COMMON_GUARD_STABILIZATION_CORE_ID,
        stabilization_passed=True,
        common_shapes_ready=True,
        stabilization_guard_names=EXPECTED_COMMON_GUARD_IDS,
        issue_codes=(),
    )


def _common_guard_proof_id(
    *,
    source_envelope_id: str,
    graph_id: str,
    plan_id: str,
    guarded_observation_units: Sequence[tuple[str, str]],
    guard_results: Sequence[CommonGuardResultProof],
    stabilization_report_name: str,
    stabilization_phase: str,
    stabilization_core_id: str,
    stabilization_passed: bool,
    common_shapes_ready: bool,
    stabilization_guard_names: Sequence[str],
    issue_codes: Sequence[str],
) -> str:
    material = {
        "schema_version": CMEE_COMMON_GUARD_PROOF_VERSION,
        "source_envelope_id": source_envelope_id,
        "graph_id": graph_id,
        "plan_id": plan_id,
        "guarded_observation_units": [list(row) for row in guarded_observation_units],
        "guard_results": [
            {"guard_id": row.guard_id, "passed": row.passed}
            for row in guard_results
        ],
        "stabilization": {
            "report_name": stabilization_report_name,
            "phase": stabilization_phase,
            "core_id": stabilization_core_id,
            "passed": stabilization_passed,
            "common_shapes_ready": common_shapes_ready,
            "guard_names": list(stabilization_guard_names),
            "issue_codes": list(issue_codes),
        },
    }
    canonical = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"common-guard-proof-{hashlib.sha256(canonical).hexdigest()}"


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
        "\x1f".join(
            (
                row.meaning_owner_id,
                row.owner_class.value,
                row.provider_resolution.value,
                row.attachment_admission.value,
                row.visible_authority.value,
                row.route_b_disposition.value,
                "visible_claim_refs",
                *row.visible_claim_refs,
                "evidence_refs",
                *row.evidence_refs,
                "target_unknown_ref",
                row.target_unknown_ref or "",
                "reason_codes",
                *row.reason_codes,
            )
        )
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
        plan.source_envelope_id,
        plan.source_version,
        plan.obligation_version,
        plan.owner_universe_digest,
        plan.source_plan_version,
        plan.observation_duty_id,
        plan.unknown_duty_id,
        plan.reception_duty_id,
        plan.reception_plan_digest,
        *plan.allowed_reception_act_ids,
        *plan.required_observation_owner_ids,
        *plan.reception_target_owner_ids,
        *plan.visible_owner_ids,
        *plan.unresolved_owner_ids,
        *plan.visible_unknown_owner_ids,
        *plan.required_unknown_owner_ids,
        *visible_line_ids,
    )


def _reception_plan_contract(grounded_plan: Any) -> tuple[str, tuple[str, ...]]:
    reception_plan = _cmee_semantic_reception_plan(grounded_plan)
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
    common_guard_proof_id: str,
    observation: str,
    visible_unknowns: Sequence[str],
    reception: str,
) -> str:
    return _stable_id(
        "artifact",
        source_envelope_id,
        graph_id,
        plan_id,
        common_guard_proof_id,
        *REALIZER_CONTRACT_IDS,
        *TRUST_POLICY_IDS,
        _sha256_text(observation),
        *(_sha256_text(row) for row in visible_unknowns),
        _sha256_text(reception),
    )


def _build_common_guard_proof(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    plan: ExperiencePlan,
    safe_lines: Sequence[Any],
    material: _CommonGuardSealMaterial,
) -> CommonGuardProof:
    guarded_observation_units = tuple(
        (line.sentence_id, _sha256_text(line.text))
        for line in safe_lines
        if line.binding.line_role == "cmee_observation"
    )
    if not guarded_observation_units:
        raise CMEEVerticalError("common_guard_proof_observation_missing")
    proof_id = _common_guard_proof_id(
        source_envelope_id=source.envelope.envelope_id,
        graph_id=graph.graph_id,
        plan_id=plan.plan_id,
        guarded_observation_units=guarded_observation_units,
        guard_results=material.guard_results,
        stabilization_report_name=material.stabilization_report_name,
        stabilization_phase=material.stabilization_phase,
        stabilization_core_id=material.stabilization_core_id,
        stabilization_passed=material.stabilization_passed,
        common_shapes_ready=material.common_shapes_ready,
        stabilization_guard_names=material.stabilization_guard_names,
        issue_codes=material.issue_codes,
    )
    return CommonGuardProof(
        schema_version=CMEE_COMMON_GUARD_PROOF_VERSION,
        proof_id=proof_id,
        source_envelope_id=source.envelope.envelope_id,
        graph_id=graph.graph_id,
        plan_id=plan.plan_id,
        guarded_observation_units=guarded_observation_units,
        guard_results=material.guard_results,
        stabilization_report_name=material.stabilization_report_name,
        stabilization_phase=material.stabilization_phase,
        stabilization_core_id=material.stabilization_core_id,
        stabilization_passed=material.stabilization_passed,
        common_shapes_ready=material.common_shapes_ready,
        stabilization_guard_names=material.stabilization_guard_names,
        issue_codes=material.issue_codes,
    )


def _ordered(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _owner_for_source_span(source: AdmittedTextSource, source_span_id: str) -> str:
    try:
        return source.meaning_owner_for_span(source_span_id)
    except Exception:
        raise CMEEVerticalError("source_span_owner_binding_mismatch") from None


def _owner_for_nucleus(source: AdmittedTextSource, nucleus: Any) -> str:
    source_span_ids = _ordered(getattr(nucleus, "source_span_ids", ()))
    if len(source_span_ids) != 1:
        raise CMEEVerticalError("nucleus_owner_binding_not_exact1")
    return _owner_for_source_span(source, source_span_ids[0])


def _owner_for_relation(source: AdmittedTextSource, relation: Any) -> str:
    owners = _ordered(
        _owner_for_source_span(source, source_span_id)
        for source_span_id in getattr(relation, "source_span_ids", ())
    )
    if len(owners) != 1:
        raise CMEEVerticalError("relation_endpoint_binding_not_supported")
    return owners[0]


def _build_graph(
    source: AdmittedTextSource,
    grounded_plan: Any,
    planned_visible_nucleus_ids: Sequence[str],
    planned_visible_relation_ids: Sequence[str],
) -> GroundedMeaningGraph:
    try:
        canonical_universe = build_source_owner_universe(
            source.envelope,
            source.evidence_refs,
        )
    except Exception:
        raise CMEEVerticalError("source_owner_universe_recompute_failed") from None
    if source.owner_universe != canonical_universe:
        raise CMEEVerticalError("source_owner_universe_mismatch")

    visible_nuclei = set(planned_visible_nucleus_ids)
    visible_relations = set(planned_visible_relation_ids)
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}

    nodes: list[MeaningNode] = []
    node_id_by_source: dict[str, str] = {}
    visible_claims_by_owner: dict[str, list[str]] = {}
    for nucleus in grounded_plan.nuclei:
        is_visible = nucleus.nucleus_id in visible_nuclei
        if nucleus.grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING:
            if is_visible:
                raise CMEEVerticalError("provisional_nucleus_visible_authority_forbidden")
            continue
        owner = _owner_for_nucleus(source, nucleus)
        evidence = tuple(
            ref_by_span[span_id].evidence_id
            for span_id in nucleus.source_span_ids
            if span_id in ref_by_span
        )
        if len(evidence) != len(tuple(nucleus.source_span_ids)) or not evidence:
            raise CMEEVerticalError("nucleus_evidence_binding_mismatch")
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
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=evidence,
            )
        )
        if is_visible:
            visible_claims_by_owner.setdefault(owner, []).append(node_id)

    edges: list[MeaningEdge] = []
    for relation in grounded_plan.relations:
        is_visible = relation.relation_id in visible_relations
        if relation.grounding_kind not in ADMISSIBLE_RELATION_GROUNDING:
            if is_visible:
                raise CMEEVerticalError("provisional_relation_visible_authority_forbidden")
            # Route B keeps provisional provider/legacy proposals outside the
            # grounded graph; absence does not create a post-plan owner.
            continue
        owner = _owner_for_relation(source, relation)
        evidence = tuple(
            ref_by_span[span_id].evidence_id
            for span_id in relation.source_span_ids
            if span_id in ref_by_span
        )
        if len(evidence) != len(tuple(relation.source_span_ids)) or not evidence:
            raise CMEEVerticalError("relation_evidence_binding_mismatch")
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
                epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                evidence_ids=evidence,
            )
        )
        if is_visible:
            visible_claims_by_owner.setdefault(owner, []).append(edge_id)

    # Strength is part of the admitted structured source but this slice does
    # not realize it. It remains SOURCE_EXPLICIT but is not misclassified as
    # an unknown merely because it is not selected for the visible plan.
    strength_ref = source.evidence_ref("structured:emotion_strength")
    strength_owner = _owner_for_source_span(source, strength_ref.source_span_id)
    nodes.append(
        MeaningNode(
            node_id=_stable_id("mn", source.envelope.envelope_id, strength_owner),
            owner_id=strength_owner,
            node_kind="STRUCTURED_EMOTION_STRENGTH",
            grounding_kind="source_explicit_not_realized",
            value=source.strength,
            epistemic_state=EpistemicState.SOURCE_EXPLICIT,
            evidence_ids=(strength_ref.evidence_id,),
        )
    )

    dispositions: list[OwnerDisposition] = []
    for obligation in source.owner_universe.obligations:
        owner_id = obligation.meaning_owner_id
        visible_claim_refs = tuple(visible_claims_by_owner.get(owner_id, ()))
        if obligation.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT":
            dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    provider_resolution=ProviderResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.NONE,
                    route_b_disposition=RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
                    visible_claim_refs=(),
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=("ATTACHMENT_UNRESOLVED",),
                )
            )
        elif visible_claim_refs:
            dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    provider_resolution=ProviderResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.SOURCE_EXPLICIT,
                    route_b_disposition=RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
                    visible_claim_refs=visible_claim_refs,
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=(),
                )
            )
        else:
            dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    provider_resolution=ProviderResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.NONE,
                    route_b_disposition=RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
                    visible_claim_refs=(),
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=("ATTACHMENT_UNRESOLVED",),
                )
            )

    owner_refs = tuple(row.meaning_owner_id for row in dispositions)
    expected_owner_refs = (
        source.owner_universe.required_owner_refs
        + source.owner_universe.active_optional_owner_refs
    )
    if owner_refs != expected_owner_refs or len(owner_refs) != len(set(owner_refs)):
        raise CMEEVerticalError("route_b_owner_duplicate")
    owner_digest = source.owner_universe.owner_universe_digest
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
        required_owner_refs=source.owner_universe.required_owner_refs,
        active_optional_owner_refs=source.owner_universe.active_optional_owner_refs,
        source_version=source.owner_universe.source_version,
        obligation_version=source.owner_universe.obligation_version,
        owner_universe_digest=owner_digest,
    )
    if tuple(row.owner_id for row in graph.owner_dispositions) != expected_owner_refs:
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


def _source_plan_binding_version(
    grounded_plan: Any,
    required_nucleus_ids: Sequence[str],
    required_relation_ids: Sequence[str],
    reception_target_ids: Sequence[str],
) -> str:
    """Seal exact private realization obligations into the existing plan field."""

    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    material = {
        "binding_version": "cocolon.cmee.emlis.r4_realization_obligations.v1",
        "source_plan_schema_version": str(grounded_plan.schema_version),
        "source_plan_generation_path": str(grounded_plan.generation_path),
        "required_nucleus_ids": list(required_nucleus_ids),
        "required_relations": [
            {
                "relation_id": relation_id,
                "relation_type": str(relation_index[relation_id].type),
                "from_nucleus_id": str(
                    relation_index[relation_id].from_nucleus_id
                ),
                "to_nucleus_id": str(relation_index[relation_id].to_nucleus_id),
                "evidence_span_ids": list(
                    relation_index[relation_id].source_span_ids
                ),
            }
            for relation_id in required_relation_ids
        ],
        "reception_target_ids": list(reception_target_ids),
    }
    digest = _sha256_text(
        json.dumps(
            material,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return (
        f"{grounded_plan.schema_version}|{grounded_plan.generation_path}|"
        f"cocolon.cmee.emlis.r4_realization_obligations.v1:{digest}"
    )


def _build_experience_plan(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: Any,
    required_nucleus_ids: Sequence[str],
    required_relation_ids: Sequence[str],
    reception_target_ids: Sequence[str],
) -> ExperiencePlan:
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    positive_dispositions = {
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    visible = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition in positive_dispositions
    )
    unresolved = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition not in positive_dispositions
    )
    visible_unknown = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if source.owner_obligation(row.owner_id).obligation_kind
        == "STRUCTURED_CONTEXT_ATTACHMENT"
        and row.disposition
        in {
            RouteBDisposition.UNKNOWN_PRESERVED_LIMITED,
            RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
        }
    )
    unresolved_required = tuple(
        row
        for row in graph.owner_dispositions
        if row.owner_class is OwnerClass.REQUIRED
        and row.disposition not in positive_dispositions
    )
    if any(row.owner_id not in set(visible_unknown) for row in unresolved_required):
        raise CMEEVerticalError("required_unknown_not_safely_visible")
    required_unknown = tuple(
        row.owner_id for row in unresolved_required
    )
    source_plan_version = _source_plan_binding_version(
        grounded_plan,
        required_nucleus_ids,
        required_relation_ids,
        reception_target_ids,
    )
    required_observation_owners = _ordered(
        (
            *(
                _owner_for_nucleus(source, nucleus_index[row_id])
                for row_id in required_nucleus_ids
            ),
            *(
                _owner_for_relation(source, relation_index[row_id])
                for row_id in required_relation_ids
            ),
        )
    )
    reception_target_owners = _ordered(
        _owner_for_nucleus(source, nucleus_index[row_id])
        for row_id in reception_target_ids
    )
    if not set(required_observation_owners + reception_target_owners).issubset(set(visible)):
        raise CMEEVerticalError("experience_plan_visible_owner_mismatch")
    if not visible_unknown:
        raise CMEEVerticalError("limited_visible_unknown_owner_missing")
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
        source_envelope_id=source.envelope.envelope_id,
        source_version=graph.source_version,
        obligation_version=graph.obligation_version,
        owner_universe_digest=graph.owner_universe_digest,
        source_plan_version=source_plan_version,
        observation_duty_id=OBSERVATION_DUTY_ID,
        unknown_duty_id=UNKNOWN_DUTY_ID,
        reception_duty_id=RECEPTION_DUTY_ID,
        reception_plan_digest=reception_plan_digest,
        allowed_reception_act_ids=allowed_reception_act_ids,
        required_observation_owner_ids=required_observation_owners,
        reception_target_owner_ids=reception_target_owners,
        visible_owner_ids=visible,
        unresolved_owner_ids=unresolved,
        visible_unknown_owner_ids=visible_unknown,
        required_unknown_owner_ids=required_unknown,
        visible_line_ids=(),
    )


def _cmee_semantic_reception_plan(grounded_plan: Any) -> Any:
    """Project the existing target into a polarity-strict CMEE reception plan.

    The legacy short-state compatibility policy intentionally collapses every
    one-span target to current burden.  CMEE keeps the source-selected target
    and evidence unchanged, but asks the existing semantic selector to choose
    the act from that target rather than from the short-input compatibility
    bucket.  This is a private adapter projection; it does not mutate or
    reclassify ``GroundedObservationPlan.input_profile``.
    """

    response_plan = grounded_plan.response_plan
    reception_plan = build_grounded_human_reception_plan(
        required=grounded_plan.coverage_requirements.human_follow_required,
        human_follow_target_ids=response_plan.human_follow_target_ids,
        primary_nucleus_ids=response_plan.primary_nucleus_ids,
        supporting_nucleus_ids=response_plan.supporting_nucleus_ids,
        required_nucleus_ids=response_plan.required_nucleus_ids,
        fact_boundary_nucleus_ids=response_plan.fact_boundary_nucleus_ids,
        nuclei=grounded_plan.nuclei,
        relations=grounded_plan.relations,
        safety_kind=grounded_plan.safety_policy.safety_kind,
        material_quality=CMEE_RECEPTION_MATERIAL_MODE,
        semantic_complexity=grounded_plan.input_profile.semantic_complexity,
    )
    if reception_plan is None or not reception_plan.required:
        raise CMEEVerticalError("bound_human_reception_plan_missing")
    expected_targets = tuple(response_plan.human_follow_target_ids)
    if reception_plan.target_nucleus_ids != expected_targets:
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    if reception_plan.support_nucleus_ids:
        raise CMEEVerticalError("bound_human_reception_support_not_supported")

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    if any(row_id not in nucleus_index for row_id in reception_plan.target_nucleus_ids):
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    selected_nucleus_ids = _ordered(
        (*reception_plan.target_nucleus_ids, *reception_plan.support_nucleus_ids)
    )
    expected_evidence_ids = _ordered(
        source_span_id
        for row_id in selected_nucleus_ids
        for source_span_id in nucleus_index[row_id].source_span_ids
    )
    if reception_plan.source_evidence_span_ids != expected_evidence_ids:
        raise CMEEVerticalError("bound_human_reception_source_evidence_mismatch")
    if not reception_plan.moves:
        raise CMEEVerticalError("bound_human_reception_move_missing")
    if any(
        move.target_nucleus_ids != reception_plan.target_nucleus_ids
        or move.source_evidence_span_ids != reception_plan.source_evidence_span_ids
        for move in reception_plan.moves
    ):
        raise CMEEVerticalError("bound_human_reception_move_binding_mismatch")

    target_polarities = {
        str(nucleus_index[row_id].semantic_frame.polarity)
        for row_id in reception_plan.target_nucleus_ids
    }
    act_ids = _ordered(move.reception_act for move in reception_plan.moves)
    if target_polarities == {"positive"} and CMEE_BURDEN_RECEPTION_ACTS.intersection(act_ids):
        raise CMEEVerticalError("bound_human_reception_positive_burden_promotion")
    target_nuclei = tuple(
        nucleus_index[row_id] for row_id in reception_plan.target_nucleus_ids
    )
    for act_id in CMEE_POSITIVE_RECEPTION_ACTS.intersection(act_ids):
        compatible = any(
            (
                act_id == "protect_retained_intention"
                and (
                    nucleus.kind == "wish"
                    or nucleus.semantic_frame.modality in {"wish", "intention"}
                    or "semantic_role:retained_intention"
                    in set(nucleus.semantic_frame.attribute_codes)
                )
            )
            or (
                act_id == "recognize_lived_change"
                and (
                    nucleus.kind in {"change", "value"}
                    or "operator:positive_change"
                    in set(nucleus.semantic_frame.attribute_codes)
                )
            )
            or (
                act_id == "hold_help_seeking"
                and "operator:help_seeking"
                in set(nucleus.semantic_frame.attribute_codes)
            )
            or (
                act_id == "honor_concrete_effort"
                and (
                    nucleus.kind == "action"
                    or "semantic_role:concrete_action_evidence"
                    in set(nucleus.semantic_frame.attribute_codes)
                )
            )
            for nucleus in target_nuclei
        )
        if not compatible:
            raise CMEEVerticalError(
                "bound_human_reception_target_act_semantic_mismatch"
            )
    return reception_plan


def _cmee_source_anchor(nucleus: Any, resolver: Any) -> str:
    source = "".join(
        str(resolver.resolve(source_span_id).raw_text or "")
        for source_span_id in nucleus.source_span_ids
    )
    compact = re.sub(r"\s+", "", source).strip("、。！？!?「」『』")
    compact = re.sub(
        r"^(?:それでも|けれども?|でも|だけど|一方で|ただ|とはいえ|なのに)",
        "",
        compact,
    )
    # Never replay a complete short source clause.  A longer clause contributes
    # only a small source-local anchor; the binding remains authoritative for
    # the complete evidence range.
    if len(compact) <= CMEE_SOURCE_ANCHOR_LIMIT + 2:
        return ""
    return compact[:CMEE_SOURCE_ANCHOR_LIMIT] + "…"


def _cmee_nucleus_surface_label(nucleus: Any) -> str:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if nucleus.kind == "wish":
        return "保ちたい方向"
    if nucleus.kind == "constraint":
        return "前に進む際の制約"
    if nucleus.kind == "change" or "operator:positive_change" in attributes:
        return "前向きな変化"
    if nucleus.kind == "reaction":
        return (
            "負荷を伴う反応"
            if nucleus.semantic_frame.polarity == "negative"
            else "今の反応"
        )
    if nucleus.kind == "state":
        return (
            "負荷を伴う状態"
            if nucleus.semantic_frame.polarity == "negative"
            else "今の状態"
        )
    return {
        "action": "入力内の行動",
        "self_evaluation": "現在の自己評価",
        "value": "大切にしている向き",
        "event": "入力内の出来事",
    }.get(str(nucleus.kind), "現在の意味")


def _cmee_source_reference(
    anchor: str,
    nucleus: Any,
    *,
    include_semantic_label: bool = False,
) -> str:
    semantic_label = _cmee_nucleus_surface_label(nucleus)
    if not anchor:
        return f"{semantic_label}に関する記述"
    reference = f"「{anchor}」という記述"
    return (
        f"{reference}にある{semantic_label}"
        if include_semantic_label
        else reference
    )


def _canonical_r4_observation_lines(
    source: AdmittedTextSource,
    grounded_plan: Any,
    resolver: Any,
) -> tuple[_CMEEVisibleLine, ...]:
    """Build exact plan-bound observation duties without raw clause replay."""

    sentence_plan = build_grounded_sentence_plan(grounded_plan, resolver)
    required_nucleus_ids = tuple(
        grounded_plan.coverage_requirements.required_nucleus_ids
    )
    required_relation_ids = tuple(
        grounded_plan.coverage_requirements.required_relation_ids
    )
    if (
        sentence_plan.status != "generated"
        or sentence_plan.required_nucleus_ids != required_nucleus_ids
        or set(sentence_plan.covered_required_nucleus_ids) != set(required_nucleus_ids)
        or sentence_plan.required_relation_ids != required_relation_ids
        or set(sentence_plan.covered_required_relation_ids) != set(required_relation_ids)
        or sentence_plan.unresolved_evidence_span_ids
    ):
        raise CMEEVerticalError("grounded_sentence_plan_required_coverage_mismatch")

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    oracle_observation_lines = tuple(
        row for row in sentence_plan.lines if row.binding.line_role != "human_follow"
    )
    for relation_id in required_relation_ids:
        relation = relation_index.get(relation_id)
        owning_lines = tuple(
            row
            for row in oracle_observation_lines
            if relation_id in row.binding.relation_ids
        )
        if relation is None or not owning_lines:
            raise CMEEVerticalError("grounded_sentence_plan_relation_missing")
        expected_endpoints = {
            relation.from_nucleus_id,
            relation.to_nucleus_id,
        }
        expected_evidence = set(relation.source_span_ids)
        if any(
            not expected_endpoints.issubset(set(row.binding.nucleus_ids))
            or not expected_evidence.issubset(set(row.binding.evidence_span_ids))
            for row in owning_lines
        ):
            raise CMEEVerticalError("grounded_sentence_plan_relation_binding_mismatch")

    lines: list[_CMEEVisibleLine] = []
    covered_nucleus_ids: set[str] = set()
    for relation_id in required_relation_ids:
        relation = relation_index[relation_id]
        from_nucleus = nucleus_index[relation.from_nucleus_id]
        to_nucleus = nucleus_index[relation.to_nucleus_id]
        from_reference = _cmee_source_reference(
            _cmee_source_anchor(from_nucleus, resolver),
            from_nucleus,
            include_semantic_label=True,
        )
        to_reference = _cmee_source_reference(
            _cmee_source_anchor(to_nucleus, resolver),
            to_nucleus,
            include_semantic_label=True,
        )
        relation_label = CMEE_RELATION_SURFACE_LABELS.get(
            str(relation.type),
            "入力内の関係",
        )
        relation_type = str(relation.type)
        if relation_type in DIRECTIONAL_GROUNDED_RELATION_TYPES:
            text = (
                f"入力では、起点側の{from_reference}から"
                f"到達側の{to_reference}へ、"
                f"{relation_label}がこの順に示されています。"
            )
        elif relation_type == "contrast":
            text = (
                f"一方の{from_reference}ともう一方の{to_reference}は、"
                "入力内で異なる向きとして対比されています。"
            )
        elif relation_type == "wish_and_constraint":
            text = (
                f"願いと制約の組として、第一項に{from_reference}、"
                f"第二項に{to_reference}が示されています。"
            )
        elif relation_type == "coexistence":
            text = (
                f"並存する二項として、片方に{from_reference}、"
                f"別の側に{to_reference}が示されています。"
            )
        else:
            text = (
                f"{relation_label}の二項として、項Aに{from_reference}、"
                f"項Bに{to_reference}が置かれています。"
            )
        lines.append(
            _CMEEVisibleLine(
                sentence_id=f"cmee:observation:{len(lines) + 1}",
                text=text,
                binding=_CMEEVisibleBinding(
                    line_role="cmee_observation",
                    nucleus_ids=(
                        relation.from_nucleus_id,
                        relation.to_nucleus_id,
                    ),
                    relation_ids=(relation_id,),
                    evidence_span_ids=tuple(relation.source_span_ids),
                    claim_scope="cmee_plan_bound_grounded_relation",
                    required=True,
                ),
            )
        )
        covered_nucleus_ids.update(
            (relation.from_nucleus_id, relation.to_nucleus_id)
        )

    for nucleus_id in required_nucleus_ids:
        if nucleus_id in covered_nucleus_ids:
            continue
        nucleus = nucleus_index[nucleus_id]
        reference = _cmee_source_reference(
            _cmee_source_anchor(nucleus, resolver),
            nucleus,
        )
        lines.append(
            _CMEEVisibleLine(
                sentence_id=f"cmee:observation:{len(lines) + 1}",
                text=(
                    f"入力の{reference}には、"
                    f"{_cmee_nucleus_surface_label(nucleus)}が示されています。"
                ),
                binding=_CMEEVisibleBinding(
                    line_role="cmee_observation",
                    nucleus_ids=(nucleus_id,),
                    relation_ids=(),
                    evidence_span_ids=tuple(nucleus.source_span_ids),
                    claim_scope="cmee_plan_bound_grounded_nucleus",
                    required=True,
                ),
            )
        )

    observed_nuclei = {
        nucleus_id for line in lines for nucleus_id in line.binding.nucleus_ids
    }
    observed_relations = {
        relation_id for line in lines for relation_id in line.binding.relation_ids
    }
    if observed_nuclei != set(required_nucleus_ids):
        raise CMEEVerticalError("post_realization_required_nucleus_mismatch")
    if observed_relations != set(required_relation_ids):
        raise CMEEVerticalError("post_realization_required_relation_mismatch")
    if not lines:
        raise CMEEVerticalError("experience_plan_projection_empty")
    return tuple(lines)


def _canonical_r4_tail_lines(
    source: AdmittedTextSource,
    plan: ExperiencePlan,
    grounded_plan: Any,
    resolver: Any,
) -> tuple[_CMEEVisibleLine, _CMEEVisibleLine]:
    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    reception_plan = _cmee_semantic_reception_plan(grounded_plan)
    reception_surface = realize_grounded_human_reception(
        reception_plan,
        nucleus_index,
        resolver,
    )
    if validate_grounded_human_reception_surface(
        reception_surface,
        reception_plan,
        resolver,
    ):
        raise CMEEVerticalError("bound_human_reception_surface_rejected")
    expected_reception_digest, expected_reception_acts = (
        _reception_plan_contract(grounded_plan)
    )
    if (
        plan.reception_plan_digest != expected_reception_digest
        or plan.allowed_reception_act_ids != expected_reception_acts
        or tuple(reception_surface.realized_reception_acts)
        != expected_reception_acts
    ):
        raise CMEEVerticalError("bound_human_reception_act_contract_mismatch")
    reception_owner_set = set(plan.reception_target_owner_ids)
    reception_targets = tuple(
        row_id
        for row_id in grounded_plan.response_plan.human_follow_target_ids
        if row_id in nucleus_index
        and _owner_for_nucleus(source, nucleus_index[row_id])
        in reception_owner_set
    )
    if tuple(reception_surface.grounded_nucleus_ids) != reception_targets:
        raise CMEEVerticalError("bound_human_reception_target_mismatch")
    reception_line = _CMEEVisibleLine(
        sentence_id="cmee:reception:1",
        text=reception_surface.text,
        binding=_CMEEVisibleBinding(
            line_role="human_follow",
            nucleus_ids=reception_targets,
            relation_ids=(),
            evidence_span_ids=tuple(
                reception_surface.grounded_evidence_span_ids
            ),
            claim_scope="cmee_grounded_human_reception",
            required=True,
        ),
    )

    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    unknown_span_ids = _ordered(
        source_span_id
        for owner_id in plan.visible_unknown_owner_ids
        for source_span_id in source.owner_obligation(owner_id).source_span_ids
    )
    if not plan.visible_unknown_owner_ids or not unknown_span_ids:
        raise CMEEVerticalError("visible_unknown_evidence_unavailable")
    if any(source_span_id not in ref_by_span for source_span_id in unknown_span_ids):
        raise CMEEVerticalError("visible_unknown_cross_source_evidence")
    unknown_line = _CMEEVisibleLine(
        sentence_id="cmee:unknown:1",
        text=STRUCTURED_ATTACHMENT_UNKNOWN_TEXT,
        binding=_CMEEVisibleBinding(
            line_role="cmee_unknown",
            nucleus_ids=(),
            relation_ids=(),
            evidence_span_ids=unknown_span_ids,
            constrained_owner_ids=plan.visible_unknown_owner_ids,
            claim_scope="cmee_evidence_bound_unknown_preservation",
            required=True,
        ),
    )
    return unknown_line, reception_line


def _cmee_core_phrase_unit_id(source_span_id: str) -> str:
    return f"cmee-phrase:{source_span_id}"


def _cmee_core_relation_type(line: _CMEEVisibleLine, grounded_plan: Any) -> str:
    if not line.binding.relation_ids:
        return "source_explicit_nucleus"
    if len(line.binding.relation_ids) != 1:
        raise CMEEVerticalError("plan_bound_relation_binding_not_exact1")
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    relation = relation_index.get(line.binding.relation_ids[0])
    if relation is None:
        raise CMEEVerticalError("plan_bound_relation_binding_unknown")
    return str(relation.type)


def _cmee_composer_binding_row(
    line: _CMEEVisibleLine,
    grounded_plan: Any,
) -> dict[str, Any]:
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    relation_bindings = [
        {
            "relation_id": relation_id,
            "relation_type": str(relation_index[relation_id].type),
            "from_nucleus_id": str(relation_index[relation_id].from_nucleus_id),
            "to_nucleus_id": str(relation_index[relation_id].to_nucleus_id),
            "evidence_span_ids": list(relation_index[relation_id].source_span_ids),
        }
        for relation_id in line.binding.relation_ids
    ]
    binding_material = {
        "nucleus_ids": list(line.binding.nucleus_ids),
        "relation_bindings": relation_bindings,
        "evidence_span_ids": list(line.binding.evidence_span_ids),
    }
    return {
        "version": "cocolon.cmee.emlis.r4_sentence_binding.v1",
        "binding_version": "cocolon.cmee.emlis.r4_sentence_binding.v1",
        "sentence_id": line.sentence_id,
        "text": line.text,
        "used_evidence_span_ids": list(line.binding.evidence_span_ids),
        "used_phrase_unit_ids": [
            _cmee_core_phrase_unit_id(source_span_id)
            for source_span_id in line.binding.evidence_span_ids
        ],
        "relation_type": _cmee_core_relation_type(line, grounded_plan),
        "line_role": "cmee_observation",
        "coverage_scope": "cmee_required_plan",
        "must_include": True,
        "raw_input_included": False,
        "meta": {
            "cmee_nucleus_ids": list(line.binding.nucleus_ids),
            "cmee_relation_ids": list(line.binding.relation_ids),
            "cmee_relation_bindings": relation_bindings,
            "cmee_binding_digest": _sha256_text(
                json.dumps(
                    binding_material,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            ),
            "raw_input_included": False,
        },
    }


def _json_exact_identity(actual: Any, expected: Any) -> bool:
    """Compare JSON-shaped contract values without Python bool/int coercion."""

    try:
        return json.dumps(
            actual,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) == json.dumps(
            expected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        return False


def _cmee_core_binding_projection(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "version": "emlis.sentence_binding.v1",
        "binding_version": "emlis.sentence_binding.v1",
        "sentence_id": binding["sentence_id"],
        "line_role": binding["line_role"],
        "relation_type": binding["relation_type"],
        "used_evidence_span_ids": list(binding["used_evidence_span_ids"]),
        "used_phrase_unit_ids": list(binding["used_phrase_unit_ids"]),
        "coverage_scope": binding["coverage_scope"],
        "must_include": binding["must_include"],
        "raw_input_included": binding["raw_input_included"],
        "meta": {
            "source_adapter": "emlis_observation_composer_adapter.v1",
            "source_kind": "emlis_sentence_binding",
        },
    }


def _cmee_binding_aliases(meta: Mapping[str, Any]) -> tuple[Any, ...]:
    aliases: list[Any] = []
    for bundle_key in ("sentence_binding_bundle", "binding_bundle", "binding"):
        bundle = meta.get(bundle_key)
        if type(bundle) is not dict:
            return ()
        aliases.extend(
            bundle.get(alias_key)
            for alias_key in ("bindings", "sentence_bindings", "items")
        )
    diagnostic = meta.get("composer_diagnostic")
    diagnostic_bundle = (
        diagnostic.get("sentence_binding_bundle")
        if type(diagnostic) is dict
        else None
    )
    if type(diagnostic_bundle) is not dict:
        return ()
    aliases.extend(
        diagnostic_bundle.get(alias_key)
        for alias_key in ("bindings", "sentence_bindings", "items")
    )
    aliases.append(diagnostic.get("sentence_bindings"))
    return tuple(aliases)


class _CMEER4PlanBoundComposerClient:
    """One-shot adapter from canonical CMEE duties to the unchanged common core."""

    def __init__(
        self,
        observation_lines: Sequence[_CMEEVisibleLine],
        grounded_plan: Any,
    ) -> None:
        self._observation_lines = tuple(observation_lines)
        self._grounded_plan = grounded_plan

    def generate(self, payload: Any) -> dict[str, Any]:
        if type(payload) is not dict:
            return {
                "composer_source": "unavailable",
                "status": "unavailable",
                "rejection_reasons": ["cmee_plan_bound_payload_invalid"],
            }
        evidence_items = payload.get("evidence_spans")
        if type(evidence_items) is not list or any(
            type(row) is not dict for row in evidence_items
        ):
            return {
                "composer_source": "unavailable",
                "status": "unavailable",
                "rejection_reasons": ["cmee_plan_bound_evidence_invalid"],
            }
        evidence_by_id = {
            str(row.get("span_id") or ""): row for row in evidence_items
        }
        used_evidence_ids = _ordered(
            source_span_id
            for line in self._observation_lines
            for source_span_id in line.binding.evidence_span_ids
        )
        if not used_evidence_ids or any(
            source_span_id not in evidence_by_id
            for source_span_id in used_evidence_ids
        ):
            return {
                "composer_source": "unavailable",
                "status": "unavailable",
                "rejection_reasons": ["cmee_plan_bound_evidence_missing"],
            }

        phrase_units = tuple(
            _CMEECorePhraseUnit(
                phrase_unit_id=_cmee_core_phrase_unit_id(source_span_id),
                evidence_span_id=source_span_id,
                raw_text=str(evidence_by_id[source_span_id].get("raw_text") or ""),
                compressed_text=str(
                    evidence_by_id[source_span_id].get("raw_text") or ""
                ),
            )
            for source_span_id in used_evidence_ids
        )
        binding_rows = [
            _cmee_composer_binding_row(line, self._grounded_plan)
            for line in self._observation_lines
        ]
        sentence_plans = tuple(
            _CMEECoreSentencePlan(
                sentence_plan_id=f"cmee-plan:{index}",
                line_role="cmee_observation",
                phrase_unit_ids=tuple(row["used_phrase_unit_ids"]),
                relation_type=str(row["relation_type"]),
            )
            for index, row in enumerate(binding_rows, start=1)
        )
        binding_bundle = {
            "bindings": binding_rows,
            "sentence_bindings": binding_rows,
            "items": binding_rows,
            "raw_text_included": False,
            "raw_input_required_for_debug": False,
        }
        composer_meta = {
            "cmee_plan_bound_grounded_surface": {
                "version": "cocolon.cmee.emlis.plan_bound_grounded_surface.v1",
                "observation_line_count": len(binding_rows),
                "raw_text_included": False,
                "raw_input_required_for_debug": False,
            },
            "required_roles": [],
            "covered_roles": [],
            "sentence_binding_bundle": binding_bundle,
            "binding_bundle": binding_bundle,
            "binding": binding_bundle,
            "sentence_bindings": binding_rows,
            "composer_diagnostic": {
                "sentence_binding_bundle": binding_bundle,
                "sentence_bindings": binding_rows,
                "raw_text_included": False,
                "raw_input_required_for_debug": False,
            },
        }
        scope = payload.get("limited_observation_scope")
        scope = scope if type(scope) is dict else {}
        response = {
            "schema_version": "emlis.composer.response.v1",
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "status": "generated",
            "composer_model": "cocolon.cmee.emlis.plan_bound_grounded_surface.v1",
            "generation_method": "cmee_plan_bound_grounded_surface",
            "generation_scope": "current_input_only",
            "fixed_string_renderer_used": False,
            "coverage_scope": "cmee_required_plan",
            "comment_text": "\n".join(
                line.text for line in self._observation_lines
            ),
            "used_evidence_span_ids": list(used_evidence_ids),
            "used_claim_ids": list(scope.get("included_claim_ids") or []),
            "used_relation_ids": list(scope.get("included_relation_ids") or []),
            "confidence": 1.0,
            "used_phrase_unit_ids": [
                row.phrase_unit_id for row in phrase_units
            ],
            "sentence_binding_bundle": binding_bundle,
            "composer_meta": composer_meta,
        }
        evaluation = evaluate_emlis_observation_candidate(
            composer_payload=payload,
            evidence_items=evidence_items,
            phrase_units=phrase_units,
            sentence_plans=sentence_plans,
            comment_text=str(response["comment_text"]),
            used_evidence_span_ids=tuple(used_evidence_ids),
            used_phrase_unit_ids=tuple(response["used_phrase_unit_ids"]),
            coverage_scope="cmee_required_plan",
            composer_model=str(response["composer_model"]),
            composer_meta=composer_meta,
            response=response,
        )
        if evaluation.passed:
            return attach_core_evaluation_meta(response, evaluation)
        core_meta = evaluation.as_meta()
        return {
            "composer_source": "unavailable",
            "status": "unavailable",
            "rejection_reasons": [core_rejection_reason(evaluation)],
            "composer_meta": {
                "text_generation_core": core_meta,
                "core_text_generation": core_meta,
            },
        }


def _experience_plan_projection(
    source: AdmittedTextSource,
    plan: ExperiencePlan,
    grounded_plan: Any,
) -> LimitedObservationScope:
    """Project exact CMEE duties into the unchanged common-core input port.

    Meaning-owner IDs remain disposition authority only.  Request-local
    nucleus and relation identities own claims/endpoints so two source meanings
    under one owner can never collapse into one graph claim.
    """

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    span_text = {
        str(getattr(row, "span_id", "") or ""): str(getattr(row, "raw_text", "") or "")
        for row in source.evidence_spans
    }
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    required_owner_set = set(plan.required_observation_owner_ids)
    required_nucleus_ids = tuple(
        row_id
        for row_id in grounded_plan.coverage_requirements.required_nucleus_ids
        if _owner_for_nucleus(source, nucleus_index[row_id]) in required_owner_set
    )
    required_relation_ids = tuple(
        row_id
        for row_id in grounded_plan.coverage_requirements.required_relation_ids
        if _owner_for_relation(source, relation_index[row_id]) in required_owner_set
    )
    claims: list[GraphClaim] = []
    claim_id_by_nucleus: dict[str, str] = {}
    for row_id in required_nucleus_ids:
        row = nucleus_index[row_id]
        evidence_ids = list(row.source_span_ids)
        text = " / ".join(span_text[span_id] for span_id in evidence_ids if span_id in span_text).strip()
        if not text or row.grounding_kind not in ADMISSIBLE_NUCLEUS_GROUNDING:
            raise CMEEVerticalError("experience_plan_projection_nucleus_invalid")
        claim_id = _stable_id("gc", source.envelope.envelope_id, row_id)
        claim_id_by_nucleus[row_id] = claim_id
        claims.append(
            GraphClaim(
                claim_id=claim_id,
                claim_type=str(row.kind),
                text=text,
                evidence_span_ids=evidence_ids,
                confidence=1.0,
            )
        )
    if not claims:
        raise CMEEVerticalError("experience_plan_projection_empty")

    relations: list[RelationEdge] = []
    for row_id in required_relation_ids:
        row = relation_index[row_id]
        if (
            row.grounding_kind not in ADMISSIBLE_RELATION_GROUNDING
            or row.from_nucleus_id not in claim_id_by_nucleus
            or row.to_nucleus_id not in claim_id_by_nucleus
        ):
            raise CMEEVerticalError(
                "experience_plan_projection_relation_endpoint_missing"
            )
        relations.append(
            RelationEdge(
                edge_id=_stable_id("gr", source.envelope.envelope_id, row_id),
                from_claim_id=claim_id_by_nucleus[row.from_nucleus_id],
                to_claim_id=claim_id_by_nucleus[row.to_nucleus_id],
                relation_type=str(row.type),
                evidence_span_ids=list(row.source_span_ids),
                confidence=1.0,
            )
        )
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
        addressee_notes=AddresseeNotes(
            sentence_target=max(1, min(4, len(claims) + len(relations)))
        ),
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
        min_reply_sentence_count=1,
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
) -> tuple[tuple[_CMEEVisibleLine, ...], _CommonGuardSealMaterial]:
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    canonical_observation_lines = _canonical_r4_observation_lines(
        source,
        grounded_plan,
        resolver,
    )
    expected_binding_rows = [
        _cmee_composer_binding_row(line, grounded_plan)
        for line in canonical_observation_lines
    ]
    expected_core_binding_rows = [
        _cmee_core_binding_projection(row) for row in expected_binding_rows
    ]
    scope = _experience_plan_projection(source, plan, grounded_plan)
    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=source.evidence_spans,
        composer_client=_CMEER4PlanBoundComposerClient(
            canonical_observation_lines,
            grounded_plan,
        ),
        trace_id=_stable_id("composer", source.envelope.envelope_id, plan.plan_id),
        limited_observation_scope=scope,
    )
    if candidate.status != "generated" or candidate.composer_source != "ai_generated":
        raise CMEEVerticalError("plan_bound_observation_realizer_unavailable")
    composer_meta = candidate.composer_meta if isinstance(candidate.composer_meta, dict) else {}
    core_meta = composer_meta.get("core_text_generation")
    if (
        not isinstance(core_meta, dict)
        or core_meta.get("core_id") != "emlis"
        or core_meta.get("status") != "generated"
        or type(core_meta.get("passed")) is not bool
        or core_meta.get("passed") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_common_core_rejected")
    binding_reflection = core_meta.get("step7_gate_binding_reflection")
    if (
        type(binding_reflection) is not dict
        or type(binding_reflection.get("binding_used")) is not bool
        or binding_reflection.get("binding_used") is not True
    ):
        raise CMEEVerticalError("plan_bound_observation_common_core_binding_unused")
    common_guard_material = _extract_common_guard_seal(core_meta)
    core_bindings = core_meta.get("sentence_bindings")
    raw_bindings = composer_meta.get("sentence_bindings")
    result = core_meta.get("result")
    result_meta = result.get("meta") if type(result) is dict else None
    guarded_candidate = (
        result_meta.get("candidate") if type(result_meta) is dict else None
    )
    guarded_candidate_meta = (
        guarded_candidate.get("meta") if type(guarded_candidate) is dict else None
    )
    guarded_bindings = (
        guarded_candidate_meta.get("sentence_bindings")
        if type(guarded_candidate_meta) is dict
        else None
    )
    if type(raw_bindings) is not list or not raw_bindings:
        raise CMEEVerticalError("plan_bound_observation_binding_missing")
    if type(core_bindings) is not list or len(core_bindings) != len(raw_bindings):
        raise CMEEVerticalError("plan_bound_observation_core_binding_mismatch")
    if type(guarded_bindings) is not list or len(guarded_bindings) != len(raw_bindings):
        raise CMEEVerticalError("plan_bound_observation_guarded_binding_mismatch")
    if not _json_exact_identity(raw_bindings, expected_binding_rows):
        raise CMEEVerticalError("plan_bound_observation_exact_binding_mismatch")
    if not _json_exact_identity(guarded_bindings, expected_binding_rows):
        raise CMEEVerticalError("plan_bound_observation_guarded_exact_binding_mismatch")
    if not _json_exact_identity(core_bindings, expected_core_binding_rows):
        raise CMEEVerticalError("plan_bound_observation_core_exact_binding_mismatch")

    outer_binding_aliases = _cmee_binding_aliases(composer_meta)
    guarded_binding_aliases = _cmee_binding_aliases(guarded_candidate_meta)
    if any(
        type(alias) is not list
        or not _json_exact_identity(alias, expected_binding_rows)
        for alias in (*outer_binding_aliases, *guarded_binding_aliases)
    ) or len(outer_binding_aliases) != 13 or len(guarded_binding_aliases) != 13:
        raise CMEEVerticalError("plan_bound_observation_binding_alias_mismatch")
    if any(
        type(alias) is not list
        or len(alias) != len(expected_binding_rows)
        for alias in (*outer_binding_aliases, *guarded_binding_aliases)
    ):
        raise CMEEVerticalError("plan_bound_observation_binding_alias_shape_mismatch")

    guard_rows = result_meta.get("guard_results") if type(result_meta) is dict else None
    grounding_row = (
        guard_rows[3]
        if type(guard_rows) is list and len(guard_rows) == len(EXPECTED_COMMON_GUARD_IDS)
        else None
    )
    grounding_meta = grounding_row.get("meta") if type(grounding_row) is dict else None
    sentence_claims = (
        grounding_meta.get("sentence_claims")
        if type(grounding_meta) is dict
        else None
    )
    if type(sentence_claims) is not list or len(sentence_claims) != len(raw_bindings):
        raise CMEEVerticalError("plan_bound_observation_guarded_claim_mismatch")

    guarded_claim_sentences: list[str] = []
    for core_binding, surface_binding, guarded_binding, claim in zip(
        core_bindings,
        raw_bindings,
        guarded_bindings,
        sentence_claims,
        strict=True,
    ):
        if (
            type(core_binding) is not dict
            or type(surface_binding) is not dict
            or type(guarded_binding) is not dict
            or type(claim) is not dict
        ):
            raise CMEEVerticalError("plan_bound_observation_binding_invalid")
        for key, expected_type in (
            ("sentence_id", str),
            ("used_evidence_span_ids", list),
            ("used_phrase_unit_ids", list),
            ("relation_type", str),
            ("line_role", str),
        ):
            core_value = core_binding.get(key)
            surface_value = surface_binding.get(key)
            guarded_value = guarded_binding.get(key)
            if (
                type(core_value) is not expected_type
                or type(surface_value) is not expected_type
                or type(guarded_value) is not expected_type
                or not core_value
                or core_value != surface_value
                or core_value != guarded_value
                or (
                    expected_type is list
                    and (
                        any(type(value) is not str or not value for value in core_value)
                        or len(core_value) != len(set(core_value))
                    )
                )
            ):
                raise CMEEVerticalError("plan_bound_observation_core_binding_mismatch")
        surface_text = surface_binding.get("text")
        guarded_text = guarded_binding.get("text")
        canonical_sentences = split_sentences(surface_text, skip_greeting=False)
        if (
            type(surface_text) is not str
            or type(guarded_text) is not str
            or not surface_text
            or surface_text != surface_text.strip()
            or surface_text != guarded_text
        ):
            raise CMEEVerticalError("plan_bound_observation_guarded_binding_mismatch")
        if (
            len(canonical_sentences) != 1
            or type(claim.get("sentence")) is not str
            or claim.get("sentence") != canonical_sentences[0]
            or type(claim.get("binding_present")) is not bool
            or claim.get("binding_present") is not True
            or type(claim.get("binding_used")) is not bool
            or claim.get("binding_used") is not True
            or type(claim.get("binding_sentence_id")) is not str
            or claim.get("binding_sentence_id") != surface_binding["sentence_id"]
            or type(claim.get("binding_evidence_span_ids")) is not list
            or claim.get("binding_evidence_span_ids")
            != surface_binding["used_evidence_span_ids"]
            or type(claim.get("binding_phrase_unit_ids")) is not list
            or claim.get("binding_phrase_unit_ids")
            != surface_binding["used_phrase_unit_ids"]
            or type(claim.get("binding_relation_type")) is not str
            or claim.get("binding_relation_type") != surface_binding["relation_type"]
            or type(claim.get("declared_evidence_span_ids")) is not list
            or claim.get("declared_evidence_span_ids")
            != surface_binding["used_evidence_span_ids"]
            or type(claim.get("declared_phrase_unit_ids")) is not list
            or claim.get("declared_phrase_unit_ids")
            != surface_binding["used_phrase_unit_ids"]
            or type(claim.get("evidence_span_ids")) is not list
            or any(
                type(value) is not str or not value
                for value in claim.get("evidence_span_ids")
            )
            or len(claim.get("evidence_span_ids"))
            != len(set(claim.get("evidence_span_ids")))
            or set(surface_binding["used_evidence_span_ids"])
            != set(claim.get("evidence_span_ids"))
        ):
            raise CMEEVerticalError("plan_bound_observation_guarded_claim_mismatch")
        guarded_claim_sentences.append(claim["sentence"])

    if type(candidate.comment_text) is not str or not candidate.comment_text:
        raise CMEEVerticalError("plan_bound_observation_guarded_surface_mismatch")
    guarded_surface_sentences = split_sentences(candidate.comment_text)
    guarded_claim_sentence_tuple = tuple(guarded_claim_sentences)
    if guarded_surface_sentences != guarded_claim_sentence_tuple:
        completion = composer_meta.get(
            "environment_state_output_scope_marker_completion"
        )
        marker = completion.get("scope_marker") if type(completion) is dict else None
        expected_scoped_sentences = (
            f"{marker}、{guarded_claim_sentence_tuple[0]}",
            *guarded_claim_sentence_tuple[1:],
        )
        if (
            type(completion) is not dict
            or type(completion.get("applied")) is not bool
            or completion.get("applied") is not True
            or type(marker) is not str
            or not marker
            or type(completion.get("target_line_index")) is not int
            or guarded_surface_sentences != expected_scoped_sentences
        ):
            raise CMEEVerticalError("plan_bound_observation_guarded_surface_mismatch")

    nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
    relation_index = {row.relation_id: row for row in grounded_plan.relations}
    required_owner_set = set(plan.required_observation_owner_ids)
    required_nucleus_ids = tuple(
        grounded_plan.coverage_requirements.required_nucleus_ids
    )
    required_relation_ids = tuple(
        grounded_plan.coverage_requirements.required_relation_ids
    )
    if any(
        _owner_for_nucleus(source, nucleus_index[row_id])
        not in required_owner_set
        for row_id in required_nucleus_ids
    ) or any(
        _owner_for_relation(source, relation_index[row_id])
        not in required_owner_set
        for row_id in required_relation_ids
    ):
        raise CMEEVerticalError("plan_bound_observation_owner_missing")
    if candidate.comment_text != "\n".join(
        line.text for line in canonical_observation_lines
    ):
        raise CMEEVerticalError("plan_bound_observation_exact_surface_mismatch")
    observation_lines = list(canonical_observation_lines)

    unknown_line, reception_line = _canonical_r4_tail_lines(
        source,
        plan,
        grounded_plan,
        resolver,
    )
    reception_targets = reception_line.binding.nucleus_ids
    lines = (*observation_lines, unknown_line, reception_line)
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
    return tuple(lines), common_guard_material


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
        if line.binding.line_role == "cmee_observation"
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
    artifact_common_guard_proof_ref: str,
) -> tuple[VisibleUnitTrace, ...]:
    node_ids = {row.node_id for row in graph.nodes}
    edge_ids = {row.edge_id for row in graph.edges}
    ref_by_span = {row.source_span_id: row for row in source.evidence_refs}
    traces: list[VisibleUnitTrace] = []
    for ordinal, line in enumerate(safe_lines, start=1):
        is_reception = line.binding.line_role == "human_follow"
        is_unknown = line.binding.line_role == "cmee_unknown"
        bound_node_ids = tuple(
            _stable_id("mn", source.envelope.envelope_id, source_id)
            for source_id in line.binding.nucleus_ids
        )
        bound_edge_ids = tuple(
            _stable_id("me", source.envelope.envelope_id, source_id)
            for source_id in line.binding.relation_ids
        )
        if not set(bound_node_ids).issubset(node_ids) or not set(bound_edge_ids).issubset(edge_ids):
            raise CMEEVerticalError("visible_trace_claim_binding_missing")
        evidence_ids = tuple(ref_by_span[source_id].evidence_id for source_id in line.binding.evidence_span_ids)
        role = "UNKNOWN" if is_unknown else ("RECEPTION" if is_reception else "OBSERVATION")
        operation = (
            "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
            if is_unknown
            else (
                "BOUND_HUMAN_RECEPTION"
                if is_reception
                else "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
            )
        )
        duty_id = (
            plan.unknown_duty_id
            if is_unknown
            else (plan.reception_duty_id if is_reception else plan.observation_duty_id)
        )
        constrained_owner_ids = (
            line.binding.constrained_owner_ids
            if is_unknown
            else (plan.unresolved_owner_ids if is_reception else ())
        )
        traces.append(
            VisibleUnitTrace(
                visible_unit_id=f"visible:{ordinal}",
                source_sentence_id=line.sentence_id,
                source_envelope_id=source.envelope.envelope_id,
                source_version=graph.source_version,
                obligation_version=graph.obligation_version,
                owner_universe_digest=graph.owner_universe_digest,
                artifact_common_guard_proof_ref=artifact_common_guard_proof_ref,
                role=role,
                operation=operation,
                text_sha256=_sha256_text(line.text),
                duty_id=duty_id,
                meaning_node_ids=() if is_unknown else bound_node_ids,
                meaning_edge_ids=() if is_unknown else bound_edge_ids,
                evidence_ids=evidence_ids,
                constrained_by_owner_ids=constrained_owner_ids,
            )
        )
    return tuple(traces)


def _validate_route_b_graph_contract(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
) -> None:
    try:
        universe = build_source_owner_universe(source.envelope, source.evidence_refs)
    except Exception:
        raise CMEEVerticalError("source_owner_universe_recompute_failed") from None
    if source.owner_universe != universe:
        raise CMEEVerticalError("source_owner_universe_mismatch")

    required = universe.required_owner_refs
    active = universe.active_optional_owner_refs
    credit = universe.credit_only_owner_refs
    if (
        len(required) != len(set(required))
        or len(active) != len(set(active))
        or len(credit) != len(set(credit))
        or set(required).intersection(active)
        or set(required).intersection(credit)
        or set(active).intersection(credit)
    ):
        raise CMEEVerticalError("route_b_owner_partition_invalid")
    expected_owners = required + active
    rows = graph.owner_dispositions
    actual_owners = tuple(row.meaning_owner_id for row in rows)
    if actual_owners != expected_owners or len(actual_owners) != len(set(actual_owners)):
        raise CMEEVerticalError("route_b_owner_denominator_mismatch")
    if (
        graph.source_envelope_id != universe.source_envelope_id
        or graph.required_owner_refs != required
        or graph.active_optional_owner_refs != active
        or graph.source_version != universe.source_version
        or graph.obligation_version != universe.obligation_version
        or graph.owner_universe_digest != universe.owner_universe_digest
    ):
        raise CMEEVerticalError("route_b_owner_universe_binding_mismatch")

    obligation_by_owner = {
        row.meaning_owner_id: row for row in universe.obligations
    }
    evidence_by_id = {row.evidence_id: row for row in source.evidence_refs}
    claim_by_id: dict[str, MeaningNode | MeaningEdge] = {
        **{row.node_id: row for row in graph.nodes},
        **{row.edge_id: row for row in graph.edges},
    }
    positive = {
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for row in rows:
        obligation = obligation_by_owner.get(row.meaning_owner_id)
        if obligation is None or row.owner_class is not obligation.owner_class:
            raise CMEEVerticalError("route_b_owner_class_mismatch")
        if row.evidence_refs != obligation.evidence_refs or not row.evidence_refs:
            raise CMEEVerticalError("route_b_owner_evidence_mismatch")
        if any(reason_code not in ROUTE_B_REASON_CODES for reason_code in row.reason_codes):
            raise CMEEVerticalError("route_b_reason_code_invalid")
        if any(
            evidence_id not in evidence_by_id
            or evidence_by_id[evidence_id].source_envelope_id
            != source.envelope.envelope_id
            for evidence_id in row.evidence_refs
        ):
            raise CMEEVerticalError("route_b_owner_cross_source_evidence")
        if (
            row.provider_resolution is ProviderResolution.MISSING_OR_INVALID
            and row.attachment_admission is not AttachmentAdmission.UNAVAILABLE
        ):
            raise CMEEVerticalError("route_b_provider_admission_mismatch")

        if row.route_b_disposition in positive:
            expected_authority = (
                VisibleAuthority.SOURCE_EXPLICIT
                if row.route_b_disposition
                is RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                else VisibleAuthority.SUPPLEMENTAL_USER
            )
            if (
                row.visible_authority is not expected_authority
                or not row.visible_claim_refs
                or row.target_unknown_ref is not None
                or row.reason_codes
            ):
                raise CMEEVerticalError("route_b_positive_visible_field_mismatch")
            for claim_ref in row.visible_claim_refs:
                claim = claim_by_id.get(claim_ref)
                if (
                    claim is None
                    or claim.owner_id != row.meaning_owner_id
                    or claim.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or not set(claim.evidence_ids).issubset(set(row.evidence_refs))
                ):
                    raise CMEEVerticalError("route_b_positive_visible_claim_mismatch")
        elif row.route_b_disposition is RouteBDisposition.UNKNOWN_PRESERVED_LIMITED:
            target = claim_by_id.get(row.target_unknown_ref or "")
            if (
                row.provider_resolution is not ProviderResolution.UNRESOLVED
                or row.attachment_admission is not AttachmentAdmission.UNRESOLVED
                or row.visible_authority is not VisibleAuthority.NONE
                or row.target_unknown_ref is None
                or row.visible_claim_refs != (row.target_unknown_ref,)
                or not isinstance(target, MeaningNode)
                or target.owner_id != row.meaning_owner_id
                or target.epistemic_state is not EpistemicState.UNKNOWN
                or target.evidence_ids != row.evidence_refs
                or obligation.obligation_kind != "STRUCTURED_CONTEXT_ATTACHMENT"
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                raise CMEEVerticalError("route_b_visible_unknown_field_mismatch")
        elif row.route_b_disposition is RouteBDisposition.NOT_VISIBLE_UNRESOLVED:
            if (
                row.provider_resolution is not ProviderResolution.MISSING_OR_INVALID
                or row.attachment_admission is not AttachmentAdmission.UNAVAILABLE
                or row.visible_authority is not VisibleAuthority.NONE
                or row.visible_claim_refs
                or row.target_unknown_ref is not None
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                raise CMEEVerticalError("route_b_nonvisible_field_mismatch")
        else:
            raise CMEEVerticalError("route_b_disposition_unsupported_in_limited")

    expected_owner_set = set(expected_owners)
    if any(row.owner_id not in expected_owner_set for row in (*graph.nodes, *graph.edges)):
        raise CMEEVerticalError("grounded_graph_owner_outside_universe")


def _validate_common_guard_proof(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    artifact: GenerationArtifactBundle,
    safe_lines: Sequence[Any],
) -> None:
    """Independently verify the sealed one-shot guard proof and its bindings."""

    proof = artifact.common_guard_proof
    if type(proof) is not CommonGuardProof:
        raise CMEEVerticalError("common_guard_proof_type_mismatch")
    expected_units = tuple(
        (line.sentence_id, _sha256_text(line.text))
        for line in safe_lines
        if line.binding.line_role == "cmee_observation"
    )
    if not expected_units:
        raise CMEEVerticalError("common_guard_proof_observation_missing")
    if (
        type(proof.guarded_observation_units) is not tuple
        or proof.guarded_observation_units != expected_units
        or any(
            type(row) is not tuple
            or len(row) != 2
            or any(type(value) is not str for value in row)
            for row in proof.guarded_observation_units
        )
    ):
        raise CMEEVerticalError("common_guard_proof_observation_binding_mismatch")
    if (
        proof.schema_version != CMEE_COMMON_GUARD_PROOF_VERSION
        or proof.source_envelope_id != source.envelope.envelope_id
        or proof.source_envelope_id != graph.source_envelope_id
        or proof.graph_id != graph.graph_id
        or proof.plan_id != artifact.plan.plan_id
    ):
        raise CMEEVerticalError("common_guard_proof_artifact_binding_mismatch")

    if type(proof.guard_results) is not tuple or len(proof.guard_results) != len(
        EXPECTED_COMMON_GUARD_IDS
    ):
        raise CMEEVerticalError("common_guard_proof_result_shape_mismatch")
    for expected_guard_id, row in zip(
        EXPECTED_COMMON_GUARD_IDS,
        proof.guard_results,
        strict=True,
    ):
        if (
            type(row) is not CommonGuardResultProof
            or type(row.guard_id) is not str
            or row.guard_id != expected_guard_id
            or type(row.passed) is not bool
            or row.passed is not True
        ):
            raise CMEEVerticalError("common_guard_proof_result_mismatch")

    if (
        proof.stabilization_report_name
        != COMMON_GUARD_STABILIZATION_REPORT_NAME
        or proof.stabilization_phase != COMMON_GUARD_STABILIZATION_PHASE
        or proof.stabilization_core_id != COMMON_GUARD_STABILIZATION_CORE_ID
        or type(proof.stabilization_passed) is not bool
        or proof.stabilization_passed is not True
        or type(proof.common_shapes_ready) is not bool
        or proof.common_shapes_ready is not True
        or type(proof.stabilization_guard_names) is not tuple
        or proof.stabilization_guard_names != EXPECTED_COMMON_GUARD_IDS
        or type(proof.issue_codes) is not tuple
        or proof.issue_codes
    ):
        raise CMEEVerticalError("common_guard_proof_stabilization_mismatch")

    expected_proof_id = _common_guard_proof_id(
        source_envelope_id=proof.source_envelope_id,
        graph_id=proof.graph_id,
        plan_id=proof.plan_id,
        guarded_observation_units=proof.guarded_observation_units,
        guard_results=proof.guard_results,
        stabilization_report_name=proof.stabilization_report_name,
        stabilization_phase=proof.stabilization_phase,
        stabilization_core_id=proof.stabilization_core_id,
        stabilization_passed=proof.stabilization_passed,
        common_shapes_ready=proof.common_shapes_ready,
        stabilization_guard_names=proof.stabilization_guard_names,
        issue_codes=proof.issue_codes,
    )
    if proof.proof_id != expected_proof_id:
        raise CMEEVerticalError("common_guard_proof_identity_mismatch")
    if not artifact.trace or any(
        type(row.artifact_common_guard_proof_ref) is not str
        or row.artifact_common_guard_proof_ref != proof.proof_id
        for row in artifact.trace
    ):
        raise CMEEVerticalError("common_guard_proof_trace_binding_mismatch")


def validate_positive_realization_trace(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    artifact: GenerationArtifactBundle,
    safe_lines: Sequence[Any],
) -> None:
    _validate_route_b_graph_contract(source, graph)
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
    canonical_observation_lines = _canonical_r4_observation_lines(
        source,
        canonical_grounded_plan,
        canonical_resolver,
    )
    canonical_unknown_line, canonical_reception_line = _canonical_r4_tail_lines(
        source,
        canonical_plan,
        canonical_grounded_plan,
        canonical_resolver,
    )
    canonical_safe_lines = (
        *canonical_observation_lines,
        canonical_unknown_line,
        canonical_reception_line,
    )
    if tuple(safe_lines) != canonical_safe_lines:
        raise CMEEVerticalError("visible_line_source_semantic_mismatch")
    _validate_reception_semantic_compatibility(source, canonical_safe_lines)
    canonical_plan = _bind_plan_to_visible_lines(
        source,
        canonical_graph,
        canonical_plan,
        canonical_safe_lines,
    )
    if artifact.plan != canonical_plan:
        raise CMEEVerticalError("experience_plan_source_semantic_mismatch")
    if graph.source_envelope_id != source.envelope.envelope_id:
        raise CMEEVerticalError("graph_source_envelope_mismatch")
    owners = tuple(row.owner_id for row in graph.owner_dispositions)
    expected_owners = graph.required_owner_refs + graph.active_optional_owner_refs
    if owners != expected_owners or len(owners) != len(set(owners)):
        raise CMEEVerticalError("route_b_owner_denominator_mismatch")
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
    if artifact.plan.unknown_duty_id != UNKNOWN_DUTY_ID:
        raise CMEEVerticalError("unknown_duty_identity_mismatch")
    if artifact.plan.reception_duty_id != RECEPTION_DUTY_ID:
        raise CMEEVerticalError("reception_duty_identity_mismatch")
    expected_binding = (
        graph.source_envelope_id,
        graph.source_version,
        graph.obligation_version,
        graph.owner_universe_digest,
    )
    plan_binding = (
        artifact.plan.source_envelope_id,
        artifact.plan.source_version,
        artifact.plan.obligation_version,
        artifact.plan.owner_universe_digest,
    )
    if plan_binding != expected_binding:
        raise CMEEVerticalError("experience_plan_universe_binding_mismatch")
    if artifact.realizer_contract_ids != REALIZER_CONTRACT_IDS:
        raise CMEEVerticalError("realizer_contract_identity_mismatch")
    if artifact.trust_policy_ids != TRUST_POLICY_IDS:
        raise CMEEVerticalError("trust_policy_identity_mismatch")
    _validate_common_guard_proof(source, graph, artifact, safe_lines)
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
    positive = {
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    expected_visible_unknown = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if source.owner_obligation(row.owner_id).obligation_kind
        == "STRUCTURED_CONTEXT_ATTACHMENT"
        and row.disposition
        in {
            RouteBDisposition.UNKNOWN_PRESERVED_LIMITED,
            RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
        }
    )
    expected_required_unknown = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.owner_class is OwnerClass.REQUIRED
        and row.owner_id in set(expected_visible_unknown)
    )
    unresolved_required = tuple(
        row
        for row in graph.owner_dispositions
        if row.owner_class is OwnerClass.REQUIRED and row.disposition not in positive
    )
    if any(
        row.owner_id not in set(expected_visible_unknown)
        for row in unresolved_required
    ):
        raise CMEEVerticalError("required_unknown_not_safely_visible")
    if (
        artifact.plan.visible_unknown_owner_ids != expected_visible_unknown
        or artifact.plan.required_unknown_owner_ids != expected_required_unknown
    ):
        raise CMEEVerticalError("plan_required_unknown_owner_mismatch")
    if artifact.plan.visible_line_ids != tuple(line.sentence_id for line in safe_lines):
        raise CMEEVerticalError("plan_visible_line_set_mismatch")
    if len(artifact.trace) != len(safe_lines):
        raise CMEEVerticalError("visible_trace_count_mismatch")
    expected_visible_unit_ids = tuple(
        f"visible:{ordinal}" for ordinal in range(1, len(safe_lines) + 1)
    )
    if tuple(row.visible_unit_id for row in artifact.trace) != expected_visible_unit_ids:
        raise CMEEVerticalError("visible_trace_unit_identity_mismatch")
    line_roles = tuple(line.binding.line_role for line in safe_lines)
    if (
        not line_roles
        or line_roles[-2:] != ("cmee_unknown", "human_follow")
        or any(role != "cmee_observation" for role in line_roles[:-2])
        or not line_roles[:-2]
    ):
        raise CMEEVerticalError("visible_line_role_cardinality_mismatch")
    if any(
        (
            row.source_envelope_id,
            row.source_version,
            row.obligation_version,
            row.owner_universe_digest,
        )
        != expected_binding
        for row in artifact.trace
    ):
        raise CMEEVerticalError("visible_trace_universe_binding_mismatch")

    unknown_lines = tuple(
        line for line in safe_lines if line.binding.line_role == "cmee_unknown"
    )
    if len(unknown_lines) != 1:
        raise CMEEVerticalError("visible_required_unknown_missing")
    covered_unknown_owners = tuple(
        owner_id
        for line in unknown_lines
        for owner_id in line.binding.constrained_owner_ids
    )
    if (
        covered_unknown_owners != artifact.plan.visible_unknown_owner_ids
        or len(covered_unknown_owners) != len(set(covered_unknown_owners))
    ):
        raise CMEEVerticalError("visible_required_unknown_coverage_mismatch")
    expected_unknown_span_ids = _ordered(
        source_span_id
        for owner_id in artifact.plan.visible_unknown_owner_ids
        for source_span_id in source.owner_obligation(owner_id).source_span_ids
    )
    unknown_line = unknown_lines[0]
    if (
        unknown_line.sentence_id != "cmee:unknown:1"
        or unknown_line.text != STRUCTURED_ATTACHMENT_UNKNOWN_TEXT
        or unknown_line.binding.nucleus_ids
        or unknown_line.binding.relation_ids
        or unknown_line.binding.evidence_span_ids != expected_unknown_span_ids
        or unknown_line.binding.constrained_owner_ids
        != artifact.plan.visible_unknown_owner_ids
        or unknown_line.binding.claim_scope
        != "cmee_evidence_bound_unknown_preservation"
        or unknown_line.binding.contains_question
        or not unknown_line.binding.required
    ):
        raise CMEEVerticalError("visible_unknown_canonical_binding_mismatch")

    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    dispositions = {row.owner_id: row for row in graph.owner_dispositions}
    refs = {row.source_span_id: row for row in source.evidence_refs}
    observation_text: list[str] = []
    unknown_text: list[str] = []
    reception_text: list[str] = []
    for trace, line in zip(artifact.trace, safe_lines, strict=True):
        is_reception = line.binding.line_role == "human_follow"
        is_unknown = line.binding.line_role == "cmee_unknown"
        if not is_reception and not is_unknown and line.binding.line_role != "cmee_observation":
            raise CMEEVerticalError("visible_line_role_invalid")
        expected_role = (
            "UNKNOWN" if is_unknown else ("RECEPTION" if is_reception else "OBSERVATION")
        )
        expected_duty = (
            artifact.plan.unknown_duty_id
            if is_unknown
            else (
                artifact.plan.reception_duty_id
                if is_reception
                else artifact.plan.observation_duty_id
            )
        )
        expected_operation = (
            "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
            if is_unknown
            else (
                "BOUND_HUMAN_RECEPTION"
                if is_reception
                else "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
            )
        )
        expected_nodes = (
            ()
            if is_unknown
            else tuple(
                _stable_id("mn", source.envelope.envelope_id, source_id)
                for source_id in line.binding.nucleus_ids
            )
        )
        expected_edges = (
            ()
            if is_unknown
            else tuple(
                _stable_id("me", source.envelope.envelope_id, source_id)
                for source_id in line.binding.relation_ids
            )
        )
        expected_evidence = tuple(
            refs[source_id].evidence_id
            for source_id in line.binding.evidence_span_ids
        )
        expected_constraints = (
            line.binding.constrained_owner_ids
            if is_unknown
            else (artifact.plan.unresolved_owner_ids if is_reception else ())
        )
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
        if is_unknown:
            if not trace.evidence_ids or trace.meaning_node_ids or trace.meaning_edge_ids:
                raise CMEEVerticalError("visible_unknown_trace_authority_mismatch")
        else:
            if not expected_nodes and not expected_edges:
                raise CMEEVerticalError("positive_visible_claim_binding_empty")
            for node_id in trace.meaning_node_ids:
                node = nodes.get(node_id)
                row = dispositions.get(node.owner_id) if node is not None else None
                if (
                    node is None
                    or row is None
                    or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or row.disposition is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                    or node_id not in row.visible_claim_refs
                ):
                    raise CMEEVerticalError("visible_trace_node_authority_mismatch")
            for edge_id in trace.meaning_edge_ids:
                edge = edges.get(edge_id)
                row = dispositions.get(edge.owner_id) if edge is not None else None
                if (
                    edge is None
                    or row is None
                    or edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or row.disposition is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                    or edge_id not in row.visible_claim_refs
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
                or normalize_evidence_literal(selected_raw.decode("utf-8"))
                != expected_normalized
                or _sha256_text(selected_raw.decode("utf-8")) != ref.literal_sha256
                or _sha256_text(
                    source.envelope.raw_utf8[
                        ref.field_utf8_start : ref.field_utf8_end
                    ].decode("utf-8")
                )
                != ref.field_sha256
            ):
                raise CMEEVerticalError("visible_trace_source_locator_mismatch")
        (
            unknown_text
            if is_unknown
            else (reception_text if is_reception else observation_text)
        ).append(line.text)
    if (
        artifact.observation != "\n".join(observation_text)
        or artifact.reception != "\n".join(reception_text)
    ):
        raise CMEEVerticalError("artifact_surface_trace_mismatch")
    if not observation_text or not unknown_text or not reception_text:
        raise CMEEVerticalError("limited_artifact_duty_missing")
    expected_visible_unknowns = tuple(
        VisibleUnknownUnit(
            unknown_unit_id=trace.visible_unit_id,
            source_sentence_id=line.sentence_id,
            source_envelope_id=trace.source_envelope_id,
            source_version=trace.source_version,
            obligation_version=trace.obligation_version,
            owner_universe_digest=trace.owner_universe_digest,
            duty_id=trace.duty_id,
            text=line.text,
            owner_ids=trace.constrained_by_owner_ids,
            evidence_ids=trace.evidence_ids,
        )
        for trace, line in zip(artifact.trace, safe_lines, strict=True)
        if trace.role == "UNKNOWN"
    )
    if artifact.visible_unknowns != expected_visible_unknowns:
        raise CMEEVerticalError("visible_unknown_unit_exact_binding_mismatch")
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
        artifact.common_guard_proof.proof_id,
        artifact.observation,
        tuple(row.text for row in artifact.visible_unknowns),
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
    safe_lines, common_guard_material = _realize_cmee_experience(
        source,
        graph,
        plan,
        grounded_plan,
    )
    plan = _bind_plan_to_visible_lines(source, graph, plan, safe_lines)
    observation = "\n".join(
        line.text
        for line in safe_lines
        if line.binding.line_role == "cmee_observation"
    )
    reception = "\n".join(
        line.text for line in safe_lines if line.binding.line_role == "human_follow"
    )
    common_guard_proof = _build_common_guard_proof(
        source,
        graph,
        plan,
        safe_lines,
        common_guard_material,
    )
    trace = _trace_for_lines(
        source,
        graph,
        plan,
        safe_lines,
        common_guard_proof.proof_id,
    )
    visible_unknowns = tuple(
        VisibleUnknownUnit(
            unknown_unit_id=trace_row.visible_unit_id,
            source_sentence_id=line.sentence_id,
            source_envelope_id=trace_row.source_envelope_id,
            source_version=trace_row.source_version,
            obligation_version=trace_row.obligation_version,
            owner_universe_digest=trace_row.owner_universe_digest,
            duty_id=trace_row.duty_id,
            text=line.text,
            owner_ids=trace_row.constrained_by_owner_ids,
            evidence_ids=trace_row.evidence_ids,
        )
        for trace_row, line in zip(trace, safe_lines, strict=True)
        if trace_row.role == "UNKNOWN"
    )
    artifact = GenerationArtifactBundle(
        artifact_id=_artifact_id(
            source.envelope.envelope_id,
            graph.graph_id,
            plan.plan_id,
            common_guard_proof.proof_id,
            observation,
            tuple(row.text for row in visible_unknowns),
            reception,
        ),
        realizer_contract_ids=REALIZER_CONTRACT_IDS,
        trust_policy_ids=TRUST_POLICY_IDS,
        common_guard_proof=common_guard_proof,
        observation=observation,
        reception=reception,
        plan=plan,
        trace=trace,
        visible_unknowns=visible_unknowns,
    )
    validate_positive_realization_trace(source, graph, artifact, safe_lines)
    return graph, plan, artifact


__all__ = [
    "ADMISSIBLE_NUCLEUS_GROUNDING",
    "ADMISSIBLE_RELATION_GROUNDING",
    "CMEEVerticalError",
    "OBSERVATION_DUTY_ID",
    "RECEPTION_DUTY_ID",
    "UNKNOWN_DUTY_ID",
    "build_text_grounded_limited_artifact",
    "validate_positive_realization_trace",
]
