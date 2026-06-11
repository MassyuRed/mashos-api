# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-1 visible readiness boundary for User Label Connection.

This module decides whether a P5-ready User Label Connection may proceed to
limited visible connection, must remain meta-only, must stay on hold, or must be
blocked.  It is meta-only and never writes ``comment_text``.
"""

from collections.abc import Iterable, Mapping
import json
from typing import Any, Final

from emlis_ai_user_label_connection_p5_readiness import (
    assert_user_label_connection_p5_readiness_contract,
)


USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_visibility_boundary.v1"
)
USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP: Final = (
    "P5-1_UserLabelConnection_VisibleReadinessBoundary"
)
USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_VisibleReadinessBoundary_20260611"
)

DECISION_ALLOW_LIMITED_VISIBLE: Final = "allow_limited_visible"
DECISION_META_ONLY: Final = "meta_only"
DECISION_HOLD: Final = "hold"
DECISION_BLOCK: Final = "block"

REASON_P5_ENTRY_NOT_ALLOWED: Final = "p5_entry_not_allowed"
REASON_FREE_TIER_HISTORY_BLOCKED: Final = "free_tier_history_blocked"
REASON_OWNED_HISTORY_ONLY_NOT_MET: Final = "owned_history_only_not_met"
REASON_CURRENT_INPUT_MISSING: Final = "current_input_missing"
REASON_HISTORY_RECORD_COUNT_INSUFFICIENT: Final = "history_record_count_insufficient"
REASON_USER_FACT_GROUNDING_BOUNDARY_BLOCKED: Final = "user_fact_grounding_boundary_blocked"
REASON_SCOPE_MARKER_MISSING: Final = "scope_marker_missing"
REASON_SOFT_MARKER_MISSING: Final = "soft_marker_missing"
REASON_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED: Final = "low_information_history_promotion_blocked"
REASON_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED: Final = "safety_adjacent_history_connection_blocked"
REASON_SELF_DENIAL_HISTORY_CONNECTION_BLOCKED: Final = "self_denial_history_connection_blocked"
REASON_TARGET_JUDGEMENT_HISTORY_CONNECTION_BLOCKED: Final = "target_judgement_history_connection_blocked"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"
REASON_EXISTING_COMMENT_TEXT_MISSING: Final = "existing_comment_text_missing"
REASON_EXISTING_GATE_BLOCKED: Final = "existing_gate_blocked"
REASON_CURRENT_INPUT_MASKED_BY_HISTORY: Final = "current_input_masked_by_history"

_SOURCE_SCOPE_OWNED_HISTORY: Final = "current_input_with_owned_history"
_SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE: Final = "current_input_with_owned_history_and_cross_core"

_LOW_INFORMATION_MARKERS: Final = frozenset(
    {"low_information", "low_information_short", "insufficient_information", "low_information_protected"}
)
_SAFETY_MARKERS: Final = frozenset(
    {
        "safety_triage_required",
        "safety_required",
        "safety_adjacent",
        "safety_blocked",
        "emergency",
        "emergency_safety_required",
    }
)
_SELF_DENIAL_MARKERS: Final = frozenset(
    {
        "self_denial",
        "self_denial_context",
        "self_denial_safe_state_answer",
        "self_denial_identity",
        "identity_claim_as_fact",
    }
)
_TARGET_JUDGEMENT_MARKERS: Final = frozenset(
    {
        "target_judgement",
        "target_judgement_context",
        "anger_or_boundary",
        "anger_or_boundary_strict_context",
        "opponent_intent_claim",
        "target_attack_agreement",
    }
)

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
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
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "visible_text",
        "visibleText",
        "realized_text",
        "realizedText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "blind_qa_free_text",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_physical_name_changed",
        "db_schema_changed",
        "rn_contract_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "p5_runtime_change_applied",
        "fixed_sentence_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "release_allowed",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return {str(key): item for key, item in meta.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except (TypeError, ValueError):
        return default


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(child) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str] = _FORBIDDEN_TRUE_FLAGS) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _has_marker(value: Any, markers: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _clean(key).lower()
            if key_text in markers:
                if child is True:
                    return True
                if child in (False, None, "", (), [], {}):
                    continue
                if _has_marker(child, markers):
                    return True
            elif _has_marker(child, markers):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_has_marker(child, markers) for child in value)
    text = _clean(value).lower()
    return bool(text and any(marker in text for marker in markers))


def _first_str(*sources: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    for source in sources:
        for key in keys:
            value = _clean(source.get(key))
            if value:
                return value
    return ""


def _first_bool(*sources: Mapping[str, Any], keys: tuple[str, ...], default: bool = False) -> bool:
    for source in sources:
        for key in keys:
            if key in source:
                return source.get(key) is True
    return default


def _first_int(*sources: Mapping[str, Any], keys: tuple[str, ...], default: int = 0) -> int:
    for source in sources:
        for key in keys:
            if key in source:
                return _int(source.get(key), default)
    return default


def _gate_reports_passed(existing_gate_reports: Mapping[str, Any] | None) -> tuple[bool, list[str]]:
    reports = _safe_mapping(existing_gate_reports)
    if not reports:
        return False, ["existing_gate_reports_missing"]
    blockers: list[str] = []
    for name, report in reports.items():
        if isinstance(report, bool):
            passed = report is True
        else:
            meta = _safe_mapping(report)
            if meta.get("blocked") is True or meta.get("passed") is False:
                passed = False
            elif meta.get("passed") is True or meta.get("action") in {"allow", "warn"}:
                passed = True
            else:
                passed = False
        if not passed:
            blockers.append(f"existing_gate_blocked:{name}")
    return not blockers, blockers


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "release_allowed": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
    }


def _eligibility_summary(
    *,
    subscription_history_allowed: bool,
    owned_history_only: bool,
    current_input_included: bool,
    evidence_record_count: int,
    user_fact_grounding_boundary_passed: bool,
    scope_marker_required: bool,
    soft_marker_required: bool,
    current_input_not_masked_by_history: bool,
) -> dict[str, Any]:
    return {
        "subscription_history_allowed": subscription_history_allowed,
        "owned_history_only": owned_history_only,
        "current_input_included": current_input_included,
        "evidence_record_count": evidence_record_count,
        "minimum_evidence_record_count": 2,
        "user_fact_grounding_boundary_passed": user_fact_grounding_boundary_passed,
        "scope_marker_required": scope_marker_required,
        "soft_marker_required": soft_marker_required,
        "current_input_not_masked_by_history": current_input_not_masked_by_history,
    }


def _decision_from_reasons(reasons: Sequence[str], *, p5_ready: bool) -> str:
    blocking = {
        REASON_FREE_TIER_HISTORY_BLOCKED,
        REASON_OWNED_HISTORY_ONLY_NOT_MET,
        REASON_CURRENT_INPUT_MISSING,
        REASON_HISTORY_RECORD_COUNT_INSUFFICIENT,
        REASON_USER_FACT_GROUNDING_BOUNDARY_BLOCKED,
        REASON_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED,
        REASON_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED,
        REASON_SELF_DENIAL_HISTORY_CONNECTION_BLOCKED,
        REASON_TARGET_JUDGEMENT_HISTORY_CONNECTION_BLOCKED,
        REASON_RAW_TEXT_PAYLOAD_DETECTED,
        REASON_CONTRACT_MUTATION_DETECTED,
        REASON_EXISTING_GATE_BLOCKED,
        REASON_CURRENT_INPUT_MASKED_BY_HISTORY,
    }
    if any(reason in blocking or reason.startswith("existing_gate_blocked:") for reason in reasons):
        return DECISION_BLOCK
    if not p5_ready:
        return DECISION_HOLD
    if REASON_EXISTING_COMMENT_TEXT_MISSING in reasons or REASON_SCOPE_MARKER_MISSING in reasons or REASON_SOFT_MARKER_MISSING in reasons:
        return DECISION_META_ONLY
    return DECISION_ALLOW_LIMITED_VISIBLE


def build_user_label_connection_p5_visibility_boundary(
    *,
    p5_readiness: Mapping[str, Any] | None = None,
    material_meta: Mapping[str, Any] | None = None,
    gate_meta: Mapping[str, Any] | None = None,
    surface_plan_meta: Mapping[str, Any] | None = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    existing_comment_text_present: bool = False,
    existing_gate_reports: Mapping[str, Any] | None = None,
    subscription_tier: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the P5-1 visible readiness boundary decision."""

    readiness = _safe_mapping(p5_readiness)
    material = _safe_mapping(material_meta)
    gate = _safe_mapping(gate_meta)
    surface = _safe_mapping(surface_plan_meta)
    observation = _safe_mapping(observation_reply_meta)

    if readiness:
        assert_user_label_connection_p5_readiness_contract(readiness, allow_partial=True)

    sources = [readiness, material, gate, surface, observation]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)

    tier = (_clean(subscription_tier) or _clean(material.get("capability_tier")) or "free").lower()
    source_scope = _first_str(
        surface,
        gate,
        material,
        keys=("source_scope", "record_scope"),
    )
    evidence_record_count = _first_int(
        surface.get("evidence_contract") if isinstance(surface.get("evidence_contract"), Mapping) else {},
        gate.get("evidence_contract") if isinstance(gate.get("evidence_contract"), Mapping) else {},
        gate,
        material,
        keys=("evidence_record_count", "history_connection_evidence_record_count", "max_edge_evidence_record_count"),
        default=0,
    )
    if evidence_record_count <= 0:
        edge_counts = [
            _int(edge.get("evidence_record_count"), 0)
            for edge in _listify(material.get("connection_edges"))
            if isinstance(edge, Mapping)
        ]
        evidence_record_count = max(edge_counts, default=0)
    current_input_included = _first_bool(
        surface.get("evidence_contract") if isinstance(surface.get("evidence_contract"), Mapping) else {},
        gate.get("evidence_contract") if isinstance(gate.get("evidence_contract"), Mapping) else {},
        gate,
        material,
        keys=("current_record_included", "current_input_included", "current_point_present"),
    )
    if not current_input_included:
        current_input_included = any(
            edge.get("current_record_included") is True or edge.get("current_input_included") is True
            for edge in _listify(material.get("connection_edges"))
            if isinstance(edge, Mapping)
        )
    user_fact_boundary_passed = _first_bool(
        material,
        gate,
        keys=("user_fact_grounding_boundary_passed", "grounding_boundary_passed", "user_fact_boundary_passed"),
    )
    if "user_fact_grounding_boundary_passed" not in material and "grounding_boundary_passed" not in material:
        user_fact_boundary_passed = material.get("record_scope") not in {
            "blocked_grounding_boundary",
            "blocked_free_tier",
        }
    scope_marker_required = _first_bool(surface, gate, keys=("scope_marker_required", "scope_marker_present"), default=True)
    soft_marker_required = _first_bool(surface, gate, keys=("soft_marker_required", "soft_marker_present"), default=True)
    current_input_not_masked = not _first_bool(
        readiness,
        surface,
        gate,
        material,
        keys=("history_line_masks_current_input_gap", "history_line_masking_observed"),
    )

    subscription_history_allowed = tier in {"plus", "premium"}
    owned_history_only = source_scope == _SOURCE_SCOPE_OWNED_HISTORY

    existing_gates_ok, gate_blockers = _gate_reports_passed(existing_gate_reports)
    p5_ready = readiness.get("p5_entry_allowed") is True and readiness.get("p5_visible_strengthening_allowed") is True

    reasons: list[str] = []
    if unsafe_payload:
        reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if contract_mutation:
        reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    if not p5_ready:
        reasons.append(REASON_P5_ENTRY_NOT_ALLOWED)
        reasons.extend(f"p5_hold:{reason}" for reason in _dedupe(readiness.get("p5_hold_reason_codes")))
    if not subscription_history_allowed:
        reasons.append(REASON_FREE_TIER_HISTORY_BLOCKED)
    if not owned_history_only:
        reasons.append(REASON_OWNED_HISTORY_ONLY_NOT_MET)
    if not current_input_included:
        reasons.append(REASON_CURRENT_INPUT_MISSING)
    if evidence_record_count < 2:
        reasons.append(REASON_HISTORY_RECORD_COUNT_INSUFFICIENT)
    if not user_fact_boundary_passed:
        reasons.append(REASON_USER_FACT_GROUNDING_BOUNDARY_BLOCKED)
    if not scope_marker_required:
        reasons.append(REASON_SCOPE_MARKER_MISSING)
    if not soft_marker_required:
        reasons.append(REASON_SOFT_MARKER_MISSING)
    if not existing_comment_text_present:
        reasons.append(REASON_EXISTING_COMMENT_TEXT_MISSING)
    if not existing_gates_ok:
        reasons.append(REASON_EXISTING_GATE_BLOCKED)
        reasons.extend(gate_blockers)
    if not current_input_not_masked:
        reasons.append(REASON_CURRENT_INPUT_MASKED_BY_HISTORY)
    if _has_marker(sources, _LOW_INFORMATION_MARKERS):
        reasons.append(REASON_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED)
    if _has_marker(sources, _SAFETY_MARKERS):
        reasons.append(REASON_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED)
    if _has_marker(sources, _SELF_DENIAL_MARKERS):
        reasons.append(REASON_SELF_DENIAL_HISTORY_CONNECTION_BLOCKED)
    if _has_marker(sources, _TARGET_JUDGEMENT_MARKERS):
        reasons.append(REASON_TARGET_JUDGEMENT_HISTORY_CONNECTION_BLOCKED)
    reasons = _dedupe(reasons)

    decision = _decision_from_reasons(reasons, p5_ready=p5_ready)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP,
        "source": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SOURCE,
        "run_id": run_id or "p5_visibility_boundary",
        "decision": decision,
        "allow_limited_visible": decision == DECISION_ALLOW_LIMITED_VISIBLE,
        "meta_only": decision == DECISION_META_ONLY,
        "hold": decision == DECISION_HOLD,
        "blocked": decision == DECISION_BLOCK,
        "rejection_reasons": reasons,
        "eligibility": _eligibility_summary(
            subscription_history_allowed=subscription_history_allowed,
            owned_history_only=owned_history_only,
            current_input_included=current_input_included,
            evidence_record_count=evidence_record_count,
            user_fact_grounding_boundary_passed=user_fact_boundary_passed,
            scope_marker_required=scope_marker_required,
            soft_marker_required=soft_marker_required,
            current_input_not_masked_by_history=current_input_not_masked,
        ),
        "existing_comment_text_present": existing_comment_text_present,
        "existing_gate_reports_passed": existing_gates_ok,
        "p5_entry_allowed": readiness.get("p5_entry_allowed") is True,
        "p5_visible_strengthening_allowed": readiness.get("p5_visible_strengthening_allowed") is True,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_user_label_connection_p5_visibility_boundary_contract(summary)
    return summary


