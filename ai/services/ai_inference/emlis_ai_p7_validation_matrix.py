# -*- coding: utf-8 -*-
"""P7-9 Validation / regression matrix.

The validation matrix fixes what may be called green after P7 implementation and
what must stay RED/HOLD/isolated.  It deliberately distinguishes P7 core contract
green from full backend-suite green and from release readiness.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_INITIAL_HOLD_IDS,
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_blind_qa_material import (
    P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION,
    assert_p7_human_qa_material_index_contract,
    build_p7_human_qa_material_index,
)
from emlis_ai_p7_event_bridge import (
    P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION,
    assert_p7_p6_visible_expansion_boundary_contract,
    build_p7_p6_visible_expansion_boundary_validation,
)
from emlis_ai_p7_hold_matrix import (
    P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION,
    P7_R10_HOLD_MATRIX_SCHEMA_VERSION,
    P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION,
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    assert_p7_real_device_modal_readfeel_check_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
    build_p7_real_device_modal_readfeel_check,
)
from emlis_ai_p7_red_closure_classification import (
    P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
    assert_p7_red_closure_classification_matrix_contract,
    build_p7_red_closure_classification_matrix,
)
from emlis_ai_p7_red_ledger import P7_RED_LEDGER_SCHEMA_VERSION, assert_p7_red_ledger_contract, build_p7_red_ledger
from emlis_ai_p7_release_handoff import (
    P7_RELEASE_HANDOFF_SCHEMA_VERSION,
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_p7_runner_plan import P7_RUNNER_PLAN_SCHEMA_VERSION, assert_p7_runner_plan_contract, build_p7_runner_plan
from emlis_ai_p7_timeout_isolation import (
    P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY,
    P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E,
    P7_CONNECTION_E2E_OWNER_UNKNOWN,
    P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
    assert_p7_e2e_isolation_result_contract,
    build_p7_connection_e2e_r13_passed_observation_result,
    build_p7_connection_e2e_timeout_isolation_result,
)

P7_VALIDATION_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.validation_matrix.v1"
P7_VALIDATION_MATRIX_STEP: Final = "P7-9_ValidationRegressionMatrix_20260612"
P7_VALIDATION_MATRIX_SCOPE: Final = "P7_validation_regression_matrix"
P7_IMPLEMENTATION_RESULT_DOC_PATH: Final = "docs/Cocolon_EmlisAI_P7_ProductQualityRunner_ImplementationResult_20260612.md"
P7_RED_HOLD_CLOSURE_VALIDATION_SUMMARY_SCHEMA_VERSION: Final = "cocolon.emlis.p7.red_hold_closure_validation_summary.v1"

_ALLOWED_ROW_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "PASS",
        "RED_LEDGERED",
        "TIMEOUT_ISOLATED",
        "HANG_ISOLATED",
        "FAILED_ISOLATED",
        "PASSED_ISOLATED",
        "HOLD_UNCONFIRMED",
        "NOT_RUN",
        "NOT_RUN_ISOLATED",
        "BLOCKED",
    }
)
_ALLOWED_CHECK_KINDS: Final[frozenset[str]] = frozenset(
    {
        "p7_core_contract",
        "existing_reuse_subset",
        "heavy_positive_recovery_red",
        "heavy_connection_timeout",
        "full_backend_suite",
        "rn_contract",
        "api_response_contract",
        "db_contract",
        "release_handoff",
        "body_free_boundary",
        "red_closure_classification",
        "connection_timeout_isolation",
        "p5_human_qa_material_boundary",
        "p6_visible_expansion_boundary",
        "real_device_submit_modal_readfeel",
        "backend_suite_split_matrix",
        "r10_hold_matrix",
    }
)


def _observed(observed_results: Mapping[str, Any] | None, key: str) -> dict[str, Any]:
    source = safe_mapping(observed_results)
    value = source.get(key)
    if isinstance(value, Mapping):
        return safe_mapping(value)
    if isinstance(value, bool):
        return {"passed": value, "result_kind": "passed" if value else "failed"}
    if isinstance(value, str):
        return {"result_kind": value}
    return {}


def _result_kind(result: Mapping[str, Any]) -> str:
    if result.get("passed") is True:
        return "passed"
    return clean_identifier(result.get("result_kind") or result.get("status"), default="not_run", max_length=80)


def _row(
    row_id: str,
    *,
    check_kind: str,
    source_ref: str,
    observed_status: str,
    green_claim_scope: str,
    green_claim_allowed: bool,
    red_or_hold_allowed: bool,
    release_blocking: bool,
    red_refs: Sequence[Any] = (),
    hold_refs: Sequence[Any] = (),
    reason_codes: Sequence[Any] = (),
) -> dict[str, Any]:
    return {
        "row_id": clean_identifier(row_id, max_length=120),
        "check_kind": clean_identifier(check_kind, max_length=120),
        "source_ref": clean_identifier(source_ref, max_length=220),
        "observed_status": clean_identifier(observed_status, default="NOT_RUN", max_length=80),
        "green_claim_scope": clean_identifier(green_claim_scope, max_length=120),
        "green_claim_allowed": green_claim_allowed is True,
        "red_or_hold_allowed": red_or_hold_allowed is True,
        "release_blocking": release_blocking is True,
        "red_refs": dedupe_identifiers(red_refs, limit=40, max_length=120),
        "hold_refs": dedupe_identifiers(hold_refs, limit=40, max_length=120),
        "reason_codes": dedupe_identifiers(reason_codes, limit=80, max_length=160),
        "body_free": True,
        "release_allowed": False,
    }


def _p7_core_status(result: Mapping[str, Any]) -> str:
    kind = _result_kind(result)
    return "PASS" if kind in {"passed", "green"} else ("NOT_RUN" if kind == "not_run" else "BLOCKED")


def _heavy_positive_status(result: Mapping[str, Any]) -> str:
    kind = _result_kind(result)
    if kind in {"passed", "green", "closed", "closed_by_r0_r5_positive_recovery_suite"}:
        return "PASS"
    if kind in {"failed_preserved", "red_preserved", "red_ledgered", "failed", "2_failed"}:
        return "RED_LEDGERED"
    if kind == "not_run":
        return "NOT_RUN"
    return "BLOCKED"


def _heavy_connection_status(result: Mapping[str, Any]) -> str:
    kind = _result_kind(result)
    if kind in {"passed", "green", "closed", "body_free_guard_repaired"}:
        return "PASSED_ISOLATED"
    if kind in {"timeout_preserved", "timeout", "hang_preserved", "red_preserved", "red_ledgered"}:
        return "TIMEOUT_ISOLATED"
    if kind in {"failed", "failed_isolated", "body_free_violation", "compact_body_free_violation"}:
        return "FAILED_ISOLATED"
    if kind == "not_run":
        return "NOT_RUN"
    return "BLOCKED"


def _full_suite_status(result: Mapping[str, Any]) -> str:
    kind = _result_kind(result)
    if kind in {"not_run", "unconfirmed", "timeout", "hang"}:
        return "HOLD_UNCONFIRMED"
    return "BLOCKED" if kind in {"passed", "green"} and result.get("green_claim_allowed") is True else "HOLD_UNCONFIRMED"


def _connection_result_to_isolation_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return body-free P7-RED-003 observation material for validation.

    R13-8 consumes the repaired Product Quality Connection E2E result as the
    default validation material.  Explicit observed timeout/hang/failure inputs
    are still honored so older unresolved branches remain testable.
    """

    kind = _result_kind(result).lower()
    if kind in {
        "passed",
        "green",
        "closed",
        "closed_confirmed",
        "passed_closed",
        "passed_isolated",
        "body_free_guard_repaired",
    }:
        return build_p7_connection_e2e_r13_passed_observation_result()
    if kind in {"failed", "failed_isolated", "red_preserved", "red_ledgered", "compact_failure"}:
        owner = clean_identifier(
            result.get("owner_layer"),
            default=P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E,
            max_length=120,
        )
        if owner == "product_quality_scorecard_body_free_boundary":
            owner = P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY
        return build_p7_connection_e2e_timeout_isolation_result(
            result_kind="failed",
            last_completed_stage=result.get("last_completed_stage") or "product_quality_connection_e2e_compact_failure",
            owner_layer=owner,
        )
    if kind in {"hang", "hang_preserved", "hang_isolated"}:
        return build_p7_connection_e2e_timeout_isolation_result(
            result_kind="hang",
            last_completed_stage=result.get("last_completed_stage") or "unknown",
            owner_layer=result.get("owner_layer") or P7_CONNECTION_E2E_OWNER_UNKNOWN,
        )
    if kind in {"not_run", "unconfirmed"}:
        return build_p7_connection_e2e_timeout_isolation_result(
            result_kind="not_run",
            last_completed_stage=result.get("last_completed_stage") or "not_run",
            owner_layer=result.get("owner_layer") or P7_CONNECTION_E2E_OWNER_UNKNOWN,
        )
    return build_p7_connection_e2e_timeout_isolation_result(
        result_kind="timeout",
        last_completed_stage=result.get("last_completed_stage") or "unknown",
        owner_layer=result.get("owner_layer") or P7_CONNECTION_E2E_OWNER_UNKNOWN,
    )



