# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP04/OP05 readiness/session-boundary tests."""

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
    _rsr_op02_partial_ready,
    _valid_explicit_allow_receipt,
)


RSR_STOP_EXPLICIT_ALLOW_MISSING = "RSR_STOP_EXPLICIT_ALLOW_MISSING"
RSR_STOP_ENVIRONMENT_MISSING = "RSR_STOP_ENVIRONMENT_MISSING"
RSR_STOP_MATERIAL_MISSING = "RSR_STOP_MATERIAL_MISSING"
RSR_STOP_REVIEWER_PERSON_NOT_CONFIRMED = "RSR_STOP_REVIEWER_PERSON_NOT_CONFIRMED"
RSR_STOP_LOCAL_ONLY_BOUNDARY_NOT_CONFIRMED = "RSR_STOP_LOCAL_ONLY_BOUNDARY_NOT_CONFIRMED"
RSR_STOP_PURGE_PLAN_MISSING = "RSR_STOP_PURGE_PLAN_MISSING"
RSR_STOP_SOURCE_CLAIM_INSUFFICIENT = "RSR_STOP_SOURCE_CLAIM_INSUFFICIENT"
RSR_STOP_BODY_LEAK_RISK = "RSR_STOP_BODY_LEAK_RISK"


def _rsr_op03_allow_accepted() -> dict[str, object]:
    op02 = _rsr_op02_partial_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=op02,
        explicit_local_only_allow_receipt=_valid_explicit_allow_receipt(op02["review_session_id"]),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(material) is True
    assert material["rsr_op03_ready_for_readiness_blocker_classifier"] is True
    assert material["rsr_op03_explicit_allow_accepted"] is True
    return material


