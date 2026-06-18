# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_FAMILIES,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_TARGETS,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_P5_FIRST_FORMAL_MINIMUMS,
    P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS,
    P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
    P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF,
    build_p7_r47_r14_r15_validation_touch_boundary_freeze,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION,
    P7_R48_FIRST_NEXT_WORK_REF,
    P7_R48_NEXT_REQUIRED_STEP_REF,
    P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
    P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
    P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION,
    P7_R48_P5_REVIEW_POLICY_SCHEMA_VERSION,
    P7_R48_PACKET_KIND,
    P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION,
    P7_R48_REVIEW_KIND,
    P7_R48_SCOPE,
    P7_R48_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION,
    P7_R48_STEP,
    assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract,
    assert_p7_r48_r0_r1_scope_freeze_contract,
    assert_p7_r48_scope_schema_packet_kind_freeze_contract,
    build_p7_r48_current_source_r47_handoff_hold_refreeze,
    build_p7_r48_r0_r1_scope_freeze,
    build_p7_r48_scope_schema_packet_kind_freeze,
)

SECRET_INPUT = "R48 R0/R1 secret raw input must not enter body-free material"
SECRET_SURFACE = "R48 R0/R1 secret Emlis surface must not enter body-free material"
SECRET_REVIEWER = "R48 R0/R1 reviewer free text must not enter body-free material"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_or_release_promotion(value: dict[str, object]) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"current_input_review_surface":' not in dumped
    assert '"returned_emlis_surface":' not in dumped
    assert '"bounded_owned_history_review_surface":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"body_content_hash":' not in dumped
    assert '"local_absolute_path":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def test_r48_r0_refreezes_current_source_r47_ready_handoff_and_unresolved_holds_only() -> None:
    refreeze = build_p7_r48_current_source_r47_handoff_hold_refreeze()
    assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract(refreeze)

    assert refreeze["schema_version"] == P7_R48_CURRENT_SOURCE_R47_HANDOFF_HOLD_REFREEZE_SCHEMA_VERSION
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == P7_R48_STEP
    assert refreeze["scope"] == P7_R48_SCOPE
    assert refreeze["current_phase"] == "P7"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True

    r47 = refreeze["r47_handoff"]
    assert r47["r47_policy_ready"] is True
    assert r47["local_review_packet_policy_ready"] is True
    assert r47["policy_ready"] is True
    assert r47["r47_next_required_step"] == P7_R47_R14_R15_NEXT_REQUIRED_STEP_REF
    assert r47["p5_human_blind_qa_start_allowed_after_r47_policy"] is True
    assert r47["p5_human_blind_qa_confirmed"] is False
    assert r47["p6_limited_human_readfeel_start_allowed"] is False
    assert r47["real_device_modal_review_start_allowed"] is False
    assert r47["release_allowed"] is False

    hold = refreeze["hold_state"]
    assert "P7-HOLD-001" in hold["unresolved_hold_refs"]
    assert "P7-HOLD-004" in hold["unresolved_hold_refs"]
    assert "HOLD-DC-005" in hold["unresolved_hold_refs"]
    assert hold["p5_human_blind_qa_confirmed"] is False
    assert hold["p6_limited_human_readfeel_start_allowed"] is False
    assert hold["body_full_review_packet_generated"] is False
    assert hold["body_free_case_matrix_ready"] is False
    assert hold["disposal_receipt_verified"] is False

    assert refreeze["r0_current_source_r47_handoff_hold_refrozen"] is True
    assert refreeze["r1_scope_schema_packet_kind_fixed"] is False
    assert refreeze["p5_human_blind_qa_start_allowed_after_r47_policy"] is True
    assert refreeze["p5_human_blind_qa_actual_review_start_allowed_after_r48_r0_r1"] is False
    assert refreeze["p5_human_blind_qa_confirmed"] is False
    assert refreeze["actual_human_review_run_here"] is False
    assert refreeze["actual_body_full_packet_generated_here"] is False
    assert refreeze["release_allowed"] is False
    assert refreeze["p7_complete"] is False
    assert refreeze["p8_start_allowed"] is False
    assert refreeze["hold004_close_allowed"] is False

    _assert_no_body_or_release_promotion(refreeze)


