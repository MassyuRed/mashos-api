# -*- coding: utf-8 -*-
from __future__ import annotations

"""P7-HOLD-004 positive public fixture shape boundary material.

This module tracks the body-free state of the P7-HOLD-004 positive public shape
boundary from R0/R1 classification through the R6 target-green handoff.  It
stores only identifiers, statuses, booleans, and reason codes.  It must never
carry raw input, candidate bodies, public comment bodies, completed surface
bodies, reviewer free text, or terminal output.
"""

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

P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7.hold004.positive_public_shape_boundary.v1"
)
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_STEP: Final = "P7-HOLD-004_PositivePublicShapeBoundary_R0_R1_20260614"
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIR_STEP: Final = (
    "P7-HOLD-004_PositivePublicShapeBoundary_R2_R6_20260614"
)
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS: Final = "REPAIRED_TARGET_GREEN_PENDING_FULL_SUITE"
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_HOLD_ID: Final = "P7-HOLD-004"
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_BOUNDARY_ID: Final = "p7_hold004_positive_public_shape_boundary_20260614"
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_PATH_ID: Final = "emotion_submit_public_product_visible_fixture_suite"
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_FIXTURE_FAMILY: Final = "positive_change_after_work_streaming"
P7_HOLD004_POSITIVE_PUBLIC_SHAPE_CLASSIFICATION: Final = (
    "safety_triage_expression_difficulty_false_positive_to_self_denial_safe_state"
)

_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "CLASSIFIED_UNRESOLVED",
        "IMPLEMENTATION_REPAIR_REQUIRED",
        P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS,
    }
)
_ALLOWED_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {P7_HOLD004_POSITIVE_PUBLIC_SHAPE_CLASSIFICATION}
)
_ALLOWED_OWNER_LAYERS: Final[frozenset[str]] = frozenset(
    {
        "safety_triage_expression_difficulty_boundary",
        "input_material_bundle_safety_quality_boundary",
        "public_surface_requirement_boundary",
        "emotion_submit_public_two_stage_path",
    }
)
_ALLOWED_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        "positive_public_fixture_labelled_two_stage_mismatch",
        "expression_difficulty_not_identity_denial",
        "self_denial_safe_state_false_positive_candidate",
        "public_feedback_present_wrong_family_wrong_shape",
        "target_test_added_pending_runtime_repair",
        "safety_triage_false_positive_boundary_repaired",
        "input_material_bundle_not_safety_triage_required",
        "positive_public_e2e_labelled_two_stage_restored",
        "true_self_denial_regression_preserved",
        "emergency_safety_regression_preserved",
        "support_required_regression_preserved",
        "target_green_confirmed_pending_full_suite",
    }
)
_ALWAYS_FALSE_KEYS: Final[tuple[str, ...]] = (
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claim_allowed",
    "hold004_close_allowed",
    "p7_complete_claim_allowed",
    "p8_start_allowed",
    "release_allowed",
)
_PROGRESS_KEYS: Final[tuple[str, ...]] = (
    "runtime_repair_applied",
    "target_green_confirmed",
    "true_self_denial_regression_preserved",
    "emergency_safety_regression_preserved",
    "support_required_regression_preserved",
    "r2_runtime_repair_applied",
    "r3_input_material_bundle_not_safety_triage_required",
    "r4_public_e2e_labelled_two_stage_confirmed",
    "r5_safety_regression_preserved",
)


def _clean_status(value: Any) -> str:
    status = clean_identifier(value, default="CLASSIFIED_UNRESOLVED", max_length=120)
    return status if status in _ALLOWED_STATUSES else "CLASSIFIED_UNRESOLVED"


def _default_reason_codes(status: str) -> tuple[str, ...]:
    if status == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS:
        return (
            "safety_triage_false_positive_boundary_repaired",
            "input_material_bundle_not_safety_triage_required",
            "positive_public_e2e_labelled_two_stage_restored",
            "true_self_denial_regression_preserved",
            "emergency_safety_regression_preserved",
            "support_required_regression_preserved",
            "target_green_confirmed_pending_full_suite",
        )
    return (
        "positive_public_fixture_labelled_two_stage_mismatch",
        "expression_difficulty_not_identity_denial",
        "self_denial_safe_state_false_positive_candidate",
        "public_feedback_present_wrong_family_wrong_shape",
        "target_test_added_pending_runtime_repair",
    )


def _reason_codes(status: str, values: Sequence[Any] | Any | None = None) -> list[str]:
    codes = dedupe_identifiers(values or _default_reason_codes(status), limit=40, max_length=160)
    return [code for code in codes if code in _ALLOWED_REASON_CODES]


