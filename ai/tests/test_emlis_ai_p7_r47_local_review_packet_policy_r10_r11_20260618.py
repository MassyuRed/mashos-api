# -*- coding: utf-8 -*-
"""P7-R47 R10/R11 P6 readfeel and real-device modal packet policy freeze."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P6_LIMITED_READFEEL_RATING_AXES,
    P6_LIMITED_READFEEL_REVIEW_FAMILIES,
    P6_LIMITED_READFEEL_TARGETS,
    P6_NO_CONNECT_FAMILIES,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_P6_FIRST_FORMAL_MINIMUMS,
    P7_R47_P6_LIMITED_HUMAN_READFEEL_PACKET_POLICY_SCHEMA_VERSION,
    P7_R47_P6_REVIEWER_FACING_ALLOWED_FIELD_REFS,
    P7_R47_P6_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
    P7_R47_R10_R11_IMPLEMENTED_STEPS,
    P7_R47_R10_R11_NEXT_REQUIRED_STEP_REF,
    P7_R47_R10_R11_NOT_YET_IMPLEMENTED_STEPS,
    P7_R47_R10_R11_P6_REAL_DEVICE_PACKET_POLICY_SCHEMA_VERSION,
    P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS,
    P7_R47_REAL_DEVICE_MODAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION,
    P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS,
    P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILIES,
    P7_R47_REAL_DEVICE_REVIEWER_FACING_ALLOWED_FIELD_REFS,
    P7_R47_REAL_DEVICE_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
    assert_p7_r47_p6_limited_human_readfeel_packet_policy_contract,
    assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract,
    assert_p7_r47_real_device_modal_review_packet_policy_contract,
    build_p7_r47_p6_limited_human_readfeel_packet_policy,
    build_p7_r47_r10_r11_p6_real_device_packet_policy_freeze,
    build_p7_r47_real_device_modal_review_packet_policy,
)

SECRET_INPUT = "R47 R10/R11 raw input must never enter body-free materials"
SECRET_SURFACE = "R47 R10/R11 visible Emlis surface must remain local-only"
SECRET_NOTE = "R47 R10/R11 reviewer note must remain local-only"
SECRET_SCREENSHOT = "R47 R10/R11 screenshot body must never enter body-free materials"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_or_release_promotion(value: object) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_NOTE not in dumped
    assert SECRET_SCREENSHOT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"visible_text":' not in dumped
    assert '"screenshot_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"reviewer_notes":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def test_r47_r10_p6_packet_policy_matches_r46_handoff_families_axes_and_thresholds() -> None:
    policy = build_p7_r47_p6_limited_human_readfeel_packet_policy()
    assert_p7_r47_p6_limited_human_readfeel_packet_policy_contract(policy)

    assert policy["schema_version"] == P7_R47_P6_LIMITED_HUMAN_READFEEL_PACKET_POLICY_SCHEMA_VERSION
    assert policy["packet_kind"] == "p6_limited_human_readfeel_local_review_packet"
    assert policy["review_kind"] == "p6_structure_insight_limited_readfeel"
    assert tuple(policy["review_family_refs"]) == P6_LIMITED_READFEEL_REVIEW_FAMILIES
    assert tuple(policy["no_connect_family_refs"]) == P6_NO_CONNECT_FAMILIES
    assert tuple(policy["rating_axis_refs"]) == P6_LIMITED_READFEEL_RATING_AXES
    assert policy["rating_axis_target_thresholds"] == P6_LIMITED_READFEEL_TARGETS

    minimums = policy["first_formal_review_minimums"]
    assert minimums == P7_R47_P6_FIRST_FORMAL_MINIMUMS
    assert minimums["minimum_total_cases"] == 18
    assert minimums["minimum_review_family_cases"] == {
        "structure_question": 4,
        "long_meaning_arc": 4,
        "self_understanding_follow": 4,
    }
    assert minimums["minimum_no_connect_audit_cases"] == {
        "daily_unpleasant": 1,
        "daily_positive": 1,
        "positive_only": 1,
        "low_information": 1,
        "limited_grounding_insufficient": 1,
        "safety_triage_required": 1,
    }

    assert policy["p5_human_blind_qa_confirmed_required_before_p6_start"] is True
    assert policy["p6_waits_for_p5_confirmation"] is True
    assert policy["visible_expansion_allowed"] is False
    assert policy["history_used_as_fact_allowed"] is False
    assert policy["p5_history_line_substitution_allowed"] is False
    assert policy["p6_limited_human_readfeel_start_allowed"] is False
    assert policy["p6_limited_human_readfeel_confirmed"] is False
    assert policy["actual_human_review_run_here"] is False
    assert policy["release_allowed"] is False

    assert tuple(policy["reviewer_facing_allowed_field_refs"]) == P7_R47_P6_REVIEWER_FACING_ALLOWED_FIELD_REFS
    assert tuple(policy["reviewer_facing_forbidden_field_refs"]) == P7_R47_P6_REVIEWER_FACING_FORBIDDEN_FIELD_REFS
    assert not (set(policy["reviewer_facing_allowed_field_refs"]) & set(policy["reviewer_facing_forbidden_field_refs"]))
    _assert_no_body_or_release_promotion(policy)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda p: p.__setitem__("review_family_refs", list(P6_LIMITED_READFEEL_REVIEW_FAMILIES[:-1])),
        lambda p: p.__setitem__("no_connect_family_refs", list(P6_NO_CONNECT_FAMILIES[:-1])),
        lambda p: p.__setitem__("rating_axis_refs", list(P6_LIMITED_READFEEL_RATING_AXES[:-1])),
        lambda p: p["first_formal_review_minimums"].__setitem__("minimum_total_cases", 17),
        lambda p: p["minimum_review_family_case_counts"].__setitem__("structure_question", 3),
        lambda p: p.__setitem__("visible_expansion_allowed", True),
        lambda p: p.__setitem__("history_used_as_fact_allowed", True),
        lambda p: p.__setitem__("p6_limited_human_readfeel_start_allowed", True),
        lambda p: p.__setitem__("p6_limited_human_readfeel_confirmed", True),
    ],
)
def test_r47_r10_p6_packet_policy_rejects_family_axis_minimum_or_runtime_drift(mutator) -> None:  # type: ignore[no-untyped-def]
    policy = build_p7_r47_p6_limited_human_readfeel_packet_policy()
    mutator(policy)
    with pytest.raises(ValueError):
        assert_p7_r47_p6_limited_human_readfeel_packet_policy_contract(policy)


def test_r47_r11_real_device_modal_policy_preserves_rn_api_display_boundaries() -> None:
    policy = build_p7_r47_real_device_modal_review_packet_policy()
    assert_p7_r47_real_device_modal_review_packet_policy_contract(policy)

    assert policy["schema_version"] == P7_R47_REAL_DEVICE_MODAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION
    assert policy["packet_kind"] == "real_device_modal_review_local_packet"
    assert tuple(policy["required_manual_review_family_refs"]) == P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILIES
    assert tuple(policy["readfeel_axis_refs"]) == P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS
    assert policy["first_review_minimums"] == P7_R47_REAL_DEVICE_FIRST_REVIEW_MINIMUMS
    assert policy["minimum_total_cases_first_review"] == 5
    assert policy["minimum_device_contexts"] == 1
    assert policy["visible_payload_source_public_ref"] == "input_feedback.comment_text"
    assert policy["input_feedback_comment_text_source_required"] is True
    assert policy["rn_title_preserved_required"] is True
    assert policy["rn_display_condition_preserved_required"] is True
    assert policy["public_top_level_shape_preserved_required"] is True
    assert policy["rn_visible_contract_changed"] is False
    assert policy["api_response_key_added"] is False
    assert policy["db_schema_changed"] is False
    assert policy["visible_payload_source_changed"] is False
    assert policy["gate_relaxed"] is False
    assert policy["screenshot_local_only"] is True
    assert policy["visible_modal_text_local_only"] is True
    assert policy["screenshot_or_visible_body_export_allowed"] is False
    assert policy["body_free_readfeel_axes_only"] is True
    assert policy["real_device_modal_review_start_allowed"] is False
    assert policy["actual_real_device_review_run_here"] is False
    assert policy["release_allowed"] is False

    assert tuple(policy["reviewer_facing_allowed_field_refs"]) == P7_R47_REAL_DEVICE_REVIEWER_FACING_ALLOWED_FIELD_REFS
    assert tuple(policy["reviewer_facing_forbidden_field_refs"]) == P7_R47_REAL_DEVICE_REVIEWER_FACING_FORBIDDEN_FIELD_REFS
    assert not (set(policy["reviewer_facing_allowed_field_refs"]) & set(policy["reviewer_facing_forbidden_field_refs"]))
    _assert_no_body_or_release_promotion(policy)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda p: p.__setitem__("required_manual_review_family_refs", list(P7_R47_REAL_DEVICE_REQUIRED_MANUAL_REVIEW_FAMILIES[:-1])),
        lambda p: p.__setitem__("readfeel_axis_refs", list(P7_R47_REAL_DEVICE_READFEEL_AXIS_REFS[:-1])),
        lambda p: p["first_review_minimums"].__setitem__("minimum_total_cases_first_review", 4),
        lambda p: p.__setitem__("visible_payload_source_public_ref", "public_meta.comment_text"),
        lambda p: p.__setitem__("rn_visible_contract_changed", True),
        lambda p: p.__setitem__("api_response_key_added", True),
        lambda p: p.__setitem__("screenshot_or_visible_body_export_allowed", True),
        lambda p: p.__setitem__("real_device_modal_review_start_allowed", True),
        lambda p: p.__setitem__("real_device_modal_review_confirmed", True),
    ],
)
def test_r47_r11_real_device_modal_policy_rejects_contract_or_runtime_drift(mutator) -> None:  # type: ignore[no-untyped-def]
    policy = build_p7_r47_real_device_modal_review_packet_policy()
    mutator(policy)
    with pytest.raises(ValueError):
        assert_p7_r47_real_device_modal_review_packet_policy_contract(policy)


def test_r47_r10_r11_combined_policy_freeze_advances_next_step_to_r12_but_keeps_review_closed() -> None:
    freeze = build_p7_r47_r10_r11_p6_real_device_packet_policy_freeze()
    assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R47_R10_R11_P6_REAL_DEVICE_PACKET_POLICY_SCHEMA_VERSION
    assert tuple(freeze["implemented_steps"]) == P7_R47_R10_R11_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == P7_R47_R10_R11_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["implemented_steps"][-2:] == [
        "R10_p6_limited_human_readfeel_packet_policy",
        "R11_real_device_modal_review_packet_policy",
    ]
    assert freeze["not_yet_implemented_steps"][0] == "R12_r46_next_decision_ledger_connection"
    assert freeze["next_required_step"] == P7_R47_R10_R11_NEXT_REQUIRED_STEP_REF
    assert freeze["p6_limited_human_readfeel_packet_policy_fixed"] is True
    assert freeze["real_device_modal_review_packet_policy_fixed"] is True
    assert freeze["p6_first_formal_review_minimum_total_cases"] == 18
    assert freeze["real_device_minimum_total_cases_first_review"] == 5
    assert freeze["local_review_packet_policy_ready"] is False
    assert freeze["policy_ready"] is False
    assert freeze["r47_policy_ready"] is False
    assert freeze["p5_human_blind_qa_start_allowed_after_r10_r11"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p6_limited_human_readfeel_confirmed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["real_device_modal_review_confirmed"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_real_device_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
    _assert_no_body_or_release_promotion(freeze)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_SURFACE),
        ("visible_text", SECRET_SURFACE),
        ("screenshot_body", SECRET_SCREENSHOT),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter combined freeze"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("p6_limited_human_readfeel_confirmed", True),
        ("real_device_modal_review_confirmed", True),
        ("actual_real_device_review_run_here", True),
    ],
)
def test_r47_r10_r11_combined_policy_rejects_body_keys_or_release_review_promotion(key: str, value: object) -> None:
    freeze = build_p7_r47_r10_r11_p6_real_device_packet_policy_freeze()
    freeze[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_r10_r11_p6_real_device_packet_policy_freeze_contract(freeze)
