# -*- coding: utf-8 -*-
"""R54-AHR-CS10/CS11 current snapshot actual review re-entry contract tests."""

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
    "comment_text_body",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_notes_body",
    "question_text",
    "draft_question_text",
    "raw_question_answer",
    "body_full_packet_content",
    "packet_content",
    "local_absolute_path",
    "local_file_path",
    "body_hash",
    "terminal_output_body",
    "stdout_body",
    "stderr_body",
    "traceback_body",
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


def _assert_bodyfree_no_touch_allowing(material: dict[str, Any], allowed_true_flags: tuple[str, ...]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if key in allowed_true_flags:
            continue
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _build_ready_cs09() -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake(
        operation_receipt_ref=cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
        reviewer_person_ref=cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_operation_run=True,
        actual_human_review_executed_by_person=True,
        review_started_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT,
        review_completed_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT,
        reviewed_case_count=cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        selection_row_count=cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    )
    assert cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(material) is True
    return material


def _base_review_result_rows(*, mixed: bool = False) -> list[dict[str, Any]]:
    manifest = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze()
    assert cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(manifest) is True
    rows: list[dict[str, Any]] = []
    for index, manifest_row in enumerate(manifest["case_manifest_rows"], start=1):
        axis_scores = {axis_ref: 1.0 for axis_ref in cs.P7_R54_AHR_CS04_RATING_AXIS_REFS}
        verdict = "PASS"
        sanitized_reason_ids = [cs.P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS[0]]
        readfeel_blocker_ids: list[str] = []
        execution_blocker_ids: list[str] = []
        question_need_primary_class = cs.P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS[0]
        ambiguity_kind_refs = [cs.P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS[0]]
        one_question_fit_ref = cs.P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS[0]
        repair_required_refs = [cs.P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS[0]]
        plan_candidate_flags = {flag_ref: False for flag_ref in cs.P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS}

        if mixed and index == 1:
            axis_scores["creepy_absence"] = 0.75
            verdict = "YELLOW"
            sanitized_reason_ids = [cs.P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS[2]]
            readfeel_blocker_ids = [cs.P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS[1]]
            question_need_primary_class = "question_may_reduce_overread_risk"
            ambiguity_kind_refs = ["history_connection_basis_unclear"]
            one_question_fit_ref = "fits_one_question"
        elif mixed and index == 2:
            axis_scores["history_connection_naturalness"] = 0.5
            verdict = "REPAIR_REQUIRED"
            sanitized_reason_ids = [cs.P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS[1]]
            readfeel_blocker_ids = [cs.P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS[0]]
            repair_required_refs = ["emlis_readfeel_repair_required"]
            question_need_primary_class = "not_question_emlis_readfeel_repair_required"
            one_question_fit_ref = "repair_required_not_question"
        elif mixed and index == 3:
            axis_scores["overclaim_absence"] = 0.25
            verdict = "BLOCKED"
            sanitized_reason_ids = [cs.P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS[-1]]
            execution_blocker_ids = [cs.P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS[0]]
            question_need_primary_class = "insufficient_material_execution_blocker"
            one_question_fit_ref = "insufficient_material"

        rows.append(
            {
                "review_result_row_ref": f"review_result_row_{index:03d}",
                "review_session_id": cs.P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
                "case_ref_id": manifest_row["case_ref_id"],
                "blind_case_id": manifest_row["blind_case_id"],
                "packet_ref_id": manifest_row["packet_ref_id"],
                "case_family_ref": manifest_row["case_family_ref"],
                "case_role_ref": manifest_row["case_role_ref"],
                "subscription_tier_ref": manifest_row["subscription_tier_ref"],
                "history_evidence_policy_ref": manifest_row["history_evidence_policy_ref"],
                "current_basis_ref": cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                "reviewer_person_ref": cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
                "reviewed_at_bucket_ref": f"reviewed_at_bucket_ref_{index:03d}",
                "axis_scores": axis_scores,
                "axis_score_count": len(cs.P7_R54_AHR_CS04_RATING_AXIS_REFS),
                "verdict": verdict,
                "sanitized_reason_ids": sanitized_reason_ids,
                "readfeel_blocker_ids": readfeel_blocker_ids,
                "execution_blocker_ids": execution_blocker_ids,
                "question_need_primary_class": question_need_primary_class,
                "ambiguity_kind_refs": ambiguity_kind_refs,
                "one_question_fit_ref": one_question_fit_ref,
                "repair_required_refs": repair_required_refs,
                "plan_candidate_flags": plan_candidate_flags,
                "selection_only_row": True,
                **{flag_ref: False for flag_ref in cs.P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS},
                "body_free": True,
            }
        )
    return rows


def _build_ready_cs10(*, mixed: bool = False) -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs10_sanitized_review_result_row_intake(
        actual_human_review_operation_receipt_intake=_build_ready_cs09(),
        review_result_rows=_base_review_result_rows(mixed=mixed),
    )
    assert cs.assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract(material) is True
    return material


def _build_ready_cs11(*, mixed: bool = False) -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs11_rating_row_normalization(
        sanitized_review_result_row_intake=_build_ready_cs10(mixed=mixed)
    )
    assert cs.assert_p7_r54_ahr_cs11_rating_row_normalization_contract(material) is True
    return material


def test_cs00_to_cs09_are_present_before_cs10_cs11() -> None:
    cs00 = cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze()
    cs01 = cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=cs00)
    cs02 = cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile(current_snapshot_basis_refreeze=cs01)
    cs03 = cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment(
        historical_helper_refs_reconcile=cs02
    )
    cs04 = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze(
        manifest_packet_evidence_impact_assessment=cs03
    )
    cs05 = cs.build_p7_r54_ahr_cs05_local_only_preflight(current_24_case_manifest_refreeze=cs04)
    cs06 = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge(local_only_preflight=cs05)
    cs07 = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(
        packet_generation_request_receipt_bridge=cs06
    )
    cs08 = cs.build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility(
        packet_completeness_export_denylist_scan=cs07
    )
    cs09 = cs.build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake(
        reviewer_selection_form_current_compatibility=cs08,
        operation_receipt_ref=cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
        reviewer_person_ref=cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_operation_run=True,
        actual_human_review_executed_by_person=True,
        review_started_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT,
        review_completed_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT,
        reviewed_case_count=cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        selection_row_count=cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    )

    assert cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(cs00) is True
    assert cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(cs01) is True
    assert cs.assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(cs02) is True
    assert cs.assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(cs03) is True
    assert cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(cs04) is True
    assert cs.assert_p7_r54_ahr_cs05_local_only_preflight_contract(cs05) is True
    assert cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(cs06) is True
    assert cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(cs07) is True
    assert cs.assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(cs08) is True
    assert cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(cs09) is True
    assert tuple(cs09["implemented_steps"]) == cs.P7_R54_AHR_CS09_IMPLEMENTED_STEPS
    assert cs09["next_required_step"] == cs.P7_R54_AHR_CS10_STEP_REF
    assert cs09["sanitized_review_result_row_intake_allowed_next"] is True


