# -*- coding: utf-8 -*-
from __future__ import annotations

"""Canonical EmlisAI reply orchestration after the I5 single cutover.

The public callable contract is unchanged.  Substantive current-input replies
now have one source of truth:

Evidence Ledger -> GroundedObservationPlan -> GroundedSentencePlan ->
functional Surface -> semantic Gate -> ReplyEnvelope.

The pre-I5 composer/recomposition/recovery body routes are intentionally not
imported here.  Safety support and emergency remain non-observation outcomes
owned by their separate safety perimeter.
"""

from typing import Any, Dict, List, Optional
from uuid import uuid4

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_response_contract import (
    EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY,
    EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION,
    EMLIS_INTERNAL_RESPONSE_CONTRACT_VERSION_META_KEY,
    ResponseKind,
    build_emlis_internal_response_contract,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    build_emlis_safety_triage_decision,
)
from emlis_ai_types import ReplyEnvelope


def _response_kind(*, safety_kind: str, material_quality: str) -> str:
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        return ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER.value
    if safety_kind == TRIAGE_SAFETY_SUPPORT_REQUIRED:
        return ResponseKind.SAFETY_SUPPORT_REQUIRED.value
    if safety_kind == TRIAGE_SAFETY_BLOCKED_EMERGENCY:
        return ResponseKind.SAFETY_BLOCKED_EMERGENCY.value
    if material_quality in {"limited_grounding", "labels_only_limited"}:
        return ResponseKind.LIMITED_GROUNDING_OBSERVATION.value
    if material_quality == "short_state_sufficient":
        return ResponseKind.LOW_INFORMATION_OBSERVATION.value
    return ResponseKind.NORMAL_OBSERVATION.value


def _reply_kind(response_kind: str) -> str:
    if response_kind == ResponseKind.NORMAL_OBSERVATION.value:
        return "eligible_observation"
    if response_kind == ResponseKind.LOW_INFORMATION_OBSERVATION.value:
        return "low_information_observation"
    return response_kind


