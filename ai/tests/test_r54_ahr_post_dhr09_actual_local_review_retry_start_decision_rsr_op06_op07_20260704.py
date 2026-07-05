# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP06/OP07 packet request/receipt-boundary tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_op03_20260704 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op04_op05_20260704 import (
    _rsr_op04_ready,
)


def _case_refs() -> list[str]:
    return [f"case_ref_{index:02d}_bodyfree" for index in range(1, 25)]


def _rsr_op05_ready() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=_rsr_op04_ready(),
        reviewer_person_ref="reviewer_person_bodyfree_ref_001",
        reviewer_is_person_confirmed=True,
        reviewer_role_ref=rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF,
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(material) is True
    assert material["rsr_op05_ready_for_body_full_packet_transient_request_boundary"] is True
    return material


def _rsr_op06_ready() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary(
        local_only_review_session_envelope=_rsr_op05_ready(),
        case_ref_values=_case_refs(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(material) is True
    assert material["rsr_op06_ready_for_body_full_packet_generation_receipt_intake"] is True
    return material


def _valid_packet_generation_receipt(op06: dict[str, object] | None = None) -> dict[str, object]:
    op06 = op06 or _rsr_op06_ready()
    return {
        "schema_version": rsr.P7_R54_AHR_POST_DHR09_RSR_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION,
        "packet_generation_receipt_ref": "packet_generation_receipt_bodyfree_ref_001",
        "packet_request_ref": op06["packet_request_ref"],
        "review_session_id": op06["review_session_id"],
        "generated_case_count": 24,
        "generated_local_only": True,
        "persisted_to_repo": False,
        "external_export_performed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def _assert_op06_no_actual_operation(material: dict[str, object]) -> None:
    assert material["rsr_op06_does_not_generate_body_full_packet"] is True
    assert material["rsr_op06_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op06_does_not_create_receipts_rows_or_disposal"] is True
    assert material["packet_generated_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["external_export_allowed"] is False
    assert material["persisted_to_repo_allowed"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_generation_run_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False


def _assert_op07_no_actual_operation(material: dict[str, object]) -> None:
    assert material["rsr_op07_does_not_generate_body_full_packet_here"] is True
    assert material["rsr_op07_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op07_does_not_create_actual_operation_receipt_rows_or_disposal"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_generation_run_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False


def test_rsr_op06_waits_when_review_session_envelope_is_not_ready() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary()

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF
    assert material["op05_contract_valid"] is True
    assert material["op05_ready_for_body_full_packet_transient_request_boundary"] is False
    assert material["rsr_op06_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_WAITING_FOR_SESSION_ENVELOPE_REF
    assert material["rsr_op06_waiting_for_session_envelope"] is True
    assert material["packet_request_created_here"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_REVIEW_SESSION_ENVELOPE_BEFORE_PACKET_REQUEST_REF
    _assert_op06_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op06_accepts_24_case_bodyfree_request_without_generating_packet() -> None:
    material = _rsr_op06_ready()

    assert material["rsr_op06_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_ACCEPTED_BODYFREE_REF
    assert material["expected_case_count"] == 24
    assert material["case_ref_count"] == 24
    assert material["case_ref_unique_count"] == 24
    assert material["case_ref_duplicate_refs"] == []
    assert material["case_ref_invalid_refs"] == []
    assert material["case_ref_manifest_bodyfree"] is True
    assert material["case_ref_manifest_exactly_24_unique"] is True
    assert material["packet_request_ref_bodyfree"] is True
    assert material["packet_request_created_here"] is True
    assert material["transient_body_full_packet_required"] is True
    assert material["local_only_transient_boundary_confirmed"] is True
    assert material["rsr_op06_ready_for_body_full_packet_generation_receipt_intake"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF
    _assert_op06_no_actual_operation(material)
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("case_refs", "expected_blocker"),
    [
        (_case_refs()[:23], "case_ref_count_not_24"),
        (_case_refs() + ["case_ref_25_bodyfree"], "case_ref_count_not_24"),
        (_case_refs()[:-1] + [_case_refs()[0]], "case_ref_duplicates_detected"),
    ],
)
def test_rsr_op06_repairs_count_and_duplicate_case_ref_boundaries(case_refs: list[str], expected_blocker: str) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary(
        local_only_review_session_envelope=_rsr_op05_ready(),
        case_ref_values=case_refs,
    )

    assert material["rsr_op06_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_CASE_MANIFEST_REPAIR_REQUIRED_REF
    assert expected_blocker in material["packet_request_blocker_refs"]
    assert material["rsr_op06_case_manifest_repair_required"] is True
    assert material["packet_request_created_here"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_24_CASE_BODYFREE_CASE_REF_MANIFEST_BEFORE_PACKET_REQUEST_REF
    _assert_op06_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    "bad_case_ref",
    [
        "raw input body should never be a case ref",
        "/mnt/private/local/body_full_packet.json",
        "case_ref_with_sha256_hash",
        "reviewer@example.com",
    ],
)
def test_rsr_op06_repairs_body_like_case_ref_shape_without_leaking_value(bad_case_ref: str) -> None:
    case_refs = _case_refs()
    case_refs[5] = bad_case_ref
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary(
        local_only_review_session_envelope=_rsr_op05_ready(),
        case_ref_values=case_refs,
    )

    assert material["rsr_op06_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_CASE_MANIFEST_REPAIR_REQUIRED_REF
    assert "case_ref_invalid_shape_detected" in material["packet_request_blocker_refs"]
    assert material["case_ref_invalid_ref_count"] > 0
    assert bad_case_ref not in repr(material)
    _assert_op06_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op06_blocks_forbidden_packet_request_material_without_leaking_value() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary(
        local_only_review_session_envelope=_rsr_op05_ready(),
        case_ref_values=_case_refs(),
        packet_request_material={"raw_input": "body full input must not leak", "body_free": True},
    )

    assert material["rsr_op06_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_BODY_LEAK_BLOCKED_REF
    assert material["packet_request_forbidden_payload_key_path_count"] > 0
    assert material["packet_request_body_like_value_path_count"] > 0
    assert "packet_request_forbidden_payload_key_detected" in material["packet_request_blocker_refs"]
    assert "body full input must not leak" not in repr(material)
    _assert_op06_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("packet_request_created_here", False),
        ("packet_generated_here", True),
        ("body_full_packet_content_included", True),
        ("rsr_op06_does_not_generate_body_full_packet", False),
        ("body_full_packet_generated_here", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_operation_receipt_created_here", True),
        ("dmd_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF),
    ],
)
def test_rsr_op06_contract_rejects_packet_generation_review_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _rsr_op06_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(material)


def test_rsr_op07_waits_when_op06_packet_request_boundary_is_not_ready() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=rsr.build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary()
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF
    assert material["op06_contract_valid"] is True
    assert material["op06_ready_for_body_full_packet_generation_receipt_intake"] is False
    assert material["packet_generation_receipt_present"] is False
    assert material["rsr_op07_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_REQUEST_BOUNDARY_BEFORE_RECEIPT_REF
    _assert_op07_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op07_waits_for_bodyfree_generation_receipt_after_packet_request_ready() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=_rsr_op06_ready()
    )

    assert material["rsr_op07_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF
    assert material["packet_generation_receipt_present"] is False
    assert material["packet_generation_receipt_contract_valid"] is False
    assert material["packet_generation_receipt_accepted_by_rsr_op07"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_GENERATION_RECEIPT_REF
    _assert_op07_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op07_accepts_bodyfree_packet_generation_receipt_without_executing_review() -> None:
    op06 = _rsr_op06_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06,
        body_full_packet_generation_receipt=_valid_packet_generation_receipt(op06),
    )

    assert material["rsr_op07_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_ACCEPTED_BODYFREE_REF
    assert material["packet_generation_receipt_present"] is True
    assert material["packet_generation_receipt_contract_valid"] is True
    assert material["packet_generation_receipt_generated_case_count"] == 24
    assert material["packet_generation_receipt_generated_local_only"] is True
    assert material["packet_generation_receipt_persisted_to_repo"] is False
    assert material["packet_generation_receipt_external_export_performed"] is False
    assert material["packet_generation_receipt_blocker_refs"] == []
    assert material["packet_generation_receipt_export_or_persistence_blocker_refs"] == []
    assert material["packet_generation_receipt_accepted_by_rsr_op07"] is True
    assert material["packet_generation_receipt_accepted_but_actual_review_not_executed"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF
    _assert_op07_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("schema_version", "bad.schema", "packet_generation_receipt_schema_invalid"),
        ("packet_request_ref", "other_packet_request_ref", "packet_generation_receipt_packet_request_ref_mismatch"),
        ("review_session_id", "other_review_session_id", "packet_generation_receipt_review_session_mismatch"),
        ("generated_case_count", 23, "packet_generation_receipt_generated_case_count_not_24"),
        ("generated_local_only", False, "packet_generation_receipt_generated_local_only_not_true"),
        ("body_free", False, "packet_generation_receipt_body_free_not_true"),
        ("raw_input_included", True, "packet_generation_receipt_raw_input_included_must_be_false"),
        ("local_path_included", True, "packet_generation_receipt_local_path_included_must_be_false"),
    ],
)
def test_rsr_op07_repairs_invalid_packet_generation_receipt_contract(field: str, bad_value: object, expected_blocker: str) -> None:
    op06 = _rsr_op06_ready()
    receipt = _valid_packet_generation_receipt(op06)
    receipt[field] = bad_value
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06,
        body_full_packet_generation_receipt=receipt,
    )

    assert material["rsr_op07_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert expected_blocker in material["packet_generation_receipt_blocker_refs"]
    assert material["packet_generation_receipt_accepted_by_rsr_op07"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_BODY_FULL_PACKET_GENERATION_RECEIPT_REF
    _assert_op07_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "expected_blocker"),
    [
        ("persisted_to_repo", "packet_generation_receipt_persisted_to_repo_not_false"),
        ("external_export_performed", "packet_generation_receipt_external_export_performed_not_false"),
    ],
)
def test_rsr_op07_blocks_export_or_repo_persistence_receipt_flags(field: str, expected_blocker: str) -> None:
    op06 = _rsr_op06_ready()
    receipt = _valid_packet_generation_receipt(op06)
    receipt[field] = True
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06,
        body_full_packet_generation_receipt=receipt,
    )

    assert material["rsr_op07_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_EXPORT_OR_PERSISTENCE_BLOCKED_REF
    assert expected_blocker in material["packet_generation_receipt_export_or_persistence_blocker_refs"]
    assert material["packet_generation_receipt_accepted_by_rsr_op07"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_PACKET_EXPORT_OR_REPO_PERSISTENCE_REF
    _assert_op07_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op07_repairs_receipt_with_raw_path_or_terminal_payload_without_leaking_value() -> None:
    op06 = _rsr_op06_ready()
    receipt = _valid_packet_generation_receipt(op06)
    receipt.update({
        "raw_input": "body-full packet content must not leak",
        "local_path": "/mnt/private/body_full_packet.json",
        "terminal_output": "stdout body must not leak",
    })
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06,
        body_full_packet_generation_receipt=receipt,
    )

    assert material["rsr_op07_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert material["packet_generation_receipt_forbidden_payload_key_path_count"] >= 3
    assert material["packet_generation_receipt_body_like_value_path_count"] >= 3
    assert "packet_generation_receipt_forbidden_payload_key_detected" in material["packet_generation_receipt_blocker_refs"]
    assert "body-full packet content must not leak" not in repr(material)
    assert "/mnt/private/body_full_packet.json" not in repr(material)
    assert "stdout body must not leak" not in repr(material)
    _assert_op07_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rsr_op07_does_not_generate_body_full_packet_here", False),
        ("rsr_op07_does_not_run_actual_local_human_review", False),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_generation_run_here", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_operation_receipt_created_here", True),
        ("actual_rows_created_here", True),
        ("dmd_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF),
    ],
)
def test_rsr_op07_contract_rejects_generation_review_or_promotion_mutations(field: str, bad_value: object) -> None:
    op06 = _rsr_op06_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06,
        body_full_packet_generation_receipt=_valid_packet_generation_receipt(op06),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material)


def test_rsr_op06_op07_full_title_aliases_match_canonical_builders() -> None:
    op06_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op06_24_case_body_full_packet_transient_request_boundary(
        local_only_review_session_envelope=_rsr_op05_ready(),
        case_ref_values=_case_refs(),
    )
    op06_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary(
        local_only_review_session_envelope=_rsr_op05_ready(),
        case_ref_values=_case_refs(),
    )
    assert op06_alias == op06_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(op06_alias) is True

    op07_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06_canonical,
        body_full_packet_generation_receipt=_valid_packet_generation_receipt(op06_canonical),
    )
    op07_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06_canonical,
        body_full_packet_generation_receipt=_valid_packet_generation_receipt(op06_canonical),
    )
    assert op07_alias == op07_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(op07_alias) is True
