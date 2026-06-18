# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_next_decision_handoff_ledger import (
    BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT,
    build_p7_r46_next_decision_handoff_ledger,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION,
    P7_R47_FIRST_NEXT_WORK_REF,
    P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION,
    P7_R47_LOCAL_REVIEW_PACKET_SCOPE,
    P7_R47_LOCAL_REVIEW_PACKET_STEP,
    P7_R47_NEXT_REQUIRED_STEP_REF,
    P7_R47_PACKET_KINDS,
    P7_R47_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION,
    P7_R47_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION,
    assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract,
    assert_p7_r47_r0_r1_scope_freeze_contract,
    assert_p7_r47_scope_schema_packet_kind_freeze_contract,
    build_p7_r47_current_source_r46_handoff_hold_refreeze,
    build_p7_r47_r0_r1_scope_freeze,
    build_p7_r47_scope_schema_packet_kind_freeze,
)

SECRET_INPUT = "R47 R0/R1 secret raw input must not enter body-free material"
SECRET_SURFACE = "R47 R0/R1 secret Emlis surface must not enter body-free material"
SECRET_REVIEWER = "R47 R0/R1 reviewer free text must not enter body-free material"


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
    assert '"reviewer_free_text":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def test_r47_r0_refreezes_current_source_r46_branch_a_and_unresolved_holds_only() -> None:
    refreeze = build_p7_r47_current_source_r46_handoff_hold_refreeze()
    assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract(refreeze)

    assert refreeze["schema_version"] == P7_R47_CURRENT_SOURCE_REFREEZE_SCHEMA_VERSION
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == P7_R47_LOCAL_REVIEW_PACKET_STEP
    assert refreeze["scope"] == P7_R47_LOCAL_REVIEW_PACKET_SCOPE
    assert refreeze["current_phase"] == "P7"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True

    r46 = refreeze["r46_handoff"]
    assert r46["active_decision_branch"] == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT
    assert r46["next_order_first"] == P7_R47_FIRST_NEXT_WORK_REF
    assert r46["display_contract_green_confirmed"] is True
    assert r46["public_lineage_consistency_confirmed"] is True
    assert r46["p5_human_blind_qa_path_open_from_r46"] is True
    assert r46["p5_human_blind_qa_confirmed"] is False
    assert r46["p6_limited_human_readfeel_path_open_from_r46"] is False
    assert r46["p6_limited_human_readfeel_confirmed"] is False

    hold = refreeze["hold_state"]
    assert "P7-HOLD-004" in hold["unresolved_hold_refs"]
    assert "HOLD-DC-005" in hold["unresolved_hold_refs"]
    assert hold["local_review_packet_policy_ready"] is False
    assert hold["body_full_review_packet_generated"] is False
    assert refreeze["r0_current_source_handoff_hold_refrozen"] is True
    assert refreeze["r1_scope_packet_kind_enum_fixed"] is False
    assert refreeze["release_allowed"] is False
    assert refreeze["p7_complete"] is False
    assert refreeze["p8_start_allowed"] is False
    assert refreeze["hold004_close_allowed"] is False
    assert refreeze["local_review_packet_policy_ready"] is False
    assert refreeze["p5_human_blind_qa_start_allowed_after_r0_r1"] is False

    _assert_no_body_or_release_promotion(refreeze)


