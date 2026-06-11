# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-0 body-free entry freeze for Structure Insight.

This module receives the P5-7 regression handoff and decides whether roadmap
P6 may start, must stay on hold, or must return to P5/P4 repair.  It does not
generate visible text, add public response keys, or promote any Product QA
signal into release.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_user_label_connection_p5_regression_handoff import (
    DECISION_P4_RETURN,
    DECISION_P5_CONTINUE,
    DECISION_P6_HOLD,
    DECISION_P6_READY,
    P6_ALLOWED_TARGET_FAMILIES,
    assert_user_label_connection_p5_regression_handoff_contract,
)


STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_entry_freeze.v1"
)
STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_entry_freeze_summary.v1"
)
STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP: Final = "P6-0_P5Handoff_P6EntryFreeze"
STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_P6EntryFreeze_20260611"
)

DECISION_P6_ENTRY_ALLOWED: Final = "p6_entry_allowed"
DECISION_P6_ENTRY_HOLD: Final = "p6_entry_hold"
DECISION_P5_RETURN_REQUIRED: Final = "p5_return_required"
DECISION_P4_RETURN_REQUIRED: Final = "p4_return_required"

REASON_P5_7_HANDOFF_NOT_READY: Final = "p5_7_handoff_not_p6_ready"
REASON_P5_LIMITED_VISIBLE_CONNECTION_NOT_READY: Final = "p5_limited_visible_connection_not_ready"
REASON_CURRENT_INPUT_MASKED_BY_HISTORY: Final = "current_input_masked_by_history"
REASON_CREEPY_OVERCLAIM_SELF_BLAME_RISK_INCREASED: Final = "creepy_overclaim_self_blame_risk_increased"
REASON_P5_DEEP_INSIGHT_SUBSTITUTE_RISK: Final = "p5_deep_insight_substitute_risk"
REASON_P4_CURRENT_ONLY_REGRESSION_NOT_PRESERVED: Final = "p4_current_only_regression_not_preserved"
REASON_REQUIRED_REGRESSION_NOT_GREEN: Final = "required_regression_not_green"
REASON_P6_TARGET_FAMILY_MISSING: Final = "p6_target_family_missing"
REASON_P6_TARGET_FAMILY_OUT_OF_SCOPE: Final = "p6_target_family_out_of_scope"
REASON_STRUCTURE_INSIGHT_INVENTORY_NOT_CONFIRMED: Final = "structure_insight_inventory_not_confirmed"
REASON_P6_RELATION_POLICY_NOT_FIXED: Final = "p6_relation_policy_not_fixed"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"
REASON_UPSTREAM_HANDOFF_CONTRACT_INVALID: Final = "upstream_p5_7_handoff_contract_invalid"
REASON_UPSTREAM_INVENTORY_CONTRACT_INVALID: Final = "upstream_structure_insight_inventory_contract_invalid"

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
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "reply_text",
        "replyText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_free_text",
        "raw_test_output",
        "test_output",
        "command_output",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
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
        "db_schema_changed",
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
        "structure_insight_gate_relaxed",
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
        "reviewer_free_text_included",
        "raw_test_output_included",
        "command_output_included",
        "terminal_output_included",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "target_judgement_agreement_allowed",
        "period_tendency_from_single_record_allowed",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
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
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _summary_from_p5_7_handoff(value: Mapping[str, Any]) -> dict[str, Any]:
    summary = _safe_mapping(value.get("summary"))
    return summary or dict(value)


def _inventory_ready(value: Mapping[str, Any]) -> bool:
    summary = _safe_mapping(value.get("summary")) or value
    return (
        summary.get("p6_inventory_ready") is True
        or summary.get("structure_insight_inventory_confirmed") is True
        or summary.get("ready_for_p6_entry_freeze") is True
    )


