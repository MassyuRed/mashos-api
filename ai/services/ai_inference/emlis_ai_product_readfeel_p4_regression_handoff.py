# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-10 regression handoff and P5 hold re-check for Product Read Feel.

This module is a meta-only handoff boundary.  It consumes the P4-9
ratings-only review plus body-free regression suite statuses, then records
whether P5 must remain held.  It does not generate or rewrite Emlis visible
text, relax gates, change RN/API/DB contracts, or unlock P5 unless the P4-9
review already carries explicit full current-only clean evidence and required
regression suites are green.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_P4_NEXT_P5_HOLD,
    DECISION_P5_READY_AFTER_P4,
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609,
)
from emlis_ai_product_readfeel_p4_ratings_review import (
    assert_product_readfeel_p4_ratings_review_meta_only_20260610,
    build_product_readfeel_p4_ratings_review_public_summary_20260610,
)

PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.regression_handoff.20260610.v1"
)
PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUITE_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.regression_suite_status.20260610.v1"
)
PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.regression_handoff_summary.20260610.v1"
)
PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610: Final = (
    "P4-10_Regression_P5_Hold_Recheck_Handoff"
)
PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SOURCE_20260610: Final = (
    "Cocolon_EmlisAI_P4_FamilyProductTuning_RegressionHandoff_20260610"
)
PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_PROFILE_20260610: Final = (
    "p4_10_regression_p5_hold_recheck_handoff"
)

STATUS_PASSED: Final = "passed"
STATUS_FAILED: Final = "failed"
STATUS_TIMEOUT: Final = "timeout"
STATUS_NOT_EXECUTED: Final = "not_executed"
STATUS_BLOCKED: Final = "blocked"

P4_10_REQUIRED_REGRESSION_SUITES_20260610: Final[tuple[str, ...]] = (
    "p4_new_tests",
    "p3_product_readfeel_regression",
    "product_readfeel_surface_guard_subset",
    "public_recovery_limited_source_unavailable_subset",
    "user_label_connection_boundary_subset",
    "backend_contract",
    "display_contract",
    "two_stage_e2e",
    "rn_contract",
)
P4_10_OPTIONAL_LEDGER_SUITES_20260610: Final[tuple[str, ...]] = (
    "p3_p4_combined_command",
    "backend_contract_display_two_stage_combined",
    "full_backend_suite",
)

P4_10_REASON_REQUIRED_REGRESSION_NOT_GREEN: Final = "required_regression_not_green"
P4_10_REASON_REQUIRED_REGRESSION_MISSING: Final = "required_regression_missing"
P4_10_REASON_COMMAND_TIMEOUT: Final = "command_timeout_recorded"
P4_10_REASON_P4_9_REVIEW_MISSING: Final = "p4_9_ratings_review_missing"
P4_10_REASON_P4_9_P5_HOLD: Final = "p4_9_redecision_keeps_p5_hold"
P4_10_REASON_P4_9_BLOCKERS_REMAIN: Final = "p4_9_remaining_blockers_or_unreviewed_cases"

_FORBIDDEN_BODY_KEYS_20260610: Final[frozenset[str]] = frozenset(
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
_FORBIDDEN_TRUE_FLAGS_20260610: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_physical_name_changed",
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
        "product_quality_released",
        "release_allowed",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "exact_comment_text_locked",
        "exact_comment_text_required",
        "case_specific_runtime_branch",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
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
    if value is None:
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 128) -> str:
    text = _clean(value) or default
    chars = [ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "-" for ch in text[:max_length]]
    return "".join(chars).strip("-") or default


def _listify(value: Iterable[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.keys())
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_BODY_KEYS_20260610:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            current_path = f"{path}.{key_text}"
            if key_text in _FORBIDDEN_TRUE_FLAGS_20260610 and child is True:
                return current_path
            nested = _forbidden_true_flag_path(child, path=current_path)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for index, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def assert_product_readfeel_p4_regression_handoff_meta_only_20260610(
    payload: Mapping[str, Any],
    *,
    source: str = "p4_10_regression_handoff",
) -> None:
    """Reject body-bearing, release-mutating, or gate-relaxing handoff payloads."""

    if not isinstance(payload, Mapping):
        raise TypeError(f"{source} must be a mapping")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} must not contain input/output/history/reviewer/test body keys")
    true_flag_path = _forbidden_true_flag_path(payload, path=source)
    if true_flag_path:
        raise ValueError(f"{source} contains forbidden true flag: {true_flag_path}")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        payload, source=f"{source}.p3_p4_p5_boundary"
    )


