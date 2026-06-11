# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-0 readiness freeze for User Label Connection visible work.

This module reads body-free P4 handoff / ratings summaries and decides whether
P5 visible User Label Connection work may begin.  It does not generate or alter
``comment_text``, does not connect visible history lines, and does not change
RN/API/DB/public response contracts.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final


USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_readiness.v1"
)
USER_LABEL_CONNECTION_P5_READINESS_STEP: Final = (
    "P5-0_P4_Handoff_CurrentOnlyReadfeel_RecheckFreeze"
)
USER_LABEL_CONNECTION_P5_READINESS_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_ReadinessFreeze_20260611"
)

P5_ENTRY_DECISION_ALLOWED: Final = "p5_entry_allowed"
P5_ENTRY_DECISION_HOLD: Final = "p5_entry_hold"
P5_ENTRY_DECISION_REGRESSION_BLOCKED: Final = "p5_entry_regression_blocked"
P5_ENTRY_DECISION_CURRENT_ONLY_RECHECK_REQUIRED: Final = (
    "p5_entry_current_only_recheck_required"
)
P5_ENTRY_DECISION_BLOCKED_UNSAFE_PAYLOAD: Final = "p5_entry_blocked_unsafe_payload"

REASON_P4_HANDOFF_MISSING: Final = "p4_handoff_missing"
REASON_REQUIRED_REGRESSION_NOT_GREEN: Final = "required_regression_not_green"
REASON_P4_P5_CONNECTION_NOT_ALLOWED: Final = "post_p4_p5_connection_not_allowed"
REASON_CURRENT_ONLY_READFEEL_NOT_MET: Final = "current_only_readfeel_minimum_not_met"
REASON_MAIN_FAMILY_READFEEL_NOT_MET: Final = "main_family_readfeel_minimum_not_met"
REASON_HISTORY_LINE_MASKS_CURRENT_INPUT_GAP: Final = "history_line_masks_current_input_gap"
REASON_P5_HOLD_REASON_CODES_PRESENT: Final = "p5_hold_reason_codes_present"
REASON_P5_VISIBLE_ALREADY_STRENGTHENED: Final = "p5_visible_surface_already_strengthened"
REASON_P5_RUNTIME_ALREADY_CHANGED: Final = "p5_runtime_change_already_applied"
REASON_UNSAFE_TEXT_PAYLOAD: Final = "unsafe_text_payload_detected"
REASON_CONTRACT_MUTATION: Final = "contract_mutation_detected"

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
        "stdout",
        "stderr",
        "raw_test_output",
        "test_output",
        "traceback",
        "traceback_body",
        "command_output",
        "terminal_output",
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
        "public_payload_changed",
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
        "raw_test_output_included",
        "command_output_included",
        "terminal_output_included",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "exact_comment_text_locked",
        "exact_comment_text_required",
        "case_specific_runtime_branch",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "runtime_repair_applied",
        "implementation_change_applied",
        "p4_runtime_tuning_applied",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "schema_file_materialized",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


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


def _summary_from(value: Any) -> dict[str, Any]:
    meta = _safe_mapping(value)
    for key in ("summary", "public_summary", "p4_10_summary", "p4_ratings_review_summary"):
        nested = _safe_mapping(meta.get(key))
        if nested:
            return nested
    return meta


def _first_bool(sources: Sequence[Mapping[str, Any]], *keys: str, default: bool = False) -> bool:
    for source in sources:
        for key in keys:
            if key in source:
                return source.get(key) is True
    return default


def _first_list(sources: Sequence[Mapping[str, Any]], *keys: str) -> list[str]:
    for source in sources:
        for key in keys:
            values = _dedupe(source.get(key))
            if values:
                return values
    return []


def _build_public_contract() -> dict[str, bool]:
    return {
        "rn_contract_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "db_physical_name_changed": False,
        "release_allowed": False,
    }


def _build_body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _decision_from_reasons(
    *,
    unsafe_payload: bool,
    contract_mutation: bool,
    all_required_regression_green: bool,
    current_only_met: bool,
    main_family_met: bool,
    p5_entry_allowed: bool,
) -> str:
    if unsafe_payload or contract_mutation:
        return P5_ENTRY_DECISION_BLOCKED_UNSAFE_PAYLOAD
    if p5_entry_allowed:
        return P5_ENTRY_DECISION_ALLOWED
    if not all_required_regression_green:
        return P5_ENTRY_DECISION_REGRESSION_BLOCKED
    if not current_only_met or not main_family_met:
        return P5_ENTRY_DECISION_CURRENT_ONLY_RECHECK_REQUIRED
    return P5_ENTRY_DECISION_HOLD


