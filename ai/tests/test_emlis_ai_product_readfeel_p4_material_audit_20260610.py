from __future__ import annotations

import json

import pytest

from emlis_ai_input_material_bundle import MATERIAL_QUALITY_ELIGIBLE, MATERIAL_QUALITY_LOW_INFORMATION
from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_STRUCTURE_QUESTION,
)
from emlis_ai_product_readfeel_p4_material_audit import (
    BLOCKER_QUESTION_ONLY_SURFACE,
    BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE,
    BLOCKER_SOURCE_UNAVAILABLE_RECAST_AS_NORMAL_REBUILD,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_EVENT_VERSION_20260610,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610,
    SLOT_GROUP_EVENTISH,
    SLOT_GROUP_REACTIONISH,
    SLOT_GROUP_STRUCTURE_QUESTION,
    assert_product_readfeel_p4_material_audit_meta_only_20260610,
    build_product_readfeel_p4_material_audit_event_20260610,
    build_product_readfeel_p4_material_audit_public_summary_20260610,
)
from emlis_ai_public_surface_requirement import SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
from fixtures.emlis_ai_product_readfeel_p4_material_audit_20260610 import (
    build_product_readfeel_p4_material_audit_from_p4_1_20260610,
    dump_product_readfeel_p4_material_audit_summary_from_p4_1_20260610,
)


def _by_id(audit: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(event["case_ref_id"]): event
        for event in audit["material_audit_events"]  # type: ignore[index]
    }


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_p4_2_material_audit_builds_body_free_events_from_p4_1_targets() -> None:
    audit = build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        run_id="p4_2_material_audit_default"
    )
    summary = audit["summary"]
    events = audit["material_audit_events"]
    events_by_id = _by_id(audit)

    assert audit["schema_version"] == PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610
    assert audit["source_step"] == PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610
    assert audit["audit_profile"] == PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610
    assert summary["schema_version"] == PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610
    assert summary["p4_0_connection_freeze_respected"] is True
    assert summary["p4_1_target_case_selection_used"] is True
    assert summary["p4_2_material_audit_ready"] is True
    assert summary["p5_connection_allowed"] is False
    assert summary["selected_case_count"] == len(events)
    assert summary["audited_case_count"] == len(events)
    assert summary["family_counts"][FAMILY_DAILY_UNPLEASANT] >= 5
    assert summary["family_counts"][FAMILY_STRUCTURE_QUESTION] >= 5
    assert summary["p3_reported_rich_input_low_information_overroute_count"] >= 10
    assert summary["rich_input_candidate_count"] >= 10
    assert summary["p4_3_surface_requirement_boundary_review_ready"] is True

    daily = events_by_id["p3-daily_unpleasant-001"]
    structure = events_by_id["p3-structure_question-003"]

    for event in (daily, structure):
        assert event["schema_version"] == PRODUCT_READFEEL_P4_MATERIAL_AUDIT_EVENT_VERSION_20260610
        assert event["rich_input_candidate"] is True
        assert event["visible_material_slot_count"] >= 3
        assert SLOT_GROUP_EVENTISH in event["visible_slot_groups_present"]
        assert SLOT_GROUP_REACTIONISH in event["visible_slot_groups_present"]
        assert event["p3_reported_rich_input_low_information_overroute"] is True
        assert event["low_information_route_selected"] is False
        assert event["rich_input_low_information_overroute_detected"] is False
        assert event["raw_input_included"] is False
        assert event["comment_text_body_included"] is False
        assert event["p4_runtime_tuning_applied"] is False
        assert event["p5_visible_surface_strengthened"] is False
        assert event["gate_relaxed"] is False

    assert SLOT_GROUP_STRUCTURE_QUESTION in events_by_id["p3-structure_question-001"]["visible_slot_groups_present"]
    assert_product_readfeel_p4_material_audit_meta_only_20260610(audit)


