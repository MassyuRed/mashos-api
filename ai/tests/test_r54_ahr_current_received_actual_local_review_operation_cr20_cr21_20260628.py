# -*- coding: utf-8 -*-
"""R54-AHR-CR20/CR21 current received actual local review operation tests."""

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
    cr00_material = cr.build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze()
    cr01_material = cr.build_p7_r54_ahr_cr01_current_received_basis_envelope(
        scope_no_touch_boundary_freeze=cr00_material,
    )
    cr02_material = cr.build_p7_r54_ahr_cr02_historical_helper_refs_separation(
        current_received_basis_envelope=cr01_material,
    )
    cr03_material = cr.build_p7_r54_ahr_cr03_basis_impact_assessment(
        historical_helper_refs_separation=cr02_material,
    )
    cr04_material = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze(
        basis_impact_assessment=cr03_material,
    )
    cr05_material = cr.build_p7_r54_ahr_cr05_local_only_preflight(
        explicit_allow_ref=cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
    )
    cr06_material = cr.build_p7_r54_ahr_cr06_packet_generation_request_bridge(
        local_only_preflight=cr05_material,
    )
    cr07_material = cr.build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
        packet_generation_request_bridge=cr06_material,
        receipt_input=cr.build_p7_r54_ahr_cr07_bodyfree_receipt_input(),
    )
    cr08_material = cr.build_p7_r54_ahr_cr08_reviewer_selection_form(
        packet_generation_receipt_scan=cr07_material,
        reviewer_person_ref=cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
    )
    cr09_material = cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=cr08_material,
        operation_receipt_input=cr.build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input(),
    )
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
    cr18_material = cr.build_p7_r54_ahr_cr18_p6_candidate_only_handoff(
        p5_decision_candidate_repair_separation=cr17_material,
    )
    cr19_material = cr.build_p7_r54_ahr_cr19_p8_material_candidate_only_handoff(
        question_need_observation_normalization=cr13_material,
        rating_question_consistency_guard=cr14_material,
        p5_decision_candidate_repair_separation=cr17_material,
    )
    return {
        "cr00": cr00_material,
        "cr01": cr01_material,
        "cr02": cr02_material,
        "cr03": cr03_material,
        "cr04": cr04_material,
        "cr05": cr05_material,
        "cr06": cr06_material,
        "cr07": cr07_material,
        "cr08": cr08_material,
        "cr09": cr09_material,
        "cr10": cr10_material,
        "cr11": cr11_material,
        "cr12": cr12_material,
        "cr13": cr13_material,
        "cr14": cr14_material,
        "cr15": cr15_material,
        "cr16": cr16_material,
        "cr17": cr17_material,
        "cr18": cr18_material,
        "cr19": cr19_material,
    }


def _ready_chain_with_cr20(rows: list[dict[str, object]] | None = None) -> dict[str, dict[str, object]]:
    chain = _ready_chain(rows)
    chain["cr20"] = cr.build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope(
        cr16_summary=chain["cr16"],
        cr17_p5_decision=chain["cr17"],
        cr18_p6_candidate=chain["cr18"],
        cr19_p8_candidate=chain["cr19"],
    )
    return chain


