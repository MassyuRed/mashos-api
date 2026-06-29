# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR20-CLR21 contract tests."""

from __future__ import annotations

from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr11
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr13
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr16_clr17_20260627 as clr17
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr18_clr19_20260627 as clr19
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr20_clr21_20260627 as clr


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "local_path",
    "local_absolute_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any], *, allowed_true_false_flags: set[str] | None = None) -> None:
    allowed = allowed_true_false_flags or set()
    assert material["body_free"] is True
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        if key in allowed:
            assert material[key] is True, key
        else:
            assert material[key] is False, key
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r54_clr_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _ready_clr09() -> dict[str, Any]:
    form = clr09.build_p7_r54_clr09_reviewer_selection_form_freeze()
    assert clr09.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(form) is True
    return form


def _completed_clr10() -> dict[str, Any]:
    form = _ready_clr09()
    receipt = clr11.build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form(
        reviewer_selection_form_freeze=form,
        reviewer_ref_ids=["r54-local-reviewer-bodyfree-ref-001"],
    )
    material = clr11.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=form,
        local_human_review_operation_receipt=receipt,
    )
    assert clr11.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True
    return material


def _ready_rows(op10: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return clr11.build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion(op10 or _completed_clr10())


def _ready_clr11(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    op10 = _completed_clr10()
    material = clr11.build_p7_r54_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10,
        reviewer_selection_rows=rows or _ready_rows(op10),
    )
    assert clr11.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True
    return material


def _ready_clr12(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr13.build_p7_r54_clr12_rating_row_normalization(
        sanitized_review_result_row_intake=_ready_clr11(rows),
    )
    assert clr13.assert_p7_r54_clr12_rating_row_normalization_contract(material) is True
    return material


def _ready_clr13(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr13.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=_ready_clr12(rows),
    )
    assert clr13.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True
    return material


def _ready_clr14(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr15.build_p7_r54_clr14_question_need_observation_normalization(
        readfeel_blocker_execution_blocker_ingestion=_ready_clr13(rows),
    )
    assert clr15.assert_p7_r54_clr14_question_need_observation_normalization_contract(material) is True
    return material


def _ready_clr15(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr15.build_p7_r54_clr15_rating_question_consistency_guard(
        question_need_observation_normalization=_ready_clr14(rows),
    )
    assert clr15.assert_p7_r54_clr15_rating_question_consistency_guard_contract(material) is True
    return material


def _ready_clr17(rows: list[dict[str, Any]] | None = None, *, clr15_material: dict[str, Any] | None = None) -> dict[str, Any]:
    op16 = clr17.build_p7_r54_clr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=clr15_material or _ready_clr15(rows),
    )
    assert clr17.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(op16) is True
    receipt = clr17.build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol(op16)
    material = clr17.build_p7_r54_clr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=op16,
        disposal_receipt=receipt,
    )
    assert clr17.assert_p7_r54_clr17_purge_disposal_receipt_contract(material) is True
    return material


def _ready_clr18(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    guard = _ready_clr15(rows)
    material = clr19.build_p7_r54_clr18_bodyfree_post_review_summary(
        purge_disposal_receipt=_ready_clr17(clr15_material=guard),
        rating_question_consistency_guard=guard,
    )
    assert clr19.assert_p7_r54_clr18_bodyfree_post_review_summary_contract(material) is True
    return material


def _ready_clr19(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr19.build_p7_r54_clr19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_ready_clr18(rows),
    )
    assert clr19.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material) is True
    return material


def test_r54_clr00_to_clr19_are_present_before_clr20_clr21() -> None:
    material = _ready_clr19()

    assert tuple(material["implemented_steps"]) == clr19.P7_R54_CLR19_IMPLEMENTED_STEPS
    assert material["p5_decision_candidate_ref"] == clr19.P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR20_STEP_REF


def test_r54_clr20_default_blocks_without_confirmed_clr19() -> None:
    material = clr.build_p7_r54_clr20_p6_candidate_only_handoff()

    assert set(material) == set(clr.P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR20_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR20_STEP_REF
    assert material["p6_candidate_handoff_status"] == clr.P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_candidate_only_not_start"] is True
    assert material["p6_start_blocked_here"] is True
    assert "p5_confirmed_candidate_not_available_for_clr20_p6_candidate_handoff" in material["open_execution_blocker_ids"]
    assert material["next_required_step"] == clr.P7_R54_CLR20_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr20_p6_candidate_only_handoff_contract(material) is True


def test_r54_clr20_ready_is_candidate_only_not_p6_start() -> None:
    material = clr.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=_ready_clr19(),
    )

    assert set(material) == set(clr.P7_R54_CLR20_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["p6_candidate_handoff_status"] == clr.P7_R54_CLR20_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
    assert material["p6_candidate_handoff_ref"] == clr.P7_R54_CLR20_P6_CANDIDATE_HANDOFF_REF
    assert material["p6_limited_human_readfeel_candidate_ref"] == clr.P7_R54_CLR20_P6_CANDIDATE_REF
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_candidate_only_not_start"] is True
    assert material["p6_start_blocked_here"] is True
    assert material["p8_material_candidate_handoff_allowed_next"] is True
    assert material["p8_question_design_material_candidate"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR21_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
        },
    )
    assert clr.assert_p7_r54_clr20_p6_candidate_only_handoff_contract(material) is True


def test_r54_clr20_blocks_p5_repair_return() -> None:
    rows = _ready_rows()
    rows[0]["verdict"] = "YELLOW"
    rows[0]["overall_read_feeling_ref"] = "felt_generic_or_shallow"
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["axis_scores"] = dict(rows[0]["axis_scores"])
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.75
    p5_decision = _ready_clr19(rows)
    material = clr.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=p5_decision,
    )

    assert p5_decision["p5_decision_candidate_ref"] == clr19.P7_R54_CLR19_P5_REPAIR_RETURN_REF
    assert material["p6_candidate_handoff_status"] == clr.P7_R54_CLR20_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert "p5_confirmed_candidate_not_available_for_clr20_p6_candidate_handoff" in material["open_execution_blocker_ids"]
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR20_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert clr.assert_p7_r54_clr20_p6_candidate_only_handoff_contract(material) is True


def test_r54_clr21_blocks_if_clr20_not_ready() -> None:
    clr20 = clr.build_p7_r54_clr20_p6_candidate_only_handoff()
    material = clr.build_p7_r54_clr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=clr20,
    )

    assert set(material) == set(clr.P7_R54_CLR21_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["p8_material_candidate_handoff_status"] == clr.P7_R54_CLR21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF
    assert material["question_need_observation_rows_aggregated"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert "clr20_p6_candidate_handoff_not_ready_for_p8_material_candidate_handoff" in material["open_execution_blocker_ids"]
    assert material["next_required_step"] == clr.P7_R54_CLR21_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(material) is True


def test_r54_clr21_ready_with_no_p8_material_is_candidate_only_no_start() -> None:
    clr20 = clr.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=_ready_clr19(),
    )
    material = clr.build_p7_r54_clr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=clr20,
    )

    assert material["p8_material_candidate_handoff_status"] == clr.P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    assert material["question_need_observation_rows_aggregated"] is True
    assert material["question_need_observation_rows_aggregated_count"] == 24
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p8_material_candidate_allowed_primary_class_counts"] == {}
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_question_design_material_candidate_ref"] == ""
    assert material["p8_material_candidate_handoff_reason_refs"] == [clr.P7_R54_CLR21_NO_MATERIAL_REASON_REF]
    assert material["p8_design_material_candidate_only_not_start"] is True
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["question_api_implemented"] is False
    assert material["question_db_schema_implemented"] is False
    assert material["question_rn_ui_implemented"] is False
    assert material["question_response_key_implemented"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR22_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
        },
    )
    assert clr.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(material) is True


