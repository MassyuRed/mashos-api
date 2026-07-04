# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP14/OP15 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op06_op07_20260703 import (  # noqa: E501
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op12_op13_20260703 import (  # noqa: E501
    _op11_normalized,
    _op12_normalized,
)

_OP13_PASSED_CACHE: dict[str, object] | None = None
_OP14_ACCEPTED_CACHE: dict[str, object] | None = None
_OP15_PASSED_CACHE: dict[str, object] | None = None


def _op13_passed() -> dict[str, object]:
    global _OP13_PASSED_CACHE
    if _OP13_PASSED_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation(
            op11_rating_rows_normalization=_op11_normalized(),
            op12_question_need_observation_rows_normalization=_op12_normalized(),
        )
        assert material["rating_question_consistency_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STATUS_PASSED_REF
        assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STEP_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation_contract(material) is True
        _OP13_PASSED_CACHE = material
    return deepcopy(_OP13_PASSED_CACHE)


def _valid_disposal_purge_receipt(op13: dict[str, object] | None = None) -> dict[str, object]:
    op13 = op13 or _op13_passed()
    receipt: dict[str, object] = {
        "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION,
        "disposal_purge_receipt_ref": "elr_op14_disposal_purge_receipt_bodyfree_ref_20260704_v1",
        "review_session_id": str(op13["review_session_id"]),
        "source_kind_ref": elr.P7_R54_AHR_POST_ALR12_ELR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "operation_receipt_ref": "elr_op09_actual_operation_receipt_bodyfree_ref_20260704_v1",
        "packet_request_ref": "elr_op04_bodyfull_packet_request_bodyfree_ref_20260704_v1",
        "purge_scope_ref": "disposal_purge_for_local_only_24_case_review_materials_bodyfree_ref",
        "disposal_purge_executed_by_person": True,
        "local_only_operation_confirmed": True,
        "selection_only_materials_preserved_bodyfree": True,
        "disposal_purge_receipt_accepted": True,
        "body_free": True,
    }
    for field in elr.P7_R54_AHR_POST_ALR12_ELR_OP14_DISPOSAL_RETENTION_FALSE_FIELD_REFS:
        receipt[field] = False
    assert set(elr.P7_R54_AHR_POST_ALR12_ELR_OP14_REQUIRED_DISPOSAL_PURGE_RECEIPT_FIELD_REFS).issubset(receipt)
    return receipt


def _op14_accepted() -> dict[str, object]:
    global _OP14_ACCEPTED_CACHE
    if _OP14_ACCEPTED_CACHE is None:
        op13 = _op13_passed()
        material = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
            op13_rating_question_consistency_blocker_separation=op13,
            disposal_purge_receipt_optional=_valid_disposal_purge_receipt(op13),
        )
        assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_ACCEPTED_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True
        _OP14_ACCEPTED_CACHE = material
    return deepcopy(_OP14_ACCEPTED_CACHE)


