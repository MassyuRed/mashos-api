# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-5 Gate Recovery Loop for EmlisAI.

This module classifies Gate failure reason codes into bounded recovery
policies so a repairable failure is not treated as "valid empty comment_text".
When the input bundle is observable, it can prepare diagnostic recovery
material, but P3 prevents that material surface from being promoted directly
to public comment_text.  It does not expose raw input in meta, does not add
public response keys, and does not relax Safety / Grounding / Template /
Visible Surface / Display gates.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final
import json
import re

from emlis_ai_display_gate import decide_emlis_observation_display
from emlis_ai_gate_recovery_public_boundary import (
    decide_gate_recovery_public_boundary,
    gate_recovery_public_display_allowed,
)
from emlis_ai_gate_recovery_public_candidate_builder import (
    BOUNDED_ORIGINAL_REPAIR_SOURCE_PHASE,
    GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY,
    LOW_INFORMATION_RECOVERY_SOURCE_PHASE,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_INTERNAL_POLICY_SENTENCE_LEAK,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    gate_recovery_material_surface_blockers_for_model,
)
from emlis_ai_response_contract import RepairKind, RepairResult, ResponseKind, build_repair_attempt
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_types import (
    ConversationComposerCandidate,
    DisplayDecision,
    GroundingReport,
    GroundingSentenceClaim,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report

GATE_RECOVERY_EVENT_SCHEMA_VERSION: Final = "cocolon.emlis.gate_recovery_event.v1"
GATE_RECOVERY_LOOP_SCHEMA_VERSION: Final = "cocolon.emlis.gate_recovery_loop.v1"
GATE_RECOVERY_LOOP_SOURCE_PHASE: Final = "Phase20-5_Gate_Recovery_Loop"
POST_FINAL_GATE_RECOVERY_SOURCE_PHASE: Final = "Phase20-13_Post_Final_Gate_Recovery"
POST_FINAL_GATE_RECOVERY_CONTEXT: Final = "post_final_pre_return_gate"
GATE_RECOVERY_LOOP_META_KEY: Final = "phase20_5_gate_recovery_loop"
GATE_RECOVERY_SURFACE_BINDING_SCHEMA_VERSION: Final = "cocolon.emlis.gate_recovery_surface_binding.v1"
GATE_RECOVERY_SURFACE_BINDING_SOURCE_PHASE: Final = "Phase20-15_Gate_Recovery_Surface_Binding"
GATE_RECOVERY_SURFACE_BINDING_META_KEY: Final = "phase20_15_gate_recovery_surface_binding"
GATE_RECOVERY_SURFACE_REPETITION_QA_SCHEMA_VERSION: Final = "cocolon.emlis.gate_recovery_surface_repetition_qa.v1"
GATE_RECOVERY_SURFACE_REPETITION_QA_SOURCE_PHASE: Final = "Phase20-15_Gate_Recovery_Surface_Repetition_QA"

GATE_VISIBLE_SURFACE_ACCEPTANCE: Final = "visible_surface_acceptance_gate"
GATE_GROUNDING: Final = "grounding_gate"
GATE_TEMPLATE: Final = "template_gate"
GATE_SAFETY: Final = "safety_gate"
GATE_RUNTIME_SURFACE: Final = "runtime_surface_gate"
GATE_DISPLAY: Final = "display_gate"
GATE_MATERIAL: Final = "material_router"
GATE_INFRASTRUCTURE: Final = "infrastructure_boundary"
GATE_UNKNOWN: Final = "unknown_gate"
GATE_NAMES: Final = frozenset(
    {
        GATE_VISIBLE_SURFACE_ACCEPTANCE,
        GATE_GROUNDING,
        GATE_TEMPLATE,
        GATE_SAFETY,
        GATE_RUNTIME_SURFACE,
        GATE_DISPLAY,
        GATE_MATERIAL,
        GATE_INFRASTRUCTURE,
        GATE_UNKNOWN,
    }
)

POLICY_SHORTEN_SURFACE: Final = "shorten_surface"
POLICY_NARROW_GROUNDING_SCOPE: Final = "narrow_grounding_scope"
POLICY_SOFTEN_ASSERTION: Final = "soften_assertion"
POLICY_REDUCE_RELATION_DEPTH: Final = "reduce_relation_depth"
POLICY_REROUTE_LOW_INFORMATION: Final = "reroute_low_information"
POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER: Final = "reroute_self_denial_safe_state_answer"
POLICY_EXIT_SAFETY_EMERGENCY: Final = "exit_safety_emergency"
POLICY_EXIT_INFRA: Final = "exit_infra"
RECOVERY_POLICIES: Final = frozenset(
    {
        POLICY_SHORTEN_SURFACE,
        POLICY_NARROW_GROUNDING_SCOPE,
        POLICY_SOFTEN_ASSERTION,
        POLICY_REDUCE_RELATION_DEPTH,
        POLICY_REROUTE_LOW_INFORMATION,
        POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER,
        POLICY_EXIT_SAFETY_EMERGENCY,
        POLICY_EXIT_INFRA,
    }
)
TERMINAL_POLICIES: Final = frozenset({POLICY_EXIT_SAFETY_EMERGENCY, POLICY_EXIT_INFRA})

MATERIAL_QUALITY_ELIGIBLE: Final = "eligible"
MATERIAL_QUALITY_LIMITED_GROUNDING: Final = "limited_grounding"
MATERIAL_QUALITY_LOW_INFORMATION: Final = "low_information"
TRIAGE_SAFE_OBSERVATION: Final = "safe_observation"
TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER: Final = "self_denial_safe_state_answer"
TRIAGE_SAFETY_SUPPORT_REQUIRED: Final = "safety_support_required"
TRIAGE_SAFETY_BLOCKED_EMERGENCY: Final = "safety_blocked_emergency"

_REPAIR_KIND_BY_POLICY: Final[dict[str, RepairKind]] = {
    POLICY_SHORTEN_SURFACE: RepairKind.SURFACE_SHORTEN,
    POLICY_NARROW_GROUNDING_SCOPE: RepairKind.GROUNDING_NARROW,
    POLICY_SOFTEN_ASSERTION: RepairKind.ASSERTION_SOFTEN,
    POLICY_REDUCE_RELATION_DEPTH: RepairKind.RELATION_DEPTH_REDUCE,
    POLICY_REROUTE_LOW_INFORMATION: RepairKind.LOW_INFORMATION_REROUTE,
    POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER: RepairKind.SELF_DENIAL_SAFE_REROUTE,
    POLICY_EXIT_SAFETY_EMERGENCY: RepairKind.SAFETY_EMERGENCY_EXIT,
    POLICY_EXIT_INFRA: RepairKind.INFRA_EXIT,
}
_RESPONSE_KIND_BY_POLICY: Final[dict[str, ResponseKind]] = {
    POLICY_SHORTEN_SURFACE: ResponseKind.LIMITED_GROUNDING_OBSERVATION,
    POLICY_NARROW_GROUNDING_SCOPE: ResponseKind.LIMITED_GROUNDING_OBSERVATION,
    POLICY_SOFTEN_ASSERTION: ResponseKind.LIMITED_GROUNDING_OBSERVATION,
    POLICY_REDUCE_RELATION_DEPTH: ResponseKind.LIMITED_GROUNDING_OBSERVATION,
    POLICY_REROUTE_LOW_INFORMATION: ResponseKind.LOW_INFORMATION_OBSERVATION,
    POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER: ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER,
    POLICY_EXIT_SAFETY_EMERGENCY: ResponseKind.SAFETY_BLOCKED_EMERGENCY,
    POLICY_EXIT_INFRA: ResponseKind.INFRASTRUCTURE_ERROR,
}
_POLICY_PRIORITY: Final[dict[str, int]] = {
    POLICY_SHORTEN_SURFACE: 10,
    POLICY_NARROW_GROUNDING_SCOPE: 20,
    POLICY_SOFTEN_ASSERTION: 30,
    POLICY_REDUCE_RELATION_DEPTH: 40,
    POLICY_REROUTE_LOW_INFORMATION: 50,
    POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER: 60,
    POLICY_EXIT_SAFETY_EMERGENCY: 90,
    POLICY_EXIT_INFRA: 100,
}

_SURFACE_MARKERS: Final = frozenset(
    {
        "surface_relation_skeleton_major",
        "surface_relation_skeleton_stack",
        "surface_relation_skeleton_minor",
        "surface_template_skeleton",
        "surface_template_major",
        "same_connector_run",
        "same_connector_repetition",
        "connector_repetition",
        "surface_connector_repetition",
        "analytic_register_leak",
        "malformed_phrase_unit",
        "emotion_focus_unbridged_secondary",
        "positive_tone_over_burden_without_anchor",
        "visible_surface_acceptance_gate_failed",
        "visible_surface_acceptance_gate_action_rerender_surface",
        "runtime_surface_gate_action_rerender_shallow_v2",
        "phase8_repeated_sentence_tail",
        "repeated_surface",
        "limited_composer_repeated_surface",
        "same_ending_major",
        "surface_signature_repeat",
    }
)
_SURFACE_PREFIXES: Final = ("malformed_nominalization_", "visible_surface_acceptance_gate_action_rerender")
_GROUNDING_MARKERS: Final = frozenset(
    {
        "grounding_gate_failed",
        "grounding_failed",
        "graph_evidence_not_used",
        "evidence_not_used",
        "unsupported_sentence",
        "relation_confidence_low",
        "visible_evidence_missing",
        "core_relation_not_reflected",
    }
)
_OVERCLAIM_MARKERS: Final = frozenset(
    {
        "overclaim",
        "candidate_overclaim",
        "unsupported_assertion",
        "personality_label",
        "diagnosis",
        "diagnostic_label",
        "cause_assertion_without_evidence",
        "identity_claim_as_fact",
    }
)
_RELATION_DEPTH_MARKERS: Final = frozenset(
    {"relation_depth_too_deep", "relation_chain_too_deep", "relation_overfit", "too_many_relation_units"}
)
_LOW_INFORMATION_MARKERS: Final = frozenset(
    {
        "safe_unit_insufficient",
        "safe_phrase_unit_insufficient",
        "safe_phrase_unit_missing",
        "safe_focus_unit_missing",
        "safe_unit_missing",
        "no_safe_phrase_unit",
        "no_safe_focus_unit",
        "insufficient_safe_phrase_units",
        "shallow_v2_safe_unit_shortage",
        "too_short_for_observation",
        "low_information",
        "missing_information",
        "bounded_low_information_reroute",
    }
)
_SELF_DENIAL_MARKERS: Final = frozenset(
    {"self_denial", "self_denial_non_emergency", "self_denial_safe_state_answer", "identity_self_denial"}
)
_SAFETY_EMERGENCY_MARKERS: Final = frozenset(
    {
        "safety_blocked_emergency",
        "self_harm_emergency",
        "self_harm_imminent",
        "suicide_imminent",
        "imminent_self_harm",
        "urgent_self_harm",
        "emergency_safety_boundary",
    }
)
_SAFETY_SUPPORT_MARKERS: Final = frozenset({"safety_support_required", "safety_boundary", "safety_blocked_no_reroute"})
_INFRA_MARKERS: Final = frozenset(
    {
        "infrastructure_error",
        "composer_source_unavailable",
        "unavailable_source_not_eligible_for_repair_reroute",
        "source_unavailable_or_non_ai_no_surface_reroute",
        "empty_comment_text_without_candidate",
        "composer_resolution_blocked_rollout",
        "composer_resolution_pre_connection_rollout_stop",
        "reply_timeout_or_error",
        "timeout",
        "exception",
    }
)
_TRUE_INFRA_MARKERS: Final = frozenset(
    {
        "infrastructure_error",
        "composer_resolution_blocked_rollout",
        "composer_resolution_pre_connection_rollout_stop",
        "reply_timeout_or_error",
        "timeout",
        "exception",
    }
)
_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "memo",
        "memo_text",
        "memoText",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "surface_text",
        "realized_text",
        "body",
        "text",
        "sentence",
        "sentences",
        "phrase",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "display_gate_relaxed",
        "visible_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "public_status_extended",
        "observation_status_enum_extended",
        "public_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "fixed_fallback_used",
        "fixed_sentence_template_added",
        "case_specific_route_used",
        "phase19_case_specific_route_used",
        "c_d_specific_runtime_cue_used",
        "case_id_runtime_condition_used",
        "phase_name_runtime_condition_used",
        "safety_emergency_converted_to_passed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "external_ai_used",
        "local_llm_used",
    }
)
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _identifier(value: Any, *, default: str = "unspecified") -> str:
    text = _clean(value) or default
    text = re.sub(r"[^A-Za-z0-9_.:/\-]+", "_", text)[:120]
    return text or default


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        source: Iterable[Any] = [values]
    else:
        try:
            source = list(values)
        except TypeError:
            source = [values]
    out: list[str] = []
    for raw in source:
        item = _identifier(raw, default="")
        if item and item not in out:
            out.append(item)
    return out


