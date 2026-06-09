# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-9 P4 / P5 connection decision for EmlisAI Product Read Feel baseline.

P3-9 is a decision boundary, not a runtime repair.  It consumes body-free
P3-8 regression material plus body-free P3 baseline connection evidence and
decides whether the next work should move into P4 family tuning, whether P5
User Label Connection visible-surface work may start, or whether the work must
return to P1/P2/P3 evidence first.

The payload intentionally never retains raw input, rendered ``comment_text``
bodies, reviewer free text, history raw text, raw test logs, DB material, or
release flags.  It also does not change RN/API/DB/runtime gates.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_regression import (
    DECISION_BLOCKED_NOT_EXECUTED as P3_8_DECISION_BLOCKED_NOT_EXECUTED,
    DECISION_BLOCKED_P1_DISPLAY as P3_8_DECISION_BLOCKED_P1_DISPLAY,
    DECISION_BLOCKED_P2_RED as P3_8_DECISION_BLOCKED_P2_RED,
    DECISION_BLOCKED_REQUIRED_FAILURE as P3_8_DECISION_BLOCKED_REQUIRED_FAILURE,
    DECISION_NO_RUNTIME_TARGET as P3_8_DECISION_NO_RUNTIME_TARGET,
    DECISION_READY_FOR_FIRST_REPAIR as P3_8_DECISION_READY_FOR_FIRST_REPAIR,
    DECISION_YELLOW_TIMEOUT as P3_8_DECISION_YELLOW_TIMEOUT,
    PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609,
    assert_product_readfeel_p3_regression_meta_only_20260609,
)
from emlis_ai_product_readfeel_rubric import assert_product_readfeel_rubric_meta_only

PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.p4_p5_connection_decision.20260609.v1"
)
PRODUCT_READFEEL_P3_P4_P5_CONNECTION_EVIDENCE_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.p4_p5_connection_evidence.20260609.v1"
)
PRODUCT_READFEEL_P3_P4_P5_CONNECTION_ITEM_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.p4_p5_connection_item.20260609.v1"
)
PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.p4_p5_connection_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609: Final = (
    "P3-9_P4_P5_Connection_Decision"
)
PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_P4P5ConnectionDecision_20260609"
)
PRODUCT_READFEEL_P3_P4_P5_CONNECTION_PROFILE_20260609: Final = (
    "local_product_readfeel_p3_p4_p5_connection_decision"
)

PHASE_P4_FAMILY_TUNING: Final = "P4_Family_Product_Tuning"
PHASE_P5_USER_LABEL_CONNECTION: Final = "P5_User_Label_Connection_v1"

DECISION_BLOCKED_BY_P2_RED: Final = "p3_9_blocked_by_p2_red_before_p4_p5"
DECISION_BLOCKED_BY_P1_DISPLAY: Final = "p3_9_blocked_by_p1_display_repair_before_p4_p5"
DECISION_BLOCKED_BY_REGRESSION: Final = "p3_9_blocked_by_required_regression_before_p4_p5"
DECISION_NEEDS_BASELINE_EVIDENCE: Final = "p3_9_needs_complete_baseline_evidence_before_p4_p5"
DECISION_P4_NEXT_P5_HOLD: Final = "p3_9_p4_family_tuning_next_p5_hold"
DECISION_P5_READY_AFTER_P4: Final = "p3_9_p5_connection_ready_after_current_only_readfeel"
DECISION_HOLD_AT_P3_FIRST_REPAIR: Final = "p3_9_hold_at_p3_first_repair_before_p4_p5"

P3_8_READY_DECISIONS_20260609: Final[frozenset[str]] = frozenset(
    {
        P3_8_DECISION_READY_FOR_FIRST_REPAIR,
        P3_8_DECISION_YELLOW_TIMEOUT,
    }
)
P3_8_REQUIRED_BLOCK_DECISIONS_20260609: Final[frozenset[str]] = frozenset(
    {
        P3_8_DECISION_BLOCKED_REQUIRED_FAILURE,
        P3_8_DECISION_BLOCKED_NOT_EXECUTED,
    }
)

