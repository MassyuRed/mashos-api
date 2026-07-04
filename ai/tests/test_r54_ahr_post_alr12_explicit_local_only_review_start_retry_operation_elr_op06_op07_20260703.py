# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP06/OP07 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr

_CLOSED_RETRY_ALR_OP12_CACHE: dict[str, object] | None = None
_OP01_RETRY_CACHE: dict[str, object] | None = None
_OP02_ACCEPTED_CACHE: dict[str, object] | None = None
_OP03_READY_CACHE: dict[str, object] | None = None
_OP04_READY_CACHE: dict[str, object] | None = None
_OP05_ACCEPTED_CACHE: dict[str, object] | None = None
_OP06_PASSED_CACHE: dict[str, object] | None = None


def _alr_op12_pass_status_refs() -> dict[str, str]:
    return {
        key: alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF
        for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS
    }


def _alr_op12_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS}


def _alr_op12_regression_pass_status_refs() -> dict[str, str]:
    return {
        key: alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF
        for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS
    }


def _alr_op12_regression_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS}


def _closed_retry_alr_op12() -> dict[str, object]:
    global _CLOSED_RETRY_ALR_OP12_CACHE
    if _CLOSED_RETRY_ALR_OP12_CACHE is None:
        material = alr.build_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure(
            target_test_result_status_refs=_alr_op12_pass_status_refs(),
            target_test_result_count_refs=_alr_op12_pass_count_refs(),
            selected_regression_result_status_refs=_alr_op12_regression_pass_status_refs(),
            selected_regression_result_count_refs=_alr_op12_regression_pass_count_refs(),
            compileall_result_status_ref=alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF,
            compileall_result_count_ref="passed",
        )
        assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
        assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
        _CLOSED_RETRY_ALR_OP12_CACHE = material
    return deepcopy(_CLOSED_RETRY_ALR_OP12_CACHE)


