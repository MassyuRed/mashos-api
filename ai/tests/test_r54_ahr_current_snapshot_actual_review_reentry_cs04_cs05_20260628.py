# -*- coding: utf-8 -*-
"""R54-AHR-CS04/CS05 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "raw_body",
    "returned_emlis_body",
    "history_surface",
    "comment_text",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "raw_diff_body",
    "body_full_diff_content",
    "body_full_packet_content",
    "local_absolute_path",
    "local_file_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def test_cs00_to_cs03_are_present_before_cs04_cs05() -> None:
    cs00 = cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze()
    cs01 = cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=cs00)
    cs02 = cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile(current_snapshot_basis_refreeze=cs01)
    cs03 = cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment(
        historical_helper_refs_reconcile=cs02
    )

    assert cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(cs00) is True
    assert cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(cs01) is True
    assert cs.assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(cs02) is True
    assert cs.assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(cs03) is True
    assert tuple(cs03["implemented_steps"]) == cs.P7_R54_AHR_CS03_IMPLEMENTED_STEPS
    assert cs03["next_required_step"] == cs.P7_R54_AHR_CS04_STEP_REF
    assert cs03["current_manifest_refreeze_required"] is True
    assert cs03["old_manifest_allowed_as_current_manifest"] is False
    assert cs03["diff_impact_status_ref"] == cs.P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF


def test_cs04_refreezes_current_24_case_manifest_bodyfree() -> None:
    cs03 = cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment()
    material = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze(
        manifest_packet_evidence_impact_assessment=cs03
    )

    assert set(material) == set(cs.P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS04_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS04_STEP_REF
    assert material["cs03_schema_version"] == cs.P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION
    assert material["cs03_next_required_step"] == cs.P7_R54_AHR_CS04_STEP_REF
    assert material["cs03_current_manifest_refreeze_required"] is True
    assert material["cs03_old_manifest_allowed_as_current_manifest"] is False
    assert material["cs03_diff_impact_status_ref"] == cs.P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF

    assert material["actual_review_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["actual_review_basis_allowed"] == "current_received_snapshot_262_84_257_170_only"
    assert material["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["manifest_refreeze_status_ref"] == cs.P7_R54_AHR_CS04_MANIFEST_REFROZEN_STATUS_REF
    assert material["current_24_case_manifest_refrozen_here"] is True
    assert material["current_manifest_refreeze_uses_current_262_84_257_170_basis"] is True
    assert material["manifest_source_kind_ref"] == cs.P7_R54_AHR_CS04_MANIFEST_SOURCE_KIND_REF
    assert material["old_manifest_used_as_current_manifest"] is False
    assert material["historical_manifest_used_as_current_manifest"] is False

    assert material["required_case_count"] == 24
    assert material["manifest_row_count"] == 24
    assert material["manifest_row_count"] == 24
    assert len(material["case_manifest_rows"]) == 24
    assert material["case_ref_id_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["blind_case_id_case_ref_separated"] is True
    assert material["blind_case_id_packet_ref_separated"] is True
    assert material["case_ref_id_packet_ref_separated"] is True
    assert material["case_family_counts"] == cs.P7_R54_AHR_CS04_CASE_DISTRIBUTION
    assert material["case_distribution_matches_design"] is True

    assert material["review_axis_profile_ref"] == cs.P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF
    assert tuple(material["rating_axis_refs"]) == cs.P7_R54_AHR_CS04_RATING_AXIS_REFS
    assert material["rating_axis_count"] == 6
    assert material["required_rating_axis_count"] == 6
    assert material["rating_axis_target_thresholds"] == cs.P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS
    assert material["requires_history_line_review_count"] == 20
    assert material["current_only_boundary_case_count"] == 4
    assert material["all_case_rows_current_basis_ref"] is True
    assert material["case_manifest_rows_bodyfree_only"] is True

    for index, row in enumerate(material["case_manifest_rows"], start=1):
        assert row["case_index"] == index
        assert row["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
        assert row["review_axis_profile_ref"] == cs.P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF
        assert row["historical_manifest_allowed_as_structural_ref"] is True
        assert row["reviewer_facing_family_exposed"] is False
        assert row["reviewer_facing_tier_exposed"] is False
        assert row["body_full_packet_materialized_here"] is False
        assert row["local_reviewer_payload_materialized_here"] is False
        assert row["body_free"] is True
        assert "packet_content" not in row
        assert "question_text" not in row
        assert "raw_input" not in row
        assert "local_absolute_path" not in row

    assert material["reviewer_facing_family_exposed"] is False
    assert material["reviewer_facing_tier_exposed"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["local_reviewer_payload_materialized_here"] is False
    assert material["body_full_generation_blocked_until_local_only_preflight"] is True
    assert material["body_full_generation_blocked_until_local_only_preflight"] is True
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["actual_rating_or_question_rows_claim_blocked_here"] is True
    assert material["disposal_receipt_claim_blocked_here"] is True
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS05_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(material) is True


def test_cs05_local_only_preflight_ready_without_generating_or_exporting_packets() -> None:
    cs04 = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze()
    material = cs.build_p7_r54_ahr_cs05_local_only_preflight(current_24_case_manifest_refreeze=cs04)

    assert set(material) == set(cs.P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS05_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS05_STEP_REF
    assert material["cs04_schema_version"] == cs.P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
    assert material["cs04_next_required_step"] == cs.P7_R54_AHR_CS05_STEP_REF
    assert material["cs04_current_24_case_manifest_frozen"] is True
    assert material["cs04_manifest_row_count"] == 24
    assert material["cs04_case_ref_ids_unique"] is True
    assert material["cs04_blind_case_ids_unique"] is True
    assert material["cs04_packet_ref_ids_unique"] is True
    assert material["cs04_body_full_packet_materialized_here"] is False
    assert material["cs04_local_reviewer_payload_materialized_here"] is False

    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["current_24_case_manifest_frozen"] is True
    assert material["review_session_id_present_ref"] == cs.P7_R54_AHR_CS05_REVIEW_SESSION_PRESENT_REF
    assert material["review_session_id_present"] is True
    assert material["explicit_local_only_allow_ref"] == cs.P7_R54_AHR_CS05_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    assert material["explicit_local_only_allow_present"] is True
    assert material["local_review_root_available_ref"] == cs.P7_R54_AHR_CS05_LOCAL_REVIEW_ROOT_AVAILABLE_REF
    assert material["local_review_root_available_ref_present"] is True
    assert material["export_denylist_ready_ref"] == cs.P7_R54_AHR_CS05_EXPORT_DENYLIST_READY_REF
    assert material["export_denylist_ready"] is True
    assert material["purge_plan_ready_ref"] == cs.P7_R54_AHR_CS05_PURGE_PLAN_READY_REF
    assert material["purge_plan_ready"] is True
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["disposal_required"] is True
    assert tuple(material["export_denylist_refs"]) == cs.P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS
    assert material["export_denylist_ref_count"] == len(cs.P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS)
    assert tuple(material["forbidden_output_refs"]) == cs.P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS
    assert material["forbidden_output_ref_count"] == len(cs.P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS)
    assert material["local_only_preflight_status_ref"] == cs.P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF
    assert material["local_only_preflight_reason_refs"] == [cs.P7_R54_AHR_CS05_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []

    assert material["body_full_packet_generation_allowed_before_preflight"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is True
    assert material["body_full_generation_blocked_until_preflight_ready"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is True
    assert material["actual_review_execution_blocked_until_packet_generation_receipt"] is True
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["actual_rating_or_question_rows_claim_blocked_here"] is True
    assert material["disposal_receipt_claim_blocked_here"] is True
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS06_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs05_local_only_preflight_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("current_24_case_manifest_refrozen_here", False),
        ("current_manifest_refreeze_uses_current_262_84_257_170_basis", False),
        ("old_manifest_used_as_current_manifest", True),
        ("historical_manifest_used_as_current_manifest", True),
        ("required_case_count", 23),
        ("manifest_row_count", 23),
        ("manifest_row_count", 23),
        ("case_ref_ids_unique", False),
        ("blind_case_ids_unique", False),
        ("packet_ref_ids_unique", False),
        ("blind_case_id_case_ref_separated", False),
        ("case_distribution_matches_design", False),
        ("all_case_rows_current_basis_ref", False),
        ("case_manifest_rows_bodyfree_only", False),
        ("rating_axis_count", 5),
        ("required_rating_axis_count", 5),
        ("requires_history_line_review_count", 19),
        ("current_only_boundary_case_count", 5),
        ("reviewer_facing_family_exposed", True),
        ("reviewer_facing_tier_exposed", True),
        ("body_full_packet_materialized_here", True),
        ("local_reviewer_payload_materialized_here", True),
        ("body_full_generation_blocked_until_local_only_preflight", False),
        ("body_full_generation_blocked_until_local_only_preflight", False),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cs04_rejects_manifest_refreeze_or_promotion_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("current_24_case_manifest_frozen", False),
        ("review_session_id_present", False),
        ("explicit_local_only_allow_present", False),
        ("local_review_root_available_ref_present", False),
        ("export_denylist_ready", False),
        ("purge_plan_ready", False),
        ("local_only", False),
        ("must_not_export", False),
        ("disposal_required", False),
        ("local_only_preflight_status_ref", cs.P7_R54_AHR_CS05_PREFLIGHT_BLOCKED_STATUS_REF),
        ("local_only_preflight_reason_refs", []),
        ("execution_blocker_ids", ["blocked"]),
        ("open_execution_blocker_ids", ["blocked"]),
        ("body_full_packet_generation_allowed_before_preflight", True),
        ("body_full_packet_generation_allowed_by_preflight", False),
        ("body_full_generation_blocked_until_preflight_ready", False),
        ("body_full_packet_generation_request_allowed_next", False),
        ("actual_review_execution_blocked_until_packet_generation_receipt", False),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cs05_rejects_local_only_preflight_or_promotion_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs05_local_only_preflight())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs05_local_only_preflight_contract(mutated)


def test_cs04_cs05_reject_body_question_path_or_hash_payload_keys() -> None:
    cs04 = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze()
    mutated04 = deepcopy(cs04)
    mutated04["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(mutated04)

    mutated04_row = deepcopy(cs04)
    mutated04_row["case_manifest_rows"][0]["packet_content"] = "forbidden"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(mutated04_row)

    cs05 = cs.build_p7_r54_ahr_cs05_local_only_preflight()
    mutated05 = deepcopy(cs05)
    mutated05["local_absolute_path"] = "/forbidden/path"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs05_local_only_preflight_contract(mutated05)


def test_cs04_cs05_aliases_preserve_contract() -> None:
    cs04 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_current_24_case_manifest_refreeze_bodyfree()
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_current_24_case_manifest_refreeze_bodyfree_contract(
            cs04
        )
        is True
    )

    cs05 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_local_only_preflight_bodyfree(
        current_24_case_manifest_refreeze=cs04
    )
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_local_only_preflight_bodyfree_contract(cs05)
        is True
    )
