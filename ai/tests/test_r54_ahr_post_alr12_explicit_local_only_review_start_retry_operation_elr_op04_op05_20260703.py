# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP04/OP05 tests."""

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


def test_elr_op04_missing_manifest_waits_without_packet_generation_or_review_permission() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary(
        local_only_review_session_envelope_role_boundary=_op03_ready(),
        case_refs=[],
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP04_SCHEMA_VERSION
    assert material["manifest_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_MISSING_OR_INCOMPLETE_REF
    assert material["manifest_missing_or_incomplete"] is True
    assert material["manifest_ready"] is False
    assert material["expected_case_count"] == 24
    assert material["provided_case_count"] == 0
    assert material["case_refs_missing_count"] == 24
    assert material["body_full_packet_generation_request_ready"] is False
    assert material["body_full_packet_generation_allowed_here"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["body_full_packet_body_included"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_24_CASE_MANIFEST_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op04_accepts_24_bodyfree_case_refs_and_creates_only_packet_request_envelope() -> None:
    material = _op04_ready()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP04_REQUIRED_FIELD_REFS)
    assert material["manifest_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_READY_BODYFREE_REF
    assert material["manifest_ready"] is True
    assert material["op03_local_only_review_session_envelope_ready"] is True
    assert material["expected_case_count"] == 24
    assert material["provided_case_count"] == 24
    assert material["unique_case_ref_count"] == 24
    assert material["duplicate_case_ref_count"] == 0
    assert material["case_refs_missing_count"] == 0
    assert material["case_refs_safe"] is True
    assert material["case_refs_match_expected_count"] is True
    assert material["packet_request_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_PACKET_REQUEST_REF
    assert material["bodyfull_packet_request_bodyfree_envelope_created_here"] is True
    assert material["body_full_packet_generation_request_ready"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_generation_run_here"] is False
    assert material["body_full_packet_generation_allowed_here"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_STEP_REF
    assert material["elr_op04_does_not_generate_body_full_packet"] is True
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("case_values", "expected_status", "expected_blocker"),
    [
        (_case_refs(23), elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_MISSING_OR_INCOMPLETE_REF, None),
        (_case_refs(23) + ["elr_op04_case_ref_01"], elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_REPAIR_REQUIRED_REF, "elr_op04_case_ref_duplicate_detected"),
        (["/tmp/bodyfull_case_ref"] + _case_refs(23), elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_REPAIR_REQUIRED_REF, "elr_op04_case_ref_has_local_path_shape"),
        (["question text body should not leak"] + _case_refs(23), elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_REPAIR_REQUIRED_REF, "elr_op04_case_ref_has_question_or_body_text_shape"),
    ],
)
def test_elr_op04_incomplete_or_unsafe_manifest_does_not_generate_packet(case_values: list[str], expected_status: str, expected_blocker: str | None) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary(
        local_only_review_session_envelope_role_boundary=_op03_ready(),
        case_refs=case_values,
    )

    assert material["manifest_status_ref"] == expected_status
    if expected_blocker is not None:
        assert expected_blocker in material["elr_op04_blocker_refs"]
        assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    else:
        assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_24_CASE_MANIFEST_REF
    assert material["body_full_packet_generation_request_ready"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert "should not leak" not in repr(material)
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary_contract(material) is True


def test_elr_op04_invalid_op03_goes_to_repair() -> None:
    op03 = _op03_ready()
    op03["p8_start_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary(
        local_only_review_session_envelope_role_boundary=op03,
        case_refs=_case_refs(),
    )

    assert material["manifest_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP04_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op04_op03_session_envelope_contract_invalid_or_missing" in material["elr_op04_blocker_refs"]
    assert material["manifest_ready"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("manifest_ready", False),
        ("case_refs_match_expected_count", False),
        ("body_full_packet_generation_allowed_here", True),
        ("actual_review_execution_allowed_here", True),
        ("body_full_packet_generated_here", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op04_contract_rejects_packet_generation_or_downstream_promotion_mutations(field: str, bad_value: object) -> None:
    material = _op04_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op04_24_case_manifest_bodyfull_packet_request_boundary_contract(material)


def test_elr_op05_missing_packet_generation_receipt_waits_without_scan_or_review_permission() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
        manifest_bodyfull_packet_request_boundary=_op04_ready(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_SCHEMA_VERSION
    assert material["op04_manifest_ready"] is True
    assert material["packet_generation_receipt_present"] is False
    assert material["packet_generation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_STATUS_MISSING_WAITING_REF
    assert material["packet_generation_receipt_waiting"] is True
    assert material["packet_generation_receipt_accepted"] is False
    assert material["ready_for_packet_completeness_export_scan"] is False
    assert material["body_full_packet_generation_allowed_here"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_generation_run_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_CREATE_PACKET_GENERATION_RECEIPT_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op05_accepts_bodyfree_local_packet_generation_receipt_without_claiming_helper_generated_packet() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
        manifest_bodyfull_packet_request_boundary=_op04_ready(),
        packet_generation_receipt_optional=_valid_packet_generation_receipt(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP05_REQUIRED_FIELD_REFS)
    assert material["packet_generation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_STATUS_ACCEPTED_BODYFREE_REF
    assert material["packet_generation_receipt_accepted"] is True
    assert material["ready_for_packet_completeness_export_scan"] is True
    assert material["packet_generation_receipt_schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION
    assert material["packet_generation_receipt_ref_present"] is True
    assert material["generated_local_only"] is True
    assert material["packet_case_count"] == 24
    assert material["manifest_case_refs_match"] is True
    assert material["external_export_performed"] is False
    assert material["packet_body_included"] is False
    assert material["raw_input_included"] is False
    assert material["comment_text_body_included"] is False
    assert material["local_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert material["packet_generation_receipt_body_free"] is True
    assert material["body_full_packet_generation_receipt_accepted_without_body"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_generation_run_here"] is False
    assert material["actual_body_full_packet_generation_run_here"] is False
    assert material["elr_op05_does_not_generate_body_full_packet"] is True
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP06_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("packet_case_count", 23, "elr_op05_packet_case_count_mismatch"),
        ("generated_local_only", False, "elr_op05_generated_local_only_mismatch"),
        ("external_export_performed", True, "elr_op05_external_export_performed_mismatch"),
        ("packet_body_included", True, "elr_op05_packet_body_included_mismatch"),
        ("body_free", False, "elr_op05_body_free_mismatch"),
    ],
)
def test_elr_op05_invalid_packet_generation_receipt_goes_to_repair(field: str, bad_value: object, expected_blocker: str) -> None:
    receipt = _valid_packet_generation_receipt()
    receipt[field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
        manifest_bodyfull_packet_request_boundary=_op04_ready(),
        packet_generation_receipt_optional=receipt,
    )

    assert material["packet_generation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op05_blocker_refs"]
    assert material["ready_for_packet_completeness_export_scan"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(material) is True


def test_elr_op05_forbidden_payload_in_packet_generation_receipt_is_repair_without_body_value() -> None:
    receipt = _valid_packet_generation_receipt()
    receipt["raw_input"] = "body-full packet content must never leak"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
        manifest_bodyfull_packet_request_boundary=_op04_ready(),
        packet_generation_receipt_optional=receipt,
    )

    assert material["packet_generation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert material["packet_generation_receipt_forbidden_payload_key_paths"] == ["packet_generation_receipt.raw_input"]
    assert "must never leak" not in repr(material)
    assert "elr_op05_packet_generation_receipt_forbidden_payload_key_detected" in material["elr_op05_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(material) is True


def test_elr_op05_invalid_op04_goes_to_repair() -> None:
    op04 = _op04_ready()
    op04["release_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
        manifest_bodyfull_packet_request_boundary=op04,
        packet_generation_receipt_optional=_valid_packet_generation_receipt(),
    )

    assert material["packet_generation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert "elr_op05_op04_manifest_boundary_contract_invalid_or_missing" in material["elr_op05_blocker_refs"]
    assert material["ready_for_packet_completeness_export_scan"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("packet_generation_receipt_accepted", False),
        ("ready_for_packet_completeness_export_scan", False),
        ("generated_local_only", False),
        ("packet_body_included", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_generation_allowed_here", True),
        ("actual_review_execution_allowed_here", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op05_contract_rejects_generation_claim_body_leak_or_downstream_promotion_mutations(field: str, bad_value: object) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
        manifest_bodyfull_packet_request_boundary=_op04_ready(),
        packet_generation_receipt_optional=_valid_packet_generation_receipt(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(material)


def test_elr_op04_op05_alias_builders_and_contracts_match_canonical_functions() -> None:
    op04 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op04_24_case_manifest_bodyfull_packet_request_boundary(
        local_only_review_session_envelope_role_boundary=_op03_ready(),
        case_refs=_case_refs(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op04_24_case_manifest_bodyfull_packet_request_boundary_contract(op04) is True

    op05 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary(
        manifest_bodyfull_packet_request_boundary=op04,
        packet_generation_receipt_optional=_valid_packet_generation_receipt(packet_request_ref=op04["packet_request_ref"]),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op05_bodyfull_packet_generation_local_receipt_intake_boundary_contract(op05) is True


def test_elr_op04_op05_result_memo_is_bodyfree_and_limited_to_current_scope() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP05_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    for heading in (
        "## 1. Implementation scope",
        "## 2. Changed files",
        "## 3. Prior implementation confirmation",
        "## 4. ELR-OP04",
        "## 5. ELR-OP05",
        "## 6. Test results",
        "## 7. Not claimed",
        "## 8. Next required step",
    ):
        assert heading in text
    assert "ELR-OP06" in text
    assert "actual_local_human_review_execution: false" in text
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
