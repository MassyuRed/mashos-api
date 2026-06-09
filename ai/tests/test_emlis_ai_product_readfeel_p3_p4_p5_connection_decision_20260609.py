# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_first_repair_design import build_product_readfeel_p3_first_repair_design_20260609
from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_BLOCKED_BY_P2_RED,
    DECISION_BLOCKED_BY_REGRESSION,
    DECISION_NEEDS_BASELINE_EVIDENCE,
    DECISION_P4_NEXT_P5_HOLD,
    DECISION_P5_READY_AFTER_P4,
    PHASE_P4_FAMILY_TUNING,
    PHASE_P5_USER_LABEL_CONNECTION,
    PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609,
    PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609,
    PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609,
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609,
    build_product_readfeel_p3_p4_p5_connection_decision_20260609,
    dump_product_readfeel_p3_p4_p5_connection_public_summary_20260609,
)
from emlis_ai_product_readfeel_p3_regression import (
    STATUS_FAILED,
    build_product_readfeel_p3_regression_green_fixture_results_20260609,
    build_product_readfeel_p3_regression_result_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
)
from fixtures.emlis_ai_product_readfeel_p3_p4_p5_connection_decision_20260609 import (
    build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609,
    dump_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609,
)


def _first_repair_design_with_runtime_targets() -> dict[str, object]:
    return build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_items=[
            {
                "priority": 1,
                "blocker_id": "rich_input_low_information_overroute",
                "blocker_category": "readfeel_gap",
                "verdict_layer": VERDICT_LAYER_P3_REPAIR_REQUIRED,
                "case_count": 6,
                "families": ["daily_unpleasant", "mixed_emotion"],
                "sample_case_ids": ["p3-daily-unpleasant-001", "p3-mixed-emotion-002"],
                "reason_codes": ["rich_input_low_information_overroute", "input_core_missing"],
                "target_layers": ["input_material_bundle", "public_surface_requirement"],
            },
            {
                "priority": 2,
                "blocker_id": "generic_reception_surface",
                "blocker_category": "readfeel_gap",
                "verdict_layer": VERDICT_LAYER_P3_REPAIR_REQUIRED,
                "case_count": 4,
                "families": ["structure_question"],
                "sample_case_ids": ["p3-structure-question-003"],
                "reason_codes": ["generic_reception_surface", "family_temperature_flattened"],
                "target_layers": ["complete_surface_realizer", "ratio_policy"],
            },
        ],
        run_id="p3-9-runtime-design-source",
    )


def _first_repair_design_with_p2_red() -> dict[str, object]:
    return build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_items=[
            {
                "priority": 1,
                "blocker_id": "self_denial_identity_claim_risk",
                "blocker_category": "surface_breakage",
                "verdict_layer": VERDICT_LAYER_P2_RED,
                "case_count": 2,
                "families": ["self_denial"],
                "sample_case_ids": ["p3-self-denial-001"],
                "reason_codes": ["self_denial_identity_claim_risk"],
            }
        ],
        run_id="p3-9-p2-red-design-source",
    )


def _green_regression_result() -> dict[str, object]:
    return build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=_first_repair_design_with_runtime_targets(),
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(),
        run_id="p3-9-green-regression",
    )


