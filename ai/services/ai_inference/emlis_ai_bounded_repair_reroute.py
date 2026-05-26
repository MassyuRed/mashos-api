# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step7 bounded repair / reroute decision contract for EmlisAI.

This module defines the control-plane boundary used after Runtime Surface
Pre-Return Gate failures.  It does not render text, does not change public API
or RN response shape, does not call external AI, and does not turn arbitrary
failed candidates into displayed observations.  It only decides whether the
failed candidate may be retried through the bounded Shallow V2 path, safely
rerouted to the low-information branch, or kept fail-closed.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_ALLOW,
    ACTION_BLOCK,
    ACTION_FAIL_CLOSED,
    ACTION_RERENDER_SHALLOW_V2,
    ACTION_REROUTE_LOW_INFORMATION,
    RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
    assert_runtime_surface_pre_return_gate_meta_only,
)
from emlis_ai_visible_surface_acceptance_gate import (
    ACTION_ALLOW as VISIBLE_SURFACE_ACTION_ALLOW,
    ACTION_BLOCK as VISIBLE_SURFACE_ACTION_BLOCK,
    ACTION_FAIL_CLOSED as VISIBLE_SURFACE_ACTION_FAIL_CLOSED,
    ACTION_RERENDER_SURFACE as VISIBLE_SURFACE_ACTION_RERENDER_SURFACE,
    ACTION_REROUTE_LOW_INFORMATION as VISIBLE_SURFACE_ACTION_REROUTE_LOW_INFORMATION,
    ACTION_WARN as VISIBLE_SURFACE_ACTION_WARN,
    CLASSIFICATION_PASS as VISIBLE_SURFACE_CLASSIFICATION_PASS,
    CLASSIFICATION_RED as VISIBLE_SURFACE_CLASSIFICATION_RED,
    CLASSIFICATION_REPAIR_REQUIRED as VISIBLE_SURFACE_CLASSIFICATION_REPAIR_REQUIRED,
    VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
    assert_visible_surface_acceptance_gate_meta_only,
)

BOUNDED_REPAIR_REROUTE_VERSION: Final = "emlis.bounded_repair_reroute.v1"
BOUNDED_REPAIR_REROUTE_STEP: Final = "Step7_Bounded_Repair_Reroute"
BOUNDED_REPAIR_REROUTE_SOURCE: Final = "emlis_ai_bounded_repair_reroute"

ACTION_NO_REPAIR: Final = "no_repair"
ACTION_RERENDER_SURFACE: Final = VISIBLE_SURFACE_ACTION_RERENDER_SURFACE
BOUNDED_REPAIR_REROUTE_ACTIONS: Final = (
    ACTION_NO_REPAIR,
    ACTION_RERENDER_SHALLOW_V2,
    ACTION_RERENDER_SURFACE,
    ACTION_REROUTE_LOW_INFORMATION,
    ACTION_BLOCK,
    ACTION_FAIL_CLOSED,
)

