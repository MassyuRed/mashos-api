# -*- coding: utf-8 -*-
"""P7 body-free RED closure classification matrix.

R7 originally classified P7 RED items without turning unresolved timeout/hang
sources into P7 core green or release readiness.  R13-7 adds the explicit
P7-RED-003 closure path for the repaired Product Quality Connection E2E when it
is supplied with the R13-6 passed observation.  Validation matrix and release
handoff consumption remain separate later steps, so P7 complete / P8 start /
release allowed stay false.
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
from emlis_ai_p7_timeout_isolation import (
    P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY,
    P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD,
    P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E,
    P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE,
    P7_CONNECTION_E2E_OWNER_TEST_LEAK_GUARD,
    P7_CONNECTION_E2E_OWNER_UNKNOWN,
    P7_CONNECTION_E2E_TEST_FILE,
    P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
    P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,
    assert_p7_e2e_isolation_result_contract,
    build_p7_connection_e2e_timeout_isolation_result,
)

P7_RED_CLOSURE_CLASSIFICATION_SCHEMA_VERSION: Final = "cocolon.emlis.p7.red_closure_classification.v1"
P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p7.red_closure_classification_matrix.v1"
P7_RED_CLOSURE_CLASSIFICATION_STEP: Final = "P7-R13-7_RedClosureClassificationMatrix_20260613"
P7_RED_CLOSURE_CLASSIFICATION_MATRIX_ID: Final = "p7_red_closure_classification_matrix_20260613"
P7_POSITIVE_RECOVERY_E2E_TEST_FILE: Final = "tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py"
P7_POSITIVE_RECOVERY_CLOSED_RED_IDS: Final[tuple[str, str]] = ("P7-RED-001", "P7-RED-002")
P7_UNRESOLVED_TIMEOUT_RED_IDS: Final[tuple[str, ...]] = (P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,)

_ALLOWED_CLOSURE_STATUSES: Final[frozenset[str]] = frozenset(
    {"OPEN", "CLASSIFIED", "REPAIRED_PENDING_REGRESSION", "CLOSED"}
)
_ALLOWED_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {
        "implementation_regression",
        "runtime_route_shadowing",
        "diagnostic_mapping_issue",
        "test_expectation_stale",
        "timeout_owner_unknown",
        "timeout_owner_classified",
        "manual_hold_only",
        "not_classified",
        "body_free_guard_overbroad_substring",
        "assertion_rewrite_large_diff_timeout",
        "body_free_guard_repaired",
        "product_quality_scorecard_body_free_violation",
        "product_quality_connection_runtime_failure",
    }
)
_ALLOWED_OWNER_LAYERS: Final[frozenset[str]] = frozenset(
    {
        "reader_relation_surface",
        "fail_closed_boundary",
        P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E,
        P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD,
        P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY,
        P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE,
        P7_CONNECTION_E2E_OWNER_TEST_LEAK_GUARD,
        P7_CONNECTION_E2E_OWNER_UNKNOWN,
    }
)
_ALL_P7_RED_IDS: Final[tuple[str, str, str]] = ("P7-RED-001", "P7-RED-002", "P7-RED-003")


def _body_free_marker_set() -> dict[str, bool]:
    markers = body_free_flags(include_history=False, include_reviewer=True, include_terminal=True)
    markers["terminal_output_body_included"] = False
    return markers


def _entry(
    red_id: str,
    *,
    status: str,
    classification: str,
    owner_layer: str,
    summary_code: str,
    evidence_refs: Sequence[Any],
    closure_requires_tests: Sequence[Any],
    observed_status: Any,
) -> dict[str, Any]:
    closed = status == "CLOSED"
    return {
        "schema_version": P7_RED_CLOSURE_CLASSIFICATION_SCHEMA_VERSION,
        "red_id": clean_identifier(red_id, max_length=80),
        "status": clean_identifier(status, max_length=80),
        "classification": clean_identifier(classification, max_length=120),
        "owner_layer": clean_identifier(owner_layer, max_length=120),
        "summary_code": clean_identifier(summary_code, max_length=180),
        "observed_status": clean_identifier(observed_status, default="not_observed", max_length=120),
        "evidence_refs": dedupe_identifiers(evidence_refs, limit=20, max_length=220),
        "closure_allowed": closed,
        "closure_requires_tests": dedupe_identifiers(closure_requires_tests, limit=30, max_length=180),
        "release_blocker_until_closed": not closed,
        "release_blocker": not closed,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "terminal_output_included": False,
    }


def _red003_entry_from_isolation(isolation: Mapping[str, Any]) -> dict[str, Any]:
    kind = clean_identifier(isolation.get("result_kind"), default="timeout", max_length=80)
    observed_status = clean_identifier(isolation.get("observed_status"), default="TIMEOUT_ISOLATED", max_length=120)
    owner_layer = clean_identifier(isolation.get("owner_layer"), default=P7_CONNECTION_E2E_OWNER_UNKNOWN, max_length=120)

    if kind == "passed":
        return _entry(
            P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,
            status="CLOSED",
            classification="body_free_guard_repaired",
            owner_layer=P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD,
            summary_code="product_quality_connection_e2e_body_free_guard_structured_and_default_pytest_passed",
            evidence_refs=(
                P7_CONNECTION_E2E_TEST_FILE,
                "tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py",
                "tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py",
                "p7_connection_e2e_r13_passed_observation_result",
            ),
            closure_requires_tests=(
                "product_quality_connection_e2e_default_pytest_passed",
                "product_quality_connection_e2e_timeout_wrapper_passed",
                "p7_body_free_leak_guard_helper_passed",
                "p7_body_free_leak_guard_contract_passed",
            ),
            observed_status=observed_status,
        )

    if kind == "failed" and owner_layer == P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY:
        return _entry(
            P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,
            status="CLASSIFIED",
            classification="product_quality_scorecard_body_free_violation",
            owner_layer=P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY,
            summary_code="product_quality_connection_e2e_returns_compact_body_free_violation_not_closed",
            evidence_refs=(P7_CONNECTION_E2E_TEST_FILE, "p7_connection_e2e_timeout_isolation_result"),
            closure_requires_tests=(
                "compact_body_free_violation_repaired",
                "product_quality_connection_e2e_returns_without_timeout",
            ),
            observed_status=observed_status,
        )

    if kind == "failed":
        return _entry(
            P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,
            status="CLASSIFIED",
            classification="product_quality_connection_runtime_failure",
            owner_layer=P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E,
            summary_code="product_quality_connection_e2e_returns_compact_failure_not_closed",
            evidence_refs=(P7_CONNECTION_E2E_TEST_FILE, "p7_connection_e2e_timeout_isolation_result"),
            closure_requires_tests=(
                "product_quality_connection_e2e_runtime_failure_repaired",
                "product_quality_connection_e2e_returns_without_timeout",
            ),
            observed_status=observed_status,
        )

    if kind in {"timeout", "hang"} and owner_layer == P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE:
        classification = "assertion_rewrite_large_diff_timeout"
        selected_owner = P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE
    elif kind in {"timeout", "hang"} and owner_layer in {
        P7_CONNECTION_E2E_OWNER_TEST_LEAK_GUARD,
        P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD,
    }:
        classification = "body_free_guard_overbroad_substring"
        selected_owner = owner_layer
    elif owner_layer != P7_CONNECTION_E2E_OWNER_UNKNOWN:
        classification = "timeout_owner_classified"
        selected_owner = owner_layer if owner_layer in _ALLOWED_OWNER_LAYERS else P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E
    else:
        classification = "timeout_owner_unknown"
        selected_owner = P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E

    return _entry(
        P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID,
        status="CLASSIFIED",
        classification=classification,
        owner_layer=selected_owner,
        summary_code="product_quality_connection_e2e_timeout_or_hang_isolated_not_closed",
        evidence_refs=(P7_CONNECTION_E2E_TEST_FILE, "p7_connection_e2e_timeout_isolation_result"),
        closure_requires_tests=(
            "product_quality_connection_e2e_returns_without_timeout",
            "p7_connection_timeout_isolation_release_handoff_keeps_blocker",
        ),
        observed_status=observed_status,
    )


def build_p7_red_closure_classification_matrix(
    *,
    connection_timeout_isolation_result: Mapping[str, Any] | None = None,
    positive_recovery_r0_r5_green_confirmed: bool = True,
    matrix_id: Any = P7_RED_CLOSURE_CLASSIFICATION_MATRIX_ID,
) -> dict[str, Any]:
    """Build body-free classification material for P7-RED-001..003."""

    isolation = (
        safe_mapping(connection_timeout_isolation_result)
        if connection_timeout_isolation_result is not None
        else build_p7_connection_e2e_timeout_isolation_result()
    )
    assert_p7_e2e_isolation_result_contract(isolation)
    assert_p7_no_body_payload_or_contract_mutation(isolation, source="p7_red_closure_classification.timeout_isolation")

    positive_status = "CLOSED" if positive_recovery_r0_r5_green_confirmed else "REPAIRED_PENDING_REGRESSION"
    red003_entry = _red003_entry_from_isolation(isolation)
    entries = [
        _entry(
            "P7-RED-001",
            status=positive_status,
            classification="runtime_route_shadowing",
            owner_layer="reader_relation_surface",
            summary_code="strict_recovery_signal_keys_separated_from_relation_type",
            evidence_refs=(
                P7_POSITIVE_RECOVERY_E2E_TEST_FILE,
                "tests/test_emlis_ai_positive_recovery_strict_relation_trace_20260613.py",
                "tests/test_emlis_ai_positive_recovery_r2_r3_contract_boundary_20260613.py",
                "tests/test_emlis_ai_positive_recovery_r4_r5_fail_closed_boundary_20260613.py",
            ),
            closure_requires_tests=(
                "positive_recovery_e2e_repair_passes_with_recovery_load_bridge",
                "strict_relation_type_signal_marker_contract_boundary",
            ),
            observed_status="closed_by_r0_r5_positive_recovery_suite" if positive_status == "CLOSED" else "pending_regression",
        ),
        _entry(
            "P7-RED-002",
            status=positive_status,
            classification="implementation_regression",
            owner_layer="fail_closed_boundary",
            summary_code="strict_relation_missing_after_repair_fail_closed_restored",
            evidence_refs=(
                P7_POSITIVE_RECOVERY_E2E_TEST_FILE,
                "tests/test_emlis_ai_positive_recovery_r4_r5_fail_closed_boundary_20260613.py",
            ),
            closure_requires_tests=(
                "positive_recovery_e2e_missing_surface_rejected",
                "positive_recovery_fail_closed_boundary_keeps_relation_not_expressed",
            ),
            observed_status="closed_by_r0_r5_positive_recovery_suite" if positive_status == "CLOSED" else "pending_regression",
        ),
        red003_entry,
    ]
    closed_refs = [entry["red_id"] for entry in entries if entry["status"] == "CLOSED"]
    unresolved_refs = [entry["red_id"] for entry in entries if entry["status"] != "CLOSED"]
    red003_closed = P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in set(closed_refs)
    matrix = {
        "schema_version": P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_RED_CLOSURE_CLASSIFICATION_STEP,
        "matrix_id": clean_identifier(matrix_id, default=P7_RED_CLOSURE_CLASSIFICATION_MATRIX_ID, max_length=160),
        "source_e2e_isolation_schema_version": clean_identifier(
            isolation.get("schema_version"), default=P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION, max_length=128
        ),
        "source_e2e_isolation_result_kind": clean_identifier(isolation.get("result_kind"), default="timeout", max_length=80),
        "source_e2e_observed_status": clean_identifier(isolation.get("observed_status"), default="TIMEOUT_ISOLATED", max_length=120),
        "entries": entries,
        "closed_red_refs": dedupe_identifiers(closed_refs, limit=20, max_length=80),
        "classified_red_refs": dedupe_identifiers([entry["red_id"] for entry in entries], limit=20, max_length=80),
        "unresolved_red_refs": dedupe_identifiers(unresolved_refs, limit=20, max_length=80),
        "release_blockers": dedupe_identifiers(unresolved_refs, limit=20, max_length=80),
        "release_blocker_red_refs": dedupe_identifiers(unresolved_refs, limit=20, max_length=80),
        "positive_recovery_red_closed": positive_status == "CLOSED",
        "product_quality_connection_timeout_classified": True,
        "product_quality_connection_timeout_isolated": P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in unresolved_refs,
        "product_quality_connection_timeout_closed": red003_closed,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "body_free": True,
        "public_contract": public_contract_flags(),
        "body_free_markers": _body_free_marker_set(),
    }
    assert_p7_red_closure_classification_matrix_contract(matrix)
    return matrix


def build_p7_red_closure_classification_index(matrix: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = safe_mapping(matrix) if matrix is not None else build_p7_red_closure_classification_matrix()
    assert_p7_red_closure_classification_matrix_contract(data)
    return {
        clean_identifier(entry.get("red_id"), max_length=80): safe_mapping(entry)
        for entry in (safe_mapping(raw) for raw in data.get("entries", []))
    }


def p7_closed_red_refs_from_classification(classification: Mapping[str, Any] | None = None) -> list[str]:
    data = safe_mapping(classification) if classification is not None else build_p7_red_closure_classification_matrix()
    if data:
        assert_p7_red_closure_classification_matrix_contract(data)
    return dedupe_identifiers(data.get("closed_red_refs"), limit=20, max_length=80)


def p7_unresolved_red_refs_from_classification(classification: Mapping[str, Any] | None = None) -> list[str]:
    data = safe_mapping(classification) if classification is not None else build_p7_red_closure_classification_matrix()
    if data:
        assert_p7_red_closure_classification_matrix_contract(data)
    return dedupe_identifiers(data.get("unresolved_red_refs"), limit=20, max_length=80)


def p7_release_blocker_red_refs_from_classification(classification: Mapping[str, Any] | None = None) -> list[str]:
    data = safe_mapping(classification) if classification is not None else build_p7_red_closure_classification_matrix()
    if data:
        assert_p7_red_closure_classification_matrix_contract(data)
    return dedupe_identifiers(data.get("release_blockers"), limit=20, max_length=80)


def assert_p7_red_closure_classification_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    if data.get("schema_version") != P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P7 RED closure classification matrix schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 RED closure classification matrix phase")
    if data.get("source_e2e_isolation_schema_version") != P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION:
        raise ValueError("P7 RED closure matrix must source the R6/R13 E2E isolation result")
    for key in ("release_allowed", "p7_complete", "p8_start_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7 RED closure matrix must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("P7 RED closure matrix must be body-free")
    entries = data.get("entries")
    if not isinstance(entries, list) or len(entries) != 3:
        raise ValueError("P7 RED closure matrix must classify exactly the three P7 RED ids")
    seen: set[str] = set()
    entry_by_red_id: dict[str, dict[str, Any]] = {}
    for raw_entry in entries:
        entry = safe_mapping(raw_entry)
        red_id = clean_identifier(entry.get("red_id"), max_length=80)
        if red_id not in set(_ALL_P7_RED_IDS) or red_id in seen:
            raise ValueError("P7 RED closure entries must be unique P7 RED ids")
        seen.add(red_id)
        entry_by_red_id[red_id] = entry
        if entry.get("schema_version") != P7_RED_CLOSURE_CLASSIFICATION_SCHEMA_VERSION:
            raise ValueError("P7 RED closure entry schema_version changed")
        status = clean_identifier(entry.get("status"), max_length=80)
        classification = clean_identifier(entry.get("classification"), max_length=120)
        owner_layer = clean_identifier(entry.get("owner_layer"), max_length=120)
        if status not in _ALLOWED_CLOSURE_STATUSES:
            raise ValueError(f"P7 RED closure status is not allowed: {red_id}")
        if classification not in _ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"P7 RED closure classification is not allowed: {red_id}")
        if owner_layer not in _ALLOWED_OWNER_LAYERS:
            raise ValueError(f"P7 RED closure owner layer is not allowed: {red_id}")
        closed = status == "CLOSED"
        for key, expected in (
            ("closure_allowed", closed),
            ("release_blocker_until_closed", not closed),
            ("release_blocker", not closed),
            ("body_free", True),
        ):
            if entry.get(key) is not expected:
                raise ValueError(f"P7 RED closure entry must keep {key}={expected}: {red_id}")
        for marker in (
            "raw_input_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "reviewer_free_text_included",
            "terminal_output_included",
        ):
            if entry.get(marker) is not False:
                raise ValueError(f"P7 RED closure entry must keep {marker}=False: {red_id}")
        assert_p7_no_body_payload_or_contract_mutation(entry, source=f"p7_red_closure_entry.{red_id}")
    if seen != set(_ALL_P7_RED_IDS):
        raise ValueError("P7 RED closure matrix must classify all initial P7 RED ids")
    closed_refs = set(dedupe_identifiers(data.get("closed_red_refs"), limit=20))
    unresolved_refs = set(dedupe_identifiers(data.get("unresolved_red_refs"), limit=20))
    release_blockers = set(dedupe_identifiers(data.get("release_blockers"), limit=20))
    if not set(P7_POSITIVE_RECOVERY_CLOSED_RED_IDS).issubset(closed_refs):
        raise ValueError("P7 RED closure matrix must mark Positive Recovery R0-R5 reds closed")
    if unresolved_refs - {P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID}:
        raise ValueError("P7 RED closure matrix must only leave P7-RED-003 unresolved")
    if release_blockers != unresolved_refs:
        raise ValueError("P7 RED closure matrix release blockers must match unresolved RED refs")
    red003_closed = P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in closed_refs
    red003_unresolved = P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID in unresolved_refs
    if red003_closed == red003_unresolved:
        raise ValueError("P7-RED-003 must be either closed or unresolved, not both/neither")
    red003_entry = entry_by_red_id[P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID]
    if red003_closed:
        if red003_entry.get("status") != "CLOSED":
            raise ValueError("P7-RED-003 closed refs must match CLOSED entry status")
        if data.get("product_quality_connection_timeout_closed") is not True:
            raise ValueError("P7 RED closure matrix must expose RED-003 timeout closed when closed")
        if data.get("product_quality_connection_timeout_isolated") is not False:
            raise ValueError("P7 RED closure matrix must not keep timeout isolated after RED-003 closure")
    else:
        if red003_entry.get("status") == "CLOSED":
            raise ValueError("P7-RED-003 unresolved refs must not have CLOSED entry status")
        if data.get("product_quality_connection_timeout_closed") is not False:
            raise ValueError("P7 RED closure matrix must keep timeout_closed=false while RED-003 unresolved")
        if data.get("product_quality_connection_timeout_isolated") is not True:
            raise ValueError("P7 RED closure matrix must keep timeout isolated while RED-003 unresolved")
    if data.get("positive_recovery_red_closed") is not True:
        raise ValueError("P7 RED closure matrix must expose Positive Recovery closed status")
    if data.get("product_quality_connection_timeout_classified") is not True:
        raise ValueError("P7 RED closure matrix must classify P7-RED-003")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_red_closure_matrix.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free_markers")), source="p7_red_closure_matrix.body_free_markers")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_red_closure_matrix")
    return True


__all__ = [
    "P7_CONNECTION_E2E_TEST_FILE",
    "P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION",
    "P7_POSITIVE_RECOVERY_CLOSED_RED_IDS",
    "P7_RED_CLOSURE_CLASSIFICATION_MATRIX_ID",
    "P7_RED_CLOSURE_CLASSIFICATION_MATRIX_SCHEMA_VERSION",
    "P7_RED_CLOSURE_CLASSIFICATION_SCHEMA_VERSION",
    "P7_RED_CLOSURE_CLASSIFICATION_STEP",
    "P7_UNRESOLVED_TIMEOUT_RED_IDS",
    "assert_p7_e2e_isolation_result_contract",
    "assert_p7_red_closure_classification_matrix_contract",
    "build_p7_connection_e2e_timeout_isolation_result",
    "build_p7_red_closure_classification_index",
    "build_p7_red_closure_classification_matrix",
    "p7_closed_red_refs_from_classification",
    "p7_release_blocker_red_refs_from_classification",
    "p7_unresolved_red_refs_from_classification",
]
