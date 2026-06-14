# -*- coding: utf-8 -*-
"""P7-HOLD-004 Phase16 R4 repair and stale-contract material.

R4 scope:
- R4-A records the runtime repair boundary after Complete Composer can return a
  generated internal candidate for a structurally ready two-stage surface;
- R4-B records the stale-contract replacement design that would be used only if
  R3 explicitly routes the issue to stale direct-contract replacement.

Both materials are body-free and release-closed.  They do not serialize raw
input, public reply bodies, candidate bodies, surface bodies, reviewer text, or
terminal output.
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
from emlis_ai_p7_hold004_phase16_composer_classification import P7_HOLD004_PHASE16_HOLD_ID
from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION,
    assert_p7_hold004_phase16_decision_rule_contract,
)

P7_HOLD004_PHASE16_R4_STEP: Final = "P7-HOLD-004_R4-A_R4-B_Phase16CandidateBoundary_20260613"
P7_HOLD004_PHASE16_R4A_REPAIR_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_r4a_runtime_repair.v1"
)
P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.phase16_r4b_stale_contract_replacement_design.v1"
)

_ALLOWED_R4A_STATUSES: Final[frozenset[str]] = frozenset({"REPAIRED_PENDING_REGRESSION"})
_ALLOWED_R4B_STATUSES: Final[frozenset[str]] = frozenset({"STALE_CONTRACT_REPLACEMENT_DESIGNED"})
_R4B_TARGET_TEST_REF: Final = "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py"


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "passed", "green"}


def _object_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    out: dict[str, Any] = {}
    for key in ("status", "composer_source", "composer_meta"):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


def _meta_from_result(result: Any) -> dict[str, Any]:
    data = _object_mapping(result)
    return safe_mapping(data.get("composer_meta"))


def _status_from_result(result: Any) -> str:
    data = _object_mapping(result)
    return clean_identifier(data.get("status"), default="unknown", max_length=80)


def build_p7_hold004_phase16_r4a_runtime_repair_summary(
    *,
    direct_result: Any,
    conversation_result: Any,
    public_daily_path_labelled: bool = True,
    adjacent_public_red_registered: bool = True,
) -> dict[str, Any]:
    """Build body-free R4-A repair material from live runtime results."""

    direct_status = _status_from_result(direct_result)
    conversation_status = _status_from_result(conversation_result)
    direct_meta = _meta_from_result(direct_result)
    conversation_meta = _meta_from_result(conversation_result)
    direct_readiness = safe_mapping(direct_meta.get("complete_surface_candidate_readiness"))
    conversation_readiness = safe_mapping(conversation_meta.get("complete_surface_candidate_readiness"))
    direct_repaired = direct_status == "generated" and direct_meta.get("candidate_generated_before_display_gate") is True
    conversation_repaired = (
        conversation_status == "generated" and conversation_meta.get("candidate_generated_before_display_gate") is True
    )
    surface_structural_ready = bool(
        direct_readiness.get("surface_structural_ready") is True
        and conversation_readiness.get("surface_structural_ready") is True
    )
    display_quality_blocked = bool(
        direct_meta.get("surface_display_quality_blocked_before_display_gate") is True
        or conversation_meta.get("surface_display_quality_blocked_before_display_gate") is True
        or direct_readiness.get("surface_display_quality_blocked") is True
        or conversation_readiness.get("surface_display_quality_blocked") is True
    )
    display_reason_codes = dedupe_identifiers(
        list(direct_meta.get("surface_display_quality_reason_codes_before_display_gate") or [])
        + list(conversation_meta.get("surface_display_quality_reason_codes_before_display_gate") or [])
        + list(direct_readiness.get("display_quality_reason_codes") or [])
        + list(conversation_readiness.get("display_quality_reason_codes") or []),
        limit=80,
        max_length=160,
    )

    summary = {
        "schema_version": P7_HOLD004_PHASE16_R4A_REPAIR_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_R4_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "status": "REPAIRED_PENDING_REGRESSION",
        "repair_branch": "R4-A",
        "repair_kind": "candidate_display_boundary_minimal_repair",
        "direct_path_status": direct_status,
        "conversation_path_status": conversation_status,
        "direct_path_repaired": direct_repaired,
        "conversation_path_repaired": conversation_repaired,
        "target_paths_repaired": bool(direct_repaired and conversation_repaired),
        "candidate_generated_before_display_gate": bool(direct_repaired and conversation_repaired),
        "candidate_status_before_display_gate": "generated" if direct_repaired and conversation_repaired else "not_generated",
        "candidate_status_after_internal_gate": "rejected" if display_quality_blocked else "generated",
        "generated_not_public_display_permission": True,
        "surface_structural_ready_before_display_gate": surface_structural_ready,
        "surface_display_quality_blocked_before_display_gate": display_quality_blocked,
        "surface_display_quality_reason_codes_before_display_gate": display_reason_codes,
        "two_stage_surface_realization_applied": bool(
            safe_mapping(direct_meta.get("two_stage_surface_realization")).get("applied") is True
            and safe_mapping(conversation_meta.get("two_stage_surface_realization")).get("applied") is True
        ),
        "public_comment_text_assigned": False,
        "comment_text_publicly_assigned": False,
        "public_daily_path_labelled": bool(public_daily_path_labelled),
        "adjacent_public_red_registered": bool(adjacent_public_red_registered),
        "r4b_replacement_applied": False,
        "release_ready_claim_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "safety_boundaries": {
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "fixed_sentence_template_added": False,
            "runtime_fixture_branch_added": False,
            "public_response_key_added": False,
        },
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID],
        "required_followup_fixes": dedupe_identifiers(
            ["positive_public_fixture_shape_boundary" if adjacent_public_red_registered else ""],
            limit=20,
            max_length=160,
        ),
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_r4a_runtime_repair_summary_contract(summary)
    return summary


def assert_p7_hold004_phase16_r4a_runtime_repair_summary_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    if data.get("schema_version") != P7_HOLD004_PHASE16_R4A_REPAIR_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 R4-A repair schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 R4-A repair phase/hold")
    if data.get("status") not in _ALLOWED_R4A_STATUSES:
        raise ValueError("unsupported HOLD-004 Phase16 R4-A repair status")
    if data.get("repair_branch") != "R4-A":
        raise ValueError("R4-A repair summary must stay on R4-A branch")
    if data.get("target_paths_repaired") is not True:
        raise ValueError("R4-A repair summary requires direct and conversation target paths repaired")
    if data.get("candidate_generated_before_display_gate") is not True:
        raise ValueError("R4-A repair summary requires candidate generation before display gate")
    if data.get("generated_not_public_display_permission") is not True:
        raise ValueError("R4-A repair must keep generated separate from public display permission")
    if data.get("public_comment_text_assigned") is not False or data.get("comment_text_publicly_assigned") is not False:
        raise ValueError("R4-A repair summary must not assign public comment text")
    safety = safe_mapping(data.get("safety_boundaries"))
    assert_false_markers(safety, source="p7_hold004_phase16_r4a.safety_boundaries")
    for key in (
        "release_ready_claim_allowed",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
        "r4b_replacement_applied",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R4-A repair summary must keep {key}=False")
    if P7_HOLD004_PHASE16_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120):
        raise ValueError("R4-A repair summary must keep P7-HOLD-004 unresolved")
    if data.get("body_free") is not True:
        raise ValueError("R4-A repair summary must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_r4a.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_r4a.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_r4a")
    return True


def build_p7_hold004_phase16_r4b_stale_contract_replacement_design(
    *,
    decision_rule: Mapping[str, Any],
    replacement_target_refs: Sequence[Any] | Any = (_R4B_TARGET_TEST_REF,),
) -> dict[str, Any]:
    """Build body-free R4-B replacement design for an explicit stale decision."""

    assert_p7_hold004_phase16_decision_rule_contract(decision_rule)
    decision = safe_mapping(decision_rule)
    if decision.get("repair_branch") != "R4-B" or decision.get("status") != "STALE_CONTRACT_REPLACEMENT_REQUIRED":
        raise ValueError("R4-B replacement design requires a stale-contract R3 decision")

    design = {
        "schema_version": P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_PHASE16_R4_STEP,
        "hold_id": P7_HOLD004_PHASE16_HOLD_ID,
        "status": "STALE_CONTRACT_REPLACEMENT_DESIGNED",
        "repair_branch": "R4-B",
        "replacement_kind": "replace_stale_direct_generated_expectation",
        "source_decision_rule_schema_version": clean_identifier(
            decision.get("schema_version"), default=P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION, max_length=160
        ),
        "source_decision_status": clean_identifier(decision.get("status"), max_length=120),
        "replacement_target_refs": dedupe_identifiers(replacement_target_refs, limit=20, max_length=220),
        "old_direct_expected_status_kind": "generated_candidate_before_display_gate",
        "new_direct_expected_status_kind": "unavailable_with_body_free_reason_and_public_recovery_required",
        "public_daily_path_contract_required": True,
        "direct_unavailable_reason_summary_required": True,
        "two_stage_surface_summary_required": True,
        "tone_or_display_blocker_summary_required": True,
        "public_path_must_not_be_silent": True,
        "unavailable_not_safe_success": True,
        "generated_not_public_display_permission": True,
        "replacement_applied_to_test_file": False,
        "r4a_runtime_repair_applied": False,
        "release_ready_claim_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "safety_boundaries": {
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "fixed_sentence_template_added": False,
            "runtime_fixture_branch_added": False,
            "public_response_key_added": False,
        },
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID],
        "required_followup_fixes": ["phase16_direct_contract_replacement"],
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract(design)
    return design


def assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract(design: Mapping[str, Any]) -> bool:
    data = safe_mapping(design)
    if data.get("schema_version") != P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION:
        raise ValueError("unexpected HOLD-004 Phase16 R4-B replacement design schema_version")
    if data.get("phase") != P7_PHASE or data.get("hold_id") != P7_HOLD004_PHASE16_HOLD_ID:
        raise ValueError("unexpected HOLD-004 Phase16 R4-B replacement design phase/hold")
    if data.get("status") not in _ALLOWED_R4B_STATUSES:
        raise ValueError("unsupported HOLD-004 Phase16 R4-B replacement design status")
    if data.get("repair_branch") != "R4-B":
        raise ValueError("R4-B replacement design must stay on R4-B branch")
    if data.get("public_daily_path_contract_required") is not True:
        raise ValueError("R4-B replacement design must preserve public daily contract")
    if data.get("unavailable_not_safe_success") is not True:
        raise ValueError("R4-B replacement design must not treat unavailable as safe success")
    if data.get("generated_not_public_display_permission") is not True:
        raise ValueError("R4-B replacement design must keep generated separate from display permission")
    for key in (
        "replacement_applied_to_test_file",
        "r4a_runtime_repair_applied",
        "release_ready_claim_allowed",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"R4-B replacement design must keep {key}=False")
    safety = safe_mapping(data.get("safety_boundaries"))
    assert_false_markers(safety, source="p7_hold004_phase16_r4b.safety_boundaries")
    if P7_HOLD004_PHASE16_HOLD_ID not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120):
        raise ValueError("R4-B replacement design must keep P7-HOLD-004 unresolved")
    if data.get("body_free") is not True:
        raise ValueError("R4-B replacement design must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_phase16_r4b.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_phase16_r4b.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_phase16_r4b")
    return True


__all__ = [
    "P7_HOLD004_PHASE16_R4_STEP",
    "P7_HOLD004_PHASE16_R4A_REPAIR_SCHEMA_VERSION",
    "P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION",
    "assert_p7_hold004_phase16_r4a_runtime_repair_summary_contract",
    "assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract",
    "build_p7_hold004_phase16_r4a_runtime_repair_summary",
    "build_p7_hold004_phase16_r4b_stale_contract_replacement_design",
]