def normalize_product_readfeel_p4_regression_suite_status_20260610(
    suite_status: Mapping[str, Any] | None,
    *,
    index: int = 0,
) -> dict[str, Any]:
    if not isinstance(suite_status, Mapping):
        raise TypeError("P4-10 regression suite status must be a mapping")
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(
        suite_status, source="p4_10.source_regression_suite_status"
    )
    suite_id = _safe_identifier(suite_status.get("suite_id") or suite_status.get("id"), default=f"suite-{index:03d}")
    status = _clean(suite_status.get("status")).lower() or STATUS_NOT_EXECUTED
    if status not in {STATUS_PASSED, STATUS_FAILED, STATUS_TIMEOUT, STATUS_NOT_EXECUTED, STATUS_BLOCKED}:
        status = STATUS_NOT_EXECUTED
    required = suite_status.get("required")
    is_required = suite_id in P4_10_REQUIRED_REGRESSION_SUITES_20260610 if required is None else _bool(required)
    passed_count = _to_int(suite_status.get("passed_count"), 0)
    failed_count = _to_int(suite_status.get("failed_count"), 0)
    warning_count = _to_int(suite_status.get("warning_count"), 0)
    timed_out = status == STATUS_TIMEOUT or _bool(suite_status.get("timed_out"))
    passed = status == STATUS_PASSED and failed_count == 0 and not timed_out
    reason_codes = _dedupe(suite_status.get("reason_codes") or suite_status.get("failure_codes"))
    if timed_out:
        reason_codes.append(P4_10_REASON_COMMAND_TIMEOUT)
    if status == STATUS_FAILED:
        reason_codes.append("suite_failed")
    if status in {STATUS_NOT_EXECUTED, STATUS_BLOCKED}:
        reason_codes.append(status)
    if is_required and not passed:
        reason_codes.append(P4_10_REASON_REQUIRED_REGRESSION_NOT_GREEN)
    normalized = {
        "schema_version": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUITE_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUITE_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610,
        "suite_id": suite_id,
        "status": status,
        "required": is_required,
        "passed": passed,
        "timed_out": timed_out,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "warning_count": warning_count,
        "reason_codes": _dedupe(reason_codes),
        "body_free_suite_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
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
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(
        normalized, source="p4_10.normalized_regression_suite_status"
    )
    return normalized


def _required_regression_status(command_results: Sequence[Mapping[str, Any]]) -> tuple[bool, list[str], list[str]]:
    by_suite = {_clean(item.get("suite_id")): item for item in command_results}
    blockers: list[str] = []
    missing: list[str] = []
    for suite_id in P4_10_REQUIRED_REGRESSION_SUITES_20260610:
        item = by_suite.get(suite_id)
        if not item:
            missing.append(suite_id)
            blockers.append(f"{P4_10_REASON_REQUIRED_REGRESSION_MISSING}:{suite_id}")
            continue
        if item.get("passed") is not True:
            blockers.append(f"{P4_10_REASON_REQUIRED_REGRESSION_NOT_GREEN}:{suite_id}")
    return not blockers, blockers, missing


def _non_blocking_notes(command_results: Sequence[Mapping[str, Any]]) -> list[str]:
    notes: list[str] = []
    for item in command_results:
        if item.get("required") is True:
            continue
        suite_id = _clean(item.get("suite_id"))
        if item.get("timed_out") is True:
            notes.append(f"{P4_10_REASON_COMMAND_TIMEOUT}:{suite_id}")
        elif item.get("passed") is not True and _clean(item.get("status")) != STATUS_NOT_EXECUTED:
            notes.append(f"optional_regression_not_green:{suite_id}")
    return _dedupe(notes)


def _summary(
    *,
    run_id: str,
    p4_ratings_summary: Mapping[str, Any],
    command_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    all_required_green, regression_blockers, missing_required = _required_regression_status(command_results)
    optional_notes = _non_blocking_notes(command_results)
    p4_9_review_ready = bool(p4_ratings_summary)
    p4_9_next_phase = _clean(p4_ratings_summary.get("post_p4_p3_9_next_phase_decision"))
    p4_9_p5_allowed = p4_ratings_summary.get("post_p4_p5_connection_allowed") is True
    p4_9_target_floor_met = p4_ratings_summary.get("p4_target_subset_floor_met") is True
    p4_9_blockers_remain = bool(p4_ratings_summary.get("unresolved_reason_counts")) or bool(
        _to_int(p4_ratings_summary.get("unreviewed_case_count"), 0)
    )
    p5_connection_handoff_allowed = bool(
        p4_9_review_ready
        and p4_9_next_phase == DECISION_P5_READY_AFTER_P4
        and p4_9_p5_allowed
        and all_required_green
        and not regression_blockers
    )
    p5_hold_reasons = _dedupe(p4_ratings_summary.get("post_p4_p5_hold_reason_codes"))
    p5_hold_material: list[str] = []
    if not p4_9_review_ready:
        p5_hold_material.append(P4_10_REASON_P4_9_REVIEW_MISSING)
    if p4_9_next_phase == DECISION_P4_NEXT_P5_HOLD or not p4_9_p5_allowed:
        p5_hold_material.append(P4_10_REASON_P4_9_P5_HOLD)
    if p4_9_blockers_remain:
        p5_hold_material.append(P4_10_REASON_P4_9_BLOCKERS_REMAIN)
    p5_hold_material.extend(p5_hold_reasons)
    p5_hold_material.extend(regression_blockers)
    if p5_connection_handoff_allowed:
        recommended_next_action = "prepare_p5_user_label_connection_visible_surface_strengthening_after_handoff"
    elif regression_blockers:
        recommended_next_action = "rerun_missing_or_timeout_regression_before_p5_handoff"
    elif p4_9_target_floor_met:
        recommended_next_action = "handoff_p4_results_with_p5_hold_until_full_current_only_recheck"
    else:
        recommended_next_action = "continue_p4_repair_for_remaining_ratings_or_boundary_blockers"

    suite_counts = {
        "total": len(command_results),
        "required": sum(1 for item in command_results if item.get("required") is True),
        "passed": sum(1 for item in command_results if item.get("passed") is True),
        "failed": sum(1 for item in command_results if item.get("status") == STATUS_FAILED),
        "timeout": sum(1 for item in command_results if item.get("timed_out") is True),
        "not_executed": sum(1 for item in command_results if item.get("status") == STATUS_NOT_EXECUTED),
    }
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_PROFILE_20260610,
        "p4_10_handoff_packet_created": True,
        "p4_10_handoff_only": True,
        "p4_10_regression_recheck_ready": bool(command_results),
        "p4_9_ratings_review_ready": p4_9_review_ready,
        "p4_9_ratings_only_review_ready": p4_ratings_summary.get("p4_9_ratings_only_review_ready") is True,
        "p4_9_target_subset_floor_met": p4_9_target_floor_met,
        "p4_9_target_subset_review_complete": p4_ratings_summary.get("target_subset_review_complete") is True,
        "p4_9_unresolved_reason_counts": dict(p4_ratings_summary.get("unresolved_reason_counts") or {}),
        "post_p4_p3_9_next_phase_decision": p4_9_next_phase,
        "post_p4_p5_connection_allowed": p4_9_p5_allowed,
        "post_p4_p5_hold_reason_codes": p5_hold_reasons,
        "post_p4_current_only_readfeel_minimum_met": p4_ratings_summary.get("post_p4_current_only_readfeel_minimum_met") is True,
        "post_p4_main_family_readfeel_minimum_met": p4_ratings_summary.get("post_p4_main_family_readfeel_minimum_met") is True,
        "required_regression_suites": list(P4_10_REQUIRED_REGRESSION_SUITES_20260610),
        "optional_regression_ledger_suites": list(P4_10_OPTIONAL_LEDGER_SUITES_20260610),
        "regression_suite_counts": suite_counts,
        "all_required_regression_green": all_required_green,
        "missing_required_regression_suites": missing_required,
        "required_regression_blockers": regression_blockers,
        "non_blocking_regression_notes": optional_notes,
        "p5_hold_rechecked": True,
        "p5_hold_continues": not p5_connection_handoff_allowed,
        "p5_hold_material": _dedupe(p5_hold_material),
        "p5_connection_handoff_allowed": p5_connection_handoff_allowed,
        "recommended_next_action": recommended_next_action,
        "handoff_requires_full_current_only_recheck": not p5_connection_handoff_allowed,
        "handoff_requires_rn_contract_when_available": (
            "rn_contract" in missing_required
            or "required_regression_not_green:rn_contract" in regression_blockers
        ),
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_regression_status_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
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
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(summary, source="p4_10.summary")
    return summary


def build_product_readfeel_p4_regression_handoff_20260610(
    *,
    p4_ratings_review: Mapping[str, Any] | None = None,
    p4_ratings_summary: Mapping[str, Any] | None = None,
    regression_suite_statuses: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    run_id_value = _safe_identifier(run_id, default="p4_10_regression_handoff")
    if p4_ratings_review is not None:
        assert_product_readfeel_p4_ratings_review_meta_only_20260610(
            p4_ratings_review, source="p4_10.p4_ratings_review"
        )
        ratings_summary = build_product_readfeel_p4_ratings_review_public_summary_20260610(p4_ratings_review)
    else:
        ratings_summary = dict(p4_ratings_summary or {})
        if ratings_summary:
            assert_product_readfeel_p4_ratings_review_meta_only_20260610(
                ratings_summary, source="p4_10.p4_ratings_summary"
            )
    command_results = [
        normalize_product_readfeel_p4_regression_suite_status_20260610(
            item,
            index=index,
        )
        for index, item in enumerate(list(regression_suite_statuses or []), start=1)
    ]
    summary = _summary(
        run_id=run_id_value,
        p4_ratings_summary=ratings_summary,
        command_results=command_results,
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_PROFILE_20260610,
        "summary": summary,
        "p4_ratings_review_summary": ratings_summary,
        "regression_suite_statuses": command_results,
        "public_summary": {},
        "p4_10_handoff_packet_created": True,
        "p4_10_handoff_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_regression_status_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
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
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    payload["public_summary"] = build_product_readfeel_p4_regression_handoff_public_summary_20260610(payload)
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(payload, source="p4_10.payload")
    return payload


def build_product_readfeel_p4_regression_handoff_public_summary_20260610(
    handoff_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(handoff_payload_or_summary or {})
    source = dict(payload.get("summary") or payload)
    public_summary = dict(source)
    public_summary["schema_version"] = PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610
    public_summary["version"] = PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610
    public_summary["source"] = PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SOURCE_20260610
    public_summary["source_step"] = PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610
    suites = [dict(item) for item in payload.get("regression_suite_statuses") or [] if isinstance(item, Mapping)]
    public_summary["regression_suite_summary"] = [
        {
            "suite_id": _clean(item.get("suite_id")),
            "status": _clean(item.get("status")),
            "required": item.get("required") is True,
            "passed": item.get("passed") is True,
            "timed_out": item.get("timed_out") is True,
            "warning_count": _to_int(item.get("warning_count"), 0),
            "reason_codes": _dedupe(item.get("reason_codes")),
        }
        for item in suites
    ]
    public_summary.pop("p4_ratings_review_summary", None)
    public_summary.pop("regression_suite_statuses", None)
    public_summary.pop("command_results", None)
    public_summary["ratings_only_payload"] = True
    public_summary["public_text_payload_excluded"] = True
    public_summary["body_free_case_references_only"] = True
    public_summary["body_free_regression_status_only"] = True
    public_summary["comment_text_body_included"] = False
    public_summary["raw_input_included"] = False
    public_summary["candidate_body_included"] = False
    public_summary["history_raw_text_included"] = False
    public_summary["raw_test_output_included"] = False
    public_summary["command_output_included"] = False
    public_summary["terminal_output_included"] = False
    public_summary["machine_metrics_used_for_read_feeling"] = False
    public_summary["read_feeling_auto_filled_from_machine_metrics"] = False
    public_summary["p4_runtime_tuning_applied"] = False
    public_summary["p5_visible_surface_strengthened"] = False
    public_summary["p5_runtime_change_applied"] = False
    public_summary["gate_relaxed"] = False
    public_summary["product_gate_ready"] = False
    public_summary["public_release_applied"] = False
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(
        public_summary, source="p4_10.public_summary"
    )
    return public_summary


def dump_product_readfeel_p4_regression_handoff_public_summary_20260610(
    handoff_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p4_regression_handoff_public_summary_20260610(
        handoff_payload_or_summary
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610",
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUITE_VERSION_20260610",
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610",
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_PROFILE_20260610",
    "STATUS_PASSED",
    "STATUS_FAILED",
    "STATUS_TIMEOUT",
    "STATUS_NOT_EXECUTED",
    "P4_10_REQUIRED_REGRESSION_SUITES_20260610",
    "assert_product_readfeel_p4_regression_handoff_meta_only_20260610",
    "normalize_product_readfeel_p4_regression_suite_status_20260610",
    "build_product_readfeel_p4_regression_handoff_20260610",
    "build_product_readfeel_p4_regression_handoff_public_summary_20260610",
    "dump_product_readfeel_p4_regression_handoff_public_summary_20260610",
]
