# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP02/OP03 upstream/allow-gate tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op00_op01_20260704 import (
    _dhr_op09_retry_closed,
)
from test_r54_ahr_post_dmh18_downstream_manual_decision_triage_dmd_op08_result_20260703 import (
    _closed_material as _dmd_op08_closed,
)
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op12_result_20260703 import (
    _closed_validation_kwargs as _alr_op12_closed_validation_kwargs,
    _op12 as _alr_op12,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op18_op19_20260703 import (
    _op19_closed as _elr_op19_closed,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == rsr.P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["post_dhr09_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for key in rsr.P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def _rsr_op01_retry_start() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
        dhr_op09_result_memo=_dhr_op09_retry_closed(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(material) is True
    assert material["rsr_op01_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_RETRY_OR_START_REQUIRED_REF
    return material


def _rsr_op02_partial_ready() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(
        dhr_op09_intake=_rsr_op01_retry_start(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(material) is True
    assert material["rsr_op02_ready_for_explicit_local_only_allow_gate"] is True
    return material


def _valid_explicit_allow_receipt(review_session_id: str | None = None) -> dict[str, object]:
    return {
        "schema_version": rsr.P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_SCHEMA_VERSION,
        "allow_receipt_ref": "allow_rsr_op03_bodyfree_contract_fixture_20260704",
        "review_session_id": review_session_id or rsr.P7_R54_AHR_POST_DHR09_RSR_DEFAULT_REVIEW_SESSION_ID,
        "allowed_operation_scope_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_REF,
        "allowed_case_count": 24,
        "local_only_operation_allowed": True,
        "body_full_transient_review_allowed": True,
        "external_export_allowed": False,
        "disposal_purge_required": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def test_rsr_op02_accepts_dhr09_retry_closed_as_sufficient_when_optional_upstream_material_is_missing() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(
        dhr_op09_intake=_rsr_op01_retry_start(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF
    assert material["op01_contract_valid"] is True
    assert material["op01_ready_for_upstream_relationship_verification"] is True
    assert material["dhr_op09_contract_valid"] is True
    assert material["dhr_op09_result_memo_bodyfree_closed"] is True
    assert material["dhr_op09_selected_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF
    assert material["dhr_op09_next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF
    assert material["dhr_op09_dmd_handoff_plan_materialized"] is False
    assert material["op02_optional_upstream_material_count"] == 0
    assert material["op02_valid_upstream_material_count"] == 0
    assert material["op02_missing_optional_upstream_relation_ref_count"] == 3
    assert material["rsr_op02_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_PARTIAL_DHR09_CLOSED_BODYFREE_REF
    assert material["rsr_op02_partial_upstream_material_accepted_from_dhr09"] is True
    assert material["rsr_op02_ready"] is True
    assert material["rsr_op02_ready_for_explicit_local_only_allow_gate"] is True
    assert material["rsr_op02_blocker_refs"] == []
    assert material["rsr_op02_does_not_accept_explicit_local_only_allow"] is True
    assert material["rsr_op02_does_not_run_actual_local_human_review"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op02_verifies_all_supplied_upstream_materials_when_contracts_and_branches_match() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(
        dhr_op09_intake=_rsr_op01_retry_start(),
        dmd_op08_result_memo=_dmd_op08_closed(),
        alr_op12_result_memo=_alr_op12(**_alr_op12_closed_validation_kwargs()),
        elr_op19_result_memo=_elr_op19_closed(),
    )

    assert material["rsr_op02_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_VERIFIED_BODYFREE_REF
    assert material["dmd_op08_material_present"] is True
    assert material["alr_op12_material_present"] is True
    assert material["elr_op19_material_present"] is True
    assert material["dmd_op08_contract_valid"] is True
    assert material["alr_op12_contract_valid"] is True
    assert material["elr_op19_contract_valid"] is True
    assert material["op02_optional_upstream_material_count"] == 3
    assert material["op02_valid_upstream_material_count"] == 3
    assert material["op02_missing_optional_upstream_relation_refs"] == []
    assert material["op02_relation_conflict_refs"] == []
    assert material["rsr_op02_blocker_refs"] == []
    assert material["rsr_op02_ready_for_explicit_local_only_allow_gate"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op02_repairs_when_supplied_upstream_material_has_contract_conflict_or_promotion_claim() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(
        dhr_op09_intake=_rsr_op01_retry_start(),
        alr_op12_result_memo={"schema_version": "invalid", "release_allowed": True},
    )

    assert material["rsr_op02_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_REPAIR_REQUIRED_REF
    assert material["alr_op12_material_present"] is True
    assert material["alr_op12_contract_valid"] is False
    assert "alr_op12_contract_invalid" in material["op02_relation_conflict_refs"]
    assert "upstream_relation_conflict_or_contract_invalid" in material["rsr_op02_blocker_refs"]
    assert "upstream_helper_green_promotion_claim_detected" in material["rsr_op02_blocker_refs"]
    assert material["op02_promotion_claim_ref_count"] > 0
    assert material["rsr_op02_ready_for_explicit_local_only_allow_gate"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_UPSTREAM_RELATION_BEFORE_ALLOW_GATE_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op02_repairs_forbidden_upstream_payload_key_without_leaking_body_value() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(
        dhr_op09_intake=_rsr_op01_retry_start(),
        elr_op19_result_memo={"schema_version": "invalid", "question_text": "this upstream question body must not leak"},
    )

    assert material["rsr_op02_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_REPAIR_REQUIRED_REF
    assert material["op02_forbidden_payload_key_path_count"] > 0
    assert material["op02_body_like_value_path_count"] > 0
    assert "upstream_forbidden_payload_key_detected" in material["rsr_op02_blocker_refs"]
    assert "this upstream question body must not leak" not in repr(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rsr_op02_ready_for_explicit_local_only_allow_gate", False),
        ("rsr_op02_does_not_accept_explicit_local_only_allow", False),
        ("rsr_op02_does_not_run_actual_local_human_review", False),
        ("actual_local_human_review_executed_here", True),
        ("explicit_local_only_allow_receipt_accepted_here", True),
        ("dmd_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF),
    ],
)
def test_rsr_op02_contract_rejects_allow_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _rsr_op02_partial_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(material)


def test_rsr_op03_waits_when_explicit_local_only_allow_receipt_is_missing() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=_rsr_op02_partial_ready(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF
    assert material["op02_contract_valid"] is True
    assert material["op02_ready_for_explicit_local_only_allow_gate"] is True
    assert material["explicit_allow_receipt_present"] is False
    assert material["explicit_allow_receipt_contract_valid"] is False
    assert material["rsr_op03_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF
    assert material["rsr_op03_explicit_allow_missing_waiting"] is True
    assert material["rsr_op03_ready"] is False
    assert material["explicit_local_only_allow_receipt_accepted_by_rsr_op03"] is False
    assert material["explicit_local_only_allow_granted_by_helper"] is False
    assert material["rsr_op03_does_not_generate_body_full_packet"] is True
    assert material["rsr_op03_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op03_blocker_refs"] == []
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op03_accepts_externally_supplied_bodyfree_allow_receipt_without_granting_or_running_review() -> None:
    op02 = _rsr_op02_partial_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=op02,
        explicit_local_only_allow_receipt=_valid_explicit_allow_receipt(op02["review_session_id"]),
    )

    assert material["rsr_op03_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_ACCEPTED_BODYFREE_REF
    assert material["explicit_allow_receipt_present"] is True
    assert material["explicit_allow_receipt_contract_valid"] is True
    assert material["explicit_allow_allowed_case_count"] == 24
    assert material["explicit_allow_allowed_operation_scope_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_REF
    assert material["explicit_allow_local_only_operation_allowed"] is True
    assert material["explicit_allow_body_full_transient_review_allowed"] is True
    assert material["explicit_allow_external_export_allowed"] is False
    assert material["explicit_allow_disposal_purge_required"] is True
    assert material["explicit_allow_forbidden_payload_key_path_refs"] == []
    assert material["explicit_allow_body_like_value_path_refs"] == []
    assert material["explicit_allow_promotion_claim_refs"] == []
    assert material["rsr_op03_explicit_allow_accepted"] is True
    assert material["rsr_op03_ready_for_readiness_blocker_classifier"] is True
    assert material["explicit_local_only_allow_receipt_accepted_by_rsr_op03"] is True
    assert material["explicit_local_only_allow_granted_by_helper"] is False
    assert material["explicit_local_only_allow_receipt_accepted_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op03_blocks_scope_mismatch_before_actual_review_start() -> None:
    op02 = _rsr_op02_partial_ready()
    receipt = _valid_explicit_allow_receipt(op02["review_session_id"])
    receipt["allowed_case_count"] = 23
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=op02,
        explicit_local_only_allow_receipt=receipt,
    )

    assert material["rsr_op03_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_SCOPE_MISMATCH_BLOCKED_REF
    assert material["rsr_op03_explicit_allow_scope_mismatch_blocked"] is True
    assert material["explicit_allow_receipt_contract_valid"] is False
    assert "explicit_local_only_allow_case_count_mismatch" in material["rsr_op03_blocker_refs"]
    assert material["rsr_op03_ready"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_MISMATCH_REF
    assert material["actual_local_human_review_executed_here"] is False
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op03_repairs_body_leaking_allow_receipt_without_leaking_payload_value() -> None:
    op02 = _rsr_op02_partial_ready()
    receipt = _valid_explicit_allow_receipt(op02["review_session_id"])
    receipt["raw_input_included"] = True
    receipt["raw_input"] = "this local review body must never leak"
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=op02,
        explicit_local_only_allow_receipt=receipt,
    )

    assert material["rsr_op03_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert material["rsr_op03_explicit_allow_invalid_repair_required"] is True
    assert material["explicit_allow_forbidden_payload_key_path_count"] > 0
    assert material["explicit_allow_body_like_value_path_count"] > 0
    assert "explicit_local_only_allow_forbidden_payload_key_detected" in material["rsr_op03_blocker_refs"]
    assert "explicit_local_only_allow_raw_input_included_must_be_false" in material["rsr_op03_blocker_refs"]
    assert "this local review body must never leak" not in repr(material)
    assert material["rsr_op03_ready"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op03_repairs_if_op02_is_not_ready_even_with_valid_allow_fixture() -> None:
    op02 = _rsr_op02_partial_ready()
    op02 = deepcopy(op02)
    op02["rsr_op02_ready_for_explicit_local_only_allow_gate"] = False
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=op02,
        explicit_local_only_allow_receipt=_valid_explicit_allow_receipt(op02["review_session_id"]),
    )

    assert material["rsr_op03_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert material["op02_contract_valid"] is False
    assert material["op02_ready_for_explicit_local_only_allow_gate"] is False
    assert "rsr_op02_not_ready_for_allow_gate" in material["rsr_op03_blocker_refs"]
    assert material["explicit_local_only_allow_receipt_accepted_by_rsr_op03"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("explicit_local_only_allow_granted_by_helper", True),
        ("explicit_local_only_allow_receipt_accepted_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_operation_receipt_created_here", True),
        ("dmd_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_rsr_op03_contract_rejects_grant_execution_or_promotion_mutations(field: str, bad_value: object) -> None:
    op02 = _rsr_op02_partial_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=op02,
        explicit_local_only_allow_receipt=_valid_explicit_allow_receipt(op02["review_session_id"]),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(material)


def test_rsr_op02_op03_full_title_aliases_match_canonical_builders() -> None:
    canonical_op02 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(
        dhr_op09_intake=_rsr_op01_retry_start(),
    )
    alias_op02 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_upstream_relationship_verification(
        dhr_op09_intake=_rsr_op01_retry_start(),
    )
    canonical_op03 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=canonical_op02,
    )
    alias_op03 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
        upstream_relationship_verification=canonical_op02,
    )

    assert canonical_op02 == alias_op02
    assert canonical_op03 == alias_op03
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_upstream_relationship_verification_contract(alias_op02) is True
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(alias_op03) is True
