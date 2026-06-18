# -*- coding: utf-8 -*-
"""R48 R2/R3 contract tests for P5 Human Blind QA actual review packet work."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r47_local_review_packet_policy import P7_R47_P5_FIRST_FORMAL_MINIMUMS
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_EXPLICIT_ALLOW_BLOCK_REASON_REF,
    P7_R48_LOCAL_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
    P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS,
    P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
    P7_R48_PACKET_KIND,
    P7_R48_R2_R3_IMPLEMENTED_STEPS,
    P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION,
    P7_R48_R2_R3_NEXT_REQUIRED_STEP_REF,
    P7_R48_R2_R3_NOT_YET_IMPLEMENTED_STEPS,
    P7_R48_REVIEW_KIND,
    P7_R48_REVIEW_PROMPT_VERSION,
    assert_p7_r48_local_storage_root_policy_contract,
    assert_p7_r48_p5_first_formal_review_case_matrix_contract,
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract,
    build_p7_r48_local_storage_root_policy,
    build_p7_r48_p5_first_formal_review_case_matrix,
    build_p7_r48_r0_r1_scope_freeze,
    build_p7_r48_r2_r3_local_storage_case_matrix_freeze,
)

SECRET_INPUT = "これは成果物に残してはいけない入力本文です"
SECRET_REVIEWER_NOTE = "reviewer free text must stay local-only"


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


def test_r48_r2_local_storage_policy_blocks_missing_root_without_body_full_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COCOLON_EMLIS_LOCAL_REVIEW_ROOT", raising=False)

    policy = build_p7_r48_local_storage_root_policy()
    assert_p7_r48_local_storage_root_policy_contract(policy)

    assert policy["schema_version"] == P7_R48_LOCAL_STORAGE_ROOT_POLICY_SCHEMA_VERSION
    assert policy["policy_section"] == "R2_local_storage_root_policy"
    assert policy["env_var"] == "COCOLON_EMLIS_LOCAL_REVIEW_ROOT"
    assert policy["storage_mode"] == "external_local_only"
    assert policy["local_review_root_source"] == "missing"
    assert policy["local_review_root_configured"] is False
    assert policy["local_review_root_status"] == "missing"
    assert policy["local_review_root_valid"] is False
    assert policy["root_path_exposed"] is False
    assert policy["local_absolute_path_included"] is False
    assert policy["body_full_generation_requires_env_root"] is True
    assert policy["body_full_generation_requires_explicit_allow"] is True
    assert policy["explicit_body_full_generation_allow"] is False
    assert policy["local_body_packet_generation_allowed"] is False
    assert policy["body_full_generation_allowed_after_r2"] is False
    assert "review_packet_generation_blocked_missing_local_root" in policy["generation_block_reason_ids"]

    assert policy["body_free_case_matrix_ready"] is False
    assert policy["actual_case_matrix_materialized_here"] is False
    assert policy["actual_body_full_packet_generated_here"] is False
    assert policy["body_full_writer_created_here"] is False
    assert policy["actual_human_review_run_here"] is False
    assert policy["p5_human_blind_qa_actual_review_start_allowed_after_r2"] is False
    assert policy["p5_human_blind_qa_confirmed"] is False
    _assert_release_closed(policy)

    dumped = _dumped(policy)
    assert SECRET_INPUT not in dumped
    assert "local_review_root_path" not in policy
    assert "absolute_path" not in policy
    assert "local_absolute_path" not in policy


def test_r48_r2_rejects_artifact_or_repo_like_roots_as_invalid() -> None:
    policy = build_p7_r48_local_storage_root_policy(local_review_root="/mnt/data/r48-local-review-root")
    assert_p7_r48_local_storage_root_policy_contract(policy)

    assert policy["local_review_root_status"] == "invalid"
    assert policy["local_root_body_packet_generation_allowed_by_root_policy"] is False
    assert policy["local_body_packet_generation_allowed"] is False
    assert "review_packet_generation_blocked_invalid_local_root" in policy["generation_block_reason_ids"]
    assert "review_packet_generation_blocked_repo_or_artifact_root" in policy["generation_block_reason_ids"]
    assert policy["actual_body_full_packet_generated_here"] is False
    assert policy["body_full_writer_created_here"] is False
    _assert_release_closed(policy)


def test_r48_r2_valid_external_root_still_requires_explicit_allow(tmp_path) -> None:
    local_root = tmp_path / "external-local-review-root"

    blocked = build_p7_r48_local_storage_root_policy(local_review_root=str(local_root))
    assert_p7_r48_local_storage_root_policy_contract(blocked)
    assert blocked["local_review_root_status"] == "valid"
    assert blocked["local_review_root_valid"] is True
    assert blocked["local_root_body_packet_generation_allowed_by_root_policy"] is True
    assert blocked["explicit_body_full_generation_allow"] is False
    assert blocked["local_body_packet_generation_allowed"] is False
    assert P7_R48_EXPLICIT_ALLOW_BLOCK_REASON_REF in blocked["generation_block_reason_ids"]
    assert blocked["actual_body_full_packet_generated_here"] is False

    allowed = build_p7_r48_local_storage_root_policy(
        local_review_root=str(local_root),
        explicit_body_full_generation_allow=True,
    )
    assert_p7_r48_local_storage_root_policy_contract(allowed)
    assert allowed["local_review_root_status"] == "valid"
    assert allowed["explicit_body_full_generation_allow"] is True
    assert allowed["local_body_packet_generation_allowed"] is True
    assert allowed["body_full_generation_allowed_after_r2"] is True
    assert allowed["generation_block_reason_ids"] == []
    assert allowed["actual_body_full_packet_generated_here"] is False
    assert allowed["body_full_writer_created_here"] is False
    _assert_release_closed(allowed)


def test_r48_r3_builds_body_free_24_case_first_formal_matrix() -> None:
    matrix = build_p7_r48_p5_first_formal_review_case_matrix(session_short_ref="s024")
    assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)

    assert matrix["schema_version"] == P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert matrix["packet_kind"] == P7_R48_PACKET_KIND
    assert matrix["review_kind"] == P7_R48_REVIEW_KIND
    assert matrix["review_prompt_version"] == P7_R48_REVIEW_PROMPT_VERSION
    assert matrix["case_count"] == 24
    assert len(matrix["case_rows"]) == 24
    assert matrix["minimums_satisfied"] is True
    assert matrix["body_free_case_matrix_ready"] is True
    assert matrix["actual_case_matrix_materialized_here"] is True
    assert matrix["body_full_packet_materialized_here"] is False
    assert matrix["local_reviewer_payload_materialized_here"] is False
    assert matrix["actual_body_full_packet_generated_here"] is False
    assert matrix["actual_human_review_run_here"] is False
    assert matrix["p5_human_blind_qa_actual_review_start_allowed_after_r2_r3"] is False
    _assert_release_closed(matrix)

    family_counts = matrix["family_case_counts"]
    assert family_counts["history_line_eligible_input"] == 4
    assert family_counts["standard_state_answer_owned_history"] == 4
    assert family_counts["self_understanding_owned_history"] == 3
    assert family_counts["uncertainty_support_owned_history"] == 3
    assert family_counts["change_future_intention_owned_history"] == 3
    assert family_counts["relationship_gratitude_recovery_owned_history"] == 3
    assert family_counts["low_information_history_not_eligible"] == 2
    assert family_counts["free_tier_history_present_not_allowed"] == 2
    assert matrix["owned_history_positive_case_count"] >= P7_R47_P5_FIRST_FORMAL_MINIMUMS["minimum_owned_history_positive_cases"]

    blind_ids = {row["blind_case_id"] for row in matrix["case_rows"]}
    case_refs = {row["case_ref_id"] for row in matrix["case_rows"]}
    packet_refs = {row["packet_ref_id"] for row in matrix["case_rows"]}
    assert len(blind_ids) == 24
    assert len(case_refs) == 24
    assert len(packet_refs) == 24

    for row in matrix["case_rows"]:
        assert set(row) == set(P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS)
        assert row["body_free"] is True
        assert row["controller_only"] is True
        assert row["reviewer_facing_family_exposed"] is False
        assert row["reviewer_facing_tier_exposed"] is False
        assert row["body_full_packet_materialized_here"] is False
        assert row["local_reviewer_payload_materialized_here"] is False
        assert row["family"].replace("_", "-") not in row["blind_case_id"]
        assert row["subscription_tier_ref"] not in row["blind_case_id"]
        if row["family"] == "free_tier_history_present_not_allowed":
            assert row["subscription_tier_ref"] == "free"
        else:
            assert row["subscription_tier_ref"] in {"plus", "premium"}

    dumped = _dumped(matrix)
    assert SECRET_INPUT not in dumped
    assert "current_input_review_surface" not in dumped
    assert "returned_emlis_surface" not in dumped
    assert "bounded_owned_history_review_surface" not in dumped
    assert '"reviewer_free_text":' not in dumped


def test_r48_r3_case_matrix_contract_rejects_body_payload_leak_and_blind_id_leak() -> None:
    matrix = build_p7_r48_p5_first_formal_review_case_matrix()
    matrix["case_rows"][0]["raw_input"] = SECRET_INPUT
    with pytest.raises(ValueError):
        assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)

    matrix = build_p7_r48_p5_first_formal_review_case_matrix()
    matrix["case_rows"][0]["blind_case_id"] = "p7r48-p5-bqa-history-line-eligible-001"
    with pytest.raises(ValueError):
        assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)

    matrix = build_p7_r48_p5_first_formal_review_case_matrix()
    matrix["case_rows"] = matrix["case_rows"][:-1]
    matrix["case_count"] = len(matrix["case_rows"])
    with pytest.raises(ValueError):
        assert_p7_r48_p5_first_formal_review_case_matrix_contract(matrix)


def test_r48_r2_r3_combined_freeze_keeps_review_release_closed_and_points_to_r4() -> None:
    freeze = build_p7_r48_r2_r3_local_storage_case_matrix_freeze(session_short_ref="s024")
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION
    assert freeze["implemented_steps"] == list(P7_R48_R2_R3_IMPLEMENTED_STEPS)
    assert freeze["not_yet_implemented_steps"] == list(P7_R48_R2_R3_NOT_YET_IMPLEMENTED_STEPS)
    assert freeze["next_required_step"] == P7_R48_R2_R3_NEXT_REQUIRED_STEP_REF
    assert freeze["packet_kind"] == P7_R48_PACKET_KIND
    assert freeze["review_kind"] == P7_R48_REVIEW_KIND
    assert freeze["r0_current_source_r47_handoff_hold_refrozen"] is True
    assert freeze["r1_scope_schema_packet_kind_fixed"] is True
    assert freeze["local_storage_root_policy_connected"] is True
    assert freeze["p5_24_case_first_formal_review_matrix_built"] is True
    assert freeze["body_free_case_matrix_ready"] is True
    assert freeze["actual_case_matrix_materialized_here"] is True
    assert freeze["case_count"] == 24
    assert freeze["minimums_satisfied"] is True
    assert freeze["local_body_packet_generation_allowed"] is False
    assert freeze["p5_human_blind_qa_actual_review_start_allowed_after_r2_r3"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["local_reviewer_payload_materialized_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    _assert_release_closed(freeze)


def test_r48_r2_r3_valid_root_permission_does_not_materialize_body_packet(tmp_path) -> None:
    local_root = tmp_path / "external-r48-root"
    freeze = build_p7_r48_r2_r3_local_storage_case_matrix_freeze(
        local_review_root=str(local_root),
        explicit_body_full_generation_allow=True,
        session_short_ref="s024",
    )
    assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(freeze)

    assert freeze["local_storage_policy"]["local_review_root_status"] == "valid"
    assert freeze["local_body_packet_generation_allowed"] is True
    assert freeze["body_free_case_matrix_ready"] is True
    assert freeze["actual_case_matrix_materialized_here"] is True
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["local_reviewer_payload_materialized_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["p5_human_blind_qa_actual_review_start_allowed_after_r2_r3"] is False
    _assert_release_closed(freeze)


def test_r48_r2_r3_rejects_body_payload_inputs_and_release_promotion() -> None:
    r0_r1 = build_p7_r48_r0_r1_scope_freeze()
    r0_r1["reviewer_free_text"] = SECRET_REVIEWER_NOTE
    with pytest.raises(ValueError):
        build_p7_r48_local_storage_root_policy(r0_r1_scope_freeze=r0_r1)

    freeze = build_p7_r48_r2_r3_local_storage_case_matrix_freeze(session_short_ref="s024")
    freeze["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(freeze)

    freeze = build_p7_r48_r2_r3_local_storage_case_matrix_freeze(session_short_ref="s024")
    freeze["p5_human_blind_qa_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_r2_r3_local_storage_case_matrix_freeze_contract(freeze)


def test_r48_r3_rejects_session_short_ref_that_encodes_family_or_tier() -> None:
    with pytest.raises(ValueError):
        build_p7_r48_p5_first_formal_review_case_matrix(session_short_ref="free-tier-session")

    with pytest.raises(ValueError):
        build_p7_r48_p5_first_formal_review_case_matrix(session_short_ref="history-line-eligible-session")
