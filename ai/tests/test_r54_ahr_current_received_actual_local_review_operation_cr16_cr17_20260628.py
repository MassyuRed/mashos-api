# -*- coding: utf-8 -*-
"""R54-AHR-CR16/CR17 current received actual local review operation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr


def _assert_bodyfree_no_touch(material: dict[str, object], *, allowed_true_flags: tuple[str, ...] = ()) -> None:
    assert material["body_free"] is True
    allowed = set(allowed_true_flags)
    for key in cr.P7_R54_AHR_CR_FALSE_FLAG_REFS:
        if key in allowed:
            assert material[key] in (False, True), key
            continue
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


def _cr05_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr05_local_only_preflight(
        explicit_allow_ref=cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
    )


def _cr06_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr06_packet_generation_request_bridge(local_only_preflight=_cr05_ready())


def _cr07_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
        packet_generation_request_bridge=_cr06_ready(),
        receipt_input=cr.build_p7_r54_ahr_cr07_bodyfree_receipt_input(),
    )


def _cr08_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr08_reviewer_selection_form(
        packet_generation_receipt_scan=_cr07_ready(),
        reviewer_person_ref=cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
    )


def _cr09_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=_cr08_ready(),
        operation_receipt_input=cr.build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input(),
    )


def _selection_rows() -> list[dict[str, object]]:
    return cr.build_p7_r54_ahr_cr10_bodyfree_selection_result_rows_input()


def _cr10_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        selection_result_rows=rows or _selection_rows(),
    )


def _cr11_ready(cr10_material: dict[str, object] | None = None) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=cr10_material or _cr10_ready(),
    )


def _cr12_ready(cr11_material: dict[str, object] | None = None) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization(
        rating_row_normalization=cr11_material or _cr11_ready(),
    )


def _cr13_ready(
    cr10_material: dict[str, object] | None = None,
    cr11_material: dict[str, object] | None = None,
    cr12_material: dict[str, object] | None = None,
) -> dict[str, object]:
    cr10 = cr10_material or _cr10_ready()
    cr11 = cr11_material or _cr11_ready(cr10)
    cr12 = cr12_material or _cr12_ready(cr11)
    return cr.build_p7_r54_ahr_cr13_question_need_observation_normalization(
        sanitized_selection_only_result_rows_intake=cr10,
        rating_row_normalization=cr11,
        readfeel_execution_blocker_normalization=cr12,
    )


def _cr14_ready(
    cr11_material: dict[str, object] | None = None,
    cr12_material: dict[str, object] | None = None,
    cr13_material: dict[str, object] | None = None,
) -> dict[str, object]:
    cr11 = cr11_material or _cr11_ready()
    cr12 = cr12_material or _cr12_ready(cr11)
    cr13 = cr13_material or _cr13_ready(cr11_material=cr11, cr12_material=cr12)
    return cr.build_p7_r54_ahr_cr14_rating_question_consistency_guard(
        rating_row_normalization=cr11,
        readfeel_execution_blocker_normalization=cr12,
        question_need_observation_normalization=cr13,
    )


def _cr15_ready(
    cr14_material: dict[str, object] | None = None,
    *,
    receipt: dict[str, object] | None = None,
) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
        rating_question_consistency_guard=cr14_material or _cr14_ready(),
        disposal_receipt_input=receipt if receipt is not None else cr.build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(),
    )


def _ready_chain(rows: list[dict[str, object]] | None = None) -> dict[str, dict[str, object]]:
    cr10_material = _cr10_ready(rows)
    cr11_material = _cr11_ready(cr10_material)
    cr12_material = _cr12_ready(cr11_material)
    cr13_material = _cr13_ready(cr10_material, cr11_material, cr12_material)
    cr14_material = _cr14_ready(cr11_material, cr12_material, cr13_material)
    cr15_material = _cr15_ready(cr14_material)
    cr16_material = cr.build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        sanitized_selection_only_result_rows_intake=cr10_material,
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
        question_need_observation_normalization=cr13_material,
        rating_question_consistency_guard=cr14_material,
        disposal_receipt=cr15_material,
    )
    return {
        "cr10": cr10_material,
        "cr11": cr11_material,
        "cr12": cr12_material,
        "cr13": cr13_material,
        "cr14": cr14_material,
        "cr15": cr15_material,
        "cr16": cr16_material,
    }


def _cr16_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    return _ready_chain(rows)["cr16"]


def _cr16_blocked_missing_disposal() -> dict[str, object]:
    cr10_material = _cr10_ready()
    cr11_material = _cr11_ready(cr10_material)
    cr12_material = _cr12_ready(cr11_material)
    cr13_material = _cr13_ready(cr10_material, cr11_material, cr12_material)
    cr14_material = _cr14_ready(cr11_material, cr12_material, cr13_material)
    cr15_blocked = cr.build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
        rating_question_consistency_guard=cr14_material,
        disposal_receipt_input=None,
    )
    return cr.build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        sanitized_selection_only_result_rows_intake=cr10_material,
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
        question_need_observation_normalization=cr13_material,
        rating_question_consistency_guard=cr14_material,
        disposal_receipt=cr15_blocked,
    )


def test_cr16_blocks_by_default_without_ready_evidence_chain() -> None:
    material = cr.build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate()

    assert set(material) == set(cr.P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR16_STEP_REF
    assert material["post_review_summary_status_ref"] == cr.P7_R54_AHR_CR16_EVIDENCE_INCOMPLETE_STATUS_REF
    assert material["post_review_summary_ready"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR16_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_contract(material) is True


def test_cr16_completes_only_when_rows_disposal_and_all_guards_are_complete() -> None:
    material = _cr16_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR16_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS)
    assert material["post_review_summary_status_ref"] == cr.P7_R54_AHR_CR16_EVIDENCE_COMPLETE_STATUS_REF
    assert material["post_review_summary_ready"] is True
    assert material["post_review_summary_step_blocker_refs"] == []
    assert material["post_review_summary_reason_refs"] == [cr.P7_R54_AHR_CR16_READY_REASON_REF]
    assert material["reviewed_case_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_need_observation_row_count"] == 24
    assert material["disposal_verified"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["consistency_guard_passed"] is True
    assert material["actual_human_review_complete"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR16_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR17_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR16_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_contract(material) is True


def test_cr16_stays_incomplete_when_disposal_receipt_is_missing() -> None:
    material = _cr16_blocked_missing_disposal()

    assert material["post_review_summary_status_ref"] == cr.P7_R54_AHR_CR16_EVIDENCE_INCOMPLETE_STATUS_REF
    assert material["post_review_summary_ready"] is False
    assert cr.P7_R54_AHR_CR16_CR15_NOT_READY_BLOCKER_REF in material["post_review_summary_step_blocker_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_human_review_complete"] is False
    assert material["disposal_verified"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR16_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_review_evidence_complete", False),
        ("actual_human_review_complete", False),
        ("p5_confirmed_final", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("r52_reintake_execution_requested_here", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_cr16_contract_rejects_completion_and_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_cr16_ready())
    material[field] = value

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate_contract(material)


def test_cr17_blocks_without_complete_cr16_summary() -> None:
    material = cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
        post_review_summary=cr.build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate()
    )

    assert set(material) == set(cr.P7_R54_AHR_CR17_P5_DECISION_CANDIDATE_REPAIR_SEPARATION_REQUIRED_FIELD_REFS)
    assert material["p5_decision_candidate_separation_status_ref"] == cr.P7_R54_AHR_CR17_BLOCKED_STATUS_REF
    assert material["p5_decision_candidate_separation_ready"] is False
    assert cr.P7_R54_AHR_CR17_CR16_NOT_COMPLETE_BLOCKER_REF in material["p5_decision_candidate_separation_step_blocker_refs"]
    assert material["p5_confirmed_candidate"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR17_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(material) is True


def test_cr17_separates_clean_p5_confirmed_candidate_without_p5_finalization() -> None:
    material = cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
        post_review_summary=_cr16_ready()
    )

    assert material["p5_decision_candidate_separation_status_ref"] == cr.P7_R54_AHR_CR17_CONFIRMED_CANDIDATE_STATUS_REF
    assert material["p5_decision_candidate_separation_ready"] is True
    assert material["p5_decision_ref"] == "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY"
    assert material["p5_confirmed_candidate"] is True
    assert material["p5_confirmed_candidate_only"] is True
    assert material["p5_confirmed_candidate_is_not_p5_final"] is True
    assert material["p5_decision_candidate_ready_for_r52_handoff"] is True
    assert material["p5_confirmed_final"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR18_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR17_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(material) is True


def test_cr17_separates_p5_repair_required_without_p8_escape() -> None:
    rows = _selection_rows()
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.10
    material = cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
        post_review_summary=_cr16_ready(rows)
    )

    assert material["p5_decision_candidate_separation_status_ref"] == cr.P7_R54_AHR_CR17_REPAIR_OR_BLOCKED_STATUS_REF
    assert material["p5_decision_ref"] == "P5_REPAIR_REQUIRED_BEFORE_R52_REINTAKE"
    assert material["p5_repair_required_before_r52"] is True
    assert material["p5_repair_required_case_count"] == 1
    assert material["p5_repair_required_not_promoted_to_p8_material_candidate"] is True
    assert material["p8_start_allowed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR17_REPAIR_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(material) is True


def test_cr17_separates_p4_current_only_repair_required_without_p8_escape() -> None:
    rows = _selection_rows()
    rows[0]["repair_required_refs"] = ["p4_current_surface_repair_required"]
    material = cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
        post_review_summary=_cr16_ready(rows)
    )

    assert material["p5_decision_candidate_separation_status_ref"] == cr.P7_R54_AHR_CR17_REPAIR_OR_BLOCKED_STATUS_REF
    assert material["p5_decision_ref"] == "P4_CURRENT_ONLY_REPAIR_REQUIRED_BEFORE_R52_REINTAKE"
    assert material["p4_current_only_repair_required_before_r52"] is True
    assert material["p4_current_only_repair_required_case_count"] == 1
    assert material["p8_material_candidate_only_is_not_p8_start_allowed"] is True
    assert material["p8_start_allowed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR17_REPAIR_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(material) is True


def test_cr16_cr17_alias_functions_match_primary_builders_and_contracts() -> None:
    chain = _ready_chain()
    primary_cr16 = chain["cr16"]
    alias_cr16 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_post_review_summary_bodyfree(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        sanitized_selection_only_result_rows_intake=chain["cr10"],
        rating_row_normalization=chain["cr11"],
        readfeel_execution_blocker_normalization=chain["cr12"],
        question_need_observation_normalization=chain["cr13"],
        rating_question_consistency_guard=chain["cr14"],
        disposal_receipt=chain["cr15"],
    )
    assert alias_cr16 == primary_cr16
    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_post_review_summary_bodyfree_contract(alias_cr16) is True

    primary_cr17 = cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(post_review_summary=primary_cr16)
    alias_cr17 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_p5_decision_candidate_repair_separation_bodyfree(
        post_review_summary=primary_cr16,
    )
    assert alias_cr17 == primary_cr17
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_p5_decision_candidate_repair_separation_bodyfree_contract(
            alias_cr17
        )
        is True
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("p5_confirmed_candidate", False),
        ("p5_confirmed_final", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_cr17_contract_rejects_candidate_and_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(
        cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(post_review_summary=_cr16_ready())
    )
    material[field] = value

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation_contract(material)
