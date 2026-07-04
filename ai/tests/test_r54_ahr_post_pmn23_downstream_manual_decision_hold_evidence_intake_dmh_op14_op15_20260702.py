# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP14/OP15 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op12_op13_20260702 as dmh_op12_op13_prev

_READY_OP13_CACHE: dict[str, object] | None = None
_READY_RECEIPT_CACHE: dict[str, object] | None = None
_READY_OP14_CACHE: dict[str, object] | None = None
_READY_OP15_CACHE: dict[str, object] | None = None


def _ready_op13() -> dict[str, object]:
    global _READY_OP13_CACHE
    if _READY_OP13_CACHE is None:
        material = dmh_op12_op13_prev._ready_op13()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material) is True
        _READY_OP13_CACHE = material
    return deepcopy(_READY_OP13_CACHE)


def _ready_receipt() -> dict[str, object]:
    global _READY_RECEIPT_CACHE
    if _READY_RECEIPT_CACHE is None:
        op13 = _ready_op13()
        receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_bodyfree(
            review_session_id=op13["review_session_id"],
            operation_receipt_ref=op13["operation_receipt_ref"],
        )
        _READY_RECEIPT_CACHE = receipt
    return deepcopy(_READY_RECEIPT_CACHE)


def _ready_op14() -> dict[str, object]:
    global _READY_OP14_CACHE
    if _READY_OP14_CACHE is None:
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
            rating_question_consistency_blocker_separation=_ready_op13(),
            disposal_receipt_bodyfree=_ready_receipt(),
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True
        _READY_OP14_CACHE = material
    return deepcopy(_READY_OP14_CACHE)