def build_user_label_connection_p5_readiness(
    p4_regression_handoff: Mapping[str, Any] | None = None,
    *,
    p4_ratings_summary: Mapping[str, Any] | None = None,
    connection_decision_summary: Mapping[str, Any] | None = None,
    user_label_connection_public_summary: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P5 entry readiness summary.

    P5 visible work is allowed only when P4 explicitly hands off P5, current-only
    read-feel floors are met, required regression suites are green, and no
    history line masks current input gaps.
    """

    handoff = _summary_from(p4_regression_handoff or {})
    ratings = _summary_from(p4_ratings_summary or {})
    connection = _summary_from(connection_decision_summary or {})
    user_label = _summary_from(user_label_connection_public_summary or {})
    sources: list[dict[str, Any]] = [handoff, ratings, connection, user_label]

    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)

    p4_handoff_seen = (
        handoff.get("p4_10_handoff_packet_created") is True
        or _clean(handoff.get("source_step")) == "P4-10_Regression_P5_Hold_Recheck_Handoff"
        or "p5_connection_handoff_allowed" in handoff
    )
    all_required_regression_green = _first_bool(sources, "all_required_regression_green")
    post_p4_p5_connection_allowed = _first_bool(
        sources,
        "post_p4_p5_connection_allowed",
        "p5_connection_allowed",
        "p5_connection_handoff_allowed",
    )
    current_only_met = _first_bool(
        sources,
        "post_p4_current_only_readfeel_minimum_met",
        "current_only_readfeel_minimum_met",
    )
    main_family_met = _first_bool(
        sources,
        "post_p4_main_family_readfeel_minimum_met",
        "main_family_readfeel_minimum_met",
    )
    history_masks_current = _first_bool(
        sources,
        "history_line_masks_current_input_gap",
        "history_line_masking_observed",
        "history_line_masks_current_input",
    )
    visible_already_strengthened = _first_bool(sources, "p5_visible_surface_strengthened")
    runtime_already_changed = _first_bool(sources, "p5_runtime_change_applied")

    hold_codes = _first_list(
        sources,
        "post_p4_p5_hold_reason_codes",
        "p5_hold_reason_codes",
        "p5_hold_material",
    )
    regression_blockers = _first_list(sources, "required_regression_blockers", "regression_blockers")

    reason_codes: list[str] = []
    if unsafe_payload:
        reason_codes.append(REASON_UNSAFE_TEXT_PAYLOAD)
    if contract_mutation:
        reason_codes.append(REASON_CONTRACT_MUTATION)
    if not p4_handoff_seen:
        reason_codes.append(REASON_P4_HANDOFF_MISSING)
    if not all_required_regression_green:
        reason_codes.append(REASON_REQUIRED_REGRESSION_NOT_GREEN)
    if not post_p4_p5_connection_allowed:
        reason_codes.append(REASON_P4_P5_CONNECTION_NOT_ALLOWED)
    if not current_only_met:
        reason_codes.append(REASON_CURRENT_ONLY_READFEEL_NOT_MET)
    if not main_family_met:
        reason_codes.append(REASON_MAIN_FAMILY_READFEEL_NOT_MET)
    if history_masks_current:
        reason_codes.append(REASON_HISTORY_LINE_MASKS_CURRENT_INPUT_GAP)
    if hold_codes:
        reason_codes.append(REASON_P5_HOLD_REASON_CODES_PRESENT)
    if visible_already_strengthened:
        reason_codes.append(REASON_P5_VISIBLE_ALREADY_STRENGTHENED)
    if runtime_already_changed:
        reason_codes.append(REASON_P5_RUNTIME_ALREADY_CHANGED)
    reason_codes.extend(f"p4_hold:{item}" for item in hold_codes)
    reason_codes.extend(f"regression:{item}" for item in regression_blockers)
    reason_codes = _dedupe(reason_codes)

    p5_entry_allowed = bool(
        p4_handoff_seen
        and all_required_regression_green
        and post_p4_p5_connection_allowed
        and current_only_met
        and main_family_met
        and not history_masks_current
        and not hold_codes
        and not regression_blockers
        and not visible_already_strengthened
        and not runtime_already_changed
        and not unsafe_payload
        and not contract_mutation
    )
    decision = _decision_from_reasons(
        unsafe_payload=unsafe_payload,
        contract_mutation=contract_mutation,
        all_required_regression_green=all_required_regression_green,
        current_only_met=current_only_met,
        main_family_met=main_family_met,
        p5_entry_allowed=p5_entry_allowed,
    )

    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_READINESS_STEP,
        "source": USER_LABEL_CONNECTION_P5_READINESS_SOURCE,
        "run_id": run_id or "p5_readiness_freeze",
        "decision": decision,
        "p4_10_handoff_packet_seen": p4_handoff_seen,
        "p4_10_handoff_packet_created": p4_handoff_seen,
        "all_required_regression_green": all_required_regression_green,
        "post_p4_p5_connection_allowed": post_p4_p5_connection_allowed,
        "post_p4_current_only_readfeel_minimum_met": current_only_met,
        "post_p4_main_family_readfeel_minimum_met": main_family_met,
        "history_line_masks_current_input_gap": history_masks_current,
        "p5_entry_allowed": p5_entry_allowed,
        "p5_visible_strengthening_allowed": p5_entry_allowed,
        "p5_hold_continues": not p5_entry_allowed,
        "p5_hold_reason_codes": reason_codes,
        "p4_hold_reason_codes": hold_codes,
        "required_regression_blockers": regression_blockers,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "p5_visible_surface_connected": False,
        "p5_runtime_visible_connection_applied": False,
        "readiness_freeze_only": True,
        "body_free_case_references_only": True,
        "public_contract": _build_public_contract(),
        "body_free": _build_body_free_contract(),
    }
    assert_user_label_connection_p5_readiness_contract(summary)
    return summary


def user_label_connection_p5_readiness_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _safe_mapping(value)
    if not meta:
        meta = build_user_label_connection_p5_readiness(None)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_READINESS_STEP,
        "decision": _clean(meta.get("decision")) or P5_ENTRY_DECISION_HOLD,
        "p5_entry_allowed": meta.get("p5_entry_allowed") is True,
        "p5_visible_strengthening_allowed": meta.get("p5_visible_strengthening_allowed") is True,
        "p5_hold_continues": meta.get("p5_hold_continues") is not False,
        "p5_hold_reason_codes": _dedupe(meta.get("p5_hold_reason_codes")),
        "all_required_regression_green": meta.get("all_required_regression_green") is True,
        "post_p4_current_only_readfeel_minimum_met": meta.get("post_p4_current_only_readfeel_minimum_met") is True,
        "post_p4_main_family_readfeel_minimum_met": meta.get("post_p4_main_family_readfeel_minimum_met") is True,
        "history_line_masks_current_input_gap": meta.get("history_line_masks_current_input_gap") is True,
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "history_raw_text_included": False,
    }
    assert_user_label_connection_p5_readiness_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_p5_readiness_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("P5 readiness must not include raw text/comment/candidate/history payload keys")
    if _flag_true(value):
        raise ValueError("P5 readiness contains a forbidden true flag")
    json.dumps(value, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not isinstance(value, Mapping):
        raise ValueError("P5 readiness must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION:
        raise ValueError("unexpected P5 readiness schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_P5_READINESS_STEP:
        raise ValueError("unexpected P5 readiness step")
    public_contract = _safe_mapping(value.get("public_contract"))
    body_free = _safe_mapping(value.get("body_free"))
    for key in ("rn_contract_changed", "response_shape_changed", "public_response_key_added", "db_schema_changed"):
        if public_contract.get(key) is not False:
            raise ValueError(f"P5 readiness public_contract.{key} must be false")
    for key in (
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "history_raw_text_included",
    ):
        if body_free.get(key) is not False:
            raise ValueError(f"P5 readiness body_free.{key} must be false")


__all__ = [
    "USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_READINESS_STEP",
    "USER_LABEL_CONNECTION_P5_READINESS_SOURCE",
    "P5_ENTRY_DECISION_ALLOWED",
    "P5_ENTRY_DECISION_HOLD",
    "P5_ENTRY_DECISION_REGRESSION_BLOCKED",
    "P5_ENTRY_DECISION_CURRENT_ONLY_RECHECK_REQUIRED",
    "P5_ENTRY_DECISION_BLOCKED_UNSAFE_PAYLOAD",
    "build_user_label_connection_p5_readiness",
    "user_label_connection_p5_readiness_public_summary",
    "assert_user_label_connection_p5_readiness_contract",
]