def test_r54_clr21_aggregates_allowed_primary_classes_without_question_text() -> None:
    rows = _ready_rows()
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["ambiguity_kind_refs"] = ["low_information_current_input"]
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"] = ["p8_design_material_candidate"]
    clr20 = clr.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=_ready_clr19(rows),
    )
    material = clr.build_p7_r54_clr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=clr20,
    )

    assert clr20["p8_material_candidate_row_count"] == 1
    assert clr20["p8_material_candidate_allowed_primary_class_counts"] == {"question_may_reduce_overread_risk": 1}
    assert material["p8_material_candidate_handoff_status"] == clr.P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    assert material["p8_material_candidate_row_count"] == 1
    assert material["p8_material_candidate_allowed_primary_class_counts"] == {"question_may_reduce_overread_risk": 1}
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_question_design_material_candidate_ref"] == clr.P7_R54_CLR21_P8_MATERIAL_CANDIDATE_REF
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["question_storage_schema_implemented"] is False
    assert material["question_answer_persistence_implemented"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR22_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "p8_question_design_material_candidate",
        },
    )
    assert clr.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(material) is True


def test_r54_clr21_rejects_question_text_materialization() -> None:
    clr20 = clr.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=_ready_clr19(),
    )
    material = clr.build_p7_r54_clr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=clr20,
    )
    material["question_text_materialized_here"] = True

    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(material)


