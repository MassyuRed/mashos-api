from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
    build_product_readfeel_current_output_inventory,
)
from emlis_ai_product_readfeel_rubric import PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS
from fixtures.emlis_ai_product_readfeel_fixture_families import (
    PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
    PRODUCT_READFEEL_FIXTURE_FAMILY_REGISTRY_VERSION,
    PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES,
    assert_product_readfeel_fixture_family_meta_only,
    build_product_readfeel_fixture_family_coverage,
    build_product_readfeel_fixture_family_definitions,
    build_product_readfeel_fixture_family_registry,
    build_product_readfeel_fixture_family_scorecard_events,
    normalize_product_readfeel_fixture_family,
    normalize_product_readfeel_fixture_family_coverage_to_scorecard_fields,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in (
            "raw_input",
            "raw_text",
            "input_text",
            "user_input",
            "memo",
            "memo_action",
            "emotion_details",
            "comment_text",
            "expected_comment_text",
            "reply_text",
            "surface_text",
            "display_text",
            "candidate_body",
            "body",
            "text",
        ):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("input_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        assert payload.get("candidate_body_included") is not True
        assert payload.get("exact_comment_text_required") is not True
        assert payload.get("case_specific_runtime_branch") is not True
        assert payload.get("case_specific_runtime_condition_allowed") is not True
        assert payload.get("runtime_branching_uses_fixture_strings") is not True
        assert payload.get("fixture_text_used_for_runtime_branching") is not True
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def test_phase3_registry_defines_required_product_readfeel_families_as_meta_only() -> None:
    registry = build_product_readfeel_fixture_family_registry()

    assert registry["version"] == PRODUCT_READFEEL_FIXTURE_FAMILY_REGISTRY_VERSION
    assert registry["step"] == PRODUCT_READFEEL_FIXTURE_FAMILY_STEP
    assert registry["phase3_fixture_family_definition_ready"] is True
    assert registry["product_readfeel_phase3_ready"] is True
    assert tuple(registry["required_families"]) == PRODUCT_READFEEL_REQUIRED_FAMILIES
    assert tuple(registry["covered_families"]) == PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES
    assert registry["missing_families"] == []
    assert registry["exact_comment_text_required"] is False
    assert registry["case_specific_runtime_condition_allowed"] is False
    assert registry["runtime_branching_uses_fixture_strings"] is False
    assert registry["scorecard_event_projection_available"] is True
    _assert_meta_only(registry)


def test_phase3_each_family_has_modes_ratio_dimensions_forbidden_surface_and_v2_opportunity() -> None:
    definitions = build_product_readfeel_fixture_family_definitions()

    assert len(definitions) == len(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    for definition in definitions:
        assert definition["product_readfeel_family"] in PRODUCT_READFEEL_REQUIRED_FAMILIES
        assert definition["expected_internal_modes"]
        assert definition["expected_ratio_policy"]["fixed_ratio_forbidden"] is True
        assert definition["expected_ratio_policy"]["observation_zero_allowed"] is False
        assert definition["expected_ratio_policy"]["reception_zero_allowed"] is False
        assert set(PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS).issubset(set(definition["required_dimensions"]))
        assert "insight_delta" in definition["optional_v2_dimensions"]
        assert "structure_insight_candidate_quality" in definition["optional_v2_dimensions"]
        assert "diagnosis" in definition["forbidden_surface_classes"]
        assert "case_specific_runtime_branch" in definition["forbidden_surface_classes"]
        assert definition["v2_insight_opportunity"]
        assert definition["examples_are_not_runtime_templates"] is True
        _assert_meta_only(definition)


def test_phase3_low_information_alias_maps_to_registry_family_without_creating_duplicate() -> None:
    assert normalize_product_readfeel_fixture_family("low_information") == "low_information_short"
    assert normalize_product_readfeel_fixture_family("daily_unpleasant_reception") == "daily_unpleasant"
    assert normalize_product_readfeel_fixture_family("structure_question_observation") == "structure_question"


def test_phase3_scorecard_event_projection_covers_all_families_without_exact_text_lock() -> None:
    events = build_product_readfeel_fixture_family_scorecard_events()
    coverage = build_product_readfeel_fixture_family_coverage(events)
    fields = normalize_product_readfeel_fixture_family_coverage_to_scorecard_fields(coverage)

    assert len(events) == len(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert coverage["phase3_fixture_family_coverage_ready"] is True
    assert coverage["fixture_family_coverage_rate"] == 1.0
    assert coverage["missing_families"] == []
    assert fields["product_readfeel_phase3_ready"] is True
    assert fields["product_readfeel_fixture_family_coverage_rate"] == 1.0
    for event in events:
        assert event["exact_comment_text_required"] is False
        assert event["case_specific_runtime_branch"] is False
        assert event["runtime_branching_uses_fixture_strings"] is False
        assert event["comment_text_present"] is True
        _assert_meta_only(event)
    _assert_meta_only(coverage)
    _assert_meta_only(fields)


def test_phase3_events_feed_existing_product_readfeel_inventory_and_complete_scorecard() -> None:
    events = build_product_readfeel_fixture_family_scorecard_events()
    inventory = build_product_readfeel_current_output_inventory(events=events)
    scorecard = build_complete_product_quality_scorecard(scorecard_events=events)

    assert inventory["missing_families"] == []
    assert set(inventory["observed_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert inventory["family_verdicts"][FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE] == "REPAIR_REQUIRED"
    assert FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE in inventory["v2_structure_insight_backlog_families"]
    assert scorecard["product_readfeel_missing_families"] == []
    assert set(scorecard["product_readfeel_observed_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert scorecard["product_readfeel_family_verdicts"][FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE] == "REPAIR_REQUIRED"
    assert FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE in scorecard["product_readfeel_v2_structure_insight_backlog_families"]
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False
    _assert_meta_only(inventory)
    _assert_meta_only(scorecard["phase1_product_readfeel_current_output_inventory_fields"])


def test_phase3_meta_only_guard_rejects_raw_body_exact_lock_and_runtime_branch() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"raw_input": "保持禁止"})
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"exact_comment_text_required": True})
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"case_specific_runtime_branch": True})
