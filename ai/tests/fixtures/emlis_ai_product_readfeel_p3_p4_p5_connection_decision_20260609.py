# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-9 fixture connector for P4/P5 connection decision.

This fixture connects a body-free P3-8 regression result to a body-free P4/P5
next-step judgement.  Defaults are synthetic and do not call the real renderer,
retain local review packets, rendered Emlis bodies, source inputs, raw history
text, or raw test logs.
"""

from collections.abc import Mapping
import json
from typing import Any

from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_first_repair_design import build_product_readfeel_p3_first_repair_design_20260609
from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609,
    PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609,
    PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609,
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609,
    build_product_readfeel_p3_p4_p5_connection_decision_20260609,
    build_product_readfeel_p3_p4_p5_connection_public_summary_20260609,
)
from emlis_ai_product_readfeel_p3_regression import (
    build_product_readfeel_p3_regression_green_fixture_results_20260609,
    build_product_readfeel_p3_regression_result_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import VERDICT_LAYER_P3_REPAIR_REQUIRED


def _default_first_repair_design(run_id: str | None = None) -> dict[str, Any]:
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
        run_id=run_id or "p3_9_default_first_repair_design",
    )


def _default_regression_result(run_id: str | None = None) -> dict[str, Any]:
    return build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=_default_first_repair_design(run_id=run_id or "p3_9_default_first_repair_design"),
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(),
        run_id=run_id or "p3_9_default_regression_result",
    )


def _default_connection_evidence(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    evidence = {
        "baseline_case_count": 60,
        "p3_verdict_row_count": 60,
        "observed_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "missing_families": [],
        "p2_red_count": 0,
        "p2_red_independently_split": True,
        "repair_required_families": ["daily_unpleasant", "structure_question"],
        "yellow_families": ["self_denial"],
        "classified_reason_codes": [
            "rich_input_low_information_overroute",
            "generic_reception_surface",
        ],
        "first_repair_target_count": 2,
        "first_repair_target_layers": ["input_material_bundle", "ratio_policy"],
        "first_repair_blocker_ids": [
            "rich_input_low_information_overroute",
            "generic_reception_surface",
        ],
        "current_only_readfeel_minimum_met": False,
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
    evidence.update(dict(overrides or {}))
    return evidence


def build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
    *,
    regression_result: Mapping[str, Any] | None = None,
    connection_evidence: Mapping[str, Any] | None = None,
    p3_regression_result: Mapping[str, Any] | None = None,
    p3_connection_evidence: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    _ = renderer
    regression = regression_result or p3_regression_result or _default_regression_result(
        run_id=run_id or "p3_9_regression_fixture"
    )
    evidence = _default_connection_evidence(connection_evidence or p3_connection_evidence)
    decision = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=regression,
        p3_connection_evidence=evidence,
        run_id=run_id or str(regression.get("run_id") or "p3_9_p4_p5_connection_fixture"),
    )
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(decision)
    return decision


def build_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609(
    *,
    regression_result: Mapping[str, Any] | None = None,
    connection_evidence: Mapping[str, Any] | None = None,
    p3_regression_result: Mapping[str, Any] | None = None,
    p3_connection_evidence: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    decision = build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
        regression_result=regression_result,
        connection_evidence=connection_evidence,
        p3_regression_result=p3_regression_result,
        p3_connection_evidence=p3_connection_evidence,
        renderer=renderer,
        run_id=run_id,
    )
    return build_product_readfeel_p3_p4_p5_connection_public_summary_20260609(decision)


def dump_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609(
    *,
    regression_result: Mapping[str, Any] | None = None,
    connection_evidence: Mapping[str, Any] | None = None,
    p3_regression_result: Mapping[str, Any] | None = None,
    p3_connection_evidence: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609(
        regression_result=regression_result,
        connection_evidence=connection_evidence,
        p3_regression_result=p3_regression_result,
        p3_connection_evidence=p3_connection_evidence,
        renderer=renderer,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_DECISION_VERSION_20260609",
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_P4_P5_CONNECTION_STEP_20260609",
    "assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609",
    "build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609",
    "build_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609",
    "dump_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609",
]