def _public_contract_flags() -> dict[str, bool]:
    flags = public_contract_flags()
    flags.update(
        {
            "api_route_changed": False,
            "request_key_changed": False,
            "public_response_key_added": False,
            "response_shape_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "gate_relaxed": False,
            "fixed_sentence_template_added": False,
            "runtime_fixture_branch_added": False,
        }
    )
    return flags


def build_p7_hold004_positive_public_shape_boundary_classification(
    *,
    status: Any = "CLASSIFIED_UNRESOLVED",
    reason_codes: Sequence[Any] | Any | None = None,
    runtime_repair_applied: bool | None = None,
    target_green_confirmed: bool = False,
    true_self_denial_regression_preserved: bool = False,
    emergency_safety_regression_preserved: bool = False,
    support_required_regression_preserved: bool = False,
    r3_input_material_bundle_not_safety_triage_required: bool = False,
    r4_public_e2e_labelled_two_stage_confirmed: bool = False,
    full_backend_suite_green_confirmed: bool = False,
) -> dict[str, Any]:
    """Build the body-free classification/progress material for this boundary."""

    cleaned_status = _clean_status(status)
    repaired_status = cleaned_status == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS
    runtime_repair = repaired_status if runtime_repair_applied is None else bool(runtime_repair_applied)
    r3_confirmed = bool(r3_input_material_bundle_not_safety_triage_required or target_green_confirmed)
    r4_confirmed = bool(r4_public_e2e_labelled_two_stage_confirmed or target_green_confirmed)
    r5_preserved = (
        bool(true_self_denial_regression_preserved)
        and bool(emergency_safety_regression_preserved)
        and bool(support_required_regression_preserved)
    )

    material = {
        "schema_version": P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIR_STEP if repaired_status else P7_HOLD004_POSITIVE_PUBLIC_SHAPE_STEP,
        "hold_id": P7_HOLD004_POSITIVE_PUBLIC_SHAPE_HOLD_ID,
        "boundary_id": P7_HOLD004_POSITIVE_PUBLIC_SHAPE_BOUNDARY_ID,
        "status": cleaned_status,
        "classification": P7_HOLD004_POSITIVE_PUBLIC_SHAPE_CLASSIFICATION,
        "target_path_id": P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_PATH_ID,
        "target_fixture_family": P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_FIXTURE_FAMILY,
        "owner_layers": [
            "safety_triage_expression_difficulty_boundary",
            "input_material_bundle_safety_quality_boundary",
            "public_surface_requirement_boundary",
            "emotion_submit_public_two_stage_path",
        ],
        "observed_before_repair": {
            "public_reached": True,
            "labelled_two_stage_reached": False,
            "safety_triage_kind": "self_denial_safe_state_answer",
            "response_kind": "self_denial_safe_state_answer",
            "candidate_source_kind": "self_denial_safe_state_answer",
            "surface_requirement_family": "safety_blocked",
            "two_stage_required": False,
        },
        "expected_after_repair": {
            "public_reached": True,
            "labelled_two_stage_reached": True,
            "safety_triage_kind": "safe_observation",
            "response_kind": "normal_observation",
            "self_denial_safe_state_answer_candidate_used": False,
        },
        "reason_codes": _reason_codes(cleaned_status, reason_codes),
        "false_positive_category": "expression_difficulty_not_self_denial",
        "r0_current_red_classified": True,
        "r1_target_test_added": True,
        "runtime_repair_applied": runtime_repair,
        "r2_runtime_repair_applied": runtime_repair,
        "r3_input_material_bundle_not_safety_triage_required": r3_confirmed,
        "r4_public_e2e_labelled_two_stage_confirmed": r4_confirmed,
        "r5_safety_regression_preserved": r5_preserved,
        "target_green_confirmed": bool(target_green_confirmed),
        "true_self_denial_regression_preserved": bool(true_self_denial_regression_preserved),
        "emergency_safety_regression_preserved": bool(emergency_safety_regression_preserved),
        "support_required_regression_preserved": bool(support_required_regression_preserved),
        "full_backend_suite_green_confirmed": bool(full_backend_suite_green_confirmed),
        "full_backend_suite_green_claim_allowed": False,
        "hold004_close_allowed": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_POSITIVE_PUBLIC_SHAPE_HOLD_ID],
        "body_free": True,
        "public_contract": _public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_hold004_positive_public_shape_boundary_contract(material)
    return material


def build_p7_hold004_positive_public_shape_boundary_repaired_material() -> dict[str, Any]:
    """Return the R6 target-green material without closing P7-HOLD-004."""

    return build_p7_hold004_positive_public_shape_boundary_classification(
        status=P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS,
        runtime_repair_applied=True,
        target_green_confirmed=True,
        true_self_denial_regression_preserved=True,
        emergency_safety_regression_preserved=True,
        support_required_regression_preserved=True,
        r3_input_material_bundle_not_safety_triage_required=True,
        r4_public_e2e_labelled_two_stage_confirmed=True,
        full_backend_suite_green_confirmed=False,
    )


