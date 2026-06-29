# -*- coding: utf-8 -*-
"""R54-AHR-CR04/CR05 current received actual local review operation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in cr.P7_R54_AHR_CR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in (
        "raw_input",
        "raw_body",
        "current_input_body",
        "returned_emlis_body",
        "history_surface",
        "comment_text",
        "reviewer_free_text",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "packet_content",
        "body_full_packet_content",
        "local_path",
        "local_absolute_path",
        "body_hash",
        "terminal_output_body",
    ):
        assert forbidden_key not in material


def _default_cr04() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()


def _default_cr05_blocked() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr05_local_only_preflight(current_24_case_manifest_refreeze=_default_cr04())


def _default_cr05_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr05_local_only_preflight(
        current_24_case_manifest_refreeze=_default_cr04(),
        explicit_allow_ref=cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
    )


def test_cr04_refreezes_current_24_case_manifest_bodyfree_on_current_received_basis() -> None:
    cr03 = cr.build_p7_r54_ahr_cr03_basis_impact_assessment()
    material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(basis_impact_assessment=cr03)

    assert set(material) == set(cr.P7_R54_AHR_CR04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR04_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR04_STEP_REF
    assert material["cr03_schema_version"] == cr.P7_R54_AHR_CR_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION
    assert material["cr03_next_required_step"] == cr.P7_R54_AHR_CR04_STEP_REF
    assert material["cr03_current_manifest_refreeze_required"] is True
    assert material["cr03_current_24_case_manifest_must_be_refrozen_next"] is True
    assert material["cr03_old_manifest_allowed_as_current_manifest"] is False
    assert material["cr03_old_evidence_rows_allowed_as_current_actual_review_rows"] is False

    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["actual_review_basis_allowed_ref"] == "current_received_snapshot_264_85_258_171_only"
    assert material["outer_received_zip_refs_used_as_actual_review_basis"] is True
    assert material["current_received_snapshot_refs_used_as_actual_review_basis"] is True
    assert material["historical_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["historical_cs_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["historical_basis_refs_used_as_current_actual_review_basis"] is False
    assert material["historical_basis_refs_used_as_current_actual_review_evidence"] is False

    assert material["manifest_refreeze_status_ref"] == cr.P7_R54_AHR_CR04_MANIFEST_REFREEZE_STATUS_REF
    assert material["manifest_source_kind_ref"] == cr.P7_R54_AHR_CR04_MANIFEST_SOURCE_KIND_REF
    assert material["manifest_source_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["current_manifest_refrozen_here"] is True
    assert material["required_case_count"] == 24
    assert material["case_distribution"] == cr.P7_R54_AHR_CR04_CASE_DISTRIBUTION
    assert material["case_distribution_total_count"] == 24
    assert material["case_distribution_matches_design"] is True
    assert material["case_row_count"] == 24
    assert len(material["case_rows"]) == 24
    assert material["case_rows_bodyfree_only"] is True

    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_id_count"] == 24
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["blind_case_id_case_ref_separated"] is True
    assert material["blind_case_id_packet_ref_separated"] is True
    assert material["case_ref_id_packet_ref_separated"] is True

    assert material["family_ref_counts"] == cr.P7_R54_AHR_CR04_CASE_DISTRIBUTION
    assert material["case_role_counts"] == {
        "positive_history_line": 4,
        "positive_owned_history": 16,
        "boundary_no_history_line": 4,
    }
    assert material["subscription_tier_ref_counts"] == {
        "paid_owned_history_context_ref": 20,
        "tier_hidden_current_only_boundary": 2,
        "free_tier_history_present_not_allowed_boundary": 2,
    }
    assert material["history_evidence_policy_ref_counts"] == {
        "bounded_owned_history_local_only": 20,
        "history_not_eligible_current_only_boundary": 2,
        "owned_history_present_but_not_allowed_by_tier_boundary": 2,
    }
    assert material["review_axis_profile_ref"] == cr.P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF
    assert tuple(material["rating_axis_refs"]) == cr.P7_R54_AHR_CR04_RATING_AXIS_REFS
    assert material["rating_axis_count"] == 6
    assert material["rating_axis_target_thresholds"] == cr.P7_R54_AHR_CR04_RATING_AXIS_TARGET_THRESHOLDS
    assert material["requires_history_line_review_count"] == 4
    assert material["current_only_boundary_case_count"] == 4

    first = material["case_rows"][0]
    assert set(first) == set(cr.P7_R54_AHR_CR04_CASE_ROW_REQUIRED_FIELD_REFS)
    assert first == {
        "case_index": 1,
        "case_ref_id": "cral_case_ref_001",
        "blind_case_id": "cral_blind_case_001",
        "packet_ref_id": "cral_packet_ref_001",
        "family_ref": "history_line_eligible_input",
        "case_role_ref": "positive_history_line",
        "subscription_tier_ref": "paid_owned_history_context_ref",
        "history_evidence_policy_ref": "bounded_owned_history_local_only",
        "review_axis_profile_ref": cr.P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "requires_history_line_review": True,
        "current_only_boundary_case": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_free": True,
    }
    last = material["case_rows"][-1]
    assert last["case_index"] == 24
    assert last["case_ref_id"] == "cral_case_ref_024"
    assert last["family_ref"] == "free_tier_history_present_not_allowed"
    assert last["case_role_ref"] == "boundary_no_history_line"
    assert last["current_only_boundary_case"] is True

    assert material["body_full_packet_materialized_here"] is False
    assert material["local_reviewer_payload_materialized_here"] is False
    assert material["old_manifest_adopted_unconditionally"] is False
    assert material["old_packet_boundary_adopted_unconditionally"] is False
    assert material["old_evidence_rows_current_adopted"] is False
    assert material["cr04_does_not_generate_body_full_packet"] is True
    assert material["cr04_does_not_create_local_reviewer_payload"] is True
    assert material["cr04_does_not_execute_actual_human_review"] is True
    assert material["cr04_does_not_create_actual_rating_or_question_rows"] is True
    assert material["cr04_does_not_create_disposal_receipt"] is True
    assert material["body_full_generation_blocked_until_preflight"] is True
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR05_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(material) is True


def test_cr04_still_requires_current_manifest_refreeze_after_bodyfree_executed_diff() -> None:
    cr03 = cr.build_p7_r54_ahr_cr03_basis_impact_assessment(
        direct_diff_available=True,
        direct_diff_executed=True,
    )
    material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(basis_impact_assessment=cr03)

    assert material["cr03_current_manifest_refreeze_required"] is True
    assert material["current_manifest_refrozen_here"] is True
    assert material["case_row_count"] == 24
    assert material["old_manifest_adopted_unconditionally"] is False
    assert cr.assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("cr03_next_required_step", "not_cr04"),
        ("cr03_current_manifest_refreeze_required", False),
        ("cr03_current_24_case_manifest_must_be_refrozen_next", False),
        ("cr03_old_manifest_allowed_as_current_manifest", True),
        ("cr03_old_evidence_rows_allowed_as_current_actual_review_rows", True),
        ("manifest_source_basis_ref", "current_received_snapshot_262_84_257_170"),
        ("current_manifest_refrozen_here", False),
        ("case_row_count", 23),
        ("case_rows_bodyfree_only", False),
        ("case_ref_ids_unique", False),
        ("blind_case_ids_unique", False),
        ("packet_ref_ids_unique", False),
        ("blind_case_id_case_ref_separated", False),
        ("blind_case_id_packet_ref_separated", False),
        ("case_ref_id_packet_ref_separated", False),
        ("reviewer_facing_family_exposed", True),
        ("reviewer_facing_tier_exposed", True),
        ("body_full_packet_materialized_here", True),
        ("local_reviewer_payload_materialized_here", True),
        ("old_manifest_adopted_unconditionally", True),
        ("old_packet_boundary_adopted_unconditionally", True),
        ("old_evidence_rows_current_adopted", True),
        ("cr04_does_not_generate_body_full_packet", False),
        ("cr04_does_not_execute_actual_human_review", False),
        ("cr04_does_not_create_actual_rating_or_question_rows", False),
        ("cr04_does_not_create_disposal_receipt", False),
        ("actual_human_review_run_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cr04_rejects_manifest_refreeze_claim_mutations(key: str, value: object) -> None:
    mutated = deepcopy(_default_cr04())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(mutated)


def test_cr04_rejects_non_24_case_manifest() -> None:
    rows = deepcopy(_default_cr04()["case_rows"])
    rows.pop()
    material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(case_rows=rows)
    assert material["case_row_count"] == 23
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(material)


def test_cr04_rejects_duplicate_case_blind_or_packet_refs() -> None:
    rows = deepcopy(_default_cr04()["case_rows"])
    rows[1]["case_ref_id"] = rows[0]["case_ref_id"]
    material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(case_rows=rows)
    assert material["case_ref_ids_unique"] is False
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(material)


def test_cr04_rejects_forbidden_body_or_question_keys_inside_case_rows() -> None:
    rows = deepcopy(_default_cr04()["case_rows"])
    rows[0]["comment_text"] = "must not be exported"
    material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(case_rows=rows)
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(material)


def test_cr04_rejects_reviewer_facing_family_or_tier_exposure_inside_rows() -> None:
    rows = deepcopy(_default_cr04()["case_rows"])
    rows[0]["reviewer_facing_family_exposed"] = True
    material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(case_rows=rows)
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr04_current_24_case_manifest_refreeze_contract(material)


def test_cr05_blocks_by_default_without_explicit_allow_while_preserving_bodyfree_no_touch() -> None:
    cr04 = _default_cr04()
    material = cr.build_p7_r54_ahr_cr05_local_only_preflight(current_24_case_manifest_refreeze=cr04)

    assert set(material) == set(cr.P7_R54_AHR_CR05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR05_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR05_STEP_REF
    assert material["cr04_schema_version"] == cr.P7_R54_AHR_CR_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
    assert material["cr04_next_required_step"] == cr.P7_R54_AHR_CR05_STEP_REF
    assert material["cr04_current_manifest_refrozen_here"] is True
    assert material["cr04_case_row_count"] == 24
    assert material["cr04_case_rows_bodyfree_only"] is True
    assert material["cr04_body_full_packet_materialized_here"] is False
    assert material["cr04_actual_human_review_run_here"] is False

    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["historical_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["historical_cs_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["preflight_status_ref"] == cr.P7_R54_AHR_CR05_PREFLIGHT_BLOCKED_STATUS_REF
    assert tuple(material["preflight_allowed_status_refs"]) == cr.P7_R54_AHR_CR05_ALLOWED_PREFLIGHT_STATUS_REFS
    assert material["preflight_ready"] is False
    assert material["preflight_reason_refs"] == []
    assert material["preflight_blocker_refs"] == [cr.P7_R54_AHR_CR05_EXPLICIT_ALLOW_MISSING_BLOCKER_REF]
    assert material["preflight_blocker_ref_count"] == 1
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["local_review_root_ref"] == cr.P7_R54_AHR_CR05_DEFAULT_LOCAL_REVIEW_ROOT_REF
    assert material["local_review_root_ref_present"] is True
    assert material["explicit_allow_ref"] == ""
    assert material["explicit_allow_ref_present"] is False
    assert material["explicit_allow_ref_expected"] == cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF
    assert material["retention_policy_ref"] == cr.P7_R54_AHR_CR05_DEFAULT_RETENTION_POLICY_REF
    assert material["retention_policy_ref_present"] is True
    assert material["disposal_policy_ref"] == cr.P7_R54_AHR_CR05_DEFAULT_DISPOSAL_POLICY_REF
    assert material["disposal_policy_ref_present"] is True
    assert material["export_denylist_policy_ref"] == cr.P7_R54_AHR_CR05_DEFAULT_EXPORT_DENYLIST_POLICY_REF
    assert material["export_denylist_policy_ref_present"] is True
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_free_summary_export_allowed"] is True
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["actual_review_operation_allowed_by_preflight"] is False
    assert material["body_full_packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["body_full_packet_content_exported"] is False
    assert material["body_full_packet_never_export_to_repo_docs_release_public_meta"] is True
    assert material["preflight_ready_all_policy_refs_present"] is False
    assert material["preflight_blocks_without_explicit_allow"] is True
    assert material["preflight_blocks_body_full_export"] is True
    assert material["preflight_does_not_generate_packet_or_review_rows"] is True
    assert material["preflight_does_not_execute_actual_human_review"] is True
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr05_local_only_preflight_contract(material) is True


def test_cr05_ready_with_explicit_allow_only_allows_later_request_consideration_not_execution() -> None:
    material = _default_cr05_ready()

    assert material["preflight_status_ref"] == cr.P7_R54_AHR_CR05_PREFLIGHT_READY_STATUS_REF
    assert material["preflight_ready"] is True
    assert material["preflight_reason_refs"] == [cr.P7_R54_AHR_CR05_READY_REASON_REF]
    assert material["preflight_blocker_refs"] == []
    assert material["preflight_blocker_ref_count"] == 0
    assert material["explicit_allow_ref"] == cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF
    assert material["explicit_allow_ref_present"] is True
    assert material["body_full_packet_generation_allowed_by_preflight"] is True
    assert material["actual_review_operation_allowed_by_preflight"] is True
    assert material["body_full_packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["preflight_ready_all_policy_refs_present"] is True
    assert material["preflight_blocks_without_explicit_allow"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR06_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr05_local_only_preflight_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"local_only": False}, cr.P7_R54_AHR_CR05_LOCAL_ONLY_FALSE_BLOCKER_REF),
        ({"must_not_export": False}, cr.P7_R54_AHR_CR05_MUST_NOT_EXPORT_FALSE_BLOCKER_REF),
        ({"local_review_root_ref": ""}, cr.P7_R54_AHR_CR05_LOCAL_REVIEW_ROOT_MISSING_BLOCKER_REF),
        ({"explicit_allow_ref": ""}, cr.P7_R54_AHR_CR05_EXPLICIT_ALLOW_MISSING_BLOCKER_REF),
        ({"retention_policy_ref": ""}, cr.P7_R54_AHR_CR05_RETENTION_POLICY_MISSING_BLOCKER_REF),
        ({"disposal_policy_ref": ""}, cr.P7_R54_AHR_CR05_DISPOSAL_POLICY_MISSING_BLOCKER_REF),
        ({"export_denylist_policy_ref": ""}, cr.P7_R54_AHR_CR05_EXPORT_DENYLIST_POLICY_MISSING_BLOCKER_REF),
        ({"body_full_packet_export_allowed": True}, cr.P7_R54_AHR_CR05_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF),
    ],
)
def test_cr05_blocks_when_any_local_only_policy_piece_is_missing_or_unsafe(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    params: dict[str, object] = {"explicit_allow_ref": cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF}
    params.update(kwargs)
    material = cr.build_p7_r54_ahr_cr05_local_only_preflight(
        current_24_case_manifest_refreeze=_default_cr04(),
        **params,
    )

    assert material["preflight_status_ref"] == cr.P7_R54_AHR_CR05_PREFLIGHT_BLOCKED_STATUS_REF
    assert material["preflight_ready"] is False
    assert expected_blocker in material["preflight_blocker_refs"]
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["actual_review_operation_allowed_by_preflight"] is False
    assert material["body_full_packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr05_local_only_preflight_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("cr04_next_required_step", "not_cr05"),
        ("cr04_current_manifest_refrozen_here", False),
        ("cr04_case_row_count", 23),
        ("cr04_case_rows_bodyfree_only", False),
        ("cr04_body_full_packet_materialized_here", True),
        ("cr04_actual_human_review_run_here", True),
        ("preflight_allowed_status_refs", ["changed"]),
        ("preflight_ready", True),
        ("preflight_blocker_ref_count", 99),
        ("local_only", False),
        ("must_not_export", False),
        ("local_review_root_ref_present", False),
        ("explicit_allow_ref_present", True),
        ("retention_policy_ref_present", False),
        ("disposal_policy_ref_present", False),
        ("export_denylist_policy_ref_present", False),
        ("body_full_packet_export_allowed", True),
        ("body_free_summary_export_allowed", False),
        ("body_full_packet_generation_allowed_by_preflight", True),
        ("actual_review_operation_allowed_by_preflight", True),
        ("body_full_packet_generation_started_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_content_included", True),
        ("body_full_packet_content_exported", True),
        ("body_full_packet_never_export_to_repo_docs_release_public_meta", False),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("terminal_output_body_included", True),
        ("preflight_does_not_generate_packet_or_review_rows", False),
        ("preflight_does_not_execute_actual_human_review", False),
        ("actual_human_review_run_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cr05_rejects_preflight_mutations_or_execution_promotion(key: str, value: object) -> None:
    mutated = deepcopy(_default_cr05_blocked())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr05_local_only_preflight_contract(mutated)


def test_cr04_cr05_alias_functions_match_primary_builders_and_contracts() -> None:
    cr04 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_current_24_case_manifest_refreeze_bodyfree()
    cr05 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_local_only_preflight_bodyfree(
        current_24_case_manifest_refreeze=cr04,
        explicit_allow_ref=cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
    )

    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_current_24_case_manifest_refreeze_bodyfree_contract(cr04) is True
    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_local_only_preflight_bodyfree_contract(cr05) is True
    assert cr04["operation_step_ref"] == cr.P7_R54_AHR_CR04_STEP_REF
    assert cr05["operation_step_ref"] == cr.P7_R54_AHR_CR05_STEP_REF
    assert cr05["preflight_ready"] is True