def _op15_passed() -> dict[str, object]:
    global _OP15_PASSED_CACHE
    if _OP15_PASSED_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation(
            op14_disposal_purge_receipt_intake=_op14_accepted(),
        )
        assert material["final_validation_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STATUS_PASSED_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation_contract(material) is True
        _OP15_PASSED_CACHE = material
    return deepcopy(_OP15_PASSED_CACHE)


def test_elr_op14_missing_disposal_purge_receipt_waits_after_op13_without_evidence_complete() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=_op13_passed(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP14_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_SCHEMA_VERSION
    assert material["op13_ready_for_disposal_purge_receipt_intake"] is True
    assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_MISSING_WAITING_REF
    assert material["disposal_purge_receipt_missing_waiting"] is True
    assert material["disposal_purge_receipt_accepted"] is False
    assert material["ready_for_final_no_leak_no_touch_validation"] is False
    assert material["actual_disposal_purge_executed_here_by_helper"] is False
    assert material["actual_disposal_purge_receipt_created_here_by_helper"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_CREATE_DISPOSAL_PURGE_RECEIPT_REF
    assert "elr_op14_waiting_for_disposal_purge_receipt" in material["elr_op14_reason_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op14_accepts_bodyfree_disposal_purge_receipt_without_executing_purge_here() -> None:
    material = _op14_accepted()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP14_REQUIRED_FIELD_REFS)
    assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_ACCEPTED_BODYFREE_REF
    assert material["disposal_purge_receipt_accepted"] is True
    assert material["ready_for_final_no_leak_no_touch_validation"] is True
    assert material["disposal_purge_executed_by_person"] is True
    assert material["local_only_operation_confirmed"] is True
    assert material["selection_only_materials_preserved_bodyfree"] is True
    assert material["disposal_purge_execution_confirmed_by_external_receipt"] is True
    assert material["disposal_purge_receipt_bodyfree_only"] is True
    assert material["disposal_purge_receipt_has_no_body_path_hash_terminal"] is True
    for field in elr.P7_R54_AHR_POST_ALR12_ELR_OP14_DISPOSAL_RETENTION_FALSE_FIELD_REFS:
        assert material[field] is False, field
    assert material["disposal_purge_receipt_forbidden_payload_key_paths"] == []
    assert material["disposal_purge_receipt_promotion_claim_refs"] == []
    assert material["actual_disposal_purge_executed_here_by_helper"] is False
    assert material["actual_disposal_purge_receipt_created_here_by_helper"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["elr_op14_does_not_execute_purge_itself"] is True
    assert material["elr_op14_does_not_complete_actual_review_evidence"] is True
    assert material["elr_op14_does_not_start_p5_p6_p8_r52_p7_or_release"] is True
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STEP_REF
    assert material["elr_op14_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("schema_version", "bad.schema", "elr_op14_disposal_purge_receipt_schema_version_mismatch"),
        ("review_session_id", "wrong_session", "elr_op14_disposal_purge_receipt_review_session_id_mismatch"),
        ("source_kind_ref", "synthetic_fixture", "elr_op14_disposal_purge_source_kind_not_actual_local_only_human_review_by_person"),
        ("disposal_purge_executed_by_person", False, "elr_op14_disposal_purge_executed_by_person_not_true"),
        ("local_only_operation_confirmed", False, "elr_op14_local_only_operation_confirmed_not_true"),
        ("selection_only_materials_preserved_bodyfree", False, "elr_op14_selection_only_materials_preserved_bodyfree_not_true"),
        ("disposal_purge_receipt_accepted", False, "elr_op14_disposal_purge_receipt_accepted_not_true"),
        ("body_full_packet_retained", True, "elr_op14_body_full_packet_retained_not_false"),
        ("question_text_retained", True, "elr_op14_question_text_retained_not_false"),
        ("local_path_included", True, "elr_op14_local_path_included_not_false"),
        ("terminal_output_body_included", True, "elr_op14_terminal_output_body_included_not_false"),
        ("body_free", False, "elr_op14_body_free_not_true"),
    ],
)
def test_elr_op14_rejects_invalid_disposal_purge_receipt_fields(field: str, bad_value: object, expected_blocker: str) -> None:
    op13 = _op13_passed()
    receipt = _valid_disposal_purge_receipt(op13)
    receipt[field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=op13,
        disposal_purge_receipt_optional=receipt,
    )

    assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op14_blocker_refs"]
    assert material["disposal_purge_receipt_accepted"] is False
    assert material["ready_for_final_no_leak_no_touch_validation"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_DISPOSAL_PURGE_RECEIPT_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True


def test_elr_op14_rejects_required_receipt_field_missing() -> None:
    op13 = _op13_passed()
    receipt = _valid_disposal_purge_receipt(op13)
    del receipt["operation_receipt_ref"]
    material = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=op13,
        disposal_purge_receipt_optional=receipt,
    )

    assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op14_disposal_purge_receipt_required_field_missing" in material["elr_op14_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("disposal_purge_receipt_ref", "/tmp/bodyfull/receipt.json", "elr_op14_disposal_purge_receipt_ref_has_local_path_shape"),
        ("operation_receipt_ref", "これは質問本文ですか", "elr_op14_operation_receipt_ref_has_question_or_body_text_shape"),
        ("packet_request_ref", "raw input text should never be here", "elr_op14_packet_request_ref_has_question_or_body_text_shape"),
    ],
)
def test_elr_op14_rejects_unsafe_refs_without_leaking_body_value(field: str, bad_value: object, expected_blocker: str) -> None:
    op13 = _op13_passed()
    receipt = _valid_disposal_purge_receipt(op13)
    receipt[field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=op13,
        disposal_purge_receipt_optional=receipt,
    )

    assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op14_blocker_refs"]
    assert str(bad_value) not in repr(material)
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True


def test_elr_op14_rejects_forbidden_payload_key_without_leaking_body_value() -> None:
    op13 = _op13_passed()
    receipt = _valid_disposal_purge_receipt(op13)
    receipt["question_text"] = "body-full question text must not leak"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=op13,
        disposal_purge_receipt_optional=receipt,
    )

    assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert material["disposal_purge_receipt_forbidden_payload_key_paths"] == ["disposal_purge_receipt.question_text"]
    assert "body-full question text must not leak" not in repr(material)
    assert "elr_op14_disposal_purge_receipt_forbidden_payload_key_detected" in material["elr_op14_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True


def test_elr_op14_repairs_when_op13_rating_question_consistency_is_not_passed() -> None:
    op13 = _op13_passed()
    op13["rating_question_consistency_passed"] = False
    material = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=op13,
        disposal_purge_receipt_optional=_valid_disposal_purge_receipt(_op13_passed()),
    )

    assert material["disposal_purge_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op14_op13_rating_question_consistency_contract_invalid_or_missing" in material["elr_op14_blocker_refs"]
    assert material["op13_ready_for_disposal_purge_receipt_intake"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_RATING_QUESTION_CONSISTENCY_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("disposal_purge_receipt_accepted", False),
        ("ready_for_final_no_leak_no_touch_validation", False),
        ("disposal_purge_executed_by_person", False),
        ("disposal_purge_receipt_has_no_body_path_hash_terminal", False),
        ("body_full_packet_retained", True),
        ("actual_disposal_purge_executed_here_by_helper", True),
        ("actual_disposal_purge_receipt_created_here_by_helper", True),
        ("actual_review_evidence_complete_here", True),
        ("next_required_step", elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STEP_REF),
    ],
)
def test_elr_op14_contract_rejects_accepted_mutations(field: str, bad_value: object) -> None:
    material = _op14_accepted()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake_contract(material)


