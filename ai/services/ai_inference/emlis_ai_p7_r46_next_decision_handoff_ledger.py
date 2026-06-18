# -*- coding: utf-8 -*-
"""P7-R46 R14 next-decision summary and handoff ledger.

R14 records the next safe branch after the display-contract/source-lineage
repair path.  It is body-free and release-closed: no raw input, comment text,
reviewer prose, candidate body, terminal output, RN/API/DB mutation, P7
completion, release permission, or P8 start permission is materialized here.
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
from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
)
from emlis_ai_p7_r46_real_device_modal_review_closed_validation import (
    HOLD_DC_FULL_BACKEND_SUITE_REF,
    P7_HOLD_FULL_BACKEND_SUITE_REF,
    P7_HOLD_REAL_DEVICE_MODAL_REF,
    P7_RETURN_REAL_DEVICE_HOLD_REF,
    assert_p7_hold_release_p8_closed_validation_contract,
    build_p7_hold_release_p8_closed_validation,
)

P7_R46_NEXT_DECISION_SUMMARY_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r46.next_decision_summary.v1"
P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r46.next_decision_handoff_ledger.v1"
P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP: Final = "R14_NextDecisionSummaryHandoffLedger_20260617"
P7_R46_NEXT_DECISION_HANDOFF_SCOPE: Final = "p7_r46_next_decision_summary_handoff_ledger"

BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT: Final = "A_DISPLAY_GREEN_PUBLIC_LINEAGE_CONSISTENT"
BRANCH_B_LINEAGE_YELLOW: Final = "B_DISPLAY_GREEN_PUBLIC_LINEAGE_YELLOW"
BRANCH_C_BODY_LEAK: Final = "C_DISPLAY_RED_BODY_FREE_LEAK_REPAIR_RETURN"
BRANCH_D_GATE_RELAXATION: Final = "D_DISPLAY_RED_GATE_RELAXATION_REPAIR_RETURN"
BRANCH_E_TEST_STALE_ONLY: Final = "E_DISPLAY_RED_TEST_STALE_ONLY_RUNTIME_PUBLIC_META_CONSISTENT"
BRANCH_X_RECLASSIFICATION_REQUIRED: Final = "X_DISPLAY_RED_RECLASSIFICATION_REQUIRED"

# Explicit aliases kept for R14 branch-name readability.
BRANCH_B_DISPLAY_GREEN_LINEAGE_YELLOW: Final = BRANCH_B_LINEAGE_YELLOW
BRANCH_C_DISPLAY_RED_BODY_FREE_LEAK_REPAIR_RETURN: Final = BRANCH_C_BODY_LEAK
BRANCH_D_DISPLAY_RED_GATE_RELAXATION_REPAIR_RETURN: Final = BRANCH_D_GATE_RELAXATION
BRANCH_E_DISPLAY_RED_TEST_STALE_ONLY_RUNTIME_PUBLIC_META_CONSISTENT: Final = BRANCH_E_TEST_STALE_ONLY
BRANCH_X_DISPLAY_RED_RECLASSIFICATION_REQUIRED: Final = BRANCH_X_RECLASSIFICATION_REQUIRED

_ALLOWED_BRANCHES: Final[frozenset[str]] = frozenset(
    {
        BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT,
        BRANCH_B_LINEAGE_YELLOW,
        BRANCH_C_BODY_LEAK,
        BRANCH_D_GATE_RELAXATION,
        BRANCH_E_TEST_STALE_ONLY,
        BRANCH_X_RECLASSIFICATION_REQUIRED,
    }
)

_BRANCH_SEQUENCES: Final[dict[str, tuple[str, ...]]] = {
    BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT: (
        "local_review_packet_storage_generation_disposal_policy",
        "p5_human_blind_qa_material_generation_and_review",
        "p6_limited_human_readfeel_review_after_p5",
        "real_device_submit_modal_readfeel_review",
    ),
    BRANCH_B_LINEAGE_YELLOW: (
        "public_meta_final_source_consistency_repair_before_human_review",
        "rerun_display_contract_and_lineage_semantics",
    ),
    BRANCH_C_BODY_LEAK: (
        "body_free_leak_guard_repair_before_p5_p6_return",
        "rerun_display_contract_before_human_review",
    ),
    BRANCH_D_GATE_RELAXATION: (
        "gate_relaxation_repair_before_p5_p6_return",
        "rerun_display_contract_before_human_review",
    ),
    BRANCH_E_TEST_STALE_ONLY: (
        "display_contract_semantic_test_update",
        "red_ledger_update_with_test_stale_reason",
        "p5_p6_return_after_semantic_test_update",
    ),
    BRANCH_X_RECLASSIFICATION_REQUIRED: (
        "display_contract_red_reclassification",
        "lineage_evidence_freeze_before_p5_p6_return",
    ),
}
_BRANCH_REASON_IDS: Final[dict[str, tuple[str, ...]]] = {
    BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT: (
        "display_contract_green",
        "public_lineage_consistent",
        "body_free_public_meta_confirmed",
        "p5_p6_human_review_not_yet_run",
        "release_and_p8_closed",
    ),
    BRANCH_B_LINEAGE_YELLOW: ("display_contract_green", "public_lineage_consistency_yellow"),
    BRANCH_C_BODY_LEAK: ("display_contract_red", "body_free_leak_classification"),
    BRANCH_D_GATE_RELAXATION: ("display_contract_red", "gate_relaxation_classification"),
    BRANCH_E_TEST_STALE_ONLY: ("display_contract_red", "test_expectation_stale_only", "runtime_public_meta_consistent"),
    BRANCH_X_RECLASSIFICATION_REQUIRED: ("display_contract_red_or_unknown", "classification_incomplete"),
}
_BRANCH_HOLD_REFS: Final[dict[str, tuple[str, ...]]] = {
    BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT: (),
    BRANCH_B_LINEAGE_YELLOW: ("YELLOW-DC-003",),
    BRANCH_C_BODY_LEAK: ("RED-DC-BODY-FREE-LEAK",),
    BRANCH_D_GATE_RELAXATION: ("RED-DC-GATE-RELAXATION",),
    BRANCH_E_TEST_STALE_ONLY: ("YELLOW-DC-004",),
    BRANCH_X_RECLASSIFICATION_REQUIRED: ("HOLD-DC-RECLASSIFY",),
}
_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "p7_completion",
    "release_readiness",
    "p8_start",
    "p7_hold004_closure",
    "full_backend_suite_green_claim_without_execution",
)
_REQUIRED_BEFORE_RELEASE: Final[tuple[str, ...]] = (
    "p5_human_blind_qa_confirmed",
    "p6_limited_human_readfeel_confirmed",
    "real_device_submit_modal_readfeel_confirmed",
    "full_backend_suite_green_confirmed",
    "p7_hold004_closure_reviewed_in_release_layer",
)
_LOCAL_REVIEW_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "review_surface",
        "returned_surface",
        "visible_surface",
        "surface_for_reviewer",
        "comment_text_for_reviewer",
        "current_input_for_reviewer",
        "history_summary_for_reviewer",
        "reviewer_free_text",
        "manual_note",
        "manual_notes",
        "terminal_output",
        "traceback",
    }
)


def _contains_local_review_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in _LOCAL_REVIEW_PAYLOAD_KEYS or _contains_local_review_payload_key(child)
            for key, child in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_local_review_payload_key(child) for child in value)
    return False


def _assert_body_free_input(value: Any, *, source: str) -> None:
    if _contains_local_review_payload_key(value):
        raise ValueError(f"{source} contains local-only review payload keys")
    assert_p7_no_body_payload_or_contract_mutation(value, source=source)


def _closed_validation(closed_validation: Mapping[str, Any] | None) -> dict[str, Any]:
    validation = safe_mapping(closed_validation) if closed_validation is not None else build_p7_hold_release_p8_closed_validation()
    assert_p7_hold_release_p8_closed_validation_contract(validation)
    if closed_validation is not None:
        _assert_body_free_input(validation, source="p7_r46_r14.closed_validation")
    return validation


def _closed_validation_summary(validation: Mapping[str, Any]) -> dict[str, Any]:
    release = safe_mapping(validation.get("release_boundary"))
    return {
        "schema_version": clean_identifier(validation.get("schema_version"), default="unknown", max_length=160),
        "current_phase": clean_identifier(validation.get("current_phase"), default="P7", max_length=40),
        "p5_human_blind_qa_material_ready": safe_mapping(validation.get("p5_return_status")).get("human_blind_qa_ready") is True,
        "p6_limited_human_readfeel_material_ready": safe_mapping(validation.get("p6_return_status")).get("limited_review_ready") is True,
        "real_device_checklist_ready": safe_mapping(validation.get("real_device_modal_status")).get("checklist_ready") is True,
        "real_device_modal_review_confirmed": release.get("real_device_modal_review_confirmed") is True,
        "full_backend_suite_green_confirmed": release.get("full_backend_suite_green_confirmed") is True,
        "unresolved_hold_refs": dedupe_identifiers(validation.get("unresolved_hold_refs"), limit=80, max_length=120),
    }


def _display_decision_status(display_contract_status: Mapping[str, Any] | None, *, closed_validation: Mapping[str, Any]) -> dict[str, Any]:
    data = safe_mapping(display_contract_status)
    if display_contract_status is not None:
        _assert_body_free_input(data, source="p7_r46_r14.display_contract_status")
    validation_display = safe_mapping(closed_validation.get("display_contract_status"))
    red_classification = clean_identifier(data.get("red_classification") or data.get("classification"), default="none", max_length=96)
    display_green = data.get("display_contract_green", validation_display.get("display_contract_green", True)) is True
    default_lineage_passed = validation_display.get("lineage_consistency_guarded", True) is True
    public_lineage_passed = data.get("public_lineage_consistency_passed", data.get("public_lineage_consistent", default_lineage_passed)) is True
    body_leak_detected = data.get("body_leak_detected") is True or red_classification == "body_leak"
    gate_relaxation_detected = data.get("gate_relaxation_detected") is True or red_classification == "gate_relaxation"
    test_stale_only = data.get("test_expectation_stale_only") is True or red_classification == "test_expectation_stale_only"
    runtime_public_meta_consistent = data.get("runtime_public_meta_consistent", public_lineage_passed and not body_leak_detected and not gate_relaxation_detected) is True
    return {
        "red_classified": data.get("red_classified", True) is True,
        "display_contract_green": display_green,
        "public_lineage_consistency_passed": public_lineage_passed,
        "public_meta_body_free_confirmed": data.get("public_meta_body_free_confirmed", True) is True,
        "body_leak_detected": body_leak_detected,
        "gate_relaxation_detected": gate_relaxation_detected,
        "test_expectation_stale_only": test_stale_only,
        "runtime_public_meta_consistent": runtime_public_meta_consistent,
        "runtime_regression_detected": data.get("runtime_regression_detected") is True,
        "open_red_ids": dedupe_identifiers(data.get("open_red_ids"), limit=40, max_length=120),
        "yellow_ids": dedupe_identifiers(data.get("yellow_ids"), limit=40, max_length=120),
        "body_free": True,
    }


def _branch_for(display: Mapping[str, Any]) -> str:
    if display.get("body_leak_detected") is True:
        return BRANCH_C_BODY_LEAK
    if display.get("gate_relaxation_detected") is True:
        return BRANCH_D_GATE_RELAXATION
    if display.get("display_contract_green") is True and display.get("public_lineage_consistency_passed") is True:
        return BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT
    if display.get("display_contract_green") is True and display.get("public_lineage_consistency_passed") is not True:
        return BRANCH_B_LINEAGE_YELLOW
    if (
        display.get("display_contract_green") is not True
        and display.get("test_expectation_stale_only") is True
        and display.get("runtime_public_meta_consistent") is True
        and display.get("runtime_regression_detected") is not True
    ):
        return BRANCH_E_TEST_STALE_ONLY
    return BRANCH_X_RECLASSIFICATION_REQUIRED


def _release_closed_flags() -> dict[str, bool]:
    return {
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "release_readiness_claim_allowed": False,
        "p7_completion_claim_allowed": False,
        "p8_start_claim_allowed": False,
    }


def _unresolved_hold_refs(validation: Mapping[str, Any], branch: str) -> list[str]:
    return dedupe_identifiers(
        [
            *dedupe_identifiers(validation.get("unresolved_hold_refs"), limit=80, max_length=120),
            *_BRANCH_HOLD_REFS[branch],
            P5_HUMAN_BLIND_QA_HOLD_REF,
            P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
            P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
            P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
            P7_HOLD_REAL_DEVICE_MODAL_REF,
            P7_RETURN_REAL_DEVICE_HOLD_REF,
            P7_HOLD_FULL_BACKEND_SUITE_REF,
            HOLD_DC_FULL_BACKEND_SUITE_REF,
        ],
        limit=100,
        max_length=120,
    )


def _status_blocks(branch: str, validation: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    p5 = safe_mapping(validation.get("p5_return_status"))
    p6 = safe_mapping(validation.get("p6_return_status"))
    rd = safe_mapping(validation.get("real_device_modal_status"))
    branch_a = branch == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT
    branch_e = branch == BRANCH_E_TEST_STALE_ONLY
    p5_formal_review_allowed = branch_a
    p6_formal_review_allowed = False
    return (
        {
            "human_blind_qa_material_ready": p5.get("human_blind_qa_ready", True) is True,
            "formal_review_start_allowed": p5_formal_review_allowed,
            "human_blind_qa_confirmed": False,
            "hold_ref": P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
            "semantic_test_update_required_before_review": branch_e,
        },
        {
            "limited_human_readfeel_material_ready": p6.get("limited_review_ready", True) is True,
            # R14 only opens the P5 handoff entry. P6 must wait for actual P5
            # human Blind QA completion, so it remains queued, not started here.
            "formal_review_start_allowed": False,
            "ready_after_p5_human_blind_qa": branch_a,
            "human_readfeel_confirmed": False,
            "visible_expansion_allowed": False,
            "hold_ref": P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
            "semantic_test_update_required_before_review": branch_e,
        },
        {
            "checklist_ready": rd.get("checklist_ready", True) is True,
            "modal_review_confirmed": rd.get("confirmed") is True,
            "result": clean_identifier(rd.get("result"), default="NOT_RUN", max_length=80),
            "hold_ref": P7_RETURN_REAL_DEVICE_HOLD_REF,
        },
    )


def build_p7_r46_next_decision_summary(
    *,
    display_contract_status: Mapping[str, Any] | None = None,
    closed_validation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r46_next_decision_summary",
) -> dict[str, Any]:
    """Build the compact R14 next-decision summary."""

    validation = _closed_validation(closed_validation)
    display = _display_decision_status(display_contract_status, closed_validation=validation)
    branch = _branch_for(display)
    p5_status, p6_status, rd_status = _status_blocks(branch, validation)
    unresolved = _unresolved_hold_refs(validation, branch)
    summary = {
        "schema_version": P7_R46_NEXT_DECISION_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP,
        "scope": P7_R46_NEXT_DECISION_HANDOFF_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_next_decision_summary", max_length=160),
        "current_phase": "P7",
        "summary_kind": "next_decision_summary",
        "active_decision_branch": branch,
        "branch_code": branch,
        "display_decision_status": display,
        "display_contract_status": display,
        "p5_return_status": p5_status,
        "p6_return_status": p6_status,
        "real_device_modal_status": rd_status,
        "closed_validation_summary": _closed_validation_summary(validation),
        "next_recommended_work_refs": list(_BRANCH_SEQUENCES[branch]),
        "recommended_next_sequence": list(_BRANCH_SEQUENCES[branch]),
        "branch_reason_ids": list(_BRANCH_REASON_IDS[branch]),
        "blocked_actions": list(_BLOCKED_ACTIONS),
        "required_before_release": list(_REQUIRED_BEFORE_RELEASE),
        "unresolved_hold_refs": unresolved,
        "hold_refs": unresolved,
        "p5_human_blind_qa_start_allowed": branch == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT,
        "p6_limited_human_readfeel_start_allowed": False,
        "real_device_modal_review_start_allowed": branch == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT,
        "human_review_confirmed": False,
        "manual_real_device_review_confirmed": False,
        "p5_p6_return_blocked": branch in {BRANCH_B_LINEAGE_YELLOW, BRANCH_C_BODY_LEAK, BRANCH_D_GATE_RELAXATION, BRANCH_X_RECLASSIFICATION_REQUIRED},
        "semantic_test_update_required": branch == BRANCH_E_TEST_STALE_ONLY,
        "p5_p6_return_allowed_after_test_update": branch == BRANCH_E_TEST_STALE_ONLY,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "full_backend_suite_green_claim_allowed": False,
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r46_next_decision_summary_contract(summary)
    return summary


def _ledger_entries(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    branch = clean_identifier(summary.get("active_decision_branch"), default=BRANCH_X_RECLASSIFICATION_REQUIRED, max_length=120)
    p5 = safe_mapping(summary.get("p5_return_status"))
    p6 = safe_mapping(summary.get("p6_return_status"))
    rd = safe_mapping(summary.get("real_device_modal_status"))
    return [
        {
            "entry_kind": "p5_human_blind_qa_next",
            "status": "READY" if p5.get("formal_review_start_allowed") is True else "BLOCKED",
            "requires_local_body_packet_policy": True,
            "confirmed": p5.get("human_blind_qa_confirmed") is True,
            "hold_ref": P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
        },
        {
            "entry_kind": "p6_limited_human_readfeel_next",
            "status": "READY_AFTER_P5" if branch == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT else "BLOCKED",
            "visible_expansion_allowed": False,
            "confirmed": p6.get("human_readfeel_confirmed") is True,
            "hold_ref": P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
        },
        {
            "entry_kind": "real_device_submit_modal_readfeel_next",
            "status": "READY" if branch == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT else "BLOCKED",
            "checklist_ready": rd.get("checklist_ready") is True,
            "confirmed": rd.get("modal_review_confirmed") is True,
            "hold_ref": P7_RETURN_REAL_DEVICE_HOLD_REF,
        },
        {
            "entry_kind": "release_p7_p8_closed_boundary",
            "status": "CLOSED",
            "release_allowed": False,
            "p7_complete": False,
            "p8_start_allowed": False,
            "hold004_close_allowed": False,
            "hold_ref": HOLD_DC_FULL_BACKEND_SUITE_REF,
        },
    ]


def build_p7_r46_next_decision_handoff_ledger(
    *,
    display_contract_status: Mapping[str, Any] | None = None,
    closed_validation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r46_next_decision_handoff_ledger",
) -> dict[str, Any]:
    """Build the R14 body-free next-decision handoff ledger."""

    summary = build_p7_r46_next_decision_summary(display_contract_status=display_contract_status, closed_validation=closed_validation)
    entries = _ledger_entries(summary)
    ledger = {
        "schema_version": P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP,
        "scope": P7_R46_NEXT_DECISION_HANDOFF_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_next_decision_handoff_ledger", max_length=160),
        "current_phase": "P7",
        "ledger_kind": "next_decision_handoff_ledger",
        "active_decision_branch": summary["active_decision_branch"],
        "branch_code": summary["branch_code"],
        "display_contract_status": summary["display_contract_status"],
        "recommended_next_sequence": ["p5_human_blind_qa_material_generation_and_review", "p6_limited_human_readfeel_review_after_p5", "real_device_submit_modal_readfeel_review"] if summary["branch_code"] == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT else list(summary["next_recommended_work_refs"]),
        "next_decision_summary": summary,
        "ledger_entries": entries,
        "ledger_entry_count": len(entries),
        "blocked_actions": list(_BLOCKED_ACTIONS),
        "required_before_release": list(_REQUIRED_BEFORE_RELEASE),
        "unresolved_hold_refs": list(summary["unresolved_hold_refs"]),
        "hold_refs": list(summary["hold_refs"]),
        "p5_human_blind_qa_start_allowed": summary["p5_human_blind_qa_start_allowed"],
        "p6_limited_human_readfeel_start_allowed": summary["p6_limited_human_readfeel_start_allowed"],
        "real_device_modal_review_start_allowed": summary["real_device_modal_review_start_allowed"],
        "human_review_confirmed": False,
        "manual_real_device_review_confirmed": False,
        "p5_p6_return_blocked": summary["p5_p6_return_blocked"],
        "semantic_test_update_required": summary["semantic_test_update_required"],
        "p5_p6_return_allowed_after_test_update": summary["p5_p6_return_allowed_after_test_update"],
        "release_boundary": _release_closed_flags(),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "actual_human_review_run_here": False,
        "actual_real_device_review_run_here": False,
        "local_reviewer_payload_materialized_here": False,
        "full_backend_suite_green_claim_allowed": False,
        "body_free": True,
        **_release_closed_flags(),
    }
    assert_p7_r46_next_decision_handoff_ledger_contract(ledger)
    return ledger


def _assert_release_closed(data: Mapping[str, Any], *, source: str) -> None:
    for key in (
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
        "release_readiness_claim_allowed",
        "p7_completion_claim_allowed",
        "p8_start_claim_allowed",
        "full_backend_suite_green_claim_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")


def assert_p7_r46_next_decision_summary_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    if data.get("schema_version") != P7_R46_NEXT_DECISION_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected R14 next-decision summary schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP:
        raise ValueError("unexpected R14 next-decision summary phase or step")
    if data.get("current_phase") != "P7":
        raise ValueError("R14 summary must keep current phase as P7")
    branch = clean_identifier(data.get("active_decision_branch"), default="", max_length=120)
    if branch not in _ALLOWED_BRANCHES:
        raise ValueError("unsupported R14 active decision branch")
    if data.get("body_free") is not True:
        raise ValueError("R14 summary must be body-free")
    _assert_release_closed(data, source="R14 summary")
    display = safe_mapping(data.get("display_decision_status"))
    p5 = safe_mapping(data.get("p5_return_status"))
    p6 = safe_mapping(data.get("p6_return_status"))
    if branch == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT:
        if display.get("display_contract_green") is not True or display.get("public_lineage_consistency_passed") is not True:
            raise ValueError("branch A requires display green and public lineage consistency")
        if p5.get("formal_review_start_allowed") is not True:
            raise ValueError("branch A must open the P5 formal human review path")
    if branch in {BRANCH_B_LINEAGE_YELLOW, BRANCH_C_BODY_LEAK, BRANCH_D_GATE_RELAXATION, BRANCH_X_RECLASSIFICATION_REQUIRED}:
        if p5.get("formal_review_start_allowed") is not False or p6.get("formal_review_start_allowed") is not False:
            raise ValueError("repair/reclassification branches must not start P5/P6 formal review")
    if branch == BRANCH_E_TEST_STALE_ONLY:
        if display.get("test_expectation_stale_only") is not True or display.get("runtime_public_meta_consistent") is not True:
            raise ValueError("branch E requires test-stale-only and runtime/public-meta consistency")
    unresolved = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=100, max_length=120))
    required = {
        P5_HUMAN_BLIND_QA_HOLD_REF,
        P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
        P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
        P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
        P7_HOLD_REAL_DEVICE_MODAL_REF,
        P7_RETURN_REAL_DEVICE_HOLD_REF,
        P7_HOLD_FULL_BACKEND_SUITE_REF,
        HOLD_DC_FULL_BACKEND_SUITE_REF,
    }
    if required - unresolved:
        raise ValueError("R14 summary must preserve unresolved P5/P6/real-device/full-backend HOLD refs")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r46_r14_summary.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r46_r14_summary.body_free_markers")
    _assert_body_free_input(data, source="p7_r46_r14.next_decision_summary")
    return True


def assert_p7_r46_next_decision_handoff_ledger_contract(ledger: Mapping[str, Any]) -> bool:
    data = safe_mapping(ledger)
    if data.get("schema_version") != P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION:
        raise ValueError("unexpected R14 next-decision ledger schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP:
        raise ValueError("unexpected R14 next-decision ledger phase or step")
    if data.get("current_phase") != "P7":
        raise ValueError("R14 ledger must keep current phase as P7")
    if data.get("body_free") is not True:
        raise ValueError("R14 ledger must be body-free")
    _assert_release_closed(data, source="R14 ledger")
    summary = safe_mapping(data.get("next_decision_summary"))
    assert_p7_r46_next_decision_summary_contract(summary)
    if data.get("active_decision_branch") != summary.get("active_decision_branch") or data.get("branch_code") != summary.get("active_decision_branch"):
        raise ValueError("R14 ledger branch must match nested summary branch")
    entries = data.get("ledger_entries")
    if not isinstance(entries, list) or data.get("ledger_entry_count") != len(entries) or len(entries) != 4:
        raise ValueError("R14 ledger must contain exactly four ledger entries")
    release_entry = safe_mapping(entries[-1])
    if release_entry.get("status") != "CLOSED":
        raise ValueError("R14 release/P7/P8 ledger entry must stay CLOSED")
    for key in ("release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if release_entry.get(key) is not False:
            raise ValueError(f"R14 release/P7/P8 ledger entry must keep {key}=False")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r46_r14_ledger.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r46_r14_ledger.body_free_markers")
    _assert_body_free_input(data, source="p7_r46_r14.next_decision_handoff_ledger")
    return True


__all__ = [
    "BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT",
    "BRANCH_B_DISPLAY_GREEN_LINEAGE_YELLOW",
    "BRANCH_B_LINEAGE_YELLOW",
    "BRANCH_C_BODY_LEAK",
    "BRANCH_C_DISPLAY_RED_BODY_FREE_LEAK_REPAIR_RETURN",
    "BRANCH_D_DISPLAY_RED_GATE_RELAXATION_REPAIR_RETURN",
    "BRANCH_D_GATE_RELAXATION",
    "BRANCH_E_DISPLAY_RED_TEST_STALE_ONLY_RUNTIME_PUBLIC_META_CONSISTENT",
    "BRANCH_E_TEST_STALE_ONLY",
    "BRANCH_X_DISPLAY_RED_RECLASSIFICATION_REQUIRED",
    "BRANCH_X_RECLASSIFICATION_REQUIRED",
    "P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION",
    "P7_R46_NEXT_DECISION_HANDOFF_LEDGER_STEP",
    "P7_R46_NEXT_DECISION_HANDOFF_SCOPE",
    "P7_R46_NEXT_DECISION_SUMMARY_SCHEMA_VERSION",
    "assert_p7_r46_next_decision_handoff_ledger_contract",
    "assert_p7_r46_next_decision_summary_contract",
    "build_p7_r46_next_decision_handoff_ledger",
    "build_p7_r46_next_decision_summary",
]