def _inventory_blockers(value: Mapping[str, Any]) -> list[str]:
    summary = _safe_mapping(value.get("summary")) or value
    return _dedupe(summary.get("inventory_blockers") or summary.get("p6_inventory_blockers"))


def _families_from_sources(
    *,
    p5_7_summary: Mapping[str, Any],
    p6_candidate_families: Sequence[Any] | None,
    p6_scope_meta: Mapping[str, Any],
) -> list[str]:
    if p6_candidate_families is not None:
        return _dedupe(p6_candidate_families)
    for source in (p6_scope_meta, p5_7_summary):
        families = _dedupe(source.get("p6_target_families") or source.get("p6_candidate_families"))
        if families:
            return families
    return []


def _regression_green(
    *,
    p5_7_summary: Mapping[str, Any],
    required_regression_statuses: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
) -> tuple[bool, list[str]]:
    statuses = [item for item in list(required_regression_statuses or []) if isinstance(item, Mapping)]
    blockers: list[str] = []
    if statuses:
        for item in statuses:
            suite_id = _clean(item.get("suite_id") or item.get("id")) or "unknown_suite"
            status = _clean(item.get("status")).lower()
            passed = item.get("passed") is True or (status == "passed" and item.get("failed_count", 0) == 0)
            if not passed:
                blockers.append(f"{REASON_REQUIRED_REGRESSION_NOT_GREEN}:{suite_id}")
        return not blockers, _dedupe(blockers)
    blockers.extend(_dedupe(p5_7_summary.get("required_regression_blockers")))
    blockers.extend(_dedupe(p5_7_summary.get("missing_required_regression_suites")))
    return p5_7_summary.get("all_required_regression_green") is True and not blockers, _dedupe(blockers)


def _decision(
    *,
    p4_return_material: Sequence[str],
    p5_return_material: Sequence[str],
    p6_hold_material: Sequence[str],
) -> str:
    if p4_return_material:
        return DECISION_P4_RETURN_REQUIRED
    if p5_return_material:
        return DECISION_P5_RETURN_REQUIRED
    if p6_hold_material:
        return DECISION_P6_ENTRY_HOLD
    return DECISION_P6_ENTRY_ALLOWED