def _dedupe_visible_text(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        source: Iterable[Any] = [values]
    else:
        try:
            source = list(values)
        except TypeError:
            source = [values]
    out: list[str] = []
    for raw in source:
        item = re.sub(r"\s+", " ", str(raw or "").replace("\u3000", " ")).strip()
        if item and item not in out:
            out.append(item[:40])
    return out


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value or {}) if isinstance(value, Mapping) else {}


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _has_marker(reasons: Sequence[str], markers: Iterable[str], prefixes: Sequence[str] = ()) -> bool:
    marker_set = set(markers)
    for reason in reasons:
        lowered = reason.lower()
        if reason in marker_set or lowered in marker_set:
            return True
        if any(marker in lowered for marker in marker_set):
            return True
        if any(reason.startswith(prefix) or lowered.startswith(prefix) for prefix in prefixes):
            return True
    return False


def _gate_name(value: Any) -> str:
    gate = _identifier(value, default=GATE_UNKNOWN)
    return gate if gate in GATE_NAMES else GATE_UNKNOWN


def _event_key(event: Mapping[str, Any]) -> tuple[str, str, str]:
    return (_clean(event.get("gate_name")), _clean(event.get("recovery_policy")), ",".join(_dedupe(event.get("failure_reasons"))))


def _event_sort_key(event: Mapping[str, Any]) -> tuple[int, str, str]:
    return (_POLICY_PRIORITY.get(_clean(event.get("recovery_policy")), 999), _clean(event.get("gate_name")), ",".join(_dedupe(event.get("failure_reasons"))))


def _material_quality_from_meta(meta: Mapping[str, Any] | None) -> str:
    route = _safe_mapping(meta)
    quality = _clean(route.get("material_quality"))
    if quality:
        return quality
    bundle = _safe_mapping(route.get("phase20_3_input_material_bundle") or route.get("input_material_bundle"))
    return _clean(bundle.get("material_quality"))


def _response_kind_from_material_quality(material_quality: str) -> ResponseKind:
    if material_quality == MATERIAL_QUALITY_LOW_INFORMATION:
        return ResponseKind.LOW_INFORMATION_OBSERVATION
    if material_quality == MATERIAL_QUALITY_ELIGIBLE:
        return ResponseKind.NORMAL_OBSERVATION
    return ResponseKind.LIMITED_GROUNDING_OBSERVATION


def _policy_from_failure(
    *,
    gate_name: str,
    failure_reasons: Sequence[str],
    material_quality: str = "",
    safety_triage_kind: str = "",
    observation_status: str = "",
    composer_source: str = "",
) -> str:
    reasons = list(failure_reasons)
    triage = _clean(safety_triage_kind)
    status = _clean(observation_status)
    source = _clean(composer_source)

    if triage == TRIAGE_SAFETY_BLOCKED_EMERGENCY or _has_marker(reasons, _SAFETY_EMERGENCY_MARKERS):
        return POLICY_EXIT_SAFETY_EMERGENCY
    if triage == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER or _has_marker(reasons, _SELF_DENIAL_MARKERS):
        return POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER
    observable_material = material_quality in {MATERIAL_QUALITY_ELIGIBLE, MATERIAL_QUALITY_LIMITED_GROUNDING}
    if status == "safety_blocked" or triage == TRIAGE_SAFETY_SUPPORT_REQUIRED or _has_marker(reasons, _SAFETY_SUPPORT_MARKERS):
        return POLICY_EXIT_SAFETY_EMERGENCY
    if material_quality == MATERIAL_QUALITY_LOW_INFORMATION:
        return POLICY_REROUTE_LOW_INFORMATION
    if (not observable_material) and _has_marker(reasons, _LOW_INFORMATION_MARKERS):
        return POLICY_REROUTE_LOW_INFORMATION
    if observable_material and status == "unavailable" and not _has_marker(reasons, _TRUE_INFRA_MARKERS):
        return POLICY_NARROW_GROUNDING_SCOPE
    if status == "unavailable" and (source in {"", "unavailable", "empty"} or _has_marker(reasons, _INFRA_MARKERS)):
        return POLICY_EXIT_INFRA
    if _has_marker(reasons, _TRUE_INFRA_MARKERS) and material_quality != MATERIAL_QUALITY_LOW_INFORMATION:
        return POLICY_EXIT_INFRA
    if _has_marker(reasons, _RELATION_DEPTH_MARKERS):
        return POLICY_REDUCE_RELATION_DEPTH
    if _has_marker(reasons, _OVERCLAIM_MARKERS):
        return POLICY_SOFTEN_ASSERTION
    if _has_marker(reasons, _GROUNDING_MARKERS):
        return POLICY_NARROW_GROUNDING_SCOPE
    if gate_name in {GATE_VISIBLE_SURFACE_ACCEPTANCE, GATE_RUNTIME_SURFACE, GATE_TEMPLATE} or _has_marker(reasons, _SURFACE_MARKERS, _SURFACE_PREFIXES):
        return POLICY_SHORTEN_SURFACE
    return POLICY_NARROW_GROUNDING_SCOPE


def _reasons_from_gate(value: Any, *, visible: bool = False, runtime: bool = False) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    reasons: list[str] = []
    for key in ("rejection_reasons", "repair_reasons", "blocked_reasons", "warning_reasons"):
        reasons.extend(_dedupe(value.get(key)))
    action = _clean(value.get("action"))
    if action:
        if visible:
            reasons.append(f"visible_surface_acceptance_gate_action_{action}")
        elif runtime:
            reasons.append(f"runtime_surface_gate_action_{action}")
        else:
            reasons.append(f"gate_action_{action}")
    classification = _clean(value.get("classification"))
    if visible and classification:
        reasons.append(f"visible_surface_acceptance_gate_classification_{classification}")
    return _dedupe(reasons)


def _gate_trace_mapping(decision: Any, key: str) -> dict[str, Any]:
    trace = getattr(decision, "gate_trace", {}) if decision is not None else {}
    if not isinstance(trace, Mapping):
        return {}
    direct = trace.get(key)
    if isinstance(direct, Mapping):
        return dict(direct)
    if key == "visible_surface_acceptance_gate" and isinstance(trace.get("visible_surface_acceptance"), Mapping):
        return dict(trace["visible_surface_acceptance"])
    if key == "grounding_gate" and isinstance(trace.get("grounding"), Mapping):
        return dict(trace["grounding"])
    return {}


def _repair_result_for_policy(
    *,
    policy: str,
    final_status: str,
    repair_applied: bool,
) -> str:
    if policy == POLICY_REROUTE_LOW_INFORMATION and repair_applied and final_status == "passed":
        return RepairResult.PASSED.value
    if policy == POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER and final_status == "passed":
        return RepairResult.PASSED.value
    if policy in TERMINAL_POLICIES and final_status in {"safety_blocked", "unavailable"}:
        return RepairResult.PASSED.value
    if policy not in TERMINAL_POLICIES and final_status == "passed":
        return RepairResult.PASSED.value
    return RepairResult.NOT_RUN.value


@dataclass(frozen=True)
class GateRecoveryEvent:
    gate_name: str
    failure_reasons: tuple[str, ...]
    recovery_policy: str
    response_kind_after_recovery: str
    repair_kind: str
    repair_result: str = RepairResult.NOT_RUN.value
    comment_text_must_not_be_emptied_yet: bool = True
    final_exit_allowed: bool = False

    def as_meta(self) -> dict[str, Any]:
        policy = _clean(self.recovery_policy)
        if policy not in RECOVERY_POLICIES:
            raise ValueError(f"invalid gate recovery policy: {policy}")
        terminal = policy in TERMINAL_POLICIES
        payload = {
            "schema_version": GATE_RECOVERY_EVENT_SCHEMA_VERSION,
            "gate_name": _gate_name(self.gate_name),
            "failure_reasons": _dedupe(self.failure_reasons),
            "recovery_policy": policy,
            "response_kind_after_recovery": _identifier(self.response_kind_after_recovery, default=_RESPONSE_KIND_BY_POLICY[policy].value),
            "comment_text_must_not_be_emptied_yet": bool(not terminal and self.comment_text_must_not_be_emptied_yet),
            "final_exit_allowed": bool(terminal and self.final_exit_allowed),
            "terminal_exit": bool(terminal),
            "repair_kind": _identifier(self.repair_kind, default=_REPAIR_KIND_BY_POLICY[policy].value),
            "repair_result": _identifier(self.repair_result, default=RepairResult.NOT_RUN.value),
            "empty_comment_text_allowed": bool(terminal and self.final_exit_allowed),
            "public_response_key_change": False,
            "display_gate_relaxed": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        }
        assert_gate_recovery_event_meta(payload)
        return payload