def _cr00_to_cr20_materials(chain: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    return [chain[f"cr{index:02d}"] for index in range(0, 21)]


def test_cr20_blocks_by_default_without_completed_candidate_sources() -> None:
    material = cr.build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope()

    assert set(material) == set(cr.P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_ENVELOPE_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR20_STEP_REF
    assert material["r52_reintake_handoff_status_ref"] == cr.P7_R54_AHR_CR20_BLOCKED_STATUS_REF
    assert material["r52_reintake_handoff_ready"] is False
    assert material["r52_reintake_handoff_envelope_materialized_here"] is False
    assert material["r52_handoff_candidate_ref"] == ""
    assert material["r52_reintake_execution_allowed_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR20_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.P7_R54_AHR_CR20_CR16_NOT_READY_BLOCKER_REF in material["r52_reintake_handoff_step_blocker_refs"]
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR20_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr20_r52_handoff_candidate_envelope_contract(material) is True


def test_cr20_materializes_r52_handoff_candidate_without_executing_r52() -> None:
    chain = _ready_chain(_p8_candidate_rows())
    material = cr.build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope(
        cr16_summary=chain["cr16"],
        cr17_p5_decision=chain["cr17"],
        cr18_p6_candidate=chain["cr18"],
        cr19_p8_candidate=chain["cr19"],
    )

    assert material["r52_reintake_handoff_status_ref"] == cr.P7_R54_AHR_CR20_READY_STATUS_REF
    assert material["r52_reintake_handoff_ready"] is True
    assert material["r52_reintake_handoff_envelope_materialized_here"] is True
    assert material["r52_handoff_candidate_ref"] == cr.P7_R54_AHR_CR20_R52_HANDOFF_CANDIDATE_REF
    assert material["r52_handoff_candidate_bodyfree_only"] is True
    assert material["r52_handoff_candidate_contains_no_question_text"] is True
    assert material["r52_handoff_candidate_contains_no_body_payload"] is True
    assert material["p5_confirmed_candidate"] is True
    assert material["p5_confirmed_final"] is False
    assert material["p6_candidate_only_handoff_ready"] is True
    assert material["p6_start_allowed"] is False
    assert material["p8_material_candidate_only_handoff_ready"] is True
    assert material["p8_material_candidate_case_refs"] == ["cral_case_ref_001"]
    assert material["p8_start_allowed"] is False
    assert material["r52_reintake_execution_allowed_here"] is False
    assert material["r52_reintake_execution_started_here"] is False
    assert material["r52_reintake_execution_completed_here"] is False
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR20_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR20_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR21_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR20_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr20_r52_handoff_candidate_envelope_contract(material) is True


def test_cr20_blocks_when_p5_decision_is_repair() -> None:
    chain = _ready_chain(_p5_repair_rows())
    material = cr.build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope(
        cr16_summary=chain["cr16"],
        cr17_p5_decision=chain["cr17"],
        cr18_p6_candidate=chain["cr18"],
        cr19_p8_candidate=chain["cr19"],
    )

    assert material["r52_reintake_handoff_ready"] is False
    assert material["r52_reintake_handoff_status_ref"] == cr.P7_R54_AHR_CR20_BLOCKED_STATUS_REF
    assert cr.P7_R54_AHR_CR20_CR17_NOT_READY_BLOCKER_REF in material["r52_reintake_handoff_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR20_CR18_NOT_READY_BLOCKER_REF in material["r52_reintake_handoff_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR20_CR19_NOT_READY_BLOCKER_REF in material["r52_reintake_handoff_step_blocker_refs"]
    assert material["r52_handoff_candidate_ref"] == ""
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["release_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr20_r52_handoff_candidate_envelope_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("r52_reintake_execution_allowed_here", True),
        ("r52_reintake_execution_started_here", True),
        ("r52_reintake_execution_completed_here", True),
        ("r52_reintake_execution_requested_here", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_cr20_contract_rejects_r52_execution_and_promotion_mutations(field: str, value: object) -> None:
    chain = _ready_chain(_p8_candidate_rows())
    material = deepcopy(
        cr.build_p7_r54_ahr_cr20_r52_handoff_candidate_envelope(
            cr16_summary=chain["cr16"],
            cr17_p5_decision=chain["cr17"],
            cr18_p6_candidate=chain["cr18"],
            cr19_p8_candidate=chain["cr19"],
        )
    )
    material[field] = value

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr20_r52_handoff_candidate_envelope_contract(material)


def test_cr21_blocks_by_default_without_validation_materials() -> None:
    material = cr.build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation()

    assert set(material) == set(cr.P7_R54_AHR_CR21_FINAL_VALIDATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR21_FINAL_NO_BODY_NO_QUESTION_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR21_STEP_REF
    assert material["final_validation_status_ref"] == cr.P7_R54_AHR_CR21_BLOCKED_STATUS_REF
    assert material["final_validation_passed"] is False
    assert material["missing_validation_target_step_ref_count"] == len(cr.P7_R54_AHR_CR21_VALIDATION_TARGET_STEP_REFS)
    assert cr.P7_R54_AHR_CR21_CR20_NOT_READY_BLOCKER_REF in material["final_validation_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR21_MISSING_TARGET_BLOCKER_REF in material["final_validation_step_blocker_refs"]
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR21_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


def test_cr21_validates_cr00_to_cr20_without_promoting_release() -> None:
    chain = _ready_chain_with_cr20(_p8_candidate_rows())
    material = cr.build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation(
        _cr00_to_cr20_materials(chain),
    )

    assert material["final_validation_status_ref"] == cr.P7_R54_AHR_CR21_PASSED_STATUS_REF
    assert material["final_validation_passed"] is True
    assert material["final_validation_step_blocker_refs"] == []
    assert material["missing_validation_target_step_refs"] == []
    assert material["duplicate_validation_target_step_refs"] == []
    assert material["forbidden_key_refs_detected"] == []
    assert material["body_or_question_leak_refs"] == []
    assert material["path_or_hash_leak_refs"] == []
    assert material["contract_mutation_refs"] == []
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["validated_materials_bodyfree_only"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["r52_reintake_execution_allowed_here"] is False
    assert material["r52_reintake_execution_started_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR21_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR21_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR22_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR21_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


def test_cr21_detects_source_body_question_path_hash_without_exporting_leak() -> None:
    chain = _ready_chain_with_cr20(_p8_candidate_rows())
    materials = _cr00_to_cr20_materials(chain)
    leaked = deepcopy(materials)
    leaked[19]["p8_material_candidate_rows"][0]["question_text"] = "forbidden question body"
    leaked[20]["local_absolute_path"] = "/tmp/forbidden/body/full/path"
    material = cr.build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation(leaked)

    assert material["final_validation_passed"] is False
    assert cr.P7_R54_AHR_CR21_FORBIDDEN_KEY_BLOCKER_REF in material["final_validation_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR21_BODY_OR_QUESTION_LEAK_BLOCKER_REF in material["final_validation_step_blocker_refs"]
    assert cr.P7_R54_AHR_CR21_PATH_OR_HASH_LEAK_BLOCKER_REF in material["final_validation_step_blocker_refs"]
    assert material["body_or_question_leak_refs"]
    assert material["path_or_hash_leak_refs"]
    assert "question_text" not in material
    assert "local_absolute_path" not in material
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["release_allowed"] is False
    assert cr.assert_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("r52_reintake_execution_allowed_here", True),
        ("r52_reintake_execution_started_here", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_cr21_contract_rejects_final_validation_promotion_mutations(field: str, value: object) -> None:
    chain = _ready_chain_with_cr20(_p8_candidate_rows())
    material = deepcopy(
        cr.build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation(
            _cr00_to_cr20_materials(chain),
        )
    )
    material[field] = value

    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation_contract(material)


def test_cr20_cr21_alias_functions_match_primary_builders_and_contracts() -> None:
    chain = _ready_chain_with_cr20(_p8_candidate_rows())
    primary_cr20 = chain["cr20"]
    alias_cr20 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_r52_handoff_candidate_envelope_bodyfree(
        cr16_summary=chain["cr16"],
        cr17_p5_decision=chain["cr17"],
        cr18_p6_candidate=chain["cr18"],
        cr19_p8_candidate=chain["cr19"],
    )
    assert alias_cr20 == primary_cr20
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_r52_handoff_candidate_envelope_bodyfree_contract(
            alias_cr20
        )
        is True
    )

    primary_cr21 = cr.build_p7_r54_ahr_cr21_final_no_body_leak_no_question_text_no_touch_validation(
        _cr00_to_cr20_materials(chain),
    )
    alias_cr21 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        _cr00_to_cr20_materials(chain),
    )
    assert alias_cr21 == primary_cr21
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(
            alias_cr21
        )
        is True
    )