async def render_emlis_ai_reply(
    *,
    user_id: str,
    subscription_tier: Any,
    current_input: Dict[str, Any],
    display_name: Optional[str] = None,
    timezone_name: Optional[str] = None,
    composer_client: Any = None,
) -> ReplyEnvelope:
    """Render one immediate observation through the I5 canonical path.

    The retained optional arguments keep callers stable.  They cannot select a
    second substantive body path after cutover.
    """

    _ = (user_id, display_name, timezone_name, composer_client)
    trace_id = f"emlisobs-{uuid4().hex[:16]}"
    capability = resolve_emlis_ai_capability_for_tier(subscription_tier)
    normalized_input = normalize_emlis_current_input(current_input)

    evidence_spans = tuple(build_evidence_ledger(normalized_input))
    resolver = build_evidence_span_resolver(
        evidence_spans,
        current_input=normalized_input,
    )
    reports = tuple(run_perspective_observers(evidence_spans))
    board = build_perspective_board(
        evidence_spans=evidence_spans,
        reports=reports,
    )
    graph = integrate_perspective_board(board=board)
    safety_decision = build_emlis_safety_triage_decision(
        current_input=normalized_input,
        graph=graph,
        evidence_spans=evidence_spans,
    )
    plan = build_grounded_observation_plan(
        normalized_input,
        evidence_spans=evidence_spans,
        reports=reports,
        board=board,
        graph=graph,
        safety_decision=safety_decision,
    )

    selected_sentence_plan = None
    selected_surface = None
    selected_gate = None
    attempted_stages: List[str] = []
    for recovery_stage in GROUND_RECOVERY_STAGES:
        attempted_stages.append(recovery_stage)
        sentence_plan = build_grounded_sentence_plan(
            plan,
            resolver,
            recovery_stage=recovery_stage,
        )
        surface_result = realize_grounded_sentence_plan(
            sentence_plan,
            plan,
            resolver,
        )
        gate_report = evaluate_grounded_observation_gate(
            plan=plan,
            sentence_plan=sentence_plan,
            surface_result=surface_result,
            resolver=resolver,
            product_readfeel_status="not_evaluated",
        )
        selected_sentence_plan = sentence_plan
        selected_surface = surface_result
        selected_gate = gate_report
        if gate_report.passed or gate_report.public_observation_status in {
            "safety_blocked",
            "unavailable",
        }:
            break

    if selected_sentence_plan is None or selected_surface is None or selected_gate is None:
        raise RuntimeError("grounded_reply_stage_not_evaluated")

    visible_contract_guard_required = selected_surface.status == "generated"
    visible_contract_guard_passed = bool(
        not visible_contract_guard_required
        or (
            selected_gate.two_stage_contract_gate == "passed"
            and selected_gate.mechanical_restatement_gate == "passed"
            and selected_gate.two_stage_observation_section_present
            and selected_gate.two_stage_reception_section_present
        )
    )
    public_status = selected_gate.public_observation_status
    rejection_reasons = list(selected_gate.rejection_reasons)
    if selected_gate.passed and not visible_contract_guard_passed:
        public_status = "rejected"
        rejection_reasons.append("runtime_visible_contract_guard_failed")
    final_text = (
        selected_surface.text.strip()
        if selected_gate.passed and visible_contract_guard_passed
        else ""
    )
    response_kind = _response_kind(
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
    )
    reply_kind = _reply_kind(response_kind)

    gate_meta = selected_gate.as_body_free_meta()
    gate_meta.update(
        {
            "recovery_steps": list(attempted_stages),
            "semantic_plan_schema_version": plan.schema_version,
            "sentence_plan_schema_version": selected_sentence_plan.schema_version,
            "surface_schema_version": selected_surface.schema_version,
            "public_reply_path_connected": True,
            "generation_method": "functional_atom_grounded_realizer",
            "composer_source": "grounded_plan_realizer",
            "runtime_visible_contract_guard": (
                "passed"
                if visible_contract_guard_required and visible_contract_guard_passed
                else "failed"
                if visible_contract_guard_required
                else "not_evaluated"
            ),
        }
    )

    meta: Dict[str, Any] = {
        "version": "emlis_ai_v3",
        "kernel_version": "grounded_adaptive_observation.i5.v1",
        "tier": str(getattr(capability, "tier", "") or "free"),
        "observation_status": public_status,
        "public_observation_status": public_status,
        "public_comment_present": bool(final_text),
        "observation_reply_kind": reply_kind,
        "observation_trace_id": trace_id,
        "trace_id": trace_id,
        "rejection_reasons": rejection_reasons,
        "generation_path": selected_gate.generation_path,
        "generation_method": "functional_atom_grounded_realizer",
        "composer_source": "grounded_plan_realizer",
        "delivery_status": public_status,
        "semantic_quality_gate": selected_gate.semantic_quality_gate,
        "product_readfeel_status": selected_gate.product_readfeel_status,
        "grounded_observation": gate_meta,
        "used_sources": ["current_input"],
        "used_memory_layers": ["canonical_history"],
        "fallback_used": False,
        "fixed_sentence_template_used": selected_gate.fixed_semantic_surface_used,
        "case_specific_route_used": False,
        "example_cue_route_used": selected_gate.example_cue_route_used,
        "label_only_assembly_used": selected_gate.label_only_assembly_used,
        "synthetic_evidence_id_used": selected_gate.synthetic_evidence_id_used,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "public_contract_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "p5_p6_overlay": {
            "base_current_input_gate_passed": selected_gate.passed,
            "overlay_applied": False,
            "p5_status": "human_qa_pending",
            "p6_status": "p5_dependency_hold",
            "product_readfeel_status": "not_evaluated",
            "comment_text_body_included": False,
            "raw_input_included": False,
        },
    }

    if public_status in {"passed", "safety_blocked"}:
        contract = build_emlis_internal_response_contract(
            response_kind,
            reason="grounded_observation_i5_canonical_reply",
            repair_attempts=[],
            public_observation_status=public_status,
        )
        meta[EMLIS_INTERNAL_RESPONSE_CONTRACT_VERSION_META_KEY] = (
            EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION
        )
        meta[EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY] = contract

    return ReplyEnvelope(
        comment_text=final_text,
        meta=meta,
        used_evidence=[],
        evidence_by_line={},
        used_memory_layers=["canonical_history"],
        fallback_used=False,
    )


__all__ = ["render_emlis_ai_reply"]
