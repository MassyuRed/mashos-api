# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 10 CompleteComposerClient integration for EmlisAI.

This client connects the Step 3-9 Complete Composer internal pipeline to the
existing conversation composer boundary.  It is intentionally fail-closed: the
client is only usable when AP0 and rollout gates have already allowed the
Complete Composer initial path.  The client itself does not call external AI,
does not use a local LLM, and does not render fixed fallback sentences.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import (
    COMPLETE_COMPOSER_INITIAL_MODEL,
    build_complete_composer_initial_term_meta,
)
from emlis_ai_complete_composer_types import (
    COMPLETE_COMPOSER_GENERATION_METHOD,
    COMPLETE_COMPOSER_GENERATION_SCOPE,
    COMPLETE_COMPOSER_SOURCE_AI_GENERATED,
    COMPLETE_COMPOSER_SOURCE_UNAVAILABLE,
    COMPLETE_COMPOSER_STATUS_GENERATED,
    COMPLETE_COMPOSER_STATUS_UNAVAILABLE,
    CompleteComposerCandidate,
)
from emlis_ai_complete_material_service import build_complete_material_bundle
from emlis_ai_complete_focus_selector import build_complete_coverage_plan
from emlis_ai_complete_relation_graph_service import build_complete_relation_graph
from emlis_ai_complete_sentence_planner import build_complete_sentence_binding_bundle_meta, build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer import (
    CompleteSurfaceRealizationV2,
    build_complete_surface_realization_v2,
    build_complete_surface_signature,
)
from emlis_ai_complete_tone_policy import (
    COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
    COMPLETE_TONE_ENGINE_VERSION,
    build_complete_tone_guard_report,
    build_complete_tone_policy,
    build_complete_tone_policy_contract_meta,
)
from emlis_ai_complete_grounding_service import (
    build_complete_grounding_input,
    build_complete_grounding_report_meta,
    judge_complete_product_quality_grounding,
)
from emlis_ai_complete_self_repair_service import (
    ALLOWED_REPAIR_REASONS,
    build_phase17_self_repair_unavailable_reason_summary,
    normalize_complete_self_repair_reason,
    run_complete_self_repair_loop,
)
from emlis_ai_two_stage_section_surface_plan import build_two_stage_section_surface_plan
from emlis_ai_two_stage_applicability import build_two_stage_applicability_decision
from emlis_ai_types import EvidenceSpan, GraphClaim, ObservationGraph, RelationEdge

COMPLETE_COMPOSER_CLIENT_VERSION = "emlis.complete_composer_client.v1"
COMPLETE_COMPOSER_CLIENT_STAGE = "Step10_CompleteComposerClient_integration"
COMPLETE_COMPOSER_CLIENT_STEP = COMPLETE_COMPOSER_CLIENT_STAGE
COMPLETE_COMPOSER_CLIENT_IMPLEMENTATION_UNIT = "Commit 10"
COMPLETE_COMPOSER_CLIENT_SOURCE = "cocolon_complete_composer_initial"

_TRUE_VALUES = {"1", "true", "yes", "y", "on", "enabled", "enable", "green", "passed", "ok", "allowed", "allow"}
RAW_INPUT_META_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
}


def _clean(value: Any, *, limit: int = 0) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip()
    return text


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean(value).lower() in _TRUE_VALUES