def user_label_connection_p5_visibility_boundary_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _safe_mapping(value)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP,
        "decision": _clean(meta.get("decision")) or DECISION_HOLD,
        "allow_limited_visible": meta.get("allow_limited_visible") is True,
        "meta_only": meta.get("meta_only") is True,
        "hold": meta.get("hold") is True,
        "blocked": meta.get("blocked") is True,
        "rejection_reasons": _dedupe(meta.get("rejection_reasons")),
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
    }
    assert_user_label_connection_p5_visibility_boundary_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_p5_visibility_boundary_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("P5 visibility boundary must not include raw text/comment/history payload keys")
    if _flag_true(value):
        raise ValueError("P5 visibility boundary contains a forbidden true flag")
    json.dumps(value, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not isinstance(value, Mapping):
        raise ValueError("P5 visibility boundary must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION:
        raise ValueError("unexpected P5 visibility boundary schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP:
        raise ValueError("unexpected P5 visibility boundary step")
    public_contract = _safe_mapping(value.get("public_contract"))
    body_free = _safe_mapping(value.get("body_free"))
    for key in ("rn_visible_contract_changed", "public_response_key_added", "response_shape_changed", "db_schema_changed"):
        if public_contract.get(key) is not False:
            raise ValueError(f"P5 visibility public_contract.{key} must be false")
    for key in ("raw_text_included", "comment_text_body_included", "history_raw_text_included"):
        if body_free.get(key) is not False:
            raise ValueError(f"P5 visibility body_free.{key} must be false")


__all__ = [
    "USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP",
    "USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SOURCE",
    "DECISION_ALLOW_LIMITED_VISIBLE",
    "DECISION_META_ONLY",
    "DECISION_HOLD",
    "DECISION_BLOCK",
    "build_user_label_connection_p5_visibility_boundary",
    "user_label_connection_p5_visibility_boundary_public_summary",
    "assert_user_label_connection_p5_visibility_boundary_contract",
]