P4_TARGET_REASON_CODES_20260609: Final[frozenset[str]] = frozenset(
    {
        "rich_input_low_information_overroute",
        "input_core_missing",
        "event_reaction_missing",
        "desire_fear_conflict_missing",
        "state_structure_missing",
        "limited_grounding_collapsed_to_question",
        "generic_reception_surface",
        "repeated_surface_signature",
        "family_temperature_flattened",
        "structure_question_answered_as_comfort",
        "positive_overweighted",
        "positive_underreceived",
        "p3_readfeel_gap",
        "p3_yellow_readfeel_weakness",
    }
)
P5_HOLD_REASON_CODES_20260609: Final[frozenset[str]] = frozenset(
    {
        "rich_input_low_information_overroute",
        "input_core_missing",
        "event_reaction_missing",
        "desire_fear_conflict_missing",
        "state_structure_missing",
        "limited_grounding_collapsed_to_question",
        "generic_reception_surface",
        "repeated_surface_signature",
        "family_temperature_flattened",
        "self_denial_identity_claim_risk",
        "relationship_target_judgement_risk",
        "structure_question_answered_as_comfort",
        "history_line_masks_current_input_gap",
        "current_only_readfeel_below_minimum",
        "history_line_masking_observed",
        "subscription_boundary_unverified",
        "user_label_connection_surface_safety_unverified",
        "user_label_connection_creepy_or_overclaim_risk",
    }
)
P5_SENSITIVE_FAMILIES_20260609: Final[frozenset[str]] = frozenset(
    {
        "self_denial",
        "relationship_boundary",
        "structure_question",
        "daily_unpleasant",
        "mixed_emotion",
        "long_meaning_arc",
    }
)
P4_TARGET_LAYER_MARKERS_20260609: Final[frozenset[str]] = frozenset(
    {
        "input_core_retention",
        "input_material_bundle",
        "material_quality",
        "public_surface_requirement",
        "gate_recovery_route",
        "family_temperature",
        "ratio_policy",
        "state_answer_ratio_policy",
        "complete_surface_realizer",
        "two_stage_section_surface_plan",
        "reception_mode_resolver",
    }
)

FORBIDDEN_BODY_KEYS_20260609: Final[frozenset[str]] = frozenset(
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
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "blind_qa_free_text",
        "stdout",
        "stderr",
        "raw_test_output",
        "test_output",
        "traceback_body",
        "body",
        "text",
    }
)
FORBIDDEN_TRUE_FLAGS_20260609: Final[frozenset[str]] = frozenset(
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
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text = _clean(value)
    if not text:
        text = default
    allowed = []
    for ch in text[:max_length]:
        allowed.append(ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "-")
    return "".join(allowed).strip("-") or default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, bool):
            return float(int(value))
        return float(value)
    except (TypeError, ValueError):
        return default


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        values = [values]
    elif isinstance(values, Mapping):
        values = list(values.keys())
    elif not isinstance(values, Iterable):
        values = [values]
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in FORBIDDEN_BODY_KEYS_20260609:
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
            if key_text in FORBIDDEN_TRUE_FLAGS_20260609 and child is True:
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


def assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
    payload: Mapping[str, Any],
    *,
    source: str = "p3_9_p4_p5_connection_decision",
) -> None:
    """Reject body-bearing or release/runtime-mutating P3-9 payloads."""
    if not isinstance(payload, Mapping):
        raise TypeError(f"{source} must be a mapping")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} must not contain local review, input, output, history, or raw log body keys")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} contains forbidden true flag: {flag_path}")
    assert_product_readfeel_rubric_meta_only(payload, source=f"{source}.rubric")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")