def build_p7_validation_regression_matrix(
    *,
    runner_plan: Mapping[str, Any] | None = None,
    red_ledger: Mapping[str, Any] | None = None,
    release_handoff: Mapping[str, Any] | None = None,
    red_closure_classification_matrix: Mapping[str, Any] | None = None,
    connection_timeout_isolation_result: Mapping[str, Any] | None = None,
    human_qa_material_index: Mapping[str, Any] | None = None,
    p6_visible_boundary_validation: Mapping[str, Any] | None = None,
    real_device_check: Mapping[str, Any] | None = None,
    backend_suite_split_matrix: Mapping[str, Any] | None = None,
    r10_hold_matrix: Mapping[str, Any] | None = None,
    observed_results: Mapping[str, Any] | None = None,
    matrix_id: Any = "p7_validation_regression_matrix",
) -> dict[str, Any]:
    """Build the P7-9 validation matrix.

    ``observed_results`` may record local pytest outcomes, but the matrix still
    prevents full-suite, Product Pass, timeout, and release readiness claims from
    being inferred from subset green.
    """

    if observed_results is not None:
        assert_p7_no_body_payload_or_contract_mutation(observed_results, source="p7_validation_matrix.observed_results")
    plan = safe_mapping(runner_plan) if runner_plan is not None else build_p7_runner_plan()
    assert_p7_runner_plan_contract(plan)
    ledger = safe_mapping(red_ledger) if red_ledger is not None else build_p7_red_ledger()
    assert_p7_red_ledger_contract(ledger)
    observed_source = safe_mapping(observed_results)
    connection_observed_supplied = "heavy_isolated_product_quality_connection_timeout" in observed_source
    connection_result = _observed(observed_results, "heavy_isolated_product_quality_connection_timeout")
    if connection_timeout_isolation_result is not None:
        connection_isolation = safe_mapping(connection_timeout_isolation_result)
    elif red_closure_classification_matrix is not None:
        supplied_red_closure = safe_mapping(red_closure_classification_matrix)
        connection_isolation = (
            build_p7_connection_e2e_r13_passed_observation_result()
            if supplied_red_closure.get("product_quality_connection_timeout_closed") is True
            else build_p7_connection_e2e_timeout_isolation_result()
        )
    elif connection_observed_supplied:
        connection_isolation = _connection_result_to_isolation_result(connection_result)
    elif runner_plan is not None:
        connection_isolation = safe_mapping(plan.get("connection_timeout_isolation_result"))
        if not connection_isolation:
            connection_isolation = build_p7_connection_e2e_timeout_isolation_result()
    else:
        connection_isolation = build_p7_connection_e2e_r13_passed_observation_result()
    assert_p7_e2e_isolation_result_contract(connection_isolation)
    red_closure = (
        safe_mapping(red_closure_classification_matrix)
        if red_closure_classification_matrix is not None
        else build_p7_red_closure_classification_matrix(
            connection_timeout_isolation_result=connection_isolation,
            positive_recovery_r0_r5_green_confirmed=True,
        )
    )
    assert_p7_red_closure_classification_matrix_contract(red_closure)
    real_device = safe_mapping(real_device_check) if real_device_check is not None else build_p7_real_device_modal_readfeel_check()
    assert_p7_real_device_modal_readfeel_check_contract(real_device)
    backend_split = (
        safe_mapping(backend_suite_split_matrix)
        if backend_suite_split_matrix is not None
        else build_p7_backend_suite_split_matrix(
            observed_results=observed_results,
            real_device_check=real_device,
            positive_recovery_red_closed=red_closure.get("positive_recovery_red_closed") is True,
        )
    )
    assert_p7_backend_suite_split_matrix_contract(backend_split)
    r10_matrix = (
        safe_mapping(r10_hold_matrix)
        if r10_hold_matrix is not None
        else build_p7_r10_hold_matrix(real_device_check=real_device, backend_suite_split_matrix=backend_split)
    )
    assert_p7_r10_hold_matrix_contract(r10_matrix)
    handoff = (
        safe_mapping(release_handoff)
        if release_handoff is not None
        else build_p7_release_decision_handoff(runner_plan=plan, red_closure_classification=red_closure, r10_hold_matrix=r10_matrix)
    )
    assert_p7_release_decision_handoff_contract(handoff)
    human_qa_index = safe_mapping(human_qa_material_index) if human_qa_material_index is not None else build_p7_human_qa_material_index()
    assert_p7_human_qa_material_index_contract(human_qa_index)
    p6_boundary = (
        safe_mapping(p6_visible_boundary_validation)
        if p6_visible_boundary_validation is not None
        else build_p7_p6_visible_expansion_boundary_validation()
    )
    assert_p7_p6_visible_expansion_boundary_contract(p6_boundary)

    core_result = _observed(observed_results, "p7_core_contract")
    reuse_result = _observed(observed_results, "existing_p7_reuse_contract")
    positive_result = _observed(observed_results, "heavy_isolated_positive_recovery_red")
    full_suite_result = _observed(observed_results, "full_backend_suite")

    core_status = _p7_core_status(core_result)
    reuse_status = _p7_core_status(reuse_result)
    positive_status = _heavy_positive_status(positive_result)
    if red_closure.get("positive_recovery_red_closed") is True:
        positive_status = "PASS"
    release_blocker_red_refs = dedupe_identifiers(red_closure.get("release_blocker_red_refs") or red_closure.get("release_blockers"), limit=40, max_length=120)
    red003_closed = red_closure.get("product_quality_connection_timeout_closed") is True
    red003_observed_status = clean_identifier(
        red_closure.get("source_e2e_observed_status") or connection_isolation.get("observed_status"),
        default="PASSED_ISOLATED" if red003_closed else "TIMEOUT_ISOLATED",
        max_length=80,
    )
    connection_status = _heavy_connection_status(connection_result)
    if red003_closed:
        connection_status = red003_observed_status
    elif connection_status == "NOT_RUN":
        connection_status = clean_identifier(connection_isolation.get("observed_status"), default="TIMEOUT_ISOLATED", max_length=80)
    full_suite_status = _full_suite_status(full_suite_result)

    public_contract = safe_mapping(handoff.get("public_contract"))
    body_free_markers = safe_mapping(handoff.get("body_free_markers"))
    rn_contract_changed = public_contract.get("rn_visible_contract_changed") is True
    api_response_key_added = public_contract.get("api_response_key_added") is True
    db_schema_changed = public_contract.get("db_schema_changed") is True
    body_leak_detected = any(value is True for value in body_free_markers.values())
    red_closure_applied = bool(red_closure)
    p5_human_qa_completed = human_qa_index.get("p5_human_qa_completed") is True
    p5_human_qa_hold_refs = dedupe_identifiers(human_qa_index.get("unresolved_hold_refs"), limit=40, max_length=120)
    p6_visible_violations = int(p6_boundary.get("violation_count") or 0)
    p6_visible_boundary_passed = p6_boundary.get("validation_status") == "passed" and p6_visible_violations == 0
    real_device_verified = real_device.get("real_device_submit_confirmed") is True
    real_device_status = "PASS" if real_device_verified else "HOLD_UNCONFIRMED"
    backend_split_full_green = backend_split.get("full_backend_suite_green_confirmed") is True
    backend_split_status = "PASS" if backend_split_full_green else "HOLD_UNCONFIRMED"
    r10_hold_refs = dedupe_identifiers(r10_matrix.get("unresolved_hold_refs"), limit=80, max_length=120)

    rows = [
        _row(
            "P7-VAL-001",
            check_kind="p7_core_contract",
            source_ref="tests/test_emlis_ai_p7_*_20260612.py",
            observed_status=core_status,
            green_claim_scope="p7_core_contract_only",
            green_claim_allowed=core_status == "PASS",
            red_or_hold_allowed=False,
            release_blocking=core_status != "PASS",
            reason_codes=("p7_core_contract_green_only_not_release",),
        ),
        _row(
            "P7-VAL-002",
            check_kind="existing_reuse_subset",
            source_ref="Product Quality reuse subset",
            observed_status=reuse_status,
            green_claim_scope="existing_subset_only_not_full_backend_suite",
            green_claim_allowed=reuse_status == "PASS",
            red_or_hold_allowed=False,
            release_blocking=False,
            reason_codes=("existing_subset_green_is_not_p7_complete",),
        ),
        _row(
            "P7-VAL-003",
            check_kind="heavy_positive_recovery_red",
            source_ref="tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py",
            observed_status=positive_status,
            green_claim_scope="positive_recovery_red_closure_only_not_release",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=positive_status != "PASS",
            red_refs=() if positive_status == "PASS" else ("P7-RED-001", "P7-RED-002"),
            reason_codes=("positive_recovery_red_closed_by_r0_r5_but_not_p7_complete",),
        ),
        _row(
            "P7-VAL-004",
            check_kind="heavy_connection_timeout",
            source_ref="tests/test_emlis_ai_complete_product_quality_connection_e2e.py",
            observed_status=connection_status,
            green_claim_scope=(
                "r13_body_free_guard_closure_only_not_p7_complete"
                if red003_closed
                else "timeout_isolation_confirmation_only"
            ),
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=not red003_closed,
            red_refs=() if red003_closed else ("P7-RED-003",),
            reason_codes=(
                "product_quality_connection_timeout_closed_by_r13_body_free_guard_but_not_p7_complete"
                if red003_closed
                else "product_quality_connection_timeout_must_not_be_green",
            ),
        ),
        _row(
            "P7-VAL-005",
            check_kind="full_backend_suite",
            source_ref="full backend suite",
            observed_status=full_suite_status,
            green_claim_scope="no_green_claim_allowed_in_p7",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=True,
            hold_refs=("P7-HOLD-004",),
            reason_codes=("full_backend_suite_green_unconfirmed",),
        ),
        _row(
            "P7-VAL-006",
            check_kind="rn_contract",
            source_ref="RN visible contract unchanged",
            observed_status="PASS" if not rn_contract_changed else "BLOCKED",
            green_claim_scope="contract_unchanged_only",
            green_claim_allowed=not rn_contract_changed,
            red_or_hold_allowed=False,
            release_blocking=rn_contract_changed,
            reason_codes=("rn_visible_contract_unchanged",),
        ),
        _row(
            "P7-VAL-007",
            check_kind="api_response_contract",
            source_ref="public API response key unchanged",
            observed_status="PASS" if not api_response_key_added else "BLOCKED",
            green_claim_scope="contract_unchanged_only",
            green_claim_allowed=not api_response_key_added,
            red_or_hold_allowed=False,
            release_blocking=api_response_key_added,
            reason_codes=("api_response_key_unchanged",),
        ),
        _row(
            "P7-VAL-008",
            check_kind="db_contract",
            source_ref="DB schema unchanged",
            observed_status="PASS" if not db_schema_changed else "BLOCKED",
            green_claim_scope="contract_unchanged_only",
            green_claim_allowed=not db_schema_changed,
            red_or_hold_allowed=False,
            release_blocking=db_schema_changed,
            reason_codes=("db_schema_unchanged",),
        ),
        _row(
            "P7-VAL-009",
            check_kind="release_handoff",
            source_ref="P7ReleaseDecisionHandoffV1",
            observed_status="PASS" if handoff.get("release_allowed") is False else "BLOCKED",
            green_claim_scope="handoff_material_only_not_release",
            green_claim_allowed=handoff.get("release_allowed") is False,
            red_or_hold_allowed=True,
            release_blocking=bool(handoff.get("release_blockers")),
            red_refs=handoff.get("unresolved_red_refs", []),
            hold_refs=handoff.get("unresolved_hold_refs", []),
            reason_codes=("release_handoff_material_separated_from_release_decision",),
        ),
        _row(
            "P7-VAL-010",
            check_kind="body_free_boundary",
            source_ref="P7 body-free markers",
            observed_status="PASS" if not body_leak_detected else "BLOCKED",
            green_claim_scope="body_free_contract_only",
            green_claim_allowed=not body_leak_detected,
            red_or_hold_allowed=False,
            release_blocking=body_leak_detected,
            reason_codes=("raw_body_not_serialized",),
        ),
        _row(
            "P7-VAL-011",
            check_kind="red_closure_classification",
            source_ref="P7RedClosureClassificationMatrixV1",
            observed_status=(
                "PASS"
                if red_closure.get("positive_recovery_red_closed") is True
                and (release_blocker_red_refs == ["P7-RED-003"] or (red003_closed and release_blocker_red_refs == []))
                else ("NOT_RUN" if not red_closure_applied else "BLOCKED")
            ),
            green_claim_scope="red_classification_only_not_p7_complete",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=bool(release_blocker_red_refs),
            red_refs=release_blocker_red_refs,
            reason_codes=(
                "red003_closed_by_r13_but_holds_remain"
                if red003_closed
                else "positive_recovery_closed_but_timeout_red_remains",
            ),
        ),
        _row(
            "P7-VAL-012",
            check_kind="connection_timeout_isolation",
            source_ref="P7E2EIsolationResultV1",
            observed_status=red003_observed_status,
            green_claim_scope="timeout_isolation_only_not_core_green",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=False if red003_closed else connection_isolation.get("release_blocker") is True,
            red_refs=() if red003_closed else connection_isolation.get("red_refs", []),
            reason_codes=(
                "timeout_isolation_observation_closed_red003_but_cannot_join_p7_core_green"
                if red003_closed
                else "timeout_isolation_cannot_join_p7_core_green",
            ),
        ),
        _row(
            "P7-VAL-013",
            check_kind="p5_human_qa_material_boundary",
            source_ref="P7HumanQAMaterialIndexV1",
            observed_status="PASS" if p5_human_qa_completed else "HOLD_UNCONFIRMED",
            green_claim_scope="human_qa_material_boundary_only_not_release",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=not p5_human_qa_completed,
            hold_refs=p5_human_qa_hold_refs,
            reason_codes=(
                "p5_human_qa_material_keeps_local_body_packet_out_of_release_material",
                "p5_human_qa_unreviewed_stays_hold",
            ),
        ),
        _row(
            "P7-VAL-014",
            check_kind="p6_visible_expansion_boundary",
            source_ref="P7P6VisibleExpansionBoundaryV1",
            observed_status="PASS" if p6_visible_boundary_passed else "BLOCKED",
            green_claim_scope="p6_visible_boundary_validation_only_not_expansion",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=True,
            hold_refs=("P7-HOLD-002",),
            reason_codes=(
                "p6_visible_structure_question_only",
                "p6_visible_expansion_requires_future_design",
            ),
        ),
        _row(
            "P7-VAL-015",
            check_kind="real_device_submit_modal_readfeel",
            source_ref="P7RealDeviceModalReadfeelCheckV1",
            observed_status=real_device_status,
            green_claim_scope="manual_real_device_check_only_not_automated_green",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=not real_device_verified,
            hold_refs=real_device.get("hold_refs", []),
            reason_codes=("real_device_submit_modal_readfeel_unverified",),
        ),
        _row(
            "P7-VAL-016",
            check_kind="backend_suite_split_matrix",
            source_ref="P7BackendSuiteSplitMatrixV1",
            observed_status=backend_split_status,
            green_claim_scope="split_green_not_full_backend_suite_green",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=True,
            red_refs=backend_split.get("unresolved_red_refs", []),
            hold_refs=backend_split.get("unresolved_hold_refs", []),
            reason_codes=("split_green_must_not_be_called_full_backend_suite_green",),
        ),
        _row(
            "P7-VAL-017",
            check_kind="r10_hold_matrix",
            source_ref="P7R10HoldMatrixV1",
            observed_status="PASS" if not r10_hold_refs else "HOLD_UNCONFIRMED",
            green_claim_scope="r10_hold_matrix_material_only_not_p7_complete",
            green_claim_allowed=False,
            red_or_hold_allowed=True,
            release_blocking=bool(r10_hold_refs),
            red_refs=r10_matrix.get("unresolved_red_refs", []),
            hold_refs=r10_hold_refs,
            reason_codes=(
                "r10_holds_are_material_only_not_closed_by_validation",
                "manual_real_device_and_full_suite_holds_preserved",
            ),
        ),
    ]

    closed_red_refs = dedupe_identifiers(red_closure.get("closed_red_refs"), limit=80, max_length=120)
    closed_red_set = set(closed_red_refs)
    unresolved_red_refs = dedupe_identifiers(
        [ref for ref in [*release_blocker_red_refs, *handoff.get("unresolved_red_refs", [])] if ref not in closed_red_set],
        limit=80,
        max_length=120,
    )
    unresolved_hold_refs = dedupe_identifiers(
        [*P7_INITIAL_HOLD_IDS, *handoff.get("unresolved_hold_refs", []), *p5_human_qa_hold_refs, "P7-HOLD-002", *r10_hold_refs],
        limit=80,
        max_length=120,
    )
    row_statuses = {row["row_id"]: row["observed_status"] for row in rows}
    red_preserved = bool(
        red_closure.get("positive_recovery_red_closed") is True
        or positive_status == "RED_LEDGERED"
        or {"P7-RED-001", "P7-RED-002"} & set(unresolved_red_refs)
    )
    timeout_preserved = (
        not red003_closed
        and "P7-RED-003" in unresolved_red_refs
        and connection_isolation.get("can_join_p7_core_green") is False
    )
    release_blocking_rows = [row["row_id"] for row in rows if row.get("release_blocking") is True]
    release_handoff_final_consistent = (
        handoff.get("release_allowed") is False
        and handoff.get("real_device_submit_confirmed") is False
        and handoff.get("full_backend_suite_green_confirmed") is False
        and safe_mapping(handoff.get("manual_hold_status")).get("real_device_submit_hold_preserved") is True
        and safe_mapping(handoff.get("manual_hold_status")).get("full_backend_suite_hold_preserved") is True
    )
    red_hold_closure_validation_summary = {
        "schema_version": "cocolon.emlis.p7.red_hold_closure_validation_summary.v1",
        "p7_core_green_confirmed": core_status == "PASS",
        "positive_recovery_red_closed": red_closure.get("positive_recovery_red_closed") is True,
        "product_quality_connection_timeout_closed": red003_closed,
        "product_quality_connection_timeout_classified": red_closure.get("product_quality_connection_timeout_classified") is True,
        "p5_human_qa_completed": p5_human_qa_completed,
        "p5_human_qa_hold_preserved": "P7-HOLD-001" in p5_human_qa_hold_refs or p5_human_qa_completed is True,
        "p6_visible_expansion_blocked": p6_boundary.get("visible_expansion_allowed") is False,
        "p6_visible_expansion_boundary_validated": p6_visible_boundary_passed,
        "real_device_submit_confirmed": False,
        "real_device_submit_modal_readfeel_verified": False,
        "real_device_submit_hold_preserved": "P7-HOLD-003" in r10_hold_refs or real_device_verified,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_green_claim_allowed": False,
        "full_backend_suite_hold_preserved": "P7-HOLD-004" in r10_hold_refs or backend_split_full_green,
        "split_green_promoted_to_full_suite_green": False,
        "release_handoff_final_consistent": release_handoff_final_consistent,
        "p7_complete": False,
        "p7_complete_claim_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "release_blockers": dedupe_identifiers(
            [*unresolved_red_refs, *unresolved_hold_refs, *handoff.get("release_blockers", [])],
            limit=240,
            max_length=160,
        ),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "terminal_output_body_included": False,
    }

    matrix = {
        "schema_version": P7_VALIDATION_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_VALIDATION_MATRIX_STEP,
        "scope": P7_VALIDATION_MATRIX_SCOPE,
        "matrix_id": clean_identifier(matrix_id, default="p7_validation_regression_matrix", max_length=120),
        "runner_plan_schema_version": clean_identifier(plan.get("schema_version"), default=P7_RUNNER_PLAN_SCHEMA_VERSION, max_length=128),
        "red_ledger_schema_version": clean_identifier(ledger.get("schema_version"), default=P7_RED_LEDGER_SCHEMA_VERSION, max_length=128),
        "red_closure_classification_schema_version": clean_identifier(
            red_closure.get("schema_version"), default=P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION, max_length=128
        ),
        "e2e_isolation_result_schema_version": clean_identifier(
            connection_isolation.get("schema_version"), default=P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION, max_length=128
        ),
        "release_handoff_schema_version": clean_identifier(handoff.get("schema_version"), default=P7_RELEASE_HANDOFF_SCHEMA_VERSION, max_length=128),
        "human_qa_material_index_schema_version": clean_identifier(
            human_qa_index.get("schema_version"), default=P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION, max_length=128
        ),
        "p6_visible_boundary_schema_version": clean_identifier(
            p6_boundary.get("schema_version"), default=P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION, max_length=128
        ),
        "real_device_check_schema_version": clean_identifier(
            real_device.get("schema_version"), default=P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION, max_length=128
        ),
        "backend_suite_split_matrix_schema_version": clean_identifier(
            backend_split.get("schema_version"), default=P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION, max_length=128
        ),
        "r10_hold_matrix_schema_version": clean_identifier(r10_matrix.get("schema_version"), default=P7_R10_HOLD_MATRIX_SCHEMA_VERSION, max_length=128),
        "implementation_result_doc_path": P7_IMPLEMENTATION_RESULT_DOC_PATH,
        "matrix_rows": rows,
        "row_statuses": row_statuses,
        "summary": {
            "p7_core_contract_green": core_status == "PASS",
            "existing_reuse_subset_green": reuse_status == "PASS",
            "positive_recovery_red_closed": red_closure.get("positive_recovery_red_closed") is True,
            "positive_recovery_red_remains_ledgered_or_classified": red_preserved,
            "product_quality_connection_timeout_classified": red_closure.get("product_quality_connection_timeout_classified") is True,
            "red_closure_classification_applied": red_closure_applied,
            "product_quality_connection_timeout_closed": red003_closed,
            "product_quality_connection_timeout_remains_ledgered_or_isolated": timeout_preserved,
            "full_backend_suite_green_confirmed": False,
            "full_backend_suite_green_claim_allowed": False,
            "rn_contract_changed": rn_contract_changed,
            "api_response_key_added": api_response_key_added,
            "db_schema_changed": db_schema_changed,
            "body_free_boundary_kept": not body_leak_detected,
            "p5_human_qa_completed": p5_human_qa_completed,
            "p5_human_qa_material_boundary_body_free": human_qa_index.get("scorecard_body_free") is True and human_qa_index.get("release_material_body_free") is True,
            "p5_human_qa_hold_preserved": "P7-HOLD-001" in p5_human_qa_hold_refs or p5_human_qa_completed is True,
            "p6_visible_expansion_blocked": p6_boundary.get("visible_expansion_allowed") is False,
            "p6_visible_expansion_boundary_validated": p6_visible_boundary_passed,
            "p6_visible_expansion_violation_count": p6_visible_violations,
            "real_device_submit_confirmed": False,
            "real_device_submit_modal_readfeel_verified": False,
            "real_device_submit_hold_preserved": "P7-HOLD-003" in r10_hold_refs or real_device_verified,
            "backend_suite_split_matrix_applied": True,
            "backend_suite_split_matrix_hold_preserved": "P7-HOLD-004" in r10_hold_refs,
            "backend_suite_split_green_is_full_backend_suite_green": False,
            "split_green_promoted_to_full_suite_green": False,
            "full_backend_suite_hold_preserved": "P7-HOLD-004" in r10_hold_refs or backend_split_full_green,
            "r10_hold_matrix_applied": True,
            "release_handoff_final_consistent": release_handoff_final_consistent,
            "release_decision_input_ready": bool(handoff.get("release_decision_input_ready") is True),
            "release_allowed": False,
            "p7_complete_claim_allowed": False,
            "p8_start_allowed": False,
            "product_pass_is_release_ready": False,
        },
        "closed_red_refs": closed_red_refs,
        "unresolved_red_refs": unresolved_red_refs,
        "unresolved_hold_refs": unresolved_hold_refs,
        "release_blocking_rows": release_blocking_rows,
        "red_hold_closure_validation_summary": red_hold_closure_validation_summary,
        "green_claim_policy": {
            "p7_core_tests_green_can_be_claimed": core_status == "PASS",
            "existing_reuse_subset_green_can_be_claimed": reuse_status == "PASS",
            "positive_recovery_closed_can_be_claimed_release_ready": False,
            "heavy_e2e_red_can_be_claimed_green": False,
            "timeout_or_hang_can_be_claimed_green": False,
            "connection_timeout_isolation_can_join_p7_core_green": False,
            "full_backend_suite_green_claim_allowed": False,
            "split_green_can_be_called_full_backend_suite_green": False,
            "split_green_can_be_claimed_full_backend_suite_green": False,
            "split_green_can_be_promoted_to_full_backend_suite_green": False,
            "automated_test_green_can_close_real_device_hold": False,
            "p7_complete_claim_allowed": False,
            "p8_start_allowed": False,
            "release_ready_claim_allowed": False,
            "body_free": True,
        },
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free": True,
        "release_allowed": False,
    }
    assert_p7_validation_regression_matrix_contract(matrix)
    return matrix


