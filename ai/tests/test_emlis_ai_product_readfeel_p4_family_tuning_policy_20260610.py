from __future__ import annotations

import json

import pytest

from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_POSITIVE,
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_RELATIONSHIP_BOUNDARY,
    FAMILY_SELF_DENIAL,
    FAMILY_STRUCTURE_QUESTION,
)
from emlis_ai_product_readfeel_p4_family_tuning_policy import (
    COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE,
    COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION,
    FAMILY_LIMITED_GROUNDING,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_ITEM_VERSION_20260610,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_PROFILE_20260610,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_VERSION_20260610,
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610,
    build_product_readfeel_p4_family_tuning_policy_public_summary_20260610,
    get_product_readfeel_p4_family_policy_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_family_tuning_policy_20260610 import (
    build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610,
    dump_product_readfeel_p4_family_tuning_policy_summary_from_p4_1_p4_2_20260610,
)


def _policies_by_family(policy_packet: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(policy["family"]): policy
        for policy in policy_packet["family_policies"]  # type: ignore[index]
    }


def _slice_policies_by_slice(policy_packet: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(policy["coverage_slice"]): policy
        for policy in policy_packet["boundary_slice_policies"]  # type: ignore[index]
    }


def test_p4_4_family_tuning_policy_builds_body_free_packet_from_p4_1_and_p4_2() -> None:
    policy = build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
        run_id="p4_4_family_tuning_policy_default"
    )
    summary = policy["summary"]

    assert policy["schema_version"] == PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_VERSION_20260610
    assert policy["source_step"] == PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610
    assert policy["policy_profile"] == PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_PROFILE_20260610
    assert summary["schema_version"] == PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610
    assert summary["family_policy_count"] == 7
    assert summary["boundary_slice_policy_count"] == 2
    assert summary["p4_0_connection_freeze_respected"] is True
    assert summary["p4_1_target_case_selection_used"] is True
    assert summary["p4_2_material_audit_used_for_context"] is True
    assert summary["p4_3_surface_requirement_boundary_respected"] is True
    assert summary["p4_4_family_tuning_policy_ready"] is True
    assert summary["p5_connection_allowed"] is False
    assert summary["p4_runtime_tuning_applied"] is False
    assert summary["rich_input_candidate_count_from_material_audit"] >= 10
    assert len(policy["family_case_policy_links"]) >= 19  # type: ignore[arg-type]
    assert len(policy["runtime_owner_references"]) == 4  # type: ignore[arg-type]
    assert policy["runtime_owner_reference_only"] is True
    assert policy["runtime_policy_connection_applied"] is False
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(policy)


def test_p4_4_main_family_policy_defines_ratio_temperature_roles_and_questions() -> None:
    policies = _policies_by_family(
        build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
            run_id="p4_4_main_family_policy"
        )
    )

    daily = policies[FAMILY_DAILY_UNPLEASANT]
    daily_ratio = daily["ratio_profile"]
    daily_section = daily["section_policy"]
    assert daily["schema_version"] == PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_ITEM_VERSION_20260610
    assert daily["temperature_profile"] == "warm_reception_with_light_observation"
    assert daily_ratio["observation_ratio_min"] == 0.20
    assert daily_ratio["observation_ratio_max"] == 0.30
    assert daily_ratio["reception_ratio_min"] == 0.70
    assert daily_ratio["reception_ratio_max"] == 0.80
    assert daily_section["section_role_sequence"] == ["observation", "reception"]
    assert daily_section["max_questions"] == 0
    assert daily_section["question_only_forbidden"] is True
    assert "event_anchor" in daily["required_anchor_roles"]
    assert "emotion_direction_anchor" in daily["required_anchor_roles"]
    assert "emlis_reception_anchor" in daily["required_anchor_roles"]
    assert "target_judgement_agreement" in daily["forbidden_surface_classes"]
    assert "p6_over_insight" in daily["forbidden_surface_classes"]

    structure = policies[FAMILY_STRUCTURE_QUESTION]
    structure_ratio = structure["ratio_profile"]
    structure_section = structure["section_policy"]
    assert structure["temperature_profile"] == "calm_observation_with_soft_reception"
    assert structure_ratio["observation_ratio_min"] == 0.60
    assert structure_ratio["observation_ratio_max"] == 0.70
    assert structure_ratio["reception_ratio_min"] == 0.30
    assert structure_ratio["reception_ratio_max"] == 0.40
    assert structure_section["max_questions"] == 1
    assert structure_section["question_only_forbidden"] is True
    assert structure_section["requires_visible_scope_marker"] is True
    assert "structure_question_anchor" in structure["required_anchor_roles"]
    assert "soft_inference_marker" in structure["required_anchor_roles"]
    assert "comfort_only" in structure["forbidden_surface_classes"]
    assert "cause_claim_without_evidence" in structure["forbidden_surface_classes"]

    self_denial = policies[FAMILY_SELF_DENIAL]
    self_denial_ratio = self_denial["ratio_profile"]
    assert self_denial["temperature_profile"] == "careful_support_without_identity_confirmation"
    assert self_denial_ratio["observation_ratio_min"] == 0.40
    assert self_denial_ratio["observation_ratio_max"] == 0.50
    assert "self_denial_phrase_as_state_not_fact" in self_denial["required_anchor_roles"]
    assert "no_identity_claim_marker" in self_denial["required_anchor_roles"]
    assert "identity_claim_as_fact" in self_denial["forbidden_surface_classes"]
    assert "emergency_bypass" in self_denial["forbidden_surface_classes"]