def test_r48_r1_fixes_scope_schema_packet_and_review_kind_without_materialization() -> None:
    freeze = build_p7_r48_scope_schema_packet_kind_freeze()
    assert_p7_r48_scope_schema_packet_kind_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R48_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION
    assert freeze["r48_policy_schema_version"] == P7_R48_P5_REVIEW_POLICY_SCHEMA_VERSION
    assert freeze["case_matrix_schema_version"] == P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert freeze["reviewer_packet_local_only_schema_version"] == P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION
    assert freeze["disposal_receipt_bodyfree_schema_version"] == P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION
    assert freeze["review_handoff_summary_bodyfree_schema_version"] == P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert freeze["step"] == P7_R48_STEP
    assert freeze["scope"] == P7_R48_SCOPE
    assert freeze["r48_scope_fixed"] is True
    assert freeze["r48_schema_versions_fixed"] is True
    assert freeze["packet_kind_fixed"] is True
    assert freeze["review_kind_fixed"] is True
    assert freeze["packet_kind"] == P7_R48_PACKET_KIND
    assert freeze["review_kind"] == P7_R48_REVIEW_KIND
    assert freeze["first_next_work_ref"] == P7_R48_FIRST_NEXT_WORK_REF
    assert freeze["next_required_step"] == P7_R48_NEXT_REQUIRED_STEP_REF
    assert freeze["r47_local_review_root_env_var"] == P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR

    assert freeze["r47_p5_first_formal_minimums"] == P7_R47_P5_FIRST_FORMAL_MINIMUMS
    assert freeze["r47_p5_reviewer_facing_allowed_field_refs"] == list(P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS)
    assert freeze["r47_p5_reviewer_facing_forbidden_field_refs"] == list(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS)
    assert freeze["p5_human_blind_qa_families"] == list(P5_HUMAN_BLIND_QA_FAMILIES)
    assert freeze["p5_human_blind_qa_rating_axes"] == list(P5_HUMAN_BLIND_QA_RATING_AXES)
    assert freeze["p5_human_blind_qa_target_thresholds"] == P5_HUMAN_BLIND_QA_TARGETS

    policy = freeze["packet_policy"]
    assert policy["packet_kind"] == P7_R48_PACKET_KIND
    assert policy["review_kind"] == P7_R48_REVIEW_KIND
    assert policy["p5_actual_review_packet_lane_only"] is True
    assert policy["p6_limited_human_readfeel_in_scope"] is False
    assert policy["real_device_modal_review_in_scope"] is False
    assert policy["release_decision_in_scope"] is False
    assert policy["local_only_required_later"] is True
    assert policy["body_full_payload_allowed_only_later_with_valid_local_root_and_explicit_allow"] is True
    assert policy["materialized_here"] is False
    assert policy["writer_created_here"] is False
    assert policy["standard_export_allowed"] is False
    assert policy["public_meta_material_allowed"] is False
    assert policy["p7_scorecard_body_full_material_allowed"] is False
    assert policy["release_material_allowed"] is False
    assert policy["body_free_result_required_later"] is True

    assert freeze["p5_human_blind_qa_actual_review_start_allowed_after_r48_r0_r1"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["json_schema_file_created_here"] is False
    assert freeze["actual_case_matrix_materialized_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_disposal_receipt_materialized_here"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False

    _assert_no_body_or_release_promotion(freeze)


def test_r48_r0_r1_combined_scope_freeze_is_body_free_and_points_to_r2_next() -> None:
    combined = build_p7_r48_r0_r1_scope_freeze()
    assert_p7_r48_r0_r1_scope_freeze_contract(combined)

    assert combined["schema_version"] == P7_R48_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION
    assert combined["first_next_work_ref"] == P7_R48_FIRST_NEXT_WORK_REF
    assert combined["next_required_step"] == P7_R48_NEXT_REQUIRED_STEP_REF
    assert combined["packet_kind"] == P7_R48_PACKET_KIND
    assert combined["review_kind"] == P7_R48_REVIEW_KIND
    assert combined["r0_current_source_r47_handoff_hold_refrozen"] is True
    assert combined["r1_scope_schema_packet_kind_fixed"] is True
    assert combined["p5_human_blind_qa_start_allowed_after_r47_policy"] is True
    assert combined["p5_human_blind_qa_actual_review_start_allowed_after_r48_r0_r1"] is False
    assert combined["p5_human_blind_qa_confirmed"] is False
    assert combined["release_allowed"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["hold004_close_allowed"] is False

    _assert_no_body_or_release_promotion(combined)


def test_r48_r0_rejects_r47_handoff_that_is_not_policy_ready() -> None:
    r47 = build_p7_r47_r14_r15_validation_touch_boundary_freeze()
    r47["r47_policy_ready"] = False
    with pytest.raises(ValueError):
        build_p7_r48_current_source_r47_handoff_hold_refreeze(r47_policy_freeze=r47)


def test_r48_r0_rejects_r47_handoff_that_claims_p5_confirmed_or_opens_release() -> None:
    r47 = build_p7_r47_r14_r15_validation_touch_boundary_freeze()
    r47["p5_human_blind_qa_confirmed"] = True
    with pytest.raises(ValueError):
        build_p7_r48_current_source_r47_handoff_hold_refreeze(r47_policy_freeze=r47)

    r47 = build_p7_r47_r14_r15_validation_touch_boundary_freeze()
    r47["release_allowed"] = True
    with pytest.raises(ValueError):
        build_p7_r48_current_source_r47_handoff_hold_refreeze(r47_policy_freeze=r47)


def test_r48_r1_rejects_packet_or_review_kind_drift() -> None:
    with pytest.raises(ValueError):
        build_p7_r48_scope_schema_packet_kind_freeze(packet_kind="p6_limited_human_readfeel_local_review_packet")

    with pytest.raises(ValueError):
        build_p7_r48_scope_schema_packet_kind_freeze(review_kind="p6_structure_insight_limited_readfeel")


def test_r48_r0_r1_builders_reject_body_payload_or_contract_mutation_inputs() -> None:
    with pytest.raises(ValueError):
        build_p7_r48_current_source_r47_handoff_hold_refreeze(snapshot_refs={"raw_input": SECRET_INPUT})

    r0 = build_p7_r48_current_source_r47_handoff_hold_refreeze()
    r0["reviewer_free_text"] = SECRET_REVIEWER
    with pytest.raises(ValueError):
        build_p7_r48_scope_schema_packet_kind_freeze(current_source_refreeze=r0)

    with pytest.raises(ValueError):
        build_p7_r48_r0_r1_scope_freeze(snapshot_refs={"public_response_key_added": True})


def test_r48_r0_r1_contracts_reject_false_review_start_or_release_promotion() -> None:
    refreeze = build_p7_r48_current_source_r47_handoff_hold_refreeze()
    refreeze["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_current_source_r47_handoff_hold_refreeze_contract(refreeze)

    freeze = build_p7_r48_scope_schema_packet_kind_freeze()
    freeze["p5_human_blind_qa_actual_review_start_allowed_after_r48_r0_r1"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_scope_schema_packet_kind_freeze_contract(freeze)

    combined = build_p7_r48_r0_r1_scope_freeze()
    combined["body_full_writer_created_here"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_r0_r1_scope_freeze_contract(combined)
