# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-2 history-line eligibility matrix for User Label Connection.

This module classifies a P5-ready User Label Connection history line as
``connectable``, ``meta_only``, ``review_required``, or ``blocked``.  It is a
backend-internal matrix only: it does not generate visible text, does not widen
the existing limited connectable families, and does not change RN/API/DB/public
response contracts.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_user_label_connection_p5_visibility_boundary import (
    assert_user_label_connection_p5_visibility_boundary_contract,
)
from emlis_ai_user_label_connection_types import (
    EDGE_FAMILY_ACTION_STATE_BRIDGE,
    EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
    EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
    EDGE_FAMILY_CONTRAST_LINE_SHIFT,
    EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
    EDGE_FAMILY_RECOVERY_LABEL_ROUTE,
    EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
    EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
    EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
    SOURCE_SCOPE_OWNED_HISTORY,
)


USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_eligibility_matrix.v1"
)
USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP: Final = (
    "P5-2_HistoryLineEligibilityMatrix"
)
USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_HistoryLineEligibilityMatrix_20260611"
)

DECISION_CONNECTABLE: Final = "connectable"
DECISION_META_ONLY: Final = "meta_only"
DECISION_REVIEW_REQUIRED: Final = "review_required"
DECISION_BLOCKED: Final = "blocked"

REASON_P5_VISIBILITY_BOUNDARY_NOT_ALLOWED: Final = "p5_visibility_boundary_not_allowed"
REASON_SOURCE_SCOPE_NOT_OWNED_HISTORY: Final = "source_scope_not_owned_history"
REASON_CURRENT_INPUT_MISSING: Final = "current_input_missing"
REASON_EVIDENCE_RECORD_COUNT_INSUFFICIENT: Final = "evidence_record_count_insufficient"
REASON_HISTORY_RECORD_COUNT_INSUFFICIENT: Final = "history_record_count_insufficient"
REASON_FAMILY_MISSING: Final = "connectable_family_missing"
REASON_FAMILY_BLOCKED: Final = "family_blocked_initial_p5"
REASON_FAMILY_SUPPRESSED_META_ONLY: Final = "family_suppressed_meta_only"
REASON_FAMILY_REVIEW_REQUIRED: Final = "family_review_required"
REASON_FAMILY_UNSUPPORTED_REVIEW_REQUIRED: Final = "family_unsupported_review_required"
REASON_EDGE_FAMILY_MISSING: Final = "edge_family_missing"
REASON_EDGE_FAMILY_REVIEW_REQUIRED: Final = "edge_family_review_required"
REASON_EDGE_FAMILY_META_ONLY: Final = "edge_family_meta_only"
REASON_EDGE_FAMILY_UNSUPPORTED_BLOCKED: Final = "edge_family_unsupported_blocked"
REASON_LOW_INFORMATION_BLOCKED: Final = "low_information_history_promotion_blocked"
REASON_SAFETY_ADJACENT_BLOCKED: Final = "safety_adjacent_history_connection_blocked"
REASON_SELF_DENIAL_BLOCKED: Final = "self_denial_history_connection_blocked"
REASON_TARGET_JUDGEMENT_BLOCKED: Final = "target_judgement_history_connection_blocked"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"

CONNECTABLE_FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
CONNECTABLE_FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"

_CONNECTABLE_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
        CONNECTABLE_FAMILY_LONG_MEANING_ARC,
        CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    }
)
_REVIEW_REQUIRED_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "standard_state_answer",
        "uncertainty_support",
        "change_future_intention",
    }
)
_META_ONLY_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "daily_unpleasant",
        "daily_positive",
        "positive_only",
    }
)
_BLOCKED_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "low_information",
        "low_information_short",
        "insufficient_information",
        "limited_grounding",
        "self_denial",
        "self_denial_context",
        "anger_or_boundary",
        "anger_or_boundary_strict_context",
        "safety_triage_required",
        "safety_required",
        "safety_adjacent",
        "emergency",
        "emergency_safety_required",
    }
)

