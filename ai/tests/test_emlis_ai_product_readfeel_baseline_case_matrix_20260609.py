from __future__ import annotations

from collections import Counter
import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    PRODUCT_READFEEL_BASELINE_CASES_PER_FAMILY_20260609,
    PRODUCT_READFEEL_BASELINE_CASE_STEP_20260609,
    PRODUCT_READFEEL_BASELINE_CASE_VERSION_20260609,
    PRODUCT_READFEEL_BASELINE_EXPECTED_CASE_COUNT_20260609,
    REQUIRED_COVERAGE_MINIMUMS_20260609,
    assert_product_readfeel_baseline_case_matrix_contract_20260609,
    assert_product_readfeel_baseline_public_safe_meta_only_20260609,
    build_product_readfeel_baseline_case_matrix_summary_20260609,
    build_product_readfeel_baseline_cases_20260609,
    build_product_readfeel_baseline_public_safe_index_20260609,
    dump_product_readfeel_baseline_case_matrix_summary_20260609,
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def test_p3_1_baseline_case_matrix_contains_twelve_families_times_five_cases() -> None:
    cases = build_product_readfeel_baseline_cases_20260609()
    family_counts = Counter(case["family"] for case in cases)

    assert len(cases) == PRODUCT_READFEEL_BASELINE_EXPECTED_CASE_COUNT_20260609 == 60
    assert set(family_counts) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert all(
        family_counts[family] == PRODUCT_READFEEL_BASELINE_CASES_PER_FAMILY_20260609
        for family in PRODUCT_READFEEL_REQUIRED_FAMILIES
    )
    assert_product_readfeel_baseline_case_matrix_contract_20260609(cases)

    for case in cases:
        assert case["schema_version"] == PRODUCT_READFEEL_BASELINE_CASE_VERSION_20260609
        assert case["source_step"] == PRODUCT_READFEEL_BASELINE_CASE_STEP_20260609
        assert case["case_id"].startswith(f"p3-{case['family']}-")
        assert case["local_qa_only"] is True
        assert case["synthetic_case_material"] is True
        assert case["output_capture_completed"] is False
        assert case["sanitized_current_output_event_created"] is False
        assert case["product_gate_ready"] is False
        assert case["public_release_applied"] is False
        assert case["current_input"]["synthetic_case_material"] is True
        assert case["current_input"]["memo"].strip()
        assert isinstance(case["current_input"]["emotions"], list)
        assert isinstance(case["current_input"]["category"], list)
        assert case["expected_contract"]["display_expected"] is True
        assert case["expected_contract"]["rn_visible_expected"] is True
        assert case["expected_contract"]["product_surface_validation_required"] is True
        assert case["expected_contract"]["must_retain_slots"]
        assert case["expected_contract"]["must_not_surface_classes"]
        controls = case["evaluation_controls"]
        assert controls["exact_comment_text_required"] is False
        assert controls["case_specific_runtime_branch_allowed"] is False
        assert controls["gate_relaxation_allowed"] is False
        assert controls["public_meta_body_allowed"] is False
        assert case["runtime_branching_uses_fixture_strings"] is False
        assert case["fixture_text_used_for_runtime_branching"] is False

    for node in _walk_dicts(cases):
        assert "comment_text" not in node
        assert "candidate_body" not in node
        assert "reply_text" not in node


