from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_blind_qa_ratings_review import (
    build_product_readfeel_p3_blind_qa_ratings_review_20260609,
)
from emlis_ai_product_readfeel_p3_first_repair_design import (
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_ITEM_VERSION_20260609,
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609,
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609,
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609,
    build_product_readfeel_p3_first_repair_design_20260609,
)
from emlis_ai_product_readfeel_p3_repair_priority_ledger import (
    build_product_readfeel_p3_repair_priority_ledger_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
    build_product_readfeel_p3_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609 import (
    build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609,
    build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_first_repair_design_20260609 import (
    build_product_readfeel_p3_first_repair_design_from_repair_priority_ledger_20260609,
    dump_product_readfeel_p3_first_repair_design_summary_from_repair_priority_ledger_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_local_output_capture_20260609 import (
    build_product_readfeel_p3_local_output_capture_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609 import (
    build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609,
)


def _fake_reply_meta(*, observation_status: str = "passed") -> dict[str, Any]:
    return {
        "schema_version": "fake.local.renderer.meta.v1",
        "version": "fake.local.renderer.meta.v1",
        "kernel_version": "fake-kernel",
        "observation_status": observation_status,
        "observation_reply_kind": "normal_observation",
        "diagnostic_summary": {
            "material_quality": "synthetic_local_qa",
            "binding_supported_sentence_count": 2,
            "expected_binding_count": 2,
            "reason_required_count": 1,
            "reason_covered_count": 1,
        },
        "visible_surface_acceptance_gate": {
            "classification": "accepted",
            "action": "allow_public_feedback",
            "passed": True,
        },
        "product_surface_validation": {
            "product_surface_valid": True,
            "passed": True,
        },
        "public_surface_lineage": {
            "candidate_source_kind": "fake_renderer_current_output_capture",
        },
        "composer_model": "fake_renderer",
        "rejection_reasons": [],
    }


async def _fake_renderer(**kwargs: Any) -> dict[str, Any]:
    current_input = kwargs["current_input"]
    return {
        "comment_text": f"Emlisです。synthetic local QA output for {current_input['id']}.",
        "meta": _fake_reply_meta(),
    }


def _events_from_fake_capture() -> list[dict[str, Any]]:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-7-capture-test",
    )
    return [dict(event) for event in capture["sanitized_current_output_events"]]


def _append_reason(event: dict[str, Any], reason: str) -> None:
    event["reason_codes"] = [*list(event.get("reason_codes") or []), reason]


def _ledger_from_events(events: list[dict[str, Any]], *, run_id: str) -> dict[str, Any]:
    split = build_product_readfeel_p3_verdict_split_20260609(
        sanitized_current_output_events=events,
        run_id=f"{run_id}-split",
    )
    reviews = build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(verdict_split=split)
    material = build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
        verdict_split=split,
        blind_qa_reviews=reviews,
        run_id=f"{run_id}-ratings",
    )
    return build_product_readfeel_p3_repair_priority_ledger_20260609(
        blind_qa_material=material,
        verdict_split=split,
        run_id=f"{run_id}-ledger",
    )


def test_p3_7_builds_first_repair_design_from_p3_6_ledger_with_max_two_runtime_targets() -> None:
    events = _events_from_fake_capture()
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    mixed_emotion = next(event for event in events if event["family"] == "mixed_emotion")
    structure_question = next(event for event in events if event["family"] == "structure_question")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    _append_reason(mixed_emotion, "generic_reception_surface")
    _append_reason(structure_question, "family_temperature_flattened")

    ledger = _ledger_from_events(events, run_id="p3-7-two-targets")
    design = build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_ledger=ledger,
        run_id="p3-7-two-targets-design",
    )
    summary = design["summary"]
    profiles = [item["design_profile_id"] for item in design["design_items"]]

    assert design["schema_version"] == PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609
    assert design["source_step"] == PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609
    assert summary["schema_version"] == PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609
    assert summary["source_ledger_item_count"] == 2
    assert summary["design_item_count"] == 2
    assert summary["runtime_repair_design_count"] == 2
    assert summary["first_repair_targets_limited_to_max_two"] is True
    assert summary["p3_runtime_repair_can_start"] is True
    assert summary["decision"] == "start_first_repair_implementation_design_with_max_two_targets"
    assert profiles == [
        "repair_A_rich_input_low_information_overroute",
        "repair_B_generic_repeated_or_family_temperature",
    ]
    assert set(summary["first_runtime_repair_design_ids"]) == set(profiles)
    assert set(summary["families"]) >= {"daily_unpleasant", "mixed_emotion"}
    assert "mashos-api/ai/services/ai_inference/emlis_ai_input_material_bundle.py" in design["design_items"][0]["change_file_candidates"]
    assert "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py" in design["design_items"][1]["change_file_candidates"]
    assert "gate_relaxation" in design["design_items"][0]["forbidden_fix_paths"]
    assert design["runtime_change_applied"] is False
    assert design["implementation_change_applied"] is False
    assert design["product_gate_ready"] is False
    assert design["public_release_applied"] is False
    for item in design["design_items"]:
        assert item["schema_version"] == PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_ITEM_VERSION_20260609
        assert item["selected_for_first_runtime_repair"] is True
        assert item["comment_text_body_included"] is False
        assert item["raw_input_included"] is False
        assert item["candidate_body_included"] is False
        assert item["runtime_repair_applied"] is False
        assert item["implementation_change_applied"] is False
        assert item["first_test_candidates"]
        assert item["regression_subset"]
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(design)


def test_p3_7_keeps_p2_red_ahead_of_first_p3_repair_design() -> None:
    events = _events_from_fake_capture()
    self_denial = next(event for event in events if event["family"] == "self_denial")
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    _append_reason(self_denial, "self_denial_identity_claim_risk")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")

    ledger = _ledger_from_events(events, run_id="p3-7-p2-red")
    design = build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_ledger=ledger,
        run_id="p3-7-p2-red-design",
    )
    summary = design["summary"]
    first = design["design_items"][0]

    assert ledger["summary"]["p2_red_present"] is True
    assert summary["p2_red_present"] is True
    assert summary["p2_red_blocks_p3_repair"] is True
    assert summary["p3_runtime_repair_can_start"] is False
    assert summary["decision"] == "return_to_p2_surface_safety_before_first_repair_design"
    assert first["source_verdict_layer"] == VERDICT_LAYER_P2_RED
    assert first["design_profile_id"] == "p2_surface_safety_or_contract_first"
    assert first["selected_for_first_runtime_repair"] is False
    assert first["p3_runtime_repair_allowed"] is False
    assert "mashos-api/ai/services/ai_inference/emlis_ai_visible_surface_acceptance_gate.py" in first["change_file_candidates"]
    assert "gate_relaxation" in first["forbidden_fix_paths"]
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(design)


