# -*- coding: utf-8 -*-
"""R48 R6/R7 contract tests for P5 Human Blind QA actual review packet work."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import P5_HUMAN_BLIND_QA_RATING_AXES
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION,
    P7_R48_LOCAL_REVIEWER_NOTES_POLICY_SCHEMA_VERSION,
    P7_R48_R6_NEXT_REQUIRED_STEP_REF,
    P7_R48_R6_R7_IMPLEMENTED_STEPS,
    P7_R48_R6_R7_MATERIALIZATION_NOTES_POLICY_FREEZE_SCHEMA_VERSION,
    P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF,
    P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
    P7_R48_REVIEW_KIND,
    P7_R48_REVIEW_PROMPT_VERSION,
    P7_R48_PACKET_KIND,
    assert_p7_r48_body_full_packet_materialization_guard_contract,
    assert_p7_r48_local_reviewer_notes_policy_contract,
    assert_p7_r48_p5_body_full_packet_materialization_request_contract,
    assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract,
    build_p7_r48_body_full_packet_materialization_guard,
    build_p7_r48_local_reviewer_notes_policy,
    build_p7_r48_r6_r7_materialization_notes_policy_freeze,
)

LOCAL_ONLY_CURRENT_SURFACE = "local-only current surface fixture"
LOCAL_ONLY_RETURNED_SURFACE = "local-only returned Emlis surface fixture"
LOCAL_ONLY_HISTORY_SURFACE = "local-only bounded owned history surface fixture"


def _dumped(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _assert_release_closed(payload: dict) -> None:
    for key in (
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
        "full_backend_suite_green_confirmed",
    ):
        assert payload[key] is False


def _minimal_local_only_packet(blind_case_id: str = "p7r48-p5-bqa-s000-001") -> dict:
    return {
        "schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "local_only": True,
        "must_not_export": True,
        "disposal_required": True,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_session_id": "p7_r48_p5_first_formal_review_session",
        "packet_ref_id": "p7r48-p5-packet-s000-001",
        "blind_case_id": blind_case_id,
        "review_prompt_version": P7_R48_REVIEW_PROMPT_VERSION,
        "current_input_review_surface": LOCAL_ONLY_CURRENT_SURFACE,
        "returned_emlis_surface": LOCAL_ONLY_RETURNED_SURFACE,
        "bounded_owned_history_review_surface": LOCAL_ONLY_HISTORY_SURFACE,
        "review_questions": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"],
        "axis_rating_form": {
            "score_min": 0.0,
            "score_max": 1.0,
            "required_axes": list(P5_HUMAN_BLIND_QA_RATING_AXES),
            "free_text_allowed_local_only": True,
        },
    }


def test_r48_r6_default_missing_root_blocks_materialization_without_generating_body() -> None:
    guard = build_p7_r48_body_full_packet_materialization_guard()
    assert_p7_r48_body_full_packet_materialization_guard_contract(guard)

    assert guard["schema_version"] == P7_R48_BODY_FULL_PACKET_MATERIALIZATION_GUARD_SCHEMA_VERSION
    assert guard["policy_section"] == "R6_body_full_packet_materialization_guard"
    assert guard["next_required_step"] == P7_R48_R6_NEXT_REQUIRED_STEP_REF
    assert guard["local_review_root_status"] == "missing"
    assert guard["local_review_root_valid"] is False
    assert guard["explicit_body_full_generation_allow"] is False
    assert guard["body_full_packet_materialization_allowed_by_guard"] is False
    assert guard["local_body_packet_generation_allowed"] is False
    assert "review_packet_generation_blocked_missing_local_root" in guard["body_full_packet_materialization_block_reason_ids"]
    assert guard["root_path_exposed"] is False
    assert guard["local_absolute_path_included"] is False
    assert guard["local_packet_export_allowed"] is False
    assert guard["body_full_packet_zip_inclusion_allowed"] is False
    assert guard["body_free_material_can_include_local_packet_payload"] is False
    assert guard["body_free_material_can_include_body_hash"] is False
    assert guard["body_content_hash_storage_allowed"] is False
    assert guard["body_full_packet_materialized_here"] is False
    assert guard["local_reviewer_payload_materialized_here"] is False
    assert guard["actual_body_full_packet_generated_here"] is False
    assert guard["body_full_writer_created_here"] is False
    assert guard["actual_human_review_run_here"] is False
    assert guard["p5_human_blind_qa_actual_review_start_allowed_after_r6_r7"] is False
    _assert_release_closed(guard)

    dumped = _dumped(guard)
    assert LOCAL_ONLY_CURRENT_SURFACE not in dumped
    assert LOCAL_ONLY_RETURNED_SURFACE not in dumped
    assert LOCAL_ONLY_HISTORY_SURFACE not in dumped


def test_r48_r6_valid_external_root_still_requires_explicit_allow(tmp_path) -> None:
    external_root = tmp_path / "external_local_review_root"
    external_root.mkdir()

    no_allow_guard = build_p7_r48_body_full_packet_materialization_guard(
        local_review_root=str(external_root),
        explicit_body_full_generation_allow=False,
    )
    assert_p7_r48_body_full_packet_materialization_guard_contract(no_allow_guard)
    assert no_allow_guard["local_review_root_status"] == "valid"
    assert no_allow_guard["local_review_root_valid"] is True
    assert no_allow_guard["explicit_body_full_generation_allow"] is False
    assert no_allow_guard["body_full_packet_materialization_allowed_by_guard"] is False
    assert "review_packet_generation_blocked_missing_explicit_allow" in no_allow_guard[
        "body_full_packet_materialization_block_reason_ids"
    ]

    allowed_guard = build_p7_r48_body_full_packet_materialization_guard(
        local_review_root=str(external_root),
        explicit_body_full_generation_allow=True,
    )
    assert_p7_r48_body_full_packet_materialization_guard_contract(allowed_guard)
    assert allowed_guard["local_review_root_status"] == "valid"
    assert allowed_guard["local_review_root_valid"] is True
    assert allowed_guard["explicit_body_full_generation_allow"] is True
    assert allowed_guard["body_full_packet_materialization_allowed_by_guard"] is True
    assert allowed_guard["body_full_packet_materialization_permission_allowed"] is True
    assert allowed_guard["local_body_packet_generation_allowed"] is True
    assert allowed_guard["body_full_packet_materialization_block_reason_ids"] == []
    assert allowed_guard["body_full_packet_materialized_here"] is False
    assert allowed_guard["local_reviewer_payload_materialized_here"] is False
    assert allowed_guard["actual_body_full_packet_generated_here"] is False
    assert allowed_guard["body_full_writer_created_here"] is False
    _assert_release_closed(allowed_guard)


def test_r48_r6_materialization_request_contract_accepts_only_allowed_guard_and_packet_flags(tmp_path) -> None:
    external_root = tmp_path / "external_local_review_root"
    external_root.mkdir()
    allowed_guard = build_p7_r48_body_full_packet_materialization_guard(
        local_review_root=str(external_root),
        explicit_body_full_generation_allow=True,
    )
    blocked_guard = build_p7_r48_body_full_packet_materialization_guard()

    packet = _minimal_local_only_packet()
    assert_p7_r48_p5_body_full_packet_materialization_request_contract(
        packet,
        body_full_packet_materialization_guard=allowed_guard,
    )

    with pytest.raises(ValueError):
        assert_p7_r48_p5_body_full_packet_materialization_request_contract(
            packet,
            body_full_packet_materialization_guard=blocked_guard,
        )

    packet = _minimal_local_only_packet()
    packet["must_not_export"] = False
    with pytest.raises(ValueError):
        assert_p7_r48_p5_body_full_packet_materialization_request_contract(
            packet,
            body_full_packet_materialization_guard=allowed_guard,
        )

    packet = _minimal_local_only_packet()
    packet["case_ref_id"] = "p7r48-p5-case-001"
    with pytest.raises(ValueError):
        assert_p7_r48_p5_body_full_packet_materialization_request_contract(
            packet,
            body_full_packet_materialization_guard=allowed_guard,
        )


def test_r48_r6_guard_contract_rejects_permission_or_export_drift(tmp_path) -> None:
    external_root = tmp_path / "external_local_review_root"
    external_root.mkdir()
    allowed_guard = build_p7_r48_body_full_packet_materialization_guard(
        local_review_root=str(external_root),
        explicit_body_full_generation_allow=True,
    )
    allowed_guard["body_full_packet_materialization_allowed_by_guard"] = False
    with pytest.raises(ValueError):
        assert_p7_r48_body_full_packet_materialization_guard_contract(allowed_guard)

    blocked_guard = build_p7_r48_body_full_packet_materialization_guard()
    blocked_guard["body_full_packet_materialization_block_reason_ids"] = []
    with pytest.raises(ValueError):
        assert_p7_r48_body_full_packet_materialization_guard_contract(blocked_guard)

    blocked_guard = build_p7_r48_body_full_packet_materialization_guard()
    blocked_guard["root_path_exposed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_body_full_packet_materialization_guard_contract(blocked_guard)

    blocked_guard = build_p7_r48_body_full_packet_materialization_guard()
    blocked_guard["body_full_packet_zip_inclusion_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_body_full_packet_materialization_guard_contract(blocked_guard)


def test_r48_r7_local_reviewer_notes_policy_stays_local_only_and_bodyfree() -> None:
    guard = build_p7_r48_body_full_packet_materialization_guard()
    policy = build_p7_r48_local_reviewer_notes_policy(body_full_packet_materialization_guard=guard)
    assert_p7_r48_local_reviewer_notes_policy_contract(policy)

    assert policy["schema_version"] == P7_R48_LOCAL_REVIEWER_NOTES_POLICY_SCHEMA_VERSION
    assert policy["policy_section"] == "R7_local_reviewer_notes_policy"
    assert policy["next_required_step"] == P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF
    assert policy["local_only_notes_policy_fixed"] is True
    assert policy["local_notes_dir_ref"] == "reviewer_notes.local_only"
    assert policy["local_notes_standard_export_allowed"] is False
    assert policy["local_notes_release_material_allowed"] is False
    assert policy["local_notes_p7_scorecard_material_allowed"] is False
    assert policy["direct_note_copy_to_p7_allowed"] is False
    assert policy["raw_quote_to_reason_id_allowed"] is False
    assert policy["reviewer_free_text_included"] is False
    assert policy["reviewer_free_text_material_allowed"] is False
    assert policy["reviewer_free_text_bodyfree_allowed"] is False
    assert policy["body_free_rating_row_reviewer_free_text_included_required_false"] is True
    assert policy["body_free_blocker_row_reviewer_free_text_included_required_false"] is True
    assert policy["sanitized_reason_id_required_for_p7_material"] is True
    assert policy["default_unmapped_reason_id"] == "reason_id_other_local_note_purged"
    assert "reason_id_other_local_note_purged" in policy["sanitized_reason_id_refs"]
    assert "review_packet_generation_blocked_missing_local_root" in policy["execution_blocker_id_refs"]
    assert policy["notes_retention_after_rating_finalized_max_hours"] == P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    assert policy["body_full_packet_retention_max_hours"] == P7_R47_BODY_FULL_PACKET_RETENTION_HOURS
    assert policy["actual_notes_materialized_here"] is False
    assert policy["actual_reviewer_notes_materialized_here"] is False
    assert policy["actual_rating_rows_materialized_here"] is False
    assert policy["actual_body_full_packet_generated_here"] is False
    assert policy["body_full_writer_created_here"] is False
    assert policy["actual_human_review_run_here"] is False
    _assert_release_closed(policy)

    dumped = _dumped(policy)
    assert LOCAL_ONLY_CURRENT_SURFACE not in dumped
    assert LOCAL_ONLY_RETURNED_SURFACE not in dumped
    assert LOCAL_ONLY_HISTORY_SURFACE not in dumped


def test_r48_r7_notes_policy_rejects_export_or_free_text_leak() -> None:
    policy = build_p7_r48_local_reviewer_notes_policy()
    policy["local_notes_standard_export_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_local_reviewer_notes_policy_contract(policy)

    policy = build_p7_r48_local_reviewer_notes_policy()
    policy["reviewer_free_text_included"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_local_reviewer_notes_policy_contract(policy)

    policy = build_p7_r48_local_reviewer_notes_policy()
    policy["default_unmapped_reason_id"] = "raw_quote"
    with pytest.raises(ValueError):
        assert_p7_r48_local_reviewer_notes_policy_contract(policy)

    policy = build_p7_r48_local_reviewer_notes_policy()
    policy["sanitized_reason_id_refs"] = [
        reason_id for reason_id in policy["sanitized_reason_id_refs"] if reason_id != "reason_id_other_local_note_purged"
    ]
    with pytest.raises(ValueError):
        assert_p7_r48_local_reviewer_notes_policy_contract(policy)


def test_r48_r6_r7_combined_freeze_points_to_r8_and_keeps_review_release_closed(tmp_path) -> None:
    external_root = tmp_path / "external_local_review_root"
    external_root.mkdir()
    freeze = build_p7_r48_r6_r7_materialization_notes_policy_freeze(
        local_review_root=str(external_root),
        explicit_body_full_generation_allow=True,
    )
    assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R48_R6_R7_MATERIALIZATION_NOTES_POLICY_FREEZE_SCHEMA_VERSION
    assert freeze["implemented_steps"] == list(P7_R48_R6_R7_IMPLEMENTED_STEPS)
    assert freeze["not_yet_implemented_steps"] == list(P7_R48_R6_R7_NOT_YET_IMPLEMENTED_STEPS)
    assert freeze["next_required_step"] == P7_R48_R6_R7_NEXT_REQUIRED_STEP_REF
    assert freeze["packet_kind"] == P7_R48_PACKET_KIND
    assert freeze["review_kind"] == P7_R48_REVIEW_KIND
    assert freeze["case_count"] == 24
    assert freeze["minimums_satisfied"] is True
    assert freeze["r0_current_source_r47_handoff_hold_refrozen"] is True
    assert freeze["r1_scope_schema_packet_kind_fixed"] is True
    assert freeze["local_storage_root_policy_connected"] is True
    assert freeze["p5_24_case_first_formal_review_matrix_built"] is True
    assert freeze["blind_case_id_case_ref_separated"] is True
    assert freeze["reviewer_facing_local_packet_schema_fixed"] is True
    assert freeze["body_full_packet_materialization_guard_ready"] is True
    assert freeze["local_reviewer_notes_policy_fixed"] is True
    assert freeze["reviewer_notes_local_only_policy_fixed"] is True
    assert freeze["body_full_packet_materialization_allowed_by_guard"] is True
    assert freeze["body_free_case_matrix_ready"] is True
    assert freeze["actual_case_matrix_materialized_here"] is True
    assert freeze["body_full_packet_materialized_here"] is False
    assert freeze["local_reviewer_payload_materialized_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_rating_rows_materialized_here"] is False
    assert freeze["actual_reviewer_notes_materialized_here"] is False
    assert freeze["actual_disposal_receipt_materialized_here"] is False
    assert freeze["p5_human_blind_qa_actual_review_start_allowed_after_r6_r7"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    _assert_release_closed(freeze)


def test_r48_r6_r7_rejects_body_payload_inputs_and_release_promotion() -> None:
    guard = build_p7_r48_body_full_packet_materialization_guard()
    guard["reviewer_free_text"] = "must remain local-only"
    with pytest.raises(ValueError):
        build_p7_r48_local_reviewer_notes_policy(body_full_packet_materialization_guard=guard)

    freeze = build_p7_r48_r6_r7_materialization_notes_policy_freeze()
    freeze["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(freeze)

    freeze = build_p7_r48_r6_r7_materialization_notes_policy_freeze()
    freeze["actual_reviewer_notes_materialized_here"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(freeze)