def test_p3_1_baseline_case_matrix_meets_required_coverage_slices_without_family_expansion() -> None:
    cases = build_product_readfeel_baseline_cases_20260609()
    summary = build_product_readfeel_baseline_case_matrix_summary_20260609(cases)
    coverage_counts = summary["coverage_slice_counts"]

    assert summary["baseline_case_matrix_ready"] is True
    assert summary["p3_0_contract_freeze_respected"] is True
    assert summary["p3_1_baseline_case_matrix_ready"] is True
    assert summary["case_count"] == 60
    assert summary["missing_families"] == []
    assert summary["below_minimum_slices"] == []
    assert set(summary["required_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert "limited_grounding" not in summary["required_families"]
    assert "source_unavailable_high_information" not in summary["required_families"]
    assert "history_line_eligible" not in summary["required_families"]

    for slice_id, minimum in REQUIRED_COVERAGE_MINIMUMS_20260609.items():
        assert coverage_counts[slice_id] >= minimum
    assert coverage_counts["limited_grounding"] >= 5
    assert coverage_counts["source_unavailable_high_information"] >= 3
    assert coverage_counts["history_line_eligible"] >= 5
    assert coverage_counts["anger_or_boundary"] >= 5
    assert coverage_counts["standard_state_answer"] >= 5
    assert coverage_counts["render_default_path"] == 60
    assert coverage_counts["free_tier"] > 0
    assert coverage_counts["plus_tier"] > 0
    assert coverage_counts["premium_tier"] > 0


def test_p3_1_public_safe_index_drops_synthetic_input_bodies_and_does_not_create_current_output_events() -> None:
    cases = build_product_readfeel_baseline_cases_20260609()
    safe_index = build_product_readfeel_baseline_public_safe_index_20260609(cases)
    summary = build_product_readfeel_baseline_case_matrix_summary_20260609(cases)
    safe_dump = _dump({"summary": summary, "safe_index": safe_index})

    assert len(safe_index) == 60
    assert_product_readfeel_baseline_public_safe_meta_only_20260609(summary)
    assert_product_readfeel_baseline_public_safe_meta_only_20260609(safe_index)
    assert "疲れた" not in safe_dump
    assert "今日は小さなことで" not in safe_dump
    assert '"current_input":' not in safe_dump
    assert '"memo":' not in safe_dump
    assert '"memo_action":' not in safe_dump
    assert '"comment_text":' not in safe_dump
    assert '"candidate_body":' not in safe_dump
    assert summary["contains_synthetic_local_case_material"] is True
    assert summary["output_capture_completed"] is False
    assert summary["sanitized_current_output_event_created"] is False
    assert summary["scorecard_event_created"] is False
    assert summary["product_gate_ready"] is False
    assert summary["public_release_applied"] is False

    for item in safe_index:
        assert item["local_case_material_available"] is True
        assert item["local_case_material_is_synthetic"] is True
        assert item["local_case_material_retained_here"] is False
        assert item["output_capture_completed"] is False
        assert item["sanitized_current_output_event_created"] is False
        assert item["raw_input_included"] is False
        assert item["comment_text_body_included"] is False
        assert item["product_gate_ready"] is False
        assert item["public_release_applied"] is False


def test_p3_1_history_line_eligible_cases_have_owned_history_boundary_without_raw_history_text() -> None:
    cases = build_product_readfeel_baseline_cases_20260609()
    history_cases = [case for case in cases if "history_line_eligible" in case["coverage_slices"]]

    assert len(history_cases) >= REQUIRED_COVERAGE_MINIMUMS_20260609["history_line_eligible"]
    assert all(case["subscription_tier"] in {"plus", "premium"} for case in history_cases)
    assert all("history_line_candidate_path" in case["path_targets"] for case in history_cases)
    for case in history_cases:
        history = case["history_context"]
        assert history["enabled"] is True
        assert history["owned_record_count"] >= 2
        assert history["evidence_record_count"] >= 2
        assert history["current_record_included"] is True
        history_dump = _dump(history)
        assert '"memo":' not in history_dump
        assert '"raw_text":' not in history_dump
        assert '"comment_text":' not in history_dump
        for record in history["history_records"]:
            assert record["raw_text_included"] is False


def test_p3_1_summary_dump_is_body_free_and_keeps_release_flags_false() -> None:
    summary = build_product_readfeel_baseline_case_matrix_summary_20260609()
    dumped = dump_product_readfeel_baseline_case_matrix_summary_20260609(summary)
    parsed = json.loads(dumped)

    assert parsed["baseline_case_matrix_ready"] is True
    assert parsed["local_qa_only"] is True
    assert parsed["contains_synthetic_local_case_material"] is True
    assert parsed["output_capture_completed"] is False
    assert parsed["sanitized_current_output_event_created"] is False
    assert parsed["scorecard_event_created"] is False
    assert parsed["exact_comment_text_required"] is False
    assert parsed["case_specific_runtime_branch"] is False
    assert parsed["runtime_branching_uses_fixture_strings"] is False
    assert parsed["fixture_text_used_for_runtime_branching"] is False
    assert parsed["public_meta_body_allowed"] is False
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert '"current_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert_product_readfeel_baseline_public_safe_meta_only_20260609(parsed)


def test_p3_1_guards_reject_output_bodies_exact_text_locks_runtime_branches_and_public_body_meta() -> None:
    cases = build_product_readfeel_baseline_cases_20260609()
    unsafe_case = dict(cases[0])
    unsafe_case["comment_text"] = "fixtureは期待本文を持たない"
    with pytest.raises(ValueError):
        assert_product_readfeel_baseline_case_matrix_contract_20260609([unsafe_case, *cases[1:]])

    unsafe_exact = dict(cases[0])
    unsafe_exact["evaluation_controls"] = dict(unsafe_exact["evaluation_controls"])
    unsafe_exact["evaluation_controls"]["exact_comment_text_required"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_baseline_case_matrix_contract_20260609([unsafe_exact, *cases[1:]])

    unsafe_branch = dict(cases[0])
    unsafe_branch["case_specific_runtime_branch"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_baseline_case_matrix_contract_20260609([unsafe_branch, *cases[1:]])

    with pytest.raises(ValueError):
        assert_product_readfeel_baseline_public_safe_meta_only_20260609({"current_input": {"memo": "出さない"}})
    with pytest.raises(ValueError):
        assert_product_readfeel_baseline_public_safe_meta_only_20260609({"comment_text": "出さない"})
    with pytest.raises(ValueError):
        assert_product_readfeel_baseline_public_safe_meta_only_20260609({"product_gate_ready": True})
    with pytest.raises(ValueError):
        assert_product_readfeel_baseline_public_safe_meta_only_20260609({"public_meta_body_allowed": True})