def _dedupe(values: Iterable[Any] | Any | None) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        src: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        src = values
    else:
        src = [values]
    out: list[str] = []
    seen: set[str] = set()
    for raw in src:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _json_safe_value(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe_value(asdict(value))
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean(key)
        if not key_text or key_text in RAW_INPUT_META_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    out: dict[str, Any] = {}
    for key in (
        "span_id",
        "raw_text",
        "detected_type",
        "confidence",
        "source_field",
        "start_index",
        "end_index",
        "composer_meta",
        "coverage_group",
        "coverage_scope",
    ):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


def _as_mappings(values: Sequence[Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list(values or ()):
        row = _as_mapping(item)
        if row:
            rows.append(row)
    return rows


def _ap0_allows_complete_initial(value: Mapping[str, Any] | None) -> bool:
    data = _as_mapping(value)
    report = data.get("complete_composer_initial_ap0_report")
    if isinstance(report, Mapping) and any(
        _bool(report.get(key))
        for key in ("green", "can_enter_complete_composer_initial", "can_proceed_to_complete_initial", "can_proceed_to_a1")
    ):
        return True
    return any(
        _bool(data.get(key))
        for key in (
            "green",
            "can_enter_complete_composer_initial",
            "can_proceed_to_complete_initial",
            "can_proceed_to_a1",
            "can_enter_step19",
        )
    )


def _payload_release_allowed(payload: Mapping[str, Any]) -> bool | None:
    for key in ("complete_composer_control", "complete_initial_control", "rollout_control", "release_meta"):
        item = payload.get(key)
        if isinstance(item, Mapping):
            if "rollout_allowed" in item:
                return _bool(item.get("rollout_allowed"))
            if "release_allowed" in item:
                return _bool(item.get("release_allowed"))
            if "enabled" in item or "attempted" in item:
                return _bool(item.get("enabled")) or _bool(item.get("attempted"))
    return None


def _payload_ap0_decision(payload: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("complete_composer_control", "complete_initial_control", "ap0_decision", "step18_ap0_migration_decision"):
        item = payload.get(key)
        if isinstance(item, Mapping):
            if key in {"complete_composer_control", "complete_initial_control"}:
                nested = item.get("ap0_decision") or item.get("step18_ap0_migration_decision")
                if isinstance(nested, Mapping):
                    return dict(nested)
            return dict(item)
    return {}


def _composition_rejection_reasons(payload: Mapping[str, Any]) -> Tuple[str, ...]:
    contract = payload.get("composition_contract")
    if isinstance(contract, Mapping):
        return _dedupe(contract.get("previous_rejection_reasons"))
    return tuple()


def _coverage_group_from_payload(payload: Mapping[str, Any]) -> str:
    candidates: list[Any] = [
        payload.get("coverage_group"),
        payload.get("coverage_scope"),
    ]
    scope = payload.get("limited_observation_scope")
    if isinstance(scope, Mapping):
        groups = scope.get("coverage_groups")
        if isinstance(groups, (list, tuple)) and groups:
            candidates.append(groups[0])
        candidates.append(scope.get("coverage_scope"))
    graph = payload.get("observation_graph")
    if isinstance(graph, Mapping):
        if graph.get("pressure_sources"):
            candidates.append("pressure")
        if graph.get("core_tensions"):
            candidates.append("conflict")
        if graph.get("value_or_strength_signals"):
            candidates.append("recovery")
    for item in candidates:
        text = _clean(item)
        if text:
            return text
    return "short_daily"


def _payload_safety_blockers(payload: Mapping[str, Any]) -> list[str]:
    graph = payload.get("observation_graph")
    blockers: list[str] = []
    if isinstance(graph, Mapping):
        if list(graph.get("safety_boundaries") or ()):  # fail closed before text.
            blockers.append("complete_initial_safety_boundary")
        if list(graph.get("missing_information") or ()):  # do not invent missing context.
            blockers.append("complete_initial_missing_information")
    return blockers




def _evidence_span_from_row(row: Mapping[str, Any] | Any, *, index: int = 1) -> EvidenceSpan | None:
    data = _as_mapping(row)
    if not data:
        return None
    span_id = _clean(data.get("span_id") or data.get("evidence_span_id") or data.get("id") or f"complete_evidence_{index}")
    raw_text = _clean(data.get("raw_text") or data.get("text") or data.get("source_text") or data.get("sentence"))
    if not span_id or not raw_text:
        return None
    try:
        start_index = int(data.get("start_index") or 0)
    except (TypeError, ValueError):
        start_index = 0
    try:
        end_index = int(data.get("end_index") or start_index + len(raw_text))
    except (TypeError, ValueError):
        end_index = start_index + len(raw_text)
    try:
        confidence = float(data.get("confidence") if data.get("confidence") is not None else 1.0)
    except (TypeError, ValueError):
        confidence = 1.0
    return EvidenceSpan(
        span_id=span_id,
        raw_text=raw_text,
        start_index=start_index,
        end_index=end_index,
        detected_type=_clean(data.get("detected_type") or data.get("type") or "event") or "event",
        confidence=confidence,
        source_field=_clean(data.get("source_field") or "memo") or "memo",
    )


def _evidence_span_objects(rows: Sequence[Any] | None) -> list[EvidenceSpan]:
    spans: list[EvidenceSpan] = []
    seen: set[str] = set()
    for index, item in enumerate(list(rows or ()), start=1):
        if isinstance(item, EvidenceSpan):
            span = item
        else:
            span = _evidence_span_from_row(item, index=index)
        if span is None or not span.span_id or span.span_id in seen:
            continue
        seen.add(span.span_id)
        spans.append(span)
    return spans


def _claim_from_relation_node(node: Any, *, index: int) -> GraphClaim:
    evidence_id = _clean(getattr(node, "evidence_span_id", ""))
    relation = _clean(getattr(node, "relation_type", "")) or "center"
    role = _clean(getattr(node, "role", "")) or relation
    return GraphClaim(
        claim_id=_clean(getattr(node, "node_id", "")) or f"complete_claim_{index}",
        claim_type=role,
        text=role or relation or "current_input_core",
        evidence_span_ids=[evidence_id] if evidence_id else [],
        confidence=0.82,
    )


def _grounding_observation_graph(relation_graph: Any, evidence_spans: Sequence[EvidenceSpan]) -> ObservationGraph:
    nodes = list(getattr(relation_graph, "relation_nodes", ()) or ())
    if nodes:
        claims = [_claim_from_relation_node(node, index=index) for index, node in enumerate(nodes, start=1)]
        claim_by_id = {claim.claim_id: claim for claim in claims}
        primary = claims[0]
        pressure: list[GraphClaim] = []
        recovery: list[GraphClaim] = []
        self_awareness: list[GraphClaim] = []
        limit_signals: list[GraphClaim] = []
        for node, claim in zip(nodes, claims):
            relation = _clean(getattr(node, "relation_type", ""))
            role = _clean(getattr(node, "role", ""))
            if relation == "pressure" or role == "pressure":
                pressure.append(claim)
            elif relation == "recovery":
                recovery.append(claim)
            elif relation == "limit" or role == "limit":
                limit_signals.append(claim)
            elif claim.claim_id != primary.claim_id:
                self_awareness.append(claim)
        edges: list[RelationEdge] = []
        for index, edge in enumerate(list(getattr(relation_graph, "relation_edges", ()) or ()), start=1):
            from_id = _clean(getattr(edge, "source_node_id", ""))
            to_id = _clean(getattr(edge, "target_node_id", ""))
            evidence_ids: list[str] = []
            for claim_id in (from_id, to_id):
                evidence_ids.extend(claim_by_id.get(claim_id, GraphClaim("", "", "")).evidence_span_ids)
            edges.append(
                RelationEdge(
                    edge_id=_clean(getattr(edge, "edge_id", "")) or f"complete_relation_{index}",
                    from_claim_id=from_id or primary.claim_id,
                    to_claim_id=to_id or primary.claim_id,
                    relation_type=_clean(getattr(edge, "relation_type", "")) or "coexistence",
                    evidence_span_ids=list(dict.fromkeys(evidence_ids)),
                    confidence=0.82,
                )
            )
        return ObservationGraph(
            primary_state=primary,
            core_tensions=edges,
            pressure_sources=pressure,
            limit_signals=limit_signals,
            self_awareness=self_awareness,
            value_or_strength_signals=recovery,
        )

    first = evidence_spans[0] if evidence_spans else EvidenceSpan(span_id="complete_missing_evidence", raw_text="current input")
    primary = GraphClaim(
        claim_id="complete_primary_state",
        claim_type="state",
        text="current_input_core",
        evidence_span_ids=[first.span_id] if first.span_id else [],
        confidence=0.5,
    )
    return ObservationGraph(primary_state=primary)


def _report_reasons(report: Any) -> Tuple[str, ...]:
    reasons: list[str] = []
    reasons.extend(_dedupe(getattr(report, "rejection_reasons", None)))
    reasons.extend(_dedupe(getattr(report, "binding_rejection_reasons", None)))
    diagnostics = getattr(report, "binding_diagnostics", None)
    if isinstance(diagnostics, Mapping):
        reasons.extend(_dedupe(diagnostics.get("repair_targets")))
    return tuple(dict.fromkeys(reason for reason in reasons if reason))




def _two_stage_applicability_decision_from_surface_meta(
    surface_meta: Mapping[str, Any] | None,
    *,
    state_answer_two_stage_meta: Mapping[str, Any] | None = None,
    two_stage_section_plan_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    surface = _json_safe_mapping(surface_meta)
    summary = _json_safe_mapping(surface.get("two_stage_surface_realization")) or surface
    state_meta = _json_safe_mapping(state_answer_two_stage_meta)
    plan_meta = _json_safe_mapping(two_stage_section_plan_meta)
    return build_two_stage_applicability_decision(
        composer_meta={**state_meta, **plan_meta, "two_stage_surface_realization": summary, "composer_source": COMPLETE_COMPOSER_SOURCE_AI_GENERATED, "status": COMPLETE_COMPOSER_STATUS_GENERATED},
        candidate_source=COMPLETE_COMPOSER_SOURCE_AI_GENERATED,
        candidate_status=COMPLETE_COMPOSER_STATUS_GENERATED,
        comment_text_present=bool(summary.get("comment_text_present") or surface.get("comment_text_present") or summary.get("labels_present")),
        surface_shape={
            "labels_present": summary.get("labels_present"),
            "observation_label_count": 1 if summary.get("observation_label_present") else 0,
            "reception_label_count": 1 if summary.get("reception_label_present") else 0,
        },
        state_answer_two_stage_meta=state_meta,
        two_stage_section_plan_meta=plan_meta,
        two_stage_surface_meta=summary,
        explicit_required=None,
    )


def _two_stage_unavailable_reason_codes_from_surface_meta(
    surface_meta: Mapping[str, Any] | None,
    *,
    state_answer_two_stage_meta: Mapping[str, Any] | None = None,
    two_stage_section_plan_meta: Mapping[str, Any] | None = None,
) -> Tuple[str, ...]:
    surface = _json_safe_mapping(surface_meta)
    summary = _json_safe_mapping(surface.get("two_stage_surface_realization")) or surface
    state_meta = _json_safe_mapping(state_answer_two_stage_meta)
    plan_meta = _json_safe_mapping(two_stage_section_plan_meta)
    validation_errors = _dedupe(summary.get("validation_errors") or surface.get("validation_errors") or [])
    applicability_decision = _two_stage_applicability_decision_from_surface_meta(
        surface_meta,
        state_answer_two_stage_meta=state_answer_two_stage_meta,
        two_stage_section_plan_meta=two_stage_section_plan_meta,
    )
    if not bool(applicability_decision.get("required")):
        return tuple()
    reasons: list[str] = []
    if summary.get("applied") is False:
        reasons.append("two_stage_required_but_unrealized")
    if summary.get("labels_present") is False:
        reasons.append("two_stage_complete_surface_realizer_label_missing")
    if summary.get("observation_section_non_empty") is False or summary.get("reception_section_non_empty") is False:
        reasons.append("two_stage_complete_surface_realizer_section_empty")
    if "two_stage_complete_sentence_plan_observation_section_missing" in validation_errors:
        reasons.append("two_stage_complete_sentence_plan_observation_section_missing")
    if "two_stage_complete_sentence_plan_reception_section_missing" in validation_errors:
        reasons.append("two_stage_complete_sentence_plan_reception_section_missing")
    if any(reason in validation_errors for reason in (
        "two_stage_complete_sentence_plan_section_meta_missing",
        "two_stage_complete_sentence_plan_observation_section_missing",
        "two_stage_complete_sentence_plan_reception_section_missing",
    )):
        reasons.append("two_stage_complete_sentence_plan_section_meta_missing")
    for reason in validation_errors:
        if str(reason).startswith("two_stage_"):
            reasons.append(str(reason))
    reasons = list(_dedupe(reasons))
    if reasons:
        reasons.append("two_stage_complete_surface_blocked_by_gate")
    return _dedupe(reasons)


def _two_stage_unavailable_reason_summary(
    surface_meta: Mapping[str, Any] | None,
    *,
    state_answer_two_stage_meta: Mapping[str, Any] | None = None,
    two_stage_section_plan_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    decision = _two_stage_applicability_decision_from_surface_meta(
        surface_meta,
        state_answer_two_stage_meta=state_answer_two_stage_meta,
        two_stage_section_plan_meta=two_stage_section_plan_meta,
    )
    codes = _two_stage_unavailable_reason_codes_from_surface_meta(
        surface_meta,
        state_answer_two_stage_meta=state_answer_two_stage_meta,
        two_stage_section_plan_meta=two_stage_section_plan_meta,
    )
    return {
        "phase16_7_unavailable_reason_codes": list(codes),
        "two_stage_unavailable_reason_codes": list(codes),
        "two_stage_required_but_unrealized": "two_stage_required_but_unrealized" in codes,
        "two_stage_complete_surface_blocked_by_gate": "two_stage_complete_surface_blocked_by_gate" in codes,
        "two_stage_applicability_decision": decision,
        "two_stage_applicability_required": bool(decision.get("required")),
        "two_stage_applicability_decision_reason": _clean(decision.get("decision_reason")),
        "two_stage_applicability_exempt": bool(decision.get("exempt")),
        "comment_text_body_included": False,
        "raw_input_included": False,
        "display_gate_relaxed": False,
        "public_response_key_added": False,
    }


def _complete_self_repair_reasons(reasons: Iterable[Any]) -> Tuple[str, ...]:
    """Keep Complete self-repair handoff limited to reasons it can repair.

    Reader-only public display reasons such as ``addressee_not_clear`` and
    ``too_short_for_observation`` must remain visible to the outer gates, but
    they should not abort the Complete candidate generator before the existing
    Reader/Grounding/Template/Display gates can evaluate the candidate.
    """

    allowed = set(ALLOWED_REPAIR_REASONS)
    normalized: list[str] = []
    for reason in _dedupe(reasons):
        mapped = normalize_complete_self_repair_reason(reason)
        if mapped in allowed:
            normalized.append(mapped)
    return tuple(dict.fromkeys(normalized))



def _two_stage_section_surface_plan_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the internal Phase16 two-stage section plan for Complete Composer.

    The payload produced by ConversationComposer already carries this material in
    Phase16-2.  Direct callers may still provide only the older role/surface
    contracts, so this helper rebuilds the same internal plan from those
    additive contracts.  It does not render comment_text and it strips raw input
    keys through the existing JSON-safe mapping helper.
    """

    existing = _json_safe_mapping(payload.get("two_stage_section_surface_plan"))
    if existing and _bool(existing.get("required")):
        return existing
    built = build_two_stage_section_surface_plan(
        _as_mapping(payload.get("state_answer_composer_role_plan")),
        state_answer_surface_contract=_as_mapping(payload.get("state_answer_surface_contract")),
        composition_contract=_as_mapping(payload.get("composition_contract")),
    )
    return _json_safe_mapping(built)


def _two_stage_section_surface_plan_meta(plan: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _json_safe_mapping(plan)
    if not data:
        return {
            "two_stage_section_surface_plan_connected": False,
            "two_stage_section_surface_plan_required": False,
            "two_stage_section_meta_expected": False,
            "two_stage_surface_realization_expected": False,
            "raw_input_included": False,
        }
    return {
        "two_stage_section_surface_plan_connected": True,
        "two_stage_section_surface_plan_required": bool(data.get("required", True)),
        "two_stage_section_surface_plan_material_id": _clean(data.get("material_id")),
        "two_stage_section_surface_plan_schema_version": _clean(data.get("schema_version")),
        "two_stage_section_surface_plan_expected_comment_text_shape": _clean(data.get("expected_comment_text_shape")),
        "two_stage_section_surface_plan_section_order": list(data.get("section_order") or []),
        "two_stage_section_surface_plan_section_ids": list(data.get("section_ids") or []),
        "two_stage_section_meta_expected": True,
        "two_stage_surface_realization_expected": True,
        "two_stage_section_surface_plan_comment_text_generated": False,
        "two_stage_section_surface_plan_raw_input_included": False,
        "raw_input_included": False,
    }


def _state_answer_two_stage_meta_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    role_plan = _as_mapping(payload.get("state_answer_composer_role_plan"))
    composition_contract = _as_mapping(payload.get("composition_contract"))
    expected_shape = (
        _clean(role_plan.get("expected_comment_text_shape"))
        or _clean(composition_contract.get("expected_comment_text_shape"))
    )
    two_stage_required = bool(
        role_plan.get("two_stage_display_required")
        or role_plan.get("section_labels_required")
        or role_plan.get("joined_comment_text_required")
        or composition_contract.get("two_stage_reception_surface_required")
        or expected_shape == "labelled_two_stage_text"
    )
    return {
        "state_answer_composer_role_plan_connected": bool(role_plan),
        "state_answer_two_stage_display_required": two_stage_required,
        "state_answer_section_labels_required": bool(
            role_plan.get("section_labels_required")
            or composition_contract.get("section_labels_required")
            or two_stage_required
        ),
        "state_answer_expected_comment_text_shape": expected_shape or ("labelled_two_stage_text" if two_stage_required else ""),
        "two_stage_reception_surface_required": bool(
            composition_contract.get("two_stage_reception_surface_required") or two_stage_required
        ),
        "two_stage_required_propagated_to_complete_composer": two_stage_required,
        "raw_input_included": False,
    }

def build_complete_composer_client_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_COMPOSER_CLIENT_VERSION,
        "service_version": COMPLETE_COMPOSER_CLIENT_VERSION,
        "target_step": COMPLETE_COMPOSER_CLIENT_STAGE,
        "step": COMPLETE_COMPOSER_CLIENT_STAGE,
        "implementation_unit": COMPLETE_COMPOSER_CLIENT_IMPLEMENTATION_UNIT,
        "stage": "complete_composer_initial",
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "complete_composer_client_added": True,
        "connects_step3_to_step9_pipeline": True,
        "ap0_green_required": True,
        "rollout_allowed_required": True,
        "used_evidence_required": True,
        "sentence_binding_required": True,
        "no_external_ai_required": True,
        "no_fallback_required": True,
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_used": False,
        "fixed_sentence_template_allowed": False,
        "fallback_observation_sentence_added": False,
        "fallback_observation_allowed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "comment_text_contract": "passed_only",
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
        "two_stage_section_surface_plan_supported": True,
        "two_stage_complete_composer_connection_supported": True,
        "two_stage_surface_realization_summary_supported": True,
        "phase17_7_self_repair_unavailable_reason_supported": True,
        "phase17_7_self_repair_unavailable_reason_summary_only": True,
        "phase17_7_comment_text_body_included": False,
        "phase17_7_raw_input_included": False,
    }



def build_complete_composer_client_runtime_gate(
    *,
    payload: Mapping[str, Any] | None = None,
    ap0_decision: Mapping[str, Any] | None = None,
    release_allowed: bool | None = None,
    release_meta: Mapping[str, Any] | None = None,
    candidate: CompleteComposerCandidate | Mapping[str, Any] | None = None,
    require_ap0_green: bool = False,
) -> dict[str, Any]:
    """Return the Step 10 gate state used by registry and client tests.

    The gate is diagnostic-only. It never relaxes Display/Grounding gates and
    never writes public comment_text.
    """
    payload_map = dict(payload or {}) if isinstance(payload, Mapping) else {}
    decision = dict(ap0_decision or {}) if isinstance(ap0_decision, Mapping) else {}
    ap0_green = _ap0_allows_complete_initial(decision)
    if not decision and not require_ap0_green:
        ap0_green = True
    rollout_ok = bool(release_allowed) if release_allowed is not None else False
    if rollout_ok is False and isinstance(release_meta, Mapping):
        rollout_ok = _bool(release_meta.get("enabled")) or _bool(release_meta.get("attempted")) or _bool(release_meta.get("rollout_allowed"))
    external_ai_used = bool(_bool(payload_map.get("external_ai_used")) or _bool(payload_map.get("local_llm_used")))
    fallback_used = bool(_bool(payload_map.get("fallback_observation_sentence_added")) or _bool(payload_map.get("fallback_observation_used")))

    candidate_meta = candidate.as_meta(include_comment_text=False) if isinstance(candidate, CompleteComposerCandidate) else _json_safe_mapping(candidate)
    candidate_generated = None
    used_evidence_present = None
    if candidate is not None:
        candidate_generated = bool(candidate_meta.get("status") == COMPLETE_COMPOSER_STATUS_GENERATED or candidate_meta.get("display_ready"))
        used_evidence_present = bool(candidate_meta.get("used_evidence_span_ids"))

    blockers: list[str] = []
    if not ap0_green:
        blockers.append("ap0_not_green")
    if not rollout_ok:
        blockers.append("rollout_gate_not_allowed")
    if external_ai_used:
        blockers.append("external_ai_used")
    if fallback_used:
        blockers.append("fallback_observation_used")
    if candidate is not None and not candidate_generated:
        blockers.append("complete_candidate_not_generated")
    if candidate is not None and not used_evidence_present:
        blockers.append("used_evidence_span_ids_missing")

    return {
        "version": "emlis.complete_composer_client.runtime_gate.v1",
        "target_step": COMPLETE_COMPOSER_CLIENT_STAGE,
        "step": COMPLETE_COMPOSER_CLIENT_STAGE,
        "complete_composer_client_runtime_gate": True,
        "ready": not blockers,
        "green": not blockers,
        "ap0_green": bool(ap0_green),
        "ap0_decision_supplied": bool(decision),
        "rollout_allowed": bool(rollout_ok),
        "release_allowed": release_allowed,
        "release_meta": _json_safe_mapping(release_meta),
        "external_ai_used": external_ai_used,
        "local_llm_used": False,
        "fallback_observation_used": fallback_used,
        "fallback_observation_sentence_added": fallback_used,
        "candidate_generated": candidate_generated,
        "used_evidence_span_ids_present": used_evidence_present,
        "blocking_reasons": list(blockers),
        "release_blockers": list(blockers),
        "primary_reason": "green" if not blockers else blockers[0],
        "comment_text_contract": "passed_only",
        "comment_text_publicly_assigned": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "external_ai_allowed": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_allowed": False,
        "raw_input_included": False,
    }

def _unavailable_response(reason: str, *, coverage_scope: str = "complete_initial_unavailable", extra_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    extra = _json_safe_mapping(extra_meta)
    phase17_reason_summary = build_phase17_self_repair_unavailable_reason_summary(
        primary_reason=reason,
        candidate_status=COMPLETE_COMPOSER_STATUS_UNAVAILABLE,
        surface_meta=_as_mapping(extra.get("surface_realizer") or extra.get("surface_meta")),
        grounding_meta=_as_mapping(extra.get("final_grounding") or extra.get("initial_grounding") or extra.get("grounding_meta")),
        self_repair_meta=_as_mapping(extra.get("self_repair")),
        extra_meta={**extra, "rejection_reasons": [reason, *list(extra.get("rejection_reasons") or [])]},
    )
    meta = {
        **build_complete_composer_client_contract_meta(),
        **extra,
        "phase17_7_self_repair_unavailable_reason": phase17_reason_summary,
        "phase17_7_unavailable_reason_codes": list(phase17_reason_summary.get("phase17_reason_codes") or []),
        "phase17_7_self_repair_reason_codes": list(phase17_reason_summary.get("phase17_reason_codes") or []),
        "phase17_7_self_repair_handoff_reason_codes": list(phase17_reason_summary.get("self_repair_handoff_reason_codes") or []),
        "phase17_7_product_visible_fixture_reached": bool(phase17_reason_summary.get("product_visible_fixture_reached")),
        "phase17_7_self_repair_reason_summary_only": True,
        "status": COMPLETE_COMPOSER_STATUS_UNAVAILABLE,
        "ready": False,
        "display_ready": False,
        "primary_reason": reason,
        "rejection_reasons": [reason],
        "complete_composer_client_fail_closed": True,
        "comment_text_present": False,
        "comment_text_publicly_assigned": False,
        "comment_text_key_written": False,
        "raw_input_included": False,
    }
    return {
        "schema_version": "emlis.complete_composer.response.v1",
        "response_schema_version": "emlis.complete_composer.response.v1",
        "status": COMPLETE_COMPOSER_STATUS_UNAVAILABLE,
        "composer_source": COMPLETE_COMPOSER_SOURCE_UNAVAILABLE,
        "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
        "generation_scope": COMPLETE_COMPOSER_GENERATION_SCOPE,
        "coverage_scope": coverage_scope,
        "comment_text": "",
        "used_evidence_span_ids": [],
        "used_phrase_unit_ids": [],
        "used_relation_ids": [],
        "confidence": 0.0,
        "fixed_string_renderer_used": False,
        "rejection_reasons": [reason],
        "composer_meta": meta,
    }


class CocolonCompleteComposerClient:
    """Complete Composer initial client.

    The constructor gate mirrors registry gating.  A direct caller must also
    provide AP0/rollout permission, otherwise ``generate`` returns unavailable.
    """

    composer_model = COMPLETE_COMPOSER_INITIAL_MODEL
    generation_method = COMPLETE_COMPOSER_GENERATION_METHOD
    generation_scope = COMPLETE_COMPOSER_GENERATION_SCOPE

    def __init__(
        self,
        *,
        ap0_decision: Mapping[str, Any] | None = None,
        ap0_green: bool | None = None,
        rollout_allowed: bool | None = None,
        release_meta: Mapping[str, Any] | None = None,
    ) -> None:
        self.ap0_decision = dict(ap0_decision or {})
        self.ap0_green = bool(ap0_green) if ap0_green is not None else _ap0_allows_complete_initial(ap0_decision)
        self.rollout_allowed = bool(rollout_allowed)
        self.release_meta = _json_safe_mapping(release_meta)

    def _control_allows(self, payload: Mapping[str, Any]) -> tuple[bool, bool, dict[str, Any]]:
        payload_ap0 = _payload_ap0_decision(payload)
        ap0_green = self.ap0_green or _ap0_allows_complete_initial(payload_ap0)
        payload_rollout = _payload_release_allowed(payload)
        rollout_allowed = self.rollout_allowed if payload_rollout is None else bool(payload_rollout)
        return ap0_green, rollout_allowed, payload_ap0

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(payload, Mapping):
            return _unavailable_response("complete_initial_invalid_payload")

        ap0_green, rollout_allowed, payload_ap0 = self._control_allows(payload)
        if not ap0_green:
            return _unavailable_response(
                "complete_initial_ap0_not_green",
                extra_meta={"ap0_decision": payload_ap0 or self.ap0_decision, "rollout_allowed": rollout_allowed},
            )
        if not rollout_allowed:
            return _unavailable_response(
                "complete_initial_rollout_not_allowed",
                extra_meta={"ap0_green": ap0_green, "release_meta": self.release_meta},
            )

        blockers = _payload_safety_blockers(payload)
        if blockers:
            return _unavailable_response(blockers[0], extra_meta={"safety_blockers": blockers})

        evidence_source = payload.get("evidence_spans") if isinstance(payload.get("evidence_spans"), Sequence) else ()
        evidence_span_objects = _evidence_span_objects(evidence_source)
        evidence_spans = [_as_mapping(span) for span in evidence_span_objects]
        if not evidence_span_objects:
            return _unavailable_response("complete_initial_evidence_spans_missing")

        coverage_group = _coverage_group_from_payload(payload)
        previous_gate_reasons = _composition_rejection_reasons(payload)
        two_stage_section_surface_plan = _two_stage_section_surface_plan_from_payload(payload)
        two_stage_section_surface_plan_meta = _two_stage_section_surface_plan_meta(two_stage_section_surface_plan)
        state_answer_two_stage_meta = _state_answer_two_stage_meta_from_payload(payload)

        material_bundle = build_complete_material_bundle(
            evidence_spans=evidence_spans,
            coverage_group=coverage_group,
            meta={"source": "complete_composer_client", "client_step": COMPLETE_COMPOSER_CLIENT_STAGE},
        )
        if not material_bundle.ready:
            return _unavailable_response(
                "complete_initial_materials_unavailable",
                coverage_scope=coverage_group,
                extra_meta={"material_service": material_bundle.as_meta()},
            )

        coverage_plan = build_complete_coverage_plan(
            material_bundle=material_bundle,
            coverage_group=coverage_group,
            meta={"source": "complete_composer_client"},
        )
        if not coverage_plan.ready:
            return _unavailable_response(
                "complete_initial_focus_unavailable",
                coverage_scope=coverage_group,
                extra_meta={"material_service": material_bundle.as_meta(), "coverage_plan": coverage_plan.as_meta()},
            )

        relation_graph = build_complete_relation_graph(
            coverage_plan=coverage_plan,
            meta={"source": "complete_composer_client"},
        )
        if not relation_graph.ready:
            return _unavailable_response(
                "complete_initial_relation_graph_unavailable",
                coverage_scope=coverage_group,
                extra_meta={"relation_graph": relation_graph.as_meta()},
            )

        sentence_plan = build_complete_sentence_plan_v2(
            observation_graph=relation_graph,
            two_stage_section_surface_plan=two_stage_section_surface_plan,
            state_answer_composer_role_plan=_as_mapping(payload.get("state_answer_composer_role_plan")),
            state_answer_surface_contract=_as_mapping(payload.get("state_answer_surface_contract")),
            composition_contract=_as_mapping(payload.get("composition_contract")),
            meta={
                "source": "complete_composer_client",
                "two_stage_section_surface_plan": two_stage_section_surface_plan,
                **two_stage_section_surface_plan_meta,
                **state_answer_two_stage_meta,
            },
        )
        if not sentence_plan.usable:
            return _unavailable_response(
                "complete_initial_sentence_plan_unavailable",
                coverage_scope=coverage_group,
                extra_meta={"sentence_plan": sentence_plan.as_meta()},
            )

        tone_policy = build_complete_tone_policy(
            sentence_plan=sentence_plan,
            coverage_group=coverage_group,
            relation_types=sentence_plan.relation_types,
            meta={
                "source": "complete_composer_client",
                **two_stage_section_surface_plan_meta,
                **state_answer_two_stage_meta,
            },
        )
        surface_realization = build_complete_surface_realization_v2(
            sentence_plan=sentence_plan,
            tone_policy=tone_policy,
            two_stage_section_surface_plan=two_stage_section_surface_plan,
            meta={
                "source": "complete_composer_client",
                "tone_policy": tone_policy.as_meta(),
                "two_stage_section_surface_plan": two_stage_section_surface_plan,
                **two_stage_section_surface_plan_meta,
                **state_answer_two_stage_meta,
            },
        )
        if not surface_realization.ready:
            surface_meta = surface_realization.as_meta(include_realized_text=False)
            return _unavailable_response(
                "complete_initial_surface_unavailable",
                coverage_scope=coverage_group,
                extra_meta={
                    "surface_realizer": surface_meta,
                    **_two_stage_unavailable_reason_summary(
                        surface_meta,
                        state_answer_two_stage_meta=state_answer_two_stage_meta,
                        two_stage_section_plan_meta=two_stage_section_surface_plan_meta,
                    ),
                },
            )

        grounding_graph = _grounding_observation_graph(relation_graph, evidence_span_objects)
        initial_grounding_report = judge_complete_product_quality_grounding(
            graph=grounding_graph,
            evidence_spans=evidence_span_objects,
            comment_text=surface_realization.realized_text,
            surface_realization=surface_realization,
            sentence_plan=sentence_plan,
            allowed_evidence_span_ids=surface_realization.used_evidence_span_ids,
            coverage_group=coverage_group,
            meta={"source": "complete_composer_client", "stage": "initial_grounding"},
        )

        repair_result = None
        final_realization: CompleteSurfaceRealizationV2 = surface_realization
        observed_repair_reasons = tuple(dict.fromkeys(list(previous_gate_reasons) + list(_report_reasons(initial_grounding_report))))
        repair_reasons = _complete_self_repair_reasons(observed_repair_reasons)
        if repair_reasons:
            repair_result = run_complete_self_repair_loop(
                surface_realization=surface_realization,
                grounding_report=initial_grounding_report,
                gate_reasons=repair_reasons,
                evidence_spans=evidence_span_objects,
                allowed_evidence_span_ids=[span.span_id for span in evidence_span_objects],
                meta={
                    "source": "complete_composer_client",
                    "previous_gate_reasons": list(previous_gate_reasons),
                    "observed_repair_reasons": list(observed_repair_reasons),
                    "self_repair_handoff_reasons": list(repair_reasons),
                },
            )
            if repair_result.ready and not repair_result.aborted:
                final_realization = repair_result.repaired_surface_realization
            elif repair_result.aborted:
                return _unavailable_response(
                    "complete_initial_self_repair_aborted",
                    coverage_scope=coverage_group,
                    extra_meta={
                        "initial_grounding": build_complete_grounding_report_meta(initial_grounding_report),
                        "self_repair": repair_result.as_meta(include_realized_text=False),
                    },
                )

        comment_text = final_realization.comment_text
        final_grounding_report = judge_complete_product_quality_grounding(
            graph=grounding_graph,
            evidence_spans=evidence_span_objects,
            comment_text=final_realization.realized_text,
            surface_realization=final_realization,
            sentence_plan=final_realization.source_sentence_plan or sentence_plan,
            allowed_evidence_span_ids=final_realization.used_evidence_span_ids,
            coverage_group=coverage_group,
            meta={"source": "complete_composer_client", "stage": "final_grounding"},
        )
        final_grounding_meta = build_complete_grounding_report_meta(final_grounding_report)
        final_grounding_failed_before_display_gate = not bool(final_grounding_report.passed)
        final_grounding_failure_reason_codes = list(
            _dedupe(
                list(getattr(final_grounding_report, "rejection_reasons", []) or [])
                + list(getattr(final_grounding_report, "binding_rejection_reasons", []) or [])
            )
        )
        # Phase18-3: Complete Initial candidate generation and public display
        # gate evaluation are separate contracts.  A Complete surface that has
        # already produced labelled text, evidence ids, phrase ids and sentence
        # bindings remains a generated candidate even when an internal Complete
        # grounding probe reports repair targets.  The outer Reader /
        # Grounding / Template / Display gates still decide whether the text is
        # public.  This keeps the legacy Complete Initial contract
        # `candidate_generated == true` + non-passed `reply.comment_text == ""`
        # without relaxing any public gate.
        grounding_input = build_complete_grounding_input(
            surface_realization=final_realization,
            sentence_plan=final_realization.source_sentence_plan or sentence_plan,
            comment_text=final_realization.realized_text,
            coverage_group=coverage_group,
            meta={"source": "complete_composer_client"},
        )
        sentence_binding_bundle = build_complete_sentence_binding_bundle_meta(final_realization.source_sentence_plan or sentence_plan)

        candidate = CompleteComposerCandidate(
            status=COMPLETE_COMPOSER_STATUS_GENERATED,
            composer_source=COMPLETE_COMPOSER_SOURCE_AI_GENERATED,
            composer_model=COMPLETE_COMPOSER_INITIAL_MODEL,
            generation_method=COMPLETE_COMPOSER_GENERATION_METHOD,
            generation_scope=COMPLETE_COMPOSER_GENERATION_SCOPE,
            coverage_scope=coverage_group,
            comment_text=comment_text,
            used_evidence_span_ids=final_realization.used_evidence_span_ids,
            used_phrase_unit_ids=final_realization.used_phrase_unit_ids,
            used_relation_ids=final_realization.relation_types,
            sentence_binding_bundle=grounding_input,
            sentence_plan=final_realization.source_sentence_plan or sentence_plan,
            repair_trace=tuple(getattr(repair_result, "repair_trace", ()) or ()),
            composer_meta={"source": "complete_composer_client"},
        )
        if not candidate.generated:
            return _unavailable_response(
                "complete_initial_candidate_contract_failed",
                coverage_scope=coverage_group,
                extra_meta={"candidate": candidate.as_meta(include_comment_text=False)},
            )

        surface_meta = final_realization.as_meta(include_realized_text=False)
        tone_guard_report = build_complete_tone_guard_report(
            surface_realization=final_realization,
            tone_policy=tone_policy,
            comment_text=final_realization.realized_text,
        )
        repair_meta = repair_result.as_meta(include_realized_text=False) if repair_result is not None else {}
        grounding_meta = dict(grounding_input)
        phase17_reason_summary = build_phase17_self_repair_unavailable_reason_summary(
            primary_reason="" if not final_grounding_failed_before_display_gate else "complete_initial_grounding_failed",
            candidate_status=COMPLETE_COMPOSER_STATUS_GENERATED,
            surface_meta=surface_meta,
            grounding_meta=final_grounding_meta,
            self_repair_meta=repair_meta,
            extra_meta={
                "status": COMPLETE_COMPOSER_STATUS_GENERATED,
                "phase17_product_visible_fixture_reached": not final_grounding_failed_before_display_gate,
            },
        )
        composer_meta = {
            **build_complete_composer_client_contract_meta(),
            "status": COMPLETE_COMPOSER_STATUS_GENERATED,
            "candidate_status_before_display_gate": COMPLETE_COMPOSER_STATUS_GENERATED,
            "candidate_status_after_internal_gate": "generated" if not final_grounding_failed_before_display_gate else "rejected",
            "candidate_generated_before_display_gate": True,
            "complete_candidate_generated_before_display_gate": True,
            "complete_initial_candidate_generation_path_recovered": True,
            "ready": True,
            "display_ready": not final_grounding_failed_before_display_gate,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "generation_scope": COMPLETE_COMPOSER_GENERATION_SCOPE,
            "coverage_group": coverage_group,
            "coverage_scope": coverage_group,
            "ap0_green": True,
            "rollout_allowed": True,
            "release_meta": self.release_meta,
            **state_answer_two_stage_meta,
            **two_stage_section_surface_plan_meta,
            "two_stage_section_surface_plan": _json_safe_mapping(two_stage_section_surface_plan),
            "material_service": material_bundle.as_meta(),
            "coverage_plan": coverage_plan.as_meta(),
            "relation_graph": relation_graph.as_meta(),
            "sentence_plan": sentence_plan.as_meta(),
            "sentence_binding_bundle": sentence_binding_bundle,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "tone_policy": tone_policy.as_meta(),
            "tone_policy_contract": build_complete_tone_policy_contract_meta(),
            "tone_guard_report": tone_guard_report,
            "tone_guard_major_count": int(tone_guard_report.get("tone_guard_major_count") or 0),
            "tone_guard_passed": bool(tone_guard_report.get("passed", True)),
            "tone_policy_applied": True,
            "tone_meaning_added": False,
            "surface_realizer": surface_meta,
            "two_stage_surface_realization": _json_safe_mapping(surface_meta.get("two_stage_surface_realization")),
            "two_stage_applicability_decision": _two_stage_applicability_decision_from_surface_meta(
                surface_meta,
                state_answer_two_stage_meta=state_answer_two_stage_meta,
                two_stage_section_plan_meta=two_stage_section_surface_plan_meta,
            ),
            "two_stage_surface_realization_applied": bool(surface_meta.get("two_stage_surface_realization_applied")),
            "two_stage_comment_text_generated": bool(surface_meta.get("two_stage_comment_text_generated")),
            "phase16_7_unavailable_reason_codes": [],
            "two_stage_unavailable_reason_codes": [],
            "two_stage_required_but_unrealized": False,
            "two_stage_complete_surface_blocked_by_gate": False,
            "daily_unpleasant_reception_surface_quality": _json_safe_mapping(surface_meta.get("daily_unpleasant_reception_surface_quality")),
            "surface_signature": build_complete_surface_signature(final_realization),
            "initial_grounding_report": build_complete_grounding_report_meta(initial_grounding_report),
            "final_grounding_report": final_grounding_meta,
            "grounding_passed": bool(final_grounding_report.passed),
            "complete_initial_candidate_generated_before_display_gate": True,
            "candidate_generated_before_display_gate": True,
            "candidate_status_before_display_gate": COMPLETE_COMPOSER_STATUS_GENERATED,
            "candidate_status_after_display_gate": "pending_outer_display_gate",
            "complete_initial_internal_grounding_failed_before_display_gate": final_grounding_failed_before_display_gate,
            "internal_grounding_failed_before_display_gate": final_grounding_failed_before_display_gate,
            "internal_grounding_failure_reason_codes": final_grounding_failure_reason_codes,
            "complete_initial_candidate_generation_display_gate_separated": True,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "grounding_input": grounding_meta,
            "complete_grounding_binding": grounding_meta,
            "binding_meta": grounding_meta,
            "sentence_bindings": list(grounding_meta.get("sentence_bindings") or []),
            "self_repair": repair_meta,
            "self_repair_report_v2": repair_meta,
            "product_quality_self_repair": bool(repair_meta),
            "phase17_7_self_repair_unavailable_reason": phase17_reason_summary,
            "phase17_7_unavailable_reason_codes": list(phase17_reason_summary.get("phase17_reason_codes") or []),
            "phase17_7_self_repair_reason_codes": list(phase17_reason_summary.get("phase17_reason_codes") or []),
            "phase17_7_self_repair_handoff_reason_codes": list(phase17_reason_summary.get("self_repair_handoff_reason_codes") or []),
            "phase17_7_product_visible_fixture_reached": bool(phase17_reason_summary.get("product_visible_fixture_reached")),
            "phase17_7_self_repair_reason_summary_only": True,
            "repair_trace": list(repair_meta.get("repair_trace") or []),
            "repair_trace_v2": list(repair_meta.get("repair_trace_v2") or repair_meta.get("repair_trace") or []),
            "complete_composer_candidate": candidate.as_meta(include_comment_text=False),
            "used_evidence_span_ids": list(candidate.used_evidence_span_ids),
            "used_phrase_unit_ids": list(candidate.used_phrase_unit_ids),
            "used_relation_ids": list(candidate.used_relation_ids),
            "relation_types": list(candidate.used_relation_ids),
            "comment_text_present": True,
            "comment_text_publicly_assigned": False,
            "comment_text_key_written": False,
            "fallback_observation_sentence_added": False,
            "fixed_string_renderer_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "fixed_sentence_template_used": False,
            "completion_sentence_templates_added": False,
            "raw_input_included": False,
        }
        return {
            "schema_version": "emlis.complete_composer.response.v1",
            "response_schema_version": "emlis.complete_composer.response.v1",
            "status": COMPLETE_COMPOSER_STATUS_GENERATED,
            "composer_source": COMPLETE_COMPOSER_SOURCE_AI_GENERATED,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "generation_scope": COMPLETE_COMPOSER_GENERATION_SCOPE,
            "coverage_scope": coverage_group,
            "comment_text": comment_text,
            "used_evidence_span_ids": list(candidate.used_evidence_span_ids),
            "used_phrase_unit_ids": list(candidate.used_phrase_unit_ids),
            "used_claim_ids": list(coverage_plan.selected_material_ids),
            "used_relation_ids": list(candidate.used_relation_ids),
            "confidence": 0.72,
            "fixed_string_renderer_used": False,
            "composer_meta": composer_meta,
        }


CompleteComposerClient = CocolonCompleteComposerClient

__all__ = [
    "COMPLETE_COMPOSER_CLIENT_IMPLEMENTATION_UNIT",
    "COMPLETE_COMPOSER_CLIENT_SOURCE",
    "COMPLETE_COMPOSER_CLIENT_STAGE",
    "COMPLETE_COMPOSER_CLIENT_STEP",
    "COMPLETE_COMPOSER_CLIENT_VERSION",
    "CompleteComposerClient",
    "CocolonCompleteComposerClient",
    "build_complete_composer_client_contract_meta",
    "build_complete_composer_client_runtime_gate",
]