def test_elr_op15_passes_final_no_leak_no_touch_validation_without_completing_evidence() -> None:
    material = _op15_passed()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP15_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_SCHEMA_VERSION
    assert material["final_validation_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STATUS_PASSED_REF
    assert material["final_no_leak_no_touch_validation_passed"] is True
    assert material["ready_for_actual_review_evidence_complete_predicate"] is True
    assert material["forbidden_payload_key_path_count"] == 0
    assert material["promotion_claim_ref_count"] == 0
    assert material["body_free_marker_violation_ref_count"] == 0
    assert material["no_touch_violation_ref_count"] == 0
    assert material["body_like_value_path_ref_count"] == 0
    assert material["no_body_no_question_no_path_no_hash_no_terminal_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["p8_r52_p5_p6_p7_release_promotion_absent"] is True
    assert material["actual_review_evidence_complete_here"] is False
    assert material["dmd_compatible_receipt_adapter_allowed_here"] is False
    assert material["actual_review_evidence_complete_predicate_allowed_next"] is True
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STEP_REF
    assert material["elr_op15_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op15_repairs_forbidden_payload_key_without_leaking_body_value() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation(
        op14_disposal_purge_receipt_intake=_op14_accepted(),
        bodyfree_artifacts_optional=[{"material_id": "bad_artifact", "question_text": "must not leak"}],
    )

    assert material["final_validation_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STATUS_REPAIR_REQUIRED_REF
    assert material["forbidden_payload_key_paths"] == ["bad_artifact.question_text"]
    assert material["body_like_value_path_refs"] == ["bad_artifact.question_text"]
    assert "must not leak" not in repr(material)
    assert "elr_op15_forbidden_payload_key_detected" in material["elr_op15_blocker_refs"]
    assert "elr_op15_body_like_value_path_detected" in material["elr_op15_blocker_refs"]
    assert material["ready_for_actual_review_evidence_complete_predicate"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_FINAL_NO_LEAK_VALIDATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation_contract(material) is True


@pytest.mark.parametrize(
    ("artifact", "expected_blocker", "expected_nonzero_field"),
    [
        ({"material_id": "body_marker_bad", "body_free_markers": {"local_path_included": True}}, "elr_op15_body_free_marker_violation_detected", "body_free_marker_violation_ref_count"),
        ({"material_id": "no_touch_bad", "post_alr12_no_touch_contract": {"api_route_changed": True}}, "elr_op15_no_touch_violation_detected", "no_touch_violation_ref_count"),
        ({"material_id": "promotion_bad", "release_allowed": True}, "elr_op15_promotion_claim_detected", "promotion_claim_ref_count"),
        ({"material_id": "terminal_bad", "terminal_output_body": "do not leak"}, "elr_op15_forbidden_payload_key_detected", "forbidden_payload_key_path_count"),
        ({"material_id": "path_bad", "safe_ref": "/tmp/local/file.txt"}, "elr_op15_body_like_value_path_detected", "body_like_value_path_ref_count"),
    ],
)
def test_elr_op15_repairs_body_marker_no_touch_promotion_terminal_or_path_violations(
    artifact: dict[str, object], expected_blocker: str, expected_nonzero_field: str
) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation(
        op14_disposal_purge_receipt_intake=_op14_accepted(),
        bodyfree_artifacts_optional=[artifact],
    )

    assert material["final_validation_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STATUS_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op15_blocker_refs"]
    assert material[expected_nonzero_field] > 0
    assert material["ready_for_actual_review_evidence_complete_predicate"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation_contract(material) is True


def test_elr_op15_repairs_when_op14_receipt_is_missing_or_invalid() -> None:
    op14_missing = elr.build_p7_r54_ahr_post_alr12_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=_op13_passed(),
    )
    material = elr.build_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation(
        op14_disposal_purge_receipt_intake=op14_missing,
    )

    assert material["final_validation_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op15_op14_disposal_purge_receipt_not_accepted" in material["elr_op15_blocker_refs"]
    assert material["op14_disposal_purge_receipt_accepted"] is False
    assert material["ready_for_actual_review_evidence_complete_predicate"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_CREATE_DISPOSAL_PURGE_RECEIPT_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("final_no_leak_no_touch_validation_passed", False),
        ("ready_for_actual_review_evidence_complete_predicate", False),
        ("forbidden_payload_key_path_count", 1),
        ("body_free_marker_violation_ref_count", 1),
        ("no_touch_violation_ref_count", 1),
        ("promotion_claim_ref_count", 1),
        ("body_like_value_path_ref_count", 1),
        ("actual_review_evidence_complete_here", True),
        ("dmd_compatible_receipt_adapter_allowed_here", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_elr_op15_contract_rejects_passed_mutations(field: str, bad_value: object) -> None:
    material = _op15_passed()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation_contract(material)


def test_elr_op14_op15_full_operation_aliases_match_canonical_functions() -> None:
    op13 = _op13_passed()
    op14 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op14_disposal_purge_receipt_intake(
        op13_rating_question_consistency_blocker_separation=op13,
        disposal_purge_receipt_optional=_valid_disposal_purge_receipt(op13),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op14_disposal_purge_receipt_intake_contract(op14) is True
    op15 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation(
        op14_disposal_purge_receipt_intake=op14,
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op15_final_no_body_no_question_no_path_no_hash_no_terminal_no_touch_validation_contract(op15) is True
    assert op15["final_validation_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STATUS_PASSED_REF


def test_elr_op14_op15_result_memo_is_bodyfree_and_current_scope_only() -> None:
    memo_path = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP15_Result_20260704.md"
    text = memo_path.read_text(encoding="utf-8")

    assert "ELR-OP14" in text
    assert "ELR-OP15" in text
    assert "actual local-only human review execution: not performed" in text
    assert "actual disposal / purge execution by helper: false" in text
    assert "actual_review_evidence_complete: false" in text
    assert "release_allowed: false" in text
    assert "ELR-OP16: actual_review_evidence_complete predicate" in text
    assert "raw_input:" not in text
    assert "comment_text:" not in text
    assert "question_text:" not in text
    assert "local_path:" not in text
    assert "body_hash:" not in text
    assert "terminal_output:" not in text