_ALLOW_EDGE_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
        EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
    }
)
_REVIEW_EDGE_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
        EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
        EDGE_FAMILY_ACTION_STATE_BRIDGE,
        EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
        EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
    }
)
_META_ONLY_EDGE_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        EDGE_FAMILY_CONTRAST_LINE_SHIFT,
        EDGE_FAMILY_RECOVERY_LABEL_ROUTE,
    }
)

_LOW_INFORMATION_MARKERS: Final[frozenset[str]] = frozenset(
    {"low_information", "low_information_short", "insufficient_information", "low_information_protected"}
)
_SAFETY_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "safety_triage_required",
        "safety_required",
        "safety_adjacent",
        "safety_blocked",
        "emergency",
        "emergency_safety_required",
    }
)
_SELF_DENIAL_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "self_denial",
        "self_denial_context",
        "self_denial_safe_state_answer",
        "self_denial_identity",
        "identity_claim_as_fact",
    }
)
_TARGET_JUDGEMENT_MARKERS: Final[frozenset[str]] = frozenset(
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
        "db_schema_changed",
        "db_physical_name_changed",
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
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "public_release_applied",
        "release_allowed",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "p5_limited_visible_connection_applied",
        "external_ai_used",
        "local_llm_used",
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


def _edge_items(edge_meta: Any, material: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for value in _listify(edge_meta):
        item = _safe_mapping(value)
        if item:
            items.append(item)
    if items:
        return items
    for value in _listify(material.get("connection_edges")):
        item = _safe_mapping(value)
        if item:
            items.append(item)
    return items


def _edge_family_from(item: Mapping[str, Any]) -> str:
    return _clean(item.get("edge_family")) or _clean(item.get("mechanism_edge_family"))


def _edge_evidence_count(item: Mapping[str, Any]) -> int:
    return max(
        _int(item.get("evidence_record_count"), 0),
        _int(item.get("history_connection_evidence_record_count"), 0),
    )


def _edge_current_included(item: Mapping[str, Any]) -> bool:
    if item.get("current_record_included") is True or item.get("current_input_included") is True:
        return True
    return any(_clean(point_id).startswith("current:") for point_id in _listify(item.get("evidence_point_ids")))


def _nested_evidence(source: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("evidence", "evidence_contract"):
        nested = _safe_mapping(source.get(key))
        if nested:
            return nested
    return {}


def _evidence_summary(
    *,
    material: Mapping[str, Any],
    candidate: Mapping[str, Any],
    gate: Mapping[str, Any],
    surface: Mapping[str, Any],
    edges: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    evidence_sources = [
        _nested_evidence(surface),
        _nested_evidence(gate),
        _nested_evidence(candidate),
        material,
    ]
    evidence_record_count = 0
    history_record_count = 0
    current_record_included = False
    for source in evidence_sources:
        if not source:
            continue
        evidence_record_count = max(
            evidence_record_count,
            _int(source.get("evidence_record_count"), 0),
            _int(source.get("history_connection_evidence_record_count"), 0),
            _int(source.get("max_edge_evidence_record_count"), 0),
        )
        history_record_count = max(history_record_count, _int(source.get("history_record_count"), 0))
        current_record_included = current_record_included or source.get("current_record_included") is True or source.get("current_input_included") is True or source.get("current_point_present") is True
    if edges:
        evidence_record_count = max(evidence_record_count, max(_edge_evidence_count(edge) for edge in edges))
        current_record_included = current_record_included or any(_edge_current_included(edge) for edge in edges)
    if history_record_count <= 0 and evidence_record_count > 0:
        history_record_count = max(0, evidence_record_count - (1 if current_record_included else 0))
    return {
        "evidence_record_count": evidence_record_count,
        "minimum_evidence_record_count": 2,
        "current_record_included": current_record_included,
        "history_record_count": history_record_count,
        "minimum_history_record_count": 1,
    }


def _family_from(
    *,
    connectable_family: str | None,
    observation: Mapping[str, Any],
    surface: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> str:
    explicit = _clean(connectable_family)
    if explicit:
        return explicit
    return _first_str(
        surface,
        observation,
        candidate,
        keys=("connectable_family", "reply_family", "family", "context_family", "observation_family"),
    )


def _family_decision(family: str) -> tuple[str, list[str]]:
    if not family:
        return DECISION_BLOCKED, [REASON_FAMILY_MISSING]
    if family in _BLOCKED_FAMILIES:
        return DECISION_BLOCKED, [f"{REASON_FAMILY_BLOCKED}:{family}"]
    if family in _META_ONLY_FAMILIES:
        return DECISION_META_ONLY, [f"{REASON_FAMILY_SUPPRESSED_META_ONLY}:{family}"]
    if family in _REVIEW_REQUIRED_FAMILIES:
        return DECISION_REVIEW_REQUIRED, [f"{REASON_FAMILY_REVIEW_REQUIRED}:{family}"]
    if family in _CONNECTABLE_FAMILIES:
        return DECISION_CONNECTABLE, []
    return DECISION_REVIEW_REQUIRED, [f"{REASON_FAMILY_UNSUPPORTED_REVIEW_REQUIRED}:{family}"]


def _edge_decision(edge_family: str) -> tuple[str, list[str]]:
    if not edge_family:
        return DECISION_BLOCKED, [REASON_EDGE_FAMILY_MISSING]
    if edge_family in _ALLOW_EDGE_FAMILIES:
        return DECISION_CONNECTABLE, []
    if edge_family in _REVIEW_EDGE_FAMILIES:
        return DECISION_REVIEW_REQUIRED, [f"{REASON_EDGE_FAMILY_REVIEW_REQUIRED}:{edge_family}"]
    if edge_family in _META_ONLY_EDGE_FAMILIES:
        return DECISION_META_ONLY, [f"{REASON_EDGE_FAMILY_META_ONLY}:{edge_family}"]
    return DECISION_BLOCKED, [f"{REASON_EDGE_FAMILY_UNSUPPORTED_BLOCKED}:{edge_family}"]


def _rank(decision: str) -> int:
    return {
        DECISION_CONNECTABLE: 0,
        DECISION_META_ONLY: 1,
        DECISION_REVIEW_REQUIRED: 2,
        DECISION_BLOCKED: 3,
    }.get(decision, 3)


def _most_restrictive(decisions: Iterable[str]) -> str:
    values = list(decisions)
    if not values:
        return DECISION_BLOCKED
    return max(values, key=_rank)


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
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


def build_user_label_connection_p5_eligibility_matrix(
    *,
    p5_visibility_boundary: Mapping[str, Any] | None = None,
    material_meta: Mapping[str, Any] | None = None,
    candidate_meta: Mapping[str, Any] | None = None,
    gate_meta: Mapping[str, Any] | None = None,
    surface_plan_meta: Mapping[str, Any] | None = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    edge_meta: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    connectable_family: str | None = None,
    edge_family: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P5-2 history-line eligibility matrix summary."""

    visibility = _safe_mapping(p5_visibility_boundary)
    material = _safe_mapping(material_meta)
    candidate = _safe_mapping(candidate_meta)
    gate = _safe_mapping(gate_meta)
    surface = _safe_mapping(surface_plan_meta)
    observation = _safe_mapping(observation_reply_meta)
    edges = _edge_items(edge_meta, material)
    if edge_family and not edges:
        edges = [{"edge_family": edge_family}]
    elif edge_family:
        edges = [dict(edge, edge_family=edge_family) if not _edge_family_from(edge) else dict(edge) for edge in edges]

    if visibility:
        assert_user_label_connection_p5_visibility_boundary_contract(visibility, allow_partial=True)

    sources = [visibility, material, candidate, gate, surface, observation, *edges]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)

    family = _family_from(
        connectable_family=connectable_family,
        observation=observation,
        surface=surface,
        candidate=candidate,
    )
    family_decision, family_reasons = _family_decision(family)

    edge_matrix: list[dict[str, Any]] = []
    edge_decisions: list[str] = []
    edge_reasons: list[str] = []
    if not edges:
        decision, reasons = _edge_decision(_clean(edge_family))
        edge_matrix.append({"edge_family": _clean(edge_family), "decision": decision, "reason_codes": reasons})
        edge_decisions.append(decision)
        edge_reasons.extend(reasons)
    else:
        for edge in edges:
            current_edge_family = _edge_family_from(edge) or _clean(edge_family)
            decision, reasons = _edge_decision(current_edge_family)
            edge_matrix.append(
                {
                    "edge_family": current_edge_family,
                    "decision": decision,
                    "reason_codes": reasons,
                }
            )
            edge_decisions.append(decision)
            edge_reasons.extend(reasons)
    edge_decision = _most_restrictive(edge_decisions)
    primary_edge_family = next((_clean(item.get("edge_family")) for item in edge_matrix if _clean(item.get("edge_family"))), "")

    source_scope = _first_str(surface, gate, candidate, material, keys=("source_scope", "record_scope"))
    owned_history_only = source_scope == SOURCE_SCOPE_OWNED_HISTORY
    evidence = _evidence_summary(
        material=material,
        candidate=candidate,
        gate=gate,
        surface=surface,
        edges=edges,
    )
    p5_boundary_allowed = visibility.get("allow_limited_visible") is True

    reasons: list[str] = []
    if unsafe_payload:
        reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if contract_mutation:
        reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    if not p5_boundary_allowed:
        reasons.append(REASON_P5_VISIBILITY_BOUNDARY_NOT_ALLOWED)
        reasons.extend(f"p5_visibility:{reason}" for reason in _dedupe(visibility.get("rejection_reasons")))
    if not owned_history_only:
        reasons.append(REASON_SOURCE_SCOPE_NOT_OWNED_HISTORY)
    if evidence["current_record_included"] is not True:
        reasons.append(REASON_CURRENT_INPUT_MISSING)
    if evidence["evidence_record_count"] < 2:
        reasons.append(REASON_EVIDENCE_RECORD_COUNT_INSUFFICIENT)
    if evidence["history_record_count"] < 1:
        reasons.append(REASON_HISTORY_RECORD_COUNT_INSUFFICIENT)
    reasons.extend(family_reasons)
    reasons.extend(edge_reasons)
    if _has_marker(sources, _LOW_INFORMATION_MARKERS):
        reasons.append(REASON_LOW_INFORMATION_BLOCKED)
    if _has_marker(sources, _SAFETY_MARKERS):
        reasons.append(REASON_SAFETY_ADJACENT_BLOCKED)
    if _has_marker(sources, _SELF_DENIAL_MARKERS):
        reasons.append(REASON_SELF_DENIAL_BLOCKED)
    if _has_marker(sources, _TARGET_JUDGEMENT_MARKERS):
        reasons.append(REASON_TARGET_JUDGEMENT_BLOCKED)
    reasons = _dedupe(reasons)

    hard_block_reasons = {
        REASON_P5_VISIBILITY_BOUNDARY_NOT_ALLOWED,
        REASON_SOURCE_SCOPE_NOT_OWNED_HISTORY,
        REASON_CURRENT_INPUT_MISSING,
        REASON_EVIDENCE_RECORD_COUNT_INSUFFICIENT,
        REASON_HISTORY_RECORD_COUNT_INSUFFICIENT,
        REASON_RAW_TEXT_PAYLOAD_DETECTED,
        REASON_CONTRACT_MUTATION_DETECTED,
        REASON_LOW_INFORMATION_BLOCKED,
        REASON_SAFETY_ADJACENT_BLOCKED,
        REASON_SELF_DENIAL_BLOCKED,
        REASON_TARGET_JUDGEMENT_BLOCKED,
    }
    family_or_edge = _most_restrictive([family_decision, edge_decision])
    if any(reason in hard_block_reasons or reason.startswith(REASON_FAMILY_BLOCKED) or reason.startswith(REASON_EDGE_FAMILY_UNSUPPORTED_BLOCKED) for reason in reasons):
        decision = DECISION_BLOCKED
    else:
        decision = family_or_edge

    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP,
        "source": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SOURCE,
        "run_id": run_id or "p5_history_line_eligibility_matrix",
        "decision": decision,
        "connectable": decision == DECISION_CONNECTABLE,
        "meta_only": decision == DECISION_META_ONLY,
        "review_required": decision == DECISION_REVIEW_REQUIRED,
        "blocked": decision == DECISION_BLOCKED,
        "rejection_reasons": reasons,
        "connectable_family": family,
        "family_decision": family_decision,
        "edge_family": primary_edge_family,
        "edge_decision": edge_decision,
        "edge_matrix": edge_matrix,
        "eligibility": {
            "p5_visibility_boundary_allowed": p5_boundary_allowed,
            "source_scope": source_scope,
            "owned_history_only": owned_history_only,
            **evidence,
        },
        "matrix_contract": {
            "limited_connectable_families": sorted(_CONNECTABLE_FAMILIES),
            "allow_edge_families": sorted(_ALLOW_EDGE_FAMILIES),
            "review_required_edge_families": sorted(_REVIEW_EDGE_FAMILIES),
            "meta_only_edge_families": sorted(_META_ONLY_EDGE_FAMILIES),
            "blocked_families_initial_p5": sorted(_BLOCKED_FAMILIES),
        },
        "visible_surface_connected": False,
        "comment_text_generated_by_this_layer": False,
        "p5_runtime_change_applied": False,
        "body_free_case_references_only": True,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_user_label_connection_p5_eligibility_matrix_contract(summary)
    return summary


def user_label_connection_p5_eligibility_matrix_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _safe_mapping(value)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP,
        "decision": _clean(meta.get("decision")) or DECISION_BLOCKED,
        "connectable": meta.get("connectable") is True,
        "meta_only": meta.get("meta_only") is True,
        "review_required": meta.get("review_required") is True,
        "blocked": meta.get("blocked") is True,
        "rejection_reasons": _dedupe(meta.get("rejection_reasons")),
        "connectable_family": _clean(meta.get("connectable_family")),
        "edge_family": _clean(meta.get("edge_family")),
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
    }
    assert_user_label_connection_p5_eligibility_matrix_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_p5_eligibility_matrix_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("P5 eligibility matrix must not include raw text/comment/history payload keys")
    if _flag_true(value):
        raise ValueError("P5 eligibility matrix contains a forbidden true flag")
    json.dumps(value, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not isinstance(value, Mapping):
        raise ValueError("P5 eligibility matrix must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P5 eligibility matrix schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP:
        raise ValueError("unexpected P5 eligibility matrix step")
    if value.get("decision") not in {DECISION_CONNECTABLE, DECISION_META_ONLY, DECISION_REVIEW_REQUIRED, DECISION_BLOCKED}:
        raise ValueError("unexpected P5 eligibility matrix decision")
    public_contract = _safe_mapping(value.get("public_contract"))
    body_free = _safe_mapping(value.get("body_free"))
    for key in ("rn_visible_contract_changed", "public_response_key_added", "response_shape_changed", "db_schema_changed", "fixed_sentence_template_added"):
        if public_contract.get(key) is not False:
            raise ValueError(f"P5 eligibility public_contract.{key} must be false")
    for key in ("raw_text_included", "comment_text_body_included", "candidate_body_included", "history_raw_text_included"):
        if body_free.get(key) is not False:
            raise ValueError(f"P5 eligibility body_free.{key} must be false")


__all__ = [
    "USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP",
    "USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SOURCE",
    "DECISION_CONNECTABLE",
    "DECISION_META_ONLY",
    "DECISION_REVIEW_REQUIRED",
    "DECISION_BLOCKED",
    "build_user_label_connection_p5_eligibility_matrix",
    "user_label_connection_p5_eligibility_matrix_public_summary",
    "assert_user_label_connection_p5_eligibility_matrix_contract",
]
