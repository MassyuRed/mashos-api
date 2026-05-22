# -*- coding: utf-8 -*-
from __future__ import annotations

"""RuntimeSurfaceQuality Step6 Complete Runtime Activation Branch.

This module is meta-only.  It verifies whether the Step5
``complete_runtime_activation`` branch can actually measure a
``complete_initial`` runtime path before Surface / Tone / Grammar repairs start.
It never generates observation text, never relaxes AP0/Gate/RN/API/DB
contracts, and never writes public ``comment_text`` bodies.
"""

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_VERSION = (
    "emlis.runtime_surface_complete_activation_branch.v1"
)
RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_STEP = (
    "Step6_Complete_Runtime_Activation_Branch"
)
RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_SOURCE = (
    "emlis_runtime_surface_quality_step6_complete_runtime_activation_branch"
)

_COMPLETE_SOURCES = {"complete_initial", "complete_composer_initial"}
_NON_COMPLETE_SOURCES = {
    "limited",
    "a1_equivalent",
    "a_plan_equivalent",
    "limited_composer",
    "legacy_limited",
    "unavailable",
}
_BLOCKED_CONNECTION_STATUSES = {
    "blocked_ap0",
    "blocked_rollout",
    "blocked_safety",
    "blocked_scope",
    "blocked_feature_flag",
    "blocked_complete_initial_runtime_gate",
    "not_resolved",
}

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
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
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "body",
    "text",
    "sentence",
    "sentences",
}

_FORBIDDEN_TRUE_FLAGS = (
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "public_release_applied",
    "product_gate_public_release_applied",
    "product_quality_released",
    "product_gate_achieved",
    "product_gate_reached",
    "fixed_sentence_template_used",
    "fixed_fallback_used",
    "input_specific_template_added",
    "fixed_completed_sentence_template_added",
    "external_ai_used",
    "local_llm_used",
    "rn_complete_dedicated_display_branch_added",
    "complete_dedicated_rn_display_branch_added",
    "surface_text_repaired_by_step6",
)


class RuntimeSurfaceCompleteActivationBranchError(ValueError):
    """Raised when Step6 Complete Runtime Activation meta breaks contracts."""


def _clean(value: Any) -> str:
    if value is None or isinstance(value, Mapping):
        return ""
    return str(value).strip()


def _lower(value: Any) -> str:
    return _clean(value).lower().replace("-", "_").replace(" ", "_")


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = _lower(value)
    if text in {"1", "true", "yes", "y", "on", "green", "passed", "allowed", "resolved", "used"}:
        return True
    if text in {"0", "false", "no", "n", "off", "red", "blocked", "not_allowed", "not_resolved", ""}:
        return False
    return default


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_runtime_surface_complete_activation_branch_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "runtime_surface_complete_activation_branch",
) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise RuntimeSurfaceCompleteActivationBranchError(
            f"{source} must stay meta-only and must not include text payload keys"
        )
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise RuntimeSurfaceCompleteActivationBranchError(
                f"{source} violates fixed contract: {key}=true"
            )


def _first_mapping_from_sequence(values: Any, *keys: str) -> dict[str, Any]:
    for value in _listify(values):
        item = _safe_mapping(value)
        if not item:
            continue
        if not keys:
            return item
        for key in keys:
            nested = _safe_mapping(item.get(key))
            if nested:
                return nested
    return {}


def _first_source_lock(*sources: Any) -> dict[str, Any]:
    for source in sources:
        direct = _safe_mapping(source)
        if direct and _clean(direct.get("composer_source")):
            return direct
        nested = _first_mapping_from_sequence(source, "runtime_surface_source_lock", "step1_runtime_surface_source_lock")
        if nested:
            return nested
    return {}


def _first_resolution(*sources: Any) -> dict[str, Any]:
    for source in sources:
        direct = _safe_mapping(source)
        if direct and (
            _clean(direct.get("connection_status"))
            or _clean(direct.get("resolution_source"))
            or _clean(direct.get("requested_composer"))
        ):
            return direct
        nested = _first_mapping_from_sequence(
            source,
            "composer_client_resolution",
            "resolution_meta",
            "registry_resolution",
            "default_composer_resolution",
        )
        if nested:
            return nested
    return {}


