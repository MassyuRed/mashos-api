# -*- coding: utf-8 -*-
"""P7-R46 R12/R13 real-device modal checklist and release-closed validation.

R12 prepares a body-free checklist for manual submit/modal read-feel review.
R13 keeps P7 completion, release, and P8 start closed until the checks that
cannot be proven by backend/RN subset green are actually performed.

This module intentionally does not change RN, API, DB, gates, or runtime
surfaces.  It records only identifiers, booleans, small counts, and statuses;
it never materializes reviewer-facing payloads, returned surfaces, raw input,
or terminal output.
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
    assert_p5_p6_human_readfeel_handoff_summary_contract,
    build_p5_p6_human_readfeel_handoff_summary,
)

P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r46.real_device_submit_modal_readfeel_checklist.v1"
)
P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r46.hold_release_p8_closed_validation.v1"
)
P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r46.real_device_and_closed_validation_summary.v1"
)
P7_R46_REAL_DEVICE_CLOSED_VALIDATION_STEP: Final = (
    "R12_R13_RealDeviceModalReviewChecklist_ClosedValidation_20260617"
)
P7_R46_REAL_DEVICE_CLOSED_VALIDATION_SCOPE: Final = (
    "p7_r46_real_device_modal_review_and_release_closed_validation"
)

P7_HOLD_FULL_BACKEND_SUITE_REF: Final = "P7-HOLD-004"
HOLD_DC_FULL_BACKEND_SUITE_REF: Final = "HOLD-DC-005"
P7_HOLD_REAL_DEVICE_MODAL_REF: Final = "P7-HOLD-003"
P7_RETURN_REAL_DEVICE_HOLD_REF: Final = "HOLD-RD-001"

_ALLOWED_SCREEN_SIZE_CLASSES: Final[frozenset[str]] = frozenset({"small", "medium", "large", "unknown"})
_ALLOWED_SUBSCRIPTION_TIERS: Final[frozenset[str]] = frozenset({"free", "plus", "premium", "unknown"})
_ALLOWED_MODAL_CHECK_RESULTS: Final[frozenset[str]] = frozenset(
    {"NOT_RUN", "PASS", "YELLOW", "REPAIR_REQUIRED", "RED"}
)
_ALLOWED_CHECK_STATUSES: Final[frozenset[str]] = frozenset(
    {"not_run", "passed", "failed", "blocked", "not_applicable"}
)

_MODAL_CONTRACT_CHECK_KEYS: Final[tuple[str, ...]] = (
    "submit_modal_opened",
    "title_emlis_observation_preserved",
    "visible_payload_source_confirmed",
    "passed_non_empty_only_confirmed",
    "non_passed_hidden_confirmed",
    "public_top_level_shape_preserved",
)
_READFEEL_CHECK_KEYS: Final[tuple[str, ...]] = (
    "phone_readability_reviewed",
    "length_pressure_reviewed",
    "line_break_reviewed",
    "section_weight_reviewed",
    "p5_history_line_creepy_absence_reviewed",
    "p6_structure_insight_overread_absence_reviewed",
    "wants_more_input_reviewed",
)
_READFEEL_AXES: Final[tuple[str, ...]] = (
    "readable_on_phone",
    "length_pressure_absence",
    "weight_absence",
    "shallow_absence",
    "p5_history_line_creepy_absence",
    "p6_overread_absence",
    "wants_more_input",
)
_REQUIRED_MANUAL_REVIEW_FAMILIES: Final[tuple[str, ...]] = (
    "free_standard_state_answer_no_history_line",
    "plus_history_line_eligible",
    "plus_history_line_blocked_low_information",
    "p6_structure_question_visible",
    "p6_daily_positive_no_connect",
)

_REAL_DEVICE_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
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
    }
)


def _contains_real_device_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in _REAL_DEVICE_PAYLOAD_KEYS or _contains_real_device_payload_key(child)
            for key, child in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_real_device_payload_key(child) for child in value)
    return False


def _assert_no_real_device_payload_key(value: Any, *, source: str) -> None:
    if _contains_real_device_payload_key(value):
        raise ValueError(f"{source} contains local-only manual review payload keys")


def _assert_body_free_input(value: Any, *, source: str) -> None:
    _assert_no_real_device_payload_key(value, source=source)
    assert_p7_no_body_payload_or_contract_mutation(value, source=source)


def _safe_status(value: Any, *, default: str = "not_run") -> str:
    status = clean_identifier(value, default=default, max_length=80)
    return status if status in _ALLOWED_CHECK_STATUSES else default


def _safe_result(value: Any, *, default: str = "NOT_RUN") -> str:
    result = clean_identifier(value, default=default, max_length=80).upper()
    return result if result in _ALLOWED_MODAL_CHECK_RESULTS else default


def _score_or_none(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < 0.0 or score > 1.0:
        return None
    return score


def _status_group(source: Mapping[str, Any], keys: Sequence[str]) -> dict[str, str]:
    return {key: _safe_status(source.get(key), default="not_run") for key in keys}


def _scores(source: Mapping[str, Any], keys: Sequence[str]) -> dict[str, float | None]:
    return {key: _score_or_none(source.get(key)) for key in keys}


def _case_ref(row: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    data = safe_mapping(row)
    _assert_body_free_input(data, source=f"p7_r46_real_device_modal_review.case_ref[{index}]")
    tier = clean_identifier(data.get("subscription_tier"), default="unknown", max_length=32)
    if tier not in _ALLOWED_SUBSCRIPTION_TIERS:
        tier = "unknown"
    return {
        "case_ref_id": clean_identifier(
            data.get("case_ref_id") or data.get("case_id") or data.get("row_id"),
            default=f"case_{index}",
            max_length=96,
        ),
        "family": clean_identifier(data.get("family"), default="unknown", max_length=96),
        "subscription_tier": tier,
        "source_row_ref": clean_identifier(data.get("source_row_ref") or data.get("row_id"), default=f"row_{index}", max_length=96),
        "manual_review_required": True,
        "manual_review_confirmed": False,
        "local_payload_materialized_here": False,
        "body_free": True,
    }


def _case_refs(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    return [_case_ref(row, index=index) for index, row in enumerate(list(rows or []), start=1)]


def _device_context(device_context: Mapping[str, Any] | None) -> dict[str, str]:
    data = safe_mapping(device_context)
    if device_context is not None:
        _assert_body_free_input(data, source="p7_r46_real_device_modal_review.device_context")
    size = clean_identifier(data.get("screen_size_class"), default="unknown", max_length=24)
    if size not in _ALLOWED_SCREEN_SIZE_CLASSES:
        size = "unknown"
    return {
        "device_ref": clean_identifier(data.get("device_ref") or data.get("device_label"), default="manual_device_unset", max_length=96),
        "os_ref": clean_identifier(data.get("os_ref") or data.get("os"), default="os_unset", max_length=96),
        "app_build_ref": clean_identifier(data.get("app_build_ref") or data.get("app_build"), default="app_build_unset", max_length=96),
        "screen_size_class": size,
    }


def _runtime_context(runtime_context: Mapping[str, Any] | None) -> dict[str, Any]:
    data = safe_mapping(runtime_context)
    if runtime_context is not None:
        _assert_body_free_input(data, source="p7_r46_real_device_modal_review.runtime_context")
    tier = clean_identifier(data.get("subscription_tier"), default="unknown", max_length=32)
    if tier not in _ALLOWED_SUBSCRIPTION_TIERS:
        tier = "unknown"
    return {
        "api_snapshot_ref": clean_identifier(data.get("api_snapshot_ref") or data.get("api_snapshot"), default="api_snapshot_unset", max_length=120),
        "subscription_tier": tier,
        "case_family": clean_identifier(data.get("case_family") or data.get("family"), default="unknown", max_length=96),
        "display_contract_green_required": True,
        "display_contract_green_confirmed": data.get("display_contract_green") is True
        or data.get("display_contract_green_confirmed") is True,
        "public_meta_final_source_consistency_required": True,
        "public_meta_final_source_consistency_confirmed": data.get("public_meta_final_source_consistency_confirmed") is True,
    }


def _common_closed_flags() -> dict[str, bool]:
    return {
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "automated_green_can_close_manual_review": False,
        "rn_changed": False,
        "api_key_changed": False,
        "db_changed": False,
    }


def build_real_device_submit_modal_readfeel_checklist(
    *,
    device_context: Mapping[str, Any] | None = None,
    runtime_context: Mapping[str, Any] | None = None,
    manual_review_result: Mapping[str, Any] | None = None,
    case_refs: Sequence[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r46_real_device_submit_modal_readfeel_checklist",
) -> dict[str, Any]:
    """Build the R12 body-free checklist for manual real-device modal review.

    The default result is NOT_RUN.  The checklist can record body-free manual
    statuses later, but backend/RN tests alone never close this check and never
    promote release or P8 readiness.
    """

    review = safe_mapping(manual_review_result)
    if manual_review_result is not None:
        _assert_body_free_input(review, source="p7_r46_real_device_modal_review.manual_review_result")
    result = _safe_result(review.get("result"), default="NOT_RUN")
    modal_contract = _status_group(safe_mapping(review.get("modal_contract")), _MODAL_CONTRACT_CHECK_KEYS)
    readfeel_checks = _status_group(safe_mapping(review.get("readfeel_checks")), _READFEEL_CHECK_KEYS)
    readfeel_axes = _scores(safe_mapping(review.get("readfeel_axes")), _READFEEL_AXES)
    body_leak_observed = review.get("body_leak_observed") is True
    gate_relaxed = review.get("gate_relaxed") is True
    failed_or_blocked = any(status in {"failed", "blocked"} for status in (*modal_contract.values(), *readfeel_checks.values()))
    pass_like = (
        result == "PASS"
        and not body_leak_observed
        and not gate_relaxed
        and not failed_or_blocked
        and all(status in {"passed", "not_applicable"} for status in modal_contract.values())
        and all(status in {"passed", "not_applicable"} for status in readfeel_checks.values())
    )
    hold_refs = [] if pass_like else [P7_HOLD_REAL_DEVICE_MODAL_REF, P7_RETURN_REAL_DEVICE_HOLD_REF]
    checklist = {
        "schema_version": P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_REAL_DEVICE_CLOSED_VALIDATION_STEP,
        "scope": P7_R46_REAL_DEVICE_CLOSED_VALIDATION_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_real_device_submit_modal_readfeel_checklist", max_length=160),
        "review_scope": "manual_real_device_review_not_automated_green",
        "checklist_kind": "real_device_submit_modal_readfeel_checklist",
        "device_context": _device_context(device_context),
        "runtime_context": _runtime_context(runtime_context),
        "required_manual_review_families": list(_REQUIRED_MANUAL_REVIEW_FAMILIES),
        "case_refs": _case_refs(case_refs),
        "case_ref_count": len(list(case_refs or [])),
        "modal_contract_checks": modal_contract,
        "readfeel_checks": readfeel_checks,
        "readfeel_axes": readfeel_axes,
        "result": result,
        "manual_real_device_review_required": not pass_like,
        "real_device_modal_review_confirmed": pass_like,
        "manual_review_completed": result != "NOT_RUN",
        "body_leak_observed": body_leak_observed,
        "gate_relaxed_observed": gate_relaxed,
        "local_review_payload_materialized_here": False,
        "local_review_payload_public_meta_material": False,
        "local_review_payload_p7_scorecard_material": False,
        "public_top_level_shape_preserved_required": True,
        "rn_title_preserved_required": True,
        "visible_payload_source_required": "input_feedback_comment_text",
        "hold_refs": hold_refs,
        "unresolved_hold_refs": hold_refs,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_common_closed_flags(),
        "body_free": True,
    }
    assert_real_device_submit_modal_readfeel_checklist_contract(checklist)
    return checklist


def _display_status(display_contract_status: Mapping[str, Any] | None) -> dict[str, Any]:
    data = safe_mapping(display_contract_status)
    if display_contract_status is not None:
        _assert_body_free_input(data, source="p7_r46_closed_validation.display_contract_status")
    return {
        "red_classified": data.get("red_classified", True) is True,
        "display_contract_green": data.get("display_contract_green", True) is True,
        "body_leak_detected": data.get("body_leak_detected") is True,
        "gate_relaxed": data.get("gate_relaxed") is True,
        "lineage_consistency_guarded": data.get("lineage_consistency_guarded", True) is True,
        "public_meta_body_free_confirmed": data.get("public_meta_body_free_confirmed", True) is True,
    }


def _backend_suite_status(backend_suite_status: Mapping[str, Any] | None) -> dict[str, Any]:
    data = safe_mapping(backend_suite_status)
    if backend_suite_status is not None:
        _assert_body_free_input(data, source="p7_r46_closed_validation.backend_suite_status")
    return {
        "target_validation_matrix_ready": data.get("target_validation_matrix_ready", True) is True,
        "full_backend_suite_green_confirmed": data.get("full_backend_suite_green_confirmed") is True,
        "full_backend_suite_claim_allowed": data.get("full_backend_suite_green_confirmed") is True,
        "not_run_or_partial_refs": dedupe_identifiers(
            data.get("not_run_or_partial_refs") or [P7_HOLD_FULL_BACKEND_SUITE_REF, HOLD_DC_FULL_BACKEND_SUITE_REF],
            limit=40,
            max_length=120,
        ),
    }


def _release_boundary(*, checklist: Mapping[str, Any], backend: Mapping[str, Any], display: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "full_backend_suite_green_confirmed": backend.get("full_backend_suite_green_confirmed") is True,
        "real_device_modal_review_confirmed": checklist.get("real_device_modal_review_confirmed") is True,
        "p5_human_blind_qa_confirmed": False,
        "p6_human_readfeel_confirmed": False,
        "display_contract_green": display.get("display_contract_green") is True,
        "body_leak_detected": display.get("body_leak_detected") is True or checklist.get("body_leak_observed") is True,
        "gate_relaxed": display.get("gate_relaxed") is True or checklist.get("gate_relaxed_observed") is True,
    }


def build_p7_hold_release_p8_closed_validation(
    *,
    display_contract_status: Mapping[str, Any] | None = None,
    p5_p6_handoff_summary: Mapping[str, Any] | None = None,
    real_device_checklist: Mapping[str, Any] | None = None,
    backend_suite_status: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r46_hold_release_p8_closed_validation",
) -> dict[str, Any]:
    """Build R13 validation that keeps P7/release/P8 closed."""

    p5p6 = (
        safe_mapping(p5_p6_handoff_summary)
        if p5_p6_handoff_summary is not None
        else build_p5_p6_human_readfeel_handoff_summary()
    )
    assert_p5_p6_human_readfeel_handoff_summary_contract(p5p6)

    checklist = (
        safe_mapping(real_device_checklist)
        if real_device_checklist is not None
        else build_real_device_submit_modal_readfeel_checklist()
    )
    assert_real_device_submit_modal_readfeel_checklist_contract(checklist)

    display = _display_status(display_contract_status)
    backend = _backend_suite_status(backend_suite_status)
    release_boundary = _release_boundary(checklist=checklist, backend=backend, display=display)
    unresolved = dedupe_identifiers(
        [
            *dedupe_identifiers(p5p6.get("unresolved_hold_refs"), limit=40, max_length=120),
            *dedupe_identifiers(checklist.get("unresolved_hold_refs"), limit=40, max_length=120),
            P7_HOLD_FULL_BACKEND_SUITE_REF,
            HOLD_DC_FULL_BACKEND_SUITE_REF,
        ],
        limit=80,
        max_length=120,
    )
    validation = {
        "schema_version": P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_REAL_DEVICE_CLOSED_VALIDATION_STEP,
        "scope": P7_R46_REAL_DEVICE_CLOSED_VALIDATION_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_hold_release_p8_closed_validation", max_length=160),
        "current_phase": "P7",
        "validation_kind": "p7_hold_release_p8_closed_validation",
        "display_contract_status": display,
        "p5_return_status": {
            "human_blind_qa_ready": p5p6.get("p5_human_blind_qa_ready") is True,
            "human_blind_qa_confirmed": False,
            "hold_ref": P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
        },
        "p6_return_status": {
            "limited_review_ready": p5p6.get("p6_limited_human_readfeel_review_ready") is True,
            "human_readfeel_confirmed": False,
            "hold_ref": P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
        },
        "real_device_modal_status": {
            "checklist_ready": True,
            "confirmed": checklist.get("real_device_modal_review_confirmed") is True,
            "result": clean_identifier(checklist.get("result"), default="NOT_RUN", max_length=80),
            "hold_ref": P7_RETURN_REAL_DEVICE_HOLD_REF,
        },
        "backend_suite_status": backend,
        "release_boundary": release_boundary,
        "unresolved_hold_refs": unresolved,
        "hold_refs": unresolved,
        "blocked_next_decision_refs": dedupe_identifiers(
            [
                "P5_human_Blind_QA_not_confirmed",
                "P6_limited_human_readfeel_not_confirmed",
                "real_device_modal_review_not_confirmed",
                "full_backend_suite_green_not_confirmed",
            ],
            limit=20,
            max_length=120,
        ),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        **_common_closed_flags(),
        "body_free": True,
    }
    assert_p7_hold_release_p8_closed_validation_contract(validation)
    return validation


def build_real_device_and_closed_validation_summary(
    *,
    checklist: Mapping[str, Any] | None = None,
    closed_validation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r46_real_device_and_closed_validation_summary",
) -> dict[str, Any]:
    """Build a compact R12/R13 handoff summary."""

    real_device = safe_mapping(checklist) if checklist is not None else build_real_device_submit_modal_readfeel_checklist()
    assert_real_device_submit_modal_readfeel_checklist_contract(real_device)
    validation = (
        safe_mapping(closed_validation)
        if closed_validation is not None
        else build_p7_hold_release_p8_closed_validation(real_device_checklist=real_device)
    )
    assert_p7_hold_release_p8_closed_validation_contract(validation)
    summary = {
        "schema_version": P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_REAL_DEVICE_CLOSED_VALIDATION_STEP,
        "scope": P7_R46_REAL_DEVICE_CLOSED_VALIDATION_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_real_device_and_closed_validation_summary", max_length=160),
        "current_phase": "P7",
        "real_device_checklist_ready": True,
        "real_device_modal_review_confirmed": real_device.get("real_device_modal_review_confirmed") is True,
        "real_device_result": clean_identifier(real_device.get("result"), default="NOT_RUN", max_length=80),
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "unresolved_hold_refs": dedupe_identifiers(validation.get("unresolved_hold_refs"), limit=80, max_length=120),
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
    }
    assert_real_device_and_closed_validation_summary_contract(summary)
    return summary


def assert_real_device_submit_modal_readfeel_checklist_contract(checklist: Mapping[str, Any]) -> bool:
    data = safe_mapping(checklist)
    if data.get("schema_version") != P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION:
        raise ValueError("unexpected R12 real-device checklist schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R46_REAL_DEVICE_CLOSED_VALIDATION_STEP:
        raise ValueError("unexpected R12 real-device checklist phase or step")
    if data.get("review_scope") != "manual_real_device_review_not_automated_green":
        raise ValueError("real-device checklist review scope changed")
    if data.get("release_allowed") is not False or data.get("p7_complete") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("real-device checklist must stay release/P7/P8 closed")
    if data.get("hold004_close_allowed") is not False:
        raise ValueError("real-device checklist must not close P7-HOLD-004")
    if data.get("body_free") is not True:
        raise ValueError("real-device checklist must be body-free")
    result = clean_identifier(data.get("result"), default="NOT_RUN", max_length=80)
    if result not in _ALLOWED_MODAL_CHECK_RESULTS:
        raise ValueError("unsupported real-device checklist result")
    modal_contract = safe_mapping(data.get("modal_contract_checks"))
    readfeel_checks = safe_mapping(data.get("readfeel_checks"))
    if set(modal_contract) != set(_MODAL_CONTRACT_CHECK_KEYS):
        raise ValueError("real-device modal contract checklist changed")
    if set(readfeel_checks) != set(_READFEEL_CHECK_KEYS):
        raise ValueError("real-device readfeel checklist changed")
    if any(clean_identifier(status, max_length=80) not in _ALLOWED_CHECK_STATUSES for status in modal_contract.values()):
        raise ValueError("unsupported modal contract check status")
    if any(clean_identifier(status, max_length=80) not in _ALLOWED_CHECK_STATUSES for status in readfeel_checks.values()):
        raise ValueError("unsupported readfeel check status")
    if data.get("automated_green_can_close_manual_review") is not False:
        raise ValueError("manual real-device review must not close via automated green")
    if result == "NOT_RUN" and data.get("real_device_modal_review_confirmed") is not False:
        raise ValueError("NOT_RUN cannot confirm real-device modal review")
    if data.get("gate_relaxed_observed") is True and result == "PASS":
        raise ValueError("gate relaxation cannot coexist with PASS")
    if data.get("body_leak_observed") is True and result == "PASS":
        raise ValueError("body leak cannot coexist with PASS")
    if data.get("real_device_modal_review_confirmed") is not True:
        unresolved = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40, max_length=120))
        if {P7_HOLD_REAL_DEVICE_MODAL_REF, P7_RETURN_REAL_DEVICE_HOLD_REF} - unresolved:
            raise ValueError("real-device HOLD refs must remain until manual review is confirmed")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r46_real_device_checklist.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r46_real_device_checklist.body_free_markers")
    _assert_body_free_input(data, source="p7_r46_real_device_checklist")
    return True


def assert_p7_hold_release_p8_closed_validation_contract(validation: Mapping[str, Any]) -> bool:
    data = safe_mapping(validation)
    if data.get("schema_version") != P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION:
        raise ValueError("unexpected R13 closed validation schema_version")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R46_REAL_DEVICE_CLOSED_VALIDATION_STEP:
        raise ValueError("unexpected R13 closed validation phase or step")
    if data.get("current_phase") != "P7":
        raise ValueError("R13 must keep current phase as P7")
    for key in ("release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"R13 must keep {key}=False")
    if data.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("R13 must not claim full backend suite green by default")
    if data.get("body_free") is not True:
        raise ValueError("R13 validation must be body-free")
    release_boundary = safe_mapping(data.get("release_boundary"))
    for key in ("release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if release_boundary.get(key) is not False:
            raise ValueError(f"R13 release boundary must keep {key}=False")
    if safe_mapping(data.get("p5_return_status")).get("human_blind_qa_confirmed") is not False:
        raise ValueError("R13 must not confirm P5 human Blind QA")
    if safe_mapping(data.get("p6_return_status")).get("human_readfeel_confirmed") is not False:
        raise ValueError("R13 must not confirm P6 human readfeel")
    unresolved = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120))
    required = {
        P5_HUMAN_BLIND_QA_HOLD_REF,
        P5_HUMAN_BLIND_QA_RETURN_HOLD_REF,
        P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
        P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF,
        P7_HOLD_FULL_BACKEND_SUITE_REF,
        HOLD_DC_FULL_BACKEND_SUITE_REF,
    }
    if required - unresolved:
        raise ValueError("R13 must preserve unresolved P5/P6/full-backend HOLD refs")
    if safe_mapping(data.get("real_device_modal_status")).get("confirmed") is not True:
        if P7_RETURN_REAL_DEVICE_HOLD_REF not in unresolved:
            raise ValueError("R13 must preserve real-device return HOLD while modal review is unconfirmed")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r46_closed_validation.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r46_closed_validation.body_free_markers")
    _assert_body_free_input(data, source="p7_r46_closed_validation")
    return True


def assert_real_device_and_closed_validation_summary_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    if data.get("schema_version") != P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected R12/R13 summary schema_version")
    if data.get("current_phase") != "P7":
        raise ValueError("R12/R13 summary must keep current phase as P7")
    for key in ("release_allowed", "p7_complete", "p8_start_allowed", "hold004_close_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"R12/R13 summary must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R12/R13 summary must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r46_r12_r13_summary.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r46_r12_r13_summary.body_free_markers")
    _assert_body_free_input(data, source="p7_r46_r12_r13_summary")
    return True


__all__ = [
    "HOLD_DC_FULL_BACKEND_SUITE_REF",
    "P7_HOLD_FULL_BACKEND_SUITE_REF",
    "P7_HOLD_REAL_DEVICE_MODAL_REF",
    "P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION",
    "P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION",
    "P7_R46_REAL_DEVICE_CLOSED_VALIDATION_STEP",
    "P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION",
    "P7_RETURN_REAL_DEVICE_HOLD_REF",
    "assert_p7_hold_release_p8_closed_validation_contract",
    "assert_real_device_and_closed_validation_summary_contract",
    "assert_real_device_submit_modal_readfeel_checklist_contract",
    "build_p7_hold_release_p8_closed_validation",
    "build_real_device_and_closed_validation_summary",
    "build_real_device_submit_modal_readfeel_checklist",
]