def build_structure_insight_p6_entry_freeze(
    *,
    p5_7_regression_handoff: Mapping[str, Any] | None = None,
    structure_insight_inventory: Mapping[str, Any] | None = None,
    required_regression_statuses: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    p6_candidate_families: Sequence[Any] | None = None,
    p6_scope_meta: Mapping[str, Any] | None = None,
    p6_relation_policy_fixed: bool | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the P6 entry freeze payload without visible or raw text bodies."""

    run = _clean(run_id) or "p6_entry_freeze"
    handoff = _safe_mapping(p5_7_regression_handoff)
    inventory = _safe_mapping(structure_insight_inventory)
    p6_scope = _safe_mapping(p6_scope_meta)
    handoff_contract_invalid = False
    inventory_contract_invalid = False

    if handoff:
        try:
            assert_user_label_connection_p5_regression_handoff_contract(handoff, allow_partial=True)
        except ValueError:
            handoff_contract_invalid = True
    if inventory:
        try:
            json.dumps(inventory, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            inventory_contract_invalid = True

    p5_7_summary = _summary_from_p5_7_handoff(handoff)
    handoff_decision = _clean(p5_7_summary.get("handoff_decision")) or DECISION_P6_HOLD
    p6_families = _families_from_sources(
        p5_7_summary=p5_7_summary,
        p6_candidate_families=p6_candidate_families,
        p6_scope_meta=p6_scope,
    )
    p6_family_out_of_scope = sorted(set(p6_families) - set(P6_ALLOWED_TARGET_FAMILIES))
    p6_family_scope_limited = bool(p6_families and not p6_family_out_of_scope)
    all_required_green, regression_blockers = _regression_green(
        p5_7_summary=p5_7_summary,
        required_regression_statuses=required_regression_statuses,
    )

    sources = [handoff, inventory, p6_scope]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)

    p5_ready = p5_7_summary.get("p5_limited_visible_connection_ready") is True
    current_not_masked = p5_7_summary.get("current_input_not_masked_by_history") is True
    risk_not_increased = p5_7_summary.get("creepy_overclaim_self_blame_risk_not_increased") is True
    deep_insight_substitute = p5_7_summary.get("p5_deep_insight_substitute_used") is True
    p4_preserved = p5_7_summary.get("p4_current_only_readfeel_preserved") is not False
    inventory_confirmed = _inventory_ready(inventory)
    relation_policy_fixed = p6_relation_policy_fixed is not False

    p4_return_material: list[str] = []
    p5_return_material: list[str] = []
    p6_hold_material: list[str] = []

    if handoff_contract_invalid:
        p5_return_material.append(REASON_UPSTREAM_HANDOFF_CONTRACT_INVALID)
    if inventory_contract_invalid:
        p6_hold_material.append(REASON_UPSTREAM_INVENTORY_CONTRACT_INVALID)
    if unsafe_payload:
        p5_return_material.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if contract_mutation:
        p5_return_material.append(REASON_CONTRACT_MUTATION_DETECTED)
    if handoff_decision == DECISION_P4_RETURN or not p4_preserved:
        p4_return_material.append(REASON_P4_CURRENT_ONLY_REGRESSION_NOT_PRESERVED)
    if handoff_decision == DECISION_P5_CONTINUE:
        p5_return_material.append(REASON_P5_7_HANDOFF_NOT_READY)
    if not p5_ready:
        p5_return_material.append(REASON_P5_LIMITED_VISIBLE_CONNECTION_NOT_READY)
    if not current_not_masked:
        p5_return_material.append(REASON_CURRENT_INPUT_MASKED_BY_HISTORY)
    if not risk_not_increased:
        p5_return_material.append(REASON_CREEPY_OVERCLAIM_SELF_BLAME_RISK_INCREASED)
    if deep_insight_substitute:
        p5_return_material.append(REASON_P5_DEEP_INSIGHT_SUBSTITUTE_RISK)
    if handoff_decision == DECISION_P6_HOLD:
        p6_hold_material.append(REASON_P5_7_HANDOFF_NOT_READY)
    if not all_required_green:
        p6_hold_material.extend(regression_blockers or [REASON_REQUIRED_REGRESSION_NOT_GREEN])
    if not p6_families:
        p6_hold_material.append(REASON_P6_TARGET_FAMILY_MISSING)
    if p6_family_out_of_scope:
        p6_hold_material.extend(f"{REASON_P6_TARGET_FAMILY_OUT_OF_SCOPE}:{family}" for family in p6_family_out_of_scope)
    if not inventory_confirmed:
        p6_hold_material.append(REASON_STRUCTURE_INSIGHT_INVENTORY_NOT_CONFIRMED)
    if not relation_policy_fixed:
        p6_hold_material.append(REASON_P6_RELATION_POLICY_NOT_FIXED)

    p4_return_material = _dedupe(p4_return_material)
    p5_return_material = _dedupe(p5_return_material)
    p6_hold_material = _dedupe(p6_hold_material)
    handoff_result = _decision(
        p4_return_material=p4_return_material,
        p5_return_material=p5_return_material,
        p6_hold_material=p6_hold_material,
    )
    decision_reasons = _dedupe([*p4_return_material, *p5_return_material, *p6_hold_material])

    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP,
        "run_id": run,
        "p6_entry_freeze_created": True,
        "p6_entry_freeze_only": True,
        "handoff_decision": handoff_result,
        "p6_entry_allowed": handoff_result == DECISION_P6_ENTRY_ALLOWED,
        "p6_entry_hold": handoff_result == DECISION_P6_ENTRY_HOLD,
        "p5_return_required": handoff_result == DECISION_P5_RETURN_REQUIRED,
        "p4_return_required": handoff_result == DECISION_P4_RETURN_REQUIRED,
        "p5_7_handoff_decision": handoff_decision,
        "p5_7_p6_ready": handoff_decision == DECISION_P6_READY,
        "all_required_regression_green": all_required_green,
        "required_regression_blockers": regression_blockers,
        "p5_limited_visible_connection_ready": p5_ready,
        "current_input_not_masked_by_history": current_not_masked,
        "creepy_overclaim_self_blame_risk_not_increased": risk_not_increased,
        "p5_deep_insight_substitute_used": deep_insight_substitute,
        "p6_target_families": p6_families,
        "p6_allowed_target_families": sorted(P6_ALLOWED_TARGET_FAMILIES),
        "p6_target_family_scope_limited": p6_family_scope_limited,
        "p4_current_only_readfeel_preserved": p4_preserved,
        "structure_insight_inventory_confirmed": inventory_confirmed,
        "structure_insight_inventory_blockers": _inventory_blockers(inventory),
        "p6_relation_policy_fixed": relation_policy_fixed,
        "p4_return_material": p4_return_material,
        "p5_return_material": p5_return_material,
        "p6_hold_material": p6_hold_material,
        "decision_reason_codes": decision_reasons,
        "recommended_next_action": {
            DECISION_P6_ENTRY_ALLOWED: "continue_to_p6_existing_structure_insight_inventory",
            DECISION_P6_ENTRY_HOLD: "hold_p6_until_inventory_family_regression_or_policy_is_confirmed",
            DECISION_P5_RETURN_REQUIRED: "return_to_p5_limited_visible_connection_repair_or_review",
            DECISION_P4_RETURN_REQUIRED: "return_to_p4_current_only_readfeel_regression_repair",
        }[handoff_result],
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_entry_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload = {
        "schema_version": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP,
        "run_id": run,
        "summary": summary,
        "public_summary": {},
        "p6_entry_freeze_created": True,
        "p6_entry_freeze_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_entry_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload["public_summary"] = structure_insight_p6_entry_freeze_public_summary(payload)
    assert_structure_insight_p6_entry_freeze_contract(payload)
    return payload


def structure_insight_p6_entry_freeze_public_summary(
    entry_freeze_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _safe_mapping(entry_freeze_payload_or_summary)
    source = _safe_mapping(payload.get("summary")) or payload
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP,
        "run_id": _clean(source.get("run_id")),
        "p6_entry_freeze_created": source.get("p6_entry_freeze_created") is True,
        "handoff_decision": _clean(source.get("handoff_decision")) or DECISION_P6_ENTRY_HOLD,
        "p6_entry_allowed": source.get("p6_entry_allowed") is True,
        "p6_entry_hold": source.get("p6_entry_hold") is True,
        "p5_return_required": source.get("p5_return_required") is True,
        "p4_return_required": source.get("p4_return_required") is True,
        "p5_7_handoff_decision": _clean(source.get("p5_7_handoff_decision")),
        "p5_7_p6_ready": source.get("p5_7_p6_ready") is True,
        "all_required_regression_green": source.get("all_required_regression_green") is True,
        "required_regression_blockers": _dedupe(source.get("required_regression_blockers")),
        "p5_limited_visible_connection_ready": source.get("p5_limited_visible_connection_ready") is True,
        "current_input_not_masked_by_history": source.get("current_input_not_masked_by_history") is True,
        "creepy_overclaim_self_blame_risk_not_increased": source.get(
            "creepy_overclaim_self_blame_risk_not_increased"
        )
        is True,
        "p5_deep_insight_substitute_used": source.get("p5_deep_insight_substitute_used") is True,
        "p6_target_families": _dedupe(source.get("p6_target_families")),
        "p6_allowed_target_families": sorted(P6_ALLOWED_TARGET_FAMILIES),
        "p6_target_family_scope_limited": source.get("p6_target_family_scope_limited") is True,
        "p4_current_only_readfeel_preserved": source.get("p4_current_only_readfeel_preserved") is not False,
        "structure_insight_inventory_confirmed": source.get("structure_insight_inventory_confirmed") is True,
        "structure_insight_inventory_blockers": _dedupe(source.get("structure_insight_inventory_blockers")),
        "p6_relation_policy_fixed": source.get("p6_relation_policy_fixed") is not False,
        "p4_return_material": _dedupe(source.get("p4_return_material")),
        "p5_return_material": _dedupe(source.get("p5_return_material")),
        "p6_hold_material": _dedupe(source.get("p6_hold_material")),
        "decision_reason_codes": _dedupe(source.get("decision_reason_codes")),
        "recommended_next_action": _clean(source.get("recommended_next_action")),
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_entry_status_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
    }
    assert_structure_insight_p6_entry_freeze_contract(summary, allow_partial=True)
    return summary


def dump_structure_insight_p6_entry_freeze_public_summary(
    entry_freeze_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = structure_insight_p6_entry_freeze_public_summary(entry_freeze_payload_or_summary)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_structure_insight_p6_entry_freeze_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if not meta:
        raise ValueError("P6 entry freeze must be a mapping")
    if _contains_text_payload_key(meta):
        raise ValueError("P6 entry freeze must not include raw/comment/history/test body keys")
    if _flag_true(meta):
        raise ValueError("P6 entry freeze contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if meta.get("schema_version") != STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SCHEMA_VERSION:
        raise ValueError("unexpected P6 entry freeze schema_version")
    if meta.get("step") != STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP:
        raise ValueError("unexpected P6 entry freeze step")
    summary = _safe_mapping(meta.get("summary"))
    if summary.get("schema_version") != STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 entry freeze summary schema_version")
    if summary.get("handoff_decision") not in {
        DECISION_P6_ENTRY_ALLOWED,
        DECISION_P6_ENTRY_HOLD,
        DECISION_P5_RETURN_REQUIRED,
        DECISION_P4_RETURN_REQUIRED,
    }:
        raise ValueError("unexpected P6 entry freeze decision")
    if summary.get("release_allowed") is not False or meta.get("release_allowed") is not False:
        raise ValueError("P6 entry freeze must not allow release")
    for source_name, source in (("payload", meta), ("summary", summary)):
        public_contract = _safe_mapping(source.get("public_contract"))
        body_free = _safe_mapping(source.get("body_free"))
        for key in (
            "rn_visible_contract_changed",
            "rn_visible_title_changed",
            "public_response_key_added",
            "response_shape_changed",
            "api_route_changed",
            "request_key_changed",
            "db_schema_changed",
            "fixed_sentence_template_added",
            "release_allowed",
            "public_release_applied",
            "product_quality_released",
        ):
            if public_contract.get(key) is not False:
                raise ValueError(f"P6 entry freeze {source_name}.public_contract.{key} must be false")
        for key in (
            "raw_input_included",
            "raw_text_included",
            "input_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "history_raw_text_included",
            "raw_test_output_included",
            "command_output_included",
            "terminal_output_included",
        ):
            if body_free.get(key) is not False:
                raise ValueError(f"P6 entry freeze {source_name}.body_free.{key} must be false")


__all__ = [
    "STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP",
    "DECISION_P6_ENTRY_ALLOWED",
    "DECISION_P6_ENTRY_HOLD",
    "DECISION_P5_RETURN_REQUIRED",
    "DECISION_P4_RETURN_REQUIRED",
    "assert_structure_insight_p6_entry_freeze_contract",
    "build_structure_insight_p6_entry_freeze",
    "structure_insight_p6_entry_freeze_public_summary",
    "dump_structure_insight_p6_entry_freeze_public_summary",
]
