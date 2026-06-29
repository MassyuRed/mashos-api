# -*- coding: utf-8 -*-
"""R54-AHR-CR18/CR19 current received actual local review operation tests."""

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


def _p8_candidate_rows() -> list[dict[str, object]]:
    rows = _selection_rows()
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    return rows


def _p5_repair_rows() -> list[dict[str, object]]:
    rows = _selection_rows()
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.10
    return rows


def _ready_chain(rows: list[dict[str, object]] | None = None) -> dict[str, dict[str, object]]:
    cr09_material = _cr09_ready()
    cr10_material = cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=cr09_material,
        selection_result_rows=rows or _selection_rows(),
    )
    cr11_material = cr.build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=cr10_material,
    )
    cr12_material = cr.build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization(
        rating_row_normalization=cr11_material,
    )
    cr13_material = cr.build_p7_r54_ahr_cr13_question_need_observation_normalization(
        sanitized_selection_only_result_rows_intake=cr10_material,
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
    )
    cr14_material = cr.build_p7_r54_ahr_cr14_rating_question_consistency_guard(
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
        question_need_observation_normalization=cr13_material,
    )
    cr15_material = cr.build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
        rating_question_consistency_guard=cr14_material,
        disposal_receipt_input=cr.build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(),
    )
    cr16_material = cr.build_p7_r54_ahr_cr16_post_review_summary_evidence_complete_predicate(
        actual_local_human_review_operation_receipt=cr09_material,
        sanitized_selection_only_result_rows_intake=cr10_material,
        rating_row_normalization=cr11_material,
        readfeel_execution_blocker_normalization=cr12_material,
        question_need_observation_normalization=cr13_material,
        rating_question_consistency_guard=cr14_material,
        disposal_receipt=cr15_material,
    )
    cr17_material = cr.build_p7_r54_ahr_cr17_p5_decision_candidate_repair_separation(
        post_review_summary=cr16_material,
    )
    return {
        "cr09": cr09_material,
        "cr10": cr10_material,
        "cr11": cr11_material,
        "cr12": cr12_material,
        "cr13": cr13_material,
        "cr14": cr14_material,
        "cr15": cr15_material,
        "cr16": cr16_material,
        "cr17": cr17_material,
    }


def _cr17_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    return _ready_chain(rows)["cr17"]