def test_p4_4_boundary_policy_keeps_low_info_limited_grounding_source_unavailable_and_history_separate() -> None:
    policy = build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
        run_id="p4_4_boundary_policy"
    )
    policies = _policies_by_family(policy)
    slice_policies = _slice_policies_by_slice(policy)

    low_info = policies[FAMILY_LOW_INFORMATION_SHORT]
    low_info_section = low_info["section_policy"]
    assert low_info["temperature_profile"] == "limited_scope_reception"
    assert low_info_section["question_only_forbidden"] is True
    assert low_info_section["question_position"] == "after_reception_optional"
    assert "visible_scope_marker" in low_info["required_anchor_roles"]
    assert "unknown_scope_marker" in low_info["required_anchor_roles"]
    assert "deep_read" in low_info["forbidden_surface_classes"]
    assert "history_supplementation" in low_info["forbidden_surface_classes"]

    limited = policies[FAMILY_LIMITED_GROUNDING]
    limited_section = limited["section_policy"]
    assert limited["surface_requirement_preference"] == "labelled_two_stage_or_limited_grounding_reception"
    assert limited_section["question_only_forbidden"] is True
    assert limited_section["requires_visible_scope_marker"] is True
    assert "limited_grounding_marker" in limited["required_anchor_roles"]
    assert "material_quality_forced_to_eligible" in limited["forbidden_surface_classes"]
    assert "unsupported_claim" in limited["forbidden_surface_classes"]

    source_unavailable = slice_policies[COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION]
    assert source_unavailable["boundary_policy"]["source_unavailable_boundary_kept"] is True
    assert source_unavailable["boundary_policy"]["normal_rebuild_forbidden"] is True
    assert "source_unavailable_marker" in source_unavailable["required_anchor_roles"]

    history = slice_policies[COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE]
    assert history["boundary_policy"]["p5_hold_until_current_only_readfeel_stable"] is True
    assert history["boundary_policy"]["history_line_must_not_mask_current_input_gap"] is True
    assert history["boundary_policy"]["owned_history_surface_strengthening_applied"] is False


def test_p4_4_regression_families_keep_temperature_without_fixed_surface_or_case_branch() -> None:
    policies = _policies_by_family(
        build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
            run_id="p4_4_regression_family_policy"
        )
    )

    for family in (
        FAMILY_DAILY_POSITIVE,
        FAMILY_RELATIONSHIP_BOUNDARY,
        FAMILY_LOW_INFORMATION_SHORT,
        FAMILY_LIMITED_GROUNDING,
    ):
        item = policies[family]
        assert item["observation_section_required"] is True
        assert item["reception_section_required"] is True
        assert item["fixed_sentence_template_added"] is False
        assert item["case_specific_runtime_branch"] is False
        assert item["runtime_branching_uses_fixture_strings"] is False
        assert item["public_response_key_change"] is False
        assert item["gate_relaxed"] is False
        assert item["p4_runtime_tuning_applied"] is False
        assert item["p5_visible_surface_strengthened"] is False

    positive = policies[FAMILY_DAILY_POSITIVE]
    assert positive["temperature_profile"] == "positive_warmth_without_overanalysis"
    assert "positive_change_anchor" in positive["required_anchor_roles"]
    assert "overanalysis" in positive["forbidden_surface_classes"]

    boundary = policies[FAMILY_RELATIONSHIP_BOUNDARY]
    assert boundary["temperature_profile"] == "boundary_observation_without_target_judgement"
    assert "no_target_judgement_marker" in boundary["required_anchor_roles"]
    assert "other_person_intent_claim" in boundary["forbidden_surface_classes"]


def test_p4_4_public_summary_and_dump_are_body_free() -> None:
    policy = build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
        run_id="p4_4_public_summary"
    )
    public_summary = build_product_readfeel_p4_family_tuning_policy_public_summary_20260610(policy)
    dumped = dump_product_readfeel_p4_family_tuning_policy_summary_from_p4_1_p4_2_20260610(
        run_id="p4_4_public_summary"
    )
    parsed = json.loads(dumped)

    assert public_summary["schema_version"] == PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610
    assert parsed["schema_version"] == PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610
    assert public_summary["family_policy_count"] == 7
    assert public_summary["boundary_slice_policy_count"] == 2
    assert public_summary["p4_4_family_tuning_policy_ready"] is True
    assert public_summary["p5_connection_allowed"] is False
    assert public_summary["p4_runtime_tuning_applied"] is False
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(public_summary)


def test_p4_4_assertion_rejects_body_keys_and_forbidden_runtime_flags() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
            {"schema_version": "x", "comment_text": "body must not be retained"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
            {"schema_version": "x", "fixed_sentence_template_added": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
            {"schema_version": "x", "case_specific_runtime_branch": True}
        )


def test_p4_4_get_family_policy_returns_body_free_policy_item() -> None:
    item = get_product_readfeel_p4_family_policy_20260610(FAMILY_DAILY_UNPLEASANT)
    assert item["family"] == FAMILY_DAILY_UNPLEASANT
    assert item["policy_id"] == "p4_4_daily_unpleasant_warm_reception_light_observation"
    assert item["fixed_sentence_template_added"] is False
    assert item["case_specific_runtime_branch"] is False
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(item)