def test_r47_r1_fixes_scope_schema_versions_and_packet_kind_enum_without_policy_completion() -> None:
    freeze = build_p7_r47_scope_schema_packet_kind_freeze()
    assert_p7_r47_scope_schema_packet_kind_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R47_SCOPE_SCHEMA_PACKET_KIND_FREEZE_SCHEMA_VERSION
    assert freeze["policy_schema_version"] == P7_R47_LOCAL_REVIEW_PACKET_POLICY_SCHEMA_VERSION
    assert freeze["step"] == P7_R47_LOCAL_REVIEW_PACKET_STEP
    assert freeze["scope"] == P7_R47_LOCAL_REVIEW_PACKET_SCOPE
    assert freeze["r47_scope_fixed"] is True
    assert freeze["r47_schema_version_fixed"] is True
    assert freeze["packet_kind_enum_fixed"] is True
    assert tuple(freeze["packet_kind_enum"]) == P7_R47_PACKET_KINDS
    assert freeze["packet_kind_count"] == 3
    assert freeze["first_next_work_ref"] == P7_R47_FIRST_NEXT_WORK_REF
    assert freeze["next_required_step"] == P7_R47_NEXT_REQUIRED_STEP_REF
    assert freeze["r0_current_source_handoff_hold_refrozen"] is True
    assert freeze["r1_scope_packet_kind_enum_fixed"] is True

    assert freeze["policy_ready"] is False
    assert freeze["r47_policy_ready"] is False
    assert freeze["local_review_packet_policy_ready"] is False
    assert freeze["local_review_packet_storage_policy_fixed"] is False
    assert freeze["local_body_packet_generation_allowed"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["p5_human_blind_qa_start_allowed_after_r0_r1"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False

    for index, policy in enumerate(freeze["packet_kind_policies"]):
        assert policy["packet_kind"] == P7_R47_PACKET_KINDS[index]
        assert policy["local_only_required_later"] is True
        assert policy["body_full_payload_required_later"] is True
        assert policy["body_free_result_required_later"] is True
        assert policy["materialized_here"] is False
        assert policy["writer_created_here"] is False
        assert policy["standard_export_allowed"] is False
        assert policy["public_meta_material_allowed"] is False
        assert policy["p7_scorecard_material_allowed"] is False
        assert policy["release_material_allowed"] is False

    _assert_no_body_or_release_promotion(freeze)


def test_r47_r0_r1_combined_scope_freeze_is_body_free_and_points_to_r2_next() -> None:
    combined = build_p7_r47_r0_r1_scope_freeze()
    assert_p7_r47_r0_r1_scope_freeze_contract(combined)

    assert combined["schema_version"] == P7_R47_R0_R1_SCOPE_FREEZE_SCHEMA_VERSION
    assert combined["first_next_work_ref"] == P7_R47_FIRST_NEXT_WORK_REF
    assert combined["next_required_step"] == P7_R47_NEXT_REQUIRED_STEP_REF
    assert tuple(combined["packet_kind_enum"]) == P7_R47_PACKET_KINDS
    assert combined["r0_current_source_handoff_hold_refrozen"] is True
    assert combined["r1_scope_packet_kind_enum_fixed"] is True
    assert combined["local_review_packet_policy_ready"] is False
    assert combined["p5_human_blind_qa_start_allowed_after_r0_r1"] is False
    assert combined["release_allowed"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["hold004_close_allowed"] is False

    _assert_no_body_or_release_promotion(combined)


def test_r47_r0_rejects_non_branch_a_r46_handoff() -> None:
    branch_b_ledger = build_p7_r46_next_decision_handoff_ledger(
        display_contract_status={"display_contract_green": True, "public_lineage_consistent": False}
    )
    with pytest.raises(ValueError):
        build_p7_r47_current_source_r46_handoff_hold_refreeze(r46_next_decision_ledger=branch_b_ledger)


def test_r47_r1_rejects_packet_kind_enum_drift() -> None:
    with pytest.raises(ValueError):
        build_p7_r47_scope_schema_packet_kind_freeze(
            packet_kinds=(
                "p5_human_blind_qa_local_review_packet",
                "real_device_modal_review_local_packet",
            )
        )

    with pytest.raises(ValueError):
        build_p7_r47_scope_schema_packet_kind_freeze(
            packet_kinds=(
                "p5_human_blind_qa_local_review_packet",
                "p6_limited_human_readfeel_local_review_packet",
                "unexpected_review_packet_kind",
            )
        )


def test_r47_r0_r1_builders_reject_body_payload_or_contract_mutation_inputs() -> None:
    with pytest.raises(ValueError):
        build_p7_r47_current_source_r46_handoff_hold_refreeze(
            snapshot_refs={"raw_input": SECRET_INPUT}
        )

    r0 = build_p7_r47_current_source_r46_handoff_hold_refreeze()
    r0["reviewer_free_text"] = SECRET_REVIEWER
    with pytest.raises(ValueError):
        build_p7_r47_scope_schema_packet_kind_freeze(current_source_refreeze=r0)

    with pytest.raises(ValueError):
        build_p7_r47_r0_r1_scope_freeze(snapshot_refs={"public_response_key_added": True})


def test_r47_r0_r1_contracts_reject_false_completion_or_review_promotion() -> None:
    refreeze = build_p7_r47_current_source_r46_handoff_hold_refreeze()
    refreeze["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_current_source_r46_handoff_hold_refreeze_contract(refreeze)

    freeze = build_p7_r47_scope_schema_packet_kind_freeze()
    freeze["p5_human_blind_qa_start_allowed_after_r0_r1"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_scope_schema_packet_kind_freeze_contract(freeze)

    combined = build_p7_r47_r0_r1_scope_freeze()
    combined["body_full_writer_created_here"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_r0_r1_scope_freeze_contract(combined)
