# -*- coding: utf-8 -*-
"""P7 body-free timeout isolation / R13 observation material for P7-RED-003.

Product Quality Connection E2E is intentionally kept outside the P7 core green
condition.  This module records timeout/hang/fail/pass outcomes as isolated,
body-free observation material without carrying terminal output or public
response bodies.  R13-6 adds the post body-free-guard observation path used by
R13-7 classification, while keeping P7 complete / P8 start / release allowed
false.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_p7_no_body_payload_or_contract_mutation,
    clean_identifier,
    dedupe_identifiers,
    safe_mapping,
)

P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION: Final = "cocolon.emlis.p7.e2e_isolation_result.v1"
P7_CONNECTION_E2E_ISOLATION_RESULT_ID: Final = "p7_e2e_isolation:product_quality_connection:20260613"
P7_CONNECTION_E2E_TEST_FILE: Final = "tests/test_emlis_ai_complete_product_quality_connection_e2e.py"
P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID: Final = "P7-RED-003"
P7_CONNECTION_E2E_OBSERVATION_STEP: Final = "P7-R13-6_ProductQualityConnectionTimeoutObservation_20260613"

P7_CONNECTION_E2E_OWNER_UNKNOWN: Final = "unknown"
P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD: Final = "product_quality_scorecard_body_free_guard"
P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY: Final = "product_quality_scorecard_body_free_boundary"
P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE: Final = "pytest_assertion_rewrite"
P7_CONNECTION_E2E_OWNER_TEST_LEAK_GUARD: Final = "test_leak_guard"
P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E: Final = "product_quality_connection_e2e"

_ALLOWED_RESULT_KINDS: Final[frozenset[str]] = frozenset({"timeout", "hang", "failed", "passed", "not_run"})
_ALLOWED_OBSERVED_STATUSES: Final[frozenset[str]] = frozenset(
    {"TIMEOUT_ISOLATED", "HANG_ISOLATED", "FAILED_ISOLATED", "PASSED_ISOLATED", "NOT_RUN"}
)
_ALLOWED_OWNER_LAYERS: Final[frozenset[str]] = frozenset(
    {
        P7_CONNECTION_E2E_OWNER_UNKNOWN,
        P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD,
        P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY,
        P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE,
        P7_CONNECTION_E2E_OWNER_TEST_LEAK_GUARD,
        P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E,
    }
)
_OBSERVED_STATUS_BY_RESULT_KIND: Final[dict[str, str]] = {
    "timeout": "TIMEOUT_ISOLATED",
    "hang": "HANG_ISOLATED",
    "failed": "FAILED_ISOLATED",
    "passed": "PASSED_ISOLATED",
    "not_run": "NOT_RUN",
}
_RESULT_KIND_ALIASES: Final[dict[str, str]] = {
    "timeout_preserved": "timeout",
    "timeout_isolated": "timeout",
    "exit_status_124": "timeout",
    "hang_preserved": "hang",
    "hang_isolated": "hang",
    "failed_preserved": "failed",
    "red_preserved": "failed",
    "red_ledgered": "failed",
    "failed_isolated": "failed",
    "passed_closed": "passed",
    "passed_isolated": "passed",
    "green": "passed",
    "not_run": "not_run",
    "unconfirmed": "not_run",
}


def _normalize_result_kind(value: Any) -> str:
    raw = clean_identifier(value, default="timeout", max_length=80).lower()
    return _RESULT_KIND_ALIASES.get(raw, raw if raw in _ALLOWED_RESULT_KINDS else "failed")


def _normalize_owner_layer(value: Any, *, result_kind: str) -> str:
    raw = clean_identifier(value, default=P7_CONNECTION_E2E_OWNER_UNKNOWN, max_length=120)
    if raw in _ALLOWED_OWNER_LAYERS:
        return raw
    if result_kind == "passed":
        return P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD
    if result_kind == "failed":
        return P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E
    return P7_CONNECTION_E2E_OWNER_UNKNOWN


def _bounded_timeout_budget(value: Any) -> int:
    try:
        if value is None or isinstance(value, bool):
            raise ValueError
        budget = int(value)
    except (TypeError, ValueError):
        return 30
    return budget if 1 <= budget <= 600 else 30


def _summary_code(*, result_kind: str, owner_layer: str) -> str:
    if result_kind == "passed":
        return "product_quality_connection_e2e_body_free_guard_structured_and_default_pytest_passed"
    if result_kind == "failed" and owner_layer == P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY:
        return "product_quality_connection_e2e_returns_compact_body_free_violation_not_closed"
    if result_kind == "failed":
        return "product_quality_connection_e2e_returns_compact_failure_not_closed"
    if result_kind in {"timeout", "hang"} and owner_layer == P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE:
        return "product_quality_connection_e2e_pytest_assertion_rewrite_timeout_isolated"
    if result_kind in {"timeout", "hang"}:
        return "product_quality_connection_e2e_timeout_or_hang_isolated_not_closed"
    return "product_quality_connection_e2e_not_run_isolated"


def build_p7_connection_e2e_timeout_isolation_result(
    *,
    result_kind: Any = "timeout",
    timeout_budget_sec: Any = 30,
    last_completed_stage: Any = "unknown",
    owner_layer: Any = "unknown",
    result_id: Any = P7_CONNECTION_E2E_ISOLATION_RESULT_ID,
) -> dict[str, Any]:
    """Build body-free isolation / observation material for Product Quality Connection E2E."""

    kind = _normalize_result_kind(result_kind)
    observed_status = _OBSERVED_STATUS_BY_RESULT_KIND[kind]
    normalized_owner_layer = _normalize_owner_layer(owner_layer, result_kind=kind)
    release_blocker = kind in {"timeout", "hang", "failed", "not_run"}
    red_refs = [P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID] if release_blocker else []
    timeout_refs = [P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID] if kind in {"timeout", "hang", "not_run"} else []
    timeout_resolved = kind == "passed"
    result = {
        "schema_version": P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION,
        "result_id": clean_identifier(result_id, default=P7_CONNECTION_E2E_ISOLATION_RESULT_ID, max_length=160),
        "phase": P7_PHASE,
        "observation_step": P7_CONNECTION_E2E_OBSERVATION_STEP,
        "source_test_file": P7_CONNECTION_E2E_TEST_FILE,
        "command_kind": "pytest_timeout",
        "timeout_budget_sec": _bounded_timeout_budget(timeout_budget_sec),
        "result_kind": kind,
        "observed_status": observed_status,
        "summary_code": _summary_code(result_kind=kind, owner_layer=normalized_owner_layer),
        "last_completed_stage": clean_identifier(last_completed_stage, default="unknown", max_length=120),
        "owner_layer": normalized_owner_layer,
        "red_refs": red_refs,
        "hold_refs": [],
        "unresolved_timeout_refs": timeout_refs,
        "release_blocker": release_blocker,
        "body_free_guard_contract_connected": kind == "passed" or "body_free" in normalized_owner_layer,
        "default_pytest_timeout_resolved": timeout_resolved,
        "r13_closure_candidate": timeout_resolved,
        "can_join_p7_core_green": False,
        "can_claim_full_backend_suite_green": False,
        "full_backend_suite_green_confirmed": False,
        "release_decision_input_ready": False,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "terminal_output_body_included": False,
        "terminal_output_included": False,
    }
    assert_p7_e2e_isolation_result_contract(result)
    return result


def build_p7_connection_e2e_r13_passed_observation_result(
    *,
    timeout_budget_sec: Any = 30,
    result_id: Any = "p7_e2e_observation:product_quality_connection:r13_6_passed:20260613",
) -> dict[str, Any]:
    """Build the R13-6 observation for the repaired Product Quality Connection E2E.

    This is the explicit observation consumed by R13-7 classification.  The
    older default timeout isolation path is kept for runner/release handoff
    consumers until R13-8/R13-9 update those materials.
    """

    return build_p7_connection_e2e_timeout_isolation_result(
        result_kind="passed",
        timeout_budget_sec=timeout_budget_sec,
        last_completed_stage="product_quality_connection_e2e_default_pytest_passed",
        owner_layer=P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD,
        result_id=result_id,
    )


def build_p7_connection_e2e_timeout_isolation_material(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return build_p7_connection_e2e_timeout_isolation_result(*args, **kwargs)


def assert_p7_e2e_isolation_result_contract(result: Mapping[str, Any]) -> bool:
    data = safe_mapping(result)
    if data.get("schema_version") != P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION:
        raise ValueError("unexpected P7 E2E isolation result schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("P7 E2E isolation result must stay in P7 phase")
    if data.get("observation_step") != P7_CONNECTION_E2E_OBSERVATION_STEP:
        raise ValueError("P7 E2E isolation result must carry the R13-6 observation step")
    if data.get("source_test_file") != P7_CONNECTION_E2E_TEST_FILE:
        raise ValueError("P7 E2E isolation result must isolate the connection E2E source")
    if data.get("command_kind") != "pytest_timeout":
        raise ValueError("P7 E2E isolation result must record pytest timeout execution")
    kind = clean_identifier(data.get("result_kind"), max_length=80)
    if kind not in _ALLOWED_RESULT_KINDS:
        raise ValueError("P7 E2E isolation result has unsupported result_kind")
    status = clean_identifier(data.get("observed_status"), max_length=80)
    if status not in _ALLOWED_OBSERVED_STATUSES or status != _OBSERVED_STATUS_BY_RESULT_KIND[kind]:
        raise ValueError("P7 E2E isolation observed_status must match result_kind")
    owner_layer = clean_identifier(data.get("owner_layer"), max_length=120)
    if owner_layer not in _ALLOWED_OWNER_LAYERS:
        raise ValueError("P7 E2E isolation owner_layer is not supported")
    timeout_budget = data.get("timeout_budget_sec")
    if not isinstance(timeout_budget, int) or not 1 <= timeout_budget <= 600:
        raise ValueError("P7 E2E isolation timeout budget must be explicit and bounded")
    for key in (
        "can_join_p7_core_green",
        "can_claim_full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "release_decision_input_ready",
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "raw_input_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "terminal_output_body_included",
        "terminal_output_included",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7 E2E isolation result must keep {key}=False")
    if data.get("body_free") is not True:
        raise ValueError("P7 E2E isolation result must be body-free")
    red_refs = dedupe_identifiers(data.get("red_refs"), limit=20)
    timeout_refs = dedupe_identifiers(data.get("unresolved_timeout_refs"), limit=20)
    if kind in {"timeout", "hang", "failed", "not_run"}:
        if data.get("release_blocker") is not True:
            raise ValueError("P7 non-passed E2E isolation result must remain a release blocker")
        if P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID not in red_refs:
            raise ValueError("P7-RED-003 must remain on non-passed connection E2E isolation results")
        if data.get("r13_closure_candidate") is not False:
            raise ValueError("P7 non-passed E2E isolation result must not be a R13 closure candidate")
        if data.get("default_pytest_timeout_resolved") is not False:
            raise ValueError("P7 non-passed E2E isolation result must not claim timeout resolved")
    if kind in {"timeout", "hang", "not_run"} and P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID not in timeout_refs:
        raise ValueError("P7 timeout/hang isolation must expose unresolved_timeout_refs")
    if kind == "passed":
        if data.get("release_blocker") is not False:
            raise ValueError("P7 passed isolated result must not remain a timeout release blocker")
        if red_refs or timeout_refs:
            raise ValueError("P7 passed isolated result must not carry unresolved RED or timeout refs")
        if data.get("default_pytest_timeout_resolved") is not True or data.get("r13_closure_candidate") is not True:
            raise ValueError("P7 passed isolated result must expose R13 closure-candidate markers")
        if owner_layer != P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD:
            raise ValueError("P7 passed isolated result must be owned by the body-free guard repair")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_e2e_isolation_result")
    return True


__all__ = [
    "P7_CONNECTION_E2E_ISOLATION_RESULT_ID",
    "P7_CONNECTION_E2E_OBSERVATION_STEP",
    "P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_BOUNDARY",
    "P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_BODY_FREE_GUARD",
    "P7_CONNECTION_E2E_OWNER_PRODUCT_QUALITY_CONNECTION_E2E",
    "P7_CONNECTION_E2E_OWNER_PYTEST_ASSERTION_REWRITE",
    "P7_CONNECTION_E2E_OWNER_TEST_LEAK_GUARD",
    "P7_CONNECTION_E2E_OWNER_UNKNOWN",
    "P7_CONNECTION_E2E_TEST_FILE",
    "P7_E2E_ISOLATION_RESULT_SCHEMA_VERSION",
    "P7_PRODUCT_QUALITY_CONNECTION_TIMEOUT_RED_ID",
    "assert_p7_e2e_isolation_result_contract",
    "build_p7_connection_e2e_r13_passed_observation_result",
    "build_p7_connection_e2e_timeout_isolation_material",
    "build_p7_connection_e2e_timeout_isolation_result",
]
