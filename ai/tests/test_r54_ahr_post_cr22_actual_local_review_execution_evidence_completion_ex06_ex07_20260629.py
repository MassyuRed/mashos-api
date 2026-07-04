# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX06-EX07 tests."""

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


def _ready_ex06() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol(
        reviewer_person_boundary_selection_only_form_freeze=_ready_ex05(),
    )


def _accepted_ex07() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
        actual_local_only_human_review_execution_protocol=_ready_ex06(),
        operation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_OPERATION_RECEIPT_REF,
        reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_local_only_read_receipt_present=True,
        review_started_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_STARTED_BUCKET_REF,
        review_completed_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_COMPLETED_BUCKET_REF,
        reviewed_case_count=24,
        selection_row_count=24,
    )


def test_ex06_blocks_when_ex05_reviewer_boundary_is_not_ready() -> None:
    blocked_ex05 = ex.build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=_ready_ex04(),
    )
    material = ex.build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol(
        reviewer_person_boundary_selection_only_form_freeze=blocked_ex05,
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX06_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_EXECUTION_PROTOCOL_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX06_STEP_REF
    assert material["ex05_reviewer_boundary_ready"] is False
    assert material["execution_protocol_ready"] is False
    assert "ex05_reviewer_boundary_not_ready" in material["execution_protocol_blocker_refs"]
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol_contract(material) is True


def test_ex06_freezes_actual_local_only_review_protocol_without_running_review() -> None:
    material = _ready_ex06()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX06_REQUIRED_FIELD_REFS)
    assert material["execution_protocol_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX06_PROTOCOL_READY_STATUS_REF
    assert material["execution_protocol_ready"] is True
    assert material["execution_protocol_blocker_refs"] == []
    assert tuple(material["execution_protocol_step_refs"]) == ex.P7_R54_AHR_POST_CR22_EX06_PROTOCOL_STEP_REFS
    assert material["execution_protocol_step_ref_count"] == 6
    assert material["protocol_requires_local_only"] is True
    assert material["protocol_requires_must_not_export"] is True
    assert material["protocol_requires_selection_only"] is True
    assert material["required_reviewed_case_count"] == 24
    assert material["required_selection_row_count"] == 24
    assert material["reviewer_must_not_quote_body"] is True
    assert material["reviewer_notes_must_not_export"] is True
    assert material["question_text_must_not_materialize"] is True
    assert material["draft_question_text_must_not_materialize"] is True
    assert material["operation_receipt_required_next"] is True
    assert material["operation_receipt_required_actual_source_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF
    assert material["actual_operation_receipt_intaked_here"] is False
    assert material["operation_receipt_ref_present"] is False
    assert material["reviewer_local_only_read_receipt_present"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["reviewed_case_count"] == 0
    assert material["selection_row_count"] == 0
    assert material["actual_human_review_execution_protocol_does_not_run_review_here"] is True
    assert material["actual_human_review_execution_protocol_does_not_create_selection_rows_here"] is True
    assert material["actual_human_review_execution_protocol_does_not_create_rating_rows_here"] is True
    assert material["actual_human_review_execution_protocol_does_not_create_question_observation_rows_here"] is True
    assert material["actual_human_review_execution_protocol_does_not_create_disposal_receipt_here"] is True
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX07_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol_contract(material) is True


@pytest.mark.parametrize(
    ("kwargs", "expected_blocker"),
    (
        ({"local_only": False}, "protocol_local_only_must_be_true"),
        ({"must_not_export": False}, "protocol_must_not_export_must_be_true"),
        ({"selection_only": False}, "protocol_selection_only_must_be_true"),
        ({"required_reviewed_case_count": 23}, "protocol_reviewed_case_count_required_not_24"),
        ({"required_selection_row_count": 23}, "protocol_selection_row_count_required_not_24"),
        ({"body_quotation_allowed": True}, "protocol_body_quotation_allowed_must_be_false"),
        ({"reviewer_notes_export_allowed": True}, "protocol_reviewer_notes_export_allowed_must_be_false"),
        ({"question_text_allowed": True}, "protocol_question_text_allowed_must_be_false"),
        ({"draft_question_text_allowed": True}, "protocol_draft_question_text_allowed_must_be_false"),
        ({"reviewer_free_text_allowed": True}, "protocol_reviewer_free_text_allowed_must_be_false"),
    ),
)
def test_ex06_blocks_protocol_violations_without_running_review(kwargs: dict[str, object], expected_blocker: str) -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol(
        reviewer_person_boundary_selection_only_form_freeze=_ready_ex05(),
        **kwargs,
    )

    assert material["execution_protocol_ready"] is False
    assert expected_blocker in material["execution_protocol_blocker_refs"]
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_selection_rows_created_here"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_operation_receipt_intaked_here", True),
        ("operation_receipt_ref_present", True),
        ("reviewer_local_only_read_receipt_present", True),
        ("actual_human_review_executed_by_person", True),
        ("reviewed_case_count", 24),
        ("selection_row_count", 24),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_selection_rows_created_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("body_full_packet_content_included", True),
        ("local_absolute_path_included", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex06_contract_rejects_receipt_review_rows_question_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_ready_ex06())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol_contract(material)


def test_ex07_blocks_without_operation_receipt_even_after_ready_protocol() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
        actual_local_only_human_review_execution_protocol=_ready_ex06(),
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX07_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_STEP_REF
    assert material["ex06_execution_protocol_ready"] is True
    assert material["operation_receipt_accepted"] is False
    assert "operation_receipt_ref_missing" in material["operation_receipt_blocker_refs"]
    assert "reviewer_local_only_read_receipt_missing" in material["operation_receipt_blocker_refs"]
    assert "reviewed_case_count_not_24" in material["operation_receipt_blocker_refs"]
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(material) is True


def test_ex07_accepts_bodyfree_actual_operation_receipt_without_completing_evidence() -> None:
    material = _accepted_ex07()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX07_REQUIRED_FIELD_REFS)
    assert material["operation_receipt_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_ACCEPTED_STATUS_REF
    assert material["operation_receipt_accepted"] is True
    assert material["operation_receipt_blocker_refs"] == []
    assert material["operation_receipt_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_OPERATION_RECEIPT_REF
    assert material["operation_receipt_ref_is_bodyfree_ref"] is True
    assert material["reviewer_person_ref"] == ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_matches_ex06"] is True
    assert material["reviewer_local_only_read_receipt_present"] is True
    assert material["review_started_at_bucket_ref_present"] is True
    assert material["review_completed_at_bucket_ref_present"] is True
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["selection_only"] is True
    assert material["actual_source_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF
    assert material["actual_source_guard_passed"] is True
    assert material["operation_receipt_intaked_here"] is True
    assert material["operation_receipt_confirms_actual_person_local_only_review"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_selection_rows_created_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["operation_receipt_does_not_create_selection_rows_here"] is True
    assert material["operation_receipt_does_not_complete_evidence_here"] is True
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX08_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(material) is True


def test_ex07_blocks_when_ex06_protocol_is_not_ready() -> None:
    blocked_ex06 = ex.build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol(
        reviewer_person_boundary_selection_only_form_freeze=_ready_ex05(),
        question_text_allowed=True,
    )
    material = ex.build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
        actual_local_only_human_review_execution_protocol=blocked_ex06,
        operation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_OPERATION_RECEIPT_REF,
        reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_local_only_read_receipt_present=True,
        review_started_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_STARTED_BUCKET_REF,
        review_completed_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_COMPLETED_BUCKET_REF,
        reviewed_case_count=24,
        selection_row_count=24,
    )

    assert material["ex06_execution_protocol_ready"] is False
    assert material["operation_receipt_accepted"] is False
    assert "ex06_execution_protocol_not_ready" in material["operation_receipt_blocker_refs"]
    assert material["actual_human_review_executed_by_person"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("kwargs", "expected_blocker"),
    (
        ({"operation_receipt_ref": ""}, "operation_receipt_ref_missing"),
        ({"reviewer_person_ref": ""}, "reviewer_person_ref_missing"),
        ({"reviewer_person_ref": "other_person_ref"}, "reviewer_person_ref_mismatch"),
        ({"reviewer_local_only_read_receipt_present": False}, "reviewer_local_only_read_receipt_missing"),
        ({"review_started_at_bucket_ref": ""}, "review_started_at_bucket_ref_missing"),
        ({"review_completed_at_bucket_ref": ""}, "review_completed_at_bucket_ref_missing"),
        ({"reviewed_case_count": 23}, "reviewed_case_count_not_24"),
        ({"selection_row_count": 23}, "selection_row_count_not_24"),
        ({"local_only": False}, "local_only_must_be_true"),
        ({"must_not_export": False}, "must_not_export_must_be_true"),
        ({"selection_only": False}, "selection_only_must_be_true"),
        ({"actual_source_ref": "helper_default_fixture_rows"}, "operation_receipt_actual_source_ref_not_allowed"),
        ({"raw_input_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"returned_emlis_body_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"history_surface_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"comment_text_body_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"reviewer_free_text_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"reviewer_notes_body_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"question_text_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"draft_question_text_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"packet_content_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"body_full_packet_content_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"local_absolute_path_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"body_hash_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
        ({"terminal_output_body_included": True}, "operation_receipt_forbidden_body_path_hash_or_question_flag"),
    ),
)
def test_ex07_blocks_bad_operation_receipt_without_echoing_body_or_promotion(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    base = {
        "operation_receipt_ref": ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_OPERATION_RECEIPT_REF,
        "reviewer_person_ref": ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        "reviewer_local_only_read_receipt_present": True,
        "review_started_at_bucket_ref": ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_STARTED_BUCKET_REF,
        "review_completed_at_bucket_ref": ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_COMPLETED_BUCKET_REF,
        "reviewed_case_count": 24,
        "selection_row_count": 24,
    }
    base.update(kwargs)
    material = ex.build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
        actual_local_only_human_review_execution_protocol=_ready_ex06(),
        **base,
    )

    assert material["operation_receipt_accepted"] is False
    assert expected_blocker in material["operation_receipt_blocker_refs"]
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_selection_rows_created_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["raw_input_included"] is False
    assert material["returned_emlis_body_included"] is False
    assert material["reviewer_notes_body_included"] is False
    assert material["question_text_included"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(material) is True


def test_ex07_rejects_path_shaped_receipt_reviewer_and_bucket_refs_without_echoing_paths() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
        actual_local_only_human_review_execution_protocol=_ready_ex06(),
        operation_receipt_ref="/tmp/secret_operation_receipt",
        reviewer_person_ref="C:\\secret\\person_ref",
        reviewer_local_only_read_receipt_present=True,
        review_started_at_bucket_ref="../secret/started_bucket",
        review_completed_at_bucket_ref="./secret/completed_bucket",
        reviewed_case_count=24,
        selection_row_count=24,
    )

    assert material["operation_receipt_accepted"] is False
    assert material["operation_receipt_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_REJECTED_OPERATION_RECEIPT_PATH_SHAPE_REF
    assert material["reviewer_person_ref"] == ex.P7_R54_AHR_POST_CR22_EX05_REJECTED_REVIEWER_PERSON_PATH_SHAPE_REF
    assert material["review_started_at_bucket_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_REJECTED_BUCKET_PATH_SHAPE_REF
    assert material["review_completed_at_bucket_ref"] == ex.P7_R54_AHR_POST_CR22_EX07_REJECTED_BUCKET_PATH_SHAPE_REF
    assert "secret_operation_receipt" not in repr(material)
    assert "secret" not in repr(material)
    assert "operation_receipt_ref_must_be_bodyfree_ref_not_path" in material["operation_receipt_blocker_refs"]
    assert "reviewer_person_ref_must_be_bodyfree_ref_not_path" in material["operation_receipt_blocker_refs"]
    assert "review_started_at_bucket_ref_must_be_bodyfree_ref_not_path" in material["operation_receipt_blocker_refs"]
    assert "review_completed_at_bucket_ref_must_be_bodyfree_ref_not_path" in material["operation_receipt_blocker_refs"]
    assert ex.assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("operation_receipt_accepted", False),
        ("operation_receipt_intaked_here", False),
        ("operation_receipt_confirms_actual_person_local_only_review", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_human_review_run_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_selection_rows_created_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("raw_input_included", True),
        ("reviewer_notes_body_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("body_full_packet_content_included", True),
        ("local_absolute_path_included", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex07_contract_rejects_body_rows_evidence_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_accepted_ex07())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(material)


def test_ex06_and_ex07_alias_functions_match_primary_builders_and_contracts() -> None:
    ex05 = _ready_ex05()
    ex06_primary = _ready_ex06()
    ex06_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_local_only_human_review_execution_protocol_bodyfree(
            reviewer_person_boundary_selection_only_form_freeze=ex05,
        )
    )
    assert ex06_alias == ex06_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_local_only_human_review_execution_protocol_bodyfree_contract(
            ex06_alias
        )
        is True
    )

    ex07_primary = _accepted_ex07()
    ex07_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_operation_receipt_intake_bodyfree(
            actual_local_only_human_review_execution_protocol=ex06_primary,
            operation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_OPERATION_RECEIPT_REF,
            reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
            reviewer_local_only_read_receipt_present=True,
            review_started_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_STARTED_BUCKET_REF,
            review_completed_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_COMPLETED_BUCKET_REF,
            reviewed_case_count=24,
            selection_row_count=24,
        )
    )
    assert ex07_alias == ex07_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_operation_receipt_intake_bodyfree_contract(
            ex07_alias
        )
        is True
    )