_UNAVAILABLE_SOURCES: Final = frozenset({"", "unavailable", "empty"})
_SAFETY_REASON_MARKERS: Final = frozenset(
    {
        "safety_boundary",
        "safety_blocked",
        "self_harm",
        "suicide",
        "harm",
        "violence",
    }
)
_NON_REPAIRABLE_REJECTION_REASONS: Final = frozenset(
    {
        "unsupported_sentence",
        "graph_evidence_not_used",
        "core_relation_not_reflected",
        "phase8_body_too_short",
        "rollout_stage_off",
        "rollout_stage_not_matched",
        "release_gate_blocked",
        "phase7_rollout_gate_blocked",
        "composer_resolution_pre_connection_rollout_stop",
        "composer_resolution_blocked_rollout",
        "composer_resolution_blocked_ap0",
        "complete_initial_ap0_not_green",
        "complete_initial_rollout_not_allowed",
    }
)
_SAFE_UNIT_SHORTAGE_REASONS: Final = frozenset(
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
    }
)
_ACTUAL_SURFACE_FATAL_REASON_MARKERS: Final = frozenset(
    {
        "surface_template_major",
        "generic_center_phrase",
        "same_connector_run",
        "surface_template_skeleton",
        "connector_repetition",
        "same_connector_repetition",
        "surface_connector_repetition",
        "surface_grammar_warning",
        "grammar_warning",
        "malformed_nominalization_risk",
        "malformed_phrase_unit",
        "unsafe_shallow_phrase_unit",
    }
)
_ACTUAL_SURFACE_FATAL_REASON_PREFIXES: Final = (
    "malformed_nominalization_",
)
_VISIBLE_SURFACE_REPAIRABLE_REASONS: Final = frozenset(
    {
        "malformed_nominalization_conditional_fragment",
        "malformed_nominalization_obligation_fragment",
        "malformed_nominalization_prediction_noun_fragment",
        "residual_koto_splice_fragment",
        "long_clause_koto_attachment_risk",
        "surface_relation_skeleton_major",
        "surface_relation_skeleton_stack",
        "analytic_register_leak",
        "emotion_focus_unbridged_secondary",
        "positive_tone_over_burden_without_anchor",
    }
)
_VISIBLE_SURFACE_REPAIRABLE_REASON_PREFIXES: Final = (
    "malformed_nominalization_",
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
        "inputFeedbackComment",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "realized_text",
        "body",
        "text",
        "sentence",
        "sentences",
        "phrase",
        "raw_quote",
        "raw_quotes",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "public_status_extended",
        "observation_status_enum_extended",
        "public_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "reader_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "fixed_fallback_used",
        "legacy_safe_fallback_used",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


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
        item = _clean(raw)
        if item and item not in out:
            out.append(item)
    return out


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _has_safety_reason(reasons: Iterable[Any] | Any | None) -> bool:
    for reason in _dedupe(reasons):
        lowered = reason.lower()
        if any(marker in lowered for marker in _SAFETY_REASON_MARKERS):
            return True
    return False


def _actual_surface_fatal_reasons(reasons: Iterable[Any] | Any | None) -> list[str]:
    """Return surface failures that describe rendered-text quality, not empty placeholders."""

    out: list[str] = []
    for reason in _dedupe(reasons):
        if reason in _ACTUAL_SURFACE_FATAL_REASON_MARKERS or any(
            reason.startswith(prefix) for prefix in _ACTUAL_SURFACE_FATAL_REASON_PREFIXES
        ):
            out.append(reason)
    return out


def _runtime_gate_from_display_decision(display_decision: Any) -> dict[str, Any]:
    gate_trace = getattr(display_decision, "gate_trace", None)
    if not isinstance(gate_trace, Mapping):
        return {}
    direct = gate_trace.get("runtime_surface_pre_return_gate")
    if isinstance(direct, Mapping):
        return dict(direct)
    display_gate = gate_trace.get("display_gate")
    if isinstance(display_gate, Mapping) and display_gate.get("runtime_surface_pre_return_gate_evaluated"):
        return {
            "version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
            "evaluated": True,
            "passed": bool(display_gate.get("runtime_surface_pre_return_gate_passed")),
            "action": _clean(display_gate.get("runtime_surface_pre_return_gate_action")) or ACTION_BLOCK,
            "rejection_reasons": _dedupe(display_gate.get("runtime_surface_pre_return_gate_rejection_reasons")),
            "raw_input_included": False,
            "comment_text_body_included": False,
            "display_gate_relaxed": False,
        }
    return {}




def _visible_gate_from_display_decision(display_decision: Any) -> dict[str, Any]:
    gate_trace = getattr(display_decision, "gate_trace", None)
    if not isinstance(gate_trace, Mapping):
        return {}
    direct = gate_trace.get("visible_surface_acceptance_gate") or gate_trace.get("visible_surface_acceptance")
    if isinstance(direct, Mapping):
        return dict(direct)
    display_gate = gate_trace.get("display_gate")
    if isinstance(display_gate, Mapping) and display_gate.get("visible_surface_acceptance_gate_evaluated"):
        passed = bool(
            display_gate.get("visible_surface_acceptance_gate_report_passed")
            if "visible_surface_acceptance_gate_report_passed" in display_gate
            else display_gate.get("visible_surface_acceptance_gate_passed")
        )
        action = _clean(display_gate.get("visible_surface_acceptance_gate_action"))
        classification = _clean(display_gate.get("visible_surface_acceptance_gate_classification"))
        return {
            "version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
            "schema_version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
            "evaluated": True,
            "passed": passed,
            "blocked": not passed,
            "classification": classification or (VISIBLE_SURFACE_CLASSIFICATION_PASS if passed else VISIBLE_SURFACE_CLASSIFICATION_RED),
            "action": action or (VISIBLE_SURFACE_ACTION_ALLOW if passed else VISIBLE_SURFACE_ACTION_BLOCK),
            "rejection_reasons": _dedupe(display_gate.get("visible_surface_acceptance_gate_rejection_reasons")),
            "warning_reasons": [],
            "raw_input_included": False,
            "raw_text_included": False,
            "input_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "rn_visible_contract_changed": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "gate_relaxed": False,
            "fixed_sentence_template_added": False,
            "input_specific_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
    return {}


def _sanitize_runtime_gate(value: Any) -> tuple[dict[str, Any], list[str]]:
    if not value:
        return {}, []
    if not isinstance(value, Mapping):
        return {}, ["runtime_surface_pre_return_gate_invalid"]
    gate = dict(value)
    gate.setdefault("version", RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION)
    gate.setdefault("evaluated", True)
    gate.setdefault("passed", False)
    gate.setdefault("action", ACTION_BLOCK)
    gate.setdefault("rejection_reasons", [])
    gate.setdefault("raw_input_included", False)
    gate.setdefault("comment_text_body_included", False)
    gate.setdefault("display_gate_relaxed", False)
    try:
        assert_runtime_surface_pre_return_gate_meta_only(gate, source="bounded_repair_reroute.runtime_surface_gate")
    except Exception:
        return {}, ["runtime_surface_pre_return_gate_invalid"]
    return gate, []


def _sanitize_visible_gate(value: Any) -> tuple[dict[str, Any], list[str]]:
    if not value:
        return {}, []
    if not isinstance(value, Mapping):
        return {}, ["visible_surface_acceptance_gate_invalid"]
    gate = dict(value)
    gate.setdefault("version", VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION)
    gate.setdefault("schema_version", gate.get("version") or VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION)
    gate.setdefault("evaluated", True)
    gate.setdefault("passed", False)
    gate.setdefault("blocked", not bool(gate.get("passed")))
    gate.setdefault("classification", VISIBLE_SURFACE_CLASSIFICATION_RED)
    gate.setdefault("action", VISIBLE_SURFACE_ACTION_BLOCK)
    gate.setdefault("rejection_reasons", [])
    gate.setdefault("warning_reasons", [])
    gate.setdefault("raw_input_included", False)
    gate.setdefault("raw_text_included", False)
    gate.setdefault("input_text_included", False)
    gate.setdefault("comment_text_included", False)
    gate.setdefault("comment_text_body_included", False)
    gate.setdefault("rn_visible_contract_changed", False)
    gate.setdefault("response_shape_changed", False)
    gate.setdefault("public_response_key_change", False)
    gate.setdefault("api_route_changed", False)
    gate.setdefault("db_physical_name_changed", False)
    gate.setdefault("display_gate_relaxed", False)
    gate.setdefault("grounding_gate_relaxed", False)
    gate.setdefault("template_gate_relaxed", False)
    gate.setdefault("reader_gate_relaxed", False)
    gate.setdefault("gate_relaxed", False)
    gate.setdefault("fixed_sentence_template_added", False)
    gate.setdefault("input_specific_template_used", False)
    gate.setdefault("external_ai_used", False)
    gate.setdefault("local_llm_used", False)
    try:
        assert_visible_surface_acceptance_gate_meta_only(
            gate,
            source="bounded_repair_reroute.visible_surface_acceptance_gate",
        )
    except Exception:
        return {}, ["visible_surface_acceptance_gate_invalid"]
    return gate, []


def _visible_surface_blocks(gate: Mapping[str, Any] | None) -> bool:
    if not isinstance(gate, Mapping) or not gate:
        return False
    action = _clean(gate.get("action"))
    classification = _clean(gate.get("classification"))
    if action in {VISIBLE_SURFACE_ACTION_ALLOW, VISIBLE_SURFACE_ACTION_WARN}:
        return False
    if classification in {VISIBLE_SURFACE_CLASSIFICATION_RED, VISIBLE_SURFACE_CLASSIFICATION_REPAIR_REQUIRED}:
        return True
    if action in {
        VISIBLE_SURFACE_ACTION_RERENDER_SURFACE,
        VISIBLE_SURFACE_ACTION_REROUTE_LOW_INFORMATION,
        VISIBLE_SURFACE_ACTION_BLOCK,
        VISIBLE_SURFACE_ACTION_FAIL_CLOSED,
    }:
        return True
    return bool(not gate.get("passed"))


def _visible_surface_repairable_reasons(reasons: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for reason in _dedupe(reasons):
        if reason in _VISIBLE_SURFACE_REPAIRABLE_REASONS or any(
            reason.startswith(prefix) for prefix in _VISIBLE_SURFACE_REPAIRABLE_REASON_PREFIXES
        ):
            out.append(reason)
    return out


@dataclass(frozen=True)
class BoundedRepairRerouteDecision:
    action: str
    allowed: bool = False
    runtime_surface_gate_evaluated: bool = False
    runtime_surface_gate_passed: bool = False
    runtime_surface_gate_action: str = ""
    visible_surface_gate_evaluated: bool = False
    visible_surface_gate_passed: bool = False
    visible_surface_gate_action: str = ""
    visible_surface_gate_classification: str = ""
    rerender_attempted: bool = False
    rerender_attempt_limit: int = 1
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)
    repair_reasons: tuple[str, ...] = field(default_factory=tuple)
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)
    low_information_reroute_allowed: bool = False
    shallow_v2_rerender_allowed: bool = False
    surface_rerender_allowed: bool = False

    def as_meta(self) -> dict[str, Any]:
        action = _clean(self.action) or ACTION_NO_REPAIR
        out = {
            "version": BOUNDED_REPAIR_REROUTE_VERSION,
            "schema_version": BOUNDED_REPAIR_REROUTE_VERSION,
            "source": BOUNDED_REPAIR_REROUTE_SOURCE,
            "source_step": BOUNDED_REPAIR_REROUTE_STEP,
            "step": BOUNDED_REPAIR_REROUTE_STEP,
            "step7_bounded_repair_reroute_ready": True,
            "evaluated": True,
            "allowed": bool(self.allowed),
            "passed": bool(self.allowed or action == ACTION_NO_REPAIR),
            "action": action,
            "runtime_surface_gate_evaluated": bool(self.runtime_surface_gate_evaluated),
            "runtime_surface_gate_passed": bool(self.runtime_surface_gate_passed),
            "runtime_surface_gate_action": self.runtime_surface_gate_action,
            "visible_surface_gate_evaluated": bool(self.visible_surface_gate_evaluated),
            "visible_surface_gate_passed": bool(self.visible_surface_gate_passed),
            "visible_surface_gate_action": self.visible_surface_gate_action,
            "visible_surface_gate_classification": self.visible_surface_gate_classification,
            "rerender_attempted": bool(self.rerender_attempted),
            "rerender_attempt_limit": max(0, min(1, int(self.rerender_attempt_limit or 0))),
            "shallow_v2_rerender_allowed": bool(self.shallow_v2_rerender_allowed),
            "surface_rerender_allowed": bool(self.surface_rerender_allowed),
            "visible_surface_rerender_allowed": bool(self.surface_rerender_allowed),
            "low_information_reroute_allowed": bool(self.low_information_reroute_allowed),
            "rejection_reasons": list(self.rejection_reasons),
            "repair_reasons": list(self.repair_reasons),
            "blocked_reasons": list(self.blocked_reasons),
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "gate_relaxed": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "fixed_fallback_used": False,
            "legacy_safe_fallback_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "input_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
        assert_bounded_repair_reroute_meta_only(out)
        return out


def assert_bounded_repair_reroute_meta_only(value: Mapping[str, Any]) -> None:
    data = dict(value or {})
    required = {
        "version",
        "evaluated",
        "allowed",
        "action",
        "rejection_reasons",
        "blocked_reasons",
        "raw_input_included",
        "comment_text_body_included",
        "display_gate_relaxed",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"bounded repair/reroute meta missing required keys: {missing}")
    if _contains_text_payload_key(data):
        raise ValueError("bounded repair/reroute meta must not include raw text payload keys")
    action = _clean(data.get("action"))
    if action not in BOUNDED_REPAIR_REROUTE_ACTIONS:
        raise ValueError(f"invalid bounded repair/reroute action: {action}")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if data.get(key) is True:
            raise ValueError(f"bounded repair/reroute violates fixed contract: {key}=true")


def decide_bounded_repair_reroute(
    *,
    display_decision: Any,
    composer_source: Any = "",
    safety_report: Any = None,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
    repair_allowed: bool = True,
) -> BoundedRepairRerouteDecision:
    """Return the bounded action for a failed public candidate.

    Runtime Surface Gate failures may request one bounded Shallow V2 rerender.
    Step6 also lets a Visible Surface Acceptance Gate ``rerender_surface`` action
    enter the same one-attempt loop. Safety blocks, unavailable source,
    incomplete phase, invalid gate reports, and already-rerendered candidates
    remain fail-closed and never become ``passed + comment_text`` here.
    """

    status = _clean(getattr(display_decision, "observation_status", ""))
    source = _clean(composer_source)
    display_reasons = _dedupe(getattr(display_decision, "rejection_reasons", []) or [])
    explicit_runtime_surface_gate = runtime_surface_pre_return_gate_report is not None
    runtime_gate, runtime_invalid_reasons = _sanitize_runtime_gate(
        runtime_surface_pre_return_gate_report
        if explicit_runtime_surface_gate
        else _runtime_gate_from_display_decision(display_decision)
    )
    explicit_visible_surface_gate = visible_surface_acceptance_gate_report is not None
    visible_gate, visible_invalid_reasons = _sanitize_visible_gate(
        visible_surface_acceptance_gate_report
        if explicit_visible_surface_gate
        else _visible_gate_from_display_decision(display_decision)
    )
    invalid_reasons = _dedupe([*runtime_invalid_reasons, *visible_invalid_reasons])

    runtime_gate_reasons = _dedupe(runtime_gate.get("rejection_reasons") if runtime_gate else [])
    visible_gate_reasons = _dedupe(visible_gate.get("rejection_reasons") if visible_gate else [])
    visible_action = _clean(visible_gate.get("action")) if visible_gate else ""
    visible_classification = _clean(visible_gate.get("classification")) if visible_gate else ""
    visible_blocks = _visible_surface_blocks(visible_gate)
    visible_gate_reasons_with_markers = list(visible_gate_reasons)
    if visible_blocks and "visible_surface_acceptance_gate_failed" not in visible_gate_reasons_with_markers:
        visible_gate_reasons_with_markers.insert(0, "visible_surface_acceptance_gate_failed")
    if visible_blocks and visible_action and visible_action != VISIBLE_SURFACE_ACTION_ALLOW:
        visible_gate_reasons_with_markers.append(f"visible_surface_acceptance_gate_action_{visible_action}")
    if visible_blocks and visible_classification:
        visible_gate_reasons_with_markers.append(f"visible_surface_acceptance_gate_classification_{visible_classification}")
    visible_gate_reasons_with_markers = _dedupe(visible_gate_reasons_with_markers)

    reasons = _dedupe([*display_reasons, *runtime_gate_reasons, *visible_gate_reasons_with_markers, *invalid_reasons])
    gate_action = _clean(runtime_gate.get("action")) if runtime_gate else ""
    gate_evaluated = bool(runtime_gate.get("evaluated")) if runtime_gate else bool(runtime_invalid_reasons)
    gate_passed = bool(runtime_gate.get("passed")) if runtime_gate else False
    visible_gate_evaluated = bool(visible_gate.get("evaluated")) if visible_gate else bool(visible_invalid_reasons)
    visible_gate_passed = bool(visible_gate.get("passed")) if visible_gate else False
    runtime_rerender_attempted = bool(runtime_gate.get("rerender_attempted")) if runtime_gate else False
    visible_rerender_attempted = bool(visible_gate.get("rerender_attempted")) if visible_gate else False
    rerender_attempted = bool(runtime_rerender_attempted or visible_rerender_attempted)
    rerender_attempt_limit = 1
    for candidate_gate in (runtime_gate, visible_gate):
        if not candidate_gate:
            continue
        try:
            rerender_attempt_limit = min(rerender_attempt_limit, max(0, min(1, int(candidate_gate.get("rerender_attempt_limit", 1) or 0))))
        except Exception:
            rerender_attempt_limit = min(rerender_attempt_limit, 1)

    base_kwargs = {
        "runtime_surface_gate_evaluated": gate_evaluated,
        "runtime_surface_gate_passed": gate_passed,
        "runtime_surface_gate_action": gate_action,
        "visible_surface_gate_evaluated": visible_gate_evaluated,
        "visible_surface_gate_passed": visible_gate_passed,
        "visible_surface_gate_action": visible_action,
        "visible_surface_gate_classification": visible_classification,
        "rerender_attempted": rerender_attempted,
        "rerender_attempt_limit": rerender_attempt_limit,
        "rejection_reasons": tuple(reasons),
    }

    if not repair_allowed:
        return BoundedRepairRerouteDecision(
            action=ACTION_BLOCK,
            blocked_reasons=tuple(_dedupe(["repair_disabled_by_runtime_contract", *reasons])),
            **base_kwargs,
        )
    if status == "passed":
        return BoundedRepairRerouteDecision(
            action=ACTION_NO_REPAIR,
            repair_reasons=("already_passed",),
            **base_kwargs,
        )
    if (safety_report is not None and bool(getattr(safety_report, "requires_block", False))) or status == "safety_blocked" or _has_safety_reason(reasons):
        return BoundedRepairRerouteDecision(
            action=ACTION_BLOCK,
            blocked_reasons=tuple(_dedupe(["safety_blocked_no_reroute", *reasons])),
            **base_kwargs,
        )
    if invalid_reasons:
        return BoundedRepairRerouteDecision(
            action=ACTION_FAIL_CLOSED,
            blocked_reasons=tuple(_dedupe([*invalid_reasons, "bounded_repair_reroute_fail_closed"])),
            **base_kwargs,
        )
    if not runtime_gate and not visible_gate:
        return BoundedRepairRerouteDecision(
            action=ACTION_NO_REPAIR,
            repair_reasons=("no_surface_gate_failure",),
            **base_kwargs,
        )
    if (not runtime_gate or gate_passed or gate_action == ACTION_ALLOW) and (
        not visible_gate or not visible_blocks or visible_action in {VISIBLE_SURFACE_ACTION_ALLOW, VISIBLE_SURFACE_ACTION_WARN}
    ):
        return BoundedRepairRerouteDecision(
            action=ACTION_NO_REPAIR,
            repair_reasons=("surface_gates_passed",),
            **base_kwargs,
        )

    actual_surface_fatals = _actual_surface_fatal_reasons(reasons)
    placeholder_runtime_gate_without_candidate = (
        runtime_gate
        and gate_action == ACTION_FAIL_CLOSED
        and not visible_blocks
        and not actual_surface_fatals
        and (
            source in _UNAVAILABLE_SOURCES
            or source != "ai_generated"
            or "composer_source_unavailable" in reasons
            or "empty_comment_text_without_candidate" in reasons
        )
        and (
            "surface_signature_unavailable" in reasons
            or "empty_comment_text_without_candidate" in reasons
            or "empty_comment_text" in reasons
            or "empty_text" in reasons
        )
    )
    if placeholder_runtime_gate_without_candidate:
        return BoundedRepairRerouteDecision(
            action=ACTION_NO_REPAIR,
            repair_reasons=("placeholder_runtime_surface_gate_without_candidate",),
            **base_kwargs,
        )
    if source != "ai_generated" or source in _UNAVAILABLE_SOURCES:
        return BoundedRepairRerouteDecision(
            action=ACTION_BLOCK,
            blocked_reasons=tuple(_dedupe(["source_unavailable_or_non_ai_no_surface_reroute", *reasons])),
            **base_kwargs,
        )
    if "phase_not_complete" in reasons or "composer_source_unavailable" in reasons:
        return BoundedRepairRerouteDecision(
            action=ACTION_BLOCK,
            blocked_reasons=tuple(_dedupe(["phase_or_source_not_repairable", *reasons])),
            **base_kwargs,
        )
    non_repairable = [reason for reason in reasons if reason in _NON_REPAIRABLE_REJECTION_REASONS]
    if non_repairable:
        return BoundedRepairRerouteDecision(
            action=ACTION_BLOCK,
            blocked_reasons=tuple(_dedupe(["non_repairable_rejection_not_rerouted", *non_repairable])),
            **base_kwargs,
        )
    if gate_action == ACTION_RERENDER_SHALLOW_V2 and not runtime_rerender_attempted:
        return BoundedRepairRerouteDecision(
            action=ACTION_RERENDER_SHALLOW_V2,
            repair_reasons=("bounded_shallow_v2_rerender_required",),
            shallow_v2_rerender_allowed=True,
            **base_kwargs,
        )
    visible_repairable = _visible_surface_repairable_reasons(reasons)
    if visible_action == ACTION_RERENDER_SURFACE and visible_blocks:
        if not visible_rerender_attempted:
            return BoundedRepairRerouteDecision(
                action=ACTION_RERENDER_SURFACE,
                repair_reasons=tuple(
                    _dedupe(["bounded_visible_surface_rerender_required", *(visible_repairable or visible_gate_reasons_with_markers)])
                ),
                surface_rerender_allowed=True,
                **base_kwargs,
            )
        return BoundedRepairRerouteDecision(
            action=ACTION_BLOCK,
            blocked_reasons=tuple(_dedupe(["visible_surface_repair_not_available", *reasons])),
            **base_kwargs,
        )
    safe_unit_shortage = bool(set(reasons).intersection(_SAFE_UNIT_SHORTAGE_REASONS))
    if gate_action == ACTION_REROUTE_LOW_INFORMATION or visible_action == VISIBLE_SURFACE_ACTION_REROUTE_LOW_INFORMATION or safe_unit_shortage:
        return BoundedRepairRerouteDecision(
            action=ACTION_REROUTE_LOW_INFORMATION,
            allowed=True,
            repair_reasons=tuple(_dedupe(["bounded_low_information_reroute", *reasons])),
            low_information_reroute_allowed=True,
            **base_kwargs,
        )
    return BoundedRepairRerouteDecision(
        action=ACTION_BLOCK if gate_action != ACTION_FAIL_CLOSED and visible_action != VISIBLE_SURFACE_ACTION_FAIL_CLOSED else ACTION_FAIL_CLOSED,
        blocked_reasons=tuple(_dedupe(["bounded_surface_repair_not_available", *reasons])),
        **base_kwargs,
    )


__all__ = [
    "ACTION_NO_REPAIR",
    "ACTION_RERENDER_SURFACE",
    "BOUNDED_REPAIR_REROUTE_ACTIONS",
    "BOUNDED_REPAIR_REROUTE_SOURCE",
    "BOUNDED_REPAIR_REROUTE_STEP",
    "BOUNDED_REPAIR_REROUTE_VERSION",
    "BoundedRepairRerouteDecision",
    "assert_bounded_repair_reroute_meta_only",
    "decide_bounded_repair_reroute",
]
