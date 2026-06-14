# -*- coding: utf-8 -*-
"""P7 R10 manual HOLD matrix for real-device and full-suite checks.

R10 keeps the checks that cannot be closed by subset pytest green outside the
P7 core completion claim.  The material is body-free: it records check ids,
statuses, refs, booleans, and counts only.  It never serializes raw input,
comment text bodies, candidate bodies, surface bodies, reviewer text, or
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
from emlis_ai_p7_hold004_phase16_composer_classification import (
    P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_HOLD_ID,
    assert_p7_hold004_phase16_composer_classification_contract,
)
from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION,
    assert_p7_hold004_phase16_decision_rule_contract,
    assert_p7_hold004_phase16_path_matrix_contract,
    assert_p7_hold004_phase16_public_adjacent_red_registration_contract,
)

from emlis_ai_p7_hold004_positive_public_shape_boundary import (
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS,
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION,
    assert_p7_hold004_positive_public_shape_boundary_contract,
)
from emlis_ai_p7_hold004_step5_candidate_gate_classification import (
    P7_HOLD004_STEP5_HOLD_ID,
    P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION,
    P7_HOLD004_STEP5_RED_ID,
    assert_p7_hold004_step5_meta_extension_contract,
    assert_p7_hold004_step5_material_connection_contract,
)

P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION: Final = "cocolon.emlis.p7.real_device_modal_readfeel_check.v1"
P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.backend_suite_split_matrix.v1"
P7_R10_HOLD_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.r10_hold_matrix.v1"
P7_HOLD_MATRIX_SCHEMA_VERSION: Final = P7_R10_HOLD_MATRIX_SCHEMA_VERSION
P7_R10_HOLD_MATRIX_STEP: Final = "P7-R10_RealDeviceFullBackendHoldMatrix_20260613"
P7_R10_HOLD_MATRIX_SCOPE: Final = "P7_real_device_submit_full_backend_suite_hold_matrix"

P7_REAL_DEVICE_CHECK_ID: Final = "p7_real_device_submit_modal_readfeel_20260613"
P7_BACKEND_SUITE_MATRIX_ID: Final = "p7_backend_suite_split_matrix_20260613"

_REAL_DEVICE_CHECKS: Final[tuple[str, ...]] = (
    "emotion_submit_reaches_public_feedback",
    "emlis_modal_title_preserved",
    "comment_text_readable_length",
    "modal_pressure_not_too_high",
    "reinput_motivation_human_readfeel",
)
_ALLOWED_CHECK_STATUSES: Final[frozenset[str]] = frozenset({"not_verified", "verified", "partial", "blocked"})
_ALLOWED_REAL_DEVICE_STATUSES: Final[frozenset[str]] = frozenset({"not_verified", "verified", "partial", "blocked"})
_ALLOWED_BACKEND_GROUP_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "green_confirmed",
        "closed_confirmed",
        "timeout_or_unconfirmed",
        "timeout_isolated",
        "red_until_repaired",
        "not_run",
        "hold_unconfirmed",
        "blocked",
    }
)
_ALLOWED_BACKEND_GROUP_IDS: Final[tuple[str, ...]] = (
    "p7_core",
    "product_quality_reuse_subset",
    "positive_recovery_e2e",
    "product_quality_connection_e2e",
    "real_device_submit_modal_readfeel",
    "full_backend_suite",
)


def _result_kind(observed_results: Mapping[str, Any] | None, key: str) -> str:
    source = safe_mapping(observed_results)
    value = source.get(key)
    if isinstance(value, bool):
        return "passed" if value else "failed"
    if isinstance(value, str):
        return clean_identifier(value, default="not_run", max_length=80)
    data = safe_mapping(value)
    if data.get("passed") is True:
        return "passed"
    return clean_identifier(data.get("result_kind") or data.get("status"), default="not_run", max_length=80)


def _test_count(observed_results: Mapping[str, Any] | None, key: str, default: int = 0) -> int:
    data = safe_mapping(safe_mapping(observed_results).get(key))
    value = data.get("test_count_observed") or data.get("test_count") or data.get("count") or default
    try:
        if value is None or value == "" or isinstance(value, bool):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _group(
    group_id: str,
    *,
    status: str,
    green_scope: str,
    green_claim_allowed: bool,
    release_blocking: bool,
    test_count_observed: int = 0,
    red_refs: Sequence[Any] = (),
    hold_refs: Sequence[Any] = (),
    reason_codes: Sequence[Any] = (),
) -> dict[str, Any]:
    return {
        "group_id": clean_identifier(group_id, max_length=120),
        "status": clean_identifier(status, default="not_run", max_length=80),
        "green_scope": clean_identifier(green_scope, default="group_only", max_length=120),
        "green_claim_allowed": green_claim_allowed is True,
        "release_blocking": release_blocking is True,
        "test_count_observed": int(test_count_observed),
        "red_refs": dedupe_identifiers(red_refs, limit=40, max_length=120),
        "hold_refs": dedupe_identifiers(hold_refs, limit=40, max_length=120),
        "reason_codes": dedupe_identifiers(reason_codes, limit=80, max_length=160),
        "can_claim_full_backend_suite_green": False,
        "release_allowed": False,
        "body_free": True,
    }


def _green_or_not_run(kind: str) -> str:
    return "green_confirmed" if kind in {"passed", "green", "green_confirmed"} else "not_run"


def _positive_status(kind: str, *, positive_recovery_red_closed: bool) -> str:
    if positive_recovery_red_closed or kind in {"passed", "green", "closed", "closed_confirmed", "closed_by_r0_r5_positive_recovery_suite"}:
        return "closed_confirmed"
    if kind in {"failed", "red", "red_until_repaired", "2_failed", "failed_preserved"}:
        return "red_until_repaired"
    return "red_until_repaired"


def _connection_status(kind: str) -> str:
    if kind in {"timeout", "timeout_preserved", "timeout_isolated", "hang", "hang_preserved", "red_preserved"}:
        return "timeout_isolated"
    if kind in {"passed", "green"}:
        return "blocked"
    if kind == "not_run":
        return "timeout_or_unconfirmed"
    return "timeout_or_unconfirmed"


def _hold004_phase16_material_summary(
    *,
    hold004_phase16_classification: Mapping[str, Any] | None = None,
    hold004_path_matrix: Mapping[str, Any] | None = None,
    hold004_decision_rule: Mapping[str, Any] | None = None,
    hold004_adjacent_public_red_registration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize optional P7-HOLD-004 Phase16 material for P7 matrix handoff.

    R7 may connect the classified Phase16 red to the existing P7 HOLD,
    validation, and release-handoff layers.  This helper keeps that connection
    body-free and keeps P7-HOLD-004 unresolved; it never turns classified
    material into full backend-suite green.
    """

    classification = safe_mapping(hold004_phase16_classification)
    if hold004_phase16_classification is not None:
        assert_p7_hold004_phase16_composer_classification_contract(classification)
        assert_p7_no_body_payload_or_contract_mutation(
            classification,
            source="p7_hold004_phase16_material.classification",
        )

    path_matrix = safe_mapping(hold004_path_matrix)
    if hold004_path_matrix is not None:
        assert_p7_hold004_phase16_path_matrix_contract(path_matrix)
        assert_p7_no_body_payload_or_contract_mutation(
            path_matrix,
            source="p7_hold004_phase16_material.path_matrix",
        )

    decision_rule = safe_mapping(hold004_decision_rule)
    if hold004_decision_rule is not None:
        assert_p7_hold004_phase16_decision_rule_contract(decision_rule)
        assert_p7_no_body_payload_or_contract_mutation(
            decision_rule,
            source="p7_hold004_phase16_material.decision_rule",
        )

    adjacent_registration = safe_mapping(hold004_adjacent_public_red_registration)
    if hold004_adjacent_public_red_registration is not None:
        assert_p7_hold004_phase16_public_adjacent_red_registration_contract(adjacent_registration)
        assert_p7_no_body_payload_or_contract_mutation(
            adjacent_registration,
            source="p7_hold004_phase16_material.adjacent_registration",
        )

    classified_red_present = bool(classification or path_matrix or decision_rule or adjacent_registration)
    required_followup_fixes = dedupe_identifiers(
        [
            *classification.get("required_followup_fixes", []),
            *path_matrix.get("required_followup_fixes", []),
            *decision_rule.get("required_followup_fixes", []),
            *adjacent_registration.get("required_followup_fixes", []),
        ],
        limit=80,
        max_length=160,
    )
    candidate_boundary_registered = bool(
        "phase16_complete_composer_candidate_boundary" in required_followup_fixes
        or decision_rule.get("repair_branch") == "R4-A"
        or classification.get("direct_or_conversation_unavailable") is True
        or path_matrix.get("direct_or_conversation_unavailable") is True
    )
    adjacent_public_red_registered = bool(
        "positive_public_fixture_shape_boundary" in required_followup_fixes
        or path_matrix.get("adjacent_public_red_registered") is True
        or adjacent_registration.get("adjacent_public_red_registered") is True
    )
    if classified_red_present and not required_followup_fixes:
        required_followup_fixes = ["phase16_complete_composer_candidate_boundary"]

    return {
        "classified_red_present": classified_red_present,
        "classification_schema_version": clean_identifier(
            classification.get("schema_version"),
            default=P7_HOLD004_PHASE16_COMPOSER_CLASSIFICATION_SCHEMA_VERSION if classification else "",
            max_length=160,
        ),
        "path_matrix_schema_version": clean_identifier(
            path_matrix.get("schema_version"),
            default=P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION if path_matrix else "",
            max_length=160,
        ),
        "decision_rule_schema_version": clean_identifier(
            decision_rule.get("schema_version"),
            default=P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION if decision_rule else "",
            max_length=160,
        ),
        "adjacent_registration_schema_version": clean_identifier(
            adjacent_registration.get("schema_version"),
            default=(
                P7_HOLD004_PHASE16_PUBLIC_ADJACENT_RED_REGISTRATION_SCHEMA_VERSION
                if adjacent_registration
                else ""
            ),
            max_length=160,
        ),
        "classification_status": clean_identifier(
            decision_rule.get("status") or classification.get("status"),
            default="not_connected",
            max_length=120,
        ),
        "decision_kind": clean_identifier(decision_rule.get("decision_kind"), default="not_connected", max_length=160),
        "repair_branch": clean_identifier(decision_rule.get("repair_branch"), default="none", max_length=80),
        "candidate_boundary_registered": candidate_boundary_registered,
        "public_adjacent_red_registered": adjacent_public_red_registered,
        "required_followup_fixes": required_followup_fixes,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID] if classified_red_present else [],
        "release_allowed": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "body_free": True,
    }



