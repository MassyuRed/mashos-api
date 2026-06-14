# -*- coding: utf-8 -*-
"""P7-HOLD-004 Step5 candidate gate preservation classification material.

R0/R1 scope:
- freeze the current Step5 Complete Initial candidate path red as body-free
  baseline material;
- record the conflicting fail-closed/public-recovery contract pair without
  deciding stale-test vs implementation-regression.

R2/R3 scope:
- fix the body-free Display Binding Contract Decision Rule before any runtime
  repair;
- classify the owner layer as Display Gate, binding meta source, stale test
  expectation, or mixed conflict before entering R4.

R4-A/R4-B scope:
- make the Display Gate fail-closed branch explicit for any remaining
  binding_missing-without-exception Display pass;
- make the Display binding trace / expected count repair branch explicit when
  a passed public recovery path is supported by accepted grounding bindings.

R4-C/R4-D scope:
- replace the stale fail-closed Step5 test expectation only after the repaired
  path proves Gate preservation, Display binding consistency, and public
  assignment consistency;
- preserve unresolved mixed contract conflicts as body-free HOLD material without
  changing runtime public behavior.

R5/R6 scope:
- expose Step5 candidate generation, Gate preservation, Display binding
  consistency, and public assignment consistency as diagnostic-only body-free
  meta;
- connect the classified Step5 material to P7-HOLD-004 validation/release
  material without claiming full backend-suite green, P7 completion, P8 start,
  or release readiness.

All scopes keep P7-HOLD-004, P7 completion, P8 start, and release readiness
closed.

This module stores identifiers, statuses, counts, booleans, and reason codes
only.  It must never serialize raw input, candidate bodies, public reply bodies,
surface bodies, reviewer free text, or terminal output.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)

P7_HOLD004_STEP5_HOLD_ID: Final = "P7-HOLD-004"
P7_HOLD004_STEP5_RED_ID: Final = "P7-HOLD004-RED-STEP5-DISPLAY-BINDING-CONTRACT-CONSISTENCY"
P7_HOLD004_STEP5_STEP: Final = "P7-HOLD-004_Step5CandidateGatePreservation_R0_R1_20260614"
P7_HOLD004_STEP5_R2_R3_STEP: Final = "P7-HOLD-004_Step5CandidateGatePreservation_R2_R3_20260614"
P7_HOLD004_STEP5_R4_A_B_STEP: Final = "P7-HOLD-004_Step5CandidateGatePreservation_R4_A_R4_B_20260614"
P7_HOLD004_STEP5_R4_C_D_STEP: Final = "P7-HOLD-004_Step5CandidateGatePreservation_R4_C_R4_D_20260614"
P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_candidate_gate_observation.v1"
)
P7_HOLD004_STEP5_BASELINE_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_candidate_gate_baseline_freeze.v1"
)
P7_HOLD004_STEP5_CONFLICT_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_candidate_gate_conflicting_contract_matrix.v1"
)
P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_display_binding_contract_decision_rule.v1"
)
P7_HOLD004_STEP5_OWNER_LAYER_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_owner_layer_decision.v1"
)
P7_HOLD004_STEP5_R4A_FAIL_CLOSED_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_r4a_display_gate_fail_closed_branch.v1"
)
P7_HOLD004_STEP5_R4B_TRACE_REPAIR_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_r4b_display_binding_trace_repair_branch.v1"
)
P7_HOLD004_STEP5_R4C_STALE_EXPECTATION_UPDATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_r4c_stale_test_expectation_update_branch.v1"
)
P7_HOLD004_STEP5_R4D_MIXED_CONFLICT_HOLD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_r4d_mixed_contract_conflict_hold_branch.v1"
)
P7_HOLD004_STEP5_R5_R6_STEP: Final = "P7-HOLD-004_Step5CandidateGatePreservation_R5_R6_20260614"
P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_meta_extension.v1"
)
P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.step5_material_connection.v1"
)
P7_HOLD004_STEP5_R5_META_EXTENSION_ID: Final = "p7_hold004_step5_r5_meta_extension_20260614"
P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_ID: Final = "p7_hold004_step5_r6_material_connection_20260614"
P7_HOLD004_STEP5_R6_CONNECTION_ID: Final = P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_ID

P7_HOLD004_STEP5_DECISION_RULE_ID: Final = "p7_hold004_step5_display_binding_contract_decision_rule_20260614"
P7_HOLD004_STEP5_OWNER_LAYER_DECISION_ID: Final = "p7_hold004_step5_owner_layer_decision_20260614"
P7_HOLD004_STEP5_R4A_BRANCH_ID: Final = "p7_hold004_step5_r4a_display_gate_fail_closed_branch_20260614"
P7_HOLD004_STEP5_R4B_BRANCH_ID: Final = "p7_hold004_step5_r4b_display_binding_trace_repair_branch_20260614"
P7_HOLD004_STEP5_R4C_BRANCH_ID: Final = "p7_hold004_step5_r4c_stale_test_expectation_update_branch_20260614"
P7_HOLD004_STEP5_R4D_BRANCH_ID: Final = "p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_20260614"

STEP5_FAIL_CLOSED_TEST_REF: Final = (
    "tests/test_emlis_ai_complete_initial_entry_route.py::"
    "test_step5_candidate_generation_path_keeps_existing_gates_fail_closed"
)
STEP5_PUBLIC_RECOVERY_TEST_REF: Final = (
    "tests/test_emlis_ai_phase18_complete_initial_candidate_path.py::"
    "test_phase18_3_complete_initial_generates_candidate_before_display_gate_without_public_body_leak"
)
STEP5_STEP7_INTEGRATION_TEST_REF: Final = "tests/test_emlis_ai_complete_initial_step7_integration.py"

_ALLOWED_CANDIDATE_STATUSES: Final[frozenset[str]] = frozenset(
    {"generated", "blocked", "unavailable", "not_run", "unknown"}
)
_ALLOWED_DISPLAY_STATUSES: Final[frozenset[str]] = frozenset(
    {"passed", "rejected", "unavailable", "safety_blocked", "not_run", "unknown"}
)
_ALLOWED_CLASSIFICATION_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "CLASSIFIED_UNRESOLVED",
        "IMPLEMENTATION_REPAIR_REQUIRED",
        "STALE_CONTRACT_REPLACEMENT_REQUIRED",
        "TRACE_INCONSISTENCY_REPAIR_REQUIRED",
        "MIXED_CONTRACT_CONFLICT",
    }
)
_ALLOWED_RED_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {
        "display_binding_missing_passed_public_assignment_conflict",
        "display_binding_missing_passed_conflict",
        "public_assignment_without_display_contract_consistency",
        "classified_without_current_red_reproduction",
    }
)
_ALLOWED_OWNER_LAYERS: Final[frozenset[str]] = frozenset(
    {
        "step5_meta_boundary",
        "display_gate_binding_contract",
        "binding_presence_meta_source",
        "complete_composer_binding_bundle",
        "test_contract_boundary",
        "p7_hold004_classification_material",
        "mixed",
        "unknown",
    }
)
_ALLOWED_CONFLICT_STATUS: Final[frozenset[str]] = frozenset(
    {
        "CONTRACT_CONFLICT_CLASSIFIED_UNRESOLVED",
        "NO_CONFLICT_RECORDED",
    }
)
_ALLOWED_DECISION_RULE_STATUS: Final[frozenset[str]] = frozenset(
    {
        "DECISION_RULE_FIXED_RED_OPEN",
        "DECISION_RULE_FIXED_NO_CURRENT_RED",
    }
)
_ALLOWED_DECISION_RULE_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "display_binding_missing_without_exception_blocks_public_assignment",
        "public_assignment_without_display_binding_contract_consistency",
        "display_binding_contract_consistent_for_current_material",
    }
)
_ALLOWED_OWNER_DECISION_STATUS: Final[frozenset[str]] = frozenset(
    {
        "OWNER_LAYER_IMPLEMENTATION_REPAIR_REQUIRED",
        "OWNER_LAYER_TRACE_INCONSISTENCY_REPAIR_REQUIRED",
        "OWNER_LAYER_STALE_CONTRACT_REPLACEMENT_REQUIRED",
        "OWNER_LAYER_MIXED_CONTRACT_CONFLICT",
        "OWNER_LAYER_CLASSIFIED_UNRESOLVED",
    }
)
_ALLOWED_OWNER_DECISION_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "implementation_contract_red",
        "meta_trace_inconsistency",
        "stale_test_expectation",
        "mixed_contract_conflict",
        "classified_without_current_red_reproduction",
    }
)
_ALLOWED_R4A_STATUS: Final[frozenset[str]] = frozenset(
    {
        "R4A_FAIL_CLOSED_REPAIR_BRANCH_FIXED",
        "R4A_EVALUATED_NOT_APPLIED_AFTER_TRACE_REPAIR",
    }
)
_ALLOWED_R4B_STATUS: Final[frozenset[str]] = frozenset(
    {
        "R4B_TRACE_REPAIR_APPLIED",
        "R4B_TRACE_REPAIR_PLAN_FIXED",
    }
)
_ALLOWED_R4C_STATUS: Final[frozenset[str]] = frozenset(
    {
        "R4C_STALE_TEST_EXPECTATION_REPLACED",
        "R4C_STALE_TEST_EXPECTATION_REVIEW_FIXED",
    }
)
_ALLOWED_R4D_STATUS: Final[frozenset[str]] = frozenset(
    {
        "R4D_MIXED_CONTRACT_CONFLICT_HELD",
    }
)
_ALLOWED_R4A_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "display_binding_missing_without_exception_requires_fail_closed",
        "display_binding_fail_closed_not_needed_after_trace_repair",
    }
)
_ALLOWED_R4B_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "display_expected_count_aligned_to_accepted_grounding_sentence_count",
        "display_trace_repair_planned_from_pre_repair_material",
    }
)
_ALLOWED_R4C_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "stale_fail_closed_expectation_replaced_by_gate_preservation_and_binding_contract_consistency",
        "stale_fail_closed_expectation_review_kept_pending",
    }
)
_ALLOWED_R4D_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "mixed_contract_conflict_preserved_as_hold_material",
    }
)
_ALLOWED_R5_STATUS: Final[frozenset[str]] = frozenset(
    {
        "R5_STEP5_META_EXTENDED",
        "R5_STEP5_META_RECORDED_WITHOUT_CANDIDATE",
        "R5_STEP5_META_EXTENSION_READY",
        "R5_STEP5_META_EXTENSION_REVIEW_REQUIRED",
    }
)
_ALLOWED_R5_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "candidate_generated_public_allowed",
        "candidate_generated_display_binding_inconsistent",
        "candidate_generated_fail_closed",
        "candidate_not_generated",
        "blocked_before_candidate_generation",
    }
)
_ALLOWED_R6_STATUS: Final[frozenset[str]] = frozenset(
    {
        "R6_P7_HOLD004_MATERIAL_CONNECTED",
        "R6_P7_HOLD004_STEP5_MATERIAL_CONNECTED",
    }
)
_ALLOWED_R6_CLASSIFICATION: Final[frozenset[str]] = frozenset(
    {
        "step5_display_binding_material_connected_as_hold004_release_blocker",
        "step5_display_binding_contract_consistency_connected_to_p7_hold004",
    }
)

_ALLOWED_NEXT_BRANCHES: Final[frozenset[str]] = frozenset({"R4-A", "R4-B", "R4-C", "R4-D", "none"})
_ALWAYS_FALSE_KEYS: Final[tuple[str, ...]] = (
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claim_allowed",
    "hold004_close_allowed",
    "p7_complete",
    "p7_complete_claim_allowed",
    "p8_start_allowed",
    "release_allowed",
)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "passed", "green"}


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "" or isinstance(value, bool):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _clean_status(value: Any, *, allowed: frozenset[str], default: str) -> str:
    status = clean_identifier(value, default=default, max_length=120)
    return status if status in allowed else default


def _public_contract_flags() -> dict[str, bool]:
    flags = public_contract_flags()
    flags.update(
        {
            "api_route_changed": False,
            "request_key_changed": False,
            "public_response_top_level_key_changed": False,
            "public_response_key_added": False,
            "response_shape_changed": False,
            "db_write_path_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "display_gate_relaxed": False,
            "gate_relaxed": False,
            "fixed_sentence_template_added": False,
            "fixed_string_renderer_used": False,
            "runtime_fixture_branch_added": False,
            "case_specific_branch_added": False,
        }
    )
    return flags


def _binding_summary(gate: Mapping[str, Any], *, observation_status: Any = "unknown") -> dict[str, Any]:
    data = safe_mapping(gate)
    binding_required = _bool(data.get("binding_required"))
    binding_used = _bool(data.get("binding_used"))
    binding_present = _bool(data.get("binding_present"))
    binding_missing = _bool(data.get("binding_missing"))
    exception_allowed = _bool(data.get("binding_missing_exception_allowed"))
    exception_id = clean_identifier(data.get("binding_missing_exception_id"), default="", max_length=120)
    exception_valid = bool(exception_allowed and exception_id)
    missing_without_exception = bool(binding_required and binding_used and binding_missing and not exception_valid)
    display_passed = _bool(data.get("passed"))
    return {
        "evaluated": _bool(data.get("evaluated")),
        "passed": display_passed,
        "observation_status": _clean_status(
            observation_status,
            allowed=_ALLOWED_DISPLAY_STATUSES,
            default="unknown",
        ),
        "binding_required": binding_required,
        "binding_used": binding_used,
        "binding_present": binding_present,
        "binding_missing": binding_missing,
        "binding_count": _int(data.get("binding_count")),
        "expected_binding_count": _int(data.get("expected_binding_count")),
        "binding_support_source": clean_identifier(
            data.get("binding_support_source"), default="unknown", max_length=120
        ),
        "display_binding_expected_count_source": clean_identifier(
            data.get("display_binding_expected_count_source") or data.get("expected_binding_count_source"),
            default="unknown",
            max_length=120,
        ),
        "display_binding_count_source": clean_identifier(
            data.get("display_binding_count_source") or data.get("binding_count_source"),
            default="unknown",
            max_length=120,
        ),
        "display_binding_trace_repaired": _bool(
            data.get("display_binding_trace_repaired") or data.get("display_binding_trace_repair_applied")
        ),
        "display_binding_trace_repair_reason": clean_identifier(
            data.get("display_binding_trace_repair_reason"), default="", max_length=160
        ),
        "original_expected_binding_count": _int(data.get("original_expected_binding_count")),
        "binding_contract_version": clean_identifier(
            data.get("gate_binding_contract_version") or data.get("binding_contract_version"),
            default="unknown",
            max_length=120,
        ),
        "binding_missing_exception_allowed": exception_allowed,
        "binding_missing_exception_id": exception_id,
        "binding_missing_exception_valid": exception_valid,
        "binding_missing_without_exception": missing_without_exception,
        "display_binding_contract_consistent": not bool(display_passed and missing_without_exception),
        "rejection_reasons": dedupe_identifiers(data.get("rejection_reasons"), limit=40, max_length=120),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }


def _candidate_summary(step5: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "complete_initial_client_resolved": _bool(step5.get("complete_initial_client_resolved")),
        "candidate_generation_attempted": _bool(step5.get("candidate_generation_attempted")),
        "complete_composer_client_generate_called": _bool(step5.get("complete_composer_client_generate_called")),
        "candidate_generated": _bool(step5.get("candidate_generated")),
        "candidate_generated_before_display_gate": _bool(step5.get("candidate_generated_before_display_gate")),
        "candidate_status": _clean_status(
            step5.get("candidate_status"), allowed=_ALLOWED_CANDIDATE_STATUSES, default="unknown"
        ),
        "candidate_status_before_display_gate": _clean_status(
            step5.get("candidate_status_before_display_gate"),
            allowed=_ALLOWED_CANDIDATE_STATUSES,
            default="unknown",
        ),
        "candidate_status_after_display_gate": _clean_status(
            step5.get("candidate_status_after_display_gate"),
            allowed=_ALLOWED_DISPLAY_STATUSES | _ALLOWED_CANDIDATE_STATUSES,
            default="unknown",
        ),
        "composer_source": clean_identifier(step5.get("composer_source"), default="unknown", max_length=120),
        "candidate_comment_text_present": _bool(step5.get("candidate_comment_text_present")),
        "candidate_body_included": False,
    }


def _gate_preservation_summary(step5: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "existing_reader_grounding_template_display_gates_preserved": _bool(
            step5.get("existing_reader_grounding_template_display_gates_preserved")
        ),
        "reader_gate_evaluated": _bool(step5.get("reader_gate_evaluated")),
        "grounding_gate_evaluated": _bool(step5.get("grounding_gate_evaluated")),
        "template_gate_evaluated": _bool(step5.get("template_gate_evaluated")),
        "display_gate_evaluated": _bool(step5.get("display_gate_evaluated")),
        "reader_gate_relaxed": _bool(step5.get("reader_gate_relaxed")),
        "grounding_gate_relaxed": _bool(step5.get("grounding_gate_relaxed")),
        "template_gate_relaxed": _bool(step5.get("template_gate_relaxed")),
        "display_gate_relaxed": _bool(step5.get("display_gate_relaxed")),
    }


def _public_assignment_summary(
    step5: Mapping[str, Any],
    *,
    display_binding_contract_consistent: bool,
    display_gate_passed: bool,
    reply_comment_text_present: bool | None,
) -> dict[str, Any]:
    public_present = _bool(step5.get("public_comment_text_present"))
    if reply_comment_text_present is not None:
        public_present = bool(public_present or reply_comment_text_present)
    allowed_by_display = bool(display_gate_passed and display_binding_contract_consistent)
    return {
        "public_comment_text_present": public_present,
        "reply_comment_text_present": bool(reply_comment_text_present) if reply_comment_text_present is not None else public_present,
        "public_assignment_allowed_by_display_gate": allowed_by_display,
        "public_assignment_contract_consistent": bool((not public_present) or allowed_by_display),
        "non_passed_comment_text_empty": _bool(step5.get("non_passed_comment_text_empty")),
        "passed_only_comment_text_contract_preserved": _bool(step5.get("passed_only_comment_text_contract_preserved")),
        "comment_text_body_included": False,
    }


def _classify_observation(
    *,
    display_binding_summary: Mapping[str, Any],
    public_assignment_summary: Mapping[str, Any],
) -> tuple[str, list[str], list[str]]:
    display_passed = display_binding_summary.get("passed") is True
    binding_missing_without_exception = display_binding_summary.get("binding_missing_without_exception") is True
    public_present = public_assignment_summary.get("public_comment_text_present") is True
    public_consistent = public_assignment_summary.get("public_assignment_contract_consistent") is True
    if display_passed and binding_missing_without_exception and public_present:
        return (
            "display_binding_missing_passed_public_assignment_conflict",
            ["display_gate_binding_contract", "binding_presence_meta_source", "test_contract_boundary"],
            [
                "display_binding_missing_without_exception",
                "display_passed_with_binding_missing",
                "public_assignment_present_while_display_binding_inconsistent",
                "stale_or_regression_not_decided",
            ],
        )
    if display_passed and binding_missing_without_exception:
        return (
            "display_binding_missing_passed_conflict",
            ["display_gate_binding_contract", "binding_presence_meta_source"],
            ["display_binding_missing_without_exception", "display_passed_with_binding_missing"],
        )
    if public_present and not public_consistent:
        return (
            "public_assignment_without_display_contract_consistency",
            ["step5_meta_boundary", "test_contract_boundary"],
            ["public_assignment_contract_inconsistent"],
        )
    return (
        "classified_without_current_red_reproduction",
        ["p7_hold004_classification_material"],
        ["current_red_not_reproduced_in_supplied_material"],
    )


def build_p7_hold004_step5_candidate_gate_observation(
    *,
    step5_meta: Mapping[str, Any],
    runtime_meta: Mapping[str, Any] | None = None,
    reply_comment_text_present: bool | None = None,
    test_ref: Any = STEP5_FAIL_CLOSED_TEST_REF,
    observation_id: Any = "p7_hold004_step5_candidate_gate_current_red_20260614",
) -> dict[str, Any]:
    """Build R0 body-free observation material from Step5 diagnostic meta."""

    step5 = safe_mapping(step5_meta)
    if not step5:
        raise ValueError("Step5 candidate gate observation requires step5_meta")
    assert_p7_no_body_payload_or_contract_mutation(step5, source="p7_hold004_step5.source_step5_meta")
    runtime = safe_mapping(runtime_meta)
    if runtime:
        assert_p7_no_body_payload_or_contract_mutation(runtime, source="p7_hold004_step5.source_runtime_meta")

    gate_results = safe_mapping(step5.get("gate_results"))
    display = _binding_summary(
        safe_mapping(gate_results.get("display")),
        observation_status=step5.get("display_observation_status"),
    )
    grounding = _binding_summary(
        safe_mapping(gate_results.get("grounding")),
        observation_status="passed" if safe_mapping(gate_results.get("grounding")).get("passed") is True else "unknown",
    )
    public_assignment = _public_assignment_summary(
        step5,
        display_binding_contract_consistent=display["display_binding_contract_consistent"],
        display_gate_passed=display["passed"],
        reply_comment_text_present=reply_comment_text_present,
    )
    classification, owner_layers, reason_codes = _classify_observation(
        display_binding_summary=display,
        public_assignment_summary=public_assignment,
    )
    contract_flags = _public_contract_flags()
    for key in ("reader_gate_relaxed", "grounding_gate_relaxed", "template_gate_relaxed", "display_gate_relaxed"):
        contract_flags[key] = _bool(step5.get(key))
    observation = {
        "schema_version": P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_STEP,
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "observation_id": clean_identifier(observation_id, default="p7_hold004_step5_candidate_gate_observation", max_length=160),
        "test_ref": clean_identifier(test_ref, default=STEP5_FAIL_CLOSED_TEST_REF, max_length=240),
        "classification_status": "CLASSIFIED_UNRESOLVED",
        "classification": classification,
        "owner_layers": dedupe_identifiers(owner_layers, limit=8, max_length=120),
        "reason_codes": dedupe_identifiers(reason_codes, limit=40, max_length=160),
        "candidate_summary": _candidate_summary(step5),
        "gate_preservation_summary": _gate_preservation_summary(step5),
        "display_binding_summary": display,
        "grounding_binding_summary": grounding,
        "public_assignment_summary": public_assignment,
        "contract_flags": contract_flags,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "body_free": True,
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    return observation


def assert_p7_hold004_step5_candidate_gate_observation_contract(observation: Mapping[str, Any]) -> bool:
    data = safe_mapping(observation)
    if data.get("schema_version") != P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 observation schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 observation phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 red_id")
    if data.get("classification_status") not in _ALLOWED_CLASSIFICATION_STATUSES:
        raise ValueError("unsupported HOLD-004 Step5 classification_status")
    if data.get("classification") not in _ALLOWED_RED_CLASSIFICATIONS:
        raise ValueError("unsupported HOLD-004 Step5 classification")
    owner_layers = dedupe_identifiers(data.get("owner_layers"), limit=20, max_length=120)
    if not owner_layers or any(layer not in _ALLOWED_OWNER_LAYERS for layer in owner_layers):
        raise ValueError("unsupported HOLD-004 Step5 owner layer")
    candidate = safe_mapping(data.get("candidate_summary"))
    if candidate.get("candidate_status") not in _ALLOWED_CANDIDATE_STATUSES:
        raise ValueError("unsupported HOLD-004 Step5 candidate status")
    display = safe_mapping(data.get("display_binding_summary"))
    if display.get("observation_status") not in _ALLOWED_DISPLAY_STATUSES:
        raise ValueError("unsupported HOLD-004 Step5 display status")
    if display.get("passed") is True and display.get("binding_missing_without_exception") is True:
        if data.get("classification") == "classified_without_current_red_reproduction":
            raise ValueError("binding_missing + passed must not be classified as non-red")
    public_assignment = safe_mapping(data.get("public_assignment_summary"))
    if public_assignment.get("public_comment_text_present") is True and display.get("display_binding_contract_consistent") is False:
        if public_assignment.get("public_assignment_contract_consistent") is not False:
            raise ValueError("public assignment must be inconsistent when display binding contract is inconsistent")
    gates = safe_mapping(data.get("gate_preservation_summary"))
    if gates.get("display_gate_relaxed") is True:
        raise ValueError("R0/R1 Step5 classification must not record display gate relaxation")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 observation must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 observation must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_observation.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_observation.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_observation")
    return True


def _observation_status_row(observation: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(observation)
    display = safe_mapping(data.get("display_binding_summary"))
    public_assignment = safe_mapping(data.get("public_assignment_summary"))
    candidate = safe_mapping(data.get("candidate_summary"))
    return {
        "observation_id": clean_identifier(data.get("observation_id"), default="unknown_observation", max_length=160),
        "test_ref": clean_identifier(data.get("test_ref"), default="unknown_test_ref", max_length=240),
        "classification": clean_identifier(data.get("classification"), default="unknown", max_length=160),
        "candidate_status": clean_identifier(candidate.get("candidate_status"), default="unknown", max_length=80),
        "display_observation_status": clean_identifier(display.get("observation_status"), default="unknown", max_length=80),
        "display_gate_passed": display.get("passed") is True,
        "display_binding_missing": display.get("binding_missing") is True,
        "display_binding_contract_consistent": display.get("display_binding_contract_consistent") is True,
        "public_comment_text_present": public_assignment.get("public_comment_text_present") is True,
        "public_assignment_contract_consistent": public_assignment.get("public_assignment_contract_consistent") is True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }


def build_p7_hold004_step5_candidate_gate_baseline_freeze(
    *,
    observations: Sequence[Mapping[str, Any]],
    full_backend_suite_collect_count: int = 2651,
    full_backend_suite_maxfail_first_failure_ref: Any = STEP5_FAIL_CLOSED_TEST_REF,
) -> dict[str, Any]:
    """Build R0 body-free baseline freeze material for the reproduced Step5 red."""

    sanitized: list[dict[str, Any]] = []
    for observation in observations:
        assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
        sanitized.append(dict(observation))
    if not sanitized:
        raise ValueError("HOLD-004 Step5 baseline freeze requires observations")
    red_reproduced = any(
        safe_mapping(row.get("display_binding_summary")).get("passed") is True
        and safe_mapping(row.get("display_binding_summary")).get("binding_missing_without_exception") is True
        for row in sanitized
    )
    freeze = {
        "schema_version": P7_HOLD004_STEP5_BASELINE_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_STEP,
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "freeze_id": "p7_hold004_step5_candidate_gate_baseline_freeze_20260614",
        "status": "RED_REPRODUCED" if red_reproduced else "BASELINE_RECORDED",
        "observations": sanitized,
        "observation_statuses": [_observation_status_row(row) for row in sanitized],
        "full_backend_suite_collect_count": int(full_backend_suite_collect_count),
        "full_backend_suite_maxfail_first_failure_ref": clean_identifier(
            full_backend_suite_maxfail_first_failure_ref,
            default=STEP5_FAIL_CLOSED_TEST_REF,
            max_length=240,
        ),
        "full_backend_suite_first_red_reproduced": red_reproduced,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID] if red_reproduced else [],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_candidate_gate_baseline_freeze_contract(freeze)
    return freeze


def assert_p7_hold004_step5_candidate_gate_baseline_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    if data.get("schema_version") != P7_HOLD004_STEP5_BASELINE_FREEZE_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 baseline freeze schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 baseline freeze phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 baseline freeze red_id")
    observations = data.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("HOLD-004 Step5 baseline freeze requires observations")
    for observation in observations:
        assert_p7_hold004_step5_candidate_gate_observation_contract(safe_mapping(observation))
    if data.get("status") == "RED_REPRODUCED":
        if P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(data.get("unresolved_red_refs"), limit=20, max_length=160):
            raise ValueError("reproduced HOLD-004 Step5 baseline freeze requires unresolved red ref")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 baseline freeze must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 baseline freeze must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_baseline.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_baseline.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_baseline")
    return True


def _default_contract_pair_rows() -> list[dict[str, Any]]:
    return [
        {
            "pair_id": "step5_fail_closed_vs_phase20_public_recovery",
            "left_contract_ref": STEP5_FAIL_CLOSED_TEST_REF,
            "right_contract_ref": STEP5_PUBLIC_RECOVERY_TEST_REF,
            "fixture_family": "complete_initial_low_information_sample",
            "candidate_generation_expected_by_both": True,
            "left_display_expectation": "display_status_not_passed",
            "right_display_expectation": "display_may_pass_after_phase20_recovery",
            "left_public_assignment_expectation": "public_absent_fail_closed",
            "right_public_assignment_expectation": "public_present_after_recovery",
            "binding_contract_consistency_required": True,
            "public_display_permission_decided": False,
            "stale_or_regression_decided": False,
            "classification": "conflicting_public_assignment_expectations_separated_from_binding_contract",
        },
        {
            "pair_id": "step5_step7_existing_gate_preservation_boundary",
            "left_contract_ref": STEP5_FAIL_CLOSED_TEST_REF,
            "right_contract_ref": STEP5_STEP7_INTEGRATION_TEST_REF,
            "fixture_family": "complete_initial_integration_boundary",
            "candidate_generation_expected_by_both": True,
            "left_display_expectation": "candidate_path_must_not_bypass_existing_gates",
            "right_display_expectation": "public_assignment_uses_existing_display_gate_when_gate_passes",
            "left_public_assignment_expectation": "public_absent_when_gate_not_passed",
            "right_public_assignment_expectation": "public_present_when_existing_display_gate_passes",
            "binding_contract_consistency_required": True,
            "public_display_permission_decided": False,
            "stale_or_regression_decided": False,
            "classification": "existing_gate_preservation_kept_separate_from_public_assignment_shape",
        },
    ]


def build_p7_hold004_step5_conflicting_contract_pair_matrix(
    *,
    observations: Sequence[Mapping[str, Any]] = (),
    pair_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build R1 matrix for conflicting Step5 public/fail-closed expectations.

    The matrix records the conflict and the required decision axes only.  It does
    not decide whether the first red is stale-test, runtime regression, or trace
    inconsistency.
    """

    sanitized_observations: list[dict[str, Any]] = []
    for observation in observations:
        assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
        sanitized_observations.append(dict(observation))
    rows = [dict(row) for row in (pair_rows if pair_rows is not None else _default_contract_pair_rows())]
    if not rows:
        raise ValueError("HOLD-004 Step5 conflict matrix requires at least one pair row")
    source_refs = dedupe_identifiers(
        [STEP5_FAIL_CLOSED_TEST_REF, STEP5_PUBLIC_RECOVERY_TEST_REF, STEP5_STEP7_INTEGRATION_TEST_REF]
        + [row.get("left_contract_ref") for row in rows]
        + [row.get("right_contract_ref") for row in rows]
        + [row.get("test_ref") for row in sanitized_observations],
        limit=80,
        max_length=240,
    )
    matrix = {
        "schema_version": P7_HOLD004_STEP5_CONFLICT_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_STEP,
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "matrix_id": "p7_hold004_step5_conflicting_contract_pair_matrix_20260614",
        "status": "CONTRACT_CONFLICT_CLASSIFIED_UNRESOLVED",
        "source_test_refs": source_refs,
        "contract_pairs": rows,
        "observation_statuses": [_observation_status_row(row) for row in sanitized_observations],
        "decision_axes": [
            "candidate_generation_path_confirmed",
            "existing_gate_preservation_confirmed",
            "display_binding_contract_consistency",
            "public_assignment_contract_consistency",
            "stale_test_vs_implementation_regression_not_decided",
        ],
        "public_display_permission_decided": False,
        "stale_or_regression_decided": False,
        "display_binding_contract_consistency_required": True,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID],
        "required_followup_fixes": ["step5_display_binding_contract_consistency"],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(matrix)
    return matrix


def assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_HOLD004_STEP5_CONFLICT_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 conflict matrix schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 conflict matrix phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 conflict matrix red_id")
    if data.get("status") not in _ALLOWED_CONFLICT_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 conflict matrix status")
    pairs = data.get("contract_pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("HOLD-004 Step5 conflict matrix requires pair rows")
    for row in pairs:
        pair = safe_mapping(row)
        if not clean_identifier(pair.get("pair_id"), max_length=160):
            raise ValueError("HOLD-004 Step5 conflict matrix pair requires pair_id")
        if pair.get("binding_contract_consistency_required") is not True:
            raise ValueError("HOLD-004 Step5 conflict matrix must require binding contract consistency")
        if pair.get("public_display_permission_decided") is not False:
            raise ValueError("R1 conflict matrix must not decide public display permission")
        if pair.get("stale_or_regression_decided") is not False:
            raise ValueError("R1 conflict matrix must not decide stale-test vs regression")
    if data.get("display_binding_contract_consistency_required") is not True:
        raise ValueError("HOLD-004 Step5 conflict matrix must keep display binding consistency as a separate axis")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 conflict matrix must keep {key}=False")
    if data.get("public_display_permission_decided") is not False or data.get("stale_or_regression_decided") is not False:
        raise ValueError("R1 conflict matrix must stay undecided")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 conflict matrix must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_conflict_matrix.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_conflict_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_conflict_matrix")
    return True


def _decision_rule_results(observation: Mapping[str, Any]) -> dict[str, Any]:
    display = safe_mapping(observation.get("display_binding_summary"))
    public = safe_mapping(observation.get("public_assignment_summary"))
    binding_required = display.get("binding_required") is True
    binding_used = display.get("binding_used") is True
    binding_missing = display.get("binding_missing") is True
    exception_allowed = display.get("binding_missing_exception_allowed") is True
    exception_valid = bool(exception_allowed and clean_identifier(display.get("binding_missing_exception_id"), max_length=120))
    binding_missing_without_exception = bool(binding_required and binding_used and binding_missing and not exception_valid)
    display_gate_passed = display.get("passed") is True
    display_binding_contract_consistent = not bool(display_gate_passed and binding_missing_without_exception)
    public_comment_text_present = public.get("public_comment_text_present") is True
    current_public_assignment_allowed = bool(public_comment_text_present and display_gate_passed and display_binding_contract_consistent)
    public_assignment_contract_consistent = bool((not public_comment_text_present) or current_public_assignment_allowed)
    return {
        "display_binding_required": binding_required,
        "display_binding_used": binding_used,
        "display_binding_missing": binding_missing,
        "display_gate_passed": display_gate_passed,
        "binding_missing_exception_allowed": exception_allowed,
        "binding_missing_exception_valid": exception_valid,
        "binding_missing_without_exception": binding_missing_without_exception,
        "display_binding_contract_consistent": display_binding_contract_consistent,
        "public_comment_text_present": public_comment_text_present,
        "current_public_assignment_allowed": current_public_assignment_allowed,
        "public_assignment_contract_consistent": public_assignment_contract_consistent,
        "public_assignment_contract_violation": bool(public_comment_text_present and not public_assignment_contract_consistent),
    }


def build_p7_hold004_step5_display_binding_contract_decision_rule(
    *,
    observation: Mapping[str, Any],
    decision_rule_id: Any = P7_HOLD004_STEP5_DECISION_RULE_ID,
) -> dict[str, Any]:
    """Build R2 Display Binding Contract Decision Rule material.

    This function fixes the rule only.  It does not change runtime public
    response behavior and it does not choose an R4 repair branch.
    """

    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    observed = safe_mapping(observation)
    results = _decision_rule_results(observed)
    display_rule_matched = results["binding_missing_without_exception"] is True and results["display_gate_passed"] is True
    public_rule_matched = results["public_assignment_contract_violation"] is True
    current_red_open = bool(display_rule_matched or public_rule_matched)
    if display_rule_matched:
        classification = "display_binding_missing_without_exception_blocks_public_assignment"
    elif public_rule_matched:
        classification = "public_assignment_without_display_binding_contract_consistency"
    else:
        classification = "display_binding_contract_consistent_for_current_material"
    rule = {
        "schema_version": P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R2_R3_STEP,
        "source_observation_schema_version": clean_identifier(
            observed.get("schema_version"), default=P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION, max_length=128
        ),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "decision_rule_id": clean_identifier(
            decision_rule_id, default=P7_HOLD004_STEP5_DECISION_RULE_ID, max_length=160
        ),
        "status": "DECISION_RULE_FIXED_RED_OPEN" if current_red_open else "DECISION_RULE_FIXED_NO_CURRENT_RED",
        "classification": classification,
        "decision_rule_fixed": True,
        "rule_results": results,
        "rules": [
            {
                "rule_id": "binding_missing_without_exception_blocks_display_contract_consistency",
                "when": {
                    "display_binding_required": True,
                    "display_binding_used": True,
                    "display_binding_missing": True,
                    "binding_missing_exception_valid": False,
                },
                "then": {
                    "display_binding_contract_consistent": False,
                    "p7_hold004_red_open": True,
                    "release_allowed": False,
                    "p8_start_allowed": False,
                },
                "matched": display_rule_matched,
            },
            {
                "rule_id": "public_assignment_requires_display_binding_contract_consistency",
                "when": {
                    "public_comment_text_present": True,
                    "display_binding_contract_consistent": False,
                },
                "then": {
                    "public_assignment_contract_consistent": False,
                    "red_id": P7_HOLD004_STEP5_RED_ID,
                },
                "matched": public_rule_matched,
            },
            {
                "rule_id": "public_display_requires_no_missing_or_valid_exception",
                "when": {
                    "public_comment_text_present": True,
                    "display_gate_passed": True,
                },
                "then": {
                    "required_condition_any_of": [
                        "display_binding_missing_false",
                        "binding_missing_exception_allowed_with_non_empty_id",
                    ],
                    "current_public_assignment_allowed": results["current_public_assignment_allowed"],
                },
                "matched": public_rule_matched,
            },
        ],
        "display_binding_contract_consistency_required": True,
        "public_assignment_contract_consistency_required": True,
        "current_public_assignment_allowed": results["current_public_assignment_allowed"],
        "public_display_permission_rule_fixed": True,
        "runtime_public_behavior_changed": False,
        "r4_branch_selected": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID] if current_red_open else [],
        "required_followup_fixes": ["step5_display_binding_contract_consistency"],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(rule)
    return rule


def assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(rule: Mapping[str, Any]) -> bool:
    data = safe_mapping(rule)
    if data.get("schema_version") != P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 decision rule schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 decision rule phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 decision rule red_id")
    if data.get("source_observation_schema_version") != P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("HOLD-004 Step5 decision rule must reference the observation schema")
    if data.get("status") not in _ALLOWED_DECISION_RULE_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 decision rule status")
    if data.get("classification") not in _ALLOWED_DECISION_RULE_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 decision rule classification")
    if data.get("decision_rule_fixed") is not True:
        raise ValueError("HOLD-004 Step5 R2 decision rule must be fixed")
    results = safe_mapping(data.get("rule_results"))
    if results.get("binding_missing_without_exception") is True and results.get("display_gate_passed") is True:
        if results.get("display_binding_contract_consistent") is not False:
            raise ValueError("binding_missing without a valid exception must make display binding inconsistent")
    if results.get("public_comment_text_present") is True and results.get("display_binding_contract_consistent") is False:
        if results.get("public_assignment_contract_consistent") is not False:
            raise ValueError("public assignment must require display binding contract consistency")
        if data.get("current_public_assignment_allowed") is not False:
            raise ValueError("current public assignment must be blocked by the R2 decision rule")
    rules = data.get("rules")
    if not isinstance(rules, list) or len(rules) < 3:
        raise ValueError("HOLD-004 Step5 decision rule requires all R2 rule rows")
    if data.get("runtime_public_behavior_changed") is not False or data.get("r4_branch_selected") is not False:
        raise ValueError("R2 must not change runtime behavior or select an R4 branch")
    if data.get("display_binding_contract_consistency_required") is not True:
        raise ValueError("R2 must require display binding contract consistency")
    if data.get("public_assignment_contract_consistency_required") is not True:
        raise ValueError("R2 must require public assignment contract consistency")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 decision rule must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 decision rule must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_decision_rule.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_decision_rule.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_decision_rule")
    return True


def _binding_count_differential(observation: Mapping[str, Any]) -> bool:
    display = safe_mapping(observation.get("display_binding_summary"))
    grounding = safe_mapping(observation.get("grounding_binding_summary"))
    return bool(
        grounding.get("passed") is True
        and grounding.get("binding_missing") is False
        and _int(grounding.get("binding_count")) == _int(display.get("binding_count"))
        and _int(grounding.get("expected_binding_count")) == _int(display.get("binding_count"))
        and _int(display.get("expected_binding_count")) > _int(display.get("binding_count"))
    )


def build_p7_hold004_step5_owner_layer_decision(
    *,
    observation: Mapping[str, Any],
    decision_rule: Mapping[str, Any],
    conflict_matrix: Mapping[str, Any] | None = None,
    body_line_diff_only_evidence_confirmed: bool = False,
    stale_public_recovery_canonical_evidence_confirmed: bool = False,
    owner_layer_decision_id: Any = P7_HOLD004_STEP5_OWNER_LAYER_DECISION_ID,
) -> dict[str, Any]:
    """Build R3 owner-layer decision material before entering R4.

    The default keeps the current full-backend first red as mixed when the
    display-binding red, binding-count differential, and unresolved public
    expectation conflict coexist.  R4 is not executed here.
    """

    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(decision_rule)
    observed = safe_mapping(observation)
    rule = safe_mapping(decision_rule)
    matrix = safe_mapping(conflict_matrix)
    if matrix:
        assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(matrix)
    results = safe_mapping(rule.get("rule_results"))
    implementation_rule_matched = bool(
        results.get("binding_missing_without_exception") is True and results.get("display_gate_passed") is True
    )
    binding_count_differential_observed = _binding_count_differential(observed)
    trace_rule_matched = bool(binding_count_differential_observed and body_line_diff_only_evidence_confirmed)
    unresolved_conflict_pair_present = bool(
        matrix.get("status") == "CONTRACT_CONFLICT_CLASSIFIED_UNRESOLVED"
        and matrix.get("public_display_permission_decided") is False
        and matrix.get("stale_or_regression_decided") is False
    )
    stale_rule_matched = bool(stale_public_recovery_canonical_evidence_confirmed and unresolved_conflict_pair_present)
    mixed_rule_matched = bool(
        implementation_rule_matched
        and not trace_rule_matched
        and not stale_rule_matched
        and (unresolved_conflict_pair_present or binding_count_differential_observed)
    )

    if stale_rule_matched:
        status = "OWNER_LAYER_STALE_CONTRACT_REPLACEMENT_REQUIRED"
        classification = "stale_test_expectation"
        owner_layer = "test_contract_boundary"
        owner_layers = [owner_layer]
        next_branch = "R4-C"
    elif trace_rule_matched:
        status = "OWNER_LAYER_TRACE_INCONSISTENCY_REPAIR_REQUIRED"
        classification = "meta_trace_inconsistency"
        owner_layer = "binding_presence_meta_source"
        owner_layers = [owner_layer]
        next_branch = "R4-B"
    elif mixed_rule_matched:
        status = "OWNER_LAYER_MIXED_CONTRACT_CONFLICT"
        classification = "mixed_contract_conflict"
        owner_layer = "mixed"
        owner_layers = [
            "step5_meta_boundary",
            "display_gate_binding_contract",
            "binding_presence_meta_source",
            "test_contract_boundary",
        ]
        next_branch = "R4-D"
    elif implementation_rule_matched:
        status = "OWNER_LAYER_IMPLEMENTATION_REPAIR_REQUIRED"
        classification = "implementation_contract_red"
        owner_layer = "display_gate_binding_contract"
        owner_layers = [owner_layer]
        next_branch = "R4-A"
    else:
        status = "OWNER_LAYER_CLASSIFIED_UNRESOLVED"
        classification = "classified_without_current_red_reproduction"
        owner_layer = "unknown"
        owner_layers = [owner_layer]
        next_branch = "none"

    decision = {
        "schema_version": P7_HOLD004_STEP5_OWNER_LAYER_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R2_R3_STEP,
        "source_observation_schema_version": clean_identifier(
            observed.get("schema_version"), default=P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION, max_length=128
        ),
        "source_decision_rule_schema_version": clean_identifier(
            rule.get("schema_version"), default=P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION, max_length=128
        ),
        "source_conflict_matrix_schema_version": clean_identifier(
            matrix.get("schema_version"), default="", max_length=128
        ),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "owner_layer_decision_id": clean_identifier(
            owner_layer_decision_id,
            default=P7_HOLD004_STEP5_OWNER_LAYER_DECISION_ID,
            max_length=160,
        ),
        "status": status,
        "classification": classification,
        "owner_layer": owner_layer,
        "owner_layers": dedupe_identifiers(owner_layers, limit=10, max_length=120),
        "owner_layer_decision_fixed": True,
        "next_branch": next_branch,
        "r4_branch_executed": False,
        "owner_rule_evaluations": {
            "implementation_rule_matched": implementation_rule_matched,
            "binding_count_differential_observed": binding_count_differential_observed,
            "body_line_diff_only_evidence_confirmed": bool(body_line_diff_only_evidence_confirmed),
            "trace_rule_matched": trace_rule_matched,
            "unresolved_conflict_pair_present": unresolved_conflict_pair_present,
            "stale_public_recovery_canonical_evidence_confirmed": bool(
                stale_public_recovery_canonical_evidence_confirmed
            ),
            "stale_rule_matched": stale_rule_matched,
            "mixed_rule_matched": mixed_rule_matched,
        },
        "owner_matrix": [
            {
                "condition_id": "display_binding_missing_no_exception_passed",
                "matched": implementation_rule_matched,
                "classification": "implementation_contract_red",
                "owner_layer": "display_gate_binding_contract",
                "next_branch": "R4-A",
            },
            {
                "condition_id": "grounding_3_3_display_3_4_body_line_diff_confirmed",
                "matched": trace_rule_matched,
                "classification": "meta_trace_inconsistency",
                "owner_layer": "binding_presence_meta_source",
                "next_branch": "R4-B",
            },
            {
                "condition_id": "phase20_public_recovery_canonical_stale_fail_closed_confirmed",
                "matched": stale_rule_matched,
                "classification": "stale_test_expectation",
                "owner_layer": "test_contract_boundary",
                "next_branch": "R4-C",
            },
            {
                "condition_id": "coexisting_unresolved_display_trace_test_contract_conflict",
                "matched": mixed_rule_matched,
                "classification": "mixed_contract_conflict",
                "owner_layer": "mixed",
                "next_branch": "R4-D",
            },
        ],
        "display_binding_contract_consistency_required": True,
        "public_assignment_contract_consistency_required": True,
        "runtime_public_behavior_changed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID] if next_branch != "none" else [],
        "required_followup_fixes": ["step5_display_binding_contract_consistency", f"step5_owner_layer_next_{next_branch.lower()}"],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_owner_layer_decision_contract(decision)
    return decision


def assert_p7_hold004_step5_owner_layer_decision_contract(decision: Mapping[str, Any]) -> bool:
    data = safe_mapping(decision)
    if data.get("schema_version") != P7_HOLD004_STEP5_OWNER_LAYER_DECISION_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 owner layer schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 owner layer phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 owner layer red_id")
    if data.get("source_observation_schema_version") != P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("HOLD-004 Step5 owner decision must reference the observation schema")
    if data.get("source_decision_rule_schema_version") != P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION:
        raise ValueError("HOLD-004 Step5 owner decision must reference the R2 decision rule schema")
    if data.get("status") not in _ALLOWED_OWNER_DECISION_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 owner decision status")
    if data.get("classification") not in _ALLOWED_OWNER_DECISION_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 owner decision classification")
    if data.get("owner_layer") not in (_ALLOWED_OWNER_LAYERS | frozenset({"mixed"})):
        raise ValueError("unsupported HOLD-004 Step5 owner layer")
    owner_layers = set(dedupe_identifiers(data.get("owner_layers"), limit=20, max_length=120))
    if not owner_layers or not owner_layers.issubset(_ALLOWED_OWNER_LAYERS):
        raise ValueError("HOLD-004 Step5 owner decision requires known owner layers")
    if data.get("next_branch") not in _ALLOWED_NEXT_BRANCHES:
        raise ValueError("unsupported HOLD-004 Step5 next branch")
    if data.get("owner_layer_decision_fixed") is not True:
        raise ValueError("R3 owner layer decision must be fixed")
    if data.get("r4_branch_executed") is not False:
        raise ValueError("R3 must not execute R4 repair")
    if data.get("classification") == "implementation_contract_red" and data.get("next_branch") != "R4-A":
        raise ValueError("implementation contract red must route to R4-A")
    if data.get("classification") == "meta_trace_inconsistency" and data.get("next_branch") != "R4-B":
        raise ValueError("meta trace inconsistency must route to R4-B")
    if data.get("classification") == "stale_test_expectation" and data.get("next_branch") != "R4-C":
        raise ValueError("stale test expectation must route to R4-C")
    if data.get("classification") == "mixed_contract_conflict" and data.get("next_branch") != "R4-D":
        raise ValueError("mixed contract conflict must route to R4-D")
    if data.get("classification") == "classified_without_current_red_reproduction" and data.get("next_branch") != "none":
        raise ValueError("unreproduced classification must not route to R4")
    evaluations = safe_mapping(data.get("owner_rule_evaluations"))
    if data.get("classification") == "mixed_contract_conflict" and evaluations.get("mixed_rule_matched") is not True:
        raise ValueError("mixed owner decision must expose the mixed rule evaluation")
    if data.get("runtime_public_behavior_changed") is not False:
        raise ValueError("R3 must not change runtime public behavior")
    if data.get("display_binding_contract_consistency_required") is not True:
        raise ValueError("R3 must require display binding contract consistency")
    if data.get("public_assignment_contract_consistency_required") is not True:
        raise ValueError("R3 must require public assignment contract consistency")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 owner decision must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 owner decision must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_owner_decision.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_owner_decision.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_owner_decision")
    return True


def build_p7_hold004_step5_r4a_display_gate_fail_closed_branch(
    *,
    observation: Mapping[str, Any],
    decision_rule: Mapping[str, Any] | None = None,
    owner_decision: Mapping[str, Any] | None = None,
    branch_id: Any = P7_HOLD004_STEP5_R4A_BRANCH_ID,
    branch_applied: bool | None = None,
) -> dict[str, Any]:
    """Build R4-A Display Gate fail-closed branch material.

    R4-A is the branch that must be available whenever Display still has
    binding_missing without a valid exception.  It is body-free and carries the
    fail-closed reason only; it does not add fixed text, route keys, RN keys, or
    release claims.
    """

    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    observed = safe_mapping(observation)
    rule = safe_mapping(decision_rule)
    if rule:
        assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(rule)
    owner = safe_mapping(owner_decision)
    if owner:
        assert_p7_hold004_step5_owner_layer_decision_contract(owner)
    display = safe_mapping(observed.get("display_binding_summary"))
    public = safe_mapping(observed.get("public_assignment_summary"))
    missing_without_exception = display.get("binding_missing_without_exception") is True
    display_passed = display.get("passed") is True
    public_present = public.get("public_comment_text_present") is True
    should_fail_closed = bool(display_passed and missing_without_exception)
    applied = bool(should_fail_closed if branch_applied is None else branch_applied)
    status = (
        "R4A_FAIL_CLOSED_REPAIR_BRANCH_FIXED"
        if applied
        else "R4A_EVALUATED_NOT_APPLIED_AFTER_TRACE_REPAIR"
    )
    classification = (
        "display_binding_missing_without_exception_requires_fail_closed"
        if applied
        else "display_binding_fail_closed_not_needed_after_trace_repair"
    )
    branch = {
        "schema_version": P7_HOLD004_STEP5_R4A_FAIL_CLOSED_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R4_A_B_STEP,
        "source_observation_schema_version": clean_identifier(
            observed.get("schema_version"), default=P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION, max_length=128
        ),
        "source_decision_rule_schema_version": clean_identifier(
            rule.get("schema_version"), default="", max_length=128
        ),
        "source_owner_layer_schema_version": clean_identifier(
            owner.get("schema_version"), default="", max_length=128
        ),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "branch_id": clean_identifier(branch_id, default=P7_HOLD004_STEP5_R4A_BRANCH_ID, max_length=160),
        "branch": "R4-A",
        "status": status,
        "classification": classification,
        "display_gate_owner_layer": "display_gate_binding_contract",
        "fail_closed_reason": "display_sentence_binding_missing" if applied else "",
        "binding_missing_without_exception_observed": missing_without_exception,
        "display_gate_passed_before_branch": display_passed,
        "public_comment_text_present_before_branch": public_present,
        "expected_display_observation_status_after_branch": "rejected" if applied else clean_identifier(display.get("observation_status"), default="unknown", max_length=80),
        "expected_public_comment_text_present_after_branch": False if applied else public_present,
        "display_rejection_reason_expected": "display_sentence_binding_missing" if applied else "",
        "display_binding_contract_consistent_after_branch": not applied,
        "public_assignment_contract_consistent_after_branch": True,
        "runtime_public_behavior_changed": applied,
        "r4b_trace_repair_branch_required_if_public_recovery_is_canonical": bool(applied),
        "gate_threshold_relaxed": False,
        "display_gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "case_specific_branch_added": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID] if applied else [],
        "required_followup_fixes": [
            "step5_display_binding_contract_consistency",
            "step5_r4b_display_binding_trace_repair" if applied else "step5_r4c_stale_fail_closed_expectation_review",
        ],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_r4a_display_gate_fail_closed_branch_contract(branch)
    return branch


def assert_p7_hold004_step5_r4a_display_gate_fail_closed_branch_contract(branch: Mapping[str, Any]) -> bool:
    data = safe_mapping(branch)
    if data.get("schema_version") != P7_HOLD004_STEP5_R4A_FAIL_CLOSED_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 R4-A schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-A phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-A red_id")
    if data.get("branch") != "R4-A":
        raise ValueError("R4-A branch material must stay on R4-A")
    if data.get("status") not in _ALLOWED_R4A_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 R4-A status")
    if data.get("classification") not in _ALLOWED_R4A_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 R4-A classification")
    if data.get("status") == "R4A_FAIL_CLOSED_REPAIR_BRANCH_FIXED":
        if data.get("fail_closed_reason") != "display_sentence_binding_missing":
            raise ValueError("R4-A fail-closed branch requires display_sentence_binding_missing")
        if data.get("expected_public_comment_text_present_after_branch") is not False:
            raise ValueError("R4-A fail-closed branch must keep public comment_text absent after branch")
    if data.get("gate_threshold_relaxed") is not False or data.get("display_gate_relaxed") is not False:
        raise ValueError("R4-A must not relax Display Gate")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 R4-A must keep {key}=False")
    if data.get("fixed_sentence_template_added") is not False or data.get("case_specific_branch_added") is not False:
        raise ValueError("R4-A must not add fixed text or case-specific branches")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 R4-A must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_r4a.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_r4a.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_r4a")
    return True


def build_p7_hold004_step5_r4b_display_binding_trace_repair_branch(
    *,
    pre_repair_observation: Mapping[str, Any],
    post_repair_observation: Mapping[str, Any] | None = None,
    owner_decision: Mapping[str, Any] | None = None,
    branch_id: Any = P7_HOLD004_STEP5_R4B_BRANCH_ID,
) -> dict[str, Any]:
    """Build R4-B Display binding trace / expected count repair material."""

    assert_p7_hold004_step5_candidate_gate_observation_contract(pre_repair_observation)
    before = safe_mapping(pre_repair_observation)
    after: Mapping[str, Any] = post_repair_observation or {}
    if after:
        assert_p7_hold004_step5_candidate_gate_observation_contract(after)
    owner = safe_mapping(owner_decision)
    if owner:
        assert_p7_hold004_step5_owner_layer_decision_contract(owner)
    before_display = safe_mapping(before.get("display_binding_summary"))
    before_grounding = safe_mapping(before.get("grounding_binding_summary"))
    before_public = safe_mapping(before.get("public_assignment_summary"))
    after_display = safe_mapping(after.get("display_binding_summary")) if after else {}
    after_public = safe_mapping(after.get("public_assignment_summary")) if after else {}
    before_expected = _int(before_display.get("expected_binding_count"))
    before_count = _int(before_display.get("binding_count"))
    grounding_expected = _int(before_grounding.get("expected_binding_count"))
    after_expected = _int(after_display.get("expected_binding_count"), grounding_expected or before_count)
    after_missing = bool(after_display.get("binding_missing")) if after_display else False
    repair_applied = bool(
        after_display
        and before_display.get("binding_missing") is True
        and after_display.get("binding_missing") is False
        and after_expected == grounding_expected
        and _int(after_display.get("binding_count")) == _int(before_grounding.get("binding_count"))
    )
    planned_from_pre_repair = bool(not repair_applied)
    branch = {
        "schema_version": P7_HOLD004_STEP5_R4B_TRACE_REPAIR_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R4_A_B_STEP,
        "source_pre_observation_schema_version": clean_identifier(
            before.get("schema_version"), default=P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION, max_length=128
        ),
        "source_post_observation_schema_version": clean_identifier(
            after.get("schema_version") if isinstance(after, Mapping) else "", default="", max_length=128
        ),
        "source_owner_layer_schema_version": clean_identifier(
            owner.get("schema_version"), default="", max_length=128
        ),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "branch_id": clean_identifier(branch_id, default=P7_HOLD004_STEP5_R4B_BRANCH_ID, max_length=160),
        "branch": "R4-B",
        "status": "R4B_TRACE_REPAIR_APPLIED" if repair_applied else "R4B_TRACE_REPAIR_PLAN_FIXED",
        "classification": "display_expected_count_aligned_to_accepted_grounding_sentence_count"
        if repair_applied
        else "display_trace_repair_planned_from_pre_repair_material",
        "owner_layer": "binding_presence_meta_source",
        "expected_binding_count_before": before_expected,
        "expected_binding_count_after": after_expected,
        "binding_count_before": before_count,
        "binding_count_after": _int(after_display.get("binding_count"), before_count) if after_display else before_count,
        "grounding_expected_binding_count": grounding_expected,
        "grounding_binding_missing": before_grounding.get("binding_missing") is True,
        "display_binding_missing_before": before_display.get("binding_missing") is True,
        "display_binding_missing_after": after_missing,
        "display_binding_expected_count_source_after": clean_identifier(
            after_display.get("display_binding_expected_count_source")
            or after_display.get("expected_binding_count_source")
            or "accepted_grounding_sentence_count",
            default="accepted_grounding_sentence_count",
            max_length=120,
        ),
        "display_binding_count_source_after": clean_identifier(
            after_display.get("display_binding_count_source")
            or after_display.get("binding_count_source")
            or "sentence_binding_bundle",
            default="sentence_binding_bundle",
            max_length=120,
        ),
        "display_binding_trace_repaired": bool(
            repair_applied
            or after_display.get("display_binding_trace_repaired") is True
            or after_display.get("display_binding_trace_repair_applied") is True
        ),
        "repair_reason": "display_expected_count_aligned_to_accepted_grounding_sentence_count",
        "public_comment_text_present_before": before_public.get("public_comment_text_present") is True,
        "public_comment_text_present_after": bool(after_public.get("public_comment_text_present")) if after_public else False,
        "public_assignment_contract_consistent_after": bool(after_public.get("public_assignment_contract_consistent")) if after_public else False,
        "display_binding_contract_consistent_after": bool(after_display.get("display_binding_contract_consistent")) if after_display else False,
        "runtime_public_behavior_changed": False,
        "r4a_fail_closed_not_applied_to_current_repaired_path": repair_applied,
        "r4c_stale_fail_closed_expectation_review_required": repair_applied,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID] if planned_from_pre_repair else [],
        "required_followup_fixes": [
            "step5_fail_closed_test_contract_review_after_trace_repair" if repair_applied else "step5_display_binding_trace_repair_apply",
            "full_backend_suite_next_red_classification",
        ],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_r4b_display_binding_trace_repair_branch_contract(branch)
    return branch


def assert_p7_hold004_step5_r4b_display_binding_trace_repair_branch_contract(branch: Mapping[str, Any]) -> bool:
    data = safe_mapping(branch)
    if data.get("schema_version") != P7_HOLD004_STEP5_R4B_TRACE_REPAIR_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 R4-B schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-B phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-B red_id")
    if data.get("branch") != "R4-B":
        raise ValueError("R4-B branch material must stay on R4-B")
    if data.get("status") not in _ALLOWED_R4B_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 R4-B status")
    if data.get("classification") not in _ALLOWED_R4B_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 R4-B classification")
    if data.get("status") == "R4B_TRACE_REPAIR_APPLIED":
        if data.get("display_binding_missing_after") is not False:
            raise ValueError("R4-B applied branch must remove display binding_missing")
        if data.get("display_binding_contract_consistent_after") is not True:
            raise ValueError("R4-B applied branch must make Display binding contract consistent")
        if data.get("public_assignment_contract_consistent_after") is not True:
            raise ValueError("R4-B applied branch must make public assignment contract consistent")
        if data.get("expected_binding_count_after") != data.get("grounding_expected_binding_count"):
            raise ValueError("R4-B applied branch must align expected count to accepted grounding count")
    if data.get("runtime_public_behavior_changed") is not False:
        raise ValueError("R4-B trace repair must not change public behavior")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 R4-B must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 R4-B must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_r4b.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_r4b.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_r4b")
    return True


def build_p7_hold004_step5_r4c_stale_test_expectation_update_branch(
    *,
    observation: Mapping[str, Any],
    r4b_branch: Mapping[str, Any] | None = None,
    conflict_matrix: Mapping[str, Any] | None = None,
    owner_decision: Mapping[str, Any] | None = None,
    branch_id: Any = P7_HOLD004_STEP5_R4C_BRANCH_ID,
    target_test_ref: Any = STEP5_FAIL_CLOSED_TEST_REF,
) -> dict[str, Any]:
    """Build R4-C stale test expectation update material.

    R4-C changes the test contract, not runtime behavior.  The stale
    fail-closed expectation may be replaced only when the current repaired path
    proves candidate generation, existing Gate preservation, Display binding
    consistency, public-assignment consistency, and body-free diagnostics.
    """

    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    observed = safe_mapping(observation)
    r4b = safe_mapping(r4b_branch)
    if r4b:
        assert_p7_hold004_step5_r4b_display_binding_trace_repair_branch_contract(r4b)
    matrix = safe_mapping(conflict_matrix)
    if matrix:
        assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(matrix)
    owner = safe_mapping(owner_decision)
    if owner:
        assert_p7_hold004_step5_owner_layer_decision_contract(owner)

    candidate = safe_mapping(observed.get("candidate_summary"))
    gate = safe_mapping(observed.get("gate_preservation_summary"))
    display = safe_mapping(observed.get("display_binding_summary"))
    public = safe_mapping(observed.get("public_assignment_summary"))
    body_free = safe_mapping(observed.get("body_free_markers"))
    r4b_applied = bool(r4b.get("status") == "R4B_TRACE_REPAIR_APPLIED")
    trace_repaired_or_aligned = bool(
        r4b_applied
        or display.get("display_binding_trace_repaired") is True
        or clean_identifier(
            display.get("display_binding_expected_count_source") or display.get("expected_binding_count_source"),
            default="",
            max_length=120,
        )
        == "accepted_grounding_sentence_count"
    )
    replacement = {
        "candidate_generated": candidate.get("candidate_generated") is True,
        "existing_gates_preserved": gate.get("existing_reader_grounding_template_display_gates_preserved") is True,
        "display_gate_relaxed": gate.get("display_gate_relaxed") is True,
        "display_binding_contract_consistent": display.get("display_binding_contract_consistent") is True,
        "display_binding_missing": display.get("binding_missing") is True,
        "public_comment_text_present": public.get("public_comment_text_present") is True,
        "public_assignment_contract_consistent": public.get("public_assignment_contract_consistent") is True,
        "passed_only_comment_text_contract_preserved": public.get("passed_only_comment_text_contract_preserved") is True,
        "raw_input_included": body_free.get("raw_input_included") is True,
        "generated_candidate_text_included": body_free.get("candidate_body_included") is True,
        "candidate_body_included": body_free.get("candidate_body_included") is True,
        "comment_text_body_included": body_free.get("comment_text_body_included") is True,
        "display_binding_trace_repaired_or_aligned": trace_repaired_or_aligned,
    }
    stale_replaced = bool(
        replacement["candidate_generated"]
        and replacement["existing_gates_preserved"]
        and replacement["display_gate_relaxed"] is False
        and replacement["display_binding_contract_consistent"]
        and replacement["display_binding_missing"] is False
        and replacement["public_comment_text_present"]
        and replacement["public_assignment_contract_consistent"]
        and replacement["passed_only_comment_text_contract_preserved"]
        and replacement["raw_input_included"] is False
        and replacement["generated_candidate_text_included"] is False
        and replacement["candidate_body_included"] is False
        and replacement["comment_text_body_included"] is False
        and trace_repaired_or_aligned
    )
    branch = {
        "schema_version": P7_HOLD004_STEP5_R4C_STALE_EXPECTATION_UPDATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R4_C_D_STEP,
        "source_observation_schema_version": clean_identifier(
            observed.get("schema_version"), default=P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION, max_length=128
        ),
        "source_r4b_branch_schema_version": clean_identifier(r4b.get("schema_version"), default="", max_length=128),
        "source_conflict_matrix_schema_version": clean_identifier(matrix.get("schema_version"), default="", max_length=128),
        "source_owner_layer_schema_version": clean_identifier(owner.get("schema_version"), default="", max_length=128),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "branch_id": clean_identifier(branch_id, default=P7_HOLD004_STEP5_R4C_BRANCH_ID, max_length=160),
        "branch": "R4-C",
        "status": "R4C_STALE_TEST_EXPECTATION_REPLACED" if stale_replaced else "R4C_STALE_TEST_EXPECTATION_REVIEW_FIXED",
        "classification": "stale_fail_closed_expectation_replaced_by_gate_preservation_and_binding_contract_consistency"
        if stale_replaced
        else "stale_fail_closed_expectation_review_kept_pending",
        "owner_layer": "test_contract_boundary",
        "target_test_ref": clean_identifier(target_test_ref, default=STEP5_FAIL_CLOSED_TEST_REF, max_length=240),
        "canonical_public_recovery_test_ref": STEP5_PUBLIC_RECOVERY_TEST_REF,
        "target_test_expectation_replaced": stale_replaced,
        "stale_fail_closed_expectation_confirmed": stale_replaced,
        "test_expectation_public_absence_removed": stale_replaced,
        "test_expectation_only_changed": True,
        "removed_expectation_ids": [
            "step5_display_observation_status_must_not_pass",
            "reply_comment_text_must_be_empty",
            "public_comment_text_present_must_be_false",
        ],
        "replacement_assertion_ids": [
            "candidate_generated_true",
            "existing_reader_grounding_template_display_gates_preserved_true",
            "display_gate_relaxed_false",
            "display_binding_contract_consistent_true",
            "public_assignment_contract_consistent_true",
            "passed_only_comment_text_contract_preserved_true",
            "raw_input_included_false",
            "generated_candidate_text_included_false",
        ],
        "replacement_contract_summary": replacement,
        "runtime_public_behavior_changed": False,
        "target_red_closed_by_r4b_r4c": stale_replaced,
        "closed_red_refs": [P7_HOLD004_STEP5_RED_ID] if stale_replaced else [],
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [] if stale_replaced else [P7_HOLD004_STEP5_RED_ID],
        "required_followup_fixes": ["full_backend_suite_next_red_classification"],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_r4c_stale_test_expectation_update_branch_contract(branch)
    return branch


def assert_p7_hold004_step5_r4c_stale_test_expectation_update_branch_contract(branch: Mapping[str, Any]) -> bool:
    data = safe_mapping(branch)
    if data.get("schema_version") != P7_HOLD004_STEP5_R4C_STALE_EXPECTATION_UPDATE_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 R4-C schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-C phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-C red_id")
    if data.get("branch") != "R4-C":
        raise ValueError("R4-C branch material must stay on R4-C")
    if data.get("status") not in _ALLOWED_R4C_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 R4-C status")
    if data.get("classification") not in _ALLOWED_R4C_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 R4-C classification")
    if data.get("runtime_public_behavior_changed") is not False:
        raise ValueError("R4-C must not change runtime public behavior")
    if data.get("test_expectation_only_changed") is not True:
        raise ValueError("R4-C must be a test-contract update only")
    if data.get("status") == "R4C_STALE_TEST_EXPECTATION_REPLACED":
        replacement = safe_mapping(data.get("replacement_contract_summary"))
        if replacement.get("candidate_generated") is not True:
            raise ValueError("R4-C replacement requires candidate generation")
        if replacement.get("existing_gates_preserved") is not True:
            raise ValueError("R4-C replacement requires existing Gate preservation")
        if replacement.get("display_gate_relaxed") is not False:
            raise ValueError("R4-C replacement must not relax Display Gate")
        if replacement.get("display_binding_contract_consistent") is not True:
            raise ValueError("R4-C replacement requires Display binding consistency")
        if replacement.get("display_binding_missing") is not False:
            raise ValueError("R4-C replacement must not leave display binding missing")
        if replacement.get("public_assignment_contract_consistent") is not True:
            raise ValueError("R4-C replacement requires public assignment consistency")
        if replacement.get("raw_input_included") is not False or replacement.get("comment_text_body_included") is not False:
            raise ValueError("R4-C replacement material must remain body-free")
        if data.get("test_expectation_public_absence_removed") is not True:
            raise ValueError("R4-C must remove the stale public-absence expectation")
        if data.get("target_red_closed_by_r4b_r4c") is not True or data.get("closed_red_refs") != [P7_HOLD004_STEP5_RED_ID]:
            raise ValueError("R4-C must close only the current Step5 target red")
        if data.get("unresolved_red_refs") != []:
            raise ValueError("R4-C updated target must not keep the current Step5 red unresolved")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 R4-C must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 R4-C must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_r4c.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_r4c.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_r4c")
    return True


def build_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch(
    *,
    observation: Mapping[str, Any],
    decision_rule: Mapping[str, Any] | None = None,
    conflict_matrix: Mapping[str, Any] | None = None,
    owner_decision: Mapping[str, Any] | None = None,
    branch_id: Any = P7_HOLD004_STEP5_R4D_BRANCH_ID,
) -> dict[str, Any]:
    """Build R4-D mixed contract conflict HOLD material without runtime changes."""

    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    observed = safe_mapping(observation)
    rule = safe_mapping(decision_rule)
    if rule:
        assert_p7_hold004_step5_display_binding_contract_decision_rule_contract(rule)
    matrix = safe_mapping(conflict_matrix)
    if matrix:
        assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract(matrix)
    owner = safe_mapping(owner_decision)
    if owner:
        assert_p7_hold004_step5_owner_layer_decision_contract(owner)

    display = safe_mapping(observed.get("display_binding_summary"))
    public = safe_mapping(observed.get("public_assignment_summary"))
    owner_layers = dedupe_identifiers(
        owner.get("owner_layers")
        or ["step5_meta_boundary", "display_gate_binding_contract", "binding_presence_meta_source", "test_contract_boundary"],
        limit=10,
        max_length=120,
    )
    mixed_owner = bool(owner.get("classification") == "mixed_contract_conflict" and owner.get("next_branch") == "R4-D")
    branch = {
        "schema_version": P7_HOLD004_STEP5_R4D_MIXED_CONFLICT_HOLD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R4_C_D_STEP,
        "source_observation_schema_version": clean_identifier(
            observed.get("schema_version"), default=P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION, max_length=128
        ),
        "source_decision_rule_schema_version": clean_identifier(rule.get("schema_version"), default="", max_length=128),
        "source_conflict_matrix_schema_version": clean_identifier(matrix.get("schema_version"), default="", max_length=128),
        "source_owner_layer_schema_version": clean_identifier(owner.get("schema_version"), default="", max_length=128),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "branch_id": clean_identifier(branch_id, default=P7_HOLD004_STEP5_R4D_BRANCH_ID, max_length=160),
        "branch": "R4-D",
        "status": "R4D_MIXED_CONTRACT_CONFLICT_HELD",
        "classification": "mixed_contract_conflict_preserved_as_hold_material",
        "owner_layer": "mixed",
        "owner_layers": owner_layers,
        "mixed_owner_decision_confirmed": mixed_owner,
        "mixed_contract_conflict_preserved": True,
        "mixed_conflict_components": [
            "display_binding_contract_consistency",
            "display_binding_trace_expected_count_source",
            "stale_fail_closed_test_expectation",
            "public_assignment_contract_consistency",
        ],
        "display_binding_missing": display.get("binding_missing") is True,
        "display_binding_contract_consistent": display.get("display_binding_contract_consistent") is True,
        "display_gate_passed": display.get("passed") is True,
        "public_comment_text_present": public.get("public_comment_text_present") is True,
        "public_assignment_contract_consistent": public.get("public_assignment_contract_consistent") is True,
        "selected_as_single_runtime_repair": False,
        "failing_test_kept_failed_when_r4d_selected": True,
        "validation_matrix_connection_required": True,
        "release_handoff_connection_required": True,
        "validation_matrix_connection_deferred_to_r6": True,
        "release_handoff_connection_deferred_to_r6": True,
        "release_blocker": True,
        "release_blocker_recorded": True,
        "runtime_public_behavior_changed": False,
        "r4a_executed": False,
        "r4b_executed": False,
        "r4c_executed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID],
        "required_followup_fixes": [
            "step5_mixed_contract_conflict_owner_narrowing",
            "step5_mixed_contract_conflict_release_blocker_connection",
            "full_backend_suite_next_red_classification",
        ],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_contract(branch)
    return branch


def assert_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_contract(branch: Mapping[str, Any]) -> bool:
    data = safe_mapping(branch)
    if data.get("schema_version") != P7_HOLD004_STEP5_R4D_MIXED_CONFLICT_HOLD_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 R4-D schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-D phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 R4-D red_id")
    if data.get("branch") != "R4-D":
        raise ValueError("R4-D branch material must stay on R4-D")
    if data.get("status") not in _ALLOWED_R4D_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 R4-D status")
    if data.get("classification") not in _ALLOWED_R4D_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 R4-D classification")
    if data.get("owner_layer") != "mixed":
        raise ValueError("R4-D must keep mixed owner layer")
    if data.get("mixed_owner_decision_confirmed") is not True:
        raise ValueError("R4-D requires a mixed R3 owner decision")
    owner_layers = set(dedupe_identifiers(data.get("owner_layers"), limit=20, max_length=120))
    required_layers = {"step5_meta_boundary", "display_gate_binding_contract", "binding_presence_meta_source", "test_contract_boundary"}
    if not required_layers.issubset(owner_layers):
        raise ValueError("R4-D must preserve all mixed owner layers")
    if data.get("mixed_contract_conflict_preserved") is not True:
        raise ValueError("R4-D must preserve the mixed contract conflict")
    if data.get("selected_as_single_runtime_repair") is not False:
        raise ValueError("R4-D must not select a single runtime repair")
    if data.get("runtime_public_behavior_changed") is not False:
        raise ValueError("R4-D must not change runtime public behavior")
    if data.get("release_blocker") is not True or data.get("release_blocker_recorded") is not True:
        raise ValueError("R4-D must keep release blocker material")
    if data.get("validation_matrix_connection_required") is not True:
        raise ValueError("R4-D must require validation-matrix connection")
    if data.get("release_handoff_connection_required") is not True:
        raise ValueError("R4-D must require release-handoff connection")
    if data.get("validation_matrix_connection_deferred_to_r6") is not True:
        raise ValueError("R4-D must defer validation matrix connection to R6")
    if data.get("release_handoff_connection_deferred_to_r6") is not True:
        raise ValueError("R4-D must defer release handoff connection to R6")
    if data.get("unresolved_red_refs") != [P7_HOLD004_STEP5_RED_ID]:
        raise ValueError("R4-D must keep the Step5 red unresolved")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 R4-D must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 R4-D must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_r4d.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_r4d.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_r4d")
    return True


def _step5_contract_classification(
    *,
    candidate_generated: bool,
    candidate_generation_attempted: bool,
    display_status: str,
    display_binding_contract_consistent: bool,
    display_binding_missing_without_exception: bool,
    public_assignment_contract_consistent: bool,
    public_comment_text_present: bool,
) -> str:
    if not candidate_generation_attempted and not candidate_generated:
        return "blocked_before_candidate_generation"
    if not candidate_generated:
        return "candidate_not_generated"
    if display_binding_missing_without_exception or not display_binding_contract_consistent:
        return "candidate_generated_display_binding_inconsistent"
    if display_status != "passed":
        return "candidate_generated_fail_closed"
    if public_comment_text_present and public_assignment_contract_consistent:
        return "candidate_generated_public_allowed"
    return "candidate_generated_fail_closed"


def build_p7_hold004_step5_r5_meta_extension_material(
    *,
    observation: Mapping[str, Any],
    r4c_branch: Mapping[str, Any] | None = None,
    r4d_branch: Mapping[str, Any] | None = None,
    extension_id: Any = P7_HOLD004_STEP5_R5_META_EXTENSION_ID,
) -> dict[str, Any]:
    """Build R5 body-free Step5 meta-extension material.

    R5 separates candidate generation, existing Gate preservation, Display
    binding consistency, and public assignment consistency.  It is diagnostic /
    multi-perspective meta only and never changes public response top-level keys.
    """

    assert_p7_hold004_step5_candidate_gate_observation_contract(observation)
    observed = safe_mapping(observation)
    r4c = safe_mapping(r4c_branch)
    if r4c_branch is not None:
        assert_p7_hold004_step5_r4c_stale_test_expectation_update_branch_contract(r4c)
    r4d = safe_mapping(r4d_branch)
    if r4d_branch is not None:
        assert_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_contract(r4d)

    candidate = safe_mapping(observed.get("candidate_summary"))
    gate = safe_mapping(observed.get("gate_preservation_summary"))
    display = safe_mapping(observed.get("display_binding_summary"))
    public_assignment = safe_mapping(observed.get("public_assignment_summary"))
    candidate_generated = candidate.get("candidate_generated") is True
    candidate_attempted = candidate.get("candidate_generation_attempted") is True
    gates_preserved = gate.get("existing_reader_grounding_template_display_gates_preserved") is True
    display_status = clean_identifier(display.get("observation_status"), default="unknown", max_length=80)
    display_binding_contract_consistent = display.get("display_binding_contract_consistent") is True
    public_assignment_contract_consistent = public_assignment.get("public_assignment_contract_consistent") is True
    missing_without_exception = display.get("binding_missing_without_exception") is True
    public_present = public_assignment.get("public_comment_text_present") is True
    classification = _step5_contract_classification(
        candidate_generated=candidate_generated,
        candidate_generation_attempted=candidate_attempted,
        display_status=display_status,
        display_binding_contract_consistent=display_binding_contract_consistent,
        display_binding_missing_without_exception=missing_without_exception,
        public_assignment_contract_consistent=public_assignment_contract_consistent,
        public_comment_text_present=public_present,
    )
    extension_keys = [
        "step5_contract_classification",
        "candidate_path_confirmed",
        "gate_preservation_confirmed",
        "display_binding_contract_consistent",
        "public_assignment_contract_consistent",
        "display_binding_missing_without_exception",
        "display_binding_missing_exception_allowed",
        "display_binding_missing_exception_id",
        "display_binding_rejection_reason_expected",
        "public_assignment_allowed_by_display_gate",
        "public_assignment_blocked_by_binding_contract",
    ]
    contract_boundary = {
        "step5_contract_classification": classification,
        "candidate_path_confirmed": bool(candidate_generated),
        "gate_preservation_confirmed": bool(gates_preserved),
        "display_binding_contract_consistent": display_binding_contract_consistent,
        "public_assignment_contract_consistent": public_assignment_contract_consistent,
        "display_binding_missing_without_exception": missing_without_exception,
        "display_binding_missing_exception_allowed": display.get("binding_missing_exception_allowed") is True,
        "display_binding_missing_exception_id": clean_identifier(display.get("binding_missing_exception_id"), default="", max_length=160),
        "display_binding_rejection_reason_expected": "display_sentence_binding_missing" if missing_without_exception else "",
        "public_assignment_allowed_by_display_gate": public_assignment.get("public_assignment_allowed_by_display_gate") is True,
        "public_assignment_blocked_by_binding_contract": bool(public_present and not display_binding_contract_consistent),
        "body_free": True,
    }
    material = {
        "schema_version": P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R5_R6_STEP,
        "source_observation_schema_version": clean_identifier(
            observed.get("schema_version"), default=P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION, max_length=128
        ),
        "source_r4c_branch_schema_version": clean_identifier(r4c.get("schema_version"), default="", max_length=128),
        "source_r4d_branch_schema_version": clean_identifier(r4d.get("schema_version"), default="", max_length=128),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "extension_id": clean_identifier(extension_id, default=P7_HOLD004_STEP5_R5_META_EXTENSION_ID, max_length=160),
        "status": "R5_STEP5_META_EXTENSION_READY",
        "classification": classification,
        "step5_contract_classification": classification,
        "diagnostic_summary_extension_ready": True,
        "multi_perspective_extension_ready": True,
        "diagnostic_summary_body_free_meta_only": True,
        "multi_perspective_body_free_meta_only": True,
        "public_response_top_level_key_changed": False,
        "public_response_top_level_key_added": False,
        "candidate_path_confirmed": bool(candidate_generated),
        "gate_preservation_confirmed": bool(gates_preserved),
        "display_binding_contract_consistent": display_binding_contract_consistent,
        "public_assignment_contract_consistent": public_assignment_contract_consistent,
        "display_binding_missing_without_exception": missing_without_exception,
        "display_binding_missing_exception_allowed": display.get("binding_missing_exception_allowed") is True,
        "display_binding_missing_exception_id": clean_identifier(display.get("binding_missing_exception_id"), default="", max_length=160),
        "display_binding_rejection_reason_expected": "display_sentence_binding_missing" if missing_without_exception else "",
        "public_assignment_allowed_by_display_gate": public_assignment.get("public_assignment_allowed_by_display_gate") is True,
        "public_assignment_blocked_by_binding_contract": bool(public_present and not display_binding_contract_consistent),
        "step5_contract_boundary": contract_boundary,
        "diagnostic_summary_keys_added": extension_keys,
        "multi_perspective_phase_gate_keys_added": extension_keys,
        "runtime_public_behavior_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "rn_visible_contract_changed": False,
        "db_write_path_changed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID] if missing_without_exception else [],
        "required_followup_fixes": ["step5_display_binding_contract_consistency"],
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_r5_meta_extension_material_contract(material)
    return material


def assert_p7_hold004_step5_r5_meta_extension_material_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    if data.get("schema_version") != P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 R5 schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 R5 phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 R5 red_id")
    if data.get("status") not in _ALLOWED_R5_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 R5 status")
    if data.get("classification") not in _ALLOWED_R5_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 R5 classification")
    boundary = safe_mapping(data.get("step5_contract_boundary"))
    for key in (
        "step5_contract_classification",
        "candidate_path_confirmed",
        "gate_preservation_confirmed",
        "display_binding_contract_consistent",
        "public_assignment_contract_consistent",
        "display_binding_missing_without_exception",
        "display_binding_missing_exception_allowed",
        "display_binding_missing_exception_id",
        "display_binding_rejection_reason_expected",
        "public_assignment_allowed_by_display_gate",
        "public_assignment_blocked_by_binding_contract",
    ):
        if key not in boundary:
            raise ValueError(f"R5 Step5 contract boundary missing {key}")
    if boundary.get("step5_contract_classification") != data.get("classification"):
        raise ValueError("R5 classification must mirror contract boundary")
    if boundary.get("body_free") is not True:
        raise ValueError("R5 Step5 contract boundary must be body-free")
    for key in (
        "diagnostic_summary_body_free_meta_only",
        "multi_perspective_body_free_meta_only",
    ):
        if data.get(key) is not True:
            raise ValueError(f"R5 must keep {key}=True")
    for key in (
        "runtime_public_behavior_changed",
        "api_route_changed",
        "request_key_changed",
        "public_response_top_level_key_changed",
        "public_response_top_level_key_added",
        "rn_visible_contract_changed",
        "db_write_path_changed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R5 must keep {key}=False")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 R5 must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 R5 must be body-free")
    if "step5_display_binding_contract_consistency" not in dedupe_identifiers(data.get("required_followup_fixes"), limit=40, max_length=160):
        raise ValueError("R5 must keep Step5 display binding follow-up visible")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_r5.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_r5.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_r5")
    return True


def build_p7_hold004_step5_r6_material_connection(
    *,
    r5_meta_extension: Mapping[str, Any],
    r4d_branch: Mapping[str, Any] | None = None,
    r4c_branch: Mapping[str, Any] | None = None,
    connection_id: Any = P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_ID,
) -> dict[str, Any]:
    """Build R6 body-free P7-HOLD-004 Step5 material connection."""

    assert_p7_hold004_step5_r5_meta_extension_material_contract(r5_meta_extension)
    r5 = safe_mapping(r5_meta_extension)
    r4d = safe_mapping(r4d_branch)
    if r4d_branch is not None:
        assert_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_contract(r4d)
    r4c = safe_mapping(r4c_branch)
    if r4c_branch is not None:
        assert_p7_hold004_step5_r4c_stale_test_expectation_update_branch_contract(r4c)
    step5_red_present = bool(
        r5.get("display_binding_missing_without_exception") is True
        or P7_HOLD004_STEP5_RED_ID in dedupe_identifiers(r4d.get("unresolved_red_refs"), limit=40, max_length=160)
        or r4d.get("release_blocker") is True
    )
    required_followups = dedupe_identifiers(
        [
            "step5_display_binding_contract_consistency",
            *r5.get("required_followup_fixes", []),
            *r4d.get("required_followup_fixes", []),
            "full_backend_suite_next_red_classification",
        ],
        limit=80,
        max_length=160,
    )
    connection = {
        "schema_version": P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_STEP5_R5_R6_STEP,
        "source_r5_meta_extension_schema_version": clean_identifier(
            r5.get("schema_version"), default=P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION, max_length=128
        ),
        "source_r4d_branch_schema_version": clean_identifier(r4d.get("schema_version"), default="", max_length=128),
        "source_r4c_branch_schema_version": clean_identifier(r4c.get("schema_version"), default="", max_length=128),
        "hold_id": P7_HOLD004_STEP5_HOLD_ID,
        "red_id": P7_HOLD004_STEP5_RED_ID,
        "connection_id": clean_identifier(connection_id, default=P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_ID, max_length=160),
        "status": "R6_P7_HOLD004_STEP5_MATERIAL_CONNECTED",
        "classification": "step5_display_binding_material_connected_as_hold004_release_blocker",
        "step5_contract_classification": clean_identifier(r5.get("classification"), default="", max_length=160),
        "step5_display_binding_red_present": step5_red_present,
        "step5_candidate_gate_red_classified": True,
        "step5_candidate_gate_red_closed_by_r4c": r4c.get("target_red_closed_by_r4b_r4c") is True,
        "step5_mixed_contract_conflict_held": r4d.get("mixed_contract_conflict_preserved") is True,
        "validation_matrix_connection_required": True,
        "validation_matrix_connection_ready": True,
        "release_handoff_connection_required": True,
        "release_handoff_connection_ready": True,
        "release_blocker": True,
        "release_blocker_recorded": True,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "required_followup_fixes": required_followups,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID],
        "unresolved_red_refs": [P7_HOLD004_STEP5_RED_ID] if step5_red_present else [],
        "public_response_top_level_key_changed": False,
        "rn_visible_contract_changed": False,
        "db_write_path_changed": False,
        "body_free": True,
        "contract_flags": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_step5_r6_material_connection_contract(connection)
    return connection


def assert_p7_hold004_step5_r6_material_connection_contract(connection: Mapping[str, Any]) -> bool:
    data = safe_mapping(connection)
    if data.get("schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Step5 R6 schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_STEP5_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Step5 R6 phase/hold")
    if data.get("red_id") != P7_HOLD004_STEP5_RED_ID:
        raise ValueError("unexpected HOLD-004 Step5 R6 red_id")
    if data.get("status") not in _ALLOWED_R6_STATUS:
        raise ValueError("unsupported HOLD-004 Step5 R6 status")
    if data.get("classification") not in _ALLOWED_R6_CLASSIFICATION:
        raise ValueError("unsupported HOLD-004 Step5 R6 classification")
    if data.get("step5_candidate_gate_red_classified") is not True:
        raise ValueError("R6 must classify the Step5 candidate gate material")
    if data.get("validation_matrix_connection_ready") is not True:
        raise ValueError("R6 must be ready for validation matrix connection")
    if data.get("release_handoff_connection_ready") is not True:
        raise ValueError("R6 must be ready for release handoff connection")
    if data.get("release_blocker") is not True or data.get("release_blocker_recorded") is not True:
        raise ValueError("R6 must keep Step5 material as release blocker")
    if P7_HOLD004_STEP5_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=160):
        raise ValueError("R6 must keep P7-HOLD-004 unresolved")
    if "step5_display_binding_contract_consistency" not in dedupe_identifiers(data.get("required_followup_fixes"), limit=80, max_length=160):
        raise ValueError("R6 must expose step5_display_binding_contract_consistency follow-up")
    for key in (
        "public_response_top_level_key_changed",
        "rn_visible_contract_changed",
        "db_write_path_changed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R6 must keep {key}=False")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"HOLD-004 Step5 R6 must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("HOLD-004 Step5 R6 must be body-free")
    assert_false_markers(safe_mapping(data.get("contract_flags")), source="p7_hold004_step5_r6.contract_flags")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_step5_r6.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_step5_r6")
    return True


# Compatibility names used by earlier R5/R6 notes.
def build_p7_hold004_step5_meta_extension(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return build_p7_hold004_step5_r5_meta_extension_material(*args, **kwargs)


def assert_p7_hold004_step5_meta_extension_contract(material: Mapping[str, Any]) -> bool:
    return assert_p7_hold004_step5_r5_meta_extension_material_contract(material)


def build_p7_hold004_step5_material_connection(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return build_p7_hold004_step5_r6_material_connection(*args, **kwargs)


def assert_p7_hold004_step5_material_connection_contract(material: Mapping[str, Any]) -> bool:
    return assert_p7_hold004_step5_r6_material_connection_contract(material)




__all__ = [
    "P7_HOLD004_STEP5_BASELINE_FREEZE_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_CONFLICT_MATRIX_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_DECISION_RULE_ID",
    "P7_HOLD004_STEP5_DECISION_RULE_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_HOLD_ID",
    "P7_HOLD004_STEP5_OBSERVATION_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_OWNER_LAYER_DECISION_ID",
    "P7_HOLD004_STEP5_OWNER_LAYER_DECISION_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_R2_R3_STEP",
    "P7_HOLD004_STEP5_RED_ID",
    "P7_HOLD004_STEP5_STEP",
    "P7_HOLD004_STEP5_R4_A_B_STEP",
    "P7_HOLD004_STEP5_R4_C_D_STEP",
    "P7_HOLD004_STEP5_R4A_BRANCH_ID",
    "P7_HOLD004_STEP5_R4A_FAIL_CLOSED_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_R4B_BRANCH_ID",
    "P7_HOLD004_STEP5_R4B_TRACE_REPAIR_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_R4C_BRANCH_ID",
    "P7_HOLD004_STEP5_R4C_STALE_EXPECTATION_UPDATE_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_R4D_BRANCH_ID",
    "P7_HOLD004_STEP5_R4D_MIXED_CONFLICT_HOLD_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_R5_R6_STEP",
    "P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION",
    "P7_HOLD004_STEP5_R5_META_EXTENSION_ID",
    "P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_ID",
    "assert_p7_hold004_step5_meta_extension_contract",
    "assert_p7_hold004_step5_material_connection_contract",
    "assert_p7_hold004_step5_r5_meta_extension_material_contract",
    "assert_p7_hold004_step5_r6_material_connection_contract",
    "build_p7_hold004_step5_meta_extension",
    "build_p7_hold004_step5_material_connection",
    "build_p7_hold004_step5_r5_meta_extension_material",
    "build_p7_hold004_step5_r6_material_connection",
    "assert_p7_hold004_step5_r4a_display_gate_fail_closed_branch_contract",
    "assert_p7_hold004_step5_r4b_display_binding_trace_repair_branch_contract",
    "assert_p7_hold004_step5_r4c_stale_test_expectation_update_branch_contract",
    "assert_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch_contract",
    "build_p7_hold004_step5_r4a_display_gate_fail_closed_branch",
    "build_p7_hold004_step5_r4b_display_binding_trace_repair_branch",
    "build_p7_hold004_step5_r4c_stale_test_expectation_update_branch",
    "build_p7_hold004_step5_r4d_mixed_contract_conflict_hold_branch",
    "STEP5_FAIL_CLOSED_TEST_REF",
    "STEP5_PUBLIC_RECOVERY_TEST_REF",
    "STEP5_STEP7_INTEGRATION_TEST_REF",
    "assert_p7_hold004_step5_candidate_gate_baseline_freeze_contract",
    "assert_p7_hold004_step5_candidate_gate_observation_contract",
    "assert_p7_hold004_step5_conflicting_contract_pair_matrix_contract",
    "assert_p7_hold004_step5_display_binding_contract_decision_rule_contract",
    "assert_p7_hold004_step5_owner_layer_decision_contract",
    "build_p7_hold004_step5_candidate_gate_baseline_freeze",
    "build_p7_hold004_step5_candidate_gate_observation",
    "build_p7_hold004_step5_conflicting_contract_pair_matrix",
    "build_p7_hold004_step5_display_binding_contract_decision_rule",
    "build_p7_hold004_step5_owner_layer_decision",
]
