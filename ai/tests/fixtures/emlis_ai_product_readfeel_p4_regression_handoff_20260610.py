# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fixture connector for P4-10 regression / P5 hold handoff.

The fixture intentionally carries suite identifiers and status counts only.  It
does not retain command output, rendered Emlis text, raw inputs, history text,
or reviewer free-text notes.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p4_regression_handoff import (
    P4_10_OPTIONAL_LEDGER_SUITES_20260610,
    P4_10_REQUIRED_REGRESSION_SUITES_20260610,
    PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_PROFILE_20260610,
    PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610,
    PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610,
    STATUS_NOT_EXECUTED,
    STATUS_PASSED,
    STATUS_TIMEOUT,
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610,
    build_product_readfeel_p4_regression_handoff_20260610,
    build_product_readfeel_p4_regression_handoff_public_summary_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_ratings_review_20260610 import (
    SCENARIO_P5_READY as P4_9_SCENARIO_P5_READY,
    SCENARIO_REMAINING_BLOCKERS as P4_9_SCENARIO_REMAINING_BLOCKERS,
    SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD as P4_9_SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD,
    build_product_readfeel_p4_ratings_review_from_target_selection_20260610,
)

SCENARIO_GREEN_REGRESSION_P5_HOLD = "green_regression_p5_hold"
SCENARIO_GREEN_REGRESSION_P5_READY = "green_regression_p5_ready"
SCENARIO_REMAINING_BLOCKERS = "remaining_blockers"
SCENARIO_BACKEND_ONLY_RN_NOT_EXECUTED = "backend_only_rn_not_executed"
SCENARIO_TIMEOUT_LEDGER = "timeout_ledger"


def _suite_status(
    suite_id: str,
    *,
    status: str = STATUS_PASSED,
    required: bool | None = None,
    passed_count: int = 1,
    failed_count: int = 0,
    warning_count: int = 0,
    reason_codes: Sequence[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "cocolon.emlis.product_readfeel.p4.fixture_regression_suite_status.20260610.v1",
        "suite_id": suite_id,
        "status": status,
        "required": suite_id in P4_10_REQUIRED_REGRESSION_SUITES_20260610 if required is None else required,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "warning_count": warning_count,
        "reason_codes": list(reason_codes or []),
        "body_free_suite_status_only": True,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "candidate_body_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "public_release_applied": False,
        "gate_relaxed": False,
    }


def build_product_readfeel_p4_regression_handoff_green_suite_statuses_20260610(
    *,
    include_rn_contract: bool = True,
    include_optional_timeouts: bool = True,
) -> list[dict[str, Any]]:
    statuses: list[dict[str, Any]] = []
    count_by_suite = {
        "p4_new_tests": 52,
        "p3_product_readfeel_regression": 65,
        "product_readfeel_surface_guard_subset": 93,
        "public_recovery_limited_source_unavailable_subset": 42,
        "user_label_connection_boundary_subset": 92,
        "backend_contract": 4,
        "display_contract": 5,
        "two_stage_e2e": 6,
        "rn_contract": 36,
    }
    for suite_id in P4_10_REQUIRED_REGRESSION_SUITES_20260610:
        if suite_id == "rn_contract" and not include_rn_contract:
            continue
        statuses.append(
            _suite_status(
                suite_id,
                passed_count=count_by_suite.get(suite_id, 1),
                warning_count=3 if suite_id == "backend_contract" else (1 if suite_id in {"two_stage_e2e", "public_recovery_limited_source_unavailable_subset", "user_label_connection_boundary_subset"} else 0),
            )
        )
    if include_optional_timeouts:
        statuses.extend(
            [
                _suite_status(
                    "p3_p4_combined_command",
                    status=STATUS_TIMEOUT,
                    required=False,
                    passed_count=0,
                    reason_codes=["combined_command_timeout_recorded"],
                ),
                _suite_status(
                    "backend_contract_display_two_stage_combined",
                    status=STATUS_TIMEOUT,
                    required=False,
                    passed_count=0,
                    reason_codes=["combined_command_timeout_recorded"],
                ),
            ]
        )
    return statuses


def build_product_readfeel_p4_regression_handoff_suite_statuses_20260610(
    *,
    scenario: str = SCENARIO_GREEN_REGRESSION_P5_HOLD,
) -> list[dict[str, Any]]:
    if scenario == SCENARIO_BACKEND_ONLY_RN_NOT_EXECUTED:
        statuses = build_product_readfeel_p4_regression_handoff_green_suite_statuses_20260610(
            include_rn_contract=False,
            include_optional_timeouts=True,
        )
        statuses.append(
            _suite_status(
                "rn_contract",
                status=STATUS_NOT_EXECUTED,
                required=True,
                passed_count=0,
                reason_codes=["rn_workspace_not_in_backend_only_snapshot"],
            )
        )
        return statuses
    if scenario == SCENARIO_TIMEOUT_LEDGER:
        statuses = build_product_readfeel_p4_regression_handoff_green_suite_statuses_20260610(
            include_rn_contract=True,
            include_optional_timeouts=True,
        )
        statuses.append(
            _suite_status(
                P4_10_OPTIONAL_LEDGER_SUITES_20260610[-1],
                status=STATUS_TIMEOUT,
                required=False,
                passed_count=0,
                reason_codes=["full_backend_suite_timeout_recorded"],
            )
        )
        return statuses
    return build_product_readfeel_p4_regression_handoff_green_suite_statuses_20260610(
        include_rn_contract=True,
        include_optional_timeouts=True,
    )


def _p4_9_scenario_for_p4_10(scenario: str) -> str:
    if scenario == SCENARIO_GREEN_REGRESSION_P5_READY:
        return P4_9_SCENARIO_P5_READY
    if scenario == SCENARIO_REMAINING_BLOCKERS:
        return P4_9_SCENARIO_REMAINING_BLOCKERS
    return P4_9_SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD


def build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610(
    *,
    scenario: str = SCENARIO_GREEN_REGRESSION_P5_HOLD,
    regression_suite_statuses: Sequence[Mapping[str, Any] | None] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    ratings_review = build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
        scenario=_p4_9_scenario_for_p4_10(scenario),
        run_id=run_id or f"p4_10_p4_9_source_{scenario}",
    )
    suite_statuses = list(regression_suite_statuses or build_product_readfeel_p4_regression_handoff_suite_statuses_20260610(
        scenario=scenario,
    ))
    handoff = build_product_readfeel_p4_regression_handoff_20260610(
        p4_ratings_review=ratings_review,
        regression_suite_statuses=suite_statuses,
        run_id=run_id or f"p4_10_regression_handoff_{scenario}",
    )
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(handoff)
    return handoff


def build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
    *,
    scenario: str = SCENARIO_GREEN_REGRESSION_P5_HOLD,
    regression_suite_statuses: Sequence[Mapping[str, Any] | None] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    handoff = build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610(
        scenario=scenario,
        regression_suite_statuses=regression_suite_statuses,
        run_id=run_id,
    )
    return build_product_readfeel_p4_regression_handoff_public_summary_20260610(handoff)


def dump_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
    *,
    scenario: str = SCENARIO_GREEN_REGRESSION_P5_HOLD,
    regression_suite_statuses: Sequence[Mapping[str, Any] | None] | None = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
        scenario=scenario,
        regression_suite_statuses=regression_suite_statuses,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610",
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610",
    "PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_PROFILE_20260610",
    "SCENARIO_GREEN_REGRESSION_P5_HOLD",
    "SCENARIO_GREEN_REGRESSION_P5_READY",
    "SCENARIO_REMAINING_BLOCKERS",
    "SCENARIO_BACKEND_ONLY_RN_NOT_EXECUTED",
    "SCENARIO_TIMEOUT_LEDGER",
    "assert_product_readfeel_p4_regression_handoff_meta_only_20260610",
    "build_product_readfeel_p4_regression_handoff_green_suite_statuses_20260610",
    "build_product_readfeel_p4_regression_handoff_suite_statuses_20260610",
    "build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610",
    "build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610",
    "dump_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610",
]
