from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_repair_priority_ledger import (
    PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609,
    PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609,
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609,
    build_product_readfeel_p3_repair_priority_ledger_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_P2_RED,
    build_product_readfeel_p3_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609 import (
    build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609,
    build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_local_output_capture_20260609 import (
    build_product_readfeel_p3_local_output_capture_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609 import (
    build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609,
    dump_product_readfeel_p3_repair_priority_ledger_summary_from_blind_qa_20260609,
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
        run_id="p3-6-capture-test",
    )
    return [dict(event) for event in capture["sanitized_current_output_events"]]


def _append_reason(event: dict[str, Any], reason: str) -> None:
    event["reason_codes"] = [*list(event.get("reason_codes") or []), reason]


def _split_material_and_ledger_from_events(events: list[dict[str, Any]], *, run_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
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
    ledger = build_product_readfeel_p3_repair_priority_ledger_20260609(
        blind_qa_material=material,
        verdict_split=split,
        run_id=f"{run_id}-ledger",
    )
    return split, material, ledger


def test_p3_6_builds_repair_priority_ledger_from_p3_5_ratings_and_p3_4_verdicts() -> None:
    ledger = build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609(
        renderer=_fake_renderer,
        run_id="p3-6-ledger-base-test",
    )
    summary = ledger["summary"]

    assert ledger["schema_version"] == PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609
    assert ledger["source_step"] == PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609
    assert summary["schema_version"] == PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609
    assert summary["case_count"] == 60
    assert summary["review_count"] == 60
    assert set(summary["observed_required_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert summary["missing_required_families"] == []
    assert summary["first_repair_targets_limited_to_max_two"] is True
    assert summary["target_file_candidates_visible"] is True
    assert summary["do_not_touch_files_visible"] is True
    assert summary["forbidden_fix_paths_visible"] is True
    assert summary["gate_relaxation_excluded_from_fix_plan"] is True
    assert summary["fixed_template_fix_excluded"] is True
    assert summary["case_specific_runtime_branch_excluded"] is True
    assert summary["p5_history_line_not_used_to_mask_current_input_gap"] is True
    assert summary["p3_4_verdict_split_used"] is True
    assert summary["p3_5_blind_qa_ratings_only_review_used"] is True
    assert summary["p3_6_repair_priority_ledger_applied"] is True
    assert ledger["do_not_touch_files"]
    assert ledger["forbidden_fix_paths"]
    assert ledger["comment_text_body_included"] is False
    assert ledger["raw_input_included"] is False
    assert ledger["candidate_body_included"] is False
    assert ledger["product_gate_ready"] is False
    assert ledger["public_release_applied"] is False
    assert len(ledger["items"]) <= 2
    for item in ledger["items"]:
        assert item["target_file_candidates"]
        assert item["forbidden_fix_paths"]
        assert item["comment_text_body_included"] is False
        assert item["raw_input_included"] is False
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(ledger)


def test_p3_6_keeps_p2_red_as_first_priority_and_blocks_p3_repair() -> None:
    events = _events_from_fake_capture()
    self_denial = next(event for event in events if event["family"] == "self_denial")
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    mixed_emotion = next(event for event in events if event["family"] == "mixed_emotion")
    _append_reason(self_denial, "self_denial_identity_claim_risk")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    _append_reason(mixed_emotion, "generic_reception_surface")

    split, _material, ledger = _split_material_and_ledger_from_events(events, run_id="p3-6-p2-red")
    summary = ledger["summary"]
    first = ledger["items"][0]

    assert split["summary"]["p2_red_count"] >= 1
    assert summary["p2_red_present"] is True
    assert summary["p2_red_blocks_p3_repair"] is True
    assert summary["p3_repair_can_start"] is False
    assert summary["decision"] == "return_to_p2_surface_safety_before_p3_repair"
    assert first["verdict_layer"] == VERDICT_LAYER_P2_RED
    assert first["blocker_id"] == "surface_breakage"
    assert first["repair_action"] == "return_to_p2_or_contract_repair_before_product_readfeel_changes"
    assert first["p3_repair_allowed_before_p2_clear"] is False
    assert "mashos-api/ai/services/ai_inference/emlis_ai_visible_surface_acceptance_gate.py" in first["target_file_candidates"]
    assert "gate_relaxation" in first["forbidden_fix_paths"]
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(ledger)


def test_p3_6_prioritizes_current_input_readfeel_blockers_before_p5_or_p6_backlog_when_no_red() -> None:
    events = _events_from_fake_capture()
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    mixed_emotion = next(event for event in events if event["family"] == "mixed_emotion")
    structure_question = next(event for event in events if event["family"] == "structure_question")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    _append_reason(mixed_emotion, "generic_reception_surface")
    _append_reason(structure_question, "family_temperature_flattened")

    _split, _material, ledger = _split_material_and_ledger_from_events(events, run_id="p3-6-p3-priority")
    summary = ledger["summary"]
    targets = [item["blocker_id"] for item in ledger["items"]]

    assert summary["p2_red_present"] is False
    assert summary["p3_repair_can_start"] is True
    assert summary["decision"] == "start_p3_repair_with_max_two_targets"
    assert targets == ["rich_input_low_information_overroute", "generic_reception_surface"]
    assert len(targets) == 2
    assert ledger["items"][0]["families"] == ["daily_unpleasant"]
    assert "mashos-api/ai/services/ai_inference/emlis_ai_input_material_bundle.py" in ledger["items"][0]["target_file_candidates"]
    assert "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py" in ledger["items"][1]["target_file_candidates"]
    assert "history_line_masking_current_input_gap" in ledger["items"][0]["forbidden_fix_paths"]
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(ledger)


def test_p3_6_can_build_from_p3_5_ratings_only_material_without_retaining_source_rows() -> None:
    events = _events_from_fake_capture()
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    split, material, _ledger_with_split = _split_material_and_ledger_from_events(events, run_id="p3-6-material-only-source")

    ledger = build_product_readfeel_p3_repair_priority_ledger_20260609(
        blind_qa_material=material,
        run_id="p3-6-material-only-ledger",
    )

    assert material["source_verdict_row_count"] == 60
    assert ledger["source_verdict_row_count"] == 0
    assert ledger["source_review_row_count"] == 60
    assert ledger["summary"]["review_count"] == 60
    assert ledger["summary"]["first_repair_targets_limited_to_max_two"] is True
    assert ledger["summary"]["ratings_only_review_connected"] is True
    assert "review_rows" not in ledger["public_summary"]
    assert "verdict_rows" not in ledger["public_summary"]
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(ledger)
    assert split["summary"]["verdict_row_count"] == 60


def test_p3_6_public_summary_dump_excludes_rows_inventory_and_bodies() -> None:
    events = _events_from_fake_capture()
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    split, material, _ledger = _split_material_and_ledger_from_events(events, run_id="p3-6-summary-dump-source")

    dumped = dump_product_readfeel_p3_repair_priority_ledger_summary_from_blind_qa_20260609(
        verdict_split=split,
        blind_qa_material=material,
        run_id="p3-6-summary-dump",
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609
    assert parsed["case_count"] == 60
    assert parsed["first_repair_targets_limited_to_max_two"] is True
    assert parsed["comment_text_body_included"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["candidate_body_included"] is False
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert "first_repair_target_items" in parsed
    assert "review_rows" not in parsed
    assert "verdict_rows" not in parsed
    assert "items" not in parsed
    assert "current_output_inventory" not in dumped
    assert "synthetic local QA output" not in dumped
    assert "Emlisです" not in dumped
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(parsed)


def test_p3_6_meta_only_guard_rejects_body_keys_and_contract_breaking_flags() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(
            {"schema_version": "unsafe", "comment_text": "本文を入れてはいけない"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(
            {"schema_version": "unsafe", "raw_input_included": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(
            {"schema_version": "unsafe", "gate_relaxed": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(
            {"schema_version": "unsafe", "case_specific_runtime_branch": True}
        )
