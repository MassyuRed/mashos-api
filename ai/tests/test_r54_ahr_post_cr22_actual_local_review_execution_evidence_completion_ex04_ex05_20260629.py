# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX04-EX05 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


def _assert_bodyfree_no_touch_nonpromotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in ex.P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "postcr22_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in ex.P7_R54_AHR_POST_CR22_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def _ready_ex02() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze()


def _ready_ex03() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=_ready_ex02(),
        explicit_allow_ref=ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF,
    )


def _ready_ex04() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=_ready_ex03(),
        packet_generation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_GENERATION_RECEIPT_REF,
        packet_case_count=ex.P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        packet_completeness_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_COMPLETENESS_SCAN_REF,
        export_denylist_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_EXPORT_DENYLIST_SCAN_REF,
        packet_completeness_passed=True,
        export_denylist_scan_passed=True,
    )


def _ready_ex05() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=_ready_ex04(),
        reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_person_confirmed=True,
    )


def test_ex04_blocks_without_packet_receipt_even_after_ready_preflight() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=_ready_ex03(),
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == (
        ex.P7_R54_AHR_POST_CR22_EX04_LOCAL_BODY_FULL_PACKET_GENERATION_RECEIPT_COMPLETENESS_EXPORT_DENYLIST_BODYFREE_INTAKE_SCHEMA_VERSION
    )
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX04_STEP_REF
    assert material["ex03_local_only_preflight_ready"] is True
    assert material["packet_generation_receipt_accepted"] is False
    assert material["packet_generation_receipt_ref_present"] is False
    assert material["packet_case_count"] == 0
    assert "packet_generation_receipt_ref_missing" in material["packet_generation_receipt_blocker_refs"]
    assert "packet_case_count_not_24" in material["packet_generation_receipt_blocker_refs"]
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["body_full_packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_body_full_packet_generated_here"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert (
        ex.assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
            material
        )
        is True
    )


def test_ex04_accepts_bodyfree_local_packet_generation_receipt_without_exporting_body_path_or_hash() -> None:
    material = _ready_ex04()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX04_REQUIRED_FIELD_REFS)
    assert material["packet_generation_receipt_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_ACCEPTED_STATUS_REF
    assert material["packet_generation_receipt_accepted"] is True
    assert material["packet_generation_receipt_blocker_refs"] == []
    assert material["packet_generation_receipt_ref"] == ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_GENERATION_RECEIPT_REF
    assert material["packet_generation_receipt_ref_is_bodyfree_ref"] is True
    assert material["packet_generation_receipt_actual_source_ref"] == ex.P7_R54_AHR_POST_CR22_EX04_ALLOWED_ACTUAL_SOURCE_REF
    assert material["packet_generation_receipt_source_guard_passed"] is True
    assert material["packet_case_count"] == 24
    assert material["packet_case_count_is_24"] is True
    assert material["packet_completeness_scan_ref_present"] is True
    assert material["export_denylist_scan_ref_present"] is True
    assert material["packet_completeness_passed"] is True
    assert material["export_denylist_scan_passed"] is True
    assert material["packet_materialized_for_review_acknowledged_by_bodyfree_receipt"] is True
    assert material["packet_generation_receipt_bodyfree_only"] is True
    assert material["packet_generation_receipt_intaked_here"] is True
    assert material["packet_generation_receipt_does_not_generate_packet_body_here"] is True
    assert material["packet_body_not_exported"] is True
    assert material["packet_content_included"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX05_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert (
        ex.assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
            material
        )
        is True
    )


def test_ex04_blocks_when_ex03_preflight_is_not_ready_and_does_not_promote_packet_claims() -> None:
    blocked_ex03 = ex.build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=_ready_ex02(),
    )
    material = ex.build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=blocked_ex03,
        packet_generation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_GENERATION_RECEIPT_REF,
        packet_case_count=24,
        packet_completeness_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_COMPLETENESS_SCAN_REF,
        export_denylist_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_EXPORT_DENYLIST_SCAN_REF,
        packet_completeness_passed=True,
        export_denylist_scan_passed=True,
    )

    assert material["ex03_local_only_preflight_ready"] is False
    assert material["packet_generation_receipt_accepted"] is False
    assert "ex03_local_only_preflight_not_ready" in material["packet_generation_receipt_blocker_refs"]
    assert material["packet_generation_receipt_intaked_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert (
        ex.assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
            material
        )
        is True
    )