def _first_ap0_decision(*sources: Any) -> dict[str, Any]:
    for source in sources:
        direct = _safe_mapping(source)
        if direct and (_clean(direct.get("phase")) == "complete_initial_entry_ap0" or "green" in direct):
            return direct
        nested = _first_mapping_from_sequence(
            source,
            "complete_initial_entry_ap0_decision",
            "entry_ap0_decision",
            "ap0_decision_report",
        )
        if nested:
            return nested
    return {}


def _first_release(*sources: Any) -> dict[str, Any]:
    for source in sources:
        direct = _safe_mapping(source)
        if direct and any(key in direct for key in ("release_allowed", "rollout_allowed", "enabled", "stage")):
            return direct
        nested = _first_mapping_from_sequence(
            source,
            "release_meta",
            "release_gate",
            "phase7_rollout_gate",
            "complete_initial_gate",
        )
        if nested:
            return nested
    return {}


def _requested_complete_initial(resolution: Mapping[str, Any], ap0_decision: Mapping[str, Any], source_lock: Mapping[str, Any]) -> bool:
    requested = _lower(
        resolution.get("requested_composer")
        or source_lock.get("composer_requested")
        or _safe_mapping(resolution.get("feature_flag_state")).get("requested_composer")
        or _safe_mapping(ap0_decision.get("evidence_summary")).get("requested_composer")
    )
    canonical = _lower(
        resolution.get("canonical_requested_composer")
        or _safe_mapping(resolution.get("feature_flag_state")).get("canonical_requested_composer")
        or _safe_mapping(ap0_decision.get("evidence_summary")).get("canonical_requested_composer")
    )
    return bool(
        requested in {"complete_initial", "complete_composer_initial", "complete_initial_composer"}
        or canonical == "complete_composer_initial"
        or _to_bool(resolution.get("complete_initial_requested"))
        or _to_bool(resolution.get("complete_composer_initial_requested"))
        or _to_bool(resolution.get("complete_initial_client_requested"))
        or _to_bool(ap0_decision.get("can_enter_complete_composer_initial"))
        or _to_bool(ap0_decision.get("can_proceed_to_complete_initial"))
    )


def _release_allowed(resolution: Mapping[str, Any], release_meta: Mapping[str, Any]) -> bool:
    complete_gate = _safe_mapping(resolution.get("complete_initial_gate"))
    return bool(
        _to_bool(resolution.get("release_allowed"))
        or _to_bool(release_meta.get("release_allowed"))
        or _to_bool(release_meta.get("rollout_allowed"))
        or _to_bool(release_meta.get("enabled"))
        or _to_bool(release_meta.get("allowed"))
        or _to_bool(complete_gate.get("release_allowed"))
    )


def _connection_status(resolution: Mapping[str, Any]) -> str:
    return _clean(resolution.get("connection_status") or _safe_mapping(resolution.get("default_composer_resolution")).get("connection_status"))


