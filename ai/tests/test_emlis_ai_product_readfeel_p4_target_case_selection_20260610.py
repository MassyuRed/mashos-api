from __future__ import annotations

from collections import Counter
import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_P4_NEXT_P5_HOLD,
)
from emlis_ai_product_readfeel_p4_target_case_selection import (
    P4_BOUNDARY_REGRESSION_FAMILIES_20260610,
    P4_BOUNDARY_REGRESSION_SLICES_20260610,
    P4_FAMILY_SELECTION_MINIMUMS_20260610,
    P4_MAIN_TARGET_FAMILIES_20260610,
    P4_SLICE_SELECTION_MINIMUMS_20260610,
    P4_YELLOW_REVIEW_FAMILIES_20260610,
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610,
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610,
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610,
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610,
    build_product_readfeel_p4_target_case_selection_20260610,
    build_product_readfeel_p4_target_case_selection_public_summary_20260610,
    dump_product_readfeel_p4_target_case_selection_public_summary_20260610,
)
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_public_safe_index_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_p4_p5_connection_decision_20260609 import (
    build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609,
)
from fixtures.emlis_ai_product_readfeel_p4_target_cases_20260610 import (
    build_product_readfeel_p4_target_case_selection_from_p3_9_20260610,
    dump_product_readfeel_p4_target_case_selection_summary_from_p3_9_20260610,
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _family_counts(selected_cases: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(case["family"]) for case in selected_cases)


def _slice_counts(selected_cases: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for case in selected_cases:
        counter.update(case["coverage_slices"])
    return counter


def _group_counts(selected_cases: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for case in selected_cases:
        counter.update(case["selection_groups"])
    return counter


def test_p4_1_selects_initial_target_cases_from_p3_9_without_runtime_changes() -> None:
    selection = build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id="p4_1_target_case_selection"
    )
    summary = selection["summary"]
    selected_cases = selection["selected_cases"]
    family_counts = _family_counts(selected_cases)
    slice_counts = _slice_counts(selected_cases)
    group_counts = _group_counts(selected_cases)

    assert selection["schema_version"] == PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610
    assert selection["source_step"] == PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610
    assert selection["selection_profile"] == PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610
    assert summary["schema_version"] == PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610
    assert summary["source_p3_9_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert summary["p4_connection_allowed"] is True
    assert summary["p5_connection_allowed"] is False
    assert summary["current_only_readfeel_minimum_met"] is False
    assert summary["main_family_readfeel_minimum_met"] is False
    assert summary["p5_hold_fixed"] is True
    assert summary["p4_target_case_selection_fixed"] is True
    assert summary["below_minimum_families"] == []
    assert summary["below_minimum_slices"] == []
    assert group_counts["main_target"] >= 10
    assert group_counts["yellow_review"] >= 3
    assert group_counts["boundary_regression"] >= 7

    assert tuple(summary["main_target_families"]) == P4_MAIN_TARGET_FAMILIES_20260610
    assert tuple(summary["yellow_review_families"]) == P4_YELLOW_REVIEW_FAMILIES_20260610
    assert tuple(summary["boundary_regression_families"]) == P4_BOUNDARY_REGRESSION_FAMILIES_20260610
    assert tuple(summary["boundary_regression_slices"]) == P4_BOUNDARY_REGRESSION_SLICES_20260610
    for family, minimum in P4_FAMILY_SELECTION_MINIMUMS_20260610.items():
        assert family_counts[family] >= minimum
        assert summary["selected_family_counts"][family] >= minimum
    for slice_id, minimum in P4_SLICE_SELECTION_MINIMUMS_20260610.items():
        assert slice_counts[slice_id] >= minimum
        assert summary["selected_coverage_slice_counts"][slice_id] >= minimum

    assert selection["p4_0_connection_freeze_respected"] is True
    assert selection["p4_1_target_case_selection_fixed"] is True
    assert selection["p4_runtime_tuning_applied"] is False
    assert selection["p5_visible_surface_strengthened"] is False
    assert selection["runtime_repair_applied"] is False
    assert selection["implementation_change_applied"] is False
    assert selection["public_response_key_change"] is False
    assert selection["api_route_changed"] is False
    assert selection["db_physical_name_changed"] is False
    assert selection["rn_visible_contract_changed"] is False
    assert selection["gate_relaxed"] is False
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(selection)


def test_p4_1_selected_cases_are_body_free_case_refs_with_expected_roles_and_blockers() -> None:
    selection = build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id="p4_1_selected_cases"
    )
    selected_cases = selection["selected_cases"]
    by_id = {case["case_ref_id"]: case for case in selected_cases}

    assert len(by_id) == len(selected_cases)
    assert "p3-daily_unpleasant-001" in by_id
    assert "p3-structure_question-003" in by_id
    assert "p3-self_denial-001" in by_id
    assert "p3-long_meaning_arc-004" in by_id or "p3-long_meaning_arc-005" in by_id

    for case in selected_cases:
        assert case["schema_version"]
        assert case["case_ref_id"].startswith("p3-")
        assert case["family"]
        assert case["coverage_slices"]
        assert case["selection_groups"]
        assert case["blocker_ids"]
        assert case["target_layers"]
        assert case["selected_reason_codes"]
        assert case["source_p3_9_decision"] == DECISION_P4_NEXT_P5_HOLD
        assert case["body_free_case_references_only"] is True
        assert case["local_case_material_available"] is True
        assert case["local_case_material_retained_here"] is False
        assert case["raw_input_included"] is False
        assert case["comment_text_included"] is False
        assert case["comment_text_body_included"] is False
        assert case["candidate_body_included"] is False
        assert case["p4_runtime_tuning_applied"] is False
        assert case["p5_visible_surface_strengthened"] is False
        assert case["case_specific_runtime_branch"] is False
        assert case["fixed_sentence_template_added"] is False
        assert case["gate_relaxed"] is False

    daily_case = by_id["p3-daily_unpleasant-001"]
    assert "main_target" in daily_case["selection_groups"]
    assert daily_case["p3_verdict_layer"] == "P3_REPAIR_REQUIRED"
    assert "rich_input_low_information_overroute" in daily_case["blocker_ids"]
    assert "generic_reception_surface" in daily_case["blocker_ids"]
    assert "input_material_bundle" in daily_case["target_layers"]
    assert "ratio_policy" in daily_case["target_layers"]

    self_case = by_id["p3-self_denial-001"]
    assert "yellow_review" in self_case["selection_groups"]
    assert self_case["p3_verdict_layer"] == "P3_YELLOW"
    assert "self_denial_yellow_safety_adjacent_review" in self_case["blocker_ids"]

    boundary_cases = [case for case in selected_cases if "boundary_regression" in case["selection_groups"]]
    assert boundary_cases
    assert any("limited_grounding" in case["coverage_slices"] for case in boundary_cases)
    assert any("source_unavailable_high_information" in case["coverage_slices"] for case in boundary_cases)
    assert any("history_line_eligible" in case["coverage_slices"] for case in boundary_cases)
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(selection)


def test_p4_1_public_summary_and_dump_keep_case_refs_without_bodies() -> None:
    selection = build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id="p4_1_public_summary"
    )
    public_summary = build_product_readfeel_p4_target_case_selection_public_summary_20260610(selection)
    dumped = dump_product_readfeel_p4_target_case_selection_summary_from_p3_9_20260610(
        run_id="p4_1_public_summary_dump"
    )
    parsed = json.loads(dumped)

    assert public_summary["selected_case_count"] == len(public_summary["selected_case_refs"])
    assert parsed["selected_case_count"] == len(parsed["selected_case_refs"])
    assert parsed["p5_connection_allowed"] is False
    assert parsed["p5_hold_until_current_only_readfeel_stable"] is True
    assert parsed["p4_runtime_tuning_applied"] is False
    assert parsed["p5_visible_surface_strengthened"] is False
    assert '"current_input"' not in dumped
    assert '"memo"' not in dumped
    assert '"memo_action"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"candidate_body"' not in dumped
    assert "会議で軽く流された" not in dumped
    assert "Emlisです" not in dumped
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(public_summary)
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(parsed)


def test_p4_1_refuses_to_select_cases_if_p3_9_no_longer_holds_p5() -> None:
    p3_decision = build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
        connection_evidence={
            "repair_required_families": [],
            "yellow_families": [],
            "pass_families": [],
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
        },
        run_id="p4_1_p5_ready_source",
    )
    assert p3_decision["summary"]["p5_connection_allowed"] is True

    with pytest.raises(ValueError):
        build_product_readfeel_p4_target_case_selection_20260610(
            p3_connection_decision=p3_decision,
            baseline_public_safe_index=build_product_readfeel_baseline_public_safe_index_20260609(),
            run_id="p4_1_should_not_run_when_p5_ready",
        )


def test_p4_1_guard_rejects_raw_bodies_comment_bodies_and_runtime_mutation_flags() -> None:
    selection = build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id="p4_1_guard_source"
    )

    unsafe_raw = dict(selection)
    unsafe_raw["raw_input"] = "出してはいけない"
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_target_case_selection_meta_only_20260610(unsafe_raw)

    unsafe_comment = dict(selection)
    unsafe_comment["selected_cases"] = [dict(selection["selected_cases"][0])]
    unsafe_comment["selected_cases"][0]["comment_text"] = "Emlis本文をここに残してはいけない"
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_target_case_selection_meta_only_20260610(unsafe_comment)

    unsafe_p5 = dict(selection)
    unsafe_p5["p5_visible_surface_strengthened"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_target_case_selection_meta_only_20260610(unsafe_p5)

    unsafe_gate = dict(selection)
    unsafe_gate["summary"] = dict(unsafe_gate["summary"])
    unsafe_gate["summary"]["gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_target_case_selection_meta_only_20260610(unsafe_gate)

    assert '"raw_input":' not in _dump(selection)