def _rsr_op04_ready() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier(
        explicit_local_only_allow_gate=_rsr_op03_allow_accepted(),
        environment_ready=True,
        environment_ready_ref="environment_ready_bodyfree_fixture",
        material_manifest_ready=True,
        material_manifest_ready_ref="material_manifest_ready_bodyfree_fixture",
        reviewer_person_boundary_ready=True,
        local_only_boundary_ready=True,
        purge_plan_ready=True,
        body_leak_preflight_passed=True,
        source_claim_preflight_ready=True,
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(material) is True
    assert material["rsr_op04_ready_for_local_only_review_session_envelope"] is True
    return material


def _assert_op04_no_actual_operation(material: dict[str, object]) -> None:
    assert material["rsr_op04_does_not_generate_body_full_packet"] is True
    assert material["rsr_op04_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op04_does_not_create_receipts_rows_or_disposal"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False


def _assert_op05_no_actual_operation(material: dict[str, object]) -> None:
    assert material["rsr_op05_does_not_generate_body_full_packet"] is True
    assert material["rsr_op05_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op05_does_not_create_receipts_rows_or_disposal"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False


def test_rsr_op04_waits_when_explicit_local_only_allow_has_not_been_accepted() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier()

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF
    assert material["op03_contract_valid"] is True
    assert material["explicit_allow_accepted"] is False
    assert material["rsr_op04_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    assert material["rsr_op04_wait_for_explicit_local_only_allow"] is True
    assert RSR_STOP_EXPLICIT_ALLOW_MISSING in material["readiness_stop_reason_refs"]
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF
    _assert_op04_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op04_ready_only_when_all_bodyfree_readiness_boundaries_are_true() -> None:
    material = _rsr_op04_ready()

    assert material["rsr_op04_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_READY_TO_START_REF
    assert material["environment_ready"] is True
    assert material["material_manifest_ready"] is True
    assert material["reviewer_person_boundary_ready"] is True
    assert material["local_only_boundary_ready"] is True
    assert material["purge_plan_ready"] is True
    assert material["body_leak_preflight_passed"] is True
    assert material["source_claim_preflight_ready"] is True
    assert material["body_leak_preflight_forbidden_payload_key_path_refs"] == []
    assert material["body_leak_preflight_body_like_value_path_refs"] == []
    assert material["body_leak_preflight_promotion_claim_refs"] == []
    assert material["readiness_blocker_refs"] == []
    assert material["readiness_stop_reason_refs"] == []
    assert material["rsr_op04_ready"] is True
    assert material["rsr_op04_ready_for_local_only_review_session_envelope"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF
    _assert_op04_no_actual_operation(material)
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op04_repairs_when_environment_or_material_readiness_is_missing() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier(
        explicit_local_only_allow_gate=_rsr_op03_allow_accepted(),
        environment_ready=True,
        material_manifest_ready=False,
        reviewer_person_boundary_ready=True,
        local_only_boundary_ready=True,
        purge_plan_ready=True,
        body_leak_preflight_passed=True,
        source_claim_preflight_ready=True,
    )

    assert material["rsr_op04_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF
    assert RSR_STOP_MATERIAL_MISSING in material["readiness_stop_reason_refs"]
    assert "material_manifest_ready_ref_missing_or_false" in material["readiness_blocker_refs"]
    assert material["rsr_op04_ready"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_READINESS_BLOCKERS_BEFORE_SESSION_ENVELOPE_REF
    _assert_op04_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("kwargs", "expected_stop"),
    [
        ({"environment_ready": False}, RSR_STOP_ENVIRONMENT_MISSING),
        ({"reviewer_person_boundary_ready": False}, RSR_STOP_REVIEWER_PERSON_NOT_CONFIRMED),
        ({"local_only_boundary_ready": False}, RSR_STOP_LOCAL_ONLY_BOUNDARY_NOT_CONFIRMED),
        ({"purge_plan_ready": False}, RSR_STOP_PURGE_PLAN_MISSING),
    ],
)
def test_rsr_op04_classifies_each_non_allow_readiness_stop_without_starting_review(kwargs: dict[str, bool], expected_stop: str) -> None:
    base = dict(
        explicit_local_only_allow_gate=_rsr_op03_allow_accepted(),
        environment_ready=True,
        material_manifest_ready=True,
        reviewer_person_boundary_ready=True,
        local_only_boundary_ready=True,
        purge_plan_ready=True,
        body_leak_preflight_passed=True,
        source_claim_preflight_ready=True,
    )
    base.update(kwargs)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier(**base)

    assert expected_stop in material["readiness_stop_reason_refs"]
    assert material["rsr_op04_ready"] is False
    assert material["rsr_op04_ready_for_local_only_review_session_envelope"] is False
    _assert_op04_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op04_blocks_body_leak_risk_without_leaking_payload_value() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier(
        explicit_local_only_allow_gate=_rsr_op03_allow_accepted(),
        environment_ready=True,
        material_manifest_ready=True,
        reviewer_person_boundary_ready=True,
        local_only_boundary_ready=True,
        purge_plan_ready=True,
        body_leak_preflight_passed=True,
        source_claim_preflight_ready=True,
        body_leak_preflight_material={
            "raw_input": "this body-full local review input must not leak",
            "body_free": True,
        },
    )

    assert material["rsr_op04_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_BODY_LEAK_RISK_BLOCKED_REF
    assert material["body_leak_preflight_forbidden_payload_key_path_count"] > 0
    assert material["body_leak_preflight_body_like_value_path_count"] > 0
    assert RSR_STOP_BODY_LEAK_RISK in material["readiness_stop_reason_refs"]
    assert "readiness_body_leak_forbidden_payload_key_detected" in material["readiness_blocker_refs"]
    assert "this body-full local review input must not leak" not in repr(material)
    _assert_op04_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op04_classifies_source_claim_preflight_as_insufficient() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier(
        explicit_local_only_allow_gate=_rsr_op03_allow_accepted(),
        environment_ready=True,
        material_manifest_ready=True,
        reviewer_person_boundary_ready=True,
        local_only_boundary_ready=True,
        purge_plan_ready=True,
        body_leak_preflight_passed=True,
        source_claim_preflight_ready=False,
    )

    assert material["rsr_op04_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_SOURCE_CLAIM_INSUFFICIENT_REF
    assert RSR_STOP_SOURCE_CLAIM_INSUFFICIENT in material["readiness_stop_reason_refs"]
    assert "source_claim_preflight_insufficient" in material["readiness_blocker_refs"]
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SOURCE_CLAIM_PREFLIGHT_BEFORE_SESSION_ENVELOPE_REF
    assert material["actual_source_claim_for_dhr_reintake_materialized_here"] is False
    _assert_op04_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rsr_op04_does_not_generate_body_full_packet", False),
        ("rsr_op04_does_not_run_actual_local_human_review", False),
        ("rsr_op04_does_not_create_receipts_rows_or_disposal", False),
        ("body_full_packet_generated_here", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_operation_receipt_created_here", True),
        ("dmd_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF),
    ],
)
def test_rsr_op04_contract_rejects_execution_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _rsr_op04_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(material)


def test_rsr_op05_waits_when_readiness_classifier_is_not_ready() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF
    assert material["op04_contract_valid"] is True
    assert material["op04_ready_for_local_only_review_session_envelope"] is False
    assert material["reviewer_person_ref_present"] is False
    assert material["rsr_op05_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_WAITING_FOR_READINESS_REF
    assert material["rsr_op05_waiting_for_readiness"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_READINESS_BEFORE_REVIEW_SESSION_ENVELOPE_REF
    assert material["review_session_envelope_ref"].startswith("rsr_op05_review_session_envelope_")
    _assert_op05_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op05_repairs_when_reviewer_person_boundary_is_missing_after_readiness() -> None:
    op04 = _rsr_op04_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=op04,
    )

    assert material["rsr_op05_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_REVIEWER_PERSON_NOT_CONFIRMED_REF
    assert material["op04_ready_for_local_only_review_session_envelope"] is True
    assert material["reviewer_person_ref_present"] is False
    assert material["reviewer_is_person_confirmed"] is False
    assert "reviewer_person_ref_missing" in material["reviewer_boundary_blocker_refs"]
    assert "reviewer_person_not_confirmed" in material["reviewer_boundary_blocker_refs"]
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEWER_PERSON_BOUNDARY_REF
    _assert_op05_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op05_accepts_bodyfree_reviewer_person_boundary_without_starting_actual_review() -> None:
    op04 = _rsr_op04_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=op04,
        reviewer_person_ref="reviewer_person_bodyfree_ref_001",
        reviewer_is_person_confirmed=True,
        reviewer_role_ref=rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF,
    )

    assert material["rsr_op05_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_ACCEPTED_BODYFREE_REF
    assert material["review_session_id_normalized"] == op04["review_session_id"]
    assert material["review_session_id_bodyfree"] is True
    assert material["reviewer_person_ref_present"] is True
    assert material["reviewer_person_ref"] == "reviewer_person_bodyfree_ref_001"
    assert material["reviewer_person_ref_bodyfree"] is True
    assert material["reviewer_person_ref_shape_valid"] is True
    assert material["reviewer_is_person_confirmed"] is True
    assert material["reviewer_role_is_selection_only_review_operator"] is True
    assert material["selection_only_review_operator_boundary_confirmed"] is True
    assert material["actual_source_claim_allowed_by_op05"] is False
    assert material["rsr_op05_ready_for_body_full_packet_transient_request_boundary"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF
    _assert_op05_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("reviewer_ref", "confirmed", "role"),
    [
        ("", True, rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF),
        ("reviewer_person_bodyfree_ref_001", False, rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF),
        ("reviewer_person_bodyfree_ref_001", True, "free_text_reviewer"),
        ("reviewer@example.com", True, rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF),
    ],
)
def test_rsr_op05_repairs_non_bodyfree_or_unconfirmed_reviewer_boundaries(reviewer_ref: str, confirmed: bool, role: str) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=_rsr_op04_ready(),
        reviewer_person_ref=reviewer_ref,
        reviewer_is_person_confirmed=confirmed,
        reviewer_role_ref=role,
    )

    assert material["rsr_op05_status_ref"] in {
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_REVIEWER_PERSON_NOT_CONFIRMED_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF,
    }
    assert material["rsr_op05_ready"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEWER_PERSON_BOUNDARY_REF
    assert material["actual_source_claim_allowed_by_op05"] is False
    assert "reviewer@example.com" not in repr(material)
    _assert_op05_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op05_blocks_body_leaking_reviewer_boundary_without_leaking_value() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=_rsr_op04_ready(),
        reviewer_person_ref="reviewer@example.com",
        reviewer_is_person_confirmed=True,
        reviewer_boundary_material={
            "reviewer_note": "raw reviewer note must not leak",
            "body_free": True,
        },
    )

    assert material["rsr_op05_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_BODY_LEAK_BLOCKED_REF
    assert material["reviewer_person_ref"] == "reviewer_person_ref_invalid_bodyfree_boundary"
    assert material["reviewer_person_ref_shape_valid"] is False
    assert material["reviewer_boundary_forbidden_payload_key_path_count"] > 0
    assert material["reviewer_boundary_body_like_value_path_count"] > 0
    assert "reviewer_boundary_forbidden_payload_key_detected" in material["reviewer_boundary_blocker_refs"]
    assert "raw reviewer note must not leak" not in repr(material)
    assert "reviewer@example.com" not in repr(material)
    _assert_op05_no_actual_operation(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("review_session_id_bodyfree", False),
        ("rsr_op05_does_not_generate_body_full_packet", False),
        ("rsr_op05_does_not_run_actual_local_human_review", False),
        ("rsr_op05_does_not_create_receipts_rows_or_disposal", False),
        ("actual_source_claim_allowed_by_op05", True),
        ("body_full_packet_generated_here", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_operation_receipt_created_here", True),
        ("dmd_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF),
    ],
)
def test_rsr_op05_contract_rejects_session_execution_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=_rsr_op04_ready(),
        reviewer_person_ref="reviewer_person_bodyfree_ref_001",
        reviewer_is_person_confirmed=True,
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(material)


def test_rsr_op04_op05_full_title_aliases_match_canonical_builders() -> None:
    op04_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op04_readiness_blocker_classifier()
    op04_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier()
    assert op04_alias == op04_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op04_readiness_blocker_classifier_contract(op04_alias) is True

    op05_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=_rsr_op04_ready(),
        reviewer_person_ref="reviewer_person_bodyfree_ref_001",
        reviewer_is_person_confirmed=True,
    )
    op05_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
        readiness_blocker_classifier=_rsr_op04_ready(),
        reviewer_person_ref="reviewer_person_bodyfree_ref_001",
        reviewer_is_person_confirmed=True,
    )
    assert op05_alias == op05_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(op05_alias) is True
