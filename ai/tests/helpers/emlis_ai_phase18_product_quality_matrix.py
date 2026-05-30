# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase18 test-only product-quality regression matrix for EmlisAI.

The helper is intentionally scoped to tests.  It records the Phase18-0 local
baseline as meta-only check results and exposes a small matrix builder for the
Phase18 product-quality release blockers.  It does not add public response keys,
does not carry raw input, and does not carry generated ``comment_text`` bodies.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Final

PHASE18_PRODUCT_QUALITY_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase18.product_quality_regression_matrix.v1"
)
PHASE18_PRODUCT_QUALITY_BASELINE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase18.local_baseline.v1"
)
PHASE18_PRODUCT_QUALITY_SOURCE_PHASE: Final = "Phase18_product_quality_stabilization"
PHASE18_PRODUCT_QUALITY_MATRIX_ID: Final = "emlis_phase18_product_quality_baseline"
PHASE18_LOCAL_BASELINE_ID: Final = "emlis_phase18_0_local_baseline"

STATUS_GREEN: Final = "green"
STATUS_RED: Final = "red"
STATUS_NOT_RUN: Final = "not_run"
STATUS_UNKNOWN: Final = "unknown"
_ALLOWED_STATUSES: Final = frozenset({STATUS_GREEN, STATUS_RED, STATUS_NOT_RUN, STATUS_UNKNOWN})

CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES: Final = "phase17_product_visible_five_fixtures"
CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH: Final = "complete_initial_candidate_generation_path"
CHECK_LOW_INFORMATION_PUBLIC_REPAIR: Final = "low_information_public_repair"
CHECK_DAILY_UNPLEASANT_MODE_CONTEXT: Final = "daily_unpleasant_mode_context"
CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY: Final = "observation_structure_meta_only_boundary"
CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY: Final = "diagnostic_classification_taxonomy"
CHECK_VISIBLE_READABILITY_QUALITY: Final = "visible_readability_quality"
CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT: Final = "rn_passed_comment_text_contract"

PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS: Final = (
    CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES,
    CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH,
    CHECK_LOW_INFORMATION_PUBLIC_REPAIR,
    CHECK_DAILY_UNPLEASANT_MODE_CONTEXT,
    CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY,
    CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY,
    CHECK_VISIBLE_READABILITY_QUALITY,
    CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT,
)