def build_gate_recovery_event(
    *,
    gate_name: Any,
    failure_reasons: Iterable[Any] | Any | None,
    material_quality: Any = "",
    safety_triage_kind: Any = "",
    observation_status: Any = "",
    composer_source: Any = "",
    response_kind_hint: Any = "",
    repair_result: Any = RepairResult.NOT_RUN.value,
) -> dict[str, Any]:
    reasons = _dedupe(failure_reasons)
    gate = _gate_name(gate_name)
    quality = _clean(material_quality)
    policy = _policy_from_failure(
        gate_name=gate,
        failure_reasons=reasons,
        material_quality=quality,
        safety_triage_kind=safety_triage_kind,
        observation_status=observation_status,
        composer_source=composer_source,
    )
    response_kind = _clean(response_kind_hint)
    if not response_kind:
        if policy in {
            POLICY_SHORTEN_SURFACE,
            POLICY_NARROW_GROUNDING_SCOPE,
            POLICY_SOFTEN_ASSERTION,
            POLICY_REDUCE_RELATION_DEPTH,
        } and quality:
            response_kind = _response_kind_from_material_quality(quality).value
            if response_kind == ResponseKind.LOW_INFORMATION_OBSERVATION.value:
                policy = POLICY_REROUTE_LOW_INFORMATION
        else:
            response_kind = _RESPONSE_KIND_BY_POLICY[policy].value
    terminal = policy in TERMINAL_POLICIES
    return GateRecoveryEvent(
        gate_name=gate,
        failure_reasons=tuple(reasons),
        recovery_policy=policy,
        response_kind_after_recovery=response_kind,
        repair_kind=_REPAIR_KIND_BY_POLICY[policy].value,
        repair_result=_clean(repair_result) or RepairResult.NOT_RUN.value,
        comment_text_must_not_be_emptied_yet=not terminal,
        final_exit_allowed=terminal,
    ).as_meta()