def build_p7_validation_matrix(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for the shorter P7-9 matrix name."""

    return build_p7_validation_regression_matrix(*args, **kwargs)


def assert_p7_validation_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    """Compatibility alias for the shorter P7-9 matrix contract name."""

    return assert_p7_validation_regression_matrix_contract(matrix)


def assert_p7_validation_regression_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_VALIDATION_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 validation matrix schema_version")
    if data.get("phase") != P7_PHASE or data.get("scope") != P7_VALIDATION_MATRIX_SCOPE:
        raise ValueError("unexpected P7 validation matrix phase/scope")
    if data.get("runner_plan_schema_version") != P7_RUNNER_PLAN_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference runner plan")
    if data.get("red_ledger_schema_version") != P7_RED_LEDGER_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference red ledger")
    classification_schema = clean_identifier(data.get("red_closure_classification_schema_version"), default="", max_length=128)
    if classification_schema and classification_schema != P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix has unexpected red closure classification schema")
    if data.get("e2e_isolation_result_schema_version") != P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference E2E isolation result")
    if data.get("release_handoff_schema_version") != P7_RELEASE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference release handoff")
    if data.get("human_qa_material_index_schema_version") != P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference P5 human QA material index")
    if data.get("p6_visible_boundary_schema_version") != P7_P6_VISIBLE_BOUNDARY_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference P6 visible boundary validation")
    if data.get("real_device_check_schema_version") != P7_REAL_DEVICE_MODAL_READFEEL_CHECK_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference real-device HOLD check")
    if data.get("backend_suite_split_matrix_schema_version") != P7_BACKEND_SUITE_SPLIT_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference backend-suite split matrix")
    if data.get("r10_hold_matrix_schema_version") != P7_R10_HOLD_MATRIX_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must reference R10 HOLD matrix")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 validation matrix must not allow release")
    if data.get("body_free") is not True:
        raise ValueError("P7 validation matrix must be body-free")
    rows = data.get("matrix_rows")
    if not isinstance(rows, list) or len(rows) < 16:
        raise ValueError("P7 validation matrix must include validation rows")
    row_ids: set[str] = set()
    check_kinds: set[str] = set()
    for raw_row in rows:
        row = safe_mapping(raw_row)
        row_id = clean_identifier(row.get("row_id"), max_length=120)
        if not row_id or row_id in row_ids:
            raise ValueError("P7 validation matrix rows must have unique ids")
        row_ids.add(row_id)
        kind = clean_identifier(row.get("check_kind"), max_length=120)
        if kind not in _ALLOWED_CHECK_KINDS:
            raise ValueError(f"P7 validation matrix has unsupported check kind: {kind}")
        check_kinds.add(kind)
        if row.get("observed_status") not in _ALLOWED_ROW_STATUSES:
            raise ValueError("P7 validation matrix row observed_status changed")
        if row.get("release_allowed") is not False or row.get("body_free") is not True:
            raise ValueError("P7 validation matrix row must stay body-free and release-closed")
        if kind in {
            "heavy_positive_recovery_red",
            "heavy_connection_timeout",
            "full_backend_suite",
            "red_closure_classification",
            "connection_timeout_isolation",
            "p5_human_qa_material_boundary",
            "p6_visible_expansion_boundary",
            "real_device_submit_modal_readfeel",
            "backend_suite_split_matrix",
            "r10_hold_matrix",
        } and row.get("green_claim_allowed") is not False:
            raise ValueError("P7 heavy/full-suite/classification/HOLD rows must not allow green claim")
    if not _ALLOWED_CHECK_KINDS.issubset(check_kinds):
        raise ValueError("P7 validation matrix is missing required check kinds")
    summary = safe_mapping(data.get("summary"))
    for key in (
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "real_device_submit_confirmed",
        "real_device_submit_modal_readfeel_verified",
        "backend_suite_split_green_is_full_backend_suite_green",
        "split_green_promoted_to_full_suite_green",
        "release_allowed",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "product_pass_is_release_ready",
    ):
        if summary.get(key) is not False:
            raise ValueError(f"P7 validation summary must keep {key}=False")
    for key in (
        "positive_recovery_red_remains_ledgered_or_classified",
        "p5_human_qa_material_boundary_body_free",
        "p5_human_qa_hold_preserved",
        "p6_visible_expansion_blocked",
        "real_device_submit_hold_preserved",
        "backend_suite_split_matrix_applied",
        "backend_suite_split_matrix_hold_preserved",
        "full_backend_suite_hold_preserved",
        "r10_hold_matrix_applied",
        "release_handoff_final_consistent",
    ):
        if summary.get(key) is not True:
            raise ValueError(f"P7 validation summary must keep {key}=True")
    timeout_closed = summary.get("product_quality_connection_timeout_closed") is True
    timeout_remains = summary.get("product_quality_connection_timeout_remains_ledgered_or_isolated") is True
    if timeout_closed == timeout_remains:
        raise ValueError("P7 validation summary must distinguish RED-003 closed from timeout remaining")
    if summary.get("product_quality_connection_timeout_classified") is not True:
        raise ValueError("P7 validation summary must classify P7-RED-003")
    if summary.get("p5_human_qa_completed") is not False and "P7-HOLD-001" in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80):
        raise ValueError("P7 validation matrix must not keep P7-HOLD-001 unresolved after completed human QA")
    if not isinstance(summary.get("p6_visible_expansion_violation_count"), int) or summary.get("p6_visible_expansion_violation_count") < 0:
        raise ValueError("P7 validation summary must expose non-negative P6 violation count")
    closed_refs = set(dedupe_identifiers(data.get("closed_red_refs"), limit=20))
    unresolved_refs = set(dedupe_identifiers(data.get("unresolved_red_refs"), limit=20))
    if closed_refs & unresolved_refs:
        raise ValueError("P7 validation matrix must not keep closed RED refs unresolved")
    if summary.get("positive_recovery_red_closed") is True and not {"P7-RED-001", "P7-RED-002"}.issubset(closed_refs):
        raise ValueError("P7 validation matrix must expose closed Positive Recovery RED refs when marked closed")
    if summary.get("product_quality_connection_timeout_classified") is True:
        if timeout_closed:
            if "P7-RED-003" not in closed_refs or "P7-RED-003" in unresolved_refs:
                raise ValueError("P7 validation matrix must carry P7-RED-003 as closed after R13 closure")
        elif "P7-RED-003" not in unresolved_refs:
            raise ValueError("P7 validation matrix must keep P7-RED-003 unresolved when timeout is not closed")
    closure_summary = safe_mapping(data.get("red_hold_closure_validation_summary"))
    if closure_summary.get("schema_version") != "cocolon.emlis.p7.red_hold_closure_validation_summary.v1":
        raise ValueError("P7 validation matrix must expose the R11 RED/HOLD closure validation summary")
    for key in (
        "real_device_submit_confirmed",
        "real_device_submit_modal_readfeel_verified",
        "full_backend_suite_green_confirmed",
        "full_backend_suite_green_claim_allowed",
        "split_green_promoted_to_full_suite_green",
        "p7_complete",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if closure_summary.get(key) is not False:
            raise ValueError(f"P7 RED/HOLD closure summary must keep {key}=False")
    if closure_summary.get("product_quality_connection_timeout_closed") is not timeout_closed:
        raise ValueError("P7 RED/HOLD closure summary must mirror RED-003 closed state")
    for key in (
        "p5_human_qa_hold_preserved",
        "p6_visible_expansion_blocked",
        "p6_visible_expansion_boundary_validated",
        "real_device_submit_hold_preserved",
        "full_backend_suite_hold_preserved",
        "release_handoff_final_consistent",
        "body_free",
    ):
        if closure_summary.get(key) is not True:
            raise ValueError(f"P7 RED/HOLD closure summary must keep {key}=True")
    for key in (
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "reviewer_free_text_included",
        "terminal_output_body_included",
    ):
        if closure_summary.get(key) is not False:
            raise ValueError(f"P7 RED/HOLD closure summary must keep body marker {key}=False")
    unresolved_hold_refs = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=80))
    if summary.get("p5_human_qa_completed") is not True and "P7-HOLD-001" not in unresolved_hold_refs:
        raise ValueError("P7 validation matrix must keep P7-HOLD-001 unresolved until P5 human QA completes")
    if "P7-HOLD-002" not in unresolved_hold_refs:
        raise ValueError("P7 validation matrix must keep P7-HOLD-002 for P6 visible boundary")
    if "P7-HOLD-003" not in unresolved_hold_refs:
        raise ValueError("P7 validation matrix must keep P7-HOLD-003 until real-device submit/modal read-feel is verified")
    if "P7-HOLD-004" not in unresolved_hold_refs:
        raise ValueError("P7 validation matrix must keep P7-HOLD-004 until full backend suite is confirmed")
    policy = safe_mapping(data.get("green_claim_policy"))
    for key in (
        "positive_recovery_closed_can_be_claimed_release_ready",
        "heavy_e2e_red_can_be_claimed_green",
        "timeout_or_hang_can_be_claimed_green",
        "connection_timeout_isolation_can_join_p7_core_green",
        "full_backend_suite_green_claim_allowed",
        "split_green_can_be_called_full_backend_suite_green",
        "split_green_can_be_claimed_full_backend_suite_green",
        "split_green_can_be_promoted_to_full_backend_suite_green",
        "automated_test_green_can_close_real_device_hold",
        "p7_complete_claim_allowed",
        "p8_start_allowed",
        "release_ready_claim_allowed",
    ):
        if policy.get(key) is not False:
            raise ValueError(f"P7 validation green policy must keep {key}=False")
    closure_summary = safe_mapping(data.get("red_hold_closure_validation_summary"))
    if closure_summary.get("schema_version") != P7_RED_HOLD_CLOSURE_VALIDATION_SUMMARY_SCHEMA_VERSION:
        raise ValueError("P7 validation matrix must include final RED/HOLD closure validation summary")
    for key in (
        "real_device_submit_confirmed",
        "full_backend_suite_green_confirmed",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
    ):
        if closure_summary.get(key) is not False:
            raise ValueError(f"P7 RED/HOLD closure validation summary must keep {key}=False")
    if closure_summary.get("body_free") is not True:
        raise ValueError("P7 RED/HOLD closure validation summary must be body-free")
    required_closure_blockers = {"P7-HOLD-002", "P7-HOLD-003", "P7-HOLD-004"}
    if closure_summary.get("p5_human_qa_completed") is not True:
        required_closure_blockers.add("P7-HOLD-001")
    if not timeout_closed:
        required_closure_blockers.add("P7-RED-003")
    if not required_closure_blockers.issubset(set(dedupe_identifiers(closure_summary.get("release_blockers"), limit=120))):
        raise ValueError("P7 RED/HOLD closure validation summary must keep remaining RED/HOLD blockers")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_validation_matrix.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_validation_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_validation_matrix")
    return True


__all__ = [
    "P7_IMPLEMENTATION_RESULT_DOC_PATH",
    "P7_RED_HOLD_CLOSURE_VALIDATION_SUMMARY_SCHEMA_VERSION",
    "P7_VALIDATION_MATRIX_SCHEMA_VERSION",
    "P7_VALIDATION_MATRIX_SCOPE",
    "P7_VALIDATION_MATRIX_STEP",
    "assert_p7_validation_matrix_contract",
    "assert_p7_validation_regression_matrix_contract",
    "build_p7_validation_matrix",
    "build_p7_validation_regression_matrix",
]