def test_r54_clr21_aggregates_all_allowed_p8_primary_classes_only() -> None:
    rows = _ready_rows()
    for index, primary_class in enumerate(
        (
            "question_may_reduce_overread_risk",
            "plus_single_question_candidate_later",
            "premium_deep_dive_candidate_later",
        )
    ):
        rows[index]["question_need_primary_class"] = primary_class
        rows[index]["repair_required_refs"] = ["no_repair_required"]
        rows[index]["plan_candidate_flags"] = dict(rows[index]["plan_candidate_flags"])
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["ambiguity_kind_refs"] = ["low_information_current_input"]
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    rows[1]["one_question_fit_ref"] = "fits_one_question"
    rows[1]["ambiguity_kind_refs"] = ["missing_time_scope"]
    rows[1]["plan_candidate_flags"]["plus_single_question_candidate_later"] = True
    rows[2]["one_question_fit_ref"] = "needs_more_than_one_question_not_p7"
    rows[2]["ambiguity_kind_refs"] = ["history_connection_basis_unclear"]
    rows[2]["plan_candidate_flags"]["premium_deep_dive_candidate_later"] = True

    clr20 = clr.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=_ready_clr19(rows),
    )
    material = clr.build_p7_r54_clr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=clr20,
    )

    assert material["p8_material_candidate_row_count"] == 3
    assert material["p8_material_candidate_allowed_primary_class_counts"] == {
        "question_may_reduce_overread_risk": 1,
        "plus_single_question_candidate_later": 1,
        "premium_deep_dive_candidate_later": 1,
    }
    assert set(material["p8_material_candidate_allowed_primary_class_counts"]).issubset(
        set(clr.P7_R54_CLR21_P8_MATERIAL_ALLOWED_PRIMARY_CLASS_REFS)
    )
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["question_api_implemented"] is False
    assert material["question_db_schema_implemented"] is False
    assert material["question_rn_ui_implemented"] is False
    assert clr.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(material) is True


def test_r54_clr20_clr21_keep_historical_helper_refs_out_of_actual_basis() -> None:
    clr20 = clr.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=_ready_clr19(),
    )
    clr21 = clr.build_p7_r54_clr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=clr20,
    )

    assert clr20["existing_op20_current_refs_are_historical_here"] is True
    assert clr20["existing_op20_reused_as_actual_p6_candidate_basis"] is False
    assert clr20["existing_ev18_current_refs_are_historical_here"] is True
    assert clr20["existing_ev18_reused_as_actual_p6_candidate_basis"] is False
    assert clr21["existing_op21_current_refs_are_historical_here"] is True
    assert clr21["existing_op21_reused_as_actual_p8_material_basis"] is False
    assert clr21["existing_ev19_current_refs_are_historical_here"] is True
    assert clr21["existing_ev19_reused_as_actual_p8_material_basis"] is False
    assert clr20["operation_current_refs_are_actual_review_basis"] is True
    assert clr21["operation_current_refs_are_actual_review_basis"] is True
    assert clr.assert_p7_r54_clr20_p6_candidate_only_handoff_contract(clr20) is True
    assert clr.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(clr21) is True