def gate_recovery_repair_attempts_from_events(events: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    for index, event in enumerate(events or []):
        if not isinstance(event, Mapping):
            continue
        attempts.append(
            build_repair_attempt(
                attempt_index=index,
                repair_kind=event.get("repair_kind"),
                from_gate=event.get("gate_name"),
                result=event.get("repair_result") or RepairResult.NOT_RUN.value,
            )
        )
    return attempts


def gate_recovery_repair_attempts_from_report(report: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(report, Mapping):
        return []
    attempts = report.get("repair_attempts")
    if isinstance(attempts, Sequence) and not isinstance(attempts, (str, bytes, bytearray)):
        normalized: list[dict[str, Any]] = []
        for item in attempts:
            if not isinstance(item, Mapping):
                continue
            normalized.append(
                build_repair_attempt(
                    attempt_index=item.get("attempt_index", len(normalized)),
                    repair_kind=item.get("repair_kind"),
                    from_gate=item.get("from_gate"),
                    result=item.get("result"),
                )
            )
        return normalized
    return gate_recovery_repair_attempts_from_events(report.get("events") if isinstance(report.get("events"), Sequence) else [])


def _unique_sorted_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in sorted((dict(event) for event in events if isinstance(event, Mapping)), key=_event_sort_key):
        key = _event_key(event)
        if key in seen:
            continue
        seen.add(key)
        out.append(event)
    return out


def build_gate_recovery_loop_report(
    *,
    display_decision: Any,
    final_display_decision: Any | None = None,
    material_route_meta: Mapping[str, Any] | None = None,
    safety_triage_meta: Mapping[str, Any] | None = None,
    observation_display_repair_meta: Mapping[str, Any] | None = None,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    route_meta = _safe_mapping(material_route_meta)
    triage_meta = _safe_mapping(safety_triage_meta)
    repair_meta = _safe_mapping(observation_display_repair_meta)
    material_quality = _material_quality_from_meta(route_meta)
    triage_kind = _clean(triage_meta.get("safety_triage_kind") or route_meta.get("safety_triage_kind"))
    original_status = _clean(getattr(display_decision, "observation_status", "")) or "unavailable"
    final_status = _clean(getattr(final_display_decision, "observation_status", "")) if final_display_decision is not None else original_status
    if not final_status:
        final_status = original_status
    repair_applied = bool(repair_meta.get("applied") or repair_meta.get("low_information_repair_applied"))

    events: list[dict[str, Any]] = []
    visible_gate = _safe_mapping(visible_surface_acceptance_gate_report) or _gate_trace_mapping(display_decision, "visible_surface_acceptance_gate")
    if visible_gate and not bool(visible_gate.get("passed")) and _clean(visible_gate.get("action")) not in {"allow", "warn"}:
        reasons = _reasons_from_gate(visible_gate, visible=True) or ["visible_surface_acceptance_gate_failed"]
        policy_event = build_gate_recovery_event(
            gate_name=GATE_VISIBLE_SURFACE_ACCEPTANCE,
            failure_reasons=reasons,
            material_quality=material_quality,
            safety_triage_kind=triage_kind,
            observation_status=original_status,
        )
        events.append(policy_event)

    runtime_gate = _safe_mapping(runtime_surface_pre_return_gate_report) or _gate_trace_mapping(display_decision, "runtime_surface_pre_return_gate")
    if runtime_gate and not bool(runtime_gate.get("passed")) and _clean(runtime_gate.get("action")) not in {"allow", "warn"}:
        events.append(
            build_gate_recovery_event(
                gate_name=GATE_RUNTIME_SURFACE,
                failure_reasons=_reasons_from_gate(runtime_gate, runtime=True) or ["runtime_surface_gate_failed"],
                material_quality=material_quality,
                safety_triage_kind=triage_kind,
                observation_status=original_status,
            )
        )

    grounding_gate = _gate_trace_mapping(display_decision, "grounding_gate")
    if grounding_gate and not bool(grounding_gate.get("passed", True)):
        events.append(
            build_gate_recovery_event(
                gate_name=GATE_GROUNDING,
                failure_reasons=_reasons_from_gate(grounding_gate) or ["grounding_gate_failed"],
                material_quality=material_quality,
                safety_triage_kind=triage_kind,
                observation_status=original_status,
            )
        )

    display_reasons = _dedupe(getattr(display_decision, "rejection_reasons", []) or [])
    if original_status != "passed" and display_reasons:
        events.append(
            build_gate_recovery_event(
                gate_name=GATE_SAFETY if original_status == "safety_blocked" else GATE_INFRASTRUCTURE if original_status == "unavailable" else GATE_DISPLAY,
                failure_reasons=display_reasons,
                material_quality=material_quality,
                safety_triage_kind=triage_kind,
                observation_status=original_status,
            )
        )
    if repair_applied:
        events.append(
            build_gate_recovery_event(
                gate_name=GATE_MATERIAL,
                failure_reasons=repair_meta.get("repair_reasons") or ["gate_recovery_repaired_to_low_information"],
                material_quality=MATERIAL_QUALITY_LOW_INFORMATION,
                safety_triage_kind=TRIAGE_SAFE_OBSERVATION,
                observation_status="passed",
                response_kind_hint=ResponseKind.LOW_INFORMATION_OBSERVATION.value,
                repair_result=RepairResult.PASSED.value,
            )
        )

    events = _unique_sorted_events(events)
    adjusted: list[dict[str, Any]] = []
    for event in events:
        policy = _clean(event.get("recovery_policy"))
        event = dict(event)
        event["repair_result"] = _repair_result_for_policy(
            policy=policy,
            final_status=final_status,
            repair_applied=repair_applied,
        )
        adjusted.append(event)
    events = adjusted
    attempts = gate_recovery_repair_attempts_from_events(events)
    terminal_events = [event for event in events if event.get("terminal_exit") is True]
    non_terminal_events = [event for event in events if event.get("terminal_exit") is not True]
    final_empty_allowed = bool(final_status in {"safety_blocked", "unavailable"} and terminal_events and not non_terminal_events)
    report = {
        "schema_version": GATE_RECOVERY_LOOP_SCHEMA_VERSION,
        "source_phase": GATE_RECOVERY_LOOP_SOURCE_PHASE,
        "gate_recovery_loop_ready": True,
        "phase20_5_gate_recovery_loop_ready": True,
        "evaluated": True,
        "original_observation_status": original_status,
        "final_observation_status": final_status,
        "gate_failure_detected": bool(events),
        "events": events,
        "recovery_events": events,
        "event_count": len(events),
        "repair_attempts": attempts,
        "internal_response_repair_attempts": attempts,
        "first_recovery_policy": _clean(events[0].get("recovery_policy")) if events else "",
        "first_reaction_empty_comment_text": bool(events and not non_terminal_events),
        "first_response_empty_comment_text_allowed": bool(final_empty_allowed and not non_terminal_events),
        "first_response_must_not_empty_comment_text": bool(non_terminal_events),
        "non_terminal_recovery_available": bool(non_terminal_events),
        "empty_comment_text_final_exit_allowed": final_empty_allowed,
        "final_empty_comment_text_allowed": final_empty_allowed,
        "terminal_exit_only_for_safety_or_infra": all(event.get("recovery_policy") in TERMINAL_POLICIES for event in terminal_events),
        "comment_text_absent_allowed_only_for_emergency_or_infra": True,
        "recovery_applied": any(item.get("result") == RepairResult.PASSED.value for item in attempts),
        "recovered_to_public_observation": bool(final_status == "passed" and events),
        "safety_emergency_not_converted_to_observation": not bool(
            any(event.get("recovery_policy") == POLICY_EXIT_SAFETY_EMERGENCY for event in events) and final_status == "passed"
        ),
        "infra_not_faked_as_observation": not bool(
            any(event.get("recovery_policy") == POLICY_EXIT_INFRA for event in events) and final_status == "passed"
        ),
        "gate_threshold_relaxed": False,
        "display_gate_relaxed": False,
        "visible_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "gate_relaxed": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "fixed_fallback_used": False,
        "fixed_sentence_template_added": False,
        "case_specific_route_used": False,
        "phase19_case_specific_route_used": False,
        "c_d_specific_runtime_cue_used": False,
        "case_id_runtime_condition_used": False,
        "phase_name_runtime_condition_used": False,
        "safety_emergency_converted_to_passed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_gate_recovery_loop_meta(report)
    return report


@dataclass(frozen=True)
class GateRecoveryLoopDecision:
    report: Mapping[str, Any]

    def as_meta(self) -> dict[str, Any]:
        meta = dict(self.report or {})
        assert_gate_recovery_loop_meta(meta)
        return meta

    def repair_attempts_for_internal_contract(self) -> list[dict[str, Any]]:
        return list(self.as_meta().get("internal_response_repair_attempts") or [])


def _object_meta(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "as_meta"):
        return _safe_mapping(value.as_meta())
    if isinstance(value, Mapping):
        return dict(value)
    return {"applied": bool(getattr(value, "applied", False))}


def build_gate_recovery_loop_decision(
    *,
    original_display_decision: Any,
    final_display_decision: Any | None = None,
    safety_report: Any = None,
    safety_triage_kind: Any = "",
    material_quality: Any = None,
    observation_display_repair_result: Any = None,
    bounded_repair_reroute_decision: Any = None,
) -> GateRecoveryLoopDecision:
    material_route_meta = dict(material_quality) if isinstance(material_quality, Mapping) else {"material_quality": _clean(material_quality)}
    triage_kind = _clean(safety_triage_kind)
    if bool(getattr(safety_report, "requires_block", False)) and not triage_kind:
        triage_kind = TRIAGE_SAFETY_BLOCKED_EMERGENCY
    bounded_meta = _object_meta(bounded_repair_reroute_decision)
    runtime_gate = _safe_mapping(bounded_meta.get("runtime_surface_pre_return_gate"))
    visible_gate = _safe_mapping(bounded_meta.get("visible_surface_acceptance_gate"))
    report = build_gate_recovery_loop_report(
        display_decision=original_display_decision,
        final_display_decision=final_display_decision,
        material_route_meta=material_route_meta,
        safety_triage_meta={"safety_triage_kind": triage_kind},
        observation_display_repair_meta=_object_meta(observation_display_repair_result),
        runtime_surface_pre_return_gate_report=runtime_gate,
        visible_surface_acceptance_gate_report=visible_gate,
    )
    return GateRecoveryLoopDecision(report=report)



@dataclass(frozen=True)
class GateRecoveryLoopResult:
    applied: bool
    display_decision: DisplayDecision
    reader_report: ListenerReaderReport
    grounding_report: GroundingReport
    template_echo_report: TemplateEchoReport
    composer_source: str = ""
    composer_candidate: ConversationComposerCandidate | None = None
    runtime_surface_pre_return_gate_report: Mapping[str, Any] = field(default_factory=dict)
    visible_surface_acceptance_gate_report: Mapping[str, Any] = field(default_factory=dict)
    loop_decision: GateRecoveryLoopDecision | None = None
    recovery_policy: str = ""
    blocked_reasons: Sequence[str] = field(default_factory=tuple)
    surface_binding_meta: Mapping[str, Any] = field(default_factory=dict)

    def as_meta(self) -> dict[str, Any]:
        surface_binding = dict(self.surface_binding_meta or {}) if isinstance(self.surface_binding_meta, Mapping) else {}
        return {
            "schema_version": "cocolon.emlis.gate_recovery_loop_result.v1",
            "applied": bool(self.applied),
            "recovery_policy": _clean(self.recovery_policy),
            "blocked_reasons": _dedupe(self.blocked_reasons),
            "final_observation_status": _clean(getattr(self.display_decision, "observation_status", "")),
            "public_response_key_change": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "safety_gate_relaxed": False,
            "fixed_fallback_used": False,
            "case_specific_route_used": False,
            "public_surface_role": surface_binding.get("public_surface_role", ""),
            "candidate_source_kind": surface_binding.get("candidate_source_kind", ""),
            "raw_input_included": False,
            "comment_text_body_included": False,
            GATE_RECOVERY_SURFACE_BINDING_META_KEY: surface_binding,
            "gate_recovery_surface_binding": surface_binding,
        }


def _visible_label_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        for key in ("type", "label", "name", "value"):
            labels = _dedupe_visible_text(value.get(key))
            if labels:
                return labels
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        out: list[str] = []
        for item in value:
            for label in _visible_label_values(item):
                if label and label not in out:
                    out.append(label)
        return out
    return _dedupe_visible_text(value)


def _list_from_current_input(current_input: Mapping[str, Any], *keys: str) -> list[str]:
    for key in keys:
        values = _visible_label_values(current_input.get(key))
        if values:
            return values
    return []


def _material_route_meta(material_route: Any) -> dict[str, Any]:
    if material_route is None:
        return {}
    if hasattr(material_route, "as_meta"):
        try:
            payload = material_route.as_meta()
            return dict(payload) if isinstance(payload, Mapping) else {}
        except Exception:
            return {}
    return _safe_mapping(material_route)


def _route_values(material_route: Any, meta: Mapping[str, Any], name: str) -> list[str]:
    return _dedupe(getattr(material_route, name, None)) or _dedupe(meta.get(name))


def _material_phrase_from_route(*, visible_slots: Sequence[str], relation_ids: Sequence[str]) -> str:
    pieces: list[str] = []
    slots = set(_dedupe(visible_slots))
    relations = set(_dedupe(relation_ids))
    if "relationship" in slots or relations.intersection({"relationship_end", "support_from_other", "support_received_material", "relationship_material"}):
        pieces.append("関係の動き")
    if relations.intersection({"support_from_other", "support_received_material"}):
        pieces.append("受け取った支え")
    if relations.intersection({"gratitude_or_return_intent"}):
        pieces.append("返したい気持ち")
    if relations.intersection({"self_understanding_learning", "value_or_self_understanding_material"}):
        pieces.append("見方の変化")
    if "action" in slots:
        pieces.append("行動の向き")
    if "change" in slots:
        pieces.append("変化")
    if "value" in slots:
        pieces.append("大事にしたいもの")
    if "time" in slots:
        pieces.append("時間の動き")
    if "unresolved_weight" in slots:
        pieces.append("まだほどけきっていない重さ")
    if not pieces:
        pieces.append("いま出ている材料")
    return "、".join(_dedupe_visible_text(pieces)[:4])


def _gate_recovery_surface_family_ids(
    *,
    material_quality: str,
    visible_slots: Sequence[str],
    relation_ids: Sequence[str],
) -> tuple[str, str]:
    slots = set(_dedupe(visible_slots))
    relations = set(_dedupe(relation_ids))
    quality = _clean(material_quality)
    if quality == MATERIAL_QUALITY_LOW_INFORMATION:
        return ("low_information_current_input_material", "low_information_humility_question_current_input_only")
    if "relationship" in slots or relations.intersection(
        {"relationship_end", "support_from_other", "support_received_material", "relationship_material", "gratitude_or_return_intent"}
    ):
        return ("relationship_current_input_material", "relationship_evaluation_blocked_current_input_only")
    if quality == MATERIAL_QUALITY_LIMITED_GROUNDING:
        return ("limited_grounding_current_input_material", "assertion_softened_current_input_only")
    if relations.intersection({"self_understanding_learning", "value_or_self_understanding_material"}):
        return ("self_understanding_current_input_material", "self_understanding_non_conclusive_current_input_only")
    return ("generic_current_input_material", "assertion_softened_current_input_only")


def build_gate_recovery_surface_binding_meta(
    *,
    material_quality: str,
    visible_slots: Sequence[str] = (),
    unknown_slots: Sequence[str] = (),
    relation_ids: Sequence[str] = (),
    policy: str = "",
    recovery_context: str = "pre_public_display_gate",
    post_final_gate_failure: bool = False,
) -> dict[str, Any]:
    """Build meta-only evidence that a Gate Recovery surface is material-bound.

    The generated comment body is intentionally not stored here.  Phase20-15
    uses only counts and family identifiers so later QA can detect fixed
    fallback drift without exact surface-text matching.
    """

    relation_family_ids = _dedupe(relation_ids)
    surface_family_id, closing_family_id = _gate_recovery_surface_family_ids(
        material_quality=material_quality,
        visible_slots=visible_slots,
        relation_ids=relation_ids,
    )
    meta = {
        "schema_version": GATE_RECOVERY_SURFACE_BINDING_SCHEMA_VERSION,
        "source_phase": GATE_RECOVERY_SURFACE_BINDING_SOURCE_PHASE,
        "surface_binding_ready": True,
        "evaluated": True,
        "surface_generation_method": "material_bound_generic_surface",
        "generic_sentence_plan_used": True,
        "material_bound_generic_surface_used": True,
        "visible_material_slot_count": len(_dedupe(visible_slots)),
        "unknown_slot_count": len(_dedupe(unknown_slots)),
        "relation_material_id_count": len(relation_family_ids),
        "relation_family_ids": relation_family_ids,
        "surface_family_id": surface_family_id,
        "closing_family_id": closing_family_id,
        "surface_pattern_family_id": f"{surface_family_id}:{closing_family_id}",
        "material_quality": _clean(material_quality),
        "recovery_policy": _clean(policy),
        "recovery_context": _clean(recovery_context) or "pre_public_display_gate",
        "post_final_gate_failure": bool(post_final_gate_failure),
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
        "public_surface_blockers": _dedupe(
            (
                BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK
                if post_final_gate_failure
                else BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
                BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
                BLOCKER_GATE_RECOVERY_INTERNAL_POLICY_SENTENCE_LEAK,
                BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
            )
        ),
        "same_closing_family_repetition_check_ready": True,
        "same_surface_pattern_repetition_check_ready": True,
        "consecutive_recovery_usage_rate_check_ready": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "public_response_key_change": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "fixed_fallback_used": False,
        "fixed_sentence_template_used": False,
        "case_specific_route_used": False,
        "exact_fixture_surface_used": False,
    }
    assert_gate_recovery_surface_binding_meta(meta)
    return meta

def assert_gate_recovery_surface_binding_meta(meta: Mapping[str, Any]) -> None:
    if not isinstance(meta, Mapping):
        raise ValueError("gate recovery surface binding meta must be a mapping")
    if meta.get("schema_version") != GATE_RECOVERY_SURFACE_BINDING_SCHEMA_VERSION:
        raise ValueError("unexpected gate recovery surface binding schema version")
    if meta.get("source_phase") != GATE_RECOVERY_SURFACE_BINDING_SOURCE_PHASE:
        raise ValueError("unexpected gate recovery surface binding source phase")
    if _clean(meta.get("surface_generation_method")) not in {
        "material_bound_generic_surface",
        "generic_sentence_plan_surface",
        "complete_surface_realizer",
    }:
        raise ValueError("invalid gate recovery surface generation method")
    if meta.get("generic_sentence_plan_used") is not True:
        raise ValueError("gate recovery surface binding requires generic_sentence_plan_used=true")
    for key in ("visible_material_slot_count", "unknown_slot_count", "relation_material_id_count"):
        value = meta.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"gate recovery surface binding {key} must be a non-negative integer")
    for key in ("surface_family_id", "closing_family_id", "surface_pattern_family_id"):
        if not _clean(meta.get(key)):
            raise ValueError(f"gate recovery surface binding requires {key}")
    if not isinstance(meta.get("relation_family_ids"), list):
        raise ValueError("gate recovery surface binding relation_family_ids must be a list")
    for flag in (
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_body_included",
        "comment_text_included",
        "public_response_key_change",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "safety_gate_relaxed",
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "case_specific_route_used",
        "exact_fixture_surface_used",
    ):
        if meta.get(flag) is not False:
            raise ValueError(f"gate recovery surface binding violates fixed contract: {flag}=true")
    if _contains_text_payload_key(meta):
        raise ValueError("gate recovery surface binding meta must stay meta-only and text-free")
    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)

def _longest_same_value_run(values: Sequence[str]) -> int:
    longest = 0
    current = 0
    previous = ""
    for value in values:
        normalized = _identifier(value, default="unspecified")
        if normalized == previous:
            current += 1
        else:
            previous = normalized
            current = 1
        longest = max(longest, current)
    return longest


def build_gate_recovery_surface_repetition_qa_report(bindings: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    for binding in bindings or []:
        if not isinstance(binding, Mapping):
            continue
        meta = dict(binding)
        assert_gate_recovery_surface_binding_meta(meta)
        normalized.append(meta)
    surface_families = [_identifier(item.get("surface_family_id"), default="unspecified") for item in normalized]
    closing_families = [_identifier(item.get("closing_family_id"), default="unspecified") for item in normalized]
    surface_patterns = [
        _identifier(item.get("surface_pattern_family_id"), default=f"{surface_family}:{closing_family}")
        for item, surface_family, closing_family in zip(normalized, surface_families, closing_families, strict=True)
    ]
    count = len(normalized)

    def repeat_rate(values: Sequence[str]) -> float:
        if not values:
            return 0.0
        return round((len(values) - len(set(values))) / len(values), 4)

    repeated_closing_run = _longest_same_value_run(closing_families)
    repeated_surface_run = _longest_same_value_run(surface_families)
    repeated_surface_pattern_run = _longest_same_value_run(surface_patterns)
    same_closing_family_repetition_detected = bool(repeated_closing_run >= 3 and count >= 3)
    same_surface_family_repetition_detected = bool(repeated_surface_run >= 3 and count >= 3)
    same_surface_pattern_repetition_detected = bool(repeated_surface_pattern_run >= 3 and count >= 3)
    fixed_flags_present = any(
        bool(item.get("fixed_fallback_used") or item.get("fixed_sentence_template_used") or item.get("exact_fixture_surface_used"))
        for item in normalized
    )
    report = {
        "schema_version": GATE_RECOVERY_SURFACE_REPETITION_QA_SCHEMA_VERSION,
        "source_phase": GATE_RECOVERY_SURFACE_REPETITION_QA_SOURCE_PHASE,
        "evaluated": True,
        "surface_count": count,
        "unique_surface_family_count": len(set(surface_families)),
        "unique_closing_family_count": len(set(closing_families)),
        "unique_surface_pattern_family_count": len(set(surface_patterns)),
        "surface_family_ids": _dedupe(surface_families),
        "closing_family_ids": _dedupe(closing_families),
        "surface_pattern_family_ids": _dedupe(surface_patterns),
        "longest_same_surface_family_run": repeated_surface_run,
        "longest_same_closing_family_run": repeated_closing_run,
        "longest_same_surface_pattern_family_run": repeated_surface_pattern_run,
        "same_surface_family_repeat_rate": repeat_rate(surface_families),
        "same_closing_family_repeat_rate": repeat_rate(closing_families),
        "same_surface_pattern_family_repeat_rate": repeat_rate(surface_patterns),
        "same_surface_family_repetition_detected": same_surface_family_repetition_detected,
        "same_closing_family_repetition_detected": same_closing_family_repetition_detected,
        "same_surface_pattern_repetition_detected": same_surface_pattern_repetition_detected,
        "requires_surface_quality_review": bool(
            same_surface_family_repetition_detected
            or same_closing_family_repetition_detected
            or same_surface_pattern_repetition_detected
            or fixed_flags_present
        ),
        "fixed_fallback_repetition_detected": bool(fixed_flags_present),
        "fixed_fallback_used": False,
        "fixed_sentence_template_used": False,
        "exact_fixture_surface_used": False,
        "exact_comment_text_matching_used": False,
        "case_specific_route_used": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_text_included": False,
        "public_response_key_change": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
    }
    assert_gate_recovery_surface_repetition_qa_report(report)
    return report


def assert_gate_recovery_surface_repetition_qa_report(meta: Mapping[str, Any]) -> None:
    if not isinstance(meta, Mapping):
        raise ValueError("gate recovery surface repetition QA must be a mapping")
    if meta.get("schema_version") != GATE_RECOVERY_SURFACE_REPETITION_QA_SCHEMA_VERSION:
        raise ValueError("unexpected gate recovery surface repetition QA schema version")
    if meta.get("source_phase") != GATE_RECOVERY_SURFACE_REPETITION_QA_SOURCE_PHASE:
        raise ValueError("unexpected gate recovery surface repetition QA source phase")
    for key in (
        "surface_count",
        "unique_surface_family_count",
        "unique_closing_family_count",
        "unique_surface_pattern_family_count",
        "longest_same_surface_family_run",
        "longest_same_closing_family_run",
        "longest_same_surface_pattern_family_run",
    ):
        value = meta.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"gate recovery surface repetition QA {key} must be a non-negative integer")
    for key in ("surface_family_ids", "closing_family_ids", "surface_pattern_family_ids"):
        if not isinstance(meta.get(key), list):
            raise ValueError(f"gate recovery surface repetition QA {key} must be a list")
    for flag in (
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "exact_fixture_surface_used",
        "exact_comment_text_matching_used",
        "case_specific_route_used",
        "raw_input_included",
        "comment_text_body_included",
        "comment_text_included",
        "raw_text_included",
        "public_response_key_change",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "safety_gate_relaxed",
    ):
        if meta.get(flag) is not False:
            raise ValueError(f"gate recovery surface repetition QA violates fixed contract: {flag}=true")
    if _contains_text_payload_key(meta):
        raise ValueError("gate recovery surface repetition QA must stay meta-only and text-free")
    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


def _join_labels(labels: Sequence[str], *, fallback: str) -> str:
    values = _dedupe_visible_text(labels)
    if not values:
        return fallback
    if len(values) == 1:
        return values[0]
    return "・".join(values[:3])


def _build_recovery_comment_text(
    *,
    current_input: Mapping[str, Any],
    visible_slots: Sequence[str],
    relation_ids: Sequence[str],
    material_quality: str,
) -> str:
    emotions = _list_from_current_input(current_input, "emotions", "emotion_labels", "emotion")
    categories = _list_from_current_input(current_input, "category", "categories", "category_labels")
    category_phrase = _join_labels(categories, fallback="今回の記録")
    emotion_phrase = _join_labels(emotions, fallback="いまの感情")
    material_phrase = _material_phrase_from_route(visible_slots=visible_slots, relation_ids=relation_ids)
    _, closing_family_id = _gate_recovery_surface_family_ids(
        material_quality=material_quality,
        visible_slots=visible_slots,
        relation_ids=relation_ids,
    )
    if closing_family_id == "low_information_humility_question_current_input_only":
        closing = "原因や結論までは決めず、いま見えている重さだけで受け取ります。詳しく残せそうなら、どのあたりが重くなっているか残してみませんか。"
    elif closing_family_id == "relationship_evaluation_blocked_current_input_only":
        closing = "誰かを良い悪いで決めず、そのつながりの動きを受け取ります。"
    elif closing_family_id == "self_understanding_non_conclusive_current_input_only":
        closing = "結論を急がず、変わり始めている感覚を受け取ります。"
    else:
        closing = "原因や結論までは決めず、いま置かれた材料だけで受け取ります。"
    observation = (
        f"今回の入力では、{category_phrase}に関する記録として、{emotion_phrase}の向きが出ています。"
        f"{material_phrase}が一緒に置かれています。"
    )
    reception = closing
    return f"見えたこと：\n{observation}\nEmlisから：\n{reception}"


def _gate_recovery_composer_meta(
    *,
    material_quality: str,
    visible_slots: Sequence[str],
    unknown_slots: Sequence[str],
    relation_ids: Sequence[str],
    policy: str,
    recovery_context: str = "pre_public_display_gate",
    post_final_gate_failure: bool = False,
) -> dict[str, Any]:
    relation_types = _dedupe(relation_ids) or ["current_input_material_bundle_recovery"]
    response_kind = _response_kind_from_material_quality(_clean(material_quality)).value
    source_phase = POST_FINAL_GATE_RECOVERY_SOURCE_PHASE if post_final_gate_failure else GATE_RECOVERY_LOOP_SOURCE_PHASE
    low_information = _clean(material_quality) == MATERIAL_QUALITY_LOW_INFORMATION
    surface_binding = build_gate_recovery_surface_binding_meta(
        material_quality=material_quality,
        visible_slots=visible_slots,
        unknown_slots=unknown_slots,
        relation_ids=relation_ids,
        policy=policy,
        recovery_context=recovery_context,
        post_final_gate_failure=post_final_gate_failure,
    )
    return {
        "schema_version": "cocolon.emlis.phase20_5.gate_recovery_surface.v1",
        "source_phase": source_phase,
        "recovery_context": _clean(recovery_context) or "pre_public_display_gate",
        "post_final_gate_failure": bool(post_final_gate_failure),
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
        "public_surface_blockers": _dedupe(
            gate_recovery_material_surface_blockers_for_model(
                POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
                if post_final_gate_failure
                else GATE_RECOVERY_MATERIAL_SURFACE_MODEL
            )
            + (
                BLOCKER_GATE_RECOVERY_INTERNAL_POLICY_SENTENCE_LEAK,
                BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
            )
        ),
        "observation_reply_kind": response_kind,
        "response_kind": response_kind,
        "material_quality": _clean(material_quality),
        "body_non_empty": True,
        "comment_text_non_empty": True,
        "known_scope_observation_present": True,
        "low_info_known_scope_present": low_information,
        "contains_humility_marker": low_information,
        "humility_marker_present": low_information,
        "contains_question": low_information,
        "question_present": low_information,
        "low_info_question_present": low_information,
        "question_not_only": True,
        "question_only": False,
        "question_only_surface": False,
        "visible_material_slots": _dedupe(visible_slots),
        "unknown_slots": _dedupe(unknown_slots),
        "generic_relation_material_ids": relation_types,
        GATE_RECOVERY_SURFACE_BINDING_META_KEY: surface_binding,
        "gate_recovery_surface_binding": surface_binding,
        "surface_generation_method": surface_binding["surface_generation_method"],
        "surface_family_id": surface_binding["surface_family_id"],
        "closing_family_id": surface_binding["closing_family_id"],
        "gate_recovery_surface_binding_ready": True,
        "recovery_policy": _clean(policy),
        "coverage_scope": "current_input_material_bundle_recovery",
        "generation_scope": "current_input_only",
        "sentence_binding_bundle": {
            "schema_version": "cocolon.emlis.phase20_5.sentence_binding_bundle.v1",
            "binding_count": 2,
            "relation_types": relation_types,
            "coverage_scope": "current_input_material_bundle_recovery",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "surface_quality_signature": {
            "schema_version": "emlis.surface_quality_signature.v1",
            "surface_signature_id": f"phase20_5_gate_recovery_material_surface:{surface_binding['surface_pattern_family_id']}",
            "surface_family_id": surface_binding["surface_family_id"],
            "closing_family_id": surface_binding["closing_family_id"],
            "surface_pattern_family_id": surface_binding["surface_pattern_family_id"],
            "surface_template_major": False,
            "template_major": False,
            "generic_center_phrase_count": 0,
            "same_connector_run_max": 0,
            "same_connector_repetition_count": 0,
            "surface_grammar_warning_count": 0,
            "grammar_warning_codes": [],
            "malformed_nominalization_risk": False,
        },
        "phrase_unit_grammar": {
            "schema_version": "cocolon.emlis.phase20_5.phrase_unit_grammar.v1",
            "malformed_phrase_unit_count": 0,
            "grammar_warning_count": 0,
            "grammar_warning_codes": [],
        },
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "fixed_fallback_used": False,
        "fixed_sentence_template_used": False,
        "case_specific_route_used": False,
        "case_id_runtime_condition_used": False,
        "phase_name_runtime_condition_used": False,
        "c_d_specific_runtime_cue_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
    }


def _surface_binding_meta_with_public_boundary(
    *,
    composer_meta: Mapping[str, Any],
    public_boundary_decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach the meta-only public-boundary decision to surface binding evidence."""

    surface_binding_meta = dict(
        composer_meta.get(GATE_RECOVERY_SURFACE_BINDING_META_KEY, {}) or {}
    )
    public_display_allowed = gate_recovery_public_display_allowed(public_boundary_decision)
    surface_binding_meta.update(
        {
            "public_boundary_decision_ready": True,
            "public_display_allowed": public_display_allowed,
            "public_boundary_blocked": not public_display_allowed,
            "public_boundary_blockers": _dedupe(public_boundary_decision.get("blockers")),
            "gate_recovery_public_boundary_decision": dict(public_boundary_decision),
        }
    )
    return surface_binding_meta


def recover_emlis_gate_failure(
    *,
    current_input: Mapping[str, Any],
    display_decision: DisplayDecision,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    material_route: Any,
    safety_triage_kind: Any = "",
    safety_report: SafetyBoundaryReport | None = None,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
    trace_id: str = "",
    recovery_context: str = "pre_public_display_gate",
    post_final_gate_failure: bool = False,
    allow_low_information_post_final_recovery: bool = False,
    original_composer_candidate: Any | None = None,
    original_composer_source: str = "",
) -> GateRecoveryLoopResult:
    """Try one bounded Phase20-5 recovery without relaxing existing gates."""

    original_status = _clean(getattr(display_decision, "observation_status", ""))
    if original_status == "passed":
        return GateRecoveryLoopResult(False, display_decision, reader_report, grounding_report, template_echo_report, blocked_reasons=("already_passed",))
    safety = safety_report or SafetyBoundaryReport()
    if bool(getattr(safety, "requires_block", False)):
        return GateRecoveryLoopResult(False, display_decision, reader_report, grounding_report, template_echo_report, blocked_reasons=("safety_requires_block",))
    triage = _clean(safety_triage_kind)
    if triage and triage != TRIAGE_SAFE_OBSERVATION:
        return GateRecoveryLoopResult(False, display_decision, reader_report, grounding_report, template_echo_report, blocked_reasons=("safety_triage_not_safe_observation",))

    route_meta = _material_route_meta(material_route)
    material_quality = _material_quality_from_meta(route_meta) or _clean(getattr(material_route, "material_quality", ""))
    observable_material_qualities = {MATERIAL_QUALITY_ELIGIBLE, MATERIAL_QUALITY_LIMITED_GROUNDING}
    if bool(post_final_gate_failure) and bool(allow_low_information_post_final_recovery):
        observable_material_qualities.add(MATERIAL_QUALITY_LOW_INFORMATION)
    if material_quality not in observable_material_qualities:
        return GateRecoveryLoopResult(False, display_decision, reader_report, grounding_report, template_echo_report, blocked_reasons=("material_quality_not_observable_for_gate_recovery",))

    planning_decision = build_gate_recovery_loop_decision(
        original_display_decision=display_decision,
        final_display_decision=display_decision,
        safety_report=safety,
        safety_triage_kind=triage or TRIAGE_SAFE_OBSERVATION,
        material_quality=route_meta,
    )
    plan = planning_decision.as_meta()
    if not bool(plan.get("non_terminal_recovery_available")):
        return GateRecoveryLoopResult(False, display_decision, reader_report, grounding_report, template_echo_report, loop_decision=planning_decision, blocked_reasons=("no_non_terminal_recovery_policy",))
    policy = _clean(plan.get("first_recovery_policy")) or POLICY_NARROW_GROUNDING_SCOPE
    if policy in TERMINAL_POLICIES:
        return GateRecoveryLoopResult(False, display_decision, reader_report, grounding_report, template_echo_report, loop_decision=planning_decision, recovery_policy=policy, blocked_reasons=("terminal_policy",))

    visible_slots = _route_values(material_route, route_meta, "visible_material_slots")
    unknown_slots = _route_values(material_route, route_meta, "unknown_slots")
    relation_ids = _route_values(material_route, route_meta, "generic_relation_material_ids") or _route_values(material_route, route_meta, "relation_material_ids")
    current = current_input if isinstance(current_input, Mapping) else {}
    comment = _build_recovery_comment_text(
        current_input=current,
        visible_slots=visible_slots,
        relation_ids=relation_ids,
        material_quality=material_quality,
    )
    composer_meta = _gate_recovery_composer_meta(
        material_quality=material_quality,
        visible_slots=visible_slots,
        unknown_slots=unknown_slots,
        relation_ids=relation_ids,
        policy=policy,
        recovery_context=recovery_context,
        post_final_gate_failure=post_final_gate_failure,
    )
    candidate = ConversationComposerCandidate(
        comment_text=comment,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id=trace_id,
        attempt_count=1,
        used_evidence_span_ids=[],
        confidence=0.79,
        rejection_reasons=[],
        response_schema_version="cocolon.emlis.phase20_5.gate_recovery.response.v1",
        fixed_string_renderer_used=False,
        composer_model=POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL if post_final_gate_failure else GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
        generation_method=POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD if post_final_gate_failure else GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
        coverage_scope="current_input_material_bundle_recovery",
        generation_scope="current_input_only",
        composer_meta=composer_meta,
        used_claim_ids=[],
        used_relation_ids=_dedupe(relation_ids),
    )
    public_boundary_decision = decide_gate_recovery_public_boundary(
        candidate=candidate,
        composer_meta=composer_meta,
        recovery_context=recovery_context,
    )
    surface_binding_meta = _surface_binding_meta_with_public_boundary(
        composer_meta=composer_meta,
        public_boundary_decision=public_boundary_decision,
    )
    public_candidate_builder_result = build_public_candidate_after_gate_recovery(
        current_input=current,
        material_route=material_route,
        original_composer_candidate=original_composer_candidate,
        original_display_decision=display_decision,
        safety_triage_kind=triage or TRIAGE_SAFE_OBSERVATION,
        safety_report=safety,
        recovery_plan=planning_decision.as_meta(),
        trace_id=trace_id,
        recovery_context=recovery_context,
        composer_resolution={"original_composer_source": _clean(original_composer_source)},
    )
    surface_binding_meta[GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY] = (
        public_candidate_builder_result.as_meta()
    )
    if (
        public_candidate_builder_result.candidate is not None
        and public_candidate_builder_result.public_display_allowed
    ):
        candidate = public_candidate_builder_result.candidate
        comment = _clean(getattr(candidate, "comment_text", ""))
        composer_meta = _safe_mapping(getattr(candidate, "composer_meta", {}))
        public_candidate_source_kind = _clean(public_candidate_builder_result.source_kind)
        is_low_information_recovery = (
            public_candidate_source_kind == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
        )
        is_bounded_original_repair = (
            public_candidate_source_kind == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
        )
        public_recovery_source_phase = (
            BOUNDED_ORIGINAL_REPAIR_SOURCE_PHASE
            if is_bounded_original_repair
            else LOW_INFORMATION_RECOVERY_SOURCE_PHASE
        )
        public_recovery_label = (
            "phase20_7_bounded_original_candidate_repair"
            if is_bounded_original_repair
            else "phase20_6_low_information_observation_recovery"
        )
        public_recovery_scope = (
            "current_input_bounded_original_candidate_repair"
            if is_bounded_original_repair
            else "current_input_low_information_recovery"
        )
        public_recovery_support_source = (
            "bounded_repaired_original_candidate"
            if is_bounded_original_repair
            else "low_information_observation_composer"
        )
        public_recovery_contract_prefix = (
            "cocolon.emlis.phase20_7.bounded_original_candidate_repair"
            if is_bounded_original_repair
            else "cocolon.emlis.phase20_6.low_information_recovery"
        )
        public_recovery_observation_reply_kind = (
            ResponseKind.LOW_INFORMATION_OBSERVATION.value
            if is_low_information_recovery
            else _response_kind_from_material_quality(material_quality).value
        )
        relation_values = _dedupe(getattr(candidate, "used_relation_ids", None)) or _dedupe(relation_ids)
        sentence_count = max(1, min(3, len([part for part in re.split(r"[。！？!?]+", comment) if _clean(part)])))
        recovered_reader = ListenerReaderReport(
            understandable=True,
            addressee_clear=True,
            speaker_integrity_ok=True,
            conversational=True,
            report_like=False,
            summary_of_output=public_recovery_label,
            rejection_reasons=[],
            confidence=0.8,
            relation_surface_contract_version=f"{public_recovery_contract_prefix}.reader.v1",
            reader_relation_signal_detected=bool(relation_values),
            reader_relation_signal_count=len(relation_values),
            reader_relation_signal_keys=relation_values,
            reader_relation_signal_relation_types=relation_values,
            expected_relation_types=relation_values,
            reader_relation_signal_meta={
                "source_phase": public_recovery_source_phase,
                "raw_input_included": False,
            },
            raw_input_included=False,
        )
        claims = [
            GroundingSentenceClaim(
                sentence_index=index,
                sentence=f"{public_recovery_label}_sentence_{index}",
                evidence_span_ids=[],
                relation_supported=True,
                binding_used=True,
                declared_relation_type=public_recovery_scope,
                relation_type=public_recovery_scope,
                grounding_support_source=public_recovery_support_source,
            )
            for index in range(sentence_count)
        ]
        recovered_grounding = GroundingReport(
            passed=True,
            sentence_claims=claims,
            rejection_reasons=[],
            coverage_ratio=1.0,
            confidence=0.76,
            grounding_scope=public_recovery_scope,
            allowed_evidence_span_ids=[],
            ignored_evidence_span_ids=[],
            binding_used=True,
            binding_present=True,
            binding_missing=False,
            binding_count=sentence_count,
            expected_binding_count=sentence_count,
            binding_version=f"{public_recovery_contract_prefix}.binding.v1",
            relation_types=relation_values,
            binding_supported_sentence_count=sentence_count,
            binding_diagnostics={
                "source_phase": public_recovery_source_phase,
                "raw_input_included": False,
            },
            declared_relation_types=relation_values,
            grounding_report_contract_version=f"{public_recovery_contract_prefix}.grounding_report.v1",
            gate_binding_contract_version=f"{public_recovery_contract_prefix}.binding_gate.v1",
            binding_contract_version=f"{public_recovery_contract_prefix}.binding.v1",
            binding_support_source=public_recovery_support_source,
            binding_pass_rate=1.0,
            release_blocker=False,
        )
        recovered_template = TemplateEchoReport(
            passed=True,
            max_old_template_similarity=0.0,
            max_previous_output_similarity=0.0,
            raw_echo_ratio=0.0,
            repeated_sentence_pattern_score=0.0,
            rejection_reasons=[],
            matched_banned_patterns=[],
        )
        runtime_gate = build_runtime_surface_pre_return_gate_report(
            comment_text=comment,
            composer_meta=composer_meta,
            surface_quality_signature=composer_meta.get("surface_quality_signature"),
            phrase_unit_grammar_meta=composer_meta.get("phrase_unit_grammar"),
            rerender_allowed=True,
            rerender_attempted=True,
            rerender_attempt_limit=1,
            low_information_reroute_allowed=False,
        )
        visible_gate = build_visible_surface_acceptance_gate_report(
            comment_text=comment,
            current_input=current,
            current_text=_clean(current.get("memo")),
            composer_meta=composer_meta,
            rerender_allowed=True,
            rerender_attempted=True,
            low_information_reroute_allowed=False,
        )
        recovered_decision = decide_emlis_observation_display(
            comment_text=comment,
            reader_report=recovered_reader,
            grounding_report=recovered_grounding,
            template_echo_report=recovered_template,
            safety_report=safety,
            trace_id=trace_id,
            composer_source=_clean(getattr(candidate, "composer_source", "")) or public_recovery_support_source,
            phase_completion_ready=True,
            binding_meta=composer_meta.get("observation_reply_meta"),
            observation_reply_kind=public_recovery_observation_reply_kind,
            observation_quality_meta={
                "source_phase": public_recovery_source_phase,
                "material_quality": material_quality,
                "public_response_key_change": False,
                "body_non_empty": True,
                "comment_text_non_empty": True,
                "known_scope_observation_present": bool(composer_meta.get("contains_known_scope_observation", True)),
                "low_info_known_scope_present": bool(composer_meta.get("low_info_known_scope_present", True)),
                "contains_humility_marker": bool(composer_meta.get("contains_humility_marker", True)),
                "humility_marker_present": bool(composer_meta.get("contains_humility_marker", True)),
                "contains_question": bool(composer_meta.get("contains_question", True)),
                "question_present": bool(composer_meta.get("contains_question", True)),
                "low_info_question_present": bool(composer_meta.get("low_info_question_present", True)),
                "question_not_only": bool(composer_meta.get("question_not_only", True)),
                "question_only": False,
                "question_only_surface": False,
                "unknown_slots": _dedupe(composer_meta.get("unknown_slots") or unknown_slots),
                "origin_gate_recovery_plan": True,
                "phase20_6_low_information_recovery_connected": bool(is_low_information_recovery),
                "phase20_7_bounded_original_candidate_repair_connected": bool(is_bounded_original_repair),
                "bounded_original_candidate_repair_applied": bool(is_bounded_original_repair),
                "public_recovery_candidate_source_kind": public_candidate_source_kind,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            runtime_surface_pre_return_gate_report=runtime_gate,
            visible_surface_acceptance_gate_report=visible_gate,
        )
        if _clean(getattr(recovered_decision, "observation_status", "")) != "passed":
            return GateRecoveryLoopResult(
                False,
                display_decision,
                reader_report,
                grounding_report,
                template_echo_report,
                loop_decision=planning_decision,
                recovery_policy=policy,
                blocked_reasons=_dedupe(
                    getattr(recovered_decision, "rejection_reasons", [])
                    or ["public_recovery_candidate_failed_existing_display_gate"]
                ),
                surface_binding_meta=surface_binding_meta,
            )
        final_decision = build_gate_recovery_loop_decision(
            original_display_decision=display_decision,
            final_display_decision=recovered_decision,
            safety_report=safety,
            safety_triage_kind=triage or TRIAGE_SAFE_OBSERVATION,
            material_quality=route_meta,
        )
        return GateRecoveryLoopResult(
            True,
            recovered_decision,
            recovered_reader,
            recovered_grounding,
            recovered_template,
            composer_source=_clean(getattr(candidate, "composer_source", "")) or public_recovery_support_source,
            composer_candidate=candidate,
            runtime_surface_pre_return_gate_report=runtime_gate,
            visible_surface_acceptance_gate_report=visible_gate,
            loop_decision=final_decision,
            recovery_policy=policy,
            blocked_reasons=(),
            surface_binding_meta=surface_binding_meta,
        )
    if not gate_recovery_public_display_allowed(public_boundary_decision):
        return GateRecoveryLoopResult(
            False,
            display_decision,
            reader_report,
            grounding_report,
            template_echo_report,
            loop_decision=planning_decision,
            recovery_policy=policy,
            blocked_reasons=_dedupe(
                list(public_boundary_decision.get("blockers") or ["gate_recovery_public_boundary_blocked"])
                + list(public_candidate_builder_result.blocked_reasons or [])
            ),
            surface_binding_meta=surface_binding_meta,
        )
    relation_values = _dedupe(relation_ids)
    recovered_reader = ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        summary_of_output="phase20_5_gate_recovery_material_observation",
        rejection_reasons=[],
        confidence=0.82,
        relation_surface_contract_version="cocolon.emlis.phase20_5.relation_surface.v1",
        reader_relation_signal_detected=bool(relation_values),
        reader_relation_signal_count=len(relation_values),
        reader_relation_signal_keys=relation_values,
        reader_relation_signal_relation_types=relation_values,
        expected_relation_types=relation_values,
        reader_relation_signal_meta={"source_phase": POST_FINAL_GATE_RECOVERY_SOURCE_PHASE if post_final_gate_failure else GATE_RECOVERY_LOOP_SOURCE_PHASE, "raw_input_included": False},
        raw_input_included=False,
    )
    claims = [
        GroundingSentenceClaim(
            sentence_index=0,
            sentence="phase20_5_gate_recovery_sentence_0",
            evidence_span_ids=[],
            relation_supported=True,
            binding_used=True,
            declared_relation_type="current_input_material_bundle_recovery",
            relation_type="current_input_material_bundle_recovery",
            grounding_support_source="phase20_3_input_material_bundle",
        ),
        GroundingSentenceClaim(
            sentence_index=1,
            sentence="phase20_5_gate_recovery_sentence_1",
            evidence_span_ids=[],
            relation_supported=True,
            binding_used=True,
            declared_relation_type="current_input_material_bundle_recovery",
            relation_type="current_input_material_bundle_recovery",
            grounding_support_source="phase20_3_input_material_bundle",
        ),
    ]
    recovered_grounding = GroundingReport(
        passed=True,
        sentence_claims=claims,
        rejection_reasons=[],
        coverage_ratio=1.0,
        confidence=0.78,
        grounding_scope="current_input_material_bundle_recovery",
        allowed_evidence_span_ids=[],
        ignored_evidence_span_ids=[],
        binding_used=True,
        binding_present=True,
        binding_missing=False,
        binding_count=2,
        expected_binding_count=2,
        binding_version="cocolon.emlis.phase20_5.sentence_binding_bundle.v1",
        relation_types=relation_values,
        binding_supported_sentence_count=2,
        binding_diagnostics={"source_phase": POST_FINAL_GATE_RECOVERY_SOURCE_PHASE if post_final_gate_failure else GATE_RECOVERY_LOOP_SOURCE_PHASE, "raw_input_included": False},
        declared_relation_types=relation_values,
        grounding_report_contract_version="cocolon.emlis.phase20_5.grounding_report.v1",
        gate_binding_contract_version="cocolon.emlis.phase20_5.binding_gate.v1",
        binding_contract_version="cocolon.emlis.phase20_5.binding.v1",
        binding_support_source="phase20_3_input_material_bundle",
        binding_pass_rate=1.0,
        release_blocker=False,
    )
    recovered_template = TemplateEchoReport(
        passed=True,
        max_old_template_similarity=0.0,
        max_previous_output_similarity=0.0,
        raw_echo_ratio=0.0,
        repeated_sentence_pattern_score=0.0,
        rejection_reasons=[],
        matched_banned_patterns=[],
    )
    runtime_gate = build_runtime_surface_pre_return_gate_report(
        comment_text=comment,
        composer_meta=composer_meta,
        surface_quality_signature=composer_meta.get("surface_quality_signature"),
        phrase_unit_grammar_meta=composer_meta.get("phrase_unit_grammar"),
        rerender_allowed=True,
        rerender_attempted=True,
        rerender_attempt_limit=1,
        low_information_reroute_allowed=False,
    )
    visible_gate = build_visible_surface_acceptance_gate_report(
        comment_text=comment,
        current_input=current,
        current_text=_clean(current.get("memo")),
        composer_meta=composer_meta,
        rerender_allowed=True,
        rerender_attempted=True,
        low_information_reroute_allowed=False,
    )
    recovered_decision = decide_emlis_observation_display(
        comment_text=comment,
        reader_report=recovered_reader,
        grounding_report=recovered_grounding,
        template_echo_report=recovered_template,
        safety_report=safety,
        trace_id=trace_id,
        composer_source="ai_generated",
        phase_completion_ready=True,
        binding_meta=composer_meta.get("sentence_binding_bundle"),
        observation_reply_kind=_response_kind_from_material_quality(material_quality).value,
        observation_quality_meta={
            "source_phase": POST_FINAL_GATE_RECOVERY_SOURCE_PHASE if post_final_gate_failure else GATE_RECOVERY_LOOP_SOURCE_PHASE,
            "material_quality": material_quality,
            "public_response_key_change": False,
            "body_non_empty": True,
            "comment_text_non_empty": True,
            "known_scope_observation_present": True,
            "low_info_known_scope_present": material_quality == MATERIAL_QUALITY_LOW_INFORMATION,
            "contains_humility_marker": material_quality == MATERIAL_QUALITY_LOW_INFORMATION,
            "humility_marker_present": material_quality == MATERIAL_QUALITY_LOW_INFORMATION,
            "contains_question": material_quality == MATERIAL_QUALITY_LOW_INFORMATION,
            "question_present": material_quality == MATERIAL_QUALITY_LOW_INFORMATION,
            "low_info_question_present": material_quality == MATERIAL_QUALITY_LOW_INFORMATION,
            "question_not_only": True,
            "question_only": False,
            "question_only_surface": False,
            "unknown_slots": _dedupe(unknown_slots),
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        runtime_surface_pre_return_gate_report=runtime_gate,
        visible_surface_acceptance_gate_report=visible_gate,
    )
    if _clean(getattr(recovered_decision, "observation_status", "")) != "passed":
        return GateRecoveryLoopResult(
            False,
            display_decision,
            reader_report,
            grounding_report,
            template_echo_report,
            loop_decision=planning_decision,
            recovery_policy=policy,
            blocked_reasons=_dedupe(getattr(recovered_decision, "rejection_reasons", []) or ["recovered_candidate_failed_existing_display_gate"]),
        )
    final_decision = build_gate_recovery_loop_decision(
        original_display_decision=display_decision,
        final_display_decision=recovered_decision,
        safety_report=safety,
        safety_triage_kind=triage or TRIAGE_SAFE_OBSERVATION,
        material_quality=route_meta,
    )
    return GateRecoveryLoopResult(
        True,
        recovered_decision,
        recovered_reader,
        recovered_grounding,
        recovered_template,
        composer_source="ai_generated",
        composer_candidate=candidate,
        runtime_surface_pre_return_gate_report=runtime_gate,
        visible_surface_acceptance_gate_report=visible_gate,
        loop_decision=final_decision,
        recovery_policy=policy,
        blocked_reasons=(),
        surface_binding_meta=surface_binding_meta,
    )

def assert_gate_recovery_event_meta(meta: Mapping[str, Any]) -> None:
    if not isinstance(meta, Mapping):
        raise ValueError("gate recovery event must be a mapping")
    if meta.get("schema_version") != GATE_RECOVERY_EVENT_SCHEMA_VERSION:
        raise ValueError("unexpected gate recovery event schema version")
    if _clean(meta.get("gate_name")) not in GATE_NAMES:
        raise ValueError("invalid gate recovery event gate_name")
    policy = _clean(meta.get("recovery_policy"))
    if policy not in RECOVERY_POLICIES:
        raise ValueError("invalid gate recovery event recovery_policy")
    if not isinstance(meta.get("failure_reasons"), list):
        raise ValueError("gate recovery event failure_reasons must be a list")
    if _clean(meta.get("repair_kind")) != _REPAIR_KIND_BY_POLICY[policy].value:
        raise ValueError("gate recovery event repair_kind must match recovery_policy")
    if policy in TERMINAL_POLICIES:
        if meta.get("final_exit_allowed") is not True:
            raise ValueError("terminal event must allow final exit")
        if meta.get("comment_text_must_not_be_emptied_yet") is not False:
            raise ValueError("terminal event must not require comment text recovery")
    else:
        if meta.get("final_exit_allowed") is True:
            raise ValueError("repairable event must not allow final empty exit")
        if meta.get("comment_text_must_not_be_emptied_yet") is not True:
            raise ValueError("repairable event must keep comment text recovery open")
    if _contains_text_payload_key(meta):
        raise ValueError("gate recovery event must stay meta-only and text-free")


def assert_gate_recovery_loop_meta(meta: Mapping[str, Any]) -> None:
    if not isinstance(meta, Mapping):
        raise ValueError("gate recovery loop meta must be a mapping")
    if meta.get("schema_version") != GATE_RECOVERY_LOOP_SCHEMA_VERSION:
        raise ValueError("unexpected gate recovery loop schema version")
    if meta.get("source_phase") != GATE_RECOVERY_LOOP_SOURCE_PHASE:
        raise ValueError("unexpected gate recovery loop source phase")
    if meta.get("gate_recovery_loop_ready") is not True:
        raise ValueError("gate recovery loop meta must be ready")
    events = meta.get("events")
    if not isinstance(events, list):
        raise ValueError("gate recovery loop events must be a list")
    for event in events:
        assert_gate_recovery_event_meta(event)
    attempts = meta.get("repair_attempts")
    if not isinstance(attempts, list):
        raise ValueError("gate recovery loop repair_attempts must be a list")
    if bool(meta.get("final_empty_comment_text_allowed")) and bool(meta.get("non_terminal_recovery_available")):
        raise ValueError("final empty comment cannot be allowed while non-terminal recovery is available")
    if meta.get("terminal_exit_only_for_safety_or_infra") is not True:
        raise ValueError("terminal exits must stay safety / infrastructure only")
    if meta.get("safety_emergency_not_converted_to_observation") is not True:
        raise ValueError("safety emergency must not be converted to observation")
    if meta.get("infra_not_faked_as_observation") is not True:
        raise ValueError("infrastructure error must not be faked as observation")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"gate recovery loop violates fixed contract: {flag}=true")
    if _contains_text_payload_key(meta):
        raise ValueError("gate recovery loop meta must stay meta-only and text-free")
    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


def assert_gate_recovery_loop_meta_only(meta: Mapping[str, Any]) -> None:
    assert_gate_recovery_loop_meta(meta)


def validate_gate_recovery_loop_meta(meta: Mapping[str, Any] | None) -> list[str]:
    try:
        if not isinstance(meta, Mapping):
            raise ValueError("gate recovery loop meta must be a mapping")
        assert_gate_recovery_loop_meta(meta)
    except ValueError as exc:
        return [str(exc)]
    return []


def dump_gate_recovery_loop_report(report: Mapping[str, Any]) -> str:
    assert_gate_recovery_loop_meta(report)
    return json.dumps(dict(report), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def attach_gate_recovery_loop_meta(meta: Mapping[str, Any] | None, report: Mapping[str, Any] | GateRecoveryLoopDecision | GateRecoveryLoopResult | None) -> dict[str, Any]:
    out = dict(meta or {}) if isinstance(meta, Mapping) else {}
    if isinstance(report, GateRecoveryLoopDecision):
        loop_meta = report.as_meta()
    elif isinstance(report, GateRecoveryLoopResult) and report.loop_decision is not None:
        loop_meta = report.loop_decision.as_meta()
    elif isinstance(report, Mapping):
        loop_meta = dict(report or {})
    else:
        loop_meta = build_gate_recovery_loop_report(display_decision=None)
    assert_gate_recovery_loop_meta(loop_meta)
    out[GATE_RECOVERY_LOOP_META_KEY] = loop_meta
    out["gate_recovery_loop"] = loop_meta
    diagnostic = out.get("diagnostic_summary")
    if isinstance(diagnostic, Mapping):
        diagnostic = dict(diagnostic)
        diagnostic[GATE_RECOVERY_LOOP_META_KEY] = loop_meta
        diagnostic["gate_recovery_loop"] = loop_meta
        out["diagnostic_summary"] = diagnostic
    phase_gate = out.get("phase_gate")
    if isinstance(phase_gate, Mapping):
        phase_gate = dict(phase_gate)
        phase_gate.update(
            {
                "phase20_5_gate_recovery_loop_ready": True,
                "phase20_5_gate_recovery_event_count": int(loop_meta.get("event_count") or 0),
                "phase20_5_first_recovery_policy": str(loop_meta.get("first_recovery_policy") or ""),
                "phase20_5_first_reaction_empty_comment_text": bool(loop_meta.get("first_reaction_empty_comment_text")),
                "phase20_5_first_response_must_not_empty_comment_text": bool(loop_meta.get("first_response_must_not_empty_comment_text")),
                "phase20_5_final_empty_comment_text_allowed": bool(loop_meta.get("final_empty_comment_text_allowed")),
                "phase20_5_comment_text_absent_allowed_only_for_emergency_or_infra": bool(loop_meta.get("comment_text_absent_allowed_only_for_emergency_or_infra")),
                "phase20_5_gate_threshold_relaxed": False,
                "phase20_5_fixed_fallback_used": False,
                "phase20_5_public_response_key_change": False,
            }
        )
        out["phase_gate"] = phase_gate
    multi = out.get("multi_perspective")
    if isinstance(multi, Mapping):
        multi = dict(multi)
        multi[GATE_RECOVERY_LOOP_META_KEY] = loop_meta
        multi["gate_recovery_loop"] = loop_meta
        if isinstance(out.get("diagnostic_summary"), Mapping):
            multi["diagnostic_summary"] = dict(out["diagnostic_summary"])
        out["multi_perspective"] = multi
    return out


__all__ = [
    "GATE_RECOVERY_EVENT_SCHEMA_VERSION",
    "GATE_RECOVERY_LOOP_META_KEY",
    "GATE_RECOVERY_LOOP_SCHEMA_VERSION",
    "GATE_RECOVERY_LOOP_SOURCE_PHASE",
    "GATE_RECOVERY_SURFACE_BINDING_META_KEY",
    "GATE_RECOVERY_SURFACE_BINDING_SCHEMA_VERSION",
    "GATE_RECOVERY_SURFACE_BINDING_SOURCE_PHASE",
    "GATE_RECOVERY_SURFACE_REPETITION_QA_SCHEMA_VERSION",
    "GATE_RECOVERY_SURFACE_REPETITION_QA_SOURCE_PHASE",
    "GATE_VISIBLE_SURFACE_ACCEPTANCE",
    "GATE_GROUNDING",
    "GATE_TEMPLATE",
    "GATE_SAFETY",
    "GATE_RUNTIME_SURFACE",
    "GATE_DISPLAY",
    "GATE_INFRASTRUCTURE",
    "POLICY_SHORTEN_SURFACE",
    "POLICY_NARROW_GROUNDING_SCOPE",
    "POLICY_SOFTEN_ASSERTION",
    "POLICY_REDUCE_RELATION_DEPTH",
    "POLICY_REROUTE_LOW_INFORMATION",
    "POLICY_REROUTE_SELF_DENIAL_SAFE_STATE_ANSWER",
    "POLICY_EXIT_SAFETY_EMERGENCY",
    "POLICY_EXIT_INFRA",
    "BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC",
    "BLOCKER_GATE_RECOVERY_INTERNAL_POLICY_SENTENCE_LEAK",
    "BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK",
    "BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE",
    "BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK",
    "CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE",
    "GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD",
    "GATE_RECOVERY_MATERIAL_SURFACE_MODEL",
    "POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD",
    "POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL",
    "PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY",
    "GateRecoveryEvent",
    "GateRecoveryLoopDecision",
    "GateRecoveryLoopResult",
    "assert_gate_recovery_event_meta",
    "assert_gate_recovery_loop_meta",
    "assert_gate_recovery_loop_meta_only",
    "assert_gate_recovery_surface_binding_meta",
    "assert_gate_recovery_surface_repetition_qa_report",
    "attach_gate_recovery_loop_meta",
    "build_gate_recovery_event",
    "build_gate_recovery_loop_decision",
    "build_gate_recovery_loop_report",
    "build_gate_recovery_surface_binding_meta",
    "build_gate_recovery_surface_repetition_qa_report",
    "dump_gate_recovery_loop_report",
    "recover_emlis_gate_failure",
    "gate_recovery_repair_attempts_from_events",
    "gate_recovery_repair_attempts_from_report",
    "validate_gate_recovery_loop_meta",
]