def test_p3_7_defers_p5_p6_backlog_when_no_current_input_repair_target_exists() -> None:
    ledger = build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609(
        renderer=_fake_renderer,
        run_id="p3-7-backlog-source",
    )
    design = build_product_readfeel_p3_first_repair_design_from_repair_priority_ledger_20260609(
        repair_priority_ledger=ledger,
        run_id="p3-7-backlog-design",
    )
    summary = design["summary"]
    first = design["design_items"][0]

    assert first["source_blocker_id"] == "structure_insight_gap"
    assert first["design_profile_id"] == "p5_p6_backlog_not_first_p3_repair"
    assert first["selected_for_first_runtime_repair"] is False
    assert summary["runtime_repair_design_count"] == 0
    assert summary["backlog_defer_count"] == 1
    assert summary["p3_runtime_repair_can_start"] is False
    assert summary["decision"] == "defer_p5_p6_backlog_and_collect_current_input_readfeel_evidence"
    assert "mashos-api/ai/services/ai_inference/emlis_ai_structure_insight_candidate.py" in first["change_file_candidates"]
    assert "history_line_masking_current_input_gap" in first["forbidden_fix_paths"]
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(design)


def test_p3_7_public_summary_dump_excludes_source_ledger_rows_and_bodies() -> None:
    events = _events_from_fake_capture()
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    mixed_emotion = next(event for event in events if event["family"] == "mixed_emotion")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    _append_reason(mixed_emotion, "generic_reception_surface")
    ledger = _ledger_from_events(events, run_id="p3-7-summary-dump-source")

    dumped = dump_product_readfeel_p3_first_repair_design_summary_from_repair_priority_ledger_20260609(
        repair_priority_ledger=ledger,
        run_id="p3-7-summary-dump",
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609
    assert parsed["design_item_count"] == 2
    assert parsed["runtime_repair_design_count"] == 2
    assert parsed["comment_text_body_included"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["candidate_body_included"] is False
    assert parsed["runtime_change_applied"] is False
    assert parsed["implementation_change_applied"] is False
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert "first_repair_design_items" in parsed
    assert "design_items" not in parsed
    assert "items" not in parsed
    assert "verdict_rows" not in parsed
    assert "review_rows" not in parsed
    assert "current_output_inventory" not in dumped
    assert "synthetic local QA output" not in dumped
    assert "Emlisです" not in dumped
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(parsed)


def test_p3_7_meta_only_guard_rejects_body_keys_and_contract_breaking_flags() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_first_repair_design_meta_only_20260609(
            {"schema_version": "unsafe", "comment_text": "actual display body must not enter P3-7"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_first_repair_design_meta_only_20260609(
            {"schema_version": "unsafe", "raw_input_included": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_first_repair_design_meta_only_20260609(
            {"schema_version": "unsafe", "gate_relaxed": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_first_repair_design_meta_only_20260609(
            {"schema_version": "unsafe", "case_specific_runtime_branch": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_first_repair_design_meta_only_20260609(
            {"schema_version": "unsafe", "implementation_change_applied": True}
        )


def test_p3_7_rejects_blind_qa_material_if_body_key_is_smuggled_before_design() -> None:
    events = _events_from_fake_capture()
    split = build_product_readfeel_p3_verdict_split_20260609(
        sanitized_current_output_events=events,
        run_id="p3-7-unsafe-material-split",
    )
    reviews = build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(verdict_split=split)
    unsafe_review = dict(reviews[0])
    unsafe_review["comment_text"] = "actual display body must never enter ratings material"

    with pytest.raises(ValueError):
        build_product_readfeel_p3_blind_qa_ratings_review_20260609(
            verdict_split=split,
            blind_qa_reviews=[unsafe_review],
            run_id="p3-7-unsafe-material",
        )


def test_p3_7_preserves_baseline_family_context_from_source_ledger() -> None:
    events = _events_from_fake_capture()
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    ledger = _ledger_from_events(events, run_id="p3-7-family-context")
    design = build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_ledger=ledger,
        run_id="p3-7-family-context-design",
    )

    assert ledger["summary"]["all_required_families_present"] is True
    assert set(ledger["summary"]["observed_required_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert design["summary"]["p3_1_baseline_case_matrix_used"] is True
    assert "daily_unpleasant" in design["summary"]["families"]
    assert design["design_items"][0]["baseline_subset_case_ids"]
    assert design["design_items"][0]["material_quality_not_forced_to_eligible"] is True
    assert design["design_items"][0]["visible_material_slots_must_not_collapse_to_question_only"] is True
    assert design["design_items"][0]["source_unavailable_not_recast_as_normal_rebuild"] is True
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(design)
