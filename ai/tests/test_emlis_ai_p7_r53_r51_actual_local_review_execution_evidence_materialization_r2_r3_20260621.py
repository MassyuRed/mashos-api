# -*- coding: utf-8 -*-
"""P7-R53 R2/R3 tests for validation preflight and R51 current snapshot adoption."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    for key in r53.P7_R53_R0_R1_FALSE_KEY_REFS:
        assert material[key] is False, key
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False


@lru_cache(maxsize=1)
def _cached_r53_r2_blocked() -> tuple[dict[str, object]]:
    preflight = r53.build_p7_r53_validation_evidence_r49_timeout_preflight()
    assert r53.assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(preflight) is True
    return (preflight,)


def _r53_r2_blocked() -> dict[str, object]:
    return deepcopy(_cached_r53_r2_blocked()[0])


@lru_cache(maxsize=1)
def _cached_r53_r2_green_override() -> tuple[dict[str, object]]:
    preflight = r53.build_p7_r53_validation_evidence_r49_timeout_preflight(
        validation_evidence_overrides={
            "r49_split_matrix": {
                "evidence_status_ref": "PASSED_BY_R53_CURRENT_SPLIT_EXECUTION",
                "evidence_present": True,
                "passed_count": 76,
                "test_file_refs": r53.P7_R53_R49_SPLIT_MATRIX_TEST_FILE_REFS,
                "evidence_source_ref": "R53_current_session_split_green_bodyfree_evidence",
                "claim_boundary_ref": "R49 split matrix green only; wildcard bulk green is not claimed",
            }
        }
    )
    assert r53.assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(preflight) is True
    return (preflight,)


def _r53_r2_green_override() -> dict[str, object]:
    return deepcopy(_cached_r53_r2_green_override()[0])


@lru_cache(maxsize=1)
def _cached_r53_r3_blocked() -> tuple[dict[str, object]]:
    adoption = r53.build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override(
        validation_evidence_preflight=_r53_r2_blocked(),
    )
    assert r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption) is True
    return (adoption,)


def _r53_r3_blocked() -> dict[str, object]:
    return deepcopy(_cached_r53_r3_blocked()[0])


@lru_cache(maxsize=1)
def _cached_r53_r3_green_override() -> tuple[dict[str, object]]:
    adoption = r53.build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override(
        validation_evidence_preflight=_r53_r2_green_override(),
    )
    assert r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption) is True
    return (adoption,)


def _r53_r3_green_override() -> dict[str, object]:
    return deepcopy(_cached_r53_r3_green_override()[0])


def test_r53_r2_freezes_validation_preflight_without_claiming_r49_timeout_or_collect_only_as_green() -> None:
    preflight = _r53_r2_blocked()

    assert preflight["schema_version"] == r53.P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_SCHEMA_VERSION
    assert set(preflight) == set(r53.P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert preflight["phase"].startswith("P7_")
    assert preflight["step"] == r53.P7_R53_STEP
    assert preflight["scope"] == r53.P7_R53_SCOPE
    assert preflight["policy_section"] == "R53-2_r49_timeout_validation_evidence_preflight"
    assert preflight["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert preflight["r51_helper_source_snapshot_refs"] == r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert preflight["r51_helper_refs_are_current_received_refs"] is False
    assert preflight["r52_helper_refs_are_current_received_refs"] is False

    assert tuple(preflight["validation_evidence_group_refs"]) == r53.P7_R53_VALIDATION_EVIDENCE_GROUP_REFS
    assert tuple(preflight["validation_evidence_required_group_refs"]) == r53.P7_R53_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS
    assert preflight["validation_evidence_row_count"] == len(r53.P7_R53_VALIDATION_EVIDENCE_GROUP_REFS)
    assert [row["evidence_group_ref"] for row in preflight["validation_evidence_rows"]] == list(
        r53.P7_R53_VALIDATION_EVIDENCE_GROUP_REFS
    )
    for row in preflight["validation_evidence_rows"]:
        assert r53.assert_p7_r53_validation_evidence_row_contract(row) is True
        assert row["body_free"] is True
        assert row["evidence_created_here"] is False
        assert row["validation_commands_executed_here"] is False
        assert row["command_result_body_stored_here"] is False
        assert row["terminal_output_stored_here"] is False

    assert preflight["r50_target_green_evidence_present"] is True
    assert preflight["r51_target_green_evidence_present"] is True
    assert preflight["r52_target_green_evidence_present"] is True
    assert preflight["r49_split_matrix_green_evidence_present"] is False
    assert preflight["r49_split_matrix_green_required_for_actual_review_preflight"] is True
    assert preflight["r49_wildcard_bulk_timeout_unclassified"] is True
    assert preflight["r49_wildcard_green_claim_allowed"] is False
    assert preflight["r49_wildcard_green_claimed"] is False
    assert preflight["r49_wildcard_bulk_required_for_actual_review_preflight"] is False
    assert preflight["backend_collect_only_evidence_present"] is True
    assert preflight["full_backend_suite_green_confirmed"] is False
    assert preflight["backend_collect_only_claimed_as_full_backend_green"] is False
    assert preflight["rn_contract_claimed_as_real_device_modal_readfeel"] is False

    assert preflight["preflight_status"] == "BLOCKED"
    assert preflight["validation_evidence_ready_for_r51_2_preflight"] is False
    assert preflight["execution_blocker_ids"] == ["r53_missing_r49_split_green_evidence"]
    assert preflight["r51_2_local_root_preflight_allowed_after_r53_2"] is False
    assert preflight["r51_r0_r1_adoption_with_current_snapshot_override_allowed"] is True
    assert preflight["actual_review_generation_allowed_after_r53_2"] is False
    assert preflight["body_full_packet_generation_allowed_after_r53_2"] is False
    assert tuple(preflight["implemented_steps"]) == r53.P7_R53_R2_IMPLEMENTED_STEPS
    assert tuple(preflight["not_yet_implemented_steps"]) == r53.P7_R53_R2_NOT_YET_IMPLEMENTED_STEPS
    assert preflight["next_required_step"] == r53.P7_R53_R2_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(preflight)


def test_r53_r2_can_accept_split_green_evidence_override_without_wildcard_green_claim() -> None:
    preflight = _r53_r2_green_override()

    assert preflight["preflight_status"] == "PASSED"
    assert preflight["validation_evidence_required_groups_present"] is True
    assert preflight["validation_evidence_ready_for_r51_2_preflight"] is True
    assert preflight["execution_blocker_ids"] == []
    assert preflight["r49_split_matrix_green_evidence_present"] is True
    assert preflight["r49_wildcard_bulk_timeout_unclassified"] is True
    assert preflight["r49_wildcard_green_claim_allowed"] is False
    assert preflight["r49_wildcard_green_claimed"] is False
    assert preflight["full_backend_suite_green_confirmed"] is False
    assert preflight["backend_collect_only_claimed_as_full_backend_green"] is False
    assert preflight["r51_2_local_root_preflight_allowed_after_r53_2"] is True
    assert preflight["actual_review_generation_allowed_after_r53_2"] is False
    assert preflight["body_full_packet_generation_allowed_after_r53_2"] is False

    split_row = next(row for row in preflight["validation_evidence_rows"] if row["evidence_group_ref"] == "r49_split_matrix")
    wildcard_row = next(row for row in preflight["validation_evidence_rows"] if row["evidence_group_ref"] == "r49_wildcard_bulk")
    assert split_row["evidence_present"] is True
    assert split_row["timeout_unclassified"] is False
    assert wildcard_row["evidence_status_ref"] == "TIMEOUT_UNCLASSIFIED"
    assert wildcard_row["timeout_unclassified"] is True
    assert wildcard_row["required_for_actual_review_preflight"] is False

    _assert_body_free_no_promotion(preflight)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r49_wildcard_green_claim_allowed", True),
        ("r49_wildcard_green_claimed", True),
        ("r49_wildcard_bulk_required_for_actual_review_preflight", True),
        ("full_backend_suite_green_confirmed", True),
        ("backend_collect_only_claimed_as_full_backend_green", True),
        ("rn_contract_claimed_as_real_device_modal_readfeel", True),
        ("actual_review_generation_allowed_after_r53_2", True),
        ("body_full_packet_generation_allowed_after_r53_2", True),
        ("validation_commands_executed_here", True),
        ("command_result_body_stored_here", True),
        ("terminal_output_stored_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
    ],
)
def test_r53_r2_rejects_timeout_green_claim_collect_only_promotion_body_generation_or_public_contract_drift(
    key: str,
    value: object,
) -> None:
    preflight = _r53_r2_blocked()
    preflight[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(preflight)


def test_r53_r2_rejects_validation_rows_relabelled_to_hide_wildcard_timeout_or_split_gap() -> None:
    preflight = _r53_r2_blocked()
    wildcard = next(row for row in preflight["validation_evidence_rows"] if row["evidence_group_ref"] == "r49_wildcard_bulk")
    wildcard["timeout_unclassified"] = False
    with pytest.raises(ValueError):
        r53.assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(preflight)

    preflight = _r53_r2_blocked()
    split = next(row for row in preflight["validation_evidence_rows"] if row["evidence_group_ref"] == "r49_split_matrix")
    split["evidence_present"] = True
    preflight["r49_split_matrix_green_evidence_present"] = False
    with pytest.raises(ValueError):
        r53.assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(preflight)


def test_r53_r3_adopts_r51_r0_current_snapshot_override_but_blocks_r51_2_when_split_green_is_missing() -> None:
    adoption = _r53_r3_blocked()

    assert adoption["schema_version"] == r53.P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_SCHEMA_VERSION
    assert set(adoption) == set(r53.P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_REQUIRED_FIELD_REFS)
    assert adoption["phase"].startswith("P7_")
    assert adoption["step"] == r53.P7_R53_STEP
    assert adoption["scope"] == r53.P7_R53_SCOPE
    assert adoption["policy_section"] == "R53-3_r51_r0_r1_adoption_with_current_snapshot_override"
    assert adoption["r2_preflight_status"] == "BLOCKED"
    assert adoption["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert adoption["r51_default_source_snapshot_refs"] == r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert adoption["r51_r0_source_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert adoption["r51_r0_source_snapshot_refs"] != r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert adoption["r51_r0_uses_r53_current_snapshot_refs"] is True
    assert adoption["r51_r0_uses_r51_default_source_refs"] is False
    assert adoption["r51_default_source_refs_allowed_as_actual_review_basis"] is False
    assert adoption["r51_r0_current_snapshot_override_applied"] is True

    assert adoption["r51_r1_validation_evidence_required_groups_present"] is False
    assert adoption["r51_r1_r49_split_matrix_green_evidence_present"] is False
    assert adoption["r51_r1_r49_wildcard_bulk_timeout_unclassified"] is True
    assert adoption["r51_r1_r49_wildcard_green_claim_allowed"] is False
    assert adoption["r51_r1_full_backend_suite_green_confirmed"] is False
    assert adoption["r51_r1_collect_only_claimed_as_full_backend_green"] is False
    assert adoption["r51_r1_validation_evidence_ready_for_r51_2_preflight"] is False
    assert adoption["r51_r1_execution_blocker_ids"] == ["r51_missing_r49_split_green_evidence"]
    assert adoption["r51_r1_next_required_step"] == r51.P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert adoption["adoption_status"] == "ADOPTED_BLOCKED_BY_VALIDATION_EVIDENCE"
    assert adoption["r51_2_local_root_preflight_allowed_after_r53_3"] is False
    assert adoption["body_full_packet_generation_allowed_after_r53_3"] is False
    assert adoption["actual_review_generation_allowed_after_r53_3"] is False
    assert adoption["next_required_step"] == r53.P7_R53_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(adoption["implemented_steps"]) == r53.P7_R53_R3_IMPLEMENTED_STEPS
    assert tuple(adoption["not_yet_implemented_steps"]) == r53.P7_R53_R3_NOT_YET_IMPLEMENTED_STEPS

    _assert_body_free_no_promotion(adoption)


def test_r53_r3_green_preflight_adopts_r51_r0_r1_ready_without_running_review_or_generating_body_full() -> None:
    adoption = _r53_r3_green_override()

    assert adoption["r2_preflight_status"] == "PASSED"
    assert adoption["r51_r0_source_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert adoption["r51_r0_uses_r53_current_snapshot_refs"] is True
    assert adoption["r51_r0_uses_r51_default_source_refs"] is False
    assert adoption["r51_r1_validation_evidence_required_groups_present"] is True
    assert adoption["r51_r1_r49_split_matrix_green_evidence_present"] is True
    assert adoption["r51_r1_r49_wildcard_bulk_timeout_unclassified"] is True
    assert adoption["r51_r1_r49_wildcard_green_claim_allowed"] is False
    assert adoption["r51_r1_validation_evidence_ready_for_r51_2_preflight"] is True
    assert adoption["r51_r1_execution_blocker_ids"] == []
    assert adoption["r51_r1_next_required_step"] == r51.P7_R51_R1_NEXT_REQUIRED_STEP_REF
    assert adoption["adoption_status"] == "ADOPTED_READY_FOR_R53_4_PREFLIGHT"
    assert adoption["r51_2_local_root_preflight_allowed_after_r53_3"] is True
    assert adoption["body_full_packet_generation_allowed_after_r53_3"] is False
    assert adoption["actual_review_generation_allowed_after_r53_3"] is False
    assert adoption["next_required_step"] == r53.P7_R53_R3_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(adoption)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r51_r0_uses_r53_current_snapshot_refs", False),
        ("r51_r0_uses_r51_default_source_refs", True),
        ("r51_default_source_refs_allowed_as_actual_review_basis", True),
        ("r51_r0_current_snapshot_override_applied", False),
        ("r51_r1_r49_wildcard_green_claim_allowed", True),
        ("r51_r1_full_backend_suite_green_confirmed", True),
        ("r51_r1_collect_only_claimed_as_full_backend_green", True),
        ("body_full_packet_generation_allowed_after_r53_3", True),
        ("actual_review_generation_allowed_after_r53_3", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r3_rejects_old_snapshot_basis_validation_misclaim_body_generation_or_release_promotion(
    key: str,
    value: object,
) -> None:
    adoption = _r53_r3_blocked()
    adoption[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption)


def test_r53_r3_rejects_r51_r0_source_refs_reverted_to_r51_default_snapshot() -> None:
    adoption = _r53_r3_blocked()
    adoption["r51_r0_source_snapshot_refs"] = dict(r51.P7_R51_SOURCE_SNAPSHOT_REFS)
    adoption["r51_r0_uses_r53_current_snapshot_refs"] = False
    adoption["r51_r0_uses_r51_default_source_refs"] = True
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption)


def test_r53_r3_rejects_ready_status_when_r51_validation_blockers_remain_visible() -> None:
    adoption = _r53_r3_blocked()
    adoption["r51_r1_validation_evidence_ready_for_r51_2_preflight"] = True
    adoption["adoption_status"] = "ADOPTED_READY_FOR_R53_4_PREFLIGHT"
    adoption["r51_2_local_root_preflight_allowed_after_r53_3"] = True
    adoption["r51_r1_next_required_step"] = r51.P7_R51_R1_NEXT_REQUIRED_STEP_REF
    adoption["next_required_step"] = r53.P7_R53_R3_NEXT_REQUIRED_STEP_REF
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption)
