from __future__ import annotations

import json

import pytest

from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_SELF_DENIAL,
    FAMILY_STRUCTURE_QUESTION,
)
from emlis_ai_product_readfeel_p4_family_tuning_policy import (
    FAMILY_LIMITED_GROUNDING,
    get_product_readfeel_p4_family_policy_20260610,
)
from emlis_ai_product_readfeel_p4_surface_signature_audit import (
    BLOCKER_COMFORT_ONLY_SURFACE,
    BLOCKER_FAMILY_TEMPERATURE_FLATTENED,
    BLOCKER_FORBIDDEN_SURFACE_CLASS_PRESENT,
    BLOCKER_GENERIC_RECEPTION_SURFACE,
    BLOCKER_MIRROR_ONLY_SURFACE,
    BLOCKER_QUESTION_BEFORE_RECEPTION,
    BLOCKER_QUESTION_ONLY_SURFACE,
    BLOCKER_RECEPTION_ANCHOR_MISSING,
    BLOCKER_REPEATED_SURFACE_SIGNATURE,
    BLOCKER_REQUIRED_ANCHOR_MISSING,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_EVENT_VERSION_20260610,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_VERSION_20260610,
    VERDICT_PASS,
    VERDICT_REPAIR_REQUIRED,
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610,
    build_product_readfeel_p4_surface_signature_audit_event_20260610,
    build_product_readfeel_p4_surface_signature_audit_public_summary_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_surface_signature_audit_20260610 import (
    build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610,
    build_product_readfeel_p4_surface_signature_observations_20260610,
    dump_product_readfeel_p4_surface_signature_audit_summary_from_p4_1_p4_2_p4_4_20260610,
)


def _events_by_id(audit: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(event["case_ref_id"]): event
        for event in audit["surface_signature_events"]  # type: ignore[index]
    }


def test_p4_5_surface_signature_audit_builds_body_free_packet_from_p4_1_p4_2_p4_4() -> None:
    audit = build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610(
        run_id="p4_5_surface_signature_default"
    )
    summary = audit["summary"]
    events = audit["surface_signature_events"]

    assert audit["schema_version"] == PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_VERSION_20260610
    assert audit["source_step"] == PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610
    assert audit["audit_profile"] == PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610
    assert summary["schema_version"] == PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610
    assert summary["audited_case_count"] == len(events)
    assert summary["family_counts"][FAMILY_DAILY_UNPLEASANT] >= 5
    assert summary["family_counts"][FAMILY_STRUCTURE_QUESTION] >= 5
    assert summary["generic_reception_surface_detected_count"] >= 3
    assert summary["repeated_surface_signature_detected_count"] >= 3
    assert summary["surface_specificity_correction_plan_ready"] is True
    assert summary["closing_only_variation_not_sufficient"] is True
    assert summary["p4_0_connection_freeze_respected"] is True
    assert summary["p4_1_target_case_selection_used"] is True
    assert summary["p4_2_material_audit_used_for_context"] is True
    assert summary["p4_3_surface_requirement_boundary_respected"] is True
    assert summary["p4_4_family_tuning_policy_used"] is True
    assert summary["p4_5_surface_specificity_audit_ready"] is True
    assert summary["p5_connection_allowed"] is False
    assert audit["runtime_owner_reference_only"] is True
    assert audit["runtime_policy_connection_applied"] is False
    assert audit["runtime_mutation_applied_by_p4_5"] is False
    assert audit["p4_runtime_tuning_applied"] is False
    assert audit["p5_visible_surface_strengthened"] is False
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(audit)


def test_p4_5_detects_generic_reception_and_repeated_signature_without_exact_output() -> None:
    audit = build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610(
        run_id="p4_5_generic_repeated_detection"
    )
    events = _events_by_id(audit)
    daily = events["p3-daily_unpleasant-001"]

    assert daily["schema_version"] == PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_EVENT_VERSION_20260610
    assert daily["family"] == FAMILY_DAILY_UNPLEASANT
    assert daily["p3_reported_generic_reception_surface"] is True
    assert daily["generic_reception_surface_detected"] is True
    assert daily["repeated_surface_signature_detected"] is True
    assert daily["family_temperature_flattened_detected"] is True
    assert daily["required_anchor_missing_detected"] is True
    assert daily["verdict"] == VERDICT_REPAIR_REQUIRED
    assert BLOCKER_GENERIC_RECEPTION_SURFACE in daily["detected_blockers"]
    assert BLOCKER_REPEATED_SURFACE_SIGNATURE in daily["detected_blockers"]
    assert BLOCKER_FAMILY_TEMPERATURE_FLATTENED in daily["detected_blockers"]
    assert BLOCKER_REQUIRED_ANCHOR_MISSING in daily["detected_blockers"]
    assert BLOCKER_COMFORT_ONLY_SURFACE in daily["detected_blockers"]
    assert BLOCKER_FORBIDDEN_SURFACE_CLASS_PRESENT in daily["detected_blockers"]

    correction = daily["surface_specificity_correction_requirements"]
    assert correction["correction_required"] is True
    assert "event_anchor" in correction["restore_missing_anchor_roles"]
    assert "emotion_direction_anchor" in correction["restore_missing_anchor_roles"]
    assert "complete_surface_realizer" in correction["target_layers"]
    assert correction["closing_only_variation_not_sufficient"] is True
    assert correction["fixed_sentence_template_allowed"] is False
    assert correction["exact_output_allowed"] is False
    assert correction["case_specific_runtime_branch_allowed"] is False
    assert correction["apply_to_runtime_now"] is False
    assert daily["exact_comment_text_required"] is False
    assert daily["fixed_sentence_template_added"] is False
    assert daily["case_specific_runtime_branch"] is False
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(daily)


def test_p4_5_structure_question_question_surface_is_boundary_not_comfort_rewrite() -> None:
    audit = build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610(
        run_id="p4_5_structure_question_question_boundary"
    )
    events = _events_by_id(audit)
    structure = events["p3-structure_question-003"]

    assert structure["family"] == FAMILY_STRUCTURE_QUESTION
    assert structure["section_role_sequence"] == ["reception"]
    assert structure["question_only_surface_detected"] is True
    assert structure["question_before_reception_detected"] is True
    assert structure["reception_anchor_missing_detected"] is True
    assert BLOCKER_QUESTION_ONLY_SURFACE in structure["detected_blockers"]
    assert BLOCKER_QUESTION_BEFORE_RECEPTION in structure["detected_blockers"]
    assert BLOCKER_RECEPTION_ANCHOR_MISSING in structure["detected_blockers"]
    assert structure["verdict"] == VERDICT_REPAIR_REQUIRED
    correction = structure["surface_specificity_correction_requirements"]
    assert "structure_question_anchor" in correction["restore_missing_anchor_roles"]
    assert correction["preserve_expected_section_role_sequence"] == ["observation", "reception"]
    assert correction["question_only_forbidden"] is True
    assert correction["apply_to_runtime_now"] is False
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(structure)


def test_p4_5_family_specific_signature_passes_for_self_denial_low_info_and_limited_grounding_boundaries() -> None:
    audit = build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610(
        run_id="p4_5_family_specific_passes"
    )
    events = _events_by_id(audit)
    self_denial = events["p3-self_denial-001"]
    low_info = events["p3-low_information_short-001"]
    limited = events["p3-structure_question-005"]

    assert self_denial["family"] == FAMILY_SELF_DENIAL
    assert self_denial["verdict"] == VERDICT_PASS
    assert self_denial["surface_specificity_correction_required"] is False
    assert self_denial["generic_reception_surface_detected"] is False
    assert self_denial["repeated_surface_signature_detected"] is False
    assert "self_denial_phrase_as_state_not_fact" in self_denial["observed_anchor_roles"]
    assert "no_identity_claim_marker" in self_denial["observed_anchor_roles"]

    assert low_info["family"] == FAMILY_LOW_INFORMATION_SHORT
    assert low_info["verdict"] == VERDICT_PASS
    assert low_info["question_count"] == 1
    assert low_info["question_position"] == "after_reception_optional"
    assert low_info["question_only_surface_detected"] is False
    assert low_info["material_quality_forced_to_eligible"] is False
    assert low_info["history_line_masks_current_input_gap"] is False

    assert "limited_grounding" in limited["coverage_slices"]
    assert limited["verdict"] == VERDICT_PASS
    assert limited["source_unavailable_boundary_kept"] is True
    assert limited["source_unavailable_recast_as_normal_rebuild"] is False
    assert "limited_grounding_marker" in limited["observed_anchor_roles"]
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(audit)


def test_p4_5_event_builder_can_pass_family_specific_surface_without_fixture_string_route() -> None:
    selected_case = {
        "case_ref_id": "p4-5-daily-unpleasant-pass-001",
        "family": FAMILY_DAILY_UNPLEASANT,
        "coverage_slices": ["anger_or_boundary", "render_default_path"],
        "selection_groups": ["main_target"],
        "blocker_ids": ["generic_reception_surface"],
        "target_layers": ["ratio_policy", "two_stage_section_surface_plan"],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "gate_relaxed": False,
    }
    observation = {
        "section_role_sequence": ["observation", "reception"],
        "opening_shape_family": "daily_unpleasant_event_reaction_opening",
        "closing_shape_family": "daily_unpleasant_reception_closing",
        "observed_temperature_profile": "warm_reception_with_light_observation",
        "observed_anchor_roles": [
            "event_anchor",
            "emotion_direction_anchor",
            "unresolved_weight_anchor",
            "emlis_reception_anchor",
            "no_target_judgement_marker",
        ],
        "observation_anchor_count": 3,
        "reception_anchor_count": 1,
        "generic_empathy_marker_count": 0,
        "question_count": 0,
        "question_position": "none",
        "same_closing_family_repetition_count": 1,
        "same_section_role_sequence_repetition_count": 1,
        "observed_signature_cluster_size": 1,
        "mirror_only_detected": False,
        "comfort_only_surface_detected": False,
        "forbidden_surface_classes_present": [],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "gate_relaxed": False,
    }
    event = build_product_readfeel_p4_surface_signature_audit_event_20260610(
        selected_case=selected_case,
        family_policy=get_product_readfeel_p4_family_policy_20260610(FAMILY_DAILY_UNPLEASANT),
        surface_signature_observation=observation,
        run_id="p4_5_event_pass_without_route",
    )

    assert event["verdict"] == VERDICT_PASS
    assert event["detected_blockers"] == []
    assert event["p3_reported_generic_reception_surface"] is True
    assert event["generic_reception_surface_detected"] is False
    assert event["surface_specificity_correction_required"] is False
    assert event["section_role_sequence_matches_policy"] is True
    assert event["runtime_branching_uses_fixture_strings"] is False
    assert event["fixture_text_used_for_runtime_branching"] is False
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(event)


def test_p4_5_public_summary_and_dump_keep_case_refs_without_bodies() -> None:
    audit = build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610(
        run_id="p4_5_public_summary"
    )
    public_summary = build_product_readfeel_p4_surface_signature_audit_public_summary_20260610(audit)
    dumped = dump_product_readfeel_p4_surface_signature_audit_summary_from_p4_1_p4_2_p4_4_20260610(
        run_id="p4_5_public_summary_dump"
    )
    parsed = json.loads(dumped)

    assert public_summary["schema_version"] == PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610
    assert public_summary["audited_case_count"] >= 20
    assert public_summary["generic_reception_surface_detected_case_refs"]
    assert public_summary["repeated_surface_signature_detected_case_refs"]
    assert public_summary["p4_5_surface_specificity_audit_ready"] is True
    assert public_summary["p5_connection_allowed"] is False
    assert parsed["schema_version"] == PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610
    assert parsed["comment_text_body_included"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["p4_runtime_tuning_applied"] is False
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(public_summary)


def test_p4_5_meta_guard_rejects_body_keys_and_runtime_mutation_flags() -> None:
    with pytest.raises(ValueError, match="raw input"):
        assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
            {"surface_text": "not allowed", "raw_input_included": False},
            source="p4_5_body_guard",
        )

    with pytest.raises(ValueError, match="forbidden true flag"):
        assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
            {"case_ref_id": "p4-5-bad", "p4_runtime_tuning_applied": True},
            source="p4_5_runtime_guard",
        )

    with pytest.raises(ValueError, match="forbidden true flag"):
        assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
            {"case_ref_id": "p4-5-bad", "p5_visible_surface_strengthened": True},
            source="p4_5_p5_guard",
        )