def test_p4_2_reproduces_rich_input_low_information_overroute_with_body_free_route_replay() -> None:
    audit = build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        run_id="p4_2_reproduce_low_info_overroute",
        audit_route_overrides_by_case_ref_id={
            "p3-daily_unpleasant-001": {
                "material_quality": MATERIAL_QUALITY_LOW_INFORMATION,
                "response_kind": "low_information_observation",
                "audit_replay_only": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "gate_relaxed": False,
            }
        },
    )
    summary = audit["summary"]
    event = _by_id(audit)["p3-daily_unpleasant-001"]
    surface = event["public_surface_requirement"]

    assert event["material_quality"] == MATERIAL_QUALITY_ELIGIBLE
    assert event["route_material_quality_family"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert surface["surface_requirement_family"] == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
    assert event["rich_input_candidate"] is True
    assert event["low_information_route_selected"] is True
    assert event["rich_input_low_information_overroute_detected"] is True
    assert event["audit_replay_route_override_used"] is True
    assert event["audit_replay_only"] is True
    assert BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE in event["detected_blockers"]
    assert "p3-daily_unpleasant-001" in summary["rich_input_low_information_overroute_detected_case_refs"]
    assert summary["rich_input_low_information_overroute_detected_count"] == 1
    assert_product_readfeel_p4_material_audit_meta_only_20260610(audit)


def test_p4_2_true_low_information_control_is_not_marked_as_rich_overroute() -> None:
    selected_case = {
        "case_ref_id": "p3-low_information_short-999",
        "family": FAMILY_LOW_INFORMATION_SHORT,
        "coverage_slices": ["free_tier", "render_default_path"],
        "selection_groups": ["boundary_regression"],
        "blocker_ids": ["low_information_short_boundary_regression"],
        "target_layers": ["input_material_bundle", "public_surface_requirement"],
        "main_target_case": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "gate_relaxed": False,
    }
    local_case = {
        "case_id": "p3-low_information_short-999",
        "family": FAMILY_LOW_INFORMATION_SHORT,
        "coverage_slices": ["free_tier", "render_default_path"],
        "current_input": {
            "id": "p3-low_information_short-999",
            "memo": "疲れた",
            "memo_action": "",
            "emotion_details": [{"type": "疲れ", "strength": "medium"}],
            "category": [],
            "synthetic_case_material": True,
        },
    }

    event = build_product_readfeel_p4_material_audit_event_20260610(
        selected_case=selected_case,
        local_case_material=local_case,
        run_id="p4_2_true_low_information_control",
    )

    assert event["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert event["low_information_route_selected"] is True
    assert event["rich_input_candidate"] is False
    assert event["rich_input_low_information_overroute_detected"] is False
    assert BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE not in event["detected_blockers"]
    assert_product_readfeel_p4_material_audit_meta_only_20260610(event)


def test_p4_2_keeps_limited_grounding_and_source_unavailable_boundaries_visible() -> None:
    audit = build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        run_id="p4_2_boundary_visibility"
    )
    summary = audit["summary"]
    events = audit["material_audit_events"]

    limited_events = [event for event in events if "limited_grounding" in event["coverage_slices"]]
    source_unavailable_events = [
        event for event in events if "source_unavailable_high_information" in event["coverage_slices"]
    ]

    assert limited_events
    assert any(event["limited_grounding_requested"] is True for event in limited_events)
    assert source_unavailable_events
    assert summary["source_unavailable_boundary_case_count"] >= 1
    assert summary["source_unavailable_boundary_kept_count"] == summary["source_unavailable_boundary_case_count"]
    assert all(event["source_unavailable_boundary_kept"] is True for event in source_unavailable_events)
    assert all(BLOCKER_SOURCE_UNAVAILABLE_RECAST_AS_NORMAL_REBUILD not in event["detected_blockers"] for event in source_unavailable_events)
    assert_product_readfeel_p4_material_audit_meta_only_20260610(audit)


def test_p4_2_can_reproduce_question_surface_collapse_without_comment_text_body() -> None:
    audit = build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        run_id="p4_2_question_surface_replay",
        surface_observations_by_case_ref_id={
            "p3-structure_question-003": {
                "question_only_surface_detected": True,
                "question_dominance_blocker": BLOCKER_QUESTION_ONLY_SURFACE,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "gate_relaxed": False,
            }
        },
    )
    event = _by_id(audit)["p3-structure_question-003"]

    assert event["rich_input_candidate"] is True
    assert event["question_only_surface_detected"] is True
    assert event["question_dominance_blocker"] == BLOCKER_QUESTION_ONLY_SURFACE
    assert event["rich_input_low_information_overroute_detected"] is True
    assert BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE in event["detected_blockers"]
    assert BLOCKER_QUESTION_ONLY_SURFACE in event["detected_blockers"]
    assert_product_readfeel_p4_material_audit_meta_only_20260610(audit)


def test_p4_2_public_summary_and_dump_keep_case_refs_without_bodies() -> None:
    audit = build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        run_id="p4_2_public_summary"
    )
    public_summary = build_product_readfeel_p4_material_audit_public_summary_20260610(audit)
    dumped = dump_product_readfeel_p4_material_audit_summary_from_p4_1_20260610(
        run_id="p4_2_public_summary_dump"
    )
    parsed = json.loads(dumped)

    assert public_summary["schema_version"] == PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610
    assert parsed["p5_connection_allowed"] is False
    assert parsed["p4_2_material_audit_ready"] is True
    assert parsed["audited_case_count"] == len(parsed["audited_case_refs"])
    assert parsed["p4_runtime_tuning_applied"] is False
    assert parsed["p5_visible_surface_strengthened"] is False
    assert '"current_input"' not in dumped
    assert '"memo"' not in dumped
    assert '"memo_action"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"candidate_body"' not in dumped
    assert "会議で軽く流された" not in dumped
    assert "Emlisです" not in dumped
    assert_product_readfeel_p4_material_audit_meta_only_20260610(public_summary)
    assert_product_readfeel_p4_material_audit_meta_only_20260610(parsed)


def test_p4_2_guard_rejects_raw_bodies_comment_bodies_and_runtime_mutation_flags() -> None:
    audit = build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        run_id="p4_2_guard_source"
    )

    unsafe_raw = dict(audit)
    unsafe_raw["raw_input"] = "出してはいけない"
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_material_audit_meta_only_20260610(unsafe_raw)

    unsafe_comment = dict(audit)
    unsafe_comment["material_audit_events"] = [dict(audit["material_audit_events"][0])]
    unsafe_comment["material_audit_events"][0]["comment_text"] = "Emlis本文をここに残してはいけない"
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_material_audit_meta_only_20260610(unsafe_comment)

    unsafe_p5 = dict(audit)
    unsafe_p5["p5_visible_surface_strengthened"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_material_audit_meta_only_20260610(unsafe_p5)

    unsafe_gate = dict(audit)
    unsafe_gate["summary"] = dict(unsafe_gate["summary"])
    unsafe_gate["summary"]["gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_material_audit_meta_only_20260610(unsafe_gate)

    assert '"raw_input":' not in _dump(audit)
