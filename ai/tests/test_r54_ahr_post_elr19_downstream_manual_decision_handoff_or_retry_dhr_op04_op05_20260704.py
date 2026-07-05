"""Target tests for DHR-OP04/OP05 Post-ELR19 handoff-or-retry boundary."""

from __future__ import annotations

import pytest

import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op16_op17_20260703 import (
    _op17_ready,
)
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_op03_20260704 import (
    _op02_accepted_intake,
)


NO_TOUCH_FALSE_FIELDS = (
    "api_changed",
    "api_route_changed",
    "api_response_key_changed",
    "db_changed",
    "db_schema_changed",
    "db_write_path_changed",
    "rn_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_changed",
    "runtime_generation_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "body_full_packet_generated_here",
    "body_full_packet_generation_run_here",
    "actual_local_human_review_executed_here",
    "actual_human_review_run_here",
    "actual_rows_created_here",
    "actual_operation_receipt_created_here",
    "actual_sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_purge_executed_here",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "actual_review_execution_claimed_by_dhr_op01",
    "dmd_execution_started_here",
    "dmd_auto_execution_allowed",
    "manual_decision_auto_executes_downstream",
    "postcr22_ex07_ex18_reentry_executed_here",
    "postcr22_ex07_ex18_reentry_execution_requested_here",
    "r52_actual_execution_started_here",
    "r52_actual_execution_confirmed",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == dhr.P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["manual_decision_required_without_auto_execution"] is True
    assert material["body_free"] is True
    assert material["post_elr19_no_touch_contract"]["api_route_changed"] is False
    assert material["post_elr19_no_touch_contract"]["db_schema_changed"] is False
    assert material["post_elr19_no_touch_contract"]["rn_production_ui_changed"] is False
    assert material["post_elr19_no_touch_contract"]["runtime_generation_changed"] is False
    assert material["post_elr19_no_touch_contract"]["response_key_changed"] is False
    for field in NO_TOUCH_FALSE_FIELDS:
        assert material[field] is False, field


def _op03_shape_valid_extraction() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=_op17_ready(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material)
    return material


def _external_actual_source_claim() -> dict[str, object]:
    return {
        "source_kind_ref": dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF,
        "actual_source_claim_bodyfree": True,
        "body_free": True,
        "actual_source_claim_origin_ref": dhr.P7_R54_AHR_POST_ELR19_DHR_EXTERNAL_ACTUAL_SOURCE_ORIGIN_REF,
        "actual_local_only_human_review_by_person_confirmed": True,
        "actual_operation_receipt_created_by_helper_here": False,
        "actual_rows_created_by_helper_here": False,
        "helper_green_promoted_to_actual_source": False,
        "target_green_promoted_to_actual_source": False,
        "result_memo_green_promoted_to_actual_source": False,
        "fixture_promoted_to_actual_source": False,
        "historical_reuse_promoted_to_actual_source": False,
        "candidate_shape_promoted_to_actual_source": False,
    }


def _op04_not_confirmed_separation() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=_op03_shape_valid_extraction(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(material)
    return material


def _op04_confirmed_separation() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=_op03_shape_valid_extraction(),
        external_actual_operation_evidence_claim_optional=_external_actual_source_claim(),
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(material)
    return material


def test_dhr_op04_separates_shape_valid_receipt_from_actual_source_confirmation_default() -> None:
    material = _op04_not_confirmed_separation()

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_SCHEMA_VERSION
    assert material["operation_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF
    assert material["op03_contract_valid"] is True
    assert material["op03_ready_for_actual_source_claim_separation"] is True
    assert material["receipt_shape_valid"] is True
    assert material["receipt_source_kind_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF
    assert material["receipt_count_fields_are_24"] is True
    assert material["receipt_required_true_fields_passed"] is True
    assert material["receipt_body_free"] is True
    assert material["receipt_candidate_bodyfree_present"] is True
    assert material["receipt_candidate_shape_carried_only"] is True
    assert material["candidate_shape_promoted_to_actual_source"] is False
    assert material["external_actual_operation_evidence_claim_optional_present"] is False
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["actual_source_claim_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_CLAIM_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF
    assert material["actual_source_claim_requires_external_bodyfree_evidence"] is True
    assert material["actual_source_claim_missing_or_not_confirmed"] is True
    assert material["actual_source_exclusion_refs"] == ["candidate_shape_only"]
    assert material["invalid_source_kind_ref_count"] == 0
    assert material["helper_green_promoted_to_actual_source"] is False
    assert material["target_green_promoted_to_actual_source"] is False
    assert material["result_memo_green_promoted_to_actual_source"] is False
    assert material["fixture_promoted_to_actual_source"] is False
    assert material["historical_reuse_promoted_to_actual_source"] is False
    assert material["actual_operation_receipt_created_by_helper_here"] is False
    assert material["actual_rows_created_by_helper_here"] is False
    assert material["dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan"] is True
    assert material["dhr_op04_does_not_resolve_final_branch"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP05_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op04_confirms_only_explicit_external_bodyfree_actual_source_claim() -> None:
    material = _op04_confirmed_separation()

    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_CLAIM_CONFIRMED_BODYFREE_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["actual_source_claim_bodyfree"] is True
    assert material["actual_source_claim_origin_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_EXTERNAL_ACTUAL_SOURCE_ORIGIN_REF
    assert material["actual_local_only_human_review_by_person_confirmed"] is True
    assert material["external_actual_operation_evidence_claim_optional_present"] is True
    assert material["external_actual_operation_evidence_claim_source_kind_valid"] is True
    assert material["external_actual_operation_evidence_claim_forbidden_payload_key_path_count"] == 0
    assert material["external_actual_operation_evidence_claim_body_like_value_path_count"] == 0
    assert material["external_actual_operation_evidence_claim_promotion_claim_ref_count"] == 0
    assert material["actual_source_exclusion_ref_count"] == 0
    assert material["actual_operation_receipt_created_by_helper_here"] is False
    assert material["actual_rows_created_by_helper_here"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP05_REF
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize("invalid_ref", dhr.P7_R54_AHR_POST_ELR19_DHR_INVALID_SOURCE_KIND_REFS)
def test_dhr_op04_keeps_invalid_external_source_kinds_out_of_actual_source(invalid_ref: str) -> None:
    claim = _external_actual_source_claim()
    claim["source_kind_ref"] = invalid_ref

    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=_op03_shape_valid_extraction(),
        external_actual_operation_evidence_claim_optional=claim,
    )

    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_INVALID_REPAIR_REQUIRED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["invalid_source_kind_refs"] == [invalid_ref]
    assert material["invalid_source_kind_ref_count"] == 1
    assert "dhr_op04_external_actual_source_claim_invalid_source_kind_detected" in material["dhr_op04_blocker_refs"]
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(material)


def test_dhr_op04_repairs_external_claim_body_leak_without_retaining_body_value() -> None:
    claim = _external_actual_source_claim()
    claim["question_text"] = "must not remain visible"

    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=_op03_shape_valid_extraction(),
        external_actual_operation_evidence_claim_optional=claim,
    )

    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_INVALID_REPAIR_REQUIRED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["external_actual_operation_evidence_claim_forbidden_payload_key_path_count"] > 0
    assert material["external_actual_operation_evidence_claim_body_like_value_path_count"] > 0
    assert "dhr_op04_external_actual_source_claim_forbidden_payload_key_detected" in material["dhr_op04_blocker_refs"]
    assert "dhr_op04_external_actual_source_claim_body_like_value_detected" in material["dhr_op04_blocker_refs"]
    assert "must not remain visible" not in repr(material)
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(material)


def test_dhr_op04_repairs_helper_created_receipt_or_row_promotion_attempt() -> None:
    claim = _external_actual_source_claim()
    claim["actual_operation_receipt_created_by_helper_here"] = True

    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=_op03_shape_valid_extraction(),
        external_actual_operation_evidence_claim_optional=claim,
    )

    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_INVALID_REPAIR_REQUIRED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["external_actual_operation_evidence_claim_promotion_claim_ref_count"] > 0
    assert "dhr_op04_external_actual_source_claim_promotion_attempt_detected" in material["dhr_op04_blocker_refs"]
    assert material["actual_operation_receipt_created_by_helper_here"] is False
    assert material["actual_rows_created_by_helper_here"] is False
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(material)


@pytest.mark.parametrize(
    ("field", "mutated_value"),
    [
        ("actual_source_claim_confirmed_for_downstream_handoff", True),
        ("candidate_shape_promoted_to_actual_source", True),
        ("helper_green_promoted_to_actual_source", True),
        ("actual_operation_receipt_created_by_helper_here", True),
        ("actual_rows_created_by_helper_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "DMD_HANDOFF_READY"),
    ],
)
def test_dhr_op04_contract_rejects_source_or_promotion_mutations(field: str, mutated_value: object) -> None:
    material = _op04_not_confirmed_separation()
    material[field] = mutated_value
    with pytest.raises((AssertionError, ValueError)):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(material)


def test_dhr_op05_waits_when_actual_source_claim_is_not_confirmed() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_not_confirmed_separation(),
    )

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_SCHEMA_VERSION
    assert material["operation_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF
    assert material["op04_contract_valid"] is True
    assert material["op04_actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_WAITING_OR_INCOMPLETE_REF
    assert material["bodyfree_leak_promotion_source_scan_passed"] is True
    assert material["preflight_scan_passed"] is False
    assert material["preflight_waiting_or_incomplete"] is True
    assert material["evidence_incomplete_or_source_not_confirmed"] is True
    assert material["dmd_direct_call_safe_without_adapter"] is False
    assert material["dmd_direct_call_blocker_refs"] == [dhr.P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_BLOCKER_REF]
    assert material["dmh_op18_finalizer_fake_generation_allowed"] is False
    assert material["dmd_handoff_plan_candidate_allowed"] is False
    assert material["dmd_handoff_plan_candidate_blocker_refs"] == ["dhr_op05_actual_source_claim_not_confirmed_for_dmd_handoff_plan_candidate"]
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP06_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op05_allows_only_manual_handoff_plan_candidate_when_external_source_confirmed() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_confirmed_separation(),
    )

    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_CLEAR_BODYFREE_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["forbidden_payload_key_path_count"] == 0
    assert material["body_like_value_path_count"] == 0
    assert material["promotion_claim_ref_count"] == 0
    assert material["invalid_source_kind_ref_count"] == 0
    assert material["bodyfree_leak_promotion_source_scan_passed"] is True
    assert material["preflight_scan_passed"] is True
    assert material["preflight_repair_required"] is False
    assert material["preflight_waiting_or_incomplete"] is False
    assert material["dmd_direct_call_safe_without_adapter"] is False
    assert material["dmd_direct_call_blocker_refs"] == [dhr.P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_BLOCKER_REF]
    assert material["dmh_op18_finalizer_fake_generation_allowed"] is False
    assert material["dmd_handoff_plan_candidate_allowed"] is True
    assert material["dmd_handoff_plan_candidate_blocker_ref_count"] == 0
    assert material["dmd_alternate_post_elr19_intake_may_be_required"] is True
    assert material["dhr_op05_does_not_resolve_final_branch"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP06_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dhr_op05_repairs_body_leak_from_additional_material_without_retaining_value() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_confirmed_separation(),
        additional_bodyfree_materials=[{"comment_text": "must not remain visible"}],
    )

    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_REPAIR_REQUIRED_REF
    assert material["preflight_repair_required"] is True
    assert material["forbidden_payload_key_path_count"] > 0
    assert material["body_like_value_path_count"] > 0
    assert "dhr_op05_forbidden_payload_key_detected" in material["dhr_op05_blocker_refs"]
    assert "dhr_op05_body_like_value_detected" in material["dhr_op05_blocker_refs"]
    assert material["dmd_handoff_plan_candidate_allowed"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF
    assert "must not remain visible" not in repr(material)
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)


def test_dhr_op05_repairs_promotion_claims_before_branch_resolver() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_confirmed_separation(),
        additional_bodyfree_materials=[{"release_allowed": True}],
    )

    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_REPAIR_REQUIRED_REF
    assert material["preflight_repair_required"] is True
    assert material["promotion_claim_ref_count"] > 0
    assert "dhr_op05_promotion_claim_detected" in material["dhr_op05_blocker_refs"]
    assert material["dmd_handoff_plan_candidate_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)


def test_dhr_op05_repairs_invalid_source_kind_in_additional_material() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_confirmed_separation(),
        additional_bodyfree_materials=[{"source_kind_ref": "synthetic"}],
    )

    assert material["dhr_op05_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_REPAIR_REQUIRED_REF
    assert any("synthetic" in ref for ref in material["invalid_source_kind_refs"])
    assert material["invalid_source_kind_ref_count"] == 1
    assert "dhr_op05_invalid_source_kind_detected" in material["dhr_op05_blocker_refs"]
    assert material["dmd_handoff_plan_candidate_allowed"] is False
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)


@pytest.mark.parametrize(
    ("field", "mutated_value"),
    [
        ("dmd_direct_call_safe_without_adapter", True),
        ("dmh_op18_finalizer_fake_generation_allowed", True),
        ("dmd_handoff_plan_candidate_allowed", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "DMD_EXECUTION_ALLOWED"),
    ],
)
def test_dhr_op05_contract_rejects_direct_dmd_or_promotion_mutations(field: str, mutated_value: object) -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_not_confirmed_separation(),
    )
    material[field] = mutated_value
    with pytest.raises((AssertionError, ValueError)):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(material)


def test_dhr_op04_op05_full_title_aliases_match_canonical_builders_and_asserts() -> None:
    op03 = _op03_shape_valid_extraction()
    canonical_op04 = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=op03,
    )
    alias_op04 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        elr_op17_dmd_compatible_receipt_candidate_extraction=op03,
    )
    assert canonical_op04 == alias_op04
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(alias_op04)

    canonical_op05 = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=canonical_op04,
    )
    alias_op05 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=canonical_op04,
    )
    assert canonical_op05 == alias_op05
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(alias_op05)