def _regression_summary(regression_result: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(regression_result, Mapping):
        return {}
    assert_product_readfeel_p3_regression_meta_only_20260609(regression_result, source="p3_9.regression_source")
    if regression_result.get("schema_version") == PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609:
        return dict(regression_result.get("summary") or regression_result.get("public_summary") or {})
    return dict(regression_result.get("summary") or regression_result)


def _normalize_connection_evidence(evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    if evidence is None:
        evidence = {}
    if not isinstance(evidence, Mapping):
        raise TypeError("p3_9 connection evidence must be a mapping")
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        evidence, source="p3_9.connection_evidence"
    )
    observed_families = _dedupe(evidence.get("observed_families") or evidence.get("families_with_p3_verdict"))
    required_families = list(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    missing_families = _dedupe(
        evidence.get("missing_families")
        or [family for family in required_families if family not in set(observed_families)]
    )
    repair_families = _dedupe(evidence.get("repair_required_families"))
    yellow_families = _dedupe(evidence.get("yellow_families"))
    pass_families = _dedupe(evidence.get("pass_families"))
    reason_codes = _dedupe(evidence.get("classified_reason_codes") or evidence.get("reason_codes"))
    p5_hold_reason_codes = _dedupe(evidence.get("p5_hold_reason_codes"))
    if evidence.get("history_line_masks_current_input_gap") is True:
        p5_hold_reason_codes.append("history_line_masking_observed")
    if evidence.get("subscription_boundary_ok") is False:
        p5_hold_reason_codes.append("subscription_boundary_unverified")
    if evidence.get("user_label_connection_surface_safe") is False:
        p5_hold_reason_codes.append("user_label_connection_surface_safety_unverified")
    if evidence.get("creepy_or_overclaim_or_self_blame_observed") is True:
        p5_hold_reason_codes.append("user_label_connection_creepy_or_overclaim_risk")
    if evidence.get("current_only_readfeel_minimum_met") is False:
        p5_hold_reason_codes.append("current_only_readfeel_below_minimum")
    p5_hold_reason_codes = _dedupe(p5_hold_reason_codes)

    normalized = {
        "schema_version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_EVIDENCE_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_EVIDENCE_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609,
        "baseline_case_count": _to_int(evidence.get("baseline_case_count"), 0),
        "p3_verdict_row_count": _to_int(evidence.get("p3_verdict_row_count"), 0),
        "required_family_count": len(required_families),
        "observed_families": observed_families,
        "missing_families": missing_families,
        "p2_red_count": _to_int(evidence.get("p2_red_count"), 0),
        "p2_red_independently_split": evidence.get("p2_red_independently_split") is True,
        "repair_required_families": repair_families,
        "yellow_families": yellow_families,
        "pass_families": pass_families,
        "classified_reason_codes": reason_codes,
        "first_repair_target_count": _to_int(evidence.get("first_repair_target_count"), 0),
        "first_repair_target_layers": _dedupe(evidence.get("first_repair_target_layers")),
        "first_repair_blocker_ids": _dedupe(evidence.get("first_repair_blocker_ids")),
        "current_only_readfeel_minimum_met": evidence.get("current_only_readfeel_minimum_met") is True,
        "current_only_min_read_feeling": _to_float(evidence.get("current_only_min_read_feeling"), 0.0),
        "current_only_min_naturalness": _to_float(evidence.get("current_only_min_naturalness"), 0.0),
        "current_only_min_non_template": _to_float(evidence.get("current_only_min_non_template"), 0.0),
        "main_family_readfeel_minimum_met": evidence.get("main_family_readfeel_minimum_met") is True,
        "history_line_eligible_slice_checked": evidence.get("history_line_eligible_slice_checked") is True,
        "history_line_masks_current_input_gap": evidence.get("history_line_masks_current_input_gap") is True,
        "subscription_boundary_ok": evidence.get("subscription_boundary_ok") is True,
        "user_label_connection_surface_safe": evidence.get("user_label_connection_surface_safe") is True,
        "creepy_or_overclaim_or_self_blame_observed": evidence.get("creepy_or_overclaim_or_self_blame_observed") is True,
        "p4_family_tuning_completed": evidence.get("p4_family_tuning_completed") is True,
        "p5_hold_reason_codes": p5_hold_reason_codes,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        normalized, source="p3_9.normalized_evidence"
    )
    return normalized


def _regression_allows_p4_p5(summary: Mapping[str, Any]) -> bool:
    decision = _clean(summary.get("decision"))
    if decision in P3_8_READY_DECISIONS_20260609:
        return bool(summary.get("required_regression_green"))
    return False


def _p4_conditions(evidence: Mapping[str, Any]) -> tuple[bool, list[str], list[str]]:
    hold_reasons: list[str] = []
    met_conditions: list[str] = []
    observed = set(_dedupe(evidence.get("observed_families")))
    missing = _dedupe(evidence.get("missing_families"))
    reason_codes = set(_dedupe(evidence.get("classified_reason_codes")))
    target_layers = set(_dedupe(evidence.get("first_repair_target_layers")))
    first_blockers = set(_dedupe(evidence.get("first_repair_blocker_ids")))

    if _to_int(evidence.get("baseline_case_count"), 0) >= 60 and _to_int(evidence.get("p3_verdict_row_count"), 0) >= 60:
        met_conditions.append("baseline_60_cases_and_verdicts_present")
    else:
        hold_reasons.append("baseline_60_case_or_verdict_count_missing")
    if set(PRODUCT_READFEEL_REQUIRED_FAMILIES).issubset(observed) and not missing:
        met_conditions.append("all_12_required_families_have_p3_verdict")
    else:
        hold_reasons.append("missing_required_family_verdicts")
    if _to_int(evidence.get("p2_red_count"), 0) == 0 or evidence.get("p2_red_independently_split") is True:
        met_conditions.append("p2_red_zero_or_independently_split")
    else:
        hold_reasons.append("p2_red_not_independently_split")
    if reason_codes:
        met_conditions.append("repair_and_yellow_reason_codes_classified")
    else:
        hold_reasons.append("repair_and_yellow_reason_codes_missing")
    if reason_codes & P4_TARGET_REASON_CODES_20260609 or target_layers & P4_TARGET_LAYER_MARKERS_20260609 or first_blockers & P4_TARGET_REASON_CODES_20260609:
        met_conditions.append("first_targets_visible_as_input_core_or_family_tuning")
    else:
        hold_reasons.append("first_targets_not_visible_as_p4_tuning_material")

    allowed = not hold_reasons
    return allowed, met_conditions, hold_reasons


def _p5_conditions(evidence: Mapping[str, Any]) -> tuple[bool, list[str], list[str]]:
    hold_reasons: list[str] = []
    met_conditions: list[str] = []
    reason_codes = set(_dedupe(evidence.get("classified_reason_codes")))
    p5_hold_codes = set(_dedupe(evidence.get("p5_hold_reason_codes")))
    repair_families = set(_dedupe(evidence.get("repair_required_families")))
    yellow_families = set(_dedupe(evidence.get("yellow_families")))

    readfeel_ok = bool(evidence.get("current_only_readfeel_minimum_met")) or (
        _to_float(evidence.get("current_only_min_read_feeling"), 0.0) >= 0.80
        and _to_float(evidence.get("current_only_min_naturalness"), 0.0) >= 0.80
        and _to_float(evidence.get("current_only_min_non_template"), 0.0) >= 0.80
    )
    if readfeel_ok and bool(evidence.get("main_family_readfeel_minimum_met")):
        met_conditions.append("current_only_major_families_readfeel_minimum_met")
    else:
        hold_reasons.append("current_only_readfeel_not_yet_stable")

    if bool(evidence.get("history_line_eligible_slice_checked")) and not bool(evidence.get("history_line_masks_current_input_gap")):
        met_conditions.append("history_line_eligible_slice_does_not_mask_current_input_gap")
    else:
        hold_reasons.append("history_line_eligible_slice_not_clean")

    if bool(evidence.get("subscription_boundary_ok")):
        met_conditions.append("free_plus_premium_boundary_kept")
    else:
        hold_reasons.append("subscription_boundary_not_confirmed")

    if bool(evidence.get("user_label_connection_surface_safe")) and not bool(evidence.get("creepy_or_overclaim_or_self_blame_observed")):
        met_conditions.append("user_label_connection_surface_has_no_creepy_overclaim_self_blame_signal")
    else:
        hold_reasons.append("user_label_connection_surface_safety_not_confirmed")

    if not (reason_codes & P5_HOLD_REASON_CODES_20260609) and not (p5_hold_codes & P5_HOLD_REASON_CODES_20260609):
        met_conditions.append("no_p5_hold_reason_codes")
    else:
        hold_reasons.append("p5_hold_reason_codes_present")

    if not ((repair_families | yellow_families) & P5_SENSITIVE_FAMILIES_20260609):
        met_conditions.append("sensitive_families_do_not_have_current_only_repair_or_yellow_gap")
    else:
        hold_reasons.append("sensitive_families_still_have_current_only_gap")

    allowed = not hold_reasons
    return allowed, met_conditions, _dedupe(hold_reasons)


def _connection_item(
    *,
    phase_id: str,
    allowed: bool,
    met_conditions: Sequence[Any],
    hold_reasons: Sequence[Any],
    recommended_next_action: str,
    run_id: str,
) -> dict[str, Any]:
    item = {
        "schema_version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_ITEM_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_ITEM_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609,
        "run_id": run_id,
        "target_phase": phase_id,
        "allowed_to_connect": allowed,
        "met_conditions": _dedupe(met_conditions),
        "hold_reasons": _dedupe(hold_reasons),
        "recommended_next_action": _safe_identifier(recommended_next_action, default="manual_review"),
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(item, source="p3_9.connection_item")
    return item


def _summary(
    *,
    regression_summary: Mapping[str, Any],
    evidence: Mapping[str, Any],
    p4_allowed: bool,
    p4_met: Sequence[str],
    p4_hold: Sequence[str],
    p5_allowed: bool,
    p5_met: Sequence[str],
    p5_hold: Sequence[str],
    run_id: str,
) -> dict[str, Any]:
    p3_8_decision = _clean(regression_summary.get("decision"))
    regression_ready = _regression_allows_p4_p5(regression_summary)
    p2_red_present = bool(regression_summary.get("p2_red_present") or regression_summary.get("p2_red_blocks_p3_repair"))
    p1_display_repair_present = bool(regression_summary.get("p1_display_repair_present"))
    baseline_complete = "baseline_60_case_or_verdict_count_missing" not in set(p4_hold) and "missing_required_family_verdicts" not in set(p4_hold)

    if p2_red_present or p3_8_decision == P3_8_DECISION_BLOCKED_P2_RED:
        decision = DECISION_BLOCKED_BY_P2_RED
        p4_allowed = False
        p5_allowed = False
    elif p1_display_repair_present or p3_8_decision == P3_8_DECISION_BLOCKED_P1_DISPLAY:
        decision = DECISION_BLOCKED_BY_P1_DISPLAY
        p4_allowed = False
        p5_allowed = False
    elif not regression_ready or p3_8_decision in P3_8_REQUIRED_BLOCK_DECISIONS_20260609:
        decision = DECISION_BLOCKED_BY_REGRESSION
        p4_allowed = False
        p5_allowed = False
    elif not baseline_complete:
        decision = DECISION_NEEDS_BASELINE_EVIDENCE
        p4_allowed = False
        p5_allowed = False
    elif p5_allowed:
        decision = DECISION_P5_READY_AFTER_P4
    elif p4_allowed:
        decision = DECISION_P4_NEXT_P5_HOLD
    else:
        decision = DECISION_HOLD_AT_P3_FIRST_REPAIR

    p5_hold_codes = _dedupe(evidence.get("p5_hold_reason_codes"))
    p4_next_actions = []
    if p4_allowed:
        p4_next_actions.append("move_to_p4_family_product_tuning_with_current_input_repair_targets")
    elif decision == DECISION_HOLD_AT_P3_FIRST_REPAIR:
        p4_next_actions.append("finish_p3_first_repair_design_before_p4_connection")
    p5_next_actions = []
    if p5_allowed:
        p5_next_actions.append("prepare_p5_user_label_connection_visible_surface_strengthening")
    else:
        p5_next_actions.append("hold_p5_until_current_only_readfeel_is_stable")

    summary = {
        "schema_version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_PROFILE_20260609,
        "source_p3_8_decision": p3_8_decision,
        "source_p3_8_required_regression_green": bool(regression_summary.get("required_regression_green")),
        "source_p3_8_p3_runtime_repair_can_start": bool(
            regression_summary.get("p3_runtime_repair_can_start_after_regression")
        ),
        "p2_red_present": p2_red_present,
        "p1_display_repair_present": p1_display_repair_present,
        "baseline_case_count": _to_int(evidence.get("baseline_case_count"), 0),
        "p3_verdict_row_count": _to_int(evidence.get("p3_verdict_row_count"), 0),
        "required_family_count": _to_int(evidence.get("required_family_count"), len(PRODUCT_READFEEL_REQUIRED_FAMILIES)),
        "observed_family_count": len(_dedupe(evidence.get("observed_families"))),
        "missing_families": _dedupe(evidence.get("missing_families")),
        "repair_required_families": _dedupe(evidence.get("repair_required_families")),
        "yellow_families": _dedupe(evidence.get("yellow_families")),
        "classified_reason_codes": _dedupe(evidence.get("classified_reason_codes")),
        "first_repair_target_count": _to_int(evidence.get("first_repair_target_count"), 0),
        "first_repair_target_layers": _dedupe(evidence.get("first_repair_target_layers")),
        "current_only_readfeel_minimum_met": bool(evidence.get("current_only_readfeel_minimum_met")),
        "main_family_readfeel_minimum_met": bool(evidence.get("main_family_readfeel_minimum_met")),
        "history_line_eligible_slice_checked": bool(evidence.get("history_line_eligible_slice_checked")),
        "history_line_masks_current_input_gap": bool(evidence.get("history_line_masks_current_input_gap")),
        "subscription_boundary_ok": bool(evidence.get("subscription_boundary_ok")),
        "user_label_connection_surface_safe": bool(evidence.get("user_label_connection_surface_safe")),
        "creepy_or_overclaim_or_self_blame_observed": bool(evidence.get("creepy_or_overclaim_or_self_blame_observed")),
        "p4_connection_allowed": p4_allowed,
        "p4_met_conditions": _dedupe(p4_met),
        "p4_hold_reasons": _dedupe(p4_hold),
        "p4_next_actions": _dedupe(p4_next_actions),
        "p5_connection_allowed": p5_allowed,
        "p5_hold_until_current_only_readfeel_stable": not p5_allowed,
        "p5_met_conditions": _dedupe(p5_met),
        "p5_hold_reasons": _dedupe(p5_hold),
        "p5_hold_reason_codes": p5_hold_codes,
        "p5_next_actions": _dedupe(p5_next_actions),
        "next_phase_decision": decision,
        "p3_9_connection_decision_created": True,
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": True,
        "p3_2_local_output_capture_used": True,
        "p3_3_inventory_connection_used": True,
        "p3_4_verdict_split_used": True,
        "p3_5_blind_qa_ratings_only_review_used": True,
        "p3_6_repair_priority_ledger_used": True,
        "p3_7_first_repair_design_used": True,
        "p3_8_regression_used": True,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
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
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        summary, source="p3_9.summary"
    )
    return summary


def build_product_readfeel_p3_p4_p5_connection_decision_20260609(
    *,
    p3_regression_result: Mapping[str, Any] | None = None,
    p3_connection_evidence: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    regression_summary = _regression_summary(p3_regression_result)
    evidence = _normalize_connection_evidence(p3_connection_evidence)
    run_id_value = _safe_identifier(run_id or regression_summary.get("run_id"), default="p3_9_p4_p5_connection")

    p4_allowed, p4_met, p4_hold = _p4_conditions(evidence)
    p5_allowed, p5_met, p5_hold = _p5_conditions(evidence)
    summary = _summary(
        regression_summary=regression_summary,
        evidence=evidence,
        p4_allowed=p4_allowed,
        p4_met=p4_met,
        p4_hold=p4_hold,
        p5_allowed=p5_allowed,
        p5_met=p5_met,
        p5_hold=p5_hold,
        run_id=run_id_value,
    )
    if summary["next_phase_decision"] != DECISION_P5_READY_AFTER_P4:
        p5_allowed = False
    if summary["next_phase_decision"] not in {DECISION_P4_NEXT_P5_HOLD, DECISION_P5_READY_AFTER_P4}:
        p4_allowed = False

    connection_items = [
        _connection_item(
            phase_id=PHASE_P4_FAMILY_TUNING,
            allowed=p4_allowed,
            met_conditions=p4_met,
            hold_reasons=p4_hold,
            recommended_next_action=(
                "move_to_p4_family_product_tuning_with_current_input_repair_targets"
                if p4_allowed
                else "do_not_start_p4_until_p3_9_blockers_clear"
            ),
            run_id=run_id_value,
        ),
        _connection_item(
            phase_id=PHASE_P5_USER_LABEL_CONNECTION,
            allowed=p5_allowed,
            met_conditions=p5_met,
            hold_reasons=p5_hold,
            recommended_next_action=(
                "prepare_p5_user_label_connection_visible_surface_strengthening"
                if p5_allowed
                else "hold_p5_until_current_only_readfeel_is_stable"
            ),
            run_id=run_id_value,
        ),
    ]
    payload = {
        "schema_version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_P4_P5_CONNECTION_PROFILE_20260609,
        "summary": summary,
        "connection_items": connection_items,
        "public_summary": {},
        "p3_9_connection_decision_created": True,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    payload["public_summary"] = build_product_readfeel_p3_p4_p5_connection_public_summary_20260609(payload)
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(payload, source="p3_9.decision")
    return payload


def build_product_readfeel_p3_p4_p5_connection_public_summary_20260609(
    decision_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(decision_payload or {})
    summary = dict(payload.get("summary") or {})
    connection_items = [dict(item) for item in payload.get("connection_items") or [] if isinstance(item, Mapping)]
    public_summary = dict(summary)
    public_summary["schema_version"] = PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609
    public_summary["version"] = PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609
    public_summary["source"] = PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SOURCE_20260609
    public_summary["source_step"] = PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609
    public_summary["connection_items"] = [
        {
            "target_phase": _clean(item.get("target_phase")),
            "allowed_to_connect": item.get("allowed_to_connect") is True,
            "met_conditions": _dedupe(item.get("met_conditions")),
            "hold_reasons": _dedupe(item.get("hold_reasons")),
            "recommended_next_action": _clean(item.get("recommended_next_action")),
        }
        for item in connection_items
    ]
    public_summary["comment_text_body_included"] = False
    public_summary["raw_input_included"] = False
    public_summary["candidate_body_included"] = False
    public_summary["history_raw_text_included"] = False
    public_summary["raw_test_output_included"] = False
    public_summary["runtime_repair_applied"] = False
    public_summary["implementation_change_applied"] = False
    public_summary["p4_runtime_tuning_applied"] = False
    public_summary["p5_visible_surface_strengthened"] = False
    public_summary["p5_runtime_change_applied"] = False
    public_summary["gate_relaxed"] = False
    public_summary["product_gate_ready"] = False
    public_summary["public_release_applied"] = False
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        public_summary, source="p3_9.public_summary"
    )
    return public_summary


def dump_product_readfeel_p3_p4_p5_connection_public_summary_20260609(
    decision_payload: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p3_p4_p5_connection_public_summary_20260609(decision_payload)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609",
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_EVIDENCE_VERSION_20260609",
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_ITEM_VERSION_20260609",
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609",
    "PHASE_P4_FAMILY_TUNING",
    "PHASE_P5_USER_LABEL_CONNECTION",
    "DECISION_BLOCKED_BY_P2_RED",
    "DECISION_BLOCKED_BY_P1_DISPLAY",
    "DECISION_BLOCKED_BY_REGRESSION",
    "DECISION_NEEDS_BASELINE_EVIDENCE",
    "DECISION_P4_NEXT_P5_HOLD",
    "DECISION_P5_READY_AFTER_P4",
    "DECISION_HOLD_AT_P3_FIRST_REPAIR",
    "assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609",
    "build_product_readfeel_p3_p4_p5_connection_decision_20260609",
    "build_product_readfeel_p3_p4_p5_connection_public_summary_20260609",
    "dump_product_readfeel_p3_p4_p5_connection_public_summary_20260609",
]