def _hold004_positive_public_shape_material_summary(
    hold004_positive_public_shape_boundary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize the R6 positive public shape target-green material.

    This is a body-free handoff summary only.  It can show that the local target
    boundary is green, but it must not close P7-HOLD-004, claim full backend
    suite green, or allow release/P8.
    """

    material = safe_mapping(hold004_positive_public_shape_boundary)
    if hold004_positive_public_shape_boundary is not None:
        assert_p7_hold004_positive_public_shape_boundary_contract(material)
        assert_p7_no_body_payload_or_contract_mutation(
            material,
            source="p7_hold004_positive_public_shape.material",
        )

    connected = bool(material)
    status = clean_identifier(material.get("status"), default="not_connected", max_length=120)
    target_green = material.get("target_green_confirmed") is True
    repaired_pending_full_suite = bool(
        connected
        and status == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS
        and target_green
    )
    return {
        "connected": connected,
        "schema_version": clean_identifier(
            material.get("schema_version"),
            default=P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION if connected else "",
            max_length=160,
        ),
        "status": status,
        "target_green_confirmed": target_green,
        "repaired_target_green_pending_full_suite": repaired_pending_full_suite,
        "true_self_denial_regression_preserved": material.get("true_self_denial_regression_preserved") is True,
        "emergency_safety_regression_preserved": material.get("emergency_safety_regression_preserved") is True,
        "support_required_regression_preserved": material.get("support_required_regression_preserved") is True,
        "r3_input_material_bundle_not_safety_triage_required": (
            material.get("r3_input_material_bundle_not_safety_triage_required") is True
        ),
        "r4_public_e2e_labelled_two_stage_confirmed": (
            material.get("r4_public_e2e_labelled_two_stage_confirmed") is True
        ),
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "unresolved_hold_refs": [P7_HOLD004_PHASE16_HOLD_ID] if connected else [],
        "reason_codes": dedupe_identifiers(material.get("reason_codes"), limit=80, max_length=160),
        "body_free": True,
    }


def _hold004_step5_material_summary(
    *,
    hold004_step5_meta_extension: Mapping[str, Any] | None = None,
    hold004_step5_material_connection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize R5/R6 Step5 material for P7-HOLD-004 handoff layers.

    The connection is body-free and deliberately keeps P7-HOLD-004 unresolved.
    It can make the Step5 display-binding material visible to backend split,
    R10 HOLD matrix, validation matrix, and release handoff without claiming
    full backend-suite green.
    """

    r5 = safe_mapping(hold004_step5_meta_extension)
    if hold004_step5_meta_extension is not None:
        assert_p7_hold004_step5_meta_extension_contract(r5)
        assert_p7_no_body_payload_or_contract_mutation(r5, source="p7_hold004_step5_material.r5")

    r6 = safe_mapping(hold004_step5_material_connection)
    if hold004_step5_material_connection is not None:
        assert_p7_hold004_step5_material_connection_contract(r6)
        assert_p7_no_body_payload_or_contract_mutation(r6, source="p7_hold004_step5_material.r6")

    connected = bool(r5 or r6)
    step5_red_closed = bool(
        r6.get("step5_candidate_gate_red_closed") is True
        or r6.get("step5_candidate_gate_red_closed_by_r4c") is True
    )
    step5_red_present = bool(
        r6.get("step5_display_binding_red_present") is True
        or r5.get("display_binding_missing_without_exception") is True
        or P7_HOLD004_STEP5_RED_ID in dedupe_identifiers(r6.get("unresolved_red_refs"), limit=40, max_length=160)
        or P7_HOLD004_STEP5_RED_ID in dedupe_identifiers(r6.get("closed_red_refs"), limit=40, max_length=160)
    )
    required_followup_fixes = dedupe_identifiers(
        [
            *r5.get("required_followup_fixes", []),
            *r6.get("required_followup_fixes", []),
            "step5_display_binding_contract_consistency" if connected else "",
        ],
        limit=80,
        max_length=160,
    )
    unresolved_red_refs = [] if step5_red_closed else dedupe_identifiers(
        [
            *r5.get("unresolved_red_refs", []),
            *r6.get("unresolved_red_refs", []),
            P7_HOLD004_STEP5_RED_ID if step5_red_present else "",
        ],
        limit=40,
        max_length=160,
    )
    closed_red_refs = dedupe_identifiers(
        [*r6.get("closed_red_refs", []), P7_HOLD004_STEP5_RED_ID if step5_red_closed else ""],
        limit=40,
        max_length=160,
    )
    return {
        "connected": connected,
        "meta_extension_schema_version": clean_identifier(
            r5.get("schema_version") or r6.get("source_r5_meta_extension_schema_version"),
            default=P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION if (r5 or r6) else "",
            max_length=160,
        ),
        "material_connection_schema_version": clean_identifier(
            r6.get("schema_version"),
            default=P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION if r6 else "",
            max_length=160,
        ),
        "material_connection_status": clean_identifier(r6.get("status"), default="not_connected", max_length=120),
        "step5_contract_classification": clean_identifier(
            r6.get("step5_contract_classification") or r5.get("classification") or r5.get("step5_contract_classification"),
            default="not_connected",
            max_length=160,
        ),
        "step5_display_binding_red_present": step5_red_present,
        "step5_candidate_gate_red_classified": bool(r6.get("step5_candidate_gate_red_classified") is True or connected),
        "step5_candidate_gate_red_closed": step5_red_closed,
        "step5_mixed_contract_conflict_held": bool(r6.get("step5_mixed_contract_conflict_held") is True),
        "release_blocker": bool(r6.get("release_blocker") is True or connected),
        "required_followup_fixes": required_followup_fixes,
        "unresolved_hold_refs": [P7_HOLD004_STEP5_HOLD_ID] if connected else [],
        "unresolved_red_refs": unresolved_red_refs,
        "closed_red_refs": closed_red_refs,
        "full_backend_suite_green_confirmed": False,
        "hold004_close_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "body_free": True,
    }


def build_p7_real_device_modal_readfeel_check(
    *,
    check_statuses: Mapping[str, Any] | None = None,
    check_id: Any = P7_REAL_DEVICE_CHECK_ID,
) -> dict[str, Any]:
    """Build body-free material for the real-device submit/modal read-feel HOLD.

    P7 cannot close this check with backend or RN unit tests.  A verified status
    may be recorded later, but this material still does not apply release.
    """

    source = safe_mapping(check_statuses)
    if check_statuses is not None:
        assert_p7_no_body_payload_or_contract_mutation(source, source="p7_real_device_modal_readfeel_check.input")
    checks: dict[str, str] = {}
    for check_name in _REAL_DEVICE_CHECKS:
        status = clean_identifier(source.get(check_name), default="not_verified", max_length=80)
        if status not in _ALLOWED_CHECK_STATUSES:
            status = "not_verified"
        checks[check_name] = status
    verified_count = sum(1 for status in checks.values() if status == "verified")
    blocked_count = sum(1 for status in checks.values() if status == "blocked")
    if verified_count == len(_REAL_DEVICE_CHECKS):
        status = "verified"
    elif blocked_count:
        status = "blocked"
    elif verified_count:
        status = "partial"
    else:
        status = "not_verified"
    hold_refs = [] if status == "verified" else ["P7-HOLD-003"]
    result = {
        "schema_version": P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R10_HOLD_MATRIX_STEP,
        "scope": "P7_real_device_submit_modal_readfeel_check",
        "check_id": clean_identifier(check_id, default=P7_REAL_DEVICE_CHECK_ID, max_length=120),
        "status": status,
        "platforms_required": ["ios_or_android_real_device"],
        "checks": checks,
        "verified_check_count": verified_count,
        "required_check_count": len(_REAL_DEVICE_CHECKS),
        "real_device_submit_confirmed": status == "verified",
        "manual_real_device_check_required": status != "verified",
        "automated_test_green_can_close": False,
        "hold_refs": hold_refs,
        "release_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=False, include_reviewer=True),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
    }
    assert_p7_real_device_modal_readfeel_check_contract(result)
    return result


def assert_p7_real_device_modal_readfeel_check_contract(check: Mapping[str, Any]) -> bool:
    data = safe_mapping(check)
    if data.get("schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("unexpected P7 real-device check schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 real-device check phase")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 real-device check must stay body-free and release-closed")
    status = clean_identifier(data.get("status"), default="", max_length=80)
    if status not in _ALLOWED_REAL_DEVICE_STATUSES:
        raise ValueError("P7 real-device check status changed")
    checks = safe_mapping(data.get("checks"))
    if set(checks) != set(_REAL_DEVICE_CHECKS):
        raise ValueError("P7 real-device check must keep the fixed checklist")
    if any(clean_identifier(value, max_length=80) not in _ALLOWED_CHECK_STATUSES for value in checks.values()):
        raise ValueError("P7 real-device checklist has unsupported status")
    if data.get("automated_test_green_can_close") is not False:
        raise ValueError("P7 real-device HOLD must not close via automated test green")
    if status != "verified" and "P7-HOLD-003" not in dedupe_identifiers(data.get("hold_refs"), limit=20):
        raise ValueError("P7-HOLD-003 must remain while real-device submit/modal read-feel is unverified")
    if data.get("real_device_submit_confirmed") is True and status != "verified":
        raise ValueError("real_device_submit_confirmed requires verified status")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_real_device_check.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_real_device_check.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_real_device_check")
    return True


def build_p7_backend_suite_split_matrix(
    *,
    observed_results: Mapping[str, Any] | None = None,
    real_device_check: Mapping[str, Any] | None = None,
    positive_recovery_red_closed: bool = True,
    hold004_phase16_classification: Mapping[str, Any] | None = None,
    hold004_path_matrix: Mapping[str, Any] | None = None,
    hold004_decision_rule: Mapping[str, Any] | None = None,
    hold004_adjacent_public_red_registration: Mapping[str, Any] | None = None,
    hold004_positive_public_shape_boundary: Mapping[str, Any] | None = None,
    hold004_step5_meta_extension: Mapping[str, Any] | None = None,
    hold004_step5_material_connection: Mapping[str, Any] | None = None,
    matrix_id: Any = P7_BACKEND_SUITE_MATRIX_ID,
) -> dict[str, Any]:
    """Build the body-free split matrix for P7 backend/full-suite HOLDs."""

    if observed_results is not None:
        assert_p7_no_body_payload_or_contract_mutation(observed_results, source="p7_backend_suite_split_matrix.observed_results")
    real_device = safe_mapping(real_device_check) if real_device_check is not None else build_p7_real_device_modal_readfeel_check()
    assert_p7_real_device_modal_readfeel_check_contract(real_device)

    p7_core_kind = _result_kind(observed_results, "p7_core_contract")
    reuse_kind = _result_kind(observed_results, "existing_p7_reuse_contract")
    positive_kind = _result_kind(observed_results, "heavy_isolated_positive_recovery_red")
    connection_kind = _result_kind(observed_results, "heavy_isolated_product_quality_connection_timeout")
    full_kind = _result_kind(observed_results, "full_backend_suite")
    hold004_material = _hold004_phase16_material_summary(
        hold004_phase16_classification=hold004_phase16_classification,
        hold004_path_matrix=hold004_path_matrix,
        hold004_decision_rule=hold004_decision_rule,
        hold004_adjacent_public_red_registration=hold004_adjacent_public_red_registration,
    )
    hold004_positive_material = _hold004_positive_public_shape_material_summary(
        hold004_positive_public_shape_boundary
    )
    hold004_step5_material = _hold004_step5_material_summary(
        hold004_step5_meta_extension=hold004_step5_meta_extension,
        hold004_step5_material_connection=hold004_step5_material_connection,
    )

    p7_core_status = _green_or_not_run(p7_core_kind)
    reuse_status = _green_or_not_run(reuse_kind)
    positive_status = _positive_status(positive_kind, positive_recovery_red_closed=positive_recovery_red_closed)
    connection_status = _connection_status(connection_kind)
    full_suite_status = "not_run" if full_kind in {"not_run", "unconfirmed", "timeout", "hang"} else "hold_unconfirmed"
    real_device_status = "green_confirmed" if real_device.get("status") == "verified" else "hold_unconfirmed"

    full_suite_reason_codes = dedupe_identifiers(
        [
            "full_backend_suite_green_unconfirmed",
            "p7_hold004_phase16_classified_red_present"
            if hold004_material["classified_red_present"]
            else "",
            *hold004_material["required_followup_fixes"],
            "p7_hold004_step5_display_binding_red_present"
            if hold004_step5_material["step5_display_binding_red_present"]
            else "",
            *hold004_step5_material["required_followup_fixes"],
            "positive_public_shape_target_green_pending_full_suite"
            if hold004_positive_material["target_green_confirmed"]
            else "",
        ],
        limit=80,
        max_length=160,
    )

    groups = [
        _group(
            "p7_core",
            status=p7_core_status,
            green_scope="group_only",
            green_claim_allowed=p7_core_status == "green_confirmed",
            release_blocking=False,
            test_count_observed=_test_count(observed_results, "p7_core_contract", 0),
            reason_codes=("p7_core_green_is_group_only",),
        ),
        _group(
            "product_quality_reuse_subset",
            status=reuse_status,
            green_scope="group_only",
            green_claim_allowed=reuse_status == "green_confirmed",
            release_blocking=False,
            test_count_observed=_test_count(observed_results, "existing_p7_reuse_contract", 0),
            reason_codes=("reuse_subset_green_is_group_only",),
        ),
        _group(
            "positive_recovery_e2e",
            status=positive_status,
            green_scope="isolated_red_closure_only",
            green_claim_allowed=False,
            release_blocking=False,
            test_count_observed=_test_count(observed_results, "heavy_isolated_positive_recovery_red", 0),
            red_refs=() if positive_status == "closed_confirmed" else ("P7-RED-001", "P7-RED-002"),
            reason_codes=("positive_recovery_red_closure_is_not_p7_complete",),
        ),
        _group(
            "product_quality_connection_e2e",
            status=connection_status,
            green_scope="isolated_timeout_only",
            green_claim_allowed=False,
            release_blocking=True,
            test_count_observed=_test_count(observed_results, "heavy_isolated_product_quality_connection_timeout", 0),
            red_refs=("P7-RED-003",),
            reason_codes=("product_quality_connection_e2e_timeout_or_unconfirmed",),
        ),
        _group(
            "real_device_submit_modal_readfeel",
            status=real_device_status,
            green_scope="manual_real_device_check_only",
            green_claim_allowed=False,
            release_blocking=real_device.get("status") != "verified",
            hold_refs=real_device.get("hold_refs", []),
            reason_codes=("real_device_submit_modal_readfeel_unverified",),
        ),
        _group(
            "full_backend_suite",
            status=full_suite_status,
            green_scope="not_claimable_from_split_groups",
            green_claim_allowed=False,
            release_blocking=True,
            hold_refs=dedupe_identifiers(
                [
                    "P7-HOLD-004",
                    *hold004_material["unresolved_hold_refs"],
                    *hold004_positive_material["unresolved_hold_refs"],
                    *hold004_step5_material["unresolved_hold_refs"],
                ],
                limit=40,
                max_length=120,
            ),
            red_refs=hold004_step5_material["unresolved_red_refs"],
            reason_codes=full_suite_reason_codes,
        ),
    ]
    unresolved_hold_refs = dedupe_identifiers(
        [
            *real_device.get("hold_refs", []),
            "P7-HOLD-004",
            *hold004_material["unresolved_hold_refs"],
            *hold004_positive_material["unresolved_hold_refs"],
            *hold004_step5_material["unresolved_hold_refs"],
        ],
        limit=40,
        max_length=120,
    )
    unresolved_red_refs = dedupe_identifiers(
        ["P7-RED-003", *hold004_step5_material["unresolved_red_refs"]],
        limit=80,
        max_length=160,
    )
    matrix = {
        "schema_version": P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R10_HOLD_MATRIX_STEP,
        "scope": "P7_backend_suite_split_matrix",
        "matrix_id": clean_identifier(matrix_id, default=P7_BACKEND_SUITE_MATRIX_ID, max_length=120),
        "real_device_check_schema_version": clean_identifier(
            real_device.get("schema_version"), default=P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION, max_length=128
        ),
        "groups": groups,
        "group_statuses": {group["group_id"]: group["status"] for group in groups},
        "unresolved_red_refs": unresolved_red_refs,
        "unresolved_hold_refs": unresolved_hold_refs,
        "required_followup_fixes": dedupe_identifiers(
            [
                "full_backend_suite_green_unconfirmed",
                *hold004_material["required_followup_fixes"],
                *hold004_step5_material["required_followup_fixes"],
                "positive_public_shape_target_green_pending_full_suite"
                if hold004_positive_material["target_green_confirmed"]
                else "",
            ],
            limit=80,
            max_length=160,
        ),
        "hold004_phase16_classification_schema_version": hold004_material["classification_schema_version"],
        "hold004_phase16_path_matrix_schema_version": hold004_material["path_matrix_schema_version"],
        "hold004_phase16_decision_rule_schema_version": hold004_material["decision_rule_schema_version"],
        "hold004_phase16_adjacent_registration_schema_version": hold004_material["adjacent_registration_schema_version"],
        "hold004_phase16_classified_red_present": hold004_material["classified_red_present"],
        "hold004_phase16_classification_status": hold004_material["classification_status"],
        "hold004_phase16_decision_kind": hold004_material["decision_kind"],
        "hold004_phase16_repair_branch": hold004_material["repair_branch"],
        "hold004_phase16_candidate_boundary_registered": hold004_material["candidate_boundary_registered"],
        "hold004_public_adjacent_red_registered": hold004_material["public_adjacent_red_registered"],
        "hold004_required_followup_fixes": hold004_material["required_followup_fixes"],
        "hold004_step5_meta_extension_schema_version": hold004_step5_material["meta_extension_schema_version"],
        "hold004_step5_material_connection_schema_version": hold004_step5_material["material_connection_schema_version"],
        "hold004_step5_material_connection_status": hold004_step5_material["material_connection_status"],
        "hold004_step5_material_connected": hold004_step5_material["connected"],
        "hold004_step5_contract_classification": hold004_step5_material["step5_contract_classification"],
        "hold004_step5_display_binding_red_present": hold004_step5_material["step5_display_binding_red_present"],
        "hold004_step5_candidate_gate_red_classified": hold004_step5_material["step5_candidate_gate_red_classified"],
        "hold004_step5_candidate_gate_red_closed": hold004_step5_material["step5_candidate_gate_red_closed"],
        "hold004_step5_mixed_contract_conflict_held": hold004_step5_material["step5_mixed_contract_conflict_held"],
        "hold004_step5_release_blocker": hold004_step5_material["release_blocker"],
        "hold004_step5_required_followup_fixes": hold004_step5_material["required_followup_fixes"],
        "hold004_step5_unresolved_red_refs": hold004_step5_material["unresolved_red_refs"],
        "hold004_step5_closed_red_refs": hold004_step5_material["closed_red_refs"],
        "hold004_step5_material_connection_status": "connected" if hold004_step5_material["connected"] else "not_connected",
        "hold004_step5_full_backend_suite_green_confirmed": False,
        "hold004_step5_release_allowed": False,
        "hold004_positive_public_shape_boundary_schema_version": hold004_positive_material["schema_version"],
        "hold004_positive_public_shape_boundary_status": hold004_positive_material["status"],
        "hold004_positive_public_shape_target_green_confirmed": hold004_positive_material["target_green_confirmed"],
        "hold004_positive_public_shape_repaired_target_green_pending_full_suite": hold004_positive_material[
            "repaired_target_green_pending_full_suite"
        ],
        "hold004_positive_public_shape_true_self_denial_regression_preserved": hold004_positive_material[
            "true_self_denial_regression_preserved"
        ],
        "hold004_positive_public_shape_emergency_regression_preserved": hold004_positive_material[
            "emergency_safety_regression_preserved"
        ],
        "hold004_positive_public_shape_support_required_regression_preserved": hold004_positive_material[
            "support_required_regression_preserved"
        ],
        "hold004_positive_public_shape_input_material_bundle_confirmed": hold004_positive_material[
            "r3_input_material_bundle_not_safety_triage_required"
        ],
        "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed": hold004_positive_material[
            "r4_public_e2e_labelled_two_stage_confirmed"
        ],
        "hold004_positive_public_shape_full_backend_suite_green_confirmed": False,
        "hold004_positive_public_shape_release_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "split_green_is_full_backend_suite_green": False,
        "split_green_can_close_p7_hold004": False,
        "real_device_submit_confirmed": real_device.get("real_device_submit_confirmed") is True,
        "real_device_submit_hold_preserved": "P7-HOLD-003" in unresolved_hold_refs,
        "p7_hold003_preserved": "P7-HOLD-003" in unresolved_hold_refs,
        "p7_hold004_preserved": "P7-HOLD-004" in unresolved_hold_refs,
        "release_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_backend_suite_split_matrix_contract(matrix)
    return matrix


def assert_p7_backend_suite_split_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 backend suite split matrix schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 backend suite split matrix phase")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 backend suite split matrix must stay body-free and release-closed")
    if data.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7 R10 must not claim full backend suite green")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("P7 R10 must not allow full backend suite green claim")
    if data.get("split_green_is_full_backend_suite_green") is not False:
        raise ValueError("P7 split green must not be treated as full backend suite green")
    groups = data.get("groups")
    if not isinstance(groups, list) or len(groups) != len(_ALLOWED_BACKEND_GROUP_IDS):
        raise ValueError("P7 backend suite split matrix must include the fixed groups")
    group_ids: set[str] = set()
    for raw_group in groups:
        group = safe_mapping(raw_group)
        group_id = clean_identifier(group.get("group_id"), max_length=120)
        if group_id not in _ALLOWED_BACKEND_GROUP_IDS or group_id in group_ids:
            raise ValueError("P7 backend suite split matrix group id changed")
        group_ids.add(group_id)
        if group.get("status") not in _ALLOWED_BACKEND_GROUP_STATUSES:
            raise ValueError("P7 backend suite split matrix group status changed")
        if group.get("release_allowed") is not False or group.get("body_free") is not True:
            raise ValueError("P7 backend suite split group must stay body-free and release-closed")
        if group.get("can_claim_full_backend_suite_green") is not False:
            raise ValueError("P7 split group must not claim full backend suite green")
        if group_id in {"positive_recovery_e2e", "product_quality_connection_e2e", "real_device_submit_modal_readfeel", "full_backend_suite"}:
            if group.get("green_claim_allowed") is not False:
                raise ValueError("P7 isolated/manual/full-suite groups must not allow green claim")
    if set(group_ids) != set(_ALLOWED_BACKEND_GROUP_IDS):
        raise ValueError("P7 backend suite split matrix missing a fixed group")
    unresolved_hold_refs = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120))
    if data.get("real_device_submit_confirmed") is not True and "P7-HOLD-003" not in unresolved_hold_refs:
        raise ValueError("P7-HOLD-003 must remain until real-device submit/modal read-feel is verified")
    if "P7-HOLD-004" not in unresolved_hold_refs:
        raise ValueError("P7-HOLD-004 must remain until full backend suite is actually confirmed")
    if data.get("hold004_phase16_classified_red_present") is True:
        if data.get("hold004_phase16_candidate_boundary_registered") is not True:
            raise ValueError("classified HOLD-004 Phase16 material must register the candidate boundary")
        if not dedupe_identifiers(data.get("hold004_required_followup_fixes"), limit=80, max_length=160):
            raise ValueError("classified HOLD-004 Phase16 material must expose follow-up fixes")
    if data.get("hold004_step5_material_connected") is True:
        if data.get("hold004_step5_meta_extension_schema_version") != P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix Step5 R5 schema_version mismatch")
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix Step5 R6 schema_version mismatch")
        if data.get("hold004_step5_release_blocker") is not True:
            raise ValueError("P7 R10 HOLD matrix must keep Step5 material as release blocker")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"), limit=80, max_length=160
        ):
            raise ValueError("P7 R10 HOLD matrix must expose Step5 display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 R10 HOLD matrix must not promote Step5 material to full-suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 R10 HOLD matrix must keep Step5 release_allowed=false")
        if data.get("hold004_step5_display_binding_red_present") is True and data.get("hold004_step5_candidate_gate_red_closed") is not True:
            if P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(data.get("unresolved_red_refs"), limit=80, max_length=160):
                raise ValueError("P7 matrix must expose the unresolved Step5 display-binding red ref")

    if data.get("hold004_positive_public_shape_boundary_schema_version"):
        if data.get("hold004_positive_public_shape_boundary_schema_version") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION:
            raise ValueError("positive public shape boundary schema_version mismatch in backend split matrix")
        if data.get("hold004_positive_public_shape_boundary_status") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS:
            raise ValueError("positive public shape boundary must be repaired-pending-full-suite in backend split matrix")
        for key in (
            "hold004_positive_public_shape_target_green_confirmed",
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite",
            "hold004_positive_public_shape_true_self_denial_regression_preserved",
            "hold004_positive_public_shape_emergency_regression_preserved",
            "hold004_positive_public_shape_support_required_regression_preserved",
            "hold004_positive_public_shape_input_material_bundle_confirmed",
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"positive public shape backend split matrix must keep {key}=True")
        if data.get("hold004_positive_public_shape_full_backend_suite_green_confirmed") is not False:
            raise ValueError("positive public shape target green must not become full backend suite green")
        if data.get("hold004_positive_public_shape_release_allowed") is not False:
            raise ValueError("positive public shape target green must not allow release")
    if data.get("hold004_step5_material_connection_schema_version"):
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("Step5 material connection schema_version mismatch in backend split matrix")
        if data.get("hold004_step5_candidate_gate_red_classified") is not True:
            raise ValueError("Step5 material connection must classify the candidate-gate red")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ):
            raise ValueError("Step5 material connection must expose the display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("Step5 material connection must not claim full backend suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("Step5 material connection must not allow release")
        if data.get("hold004_step5_display_binding_red_present") is True and data.get("hold004_step5_candidate_gate_red_closed") is not True:
            if P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(data.get("hold004_step5_unresolved_red_refs"), limit=40, max_length=160):
                raise ValueError("unresolved Step5 display-binding red must stay visible")
    if data.get("hold004_step5_material_connected") is True:
        if data.get("hold004_step5_meta_extension_schema_version") != P7_HOLD004_STEP5_R5_META_EXTENSION_SCHEMA_VERSION:
            raise ValueError("P7 backend split matrix Step5 R5 schema_version mismatch")
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("P7 backend split matrix Step5 R6 schema_version mismatch")
        if data.get("hold004_step5_release_blocker") is not True:
            raise ValueError("P7 backend split matrix must keep Step5 material as release blocker")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"), limit=80, max_length=160
        ):
            raise ValueError("P7 backend split matrix must expose Step5 display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 backend split matrix must not promote Step5 material to full-suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 backend split matrix must keep Step5 release_allowed=false")
        if data.get("hold004_step5_display_binding_red_present") is True and P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(
            data.get("unresolved_red_refs"), limit=80, max_length=160
        ):
            raise ValueError("P7 backend split matrix must expose the Step5 display-binding red ref")

    for key in (
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "hold004_close_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if safe_mapping({key: data.get(key)}).get(key) is True:
            raise ValueError(f"P7 backend split matrix must keep {key}=False")
    if "P7-RED-003" not in dedupe_identifiers(data.get("unresolved_red_refs"), limit=40, max_length=120):
        raise ValueError("P7-RED-003 must remain visible in the R10 backend split matrix")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_backend_suite_split_matrix.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_backend_suite_split_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_backend_suite_split_matrix")
    return True


def build_p7_r10_hold_matrix(
    *,
    real_device_check: Mapping[str, Any] | None = None,
    backend_suite_split_matrix: Mapping[str, Any] | None = None,
    observed_results: Mapping[str, Any] | None = None,
    hold004_phase16_classification: Mapping[str, Any] | None = None,
    hold004_path_matrix: Mapping[str, Any] | None = None,
    hold004_decision_rule: Mapping[str, Any] | None = None,
    hold004_adjacent_public_red_registration: Mapping[str, Any] | None = None,
    hold004_positive_public_shape_boundary: Mapping[str, Any] | None = None,
    hold004_step5_meta_extension: Mapping[str, Any] | None = None,
    hold004_step5_material_connection: Mapping[str, Any] | None = None,
    matrix_id: Any = "p7_r10_hold_matrix",
) -> dict[str, Any]:
    """Build the composite R10 HOLD matrix."""

    real_device = safe_mapping(real_device_check) if real_device_check is not None else build_p7_real_device_modal_readfeel_check()
    assert_p7_real_device_modal_readfeel_check_contract(real_device)
    backend = (
        safe_mapping(backend_suite_split_matrix)
        if backend_suite_split_matrix is not None
        else build_p7_backend_suite_split_matrix(
            observed_results=observed_results,
            real_device_check=real_device,
            hold004_phase16_classification=hold004_phase16_classification,
            hold004_path_matrix=hold004_path_matrix,
            hold004_decision_rule=hold004_decision_rule,
            hold004_adjacent_public_red_registration=hold004_adjacent_public_red_registration,
            hold004_positive_public_shape_boundary=hold004_positive_public_shape_boundary,
            hold004_step5_meta_extension=hold004_step5_meta_extension,
            hold004_step5_material_connection=hold004_step5_material_connection,
        )
    )
    assert_p7_backend_suite_split_matrix_contract(backend)
    unresolved_hold_refs = dedupe_identifiers(
        [*real_device.get("hold_refs", []), *backend.get("unresolved_hold_refs", [])], limit=80, max_length=120
    )
    unresolved_red_refs = dedupe_identifiers(backend.get("unresolved_red_refs"), limit=80, max_length=120)
    matrix = {
        "schema_version": P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R10_HOLD_MATRIX_STEP,
        "scope": P7_R10_HOLD_MATRIX_SCOPE,
        "matrix_id": clean_identifier(matrix_id, default="p7_r10_hold_matrix", max_length=120),
        "real_device_check_schema_version": real_device.get("schema_version"),
        "real_device_modal_readfeel_check_schema_version": real_device.get("schema_version"),
        "backend_suite_split_matrix_schema_version": backend.get("schema_version"),
        "hold004_phase16_classification_schema_version": backend.get("hold004_phase16_classification_schema_version", ""),
        "hold004_phase16_path_matrix_schema_version": backend.get("hold004_phase16_path_matrix_schema_version", ""),
        "hold004_phase16_decision_rule_schema_version": backend.get("hold004_phase16_decision_rule_schema_version", ""),
        "hold004_phase16_adjacent_registration_schema_version": backend.get("hold004_phase16_adjacent_registration_schema_version", ""),
        "hold004_phase16_classified_red_present": backend.get("hold004_phase16_classified_red_present") is True,
        "hold004_phase16_candidate_boundary_registered": backend.get("hold004_phase16_candidate_boundary_registered") is True,
        "hold004_public_adjacent_red_registered": backend.get("hold004_public_adjacent_red_registered") is True,
        "hold004_required_followup_fixes": dedupe_identifiers(
            backend.get("hold004_required_followup_fixes"),
            limit=80,
            max_length=160,
        ),
        "hold004_step5_meta_extension_schema_version": backend.get("hold004_step5_meta_extension_schema_version", ""),
        "hold004_step5_material_connection_schema_version": backend.get("hold004_step5_material_connection_schema_version", ""),
        "hold004_step5_material_connected": backend.get("hold004_step5_material_connected") is True,
        "hold004_step5_contract_classification": backend.get("hold004_step5_contract_classification", ""),
        "hold004_step5_display_binding_red_present": backend.get("hold004_step5_display_binding_red_present") is True,
        "hold004_step5_candidate_gate_red_classified": backend.get("hold004_step5_candidate_gate_red_classified") is True,
        "hold004_step5_candidate_gate_red_closed": backend.get("hold004_step5_candidate_gate_red_closed") is True,
        "hold004_step5_mixed_contract_conflict_held": backend.get("hold004_step5_mixed_contract_conflict_held") is True,
        "hold004_step5_release_blocker": backend.get("hold004_step5_release_blocker") is True,
        "hold004_step5_required_followup_fixes": dedupe_identifiers(
            backend.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ),
        "hold004_step5_full_backend_suite_green_confirmed": False,
        "hold004_step5_release_allowed": False,
        "hold004_positive_public_shape_boundary_schema_version": backend.get(
            "hold004_positive_public_shape_boundary_schema_version", ""
        ),
        "hold004_positive_public_shape_boundary_status": backend.get(
            "hold004_positive_public_shape_boundary_status", ""
        ),
        "hold004_positive_public_shape_target_green_confirmed": backend.get(
            "hold004_positive_public_shape_target_green_confirmed"
        ) is True,
        "hold004_positive_public_shape_repaired_target_green_pending_full_suite": backend.get(
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite"
        ) is True,
        "hold004_positive_public_shape_true_self_denial_regression_preserved": backend.get(
            "hold004_positive_public_shape_true_self_denial_regression_preserved"
        ) is True,
        "hold004_positive_public_shape_emergency_regression_preserved": backend.get(
            "hold004_positive_public_shape_emergency_regression_preserved"
        ) is True,
        "hold004_positive_public_shape_support_required_regression_preserved": backend.get(
            "hold004_positive_public_shape_support_required_regression_preserved"
        ) is True,
        "hold004_positive_public_shape_input_material_bundle_confirmed": backend.get(
            "hold004_positive_public_shape_input_material_bundle_confirmed"
        ) is True,
        "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed": backend.get(
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed"
        ) is True,
        "hold004_positive_public_shape_full_backend_suite_green_confirmed": False,
        "hold004_positive_public_shape_release_allowed": False,
        "hold004_step5_material_connection_schema_version": backend.get(
            "hold004_step5_material_connection_schema_version", ""
        ),
        "hold004_step5_material_connection_status": backend.get(
            "hold004_step5_material_connection_status", ""
        ),
        "hold004_step5_candidate_gate_red_classified": backend.get(
            "hold004_step5_candidate_gate_red_classified"
        ) is True,
        "hold004_step5_display_binding_red_present": backend.get(
            "hold004_step5_display_binding_red_present"
        ) is True,
        "hold004_step5_candidate_gate_red_closed": backend.get(
            "hold004_step5_candidate_gate_red_closed"
        ) is True,
        "hold004_step5_contract_classification": backend.get("hold004_step5_contract_classification", ""),
        "hold004_step5_required_followup_fixes": dedupe_identifiers(
            backend.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ),
        "hold004_step5_unresolved_red_refs": dedupe_identifiers(
            backend.get("hold004_step5_unresolved_red_refs"),
            limit=40,
            max_length=160,
        ),
        "hold004_step5_closed_red_refs": dedupe_identifiers(
            backend.get("hold004_step5_closed_red_refs"),
            limit=40,
            max_length=160,
        ),
        "hold004_step5_full_backend_suite_green_confirmed": False,
        "hold004_step5_release_allowed": False,
        "real_device_submit_confirmed": real_device.get("real_device_submit_confirmed") is True,
        "real_device_submit_modal_readfeel_verified": real_device.get("status") == "verified",
        "full_backend_suite_green_confirmed": backend.get("full_backend_suite_green_confirmed") is True,
        "full_backend_suite_green_claim_allowed": False,
        "split_green_is_full_backend_suite_green": False,
        "split_green_promoted_to_full_suite_green": False,
        "unresolved_red_refs": unresolved_red_refs,
        "unresolved_hold_refs": unresolved_hold_refs,
        "release_blockers": dedupe_identifiers([*unresolved_red_refs, *unresolved_hold_refs], limit=120, max_length=120),
        "required_followup_fixes": dedupe_identifiers(
            [
                "real_device_submit_modal_readfeel_unverified" if "P7-HOLD-003" in unresolved_hold_refs else "",
                "full_backend_suite_green_unconfirmed" if "P7-HOLD-004" in unresolved_hold_refs else "",
                *backend.get("hold004_required_followup_fixes", []),
                *backend.get("hold004_step5_required_followup_fixes", []),
                "positive_public_shape_target_green_pending_full_suite"
                if backend.get("hold004_positive_public_shape_target_green_confirmed") is True
                else "",
                *backend.get("hold004_step5_required_followup_fixes", []),
            ],
            limit=80,
            max_length=160,
        ),
        "manual_hold_boundary": {
            "automated_test_green_can_close_real_device_hold": False,
            "split_green_can_close_full_suite_hold": False,
            "p7_complete_claim_allowed": False,
            "p8_start_allowed": False,
            "release_allowed": False,
            "body_free": True,
        },
        "release_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
    }
    assert_p7_r10_hold_matrix_contract(matrix)
    return matrix


def assert_p7_r10_hold_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_R10_HOLD_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 R10 hold matrix schema_version")
    if data.get("phase") != P7_PHASE or data.get("scope") != P7_R10_HOLD_MATRIX_SCOPE:
        raise ValueError("unexpected P7 R10 hold matrix phase/scope")
    if data.get("real_device_check_schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("P7 R10 hold matrix must reference the real-device check schema")
    if data.get("real_device_modal_readfeel_check_schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("P7 R10 hold matrix must expose the real-device modal read-feel check schema")
    if data.get("backend_suite_split_matrix_schema_version") != P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 R10 hold matrix must reference the backend-suite split matrix schema")
    if data.get("release_allowed") is not False or data.get("body_free") is not True:
        raise ValueError("P7 R10 hold matrix must stay body-free and release-closed")
    if data.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7 R10 hold matrix must keep full_backend_suite_green_confirmed=false")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("P7 R10 hold matrix must keep full_backend_suite_green_claim_allowed=false")
    if data.get("split_green_is_full_backend_suite_green") is not False:
        raise ValueError("P7 R10 hold matrix must not equate split green with full-suite green")
    if data.get("split_green_promoted_to_full_suite_green") is not False:
        raise ValueError("P7 R10 hold matrix must not promote split green to full-suite green")
    if data.get("real_device_submit_modal_readfeel_verified") is True and data.get("real_device_submit_confirmed") is not True:
        raise ValueError("P7 R10 hold matrix verified modal read-feel requires real-device submit confirmation")
    hold_refs = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80, max_length=120))
    if data.get("real_device_submit_confirmed") is not True and "P7-HOLD-003" not in hold_refs:
        raise ValueError("P7 R10 hold matrix must keep P7-HOLD-003 when real-device submit is unverified")
    if "P7-HOLD-004" not in hold_refs:
        raise ValueError("P7 R10 hold matrix must keep P7-HOLD-004")
    if data.get("hold004_phase16_classified_red_present") is True:
        if data.get("hold004_phase16_candidate_boundary_registered") is not True:
            raise ValueError("P7 R10 HOLD matrix must preserve classified HOLD-004 candidate boundary")
        if "phase16_complete_composer_candidate_boundary" not in dedupe_identifiers(
            data.get("hold004_required_followup_fixes"),
            limit=80,
            max_length=160,
        ):
            raise ValueError("P7 R10 HOLD matrix must expose the Phase16 candidate-boundary follow-up")
    if data.get("hold004_positive_public_shape_boundary_schema_version"):
        if data.get("hold004_positive_public_shape_boundary_schema_version") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix positive public shape schema_version mismatch")
        if data.get("hold004_positive_public_shape_boundary_status") != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS:
            raise ValueError("P7 R10 HOLD matrix must keep positive public shape as repaired-pending-full-suite")
        for key in (
            "hold004_positive_public_shape_target_green_confirmed",
            "hold004_positive_public_shape_repaired_target_green_pending_full_suite",
            "hold004_positive_public_shape_true_self_denial_regression_preserved",
            "hold004_positive_public_shape_emergency_regression_preserved",
            "hold004_positive_public_shape_support_required_regression_preserved",
            "hold004_positive_public_shape_input_material_bundle_confirmed",
            "hold004_positive_public_shape_public_e2e_labelled_two_stage_confirmed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7 R10 HOLD matrix must keep {key}=True")
        if data.get("hold004_positive_public_shape_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 R10 HOLD matrix must not promote positive target green to full-suite green")
        if data.get("hold004_positive_public_shape_release_allowed") is not False:
            raise ValueError("P7 R10 HOLD matrix must keep positive public shape release_allowed=false")
    if data.get("hold004_step5_material_connection_schema_version"):
        if data.get("hold004_step5_material_connection_schema_version") != P7_HOLD004_STEP5_R6_MATERIAL_CONNECTION_SCHEMA_VERSION:
            raise ValueError("P7 R10 HOLD matrix Step5 material schema_version mismatch")
        if data.get("hold004_step5_candidate_gate_red_classified") is not True:
            raise ValueError("P7 R10 HOLD matrix must classify the Step5 candidate-gate material")
        if "step5_display_binding_contract_consistency" not in dedupe_identifiers(
            data.get("hold004_step5_required_followup_fixes"),
            limit=80,
            max_length=160,
        ):
            raise ValueError("P7 R10 HOLD matrix must expose the Step5 display-binding follow-up")
        if data.get("hold004_step5_full_backend_suite_green_confirmed") is not False:
            raise ValueError("P7 R10 HOLD matrix must not promote Step5 material to full-suite green")
        if data.get("hold004_step5_release_allowed") is not False:
            raise ValueError("P7 R10 HOLD matrix must keep Step5 release_allowed=false")
        if data.get("hold004_step5_display_binding_red_present") is True and data.get("hold004_step5_candidate_gate_red_closed") is not True:
            if P7_HOLD004_STEP5_RED_ID not in dedupe_identifiers(data.get("hold004_step5_unresolved_red_refs"), limit=40, max_length=160):
                raise ValueError("P7 R10 HOLD matrix must keep unresolved Step5 red visible")
    boundary = safe_mapping(data.get("manual_hold_boundary"))
    for key in (
        "automated_test_green_can_close_real_device_hold",
        "split_green_can_close_full_suite_hold",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"P7 R10 manual hold boundary must keep {key}=False")
    if boundary.get("body_free") is not True:
        raise ValueError("P7 R10 manual hold boundary must be body-free")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_r10_hold_matrix.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_r10_hold_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r10_hold_matrix")
    return True


def build_p7_real_device_full_backend_hold_matrix(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the R10 composite HOLD matrix."""

    return build_p7_r10_hold_matrix(*args, **kwargs)


def assert_p7_real_device_full_backend_hold_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    """Compatibility alias for the R10 composite HOLD matrix contract."""

    return assert_p7_r10_hold_matrix_contract(matrix)


def build_p7_hold_matrix(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return build_p7_r10_hold_matrix(*args, **kwargs)


def assert_p7_hold_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    return assert_p7_r10_hold_matrix_contract(matrix)


__all__ = [
    "P7_BACKEND_SUITE_MATRIX_ID",
    "P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION",
    "P7_HOLD_MATRIX_SCHEMA_VERSION",
    "P7_R10_HOLD_MATRIX_SCHEMA_VERSION",
    "P7_R10_HOLD_MATRIX_SCOPE",
    "P7_R10_HOLD_MATRIX_STEP",
    "P7_REAL_DEVICE_CHECK_ID",
    "P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION",
    "assert_p7_backend_suite_split_matrix_contract",
    "assert_p7_hold_matrix_contract",
    "assert_p7_r10_hold_matrix_contract",
    "assert_p7_real_device_full_backend_hold_matrix_contract",
    "assert_p7_real_device_modal_readfeel_check_contract",
    "build_p7_backend_suite_split_matrix",
    "build_p7_hold_matrix",
    "build_p7_r10_hold_matrix",
    "build_p7_real_device_full_backend_hold_matrix",
    "build_p7_real_device_modal_readfeel_check",
]
