# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP02/OP03 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op00_op01_20260701 as dmh_op00_op01_prev


def _ready_op01() -> dict[str, object]:
    material = dmh_op00_op01_prev._ready_op01()
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(material) is True
    return material


def _ready_op02() -> dict[str, object]:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision(
        pmn_op23_downstream_manual_decision_hold_intake=_ready_op01(),
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_contract(material) is True
    return material


def _ready_explicit_allow_receipt(review_session_id: str | None = None) -> dict[str, object]:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_bodyfree(
        review_session_id=review_session_id,
    )
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_SCHEMA_VERSION
    assert material["body_free"] is True
    return material


def _ready_op03() -> dict[str, object]:
    op02 = _ready_op02()
    receipt = _ready_explicit_allow_receipt(str(op02["review_session_id"]))
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope(
        existing_pmn_postcr22_ex_reuse_decision=op02,
        explicit_allow_receipt=receipt,
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract(material) is True
    return material


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


def test_dmh_op02_reuses_existing_pmn_and_postcr22_ex_lines_without_new_giant_wrapper_or_execution() -> None:
    material = _ready_op02()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_EXISTING_PMN_POSTCR22_EX_REUSE_DECISION_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF
    assert material["dmh_op02_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_READY_STATUS_REF
    assert material["dmh_op02_ready"] is True
    assert material["dmh_op02_blocker_refs"] == []
    assert material["dmh_op02_reason_refs"] == [
        "existing_post_mn11_pmn_helper_reuse_candidate_confirmed_bodyfree",
        "existing_postcr22_ex07_ex18_reentry_candidate_confirmed_bodyfree",
        "new_giant_wrapper_not_required_minimal_bridge_only",
        "postcr22_ex07_ex18_reentry_not_executed_here",
        "helper_fixture_not_promoted_to_actual_evidence",
    ]
    assert material["existing_pmn_helper_reuse_candidate"] is True
    assert material["existing_pmn_helper_responsibility_rechecked"] is True
    assert material["existing_pmn_helper_step_ref_count"] == 24
    assert tuple(material["existing_pmn_helper_step_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS
    assert material["existing_pmn_helper_first_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS[0]
    assert material["existing_pmn_helper_last_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS[-1]
    assert material["existing_postcr22_ex_reentry_candidate"] is True
    assert material["existing_postcr22_ex_reentry_candidate_only"] is True
    assert material["existing_postcr22_ex_reentry_executed_here"] is False
    assert material["existing_postcr22_ex_reentry_step_ref_count"] == 12
    assert tuple(material["existing_postcr22_ex_reentry_step_refs"]) == pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS
    assert material["existing_postcr22_ex_reentry_first_step_ref"] == pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[0]
    assert material["existing_postcr22_ex_reentry_last_step_ref"] == pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[-1]
    assert material["new_giant_wrapper_required"] is False
    assert material["minimal_evidence_intake_bridge_allowed_if_needed"] is True
    assert material["existing_helpers_reused_without_modification"] is True
    assert material["dmh_op02_does_not_generate_body_full_packet"] is True
    assert material["dmh_op02_does_not_run_actual_human_review"] is True
    assert material["dmh_op02_does_not_create_operation_receipt_or_rows_or_disposal"] is True
    assert material["dmh_op02_does_not_start_p8_p6_r52_or_release"] is True
    assert material["dmh_op02_does_not_execute_postcr22_ex_reentry"] is True
    assert material["dmh_op02_does_not_treat_helper_fixture_as_actual_evidence"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op02_blocks_when_op01_intake_is_missing_and_does_not_claim_reuse_candidates() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_REQUIRED_FIELD_REFS)
    assert material["dmh_op02_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_STATUS_REF
    assert material["dmh_op02_ready"] is False
    assert "dmh_op02_pmn_op23_downstream_manual_decision_hold_intake_missing" in material["dmh_op02_blocker_refs"]
    assert material["existing_pmn_helper_reuse_candidate"] is False
    assert material["existing_postcr22_ex_reentry_candidate"] is False
    assert material["existing_postcr22_ex_reentry_candidate_only"] is False
    assert material["minimal_evidence_intake_bridge_allowed_if_needed"] is False
    assert material["existing_postcr22_ex_reentry_executed_here"] is False
    assert material["new_giant_wrapper_required"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("existing_pmn_helper_reuse_candidate", False),
        ("existing_postcr22_ex_reentry_candidate", False),
        ("existing_postcr22_ex_reentry_executed_here", True),
        ("new_giant_wrapper_required", True),
        ("minimal_evidence_intake_bridge_allowed_if_needed", False),
        ("dmh_op02_does_not_treat_helper_fixture_as_actual_evidence", False),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op02_contract_rejects_reuse_execution_fixture_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op02()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_contract(mutated)


def test_dmh_op03_explicit_allow_receipt_fixture_is_bodyfree_and_not_packet_generation() -> None:
    op02 = _ready_op02()
    receipt = _ready_explicit_allow_receipt(str(op02["review_session_id"]))

    assert receipt["explicit_allow_receipt_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_REF
    assert receipt["explicit_allow_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_REF
    assert receipt["allow_scope_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOW_SCOPE_REF
    assert receipt["review_session_id"] == op02["review_session_id"]
    assert receipt["actual_review_basis_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF
    assert receipt["required_case_count"] == 24
    assert receipt["local_only_required"] is True
    assert receipt["body_full_packet_generation_allowed_for_local_review_only"] is True
    assert receipt["body_full_export_allowed"] is False
    assert receipt["body_free_summary_export_allowed"] is True
    assert receipt["retention_policy_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_RETENTION_POLICY_REF
    assert receipt["disposal_policy_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_DISPOSAL_POLICY_REF
    assert receipt["export_denylist_policy_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_EXPORT_DENYLIST_POLICY_REF
    assert receipt["no_path_hash_in_artifact_required"] is True
    assert receipt["body_full_packet_generated_here"] is False
    assert receipt["body_free"] is True
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in receipt, forbidden_key


def test_dmh_op03_accepts_explicit_allow_receipt_and_freezes_local_only_session_without_packet_generation() -> None:
    material = _ready_op03()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_LOCAL_ONLY_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF
    assert material["dmh_op03_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_READY_STATUS_REF
    assert material["dmh_op03_ready"] is True
    assert material["dmh_op03_blocker_refs"] == []
    assert material["op02_dmh_ready"] is True
    assert material["op02_existing_pmn_helper_reuse_candidate"] is True
    assert material["op02_existing_postcr22_ex_reentry_candidate"] is True
    assert material["op02_new_giant_wrapper_required"] is False
    assert material["explicit_allow_receipt_present"] is True
    assert material["explicit_allow_ref_present"] is True
    assert material["allow_scope_ref_present"] is True
    assert material["review_session_id_present"] is True
    assert material["review_session_id_bodyfree_identifier"] is True
    assert material["review_session_id_has_local_path_shape"] is False
    assert material["review_session_id_has_question_or_body_text_shape"] is False
    assert material["local_only_review_session_envelope_ready"] is True
    assert material["review_session_state_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_ACCEPTED_REF
    assert tuple(material["allowed_review_session_state_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_REVIEW_SESSION_STATE_REFS
    assert tuple(material["allowed_ready_session_transition_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_READY_SESSION_TRANSITION_REFS
    assert tuple(material["forbidden_session_promotion_transition_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS
    assert material["local_review_root_ref_present"] is True
    assert material["local_review_root_ref_has_path_shape"] is False
    assert material["local_review_root_path_included"] is False
    assert material["actual_review_basis_ref_present"] is True
    assert material["required_case_count"] == 24
    assert material["local_only_required"] is True
    assert material["body_full_packet_generation_allowed_for_local_review_only"] is True
    assert material["body_full_packet_generation_allowed_by_explicit_allow_receipt"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_generation_blocked_until_24_case_manifest_boundary"] is True
    assert material["body_full_export_allowed"] is False
    assert material["body_free_summary_export_allowed"] is True
    assert material["retention_policy_ref_present"] is True
    assert material["disposal_policy_ref_present"] is True
    assert material["export_denylist_policy_ref_present"] is True
    assert material["no_path_hash_in_artifact_required"] is True
    assert material["purge_required_before_or_after_review"] is True
    assert tuple(material["purge_required_delete_target_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_DELETE_TARGET_REFS
    assert material["explicit_allow_body_stored_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["dmh_op03_does_not_generate_body_full_packet"] is True
    assert material["dmh_op03_does_not_run_actual_human_review"] is True
    assert material["dmh_op03_does_not_create_operation_receipt_or_rows_or_disposal"] is True
    assert material["dmh_op03_does_not_start_p8_p6_r52_or_release"] is True
    assert material["dmh_op03_does_not_materialize_question_text"] is True
    assert material["dmh_op03_does_not_execute_postcr22_ex_reentry"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[4]
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op03_blocks_without_explicit_allow_receipt_and_does_not_allow_packet_generation() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope(
        existing_pmn_postcr22_ex_reuse_decision=_ready_op02(),
    )

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_FIELD_REFS)
    assert material["dmh_op03_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_STATUS_REF
    assert material["dmh_op03_ready"] is False
    assert "dmh_op03_explicit_allow_receipt_missing" in material["dmh_op03_blocker_refs"]
    assert material["explicit_allow_receipt_present"] is False
    assert material["body_full_packet_generation_allowed_for_local_review_only"] is False
    assert material["body_full_packet_generation_allowed_by_explicit_allow_receipt"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op03_blocks_receipt_with_forbidden_body_question_path_hash_keys() -> None:
    op02 = _ready_op02()
    receipt = _ready_explicit_allow_receipt(str(op02["review_session_id"]))
    receipt["raw_input"] = "forbidden raw body must never be accepted"

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope(
        existing_pmn_postcr22_ex_reuse_decision=op02,
        explicit_allow_receipt=receipt,
    )

    assert material["dmh_op03_ready"] is False
    assert "dmh_op03_explicit_allow_receipt_forbidden_body_question_path_hash_key_detected" in material["dmh_op03_blocker_refs"]
    assert material["explicit_allow_receipt_forbidden_payload_key_paths"] == ["explicit_allow_receipt.raw_input"]
    assert material["explicit_allow_receipt_forbidden_payload_key_path_count"] == 1
    assert material["body_full_packet_generation_allowed_for_local_review_only"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("body_full_packet_generation_request_allowed_next", True),
        ("body_full_export_allowed", True),
        ("explicit_allow_body_stored_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_materialized_here", True),
        ("dmh_op03_does_not_generate_body_full_packet", False),
        ("dmh_op03_does_not_materialize_question_text", False),
        ("question_text_materialized_here", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op03_contract_rejects_packet_generation_body_question_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op03()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract(mutated)


def test_dmh_op02_op03_aliases_match_primary_builders_and_contracts() -> None:
    op01 = _ready_op01()
    primary_op02 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision(
        pmn_op23_downstream_manual_decision_hold_intake=op01,
    )
    alias_op02 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_existing_pmn_postcr22_ex_reuse_decision_bodyfree(
        pmn_op23_downstream_manual_decision_hold_intake=op01,
    )
    assert alias_op02 == primary_op02
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_existing_pmn_postcr22_ex_reuse_decision_bodyfree_contract(alias_op02) is True

    primary_receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_bodyfree(
        review_session_id=str(primary_op02["review_session_id"]),
    )
    alias_receipt = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_explicit_allow_receipt_bodyfree(
        review_session_id=str(primary_op02["review_session_id"]),
    )
    assert alias_receipt == primary_receipt

    primary_op03 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope(
        existing_pmn_postcr22_ex_reuse_decision=primary_op02,
        explicit_allow_receipt=primary_receipt,
    )
    alias_op03 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_explicit_allow_receipt_local_only_review_session_envelope_bodyfree(
        existing_pmn_postcr22_ex_reuse_decision=primary_op02,
        explicit_allow_receipt=primary_receipt,
    )
    assert alias_op03 == primary_op03
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_explicit_allow_receipt_local_only_review_session_envelope_bodyfree_contract(alias_op03) is True