def _connection_evidence(*, p5_ready: bool = False) -> dict[str, object]:
    if p5_ready:
        return {
            "observed_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
            "baseline_case_count": 60,
            "p3_verdict_row_count": 60,
            "p2_red_count": 0,
            "p2_red_independently_split": True,
            "repair_required_families": [],
            "yellow_families": [],
            "pass_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
            "classified_reason_codes": ["p3_readfeel_stable_for_p5_connection"],
            "first_repair_target_count": 1,
            "first_repair_target_layers": ["family_temperature", "ratio_policy"],
            "first_repair_blocker_ids": ["p3_readfeel_stable_for_p5_connection"],
            "current_only_readfeel_minimum_met": True,
            "current_only_min_read_feeling": 0.86,
            "current_only_min_naturalness": 0.86,
            "current_only_min_non_template": 0.86,
            "main_family_readfeel_minimum_met": True,
            "history_line_eligible_slice_checked": True,
            "history_line_masks_current_input_gap": False,
            "subscription_boundary_ok": True,
            "user_label_connection_surface_safe": True,
            "creepy_or_overclaim_or_self_blame_observed": False,
            "p5_hold_reason_codes": [],
        }
    return {
        "observed_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "baseline_case_count": 60,
        "p3_verdict_row_count": 60,
        "p2_red_count": 0,
        "p2_red_independently_split": True,
        "repair_required_families": ["daily_unpleasant", "mixed_emotion", "structure_question"],
        "yellow_families": ["self_denial", "relationship_boundary"],
        "pass_families": [
            family
            for family in PRODUCT_READFEEL_REQUIRED_FAMILIES
            if family not in {"daily_unpleasant", "mixed_emotion", "structure_question", "self_denial", "relationship_boundary"}
        ],
        "classified_reason_codes": [
            "rich_input_low_information_overroute",
            "input_core_missing",
            "generic_reception_surface",
            "family_temperature_flattened",
        ],
        "first_repair_target_count": 2,
        "first_repair_target_layers": ["input_material_bundle", "public_surface_requirement", "ratio_policy"],
        "first_repair_blocker_ids": ["rich_input_low_information_overroute", "generic_reception_surface"],
        "current_only_readfeel_minimum_met": False,
        "current_only_min_read_feeling": 0.62,
        "current_only_min_naturalness": 0.70,
        "current_only_min_non_template": 0.68,
        "main_family_readfeel_minimum_met": False,
        "history_line_eligible_slice_checked": True,
        "history_line_masks_current_input_gap": False,
        "subscription_boundary_ok": True,
        "user_label_connection_surface_safe": True,
        "creepy_or_overclaim_or_self_blame_observed": False,
        "p5_hold_reason_codes": [
            "rich_input_low_information_overroute",
            "generic_reception_surface",
            "current_only_readfeel_below_minimum",
        ],
    }


def test_p3_9_connection_decision_allows_p4_and_holds_p5_when_current_only_gap_remains() -> None:
    result = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=_green_regression_result(),
        p3_connection_evidence=_connection_evidence(),
        run_id="p3-9-p4-next-p5-hold",
    )
    summary = result["summary"]
    items = {item["target_phase"]: item for item in result["connection_items"]}

    assert result["schema_version"] == PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609
    assert result["source_step"] == PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609
    assert summary["next_phase_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert summary["p4_connection_allowed"] is True
    assert summary["p5_connection_allowed"] is False
    assert summary["p5_hold_until_current_only_readfeel_stable"] is True
    assert summary["observed_family_count"] == len(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert "all_12_required_families_have_p3_verdict" in summary["p4_met_conditions"]
    assert "current_only_readfeel_not_yet_stable" in summary["p5_hold_reasons"]
    assert items[PHASE_P4_FAMILY_TUNING]["allowed_to_connect"] is True
    assert items[PHASE_P5_USER_LABEL_CONNECTION]["allowed_to_connect"] is False
    assert result["p4_runtime_tuning_applied"] is False
    assert result["p5_visible_surface_strengthened"] is False
    assert result["public_release_applied"] is False
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(result)


def test_p3_9_allows_p5_only_after_current_only_readfeel_and_history_boundaries_are_clean() -> None:
    result = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=_green_regression_result(),
        p3_connection_evidence=_connection_evidence(p5_ready=True),
        run_id="p3-9-p5-ready",
    )
    summary = result["summary"]

    assert summary["next_phase_decision"] == DECISION_P5_READY_AFTER_P4
    assert summary["p4_connection_allowed"] is True
    assert summary["p5_connection_allowed"] is True
    assert summary["current_only_readfeel_minimum_met"] is True
    assert summary["history_line_masks_current_input_gap"] is False
    assert summary["subscription_boundary_ok"] is True
    assert summary["user_label_connection_surface_safe"] is True
    assert summary["creepy_or_overclaim_or_self_blame_observed"] is False
    assert "current_only_major_families_readfeel_minimum_met" in summary["p5_met_conditions"]
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(result)


def test_p3_9_blocks_p4_and_p5_when_required_regression_failed() -> None:
    rows = build_product_readfeel_p3_regression_green_fixture_results_20260609()
    rows[1] = {
        "suite_id": "backend_contract_display_split",
        "status": STATUS_FAILED,
        "passed_count": 5,
        "failed_count": 1,
        "failure_codes": ["backend_display_contract_failure"],
    }
    regression = build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=_first_repair_design_with_runtime_targets(),
        command_results=rows,
        run_id="p3-9-required-failure-source",
    )
    result = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=regression,
        p3_connection_evidence=_connection_evidence(),
        run_id="p3-9-required-failure",
    )
    summary = result["summary"]

    assert summary["next_phase_decision"] == DECISION_BLOCKED_BY_REGRESSION
    assert summary["p4_connection_allowed"] is False
    assert summary["p5_connection_allowed"] is False
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(result)