def _ready_op15(*, artifacts: list[dict[str, object]] | None = None) -> dict[str, object]:
    global _READY_OP15_CACHE
    if artifacts is None and _READY_OP15_CACHE is not None:
        return deepcopy(_READY_OP15_CACHE)
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation(
        disposal_purge_receipt_intake=_ready_op14(),
        bodyfree_artifacts=artifacts if artifacts is not None else [_ready_op13()],
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True
    if artifacts is None:
        _READY_OP15_CACHE = material
    return deepcopy(material)


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_pmn23_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def test_dmh_op14_receipt_builder_returns_bodyfree_disposal_receipt_without_path_hash_question_or_body() -> None:
    receipt = _ready_receipt()

    assert set(receipt) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS)
    assert receipt["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert receipt["disposal_receipt_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_DEFAULT_DISPOSAL_RECEIPT_REF
    assert receipt["review_session_id"] == _ready_op13()["review_session_id"]
    assert receipt["operation_receipt_ref"] == _ready_op13()["operation_receipt_ref"]
    assert receipt["disposal_status_ref"] == "BODY_PURGED"
    assert receipt["body_removed"] is True
    assert receipt["reviewer_notes_removed"] is True
    assert receipt["temporary_form_removed"] is True
    assert receipt["content_hash_of_body_stored"] is False
    assert receipt["body_hash_stored"] is False
    assert receipt["local_absolute_path_included"] is False
    assert receipt["reviewer_notes_body_stored"] is False
    assert receipt["question_text_included"] is False
    assert receipt["draft_question_text_included"] is False
    assert receipt["terminal_output_body_included"] is False
    assert receipt["actual_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_ACTUAL_SOURCE_REF
    assert receipt["body_free"] is True


def test_dmh_op14_intakes_bodyfree_disposal_receipt_and_allows_final_validation_only() -> None:
    material = _ready_op14()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF
    assert material["dmh_op14_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_READY_STATUS_REF
    assert material["dmh_op14_ready"] is True
    assert material["disposal_purge_receipt_accepted"] is True
    assert tuple(material["dmh_op14_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_READY_REASON_REFS
    assert material["op13_dmh_ready"] is True
    assert material["op13_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF
    assert material["op13_rating_question_consistency_guard_passed"] is True
    assert material["op13_disposal_purge_receipt_intake_allowed_next"] is True
    assert material["operation_receipt_ref_matches_op13"] is True
    assert material["disposal_status_is_body_purged_or_aborted_body_purged"] is True
    assert material["body_full_packet_lifecycle_closed_bodyfree"] is True
    assert material["body_removed_without_hash_path_question_or_reviewer_notes"] is True
    assert material["temporary_form_removed_without_export"] is True
    assert material["disposal_receipt_does_not_store_body_hash_or_local_path"] is True
    assert material["disposal_receipt_does_not_create_question_text"] is True
    assert material["disposal_receipt_does_not_store_terminal_output_body"] is True
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["disposal_receipt_ready_for_final_no_leak_validation_only"] is True
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op14_alias_builder_matches_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_disposal_purge_receipt_intake_bodyfree(
        rating_question_consistency_blocker_separation=_ready_op13(),
        disposal_receipt_bodyfree=_ready_receipt(),
    )

    assert material["dmh_op14_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_disposal_purge_receipt_intake_bodyfree_contract(material) is True


def test_dmh_op14_accepts_aborted_body_purged_status_as_bodyfree_closed_lifecycle() -> None:
    op13 = _ready_op13()
    receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_bodyfree(
        review_session_id=op13["review_session_id"],
        operation_receipt_ref=op13["operation_receipt_ref"],
        disposal_status_ref="ABORTED_BODY_PURGED",
        pause_abort_status_ref="DMH_ABORTED_BODY_PURGED",
    )
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
        rating_question_consistency_blocker_separation=op13,
        disposal_receipt_bodyfree=receipt,
    )

    assert material["dmh_op14_ready"] is True
    assert material["disposal_status_ref"] == "ABORTED_BODY_PURGED"
    assert material["pause_abort_status_ref"] == "DMH_ABORTED_BODY_PURGED"
    assert material["disposal_status_is_body_purged_or_aborted_body_purged"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True


def test_dmh_op14_blocks_without_op13_and_keeps_final_validation_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
        disposal_receipt_bodyfree=_ready_receipt(),
    )

    assert material["dmh_op14_ready"] is False
    assert material["dmh_op14_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_STATUS_REF
    assert "dmh_op14_op13_consistency_guard_not_passed" in material["dmh_op14_blocker_refs"]
    assert "dmh_op14_op13_disposal_intake_not_allowed_next" in material["dmh_op14_blocker_refs"]
    assert material["disposal_receipt_ready_for_final_no_leak_validation_only"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op14_blocks_without_disposal_receipt() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
        rating_question_consistency_blocker_separation=_ready_op13(),
    )

    assert material["dmh_op14_ready"] is False
    assert "dmh_op14_disposal_receipt_missing" in material["dmh_op14_blocker_refs"]
    assert material["disposal_purge_receipt_accepted"] is False
    assert material["disposal_receipt_received_here"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("schema_version", "wrong.schema", "dmh_op14_disposal_receipt_schema_version_mismatch"),
        ("review_session_id", "other_session", "dmh_op14_review_session_id_mismatch"),
        ("operation_receipt_ref", "other_operation_receipt", "dmh_op14_operation_receipt_ref_mismatch"),
        ("disposal_status_ref", "DISPOSAL_FAILED", "dmh_op14_disposal_status_not_allowed_body_purged_or_aborted_body_purged"),
        ("body_removed", False, "dmh_op14_body_removed_not_true"),
        ("reviewer_notes_removed", False, "dmh_op14_reviewer_notes_removed_not_true"),
        ("temporary_form_removed", False, "dmh_op14_temporary_form_removed_not_true"),
        ("actual_source_ref", "helper_fixture_disposal_receipt", "dmh_op14_actual_source_ref_not_allowed"),
        ("body_free", False, "dmh_op14_body_free_not_true"),
    ],
)
def test_dmh_op14_blocks_receipt_contract_mismatches(field: str, bad_value: object, expected_blocker: str) -> None:
    receipt = _ready_receipt()
    receipt[field] = bad_value
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
        rating_question_consistency_blocker_separation=_ready_op13(),
        disposal_receipt_bodyfree=receipt,
    )

    assert material["dmh_op14_ready"] is False
    assert expected_blocker in material["dmh_op14_blocker_refs"]
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("content_hash_of_body_stored", True, "dmh_op14_content_hash_of_body_stored_not_false"),
        ("body_hash_stored", True, "dmh_op14_body_hash_stored_not_false"),
        ("local_absolute_path_included", True, "dmh_op14_local_absolute_path_included_not_false"),
        ("reviewer_notes_body_stored", True, "dmh_op14_reviewer_notes_body_stored_not_false"),
        ("question_text_included", True, "dmh_op14_question_text_included_not_false"),
        ("draft_question_text_included", True, "dmh_op14_draft_question_text_included_not_false"),
        ("terminal_output_body_included", True, "dmh_op14_terminal_output_body_included_not_false"),
        ("disposal_receipt_ref", "/tmp/local/path/receipt", "dmh_op14_disposal_receipt_ref_has_path_shape"),
    ],
)
def test_dmh_op14_blocks_receipt_path_hash_question_body_and_terminal_leaks(field: str, bad_value: object, expected_blocker: str) -> None:
    receipt = _ready_receipt()
    receipt[field] = bad_value
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
        rating_question_consistency_blocker_separation=_ready_op13(),
        disposal_receipt_bodyfree=receipt,
    )

    assert material["dmh_op14_ready"] is False
    assert material["dmh_op14_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_BY_LEAK_STATUS_REF
    assert expected_blocker in material["dmh_op14_blocker_refs"]
    assert material["disposal_receipt_ready_for_final_no_leak_validation_only"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True


def test_dmh_op14_blocks_forbidden_payload_key_in_disposal_receipt() -> None:
    receipt = _ready_receipt()
    receipt["raw_input"] = "must never be accepted"
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
        rating_question_consistency_blocker_separation=_ready_op13(),
        disposal_receipt_bodyfree=receipt,
    )

    assert material["dmh_op14_ready"] is False
    assert material["dmh_op14_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_BY_LEAK_STATUS_REF
    assert "dmh_op14_disposal_receipt_forbidden_payload_key" in material["dmh_op14_blocker_refs"]
    assert material["forbidden_disposal_receipt_payload_key_path_count"] == 1
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op14_ready", False),
        ("dmh_op14_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_STATUS_REF),
        ("disposal_purge_receipt_accepted", False),
        ("disposal_receipt_intaked_here", False),
        ("operation_receipt_ref_matches_op13", False),
        ("body_full_packet_lifecycle_closed_bodyfree", False),
        ("body_removed_without_hash_path_question_or_reviewer_notes", False),
        ("disposal_receipt_does_not_create_question_text", False),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op14_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op14()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material)


def test_dmh_op15_validates_final_bodyfree_no_question_path_hash_and_no_touch_boundary() -> None:
    material = _ready_op15()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF
    assert material["dmh_op15_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_READY_STATUS_REF
    assert material["dmh_op15_ready"] is True
    assert tuple(material["dmh_op15_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_READY_REASON_REFS
    assert material["op14_dmh_ready"] is True
    assert material["op14_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF
    assert material["op14_disposal_purge_receipt_accepted"] is True
    assert material["op14_disposal_receipt_ready_for_final_no_leak_validation_only"] is True
    assert material["forbidden_payload_key_paths"] == []
    assert material["body_leak_flag_paths"] == []
    assert material["question_text_flag_paths"] == []
    assert material["path_hash_flag_paths"] == []
    assert material["terminal_output_body_flag_paths"] == []
    assert material["no_touch_violation_paths"] == []
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_path_hash_validation_passed"] is True
    assert material["no_terminal_output_body_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["final_no_leak_validation_passed"] is True
    assert material["body_free_artifacts_only"] is True
    assert material["disposal_verified"] is True
    assert material["disposal_verified_by_op15_validation_only"] is True
    assert material["actual_review_evidence_complete_predicate_allowed_next"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op15_alias_builder_matches_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree(
        disposal_purge_receipt_intake=_ready_op14(),
        bodyfree_artifacts=[_ready_op13()],
    )

    assert material["dmh_op15_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree_contract(material) is True


def test_dmh_op15_can_validate_op14_only_without_claiming_evidence_complete() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation(
        disposal_purge_receipt_intake=_ready_op14(),
    )

    assert material["dmh_op15_ready"] is True
    assert material["validated_artifact_ref_count"] == 1
    assert material["disposal_verified"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_predicate_allowed_next"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True


def test_dmh_op15_blocks_without_ready_op14() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation()

    assert material["dmh_op15_ready"] is False
    assert material["dmh_op15_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_STATUS_REF
    assert "dmh_op15_op14_not_ready_for_final_validation" in material["dmh_op15_blocker_refs"]
    assert "dmh_op15_op14_next_step_not_final_validation" in material["dmh_op15_blocker_refs"]
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete_predicate_allowed_next"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True


def test_dmh_op15_blocks_if_op14_material_was_mutated_after_receipt_intake() -> None:
    op14 = _ready_op14()
    op14["next_required_step"] = dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation(
        disposal_purge_receipt_intake=op14,
    )

    assert material["dmh_op15_ready"] is False
    assert "dmh_op15_op14_disposal_purge_receipt_intake_invalid" in material["dmh_op15_blocker_refs"]
    assert "dmh_op15_op14_next_step_not_final_validation" in material["dmh_op15_blocker_refs"]
    assert material["final_no_leak_validation_passed"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True


@pytest.mark.parametrize(
    ("mutation_name", "mutator", "expected_blocker", "expected_path_key"),
    [
        ("forbidden_raw_input", lambda artifact: artifact.__setitem__("raw_input", "must never pass"), "dmh_op15_body_or_forbidden_payload_leak_detected", "forbidden_payload_key_paths"),
        ("body_leak_flag", lambda artifact: artifact.__setitem__("raw_input_included", True), "dmh_op15_body_or_forbidden_payload_leak_detected", "body_leak_flag_paths"),
        ("question_text_flag", lambda artifact: artifact.__setitem__("question_text_materialized_here", True), "dmh_op15_question_text_or_question_trigger_detected", "question_text_flag_paths"),
        ("path_hash_flag", lambda artifact: artifact.__setitem__("body_hash_stored", True), "dmh_op15_path_or_body_hash_detected", "path_hash_flag_paths"),
        ("terminal_output_flag", lambda artifact: artifact.__setitem__("terminal_output_body_included", True), "dmh_op15_terminal_output_body_detected", "terminal_output_body_flag_paths"),
        ("no_touch_top_level", lambda artifact: artifact.__setitem__("response_key_changed", True), "dmh_op15_no_touch_violation_detected", "no_touch_violation_paths"),
        ("no_touch_map", lambda artifact: artifact["post_pmn23_no_touch_contract"].__setitem__("rn_production_ui_changed", True), "dmh_op15_no_touch_violation_detected", "no_touch_violation_paths"),
    ],
)
def test_dmh_op15_blocks_body_question_path_hash_terminal_and_no_touch_violations(
    mutation_name: str,
    mutator,
    expected_blocker: str,
    expected_path_key: str,
) -> None:
    artifact = _ready_op14()
    mutator(artifact)
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation(
        disposal_purge_receipt_intake=_ready_op14(),
        bodyfree_artifacts=[artifact],
    )

    assert material["dmh_op15_ready"] is False, mutation_name
    assert material["dmh_op15_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_BY_LEAK_STATUS_REF
    assert expected_blocker in material["dmh_op15_blocker_refs"]
    assert len(material[expected_path_key]) >= 1
    assert material["final_no_leak_validation_passed"] is False
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete_predicate_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op15_ready", False),
        ("dmh_op15_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_STATUS_REF),
        ("op14_dmh_ready", False),
        ("op14_disposal_purge_receipt_accepted", False),
        ("no_body_leak_validation_passed", False),
        ("no_question_text_validation_passed", False),
        ("no_path_hash_validation_passed", False),
        ("no_terminal_output_body_validation_passed", False),
        ("no_touch_validation_passed", False),
        ("final_no_leak_validation_passed", False),
        ("body_free_artifacts_only", False),
        ("disposal_verified", False),
        ("actual_review_evidence_complete_predicate_allowed_next", False),
        ("actual_review_evidence_complete_from_real_review", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op15_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op15()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material)


def test_dmh_op15_contract_rejects_leak_count_tampering() -> None:
    artifact = _ready_op14()
    artifact["raw_input"] = "must be counted"
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation(
        disposal_purge_receipt_intake=_ready_op14(),
        bodyfree_artifacts=[artifact],
    )
    assert material["forbidden_payload_key_path_count"] == 1
    material["forbidden_payload_key_path_count"] = 0

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material)


def test_dmh_op14_op15_keep_p5_p6_p8_r52_p7_release_and_postcr22_reentry_closed() -> None:
    op14 = _ready_op14()
    op15 = _ready_op15()

    for material in (op14, op15):
        assert material["p5_final_allowed"] is False
        assert material["p6_start_allowed"] is False
        assert material["p8_start_allowed"] is False
        assert material["r52_actual_execution_confirmed"] is False
        assert material["p7_complete"] is False
        assert material["release_allowed"] is False
        assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
        assert material["actual_review_evidence_complete_from_real_review"] is False
        _assert_bodyfree_no_touch_no_promotion(material)