def test_cr18_blocks_by_default_without_p5_confirmed_candidate() -> None:
    material = cr.build_p7_r54_ahr_cr18_p6_candidate_only_handoff()

    assert set(material) == set(cr.P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR18_STEP_REF
    assert material["p6_candidate_only_handoff_status_ref"] == cr.P7_R54_AHR_CR18_BLOCKED_STATUS_REF
    assert material["p6_candidate_only_handoff_ready"] is False
    assert material["p6_candidate_only_handoff_materialized"] is False
    assert material["p6_limited_human_readfeel_candidate_only"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.P7_R54_AHR_CR18_CR17_NOT_READY_BLOCKER_REF in material["p6_candidate_only_handoff_step_blocker_refs"]
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR18_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr18_p6_candidate_only_handoff_contract(material) is True


def test_cr18_hands_off_p6_candidate_only_without_starting_p6() -> None:
    material = cr.build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
        p5_decision_candidate_repair_separation=_cr17_ready(),
    )

    assert material["p6_candidate_only_handoff_status_ref"] == cr.P7_R54_AHR_CR18_READY_STATUS_REF
    assert material["p6_candidate_only_handoff_ready"] is True
    assert material["p6_candidate_only_handoff_materialized"] is True
    assert material["p6_candidate_only_handoff_step_blocker_refs"] == []
    assert material["p6_candidate_ref"] == cr.P7_R54_AHR_CR18_P6_CANDIDATE_REF
    assert material["p6_limited_human_readfeel_candidate_only"] is True
    assert material["p6_limited_human_readfeel_candidate_materialized"] is True
    assert material["p6_candidate_only_is_not_p6_start_allowed"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p5_confirmed_candidate"] is True
    assert material["p5_confirmed_final"] is False
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR18_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR19_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR18_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr18_p6_candidate_only_handoff_contract(material) is True


def test_cr18_blocks_p6_handoff_when_cr17_contains_p5_repair() -> None:
    material = cr.build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
        p5_decision_candidate_repair_separation=_cr17_ready(_p5_repair_rows()),
    )

    assert material["p6_candidate_only_handoff_ready"] is False
    assert material["p6_candidate_only_handoff_status_ref"] == cr.P7_R54_AHR_CR18_BLOCKED_STATUS_REF
    assert cr.P7_R54_AHR_CR18_P5_CONFIRMED_CANDIDATE_NOT_PRESENT_BLOCKER_REF in material["p6_candidate_only_handoff_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR18_REPAIR_OR_BLOCKER_PRESENT_BLOCKER_REF in material["p6_candidate_only_handoff_step_blocker_refs"]
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr18_p6_candidate_only_handoff_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("p6_start_allowed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p5_confirmed_final", True),
        ("r52_reintake_execution_requested_here", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_cr18_contract_rejects_p6_start_and_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(
        cr.build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
            p5_decision_candidate_repair_separation=_cr17_ready(),
        )
    )
    material[field] = value

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr18_p6_candidate_only_handoff_contract(material)


def test_cr19_blocks_by_default_without_actual_review_candidate_sources() -> None:
    material = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff()

    assert set(material) == set(cr.P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR19_STEP_REF
    assert material["p8_material_candidate_only_handoff_status_ref"] == cr.P7_R54_AHR_CR19_BLOCKED_STATUS_REF
    assert material["p8_material_candidate_only_handoff_ready"] is False
    assert material["p8_material_candidate_only_handoff_materialized"] is False
    assert material["p8_material_candidate_rows"] == []
    assert material["p8_question_text_generation"] is False
    assert material["p8_question_api_implemented"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR19_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.P7_R54_AHR_CR19_CR13_NOT_READY_BLOCKER_REF in material["p8_material_candidate_only_handoff_step_blocker_refs"]
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR19_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(material) is True


def test_cr19_materializes_empty_candidate_only_handoff_without_starting_p8() -> None:
    chain = _ready_chain()
    material = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=chain["cr13"],
        rating_question_consistency_guard=chain["cr14"],
        p5_decision_candidate_repair_separation=chain["cr17"],
    )

    assert material["p8_material_candidate_only_handoff_status_ref"] == cr.P7_R54_AHR_CR19_READY_STATUS_REF
    assert material["p8_material_candidate_only_handoff_ready"] is True
    assert material["p8_material_candidate_only_handoff_materialized"] is True
    assert material["p8_material_candidate_only"] is False
    assert material["p8_material_candidate_rows"] == []
    assert material["no_p8_material_candidate_reason_ref"] == cr.P7_R54_AHR_CR19_NO_P8_MATERIAL_CANDIDATE_REF
    assert material["p8_candidate_rows_bodyfree_only"] is True
    assert material["p8_candidate_rows_have_no_question_text"] is True
    assert material["p8_question_text_generation"] is False
    assert material["p8_question_api_implemented"] is False
    assert material["p8_question_db_schema_implemented"] is False
    assert material["p8_question_rn_ui_implemented"] is False
    assert material["p8_question_trigger_logic_implemented"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR20_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR19_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(material) is True


def test_cr19_extracts_bodyfree_p8_candidate_rows_without_question_text() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    material = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=chain["cr13"],
        rating_question_consistency_guard=chain["cr14"],
        p5_decision_candidate_repair_separation=chain["cr17"],
    )

    assert material["p8_material_candidate_only_handoff_ready"] is True
    assert material["p8_material_candidate_only"] is True
    assert material["p8_material_candidate_row_count"] == 1
    assert material["p8_material_candidate_case_refs"] == ["cral_case_ref_001"]
    assert material["question_may_reduce_overread_risk_case_count"] == 1
    assert material["plus_single_question_candidate_case_count"] == 0
    assert material["premium_deep_dive_candidate_case_count"] == 0
    row = material["p8_material_candidate_rows"][0]
    assert set(row) == set(cr.P7_R54_AHR_CR19_ALLOWED_CANDIDATE_ROW_KEY_REFS)
    assert row == {
        "case_ref_id": "cral_case_ref_001",
        "blind_case_id": "cral_blind_case_001",
        "question_need_primary_class": "question_may_reduce_overread_risk",
        "one_question_fit_ref": "fits_one_question",
        "p8_candidate_reason_ref": "p8_material_candidate_bodyfree_only",
        "plus_or_premium_candidate_ref": cr.P7_R54_AHR_CR19_OVERREAD_RISK_ONLY_CANDIDATE_REF,
        "body_free": True,
    }
    assert "question_text" not in row
    assert "draft_question_text" not in row
    assert "raw_input" not in row
    assert "answer_body" not in row
    assert "history_body" not in row
    assert "reviewer_notes" not in row
    assert material["p8_start_allowed"] is False
    assert material["p8_question_api_implemented"] is False
    assert material["release_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(material) is True


def test_cr19_blocks_p8_handoff_when_cr17_is_repair_not_p5_confirmed_candidate() -> None:
    chain = _ready_chain(_p5_repair_rows())
    material = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=chain["cr13"],
        rating_question_consistency_guard=chain["cr14"],
        p5_decision_candidate_repair_separation=chain["cr17"],
    )

    assert material["p8_material_candidate_only_handoff_ready"] is False
    assert material["p8_material_candidate_only_handoff_status_ref"] == cr.P7_R54_AHR_CR19_BLOCKED_STATUS_REF
    assert cr.P7_R54_AHR_CR19_CR17_P5_CANDIDATE_NOT_CONFIRMED_BLOCKER_REF in material["p8_material_candidate_only_handoff_step_blocker_refs"]
    assert material["p8_material_candidate_rows"] == []
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR19_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("p8_start_allowed", True),
        ("p8_question_text_generation", True),
        ("p8_question_api_implemented", True),
        ("p8_question_db_schema_implemented", True),
        ("p8_question_rn_ui_implemented", True),
        ("p8_question_trigger_logic_implemented", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("p5_confirmed_final", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_cr19_contract_rejects_p8_start_question_implementation_and_promotion_mutations(
    field: str, value: object
) -> None:
    chain = _ready_chain(_p8_candidate_rows())
    material = deepcopy(
        cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
            question_need_observation_normalization=chain["cr13"],
            rating_question_consistency_guard=chain["cr14"],
            p5_decision_candidate_repair_separation=chain["cr17"],
        )
    )
    material[field] = value

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(material)


def test_cr19_contract_rejects_candidate_row_body_or_extra_key_leak() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    material = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=chain["cr13"],
        rating_question_consistency_guard=chain["cr14"],
        p5_decision_candidate_repair_separation=chain["cr17"],
    )
    leaked = deepcopy(material)
    leaked["p8_material_candidate_rows"][0]["question_text"] = "forbidden"

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr19_p8_material_candidate_only_handoff_contract(leaked)


def test_cr18_cr19_alias_functions_match_primary_builders_and_contracts() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    primary_cr18 = cr.build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
        p5_decision_candidate_repair_separation=chain["cr17"],
    )
    alias_cr18 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_p6_candidate_only_handoff_bodyfree(
        p5_decision_candidate_repair_separation=chain["cr17"],
    )
    assert alias_cr18 == primary_cr18
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_p6_candidate_only_handoff_bodyfree_contract(
            alias_cr18
        )
        is True
    )

    primary_cr19 = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=chain["cr13"],
        rating_question_consistency_guard=chain["cr14"],
        p5_decision_candidate_repair_separation=chain["cr17"],
    )
    alias_cr19 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_p8_material_candidate_only_handoff_bodyfree(
        question_need_observation_normalization=chain["cr13"],
        rating_question_consistency_guard=chain["cr14"],
        p5_decision_candidate_repair_separation=chain["cr17"],
    )
    assert alias_cr19 == primary_cr19
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_p8_material_candidate_only_handoff_bodyfree_contract(
            alias_cr19
        )
        is True
    )