def test_cs10_default_is_fail_closed_without_cs09_receipt_or_rows() -> None:
    material = cs.build_p7_r54_ahr_cs10_sanitized_review_result_row_intake()

    assert material["sanitized_review_result_row_intake_status_ref"] == cs.P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF
    assert material["sanitized_review_result_row_count"] == 0
    assert material["review_result_rows"] == []
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["actual_sanitized_review_result_rows_intaken_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS10_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract(material) is True


def test_cs10_sanitized_review_result_row_intake_ready_bodyfree() -> None:
    material = _build_ready_cs10()

    assert set(material) == set(cs.P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS10_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS10_STEP_REF
    assert material["cs09_next_required_step"] == cs.P7_R54_AHR_CS10_STEP_REF
    assert material["cs09_operation_status_ref"] == cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    assert material["cs09_actual_human_review_operation_run"] is True
    assert material["cs09_actual_human_review_executed_by_person"] is True
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["actual_review_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["existing_ahr_can_be_used_as_current_actual_review_evidence"] is False
    assert material["sanitized_review_result_row_intake_status_ref"] == cs.P7_R54_AHR_CS10_INTAKE_READY_STATUS_REF
    assert material["sanitized_review_result_row_intake_reason_refs"] == [cs.P7_R54_AHR_CS10_READY_REASON_REF]
    assert material["required_case_count"] == 24
    assert material["received_review_result_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["rows_match_current_24_case_manifest"] is True
    assert material["case_ref_ids_match_manifest"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_selection_only"] is True
    assert material["rows_have_required_axis_scores"] is True
    assert material["all_scores_in_allowed_options"] is True
    assert material["all_verdicts_in_allowed_options"] is True
    assert material["all_reason_ids_in_allowed_options"] is True
    assert material["rows_have_allowed_question_observation_refs"] is True
    assert material["rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["rating_row_normalization_allowed_next"] is True
    assert material["rating_rows_materialized_here"] is False
    assert material["question_need_observation_rows_materialized_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS10_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS11_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS10_ALLOWED_TRUE_FALSE_FLAG_REFS)


@pytest.mark.parametrize("row_key", cs.P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS)
def test_cs10_rows_keep_bodyfree_false_flags(row_key: str) -> None:
    material = _build_ready_cs10()
    for row in material["review_result_rows"]:
        assert row[row_key] is False
        assert row["body_free"] is True
        assert row["selection_only_row"] is True
        assert row["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF


def test_cs10_rejects_question_text_flag_in_review_result_row() -> None:
    rows = _base_review_result_rows()
    rows[0]["question_text_included"] = True
    material = cs.build_p7_r54_ahr_cs10_sanitized_review_result_row_intake(
        actual_human_review_operation_receipt_intake=_build_ready_cs09(),
        review_result_rows=rows,
    )

    assert material["sanitized_review_result_row_intake_status_ref"] == cs.P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF
    assert material["sanitized_review_result_row_count"] == 0
    assert any("question_text_included_not_false" in blocker for blocker in material["execution_blocker_ids"])
    assert material["rating_row_normalization_allowed_next"] is False
    assert cs.assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract(material) is True


@pytest.mark.parametrize(
    ("mutate_key", "mutate_value", "expected_blocker_fragment"),
    (
        ("case_ref_id", "wrong_case_ref", "case_ref_not_in_current_manifest"),
        ("verdict", "NOT_ALLOWED", "verdict_not_allowed"),
        ("selection_only_row", False, "selection_only_row_not_true"),
    ),
)
def test_cs10_rejects_invalid_review_result_row_contract(
    mutate_key: str, mutate_value: Any, expected_blocker_fragment: str
) -> None:
    rows = _base_review_result_rows()
    rows[0][mutate_key] = mutate_value
    material = cs.build_p7_r54_ahr_cs10_sanitized_review_result_row_intake(
        actual_human_review_operation_receipt_intake=_build_ready_cs09(),
        review_result_rows=rows,
    )

    assert material["sanitized_review_result_row_intake_status_ref"] == cs.P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF
    assert any(expected_blocker_fragment in blocker for blocker in material["execution_blocker_ids"])
    assert material["review_result_rows"] == []
    assert material["next_required_step"] == cs.P7_R54_AHR_CS10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cs.assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract(material) is True


def test_cs10_rejects_invalid_score_option() -> None:
    rows = _base_review_result_rows()
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.33
    material = cs.build_p7_r54_ahr_cs10_sanitized_review_result_row_intake(
        actual_human_review_operation_receipt_intake=_build_ready_cs09(),
        review_result_rows=rows,
    )

    assert material["sanitized_review_result_row_intake_status_ref"] == cs.P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF
    assert any("score_not_allowed_option" in blocker for blocker in material["execution_blocker_ids"])
    assert material["all_scores_in_allowed_options"] is False
    assert cs.assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract(material) is True


def test_cs10_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs10()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_sanitized_review_result_row_intake_bodyfree(
        actual_human_review_operation_receipt_intake=_build_ready_cs09(),
        review_result_rows=_base_review_result_rows(),
    )

    assert alias == primary
    assert cs.assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_bodyfree_contract(alias) is True
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_sanitized_review_result_row_intake_bodyfree_contract(
            alias
        )
        is True
    )


def test_cs11_default_is_fail_closed_without_ready_cs10() -> None:
    material = cs.build_p7_r54_ahr_cs11_rating_row_normalization()

    assert material["rating_row_normalization_status_ref"] == cs.P7_R54_AHR_CS11_BLOCKED_STATUS_REF
    assert material["rating_row_count"] == 0
    assert material["rating_rows"] == []
    assert material["blocker_question_need_observation_normalization_allowed_next"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS11_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs11_rating_row_normalization_contract(material) is True


def test_cs11_rating_row_normalization_ready_bodyfree() -> None:
    material = _build_ready_cs11()

    assert set(material) == set(cs.P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS11_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS11_STEP_REF
    assert material["cs10_next_required_step"] == cs.P7_R54_AHR_CS11_STEP_REF
    assert material["cs10_sanitized_review_result_row_intake_status_ref"] == cs.P7_R54_AHR_CS10_INTAKE_READY_STATUS_REF
    assert material["cs10_rating_row_normalization_allowed_next"] is True
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["rating_row_normalization_status_ref"] == cs.P7_R54_AHR_CS11_NORMALIZED_STATUS_REF
    assert material["rating_row_normalization_reason_refs"] == [cs.P7_R54_AHR_CS11_READY_REASON_REF]
    assert material["source_sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["rating_row_ref_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["axis_count"] == 6
    assert tuple(material["axis_refs"]) == cs.P7_R54_AHR_CS04_RATING_AXIS_REFS
    assert material["rating_axis_target_thresholds"] == cs.P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS
    assert material["rating_rows_bodyfree_only"] is True
    assert material["rating_rows_match_sanitized_review_result_case_refs"] is True
    assert material["rating_rows_have_required_axis_scores"] is True
    assert material["rating_scores_in_range"] is True
    assert material["rating_rows_have_allowed_verdict_refs"] is True
    assert material["below_target_axis_ref_counts"] == {axis: 0 for axis in cs.P7_R54_AHR_CS04_RATING_AXIS_REFS}
    assert material["below_target_axis_counts"] == material["below_target_axis_ref_counts"]
    assert material["below_target_case_count"] == 0
    assert material["verdict_counts"] == {"PASS": 24}
    assert material["pass_case_count"] == 24
    assert material["yellow_case_count"] == 0
    assert material["repair_required_case_count"] == 0
    assert material["blocked_case_count"] == 0
    assert material["not_reviewable_case_count"] == 0
    assert material["readfeel_blocker_id_counts"] == {}
    assert material["execution_blocker_id_counts"] == {}
    assert material["rating_rows_normalized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["blocker_question_need_observation_normalization_allowed_next"] is True
    assert material["question_need_observation_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS12_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS11_ALLOWED_TRUE_FALSE_FLAG_REFS)


def test_cs11_rating_rows_preserve_source_refs_and_bodyfree_boundaries() -> None:
    material = _build_ready_cs11()

    for row in material["rating_rows"]:
        assert set(row) == set(cs.P7_R54_AHR_CS11_RATING_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == cs.P7_R54_AHR_CS11_RATING_ROW_SCHEMA_VERSION
        assert row["review_session_id"] == cs.P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID
        assert row["source_review_result_row_ref"].startswith("review_result_row_")
        assert row["rating_row_ref"].startswith("rating_row_")
        assert row["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
        assert set(row["axis_scores"]) == set(cs.P7_R54_AHR_CS04_RATING_AXIS_REFS)
        assert row["axis_score_count"] == 6
        assert row["axis_targets"] == cs.P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS
        for flag_ref in cs.P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS:
            assert row[flag_ref] is False
        assert row["body_free"] is True


def test_cs11_rating_row_normalization_counts_below_target_and_blockers() -> None:
    material = _build_ready_cs11(mixed=True)

    assert material["rating_row_normalization_status_ref"] == cs.P7_R54_AHR_CS11_NORMALIZED_STATUS_REF
    assert material["rating_row_count"] == 24
    assert material["below_target_axis_ref_counts"]["creepy_absence"] == 1
    assert material["below_target_axis_ref_counts"]["history_connection_naturalness"] == 1
    assert material["below_target_axis_ref_counts"]["overclaim_absence"] == 1
    assert material["below_target_case_count"] == 3
    assert material["verdict_counts"]["PASS"] == 21
    assert material["verdict_counts"]["YELLOW"] == 1
    assert material["verdict_counts"]["REPAIR_REQUIRED"] == 1
    assert material["verdict_counts"]["BLOCKED"] == 1
    assert material["readfeel_blocker_row_source_count"] == 2
    assert material["execution_blocker_row_source_count"] == 1
    assert material["readfeel_blocker_id_counts"][cs.P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS[1]] == 1
    assert material["readfeel_blocker_id_counts"][cs.P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS[0]] == 1
    assert material["execution_blocker_id_counts"][cs.P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS[0]] == 1
    assert material["actual_review_evidence_complete"] is False
    assert cs.assert_p7_r54_ahr_cs11_rating_row_normalization_contract(material) is True


def test_cs11_rejects_mutated_rating_row_bodyfree_flag() -> None:
    material = _build_ready_cs11()
    mutated = deepcopy(material)
    mutated["rating_rows"][0]["question_text_included"] = True

    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs11_rating_row_normalization_contract(mutated)


def test_cs11_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs11()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_row_normalization_bodyfree(
        sanitized_review_result_row_intake=_build_ready_cs10()
    )

    assert alias == primary
    assert cs.assert_p7_r54_ahr_cs11_rating_row_normalization_bodyfree_contract(alias) is True
    assert cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_row_normalization_bodyfree_contract(alias) is True


@pytest.mark.parametrize(
    "promotion_flag",
    (
        "actual_review_evidence_complete",
        "question_need_observation_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_r52_reintake_execution_confirmed",
    ),
)
def test_cs10_cs11_do_not_promote_later_phase_or_release_flags(promotion_flag: str) -> None:
    cs10 = _build_ready_cs10()
    cs11 = _build_ready_cs11()

    assert cs10[promotion_flag] is False
    assert cs11[promotion_flag] is False