_PHASE18_REQUIRED_CHECKS: Final = (
    {
        "check_id": CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES,
        "phase_owner": "Phase18-0",
        "category": "phase17_fixture_green",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
    {
        "check_id": CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH,
        "phase_owner": "Phase18-3",
        "category": "complete_initial_candidate_path_regressed",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
    {
        "check_id": CHECK_LOW_INFORMATION_PUBLIC_REPAIR,
        "phase_owner": "Phase18-4",
        "category": "low_information_public_repair_regressed",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
    {
        "check_id": CHECK_DAILY_UNPLEASANT_MODE_CONTEXT,
        "phase_owner": "Phase18-5",
        "category": "daily_unpleasant_mode_context_regressed",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
    {
        "check_id": CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY,
        "phase_owner": "Phase18-6",
        "category": "meta_only_boundary_regressed",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
    {
        "check_id": CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY,
        "phase_owner": "Phase18-7",
        "category": "diagnostic_classification_regressed",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
    {
        "check_id": CHECK_VISIBLE_READABILITY_QUALITY,
        "phase_owner": "Phase18-8",
        "category": "visible_readability_regressed",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
    {
        "check_id": CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT,
        "phase_owner": "Phase18-10",
        "category": "rn_contract_regressed",
        "required_status": STATUS_GREEN,
        "blocks_release": True,
    },
)

# Historical Phase18-0 baseline observed in the local snapshot before repairing
# Phase18-2 and later blockers.  The entries intentionally contain only counts,
# status codes, and test-suite identifiers; they do not carry user memo text or
# generated reply bodies.
_PHASE18_0_BASELINE_OBSERVATIONS: Final = {
    CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES: {
        "observed_status": STATUS_GREEN,
        "suite_id": "phase16_17_core_and_product_visible",
        "passed": 33,
        "failed": 0,
        "warnings": 1,
    },
    CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH: {
        "observed_status": STATUS_RED,
        "suite_id": "complete_initial_entry_route_and_step7_integration",
        "passed": 9,
        "failed": 5,
        "failure_family": "candidate_generation_path_not_preserved",
    },
    CHECK_LOW_INFORMATION_PUBLIC_REPAIR: {
        "observed_status": STATUS_RED,
        "suite_id": "low_information_red_cases_and_specificity_policy",
        "passed": 6,
        "failed": 4,
        "failure_family": "public_low_information_repair_not_applied",
    },
    CHECK_DAILY_UNPLEASANT_MODE_CONTEXT: {
        "observed_status": STATUS_RED,
        "suite_id": "daily_unpleasant_reception_surface_quality",
        "passed": 1,
        "failed": 2,
        "failure_family": "daily_unpleasant_mode_context_not_applied",
    },
    CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY: {
        "observed_status": STATUS_RED,
        "suite_id": "observation_structure_phase6_meta_only_contract",
        "passed": 3,
        "failed": 6,
        "failure_family": "surface_policy_key_leak",
    },
    CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY: {
        "observed_status": STATUS_RED,
        "suite_id": "diagnostic_summary_and_v2",
        "passed": 28,
        "failed": 5,
        "failure_family": "diagnostic_status_and_stage_taxonomy_drift",
    },
    CHECK_VISIBLE_READABILITY_QUALITY: {
        "observed_status": STATUS_NOT_RUN,
        "suite_id": "phase18_visible_readability_quality",
        "passed": 0,
        "failed": 0,
        "failure_family": "reserved_for_phase18_8",
    },
    CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT: {
        "observed_status": STATUS_GREEN,
        "suite_id": "rn_screen_contracts",
        "passed": 32,
        "failed": 0,
        "warnings": 0,
    },
}

_FALSE_PUBLIC_CONTRACT: Final = {
    "public_response_key_added": False,
    "observation_text_key_added": False,
    "reception_text_key_added": False,
    "rn_visible_contract_changed": False,
    "db_physical_name_changed": False,
    "api_route_changed": False,
    "raw_input_included": False,
    "raw_text_included": False,
    "comment_text_body_included": False,
    "generated_candidate_text_included": False,
    "surface_policy_included": False,
}

_FALSE_GATE_CONTRACT: Final = {
    "display_gate_relaxed": False,
    "grounding_gate_relaxed": False,
    "reader_gate_relaxed": False,
    "template_gate_relaxed": False,
}

_FALSE_IMPLEMENTATION_CONTRACT: Final = {
    "external_ai_added": False,
    "local_llm_added": False,
    "runtime_completed_reply_templates_added": False,
    "case_id_runtime_branch_added": False,
    "rn_production_ui_changed": False,
}

_FORBIDDEN_META_KEYS: Final = frozenset(
    {
        "raw_input",
        "raw_text",
        "input_text",
        "memo",
        "comment_text",
        "observation_text",
        "reception_text",
        "generated_text",
        "candidate_text",
        "surface_policy",
        "definition",
        "evidence_requirements",
        "allowed_inference",
        "forbidden_inference",
        "default_direction",
        "strong_hand_direction",
        "notes",
        "body",
        "text",
    }
)
_TRUE_PUBLIC_OR_GATE_FLAGS: Final = frozenset(
    {
        "public_response_key_added",
        "observation_text_key_added",
        "reception_text_key_added",
        "rn_visible_contract_changed",
        "db_physical_name_changed",
        "api_route_changed",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "generated_candidate_text_included",
        "surface_policy_included",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "external_ai_added",
        "local_llm_added",
        "runtime_completed_reply_templates_added",
        "case_id_runtime_branch_added",
        "rn_production_ui_changed",
    }
)


def build_phase18_product_quality_regression_matrix() -> dict[str, Any]:
    """Return the required Phase18 product-quality matrix definition."""

    return {
        "schema_version": PHASE18_PRODUCT_QUALITY_MATRIX_SCHEMA_VERSION,
        "source_phase": PHASE18_PRODUCT_QUALITY_SOURCE_PHASE,
        "matrix_id": PHASE18_PRODUCT_QUALITY_MATRIX_ID,
        "checks": [dict(check) for check in _PHASE18_REQUIRED_CHECKS],
        "public_contract": dict(_FALSE_PUBLIC_CONTRACT),
        "gate_policy": dict(_FALSE_GATE_CONTRACT),
        "implementation_contract": dict(_FALSE_IMPLEMENTATION_CONTRACT),
    }


def build_phase18_0_local_baseline_observations() -> dict[str, Any]:
    """Return the historical local baseline captured at Phase18-0."""

    return {
        "schema_version": PHASE18_PRODUCT_QUALITY_BASELINE_SCHEMA_VERSION,
        "source_phase": PHASE18_PRODUCT_QUALITY_SOURCE_PHASE,
        "baseline_id": PHASE18_LOCAL_BASELINE_ID,
        "observations": {
            check_id: dict(observation)
            for check_id, observation in _PHASE18_0_BASELINE_OBSERVATIONS.items()
        },
        "public_contract": dict(_FALSE_PUBLIC_CONTRACT),
        "gate_policy": dict(_FALSE_GATE_CONTRACT),
        "implementation_contract": dict(_FALSE_IMPLEMENTATION_CONTRACT),
    }


def build_phase18_product_quality_matrix_with_observations(
    observed_status_by_check_id: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Attach observed statuses to the matrix and compute release readiness.

    Passing ``None`` uses the Phase18-0 local baseline.  Callers may pass a
    future live-status mapping after later Phase18 repairs without changing the
    public contract shape.
    """

    matrix = build_phase18_product_quality_regression_matrix()
    if observed_status_by_check_id is None:
        observations = build_phase18_0_local_baseline_observations()["observations"]
    else:
        observations = _observations_from_status_mapping(observed_status_by_check_id)
    _validate_observation_ids(observations)

    check_by_id = {str(check["check_id"]): check for check in matrix["checks"]}
    enriched_checks: list[dict[str, Any]] = []
    blocking_not_green: list[str] = []
    green_check_ids: list[str] = []
    red_check_ids: list[str] = []
    not_run_check_ids: list[str] = []
    unknown_check_ids: list[str] = []

    for check_id in PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS:
        check = dict(check_by_id[check_id])
        observation = dict(observations[check_id])
        observed_status = _normalize_status(observation.get("observed_status"))
        required_status = str(check["required_status"])
        check["observed_status"] = observed_status
        check["meets_required_status"] = observed_status == required_status
        check["observation"] = observation
        enriched_checks.append(check)

        if observed_status == STATUS_GREEN:
            green_check_ids.append(check_id)
        elif observed_status == STATUS_RED:
            red_check_ids.append(check_id)
        elif observed_status == STATUS_NOT_RUN:
            not_run_check_ids.append(check_id)
        else:
            unknown_check_ids.append(check_id)
        if bool(check.get("blocks_release")) and observed_status != required_status:
            blocking_not_green.append(check_id)

    matrix["checks"] = enriched_checks
    matrix["baseline"] = {
        "schema_version": PHASE18_PRODUCT_QUALITY_BASELINE_SCHEMA_VERSION,
        "baseline_id": PHASE18_LOCAL_BASELINE_ID,
        "used_historical_phase18_0_baseline": observed_status_by_check_id is None,
    }
    matrix["summary"] = {
        "schema_version": "cocolon.emlis.phase18.product_quality_regression_summary.v1",
        "source_phase": PHASE18_PRODUCT_QUALITY_SOURCE_PHASE,
        "release_ready": not blocking_not_green,
        "blocking_not_green_check_ids": blocking_not_green,
        "green_check_ids": green_check_ids,
        "red_check_ids": red_check_ids,
        "not_run_check_ids": not_run_check_ids,
        "unknown_check_ids": unknown_check_ids,
        "required_check_count": len(PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS),
        "green_check_count": len(green_check_ids),
        "red_check_count": len(red_check_ids),
        "not_run_check_count": len(not_run_check_ids),
        "unknown_check_count": len(unknown_check_ids),
        "public_contract": dict(_FALSE_PUBLIC_CONTRACT),
        "gate_policy": dict(_FALSE_GATE_CONTRACT),
    }
    return matrix


def assert_phase18_product_quality_matrix_meta_only(payload: Any) -> None:
    """Assert that a Phase18 matrix payload stays meta-only and contract-safe."""

    _assert_no_forbidden_keys(payload)
    _assert_no_true_contract_flags(payload)


def _observations_from_status_mapping(observed_status_by_check_id: Mapping[str, str]) -> dict[str, dict[str, Any]]:
    _validate_observation_ids(observed_status_by_check_id)
    observations: dict[str, dict[str, Any]] = {}
    for check_id in PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS:
        observed_status = _normalize_status(observed_status_by_check_id.get(check_id))
        observations[check_id] = {
            "observed_status": observed_status,
            "suite_id": f"{check_id}_live_status",
            "passed": 0,
            "failed": 0 if observed_status == STATUS_GREEN else 1,
        }
    return observations


def _validate_observation_ids(observations: Mapping[str, Any]) -> None:
    expected = set(PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS)
    actual = set(observations.keys())
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise ValueError(
            "Phase18 product-quality observations must match required check ids: "
            f"missing={missing}, unknown={unknown}"
        )


def _normalize_status(status: Any) -> str:
    value = str(status or STATUS_UNKNOWN)
    if value not in _ALLOWED_STATUSES:
        raise ValueError(f"Unsupported Phase18 product-quality status: {value}")
    return value


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            assert str(key) not in _FORBIDDEN_META_KEYS, key
            _assert_no_forbidden_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_forbidden_keys(item)


def _assert_no_true_contract_flags(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TRUE_PUBLIC_OR_GATE_FLAGS:
                assert item is False, key
            _assert_no_true_contract_flags(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_true_contract_flags(item)


__all__ = [
    "CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH",
    "CHECK_DAILY_UNPLEASANT_MODE_CONTEXT",
    "CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY",
    "CHECK_LOW_INFORMATION_PUBLIC_REPAIR",
    "CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY",
    "CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES",
    "CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT",
    "CHECK_VISIBLE_READABILITY_QUALITY",
    "PHASE18_PRODUCT_QUALITY_BASELINE_SCHEMA_VERSION",
    "PHASE18_PRODUCT_QUALITY_MATRIX_ID",
    "PHASE18_PRODUCT_QUALITY_MATRIX_SCHEMA_VERSION",
    "PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS",
    "PHASE18_PRODUCT_QUALITY_SOURCE_PHASE",
    "STATUS_GREEN",
    "STATUS_NOT_RUN",
    "STATUS_RED",
    "STATUS_UNKNOWN",
    "assert_phase18_product_quality_matrix_meta_only",
    "build_phase18_0_local_baseline_observations",
    "build_phase18_product_quality_matrix_with_observations",
    "build_phase18_product_quality_regression_matrix",
]