def test_p3_9_keeps_p2_red_before_any_p4_or_p5_connection() -> None:
    regression = build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=_first_repair_design_with_p2_red(),
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(),
        run_id="p3-9-p2-red-regression-source",
    )
    result = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=regression,
        p3_connection_evidence=_connection_evidence(),
        run_id="p3-9-p2-red",
    )
    summary = result["summary"]

    assert summary["p2_red_present"] is True
    assert summary["next_phase_decision"] == DECISION_BLOCKED_BY_P2_RED
    assert summary["p4_connection_allowed"] is False
    assert summary["p5_connection_allowed"] is False
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(result)


def test_p3_9_requires_all_12_family_verdicts_before_p4_or_p5_connection() -> None:
    evidence = _connection_evidence()
    evidence["observed_families"] = list(PRODUCT_READFEEL_REQUIRED_FAMILIES[:-1])
    evidence["p3_verdict_row_count"] = 55
    result = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=_green_regression_result(),
        p3_connection_evidence=evidence,
        run_id="p3-9-missing-family",
    )
    summary = result["summary"]

    assert summary["next_phase_decision"] == DECISION_NEEDS_BASELINE_EVIDENCE
    assert summary["p4_connection_allowed"] is False
    assert summary["p5_connection_allowed"] is False
    assert PRODUCT_READFEEL_REQUIRED_FAMILIES[-1] in summary["missing_families"]
    assert "missing_required_family_verdicts" in summary["p4_hold_reasons"]
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(result)


def test_p3_9_fixture_connector_builds_body_free_public_summary() -> None:
    regression = _green_regression_result()
    decision = build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
        regression_result=regression,
        connection_evidence=_connection_evidence(),
        run_id="p3-9-fixture",
    )
    dumped = dump_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609(
        regression_result=regression,
        connection_evidence=_connection_evidence(),
        run_id="p3-9-fixture-dump",
    )
    parsed = json.loads(dumped)

    assert decision["summary"]["next_phase_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609
    assert "connection_items" in parsed
    assert "regression_result_rows" not in parsed
    assert "p3_connection_evidence" not in parsed
    assert "actual display body" not in dumped
    assert "Emlisです" not in dumped
    assert "actual display body must not enter" not in dumped
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(parsed)


def test_p3_9_public_summary_and_guard_reject_body_keys_raw_logs_and_runtime_release_flags() -> None:
    result = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=_green_regression_result(),
        p3_connection_evidence=_connection_evidence(),
        run_id="p3-9-summary-dump",
    )
    dumped = dump_product_readfeel_p3_p4_p5_connection_public_summary_20260609(result)

    assert "connection_items" in dumped
    assert "regression_result_rows" not in dumped
    assert "review_rows" not in dumped
    assert "current_output_inventory" not in dumped
    assert "Emlisです" not in dumped

    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
            {"schema_version": "unsafe", "comment_text": "actual display body must not enter P3-9"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
            {"schema_version": "unsafe", "history_raw_text": "history raw text must not enter P3-9"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
            {"schema_version": "unsafe", "stdout": "raw pytest output must not be retained"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
            {"schema_version": "unsafe", "gate_relaxed": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
            {"schema_version": "unsafe", "p5_visible_surface_strengthened": True}
        )