def build_runtime_surface_complete_activation_branch(
    *,
    runtime_surface_quality_branch: Mapping[str, Any] | None = None,
    runtime_surface_source_lock: Mapping[str, Any] | None = None,
    composer_client_resolution: Mapping[str, Any] | None = None,
    complete_initial_entry_ap0_decision: Mapping[str, Any] | None = None,
    release_meta: Mapping[str, Any] | None = None,
    diagnostic_meta: Mapping[str, Any] | None = None,
    scorecard_events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    rows: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return Step6 Complete Runtime Activation report.

    The branch is intentionally diagnostic-only.  It can confirm that
    ``complete_initial`` is resolved and source-lock aligned, or it can explain
    why AP0 / rollout / request state still prevents Complete runtime from
    being measured.  It never repairs surface wording.
    """

    row_list = [dict(row) for row in list(rows or []) if isinstance(row, Mapping)]
    event_list = [dict(event) for event in list(scorecard_events or []) if isinstance(event, Mapping)]
    branch = _safe_mapping(runtime_surface_quality_branch)
    diagnostic = _safe_mapping(diagnostic_meta)
    source_lock = _first_source_lock(runtime_surface_source_lock, diagnostic, event_list, row_list)
    resolution = _first_resolution(composer_client_resolution, diagnostic, row_list, event_list)
    ap0_decision = _first_ap0_decision(complete_initial_entry_ap0_decision, diagnostic, resolution, row_list, event_list)
    release = _first_release(release_meta, diagnostic, resolution, row_list, event_list)

    assert_runtime_surface_complete_activation_branch_meta_only(source_lock, source="step6_source_lock")
    assert_runtime_surface_complete_activation_branch_meta_only(resolution, source="step6_resolution")
    assert_runtime_surface_complete_activation_branch_meta_only(ap0_decision, source="step6_ap0_decision")
    assert_runtime_surface_complete_activation_branch_meta_only(release, source="step6_release_meta")

    target_layer = _clean(branch.get("target_layer") or branch.get("runtime_surface_quality_target_layer"))
    composer_source = _clean(source_lock.get("composer_source") or diagnostic.get("runtime_composer_source"))
    complete_initial_requested = _requested_complete_initial(resolution, ap0_decision, source_lock)
    complete_initial_client_used = bool(
        _to_bool(resolution.get("complete_initial_client_used"))
        or _to_bool(source_lock.get("complete_initial_client_used"))
        or _to_bool(resolution.get("complete_composer_client_used"))
    )
    status = _connection_status(resolution)
    ap0_green = bool(
        _to_bool(ap0_decision.get("green"))
        or _to_bool(ap0_decision.get("can_proceed_to_a1"))
        or _to_bool(_safe_mapping(resolution.get("ap0_decision_report")).get("green"))
        or _to_bool(_safe_mapping(resolution.get("complete_initial_gate")).get("ap0_green"))
    )
    rollout_allowed = _release_allowed(resolution, release)
    blocked_connection = bool(status in _BLOCKED_CONNECTION_STATUSES or status.startswith("blocked_"))
    complete_initial_registry_resolved = bool(
        complete_initial_client_used
        and status in {"default_client_resolved", "provided_client"}
    )
    complete_initial_resolved = bool(
        complete_initial_registry_resolved
        and composer_source in _COMPLETE_SOURCES
    )
    non_complete_source = composer_source in _NON_COMPLETE_SOURCES or not composer_source or composer_source == "unknown"
    activation_required = bool(target_layer == "complete_runtime_activation" or (non_complete_source and not complete_initial_resolved))
    source_lock_aligned = bool(
        (complete_initial_resolved and composer_source == "complete_initial" and _to_bool(source_lock.get("complete_initial_client_used")))
        or (not complete_initial_client_used and composer_source not in _COMPLETE_SOURCES)
    )
    eligible_only = bool(not complete_initial_client_used or (ap0_green and rollout_allowed and not blocked_connection))

    reasons: list[str] = []
    if target_layer:
        reasons.append(f"branch_target:{target_layer}")
    if composer_source:
        reasons.append(f"composer_source:{composer_source}")
    if complete_initial_requested:
        reasons.append("complete_initial_requested")
    if complete_initial_resolved:
        reasons.append("complete_initial_resolved")
    elif complete_initial_requested and not ap0_green:
        reasons.append("complete_initial_ap0_not_green")
    elif complete_initial_requested and ap0_green and not rollout_allowed:
        reasons.append("complete_initial_rollout_not_allowed")
    elif complete_initial_requested and blocked_connection:
        reasons.append(f"complete_initial_connection_blocked:{status}")
    elif activation_required:
        reasons.append("complete_runtime_activation_pending")

    if complete_initial_resolved:
        activation_status = "resolved_complete_initial"
        next_step = "runtime_surface_source_remeasurement_on_complete_initial"
    elif complete_initial_registry_resolved and activation_required:
        activation_status = "complete_initial_registry_resolved_source_lock_remeasurement_required"
        next_step = "runtime_surface_source_remeasurement_on_complete_initial"
    elif complete_initial_requested and not ap0_green:
        activation_status = "blocked_ap0"
        next_step = "complete_initial_entry_ap0_prerequisite_repair"
    elif complete_initial_requested and ap0_green and not rollout_allowed:
        activation_status = "blocked_rollout"
        next_step = "complete_initial_rollout_eligibility_recheck"
    elif complete_initial_requested and blocked_connection:
        activation_status = status or "blocked_complete_initial_runtime_gate"
        next_step = "complete_initial_registry_gate_recheck"
    elif activation_required:
        activation_status = "activation_required_but_complete_initial_not_requested"
        next_step = "set_complete_initial_default_composer_or_review_branch_source"
    else:
        activation_status = "not_required_complete_runtime_already_measurable_or_next_branch_not_runtime"
        next_step = _clean(branch.get("next_work_unit")) or "continue_runtime_surface_quality_branch"

    payload = {
        "version": RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_VERSION,
        "schema_version": RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_VERSION,
        "source": RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_SOURCE,
        "source_step": RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_STEP,
        "step": RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_STEP,
        "step6_complete_runtime_activation_branch_ready": True,
        "runtime_surface_complete_activation_branch_ready": True,
        "complete_runtime_activation_branch_ready": True,
        "activation_branch_required": activation_required,
        "target_layer": "complete_runtime_activation" if activation_required else (target_layer or "not_complete_runtime_activation"),
        "previous_branch_target_layer": target_layer,
        "activation_status": activation_status,
        "next_step_after_step6": next_step,
        "selected_reason": reasons[0] if reasons else activation_status,
        "activation_reasons": _dedupe(reasons),
        "runtime_surface_source_lock_ready": bool(source_lock.get("runtime_surface_source_lock_ready") or source_lock.get("runtime_surface_source_locked")),
        "runtime_composer_source": composer_source,
        "composer_requested": _clean(source_lock.get("composer_requested") or resolution.get("requested_composer")),
        "composer_resolved": _clean(source_lock.get("composer_resolved")) or composer_source,
        "composer_model": _clean(source_lock.get("composer_model") or resolution.get("composer_model")),
        "composer_client_resolution_status": status,
        "resolution_source": _clean(resolution.get("resolution_source") or resolution.get("source")),
        "resolved_client_class": _clean(resolution.get("resolved_client_class") or resolution.get("resolved_client_name")),
        "complete_initial_requested": complete_initial_requested,
        "complete_initial_client_used": complete_initial_client_used,
        "complete_initial_registry_resolved": complete_initial_registry_resolved,
        "complete_initial_resolved": complete_initial_resolved,
        "complete_initial_source_lock_aligned": source_lock_aligned,
        "complete_initial_resolution_safe_to_measure": bool(complete_initial_resolved and source_lock_aligned and eligible_only),
        "eligible_only_complete_initial_resolution": eligible_only,
        "ap0_green": ap0_green,
        "rollout_allowed": rollout_allowed,
        "ap0_red_blocks_complete_client": bool(complete_initial_requested and not ap0_green and not complete_initial_client_used),
        "rollout_red_blocks_complete_client": bool(complete_initial_requested and ap0_green and not rollout_allowed and not complete_initial_client_used),
        "blocked_connection_status": status if blocked_connection else "",
        "complete_initial_gate_reason": _clean(_safe_mapping(resolution.get("complete_initial_gate")).get("reason")),
        "ap0_unmet_checks": _dedupe(ap0_decision.get("unmet_checks")),
        "ap0_release_blocker_keys": _dedupe(ap0_decision.get("release_blocker_keys")),
        "release_stage": _clean(release.get("stage") or release.get("rollout_stage")),
        "entry_ap0_or_rollout_required_before_surface_repair": bool(activation_required and not complete_initial_resolved),
        "surface_repair_deferred_until_complete_runtime_measurable": bool(activation_required and not complete_initial_resolved),
        "surface_text_repaired_by_step6": False,
        "surface_realizer_touched_by_step6": False,
        "tone_engine_touched_by_step6": False,
        "phrase_unit_grammar_touched_by_step6": False,
        "rn_complete_dedicated_display_branch_added": False,
        "complete_dedicated_rn_display_branch_added": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "public_response_key_change": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "response_shape_changed": False,
        "product_gate_achieved": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_used": False,
        "fixed_fallback_used": False,
        "input_specific_template_added": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_runtime_surface_complete_activation_branch_meta_only(payload)
    return payload


build_complete_runtime_activation_branch = build_runtime_surface_complete_activation_branch


def dump_runtime_surface_complete_activation_branch(branch: Mapping[str, Any]) -> str:
    data = dict(branch or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    data["comment_text_body_included"] = False
    assert_runtime_surface_complete_activation_branch_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_SOURCE",
    "RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_STEP",
    "RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_VERSION",
    "RuntimeSurfaceCompleteActivationBranchError",
    "assert_runtime_surface_complete_activation_branch_meta_only",
    "build_runtime_surface_complete_activation_branch",
    "build_complete_runtime_activation_branch",
    "dump_runtime_surface_complete_activation_branch",
]