def _op01_retry() -> dict[str, object]:
    global _OP01_RETRY_CACHE
    if _OP01_RETRY_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
            alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
        )
        assert material["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_ACCEPTED_RETRY_OR_START_REQUIRED_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True
        _OP01_RETRY_CACHE = material
    return deepcopy(_OP01_RETRY_CACHE)


def _valid_allow_receipt() -> dict[str, object]:
    return {
        "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_SCHEMA_VERSION,
        "allow_receipt_ref": "elr_op02_explicit_local_only_allow_receipt_bodyfree_ref_20260703_v1",
        "review_session_id": elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_REVIEW_SESSION_ID,
        "allow_scope_ref": elr.P7_R54_AHR_POST_ALR12_ELR_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_REF,
        "allowed_case_count": elr.P7_R54_AHR_POST_ALR12_ELR_EXPECTED_REVIEW_CASE_COUNT,
        "allow_body_full_packet_generation_local_only": True,
        "allow_actual_local_only_human_review": True,
        "allow_selection_only_recording": True,
        "allow_bodyfree_evidence_creation": True,
        "allow_disposal_purge_required": True,
        "external_export_allowed": False,
        "raw_body_persistence_allowed": False,
        "question_text_persistence_allowed": False,
        "local_path_persistence_allowed": False,
        "hash_persistence_allowed": False,
        "terminal_body_persistence_allowed": False,
        "body_free": True,
    }


def _op02_accepted() -> dict[str, object]:
    global _OP02_ACCEPTED_CACHE
    if _OP02_ACCEPTED_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op02_explicit_local_only_allow_receipt_acceptance_gate(
            op01_alr_op12_result_memo_selected_action_intake=_op01_retry(),
            explicit_local_only_allow_receipt_optional=_valid_allow_receipt(),
        )
        assert material["allow_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP02_STATUS_ACCEPTED_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op02_explicit_local_only_allow_receipt_acceptance_gate_contract(material) is True
        _OP02_ACCEPTED_CACHE = material
    return deepcopy(_OP02_ACCEPTED_CACHE)


def _op03_ready() -> dict[str, object]:
    global _OP03_READY_CACHE
    if _OP03_READY_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op03_local_only_review_session_envelope_role_boundary(
            explicit_local_only_allow_receipt_acceptance_gate=_op02_accepted(),
            operator_ref="karen_local_operator_bodyfree_ref",
            reviewer_person_ref="reviewer_person_bodyfree_ref_20260703",
            reviewer_is_person_confirmed=True,
            local_only_operation_confirmed=True,
        )
        assert material["review_session_envelope_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP03_STATUS_READY_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op03_local_only_review_session_envelope_role_boundary_contract(material) is True
        _OP03_READY_CACHE = material
    return deepcopy(_OP03_READY_CACHE)


def _case_refs(count: int = 24) -> list[str]:
    return [f"elr_op04_case_ref_{index:02d}" for index in range(1, count + 1)]


def _op04_ready() -> dict[str, object]:
    global _OP04_READY_CACHE
    if _OP04_READY_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary(
            local_only_review_session_envelope_role_boundary=_op03_ready(),
            case_refs=_case_refs(),
            packet_request_ref=elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_PACKET_REQUEST_REF,
        )
        assert material["manifest_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_READY_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary_contract(material) is True
        _OP04_READY_CACHE = material
    return deepcopy(_OP04_READY_CACHE)


def _valid_packet_generation_receipt(*, packet_request_ref: str | None = None) -> dict[str, object]:
    return {
        "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION,
        "packet_generation_receipt_ref": "elr_op05_packet_generation_receipt_bodyfree_ref_20260703_v1",
        "review_session_id": elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_REVIEW_SESSION_ID,
        "packet_request_ref": packet_request_ref or elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_PACKET_REQUEST_REF,
        "generated_local_only": True,
        "packet_case_count": elr.P7_R54_AHR_POST_ALR12_ELR_EXPECTED_REVIEW_CASE_COUNT,
        "manifest_case_refs_match": True,
        "external_export_performed": False,
        "packet_body_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def _op05_accepted() -> dict[str, object]:
    global _OP05_ACCEPTED_CACHE
    if _OP05_ACCEPTED_CACHE is None:
        op04 = _op04_ready()
        material = elr.build_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
            manifest_bodyfull_packet_request_boundary=op04,
            packet_generation_receipt_optional=_valid_packet_generation_receipt(packet_request_ref=op04["packet_request_ref"]),
        )
        assert material["packet_generation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_STATUS_ACCEPTED_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(material) is True
        _OP05_ACCEPTED_CACHE = material
    return deepcopy(_OP05_ACCEPTED_CACHE)


def _valid_packet_scan_receipt(*, packet_generation_receipt_ref: str | None = None, packet_request_ref: str | None = None) -> dict[str, object]:
    op05 = _op05_accepted()
    return {
        "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_PACKET_SCAN_RECEIPT_SCHEMA_VERSION,
        "packet_scan_receipt_ref": "elr_op06_packet_completeness_export_scan_receipt_bodyfree_ref_20260703_v1",
        "review_session_id": elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_REVIEW_SESSION_ID,
        "packet_generation_receipt_ref": packet_generation_receipt_ref or str(op05["packet_generation_receipt_ref"]),
        "packet_request_ref": packet_request_ref or str(op05["op04_packet_request_ref"]),
        "packet_case_count": elr.P7_R54_AHR_POST_ALR12_ELR_EXPECTED_REVIEW_CASE_COUNT,
        "packet_manifest_case_refs_match": True,
        "packet_completeness_checked": True,
        "packet_completeness_passed": True,
        "export_denylist_scan_completed": True,
        "export_denylist_violation_count": 0,
        "export_denylist_violation_refs": [],
        "external_export_performed": False,
        "packet_body_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "reviewer_note_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def _op06_passed() -> dict[str, object]:
    global _OP06_PASSED_CACHE
    if _OP06_PASSED_CACHE is None:
        op05 = _op05_accepted()
        material = elr.build_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt(
            bodyfull_packet_generation_local_receipt_intake_boundary=op05,
            packet_scan_receipt_optional=_valid_packet_scan_receipt(
                packet_generation_receipt_ref=str(op05["packet_generation_receipt_ref"]),
                packet_request_ref=str(op05["op04_packet_request_ref"]),
            ),
        )
        assert material["packet_scan_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_STATUS_PASSED_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(material) is True
        _OP06_PASSED_CACHE = material
    return deepcopy(_OP06_PASSED_CACHE)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in elr.P7_R54_AHR_POST_ALR12_ELR_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_alr12_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_elr_op06_missing_packet_scan_receipt_waits_without_review_ready_or_actual_review_permission() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt(
        bodyfull_packet_generation_local_receipt_intake_boundary=_op05_accepted(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_SCHEMA_VERSION
    assert material["op05_ready_for_packet_completeness_export_scan"] is True
    assert material["packet_scan_receipt_present"] is False
    assert material["packet_scan_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_STATUS_WAITING_REF
    assert material["packet_scan_waiting"] is True
    assert material["packet_scan_passed"] is False
    assert material["packet_review_ready"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["actual_review_operation_lifecycle_started_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_CREATE_PACKET_SCAN_RECEIPT_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op06_accepts_bodyfree_packet_completeness_export_scan_receipt_without_starting_review() -> None:
    material = _op06_passed()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP06_REQUIRED_FIELD_REFS)
    assert material["packet_scan_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_STATUS_PASSED_REF
    assert material["packet_scan_passed"] is True
    assert material["packet_review_ready"] is True
    assert material["ready_for_reviewer_person_selection_only_form_freeze"] is True
    assert material["packet_scan_receipt_schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_PACKET_SCAN_RECEIPT_SCHEMA_VERSION
    assert material["packet_case_count"] == 24
    assert material["packet_manifest_case_refs_match"] is True
    assert material["packet_completeness_checked"] is True
    assert material["packet_completeness_passed"] is True
    assert material["export_denylist_scan_completed"] is True
    assert material["export_denylist_violation_count"] == 0
    assert material["export_denylist_violation_refs"] == []
    assert material["external_export_performed"] is False
    assert material["packet_body_included"] is False
    assert material["raw_input_included"] is False
    assert material["question_text_included"] is False
    assert material["reviewer_note_body_included"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["actual_review_operation_lifecycle_started_here"] is False
    assert material["actual_review_operation_lifecycle_capture_required_next"] is True
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("packet_case_count", 23, "elr_op06_packet_case_count_mismatch"),
        ("packet_completeness_passed", False, "elr_op06_packet_completeness_passed_mismatch"),
        ("export_denylist_violation_count", 1, "elr_op06_export_denylist_violation_count_mismatch"),
        ("external_export_performed", True, "elr_op06_external_export_performed_mismatch"),
        ("packet_body_included", True, "elr_op06_packet_body_included_mismatch"),
        ("body_free", False, "elr_op06_body_free_mismatch"),
    ],
)
def test_elr_op06_invalid_packet_scan_receipt_goes_to_repair(field: str, bad_value: object, expected_blocker: str) -> None:
    receipt = _valid_packet_scan_receipt()
    receipt[field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt(
        bodyfull_packet_generation_local_receipt_intake_boundary=_op05_accepted(),
        packet_scan_receipt_optional=receipt,
    )

    assert material["packet_scan_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_STATUS_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op06_blocker_refs"]
    assert material["packet_review_ready"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(material) is True


def test_elr_op06_forbidden_payload_in_scan_receipt_is_repair_without_body_value() -> None:
    receipt = _valid_packet_scan_receipt()
    receipt["raw_input"] = "body-full packet content must never leak"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt(
        bodyfull_packet_generation_local_receipt_intake_boundary=_op05_accepted(),
        packet_scan_receipt_optional=receipt,
    )

    assert material["packet_scan_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_STATUS_REPAIR_REQUIRED_REF
    assert material["packet_scan_receipt_forbidden_payload_key_paths"] == ["packet_scan_receipt.raw_input"]
    assert "must never leak" not in repr(material)
    assert "elr_op06_packet_scan_receipt_forbidden_payload_key_detected" in material["elr_op06_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(material) is True


def test_elr_op06_invalid_op05_goes_to_repair() -> None:
    op05 = _op05_accepted()
    op05["release_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt(
        bodyfull_packet_generation_local_receipt_intake_boundary=op05,
        packet_scan_receipt_optional=_valid_packet_scan_receipt(),
    )

    assert material["packet_scan_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op06_op05_packet_generation_receipt_boundary_contract_invalid_or_missing" in material["elr_op06_blocker_refs"]
    assert material["packet_review_ready"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("packet_scan_passed", False),
        ("packet_review_ready", False),
        ("packet_case_count", 23),
        ("export_denylist_violation_count", 1),
        ("packet_body_included", True),
        ("actual_review_execution_allowed_here", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op06_contract_rejects_scan_ready_body_leak_or_downstream_promotion_mutations(field: str, bad_value: object) -> None:
    material = _op06_passed()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(material)


def test_elr_op07_missing_reviewer_person_or_confirmation_waits_without_actual_review_start() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan_receipt=_op06_passed(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_SCHEMA_VERSION
    assert material["op06_packet_review_ready"] is True
    assert material["reviewer_form_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_STATUS_WAITING_REF
    assert material["reviewer_selection_form_waiting"] is True
    assert material["reviewer_selection_form_ready"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["helper_executes_actual_review"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_REVIEWER_SELECTION_ONLY_FORM_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op07_freezes_person_reviewer_and_selection_only_form_without_starting_actual_review() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan_receipt=_op06_passed(),
        reviewer_person_ref="reviewer_person_bodyfree_ref_20260703",
        reviewer_is_person_confirmed=True,
        local_only_operation_confirmed=True,
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP07_REQUIRED_FIELD_REFS)
    assert material["reviewer_form_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_STATUS_READY_BODYFREE_REF
    assert material["reviewer_selection_form_ready"] is True
    assert material["reviewer_person_ref_present"] is True
    assert material["reviewer_is_person_confirmed"] is True
    assert material["local_only_operation_confirmed"] is True
    assert material["reviewer_form_kind_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_REVIEWER_FORM_SELECTION_ONLY_REF
    assert material["reviewer_form_kind_selection_only"] is True
    assert material["selection_only"] is True
    assert material["reviewer_free_text_allowed"] is False
    assert material["reviewer_note_body_allowed"] is False
    assert material["question_text_allowed"] is False
    assert material["draft_question_text_allowed"] is False
    assert material["answer_text_allowed"] is False
    assert material["selection_only_form_verdict_option_refs"] == list(elr.P7_R54_AHR_POST_ALR12_ELR_REVIEW_VERDICT_OPTION_REFS)
    assert material["question_need_primary_class_option_refs"] == list(elr.P7_R54_AHR_POST_ALR12_ELR_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS)
    assert material["actual_review_execution_allowed_here"] is False
    assert material["helper_executes_actual_review"] is False
    assert material["actual_review_operation_lifecycle_capture_required_next"] is True
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("kwargs", "expected_blocker"),
    [
        ({"reviewer_person_ref": "/tmp/reviewer"}, "elr_op07_reviewer_person_ref_has_local_path_shape"),
        ({"reviewer_form_kind_ref": "free_text_form"}, "elr_op07_reviewer_form_kind_not_selection_only"),
        ({"selection_only": False}, "elr_op07_selection_only_flag_false"),
        ({"reviewer_free_text_allowed": True}, "elr_op07_reviewer_free_text_allowed"),
        ({"question_text_allowed": True}, "elr_op07_question_text_allowed"),
        ({"external_export_allowed": True}, "elr_op07_external_export_allowed"),
    ],
)
def test_elr_op07_invalid_reviewer_or_form_boundary_goes_to_repair(kwargs: dict[str, object], expected_blocker: str) -> None:
    base_kwargs: dict[str, object] = {
        "packet_completeness_export_denylist_scan_receipt": _op06_passed(),
        "reviewer_person_ref": "reviewer_person_bodyfree_ref_20260703",
        "reviewer_is_person_confirmed": True,
        "local_only_operation_confirmed": True,
    }
    base_kwargs.update(kwargs)
    material = elr.build_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze(**base_kwargs)

    assert material["reviewer_form_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_STATUS_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op07_blocker_refs"]
    assert material["reviewer_selection_form_ready"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


def test_elr_op07_forbidden_payload_in_reviewer_form_is_repair_without_body_value() -> None:
    form = {
        "reviewer_person_ref": "reviewer_person_bodyfree_ref_20260703",
        "reviewer_is_person_confirmed": True,
        "local_only_operation_confirmed": True,
        "reviewer_form_kind_ref": elr.P7_R54_AHR_POST_ALR12_ELR_REVIEWER_FORM_SELECTION_ONLY_REF,
        "selection_only": True,
        "reviewer_free_text_allowed": False,
        "reviewer_note_body_allowed": False,
        "question_text_allowed": False,
        "draft_question_text_allowed": False,
        "answer_text_allowed": False,
        "external_export_allowed": False,
        "body_free": True,
        "raw_input": "body-full review form content must never leak",
    }
    material = elr.build_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan_receipt=_op06_passed(),
        reviewer_form_material_optional=form,
    )

    assert material["reviewer_form_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_STATUS_REPAIR_REQUIRED_REF
    assert material["reviewer_form_forbidden_payload_key_paths"] == ["reviewer_selection_form.raw_input"]
    assert "must never leak" not in repr(material)
    assert "elr_op07_reviewer_form_forbidden_payload_key_detected" in material["elr_op07_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


def test_elr_op07_invalid_op06_goes_to_repair() -> None:
    op06 = _op06_passed()
    op06["p8_start_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan_receipt=op06,
        reviewer_person_ref="reviewer_person_bodyfree_ref_20260703",
        reviewer_is_person_confirmed=True,
        local_only_operation_confirmed=True,
    )

    assert material["reviewer_form_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op07_op06_packet_scan_contract_invalid_or_missing" in material["elr_op07_blocker_refs"]
    assert material["reviewer_selection_form_ready"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("reviewer_selection_form_ready", False),
        ("reviewer_is_person_confirmed", False),
        ("selection_only", False),
        ("reviewer_free_text_allowed", True),
        ("actual_review_execution_allowed_here", True),
        ("helper_executes_actual_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op07_contract_rejects_form_breakage_actual_review_claim_or_downstream_promotion_mutations(field: str, bad_value: object) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan_receipt=_op06_passed(),
        reviewer_person_ref="reviewer_person_bodyfree_ref_20260703",
        reviewer_is_person_confirmed=True,
        local_only_operation_confirmed=True,
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(material)


def test_elr_op06_op07_alias_builders_and_contracts_match_canonical_functions() -> None:
    op06 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op06_packet_completeness_export_denylist_scan_receipt(
        bodyfull_packet_generation_local_receipt_intake_boundary=_op05_accepted(),
        packet_scan_receipt_optional=_valid_packet_scan_receipt(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op06_packet_completeness_export_denylist_scan_receipt_contract(op06) is True

    op07 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op07_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan_receipt=op06,
        reviewer_person_ref="reviewer_person_bodyfree_ref_20260703",
        reviewer_is_person_confirmed=True,
        local_only_operation_confirmed=True,
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(op07) is True


def test_elr_op06_op07_result_memo_is_bodyfree_and_limited_to_current_scope() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP07_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    for heading in (
        "## 1. Implementation scope",
        "## 2. Changed files",
        "## 3. Prior implementation confirmation",
        "## 4. ELR-OP06",
        "## 5. ELR-OP07",
        "## 6. Test results",
        "## 7. Not claimed",
        "## 8. Next required step",
    ):
        assert heading in text
    assert "ELR-OP08" in text
    assert "actual_local_human_review_execution: false" in text
    assert "actual_review_execution_allowed_here: false" in text
    assert "body_full_packet_generation_run_here: false" in text
    forbidden_literals = (
        "raw_input:",
        "comment_text:",
        "question_text:",
        "draft_question_text:",
        "terminal output body",
        "body-full packet content must never leak",
    )
    for literal in forbidden_literals:
        assert literal not in text