@pytest.mark.parametrize(
    ("kwargs", "expected_blocker"),
    (
        ({"packet_case_count": 23}, "packet_case_count_not_24"),
        ({"packet_completeness_scan_ref": ""}, "packet_completeness_scan_ref_missing"),
        ({"export_denylist_scan_ref": ""}, "export_denylist_scan_ref_missing"),
        ({"packet_completeness_passed": False}, "packet_completeness_scan_not_passed"),
        ({"export_denylist_scan_passed": False}, "export_denylist_scan_not_passed"),
        ({"actual_source_ref": "helper_default_fixture_rows"}, "packet_generation_receipt_actual_source_ref_not_allowed"),
        ({"packet_body_exported": True}, "packet_body_exported"),
        ({"packet_content_included": True}, "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_flag"),
        ({"body_full_packet_content_included": True}, "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_flag"),
        ({"local_absolute_path_included": True}, "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_flag"),
        ({"body_hash_included": True}, "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_flag"),
        ({"terminal_output_body_included": True}, "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_flag"),
    ),
)
def test_ex04_blocks_bad_receipt_count_source_scan_export_or_leak_flags(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    base = {
        "packet_generation_receipt_ref": ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_GENERATION_RECEIPT_REF,
        "packet_case_count": 24,
        "packet_completeness_scan_ref": ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_COMPLETENESS_SCAN_REF,
        "export_denylist_scan_ref": ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_EXPORT_DENYLIST_SCAN_REF,
        "packet_completeness_passed": True,
        "export_denylist_scan_passed": True,
    }
    base.update(kwargs)
    material = ex.build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=_ready_ex03(),
        **base,
    )

    assert material["packet_generation_receipt_accepted"] is False
    assert expected_blocker in material["packet_generation_receipt_blocker_refs"]
    assert material["packet_content_included"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert material["actual_review_evidence_complete"] is False
    assert (
        ex.assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
            material
        )
        is True
    )