def assert_p7_hold004_positive_public_shape_boundary_contract(material: Mapping[str, Any]) -> bool:
    """Validate that the material is body-free, release-closed, and non-promoting."""

    data = safe_mapping(material)
    if data.get("schema_version") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION:
        raise ValueError("unexpected P7-HOLD-004 positive public shape schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 phase for positive public shape boundary")
    if data.get("hold_id") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_HOLD_ID:
        raise ValueError("positive public shape boundary must stay under P7-HOLD-004")
    if data.get("boundary_id") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_BOUNDARY_ID:
        raise ValueError("positive public shape boundary_id mismatch")
    status = data.get("status")
    if status not in _ALLOWED_STATUSES:
        raise ValueError("unsupported positive public shape boundary status")
    if data.get("classification") not in _ALLOWED_CLASSIFICATIONS:
        raise ValueError("unsupported positive public shape boundary classification")
    if data.get("target_path_id") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_PATH_ID:
        raise ValueError("positive public shape boundary target_path_id mismatch")
    if data.get("target_fixture_family") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_FIXTURE_FAMILY:
        raise ValueError("positive public shape boundary target_fixture_family mismatch")
    owner_layers = set(dedupe_identifiers(data.get("owner_layers"), limit=20, max_length=160))
    if not owner_layers or not owner_layers.issubset(_ALLOWED_OWNER_LAYERS):
        raise ValueError("positive public shape boundary owner_layers must be known body-free owner identifiers")
    before = safe_mapping(data.get("observed_before_repair"))
    after = safe_mapping(data.get("expected_after_repair"))
    if before.get("public_reached") is not True or before.get("labelled_two_stage_reached") is not False:
        raise ValueError("positive public shape boundary must freeze the current public/unlabelled red")
    if before.get("safety_triage_kind") != "self_denial_safe_state_answer":
        raise ValueError("positive public shape boundary must preserve the observed self-denial triage lane")
    if after.get("safety_triage_kind") != "safe_observation" or after.get("response_kind") != "normal_observation":
        raise ValueError("positive public shape boundary expected repair must point back to normal observation")
    for key in _ALWAYS_FALSE_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"positive public shape boundary must keep {key}=False")
    repaired_status = status == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS
    progress_values = {key: data.get(key) is True for key in _PROGRESS_KEYS}
    if repaired_status:
        if not all(progress_values.values()):
            missing = [key for key, value in progress_values.items() if not value]
            raise ValueError(f"repaired positive public shape material is missing target-green progress flags: {missing}")
        if data.get("step") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIR_STEP:
            raise ValueError("repaired positive public shape material must use the R2/R6 step identifier")
    else:
        if any(progress_values.values()):
            raised = [key for key, value in progress_values.items() if value]
            raise ValueError(f"unrepaired positive public shape material must not claim progress flags: {raised}")
        if data.get("step") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_STEP:
            raise ValueError("unrepaired positive public shape material must use the R0/R1 step identifier")
    if data.get("target_green_confirmed") is True and not repaired_status:
        raise ValueError("target_green_confirmed requires REPAIRED_TARGET_GREEN_PENDING_FULL_SUITE status")
    if data.get("full_backend_suite_green_confirmed") is True:
        raise ValueError("positive public shape material must not claim full backend suite green")
    if P7_HOLD004_POSITIVE_PUBLIC_SHAPE_HOLD_ID not in dedupe_identifiers(
        data.get("unresolved_hold_refs"), limit=20, max_length=120
    ):
        raise ValueError("positive public shape boundary must keep P7-HOLD-004 unresolved")
    if data.get("body_free") is not True:
        raise ValueError("positive public shape boundary material must be body-free")
    if not _reason_codes(status, data.get("reason_codes")):
        raise ValueError("positive public shape boundary requires known body-free reason codes")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_hold004_positive_public_shape.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_hold004_positive_public_shape.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_hold004_positive_public_shape")
    return True


__all__ = [
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_BOUNDARY_ID",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_CLASSIFICATION",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_HOLD_ID",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIR_STEP",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_STEP",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_FIXTURE_FAMILY",
    "P7_HOLD004_POSITIVE_PUBLIC_SHAPE_TARGET_PATH_ID",
    "assert_p7_hold004_positive_public_shape_boundary_contract",
    "build_p7_hold004_positive_public_shape_boundary_classification",
    "build_p7_hold004_positive_public_shape_boundary_repaired_material",
]
