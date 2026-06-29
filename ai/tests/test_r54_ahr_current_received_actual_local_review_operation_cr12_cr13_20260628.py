# -*- coding: utf-8 -*-
"""R54-AHR-CR12/CR13 current received actual local review operation tests."""

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


def test_cr12_blocks_by_default_without_ready_cr11_rating_rows() -> None:
    material = cr.build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization()

    assert set(material) == set(cr.P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR12_STEP_REF
    assert material["readfeel_execution_blocker_normalization_status_ref"] == cr.P7_R54_AHR_CR12_BLOCKERS_BLOCKED_STATUS_REF
    assert material["readfeel_execution_blocker_normalization_ready"] is False
    assert cr.P7_R54_AHR_CR12_CR11_NOT_READY_BLOCKER_REF in material[
        "readfeel_execution_blocker_normalization_step_blocker_refs"
    ]
    assert material["blocker_rows"] == []
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR12_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(material) is True


def test_cr12_normalizes_empty_product_blocker_rows_without_p8_or_evidence_completion() -> None:
    material = _cr12_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR12_READFEEL_EXECUTION_BLOCKER_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["readfeel_execution_blocker_normalization_status_ref"] == cr.P7_R54_AHR_CR12_BLOCKERS_NORMALIZED_STATUS_REF
    assert material["readfeel_execution_blocker_normalization_ready"] is True
    assert material["readfeel_execution_blocker_normalization_reason_refs"] == [cr.P7_R54_AHR_CR12_READY_REASON_REF]
    assert material["readfeel_execution_blocker_normalization_step_blocker_refs"] == []
    assert material["source_rating_row_count"] == 24
    assert material["blocker_row_count"] == 0
    assert material["blocker_rows"] == []
    assert material["p5_repair_required_case_count"] == 0
    assert material["operation_blocked_case_count"] == 0
    assert material["rows_bodyfree_only"] is True
    assert material["p5_repair_required_cases_not_promoted_to_p8_material_candidate"] is True
    assert material["p4_current_repair_cases_not_promoted_to_p8_material_candidate"] is True
    assert material["operation_blocker_cases_not_promoted_to_p8_material_candidate"] is True
    assert material["readfeel_blocker_cases_not_promoted_to_p8_material_candidate"] is True
    assert material["question_need_observation_normalization_allowed_next"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR13_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR12_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(material) is True


def test_cr12_separates_p5_p4_operation_and_inconclusive_blockers_without_p8_escape() -> None:
    rows = _selection_rows()
    rows[0]["readfeel_blocker_ids"] = ["history_connection_weak"]
    rows[1]["repair_required_refs"] = ["p4_current_surface_repair_required"]
    rows[2]["execution_blocker_ids"] = ["question_text_leak", "disposal_missing"]
    rows[3]["question_need_primary_class"] = "insufficient_material_execution_blocker"
    rows[3]["one_question_fit_ref"] = "insufficient_material"
    cr10 = _cr10_ready(rows)
    cr11 = _cr11_ready(cr10)
    material = _cr12_ready(cr11)

    assert material["readfeel_execution_blocker_normalization_ready"] is True
    assert material["blocker_row_count"] == 5
    assert material["readfeel_blocker_row_count"] == 1
    assert material["repair_required_blocker_row_count"] == 1
    assert material["execution_blocker_row_count"] == 2
    assert material["inconclusive_blocker_row_count"] == 1
    assert material["p5_repair_required_case_count"] == 1
    assert material["p4_current_only_repair_required_case_count"] == 1
    assert material["operation_blocked_case_count"] == 1
    assert material["inconclusive_insufficient_material_case_count"] == 1
    assert material["blocker_category_counts"]["p5_history_connection_weak"] == 1
    assert material["blocker_category_counts"]["p4_current_only_surface_repair_required"] == 1
    assert material["blocker_category_counts"]["operation_blocked_question_text"] == 1
    assert material["blocker_category_counts"]["operation_blocked_disposal_missing"] == 1
    assert material["blocker_category_counts"]["inconclusive_insufficient_material"] == 1
    for row in material["blocker_rows"]:
        assert set(row) == set(cr.P7_R54_AHR_CR12_BLOCKER_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == cr.P7_R54_AHR_CR12_BLOCKER_ROW_SCHEMA_VERSION
        assert row["p8_material_candidate_blocked"] is True
        assert row["body_free"] is True
    assert cr.assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(material) is True


def test_cr12_derives_below_target_axis_blocker_rows_bodyfree() -> None:
    rows = _selection_rows()
    rows[0]["axis_scores"] = {axis: 1.0 for axis in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    rows[0]["axis_scores"]["creepy_absence"] = 0.5
    cr10 = _cr10_ready(rows)
    cr11 = _cr11_ready(cr10)
    material = _cr12_ready(cr11)

    assert material["readfeel_execution_blocker_normalization_ready"] is True
    assert material["below_target_axis_blocker_row_count"] == 1
    assert material["blocker_category_counts"]["p5_creepy_or_overclaim_risk"] == 1
    assert material["p5_repair_required_case_count"] == 1
    assert material["below_target_axis_ref_counts"]["creepy_absence"] == 1
    assert cr.assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "changed"),
        ("cr11_schema_version", "changed"),
        ("cr11_next_required_step", "not_cr12"),
        ("readfeel_execution_blocker_normalization_allowed_status_refs", ["changed"]),
        ("readfeel_execution_blocker_normalization_status_ref", cr.P7_R54_AHR_CR12_BLOCKERS_BLOCKED_STATUS_REF),
        ("readfeel_execution_blocker_normalization_ready", False),
        ("readfeel_execution_blocker_normalization_reason_refs", []),
        ("readfeel_execution_blocker_normalization_step_blocker_refs", ["blocked"]),
        ("readfeel_execution_blocker_normalization_step_blocker_ref_count", 99),
        ("source_rating_row_count", 23),
        ("source_rating_row_ref_count", 23),
        ("case_ref_ids_unique", False),
        ("rows_bodyfree_only", False),
        ("readfeel_execution_blockers_separated", False),
        ("p5_repair_required_cases_not_promoted_to_p8_material_candidate", False),
        ("p4_current_repair_cases_not_promoted_to_p8_material_candidate", False),
        ("operation_blocker_cases_not_promoted_to_p8_material_candidate", False),
        ("readfeel_blocker_cases_not_promoted_to_p8_material_candidate", False),
        ("question_need_observation_normalization_allowed_next", False),
        ("actual_rating_rows_materialized_here", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_human_review_run_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr13"),
    ],
)
def test_cr12_rejects_mutations_promotion_or_evidence_claims(key: str, value: object) -> None:
    mutated = deepcopy(_cr12_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(mutated)


def test_cr12_rejects_blocker_row_mutations() -> None:
    rows = _selection_rows()
    rows[0]["readfeel_blocker_ids"] = ["history_connection_weak"]
    cr12 = _cr12_ready(_cr11_ready(_cr10_ready(rows)))
    mutated = deepcopy(cr12)
    mutated["blocker_rows"][0]["p8_material_candidate_blocked"] = False
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization_contract(mutated)


def test_cr13_blocks_by_default_without_ready_inputs() -> None:
    material = cr.build_p7_r54_ahr_cr13_question_need_observation_normalization()

    assert set(material) == set(cr.P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR13_STEP_REF
    assert material["question_need_observation_normalization_status_ref"] == cr.P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF
    assert material["question_need_observation_normalization_ready"] is False
    assert cr.P7_R54_AHR_CR13_CR10_NOT_READY_BLOCKER_REF in material[
        "question_need_observation_normalization_step_blocker_refs"
    ]
    assert cr.P7_R54_AHR_CR13_CR11_NOT_READY_BLOCKER_REF in material[
        "question_need_observation_normalization_step_blocker_refs"
    ]
    assert cr.P7_R54_AHR_CR13_CR12_NOT_READY_BLOCKER_REF in material[
        "question_need_observation_normalization_step_blocker_refs"
    ]
    assert material["question_need_observation_rows"] == []
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR13_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(material) is True


def test_cr13_normalizes_24_question_observation_rows_without_question_text_or_p8_start() -> None:
    material = _cr13_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["question_need_observation_normalization_status_ref"] == cr.P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF
    assert material["question_need_observation_normalization_ready"] is True
    assert material["question_need_observation_normalization_reason_refs"] == [cr.P7_R54_AHR_CR13_READY_REASON_REF]
    assert material["question_need_observation_normalization_step_blocker_refs"] == []
    assert material["source_sanitized_review_result_row_count"] == 24
    assert material["source_rating_row_count"] == 24
    assert material["question_need_observation_row_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_have_no_question_text"] is True
    assert material["question_need_observation_rows_normalized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR14_STEP_REF
    for row in material["question_need_observation_rows"]:
        assert set(row) == set(cr.P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == cr.P7_R54_AHR_CR13_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
        assert row["question_text_materialized_here"] is False
        assert row["draft_question_text_materialized_here"] is False
        assert row["p8_start_allowed"] is False
        assert row["body_free"] is True
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR13_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(material) is True


def test_cr13_marks_overread_risk_as_p8_material_candidate_only_without_starting_p8() -> None:
    rows = _selection_rows()
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    cr10 = _cr10_ready(rows)
    cr11 = _cr11_ready(cr10)
    cr12 = _cr12_ready(cr11)
    material = _cr13_ready(cr10, cr11, cr12)

    assert material["question_need_observation_normalization_ready"] is True
    assert material["p8_material_candidate_case_count"] == 1
    assert material["question_may_reduce_overread_risk_case_count"] == 1
    assert material["p8_start_allowed"] is False
    first = material["question_need_observation_rows"][0]
    assert first["p8_design_material_candidate"] is True
    assert first["p8_material_candidate_reason_ref"] == "p8_material_candidate_bodyfree_only"
    assert first["p8_implementation_spec_finalized_here"] is False
    assert first["p8_start_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(material) is True


@pytest.mark.parametrize(
    "patch,expected_flag,expected_reason",
    [
        (
            {"readfeel_blocker_ids": ["history_connection_weak"]},
            "p5_repair_required",
            "not_p8_material_p5_repair_required",
        ),
        (
            {"repair_required_refs": ["p4_current_surface_repair_required"]},
            "p4_current_surface_repair_required",
            "not_p8_material_p4_current_only_repair_required",
        ),
        (
            {"execution_blocker_ids": ["disposal_missing"]},
            "operation_blocker_present",
            "not_p8_material_operation_blocker_present",
        ),
        (
            {
                "question_need_primary_class": "question_would_make_immediate_observation_heavy",
                "one_question_fit_ref": "would_delay_immediate_observation",
            },
            "question_would_make_immediate_observation_heavy",
            "not_p8_material_question_would_make_immediate_observation_heavy",
        ),
    ],
)
def test_cr13_does_not_promote_repair_operation_or_heavy_rows_to_p8_material(
    patch: dict[str, object], expected_flag: str, expected_reason: str
) -> None:
    rows = _selection_rows()
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    rows[0].update(patch)
    cr10 = _cr10_ready(rows)
    cr11 = _cr11_ready(cr10)
    cr12 = _cr12_ready(cr11)
    material = _cr13_ready(cr10, cr11, cr12)

    assert material["question_need_observation_normalization_ready"] is True
    first = material["question_need_observation_rows"][0]
    assert first[expected_flag] is True
    assert first["p8_design_material_candidate"] is False
    assert first["p8_material_candidate_reason_ref"] == expected_reason
    assert material["p8_material_candidate_case_count"] == 0
    assert material["p8_start_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "changed"),
        ("cr10_schema_version", "changed"),
        ("cr11_schema_version", "changed"),
        ("cr12_schema_version", "changed"),
        ("question_need_observation_normalization_allowed_status_refs", ["changed"]),
        ("question_need_observation_normalization_status_ref", cr.P7_R54_AHR_CR13_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF),
        ("question_need_observation_normalization_ready", False),
        ("question_need_observation_normalization_reason_refs", []),
        ("question_need_observation_normalization_step_blocker_refs", ["blocked"]),
        ("question_need_observation_normalization_step_blocker_ref_count", 99),
        ("source_sanitized_review_result_row_count", 23),
        ("source_rating_row_count", 23),
        ("question_need_observation_row_count", 23),
        ("question_need_observation_row_ref_count", 23),
        ("case_ref_ids_unique", False),
        ("question_need_primary_class_options", []),
        ("one_question_fit_option_refs", []),
        ("rows_bodyfree_only", False),
        ("rows_have_no_question_text", False),
        ("question_need_observation_rows_normalized_here", False),
        ("actual_question_need_observation_rows_materialized_here", False),
        ("actual_rating_rows_materialized_here", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_human_review_run_here", True),
        ("actual_review_evidence_complete", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("p8_start_allowed", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr14"),
    ],
)
def test_cr13_rejects_mutations_promotion_or_evidence_completion_claims(key: str, value: object) -> None:
    mutated = deepcopy(_cr13_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(mutated)


def test_cr13_rejects_question_observation_row_mutations() -> None:
    mutated = deepcopy(_cr13_ready())
    mutated["question_need_observation_rows"][0]["question_text_materialized_here"] = True
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr13_question_need_observation_normalization_contract(mutated)


def test_cr12_cr13_alias_functions_match_primary_builders_and_contracts() -> None:
    cr10 = _cr10_ready()
    cr11 = _cr11_ready(cr10)
    cr12 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_readfeel_execution_blocker_normalization_bodyfree(
        rating_row_normalization=cr11,
    )
    cr13 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_question_need_observation_normalization_bodyfree(
        sanitized_selection_only_result_rows_intake=cr10,
        rating_row_normalization=cr11,
        readfeel_execution_blocker_normalization=cr12,
    )

    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_readfeel_execution_blocker_normalization_bodyfree_contract(cr12) is True
    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_question_need_observation_normalization_bodyfree_contract(cr13) is True
    assert cr12["operation_step_ref"] == cr.P7_R54_AHR_CR12_STEP_REF
    assert cr13["operation_step_ref"] == cr.P7_R54_AHR_CR13_STEP_REF
    assert cr12["next_required_step"] == cr.P7_R54_AHR_CR13_STEP_REF
    assert cr13["next_required_step"] == cr.P7_R54_AHR_CR14_STEP_REF