def test_ex04_rejects_path_shaped_receipt_and_scan_refs_without_echoing_paths() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=_ready_ex03(),
        packet_generation_receipt_ref="/tmp/secret_packet_receipt",
        packet_case_count=24,
        packet_completeness_scan_ref="C:\\secret\\scan",
        export_denylist_scan_ref="../secret/export_scan",
        packet_completeness_passed=True,
        export_denylist_scan_passed=True,
    )

    assert material["packet_generation_receipt_accepted"] is False
    assert material["packet_generation_receipt_ref"] == ex.P7_R54_AHR_POST_CR22_EX04_REJECTED_RECEIPT_PATH_SHAPE_REF
    assert material["packet_completeness_scan_ref"] == ex.P7_R54_AHR_POST_CR22_EX04_REJECTED_SCAN_PATH_SHAPE_REF
    assert material["export_denylist_scan_ref"] == ex.P7_R54_AHR_POST_CR22_EX04_REJECTED_SCAN_PATH_SHAPE_REF
    assert "secret_packet_receipt" not in repr(material)
    assert "secret" not in repr(material)
    assert "packet_generation_receipt_ref_must_be_bodyfree_ref_not_path" in material["packet_generation_receipt_blocker_refs"]
    assert "packet_completeness_scan_ref_must_be_bodyfree_ref_not_path" in material["packet_generation_receipt_blocker_refs"]
    assert "export_denylist_scan_ref_must_be_bodyfree_ref_not_path" in material["packet_generation_receipt_blocker_refs"]
    assert (
        ex.assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
            material
        )
        is True
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("packet_generation_receipt_accepted", False),
        ("packet_case_count", 23),
        ("packet_completeness_passed", False),
        ("export_denylist_scan_passed", False),
        ("packet_content_included", True),
        ("body_full_packet_content_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("terminal_output_body_included", True),
        ("body_full_packet_generated_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex04_contract_rejects_receipt_leak_generation_review_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_ready_ex04())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
            material
        )


def test_ex05_blocks_without_reviewer_ref_or_confirmation_after_ready_packet_receipt() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=_ready_ex04(),
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX05_REVIEWER_PERSON_BOUNDARY_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX05_STEP_REF
    assert material["ex04_packet_generation_receipt_accepted"] is True
    assert material["reviewer_boundary_ready"] is False
    assert material["reviewer_person_ref_present"] is False
    assert "reviewer_person_ref_missing" in material["reviewer_boundary_blocker_refs"]
    assert "reviewer_person_confirmed_missing" in material["reviewer_boundary_blocker_refs"]
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


def test_ex05_freezes_reviewer_person_boundary_and_selection_only_form_without_running_review() -> None:
    material = _ready_ex05()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX05_REQUIRED_FIELD_REFS)
    assert material["reviewer_boundary_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_READY_STATUS_REF
    assert material["reviewer_boundary_ready"] is True
    assert material["reviewer_boundary_blocker_refs"] == []
    assert material["reviewer_person_ref"] == ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_is_bodyfree_ref"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_person_boundary_frozen"] is True
    assert material["reviewer_person_identity_bodyfree_only"] is True
    assert material["reviewer_local_only_read_receipt_required_later"] is True
    assert material["reviewer_local_only_read_receipt_present"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["selection_only_form_frozen"] is True
    assert material["selection_only"] is True
    assert material["selection_row_count_required"] == 24
    assert material["free_text_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["question_text_allowed"] is False
    assert material["draft_question_text_allowed"] is False
    assert material["reviewer_free_text_included"] is False
    assert material["reviewer_notes_body_included"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert tuple(material["rating_axis_refs"]) == (
        "history_connection_naturalness",
        "creepy_absence",
        "overclaim_absence",
        "self_blame_non_amplification",
        "wants_more_input_or_accumulation",
        "non_shallow_repeat",
    )
    assert material["rating_axis_count"] == 6
    assert material["question_need_primary_class_option_count"] == 9
    assert material["one_question_fit_option_count"] == 7
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX06_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


@pytest.mark.parametrize(
    ("kwargs", "expected_blocker"),
    (
        ({"reviewer_is_person": False}, "reviewer_is_person_not_confirmed"),
        ({"reviewer_person_confirmed": False}, "reviewer_person_confirmed_missing"),
        ({"selection_row_count_required": 23}, "selection_row_count_required_not_24"),
        ({"free_text_allowed": True}, "free_text_allowed_must_be_false"),
        ({"reviewer_notes_export_allowed": True}, "reviewer_notes_export_allowed_must_be_false"),
        ({"question_text_allowed": True}, "question_text_allowed_must_be_false"),
        ({"draft_question_text_allowed": True}, "draft_question_text_allowed_must_be_false"),
    ),
)
def test_ex05_blocks_reviewer_or_form_boundary_violations_without_starting_review(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    base = {
        "reviewer_person_ref": ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        "reviewer_person_confirmed": True,
    }
    base.update(kwargs)
    material = ex.build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=_ready_ex04(),
        **base,
    )

    assert material["reviewer_boundary_ready"] is False
    assert expected_blocker in material["reviewer_boundary_blocker_refs"]
    assert material["actual_human_review_executed_by_person"] is False
    assert material["reviewer_free_text_included"] is False
    assert material["reviewer_notes_body_included"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["actual_review_evidence_complete"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


def test_ex05_blocks_when_ex04_packet_receipt_is_not_accepted() -> None:
    blocked_ex04 = ex.build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=_ready_ex03(),
    )
    material = ex.build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=blocked_ex04,
        reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_person_confirmed=True,
    )

    assert material["ex04_packet_generation_receipt_accepted"] is False
    assert material["reviewer_boundary_ready"] is False
    assert "ex04_packet_generation_receipt_not_accepted" in material["reviewer_boundary_blocker_refs"]
    assert material["actual_human_review_executed_by_person"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


def test_ex05_rejects_path_shaped_reviewer_ref_without_echoing_path() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=_ready_ex04(),
        reviewer_person_ref="/tmp/secret_reviewer_person",
        reviewer_person_confirmed=True,
    )

    assert material["reviewer_boundary_ready"] is False
    assert material["reviewer_person_ref"] == ex.P7_R54_AHR_POST_CR22_EX05_REJECTED_REVIEWER_PERSON_PATH_SHAPE_REF
    assert material["reviewer_person_ref_has_local_path_shape"] is True
    assert "secret_reviewer_person" not in repr(material)
    assert "reviewer_person_ref_must_be_bodyfree_ref_not_path" in material["reviewer_boundary_blocker_refs"]
    assert ex.assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


def test_ex05_option_lists_match_existing_cr_selection_form_and_design_boundary() -> None:
    material = _ready_ex05()

    assert "PASS" in material["verdict_option_refs"]
    assert "NOT_REVIEWABLE" in material["verdict_option_refs"]
    assert "record_returned_as_natural_line" in material["sanitized_reason_id_option_refs"]
    assert "history_connection_weak" in material["readfeel_blocker_id_option_refs"]
    assert "packet_missing" in material["execution_blocker_id_option_refs"]
    assert "question_may_reduce_overread_risk" in material["question_need_primary_class_options"]
    assert "fits_one_question" in material["one_question_fit_option_refs"]
    assert "history_connection_basis_unclear" in material["ambiguity_kind_option_refs"]
    assert "p5_surface_repair_required" in material["repair_required_ref_option_refs"]
    assert "p8_implementation_spec_finalized_here" in material["plan_candidate_flag_refs"]
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("reviewer_local_only_read_receipt_present", True),
        ("actual_human_review_executed_by_person", True),
        ("reviewer_free_text_included", True),
        ("reviewer_notes_body_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("p8_implementation_spec_finalized_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_selection_rows_created_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex05_contract_rejects_actual_review_rows_question_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_ready_ex05())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(material)


def test_ex04_and_ex05_alias_functions_match_primary_builders_and_contracts() -> None:
    ex03 = _ready_ex03()
    ex04_primary = _ready_ex04()
    ex04_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_bodyfree(
            local_only_preflight_explicit_allow_packet_request_boundary=ex03,
            packet_generation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_GENERATION_RECEIPT_REF,
            packet_case_count=24,
            packet_completeness_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_COMPLETENESS_SCAN_REF,
            export_denylist_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_EXPORT_DENYLIST_SCAN_REF,
            packet_completeness_passed=True,
            export_denylist_scan_passed=True,
        )
    )
    assert ex04_alias == ex04_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_bodyfree_contract(
            ex04_alias
        )
        is True
    )

    ex05_primary = _ready_ex05()
    ex05_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_reviewer_person_boundary_selection_only_form_freeze_bodyfree(
            local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=ex04_primary,
            reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
            reviewer_person_confirmed=True,
        )
    )
    assert ex05_alias == ex05_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_reviewer_person_boundary_selection_only_form_freeze_bodyfree_contract(
            ex05_alias
        )
        is True
    )
