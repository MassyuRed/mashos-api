# -*- coding: utf-8 -*-
"""R51-2/R51-3 local root preflight and session envelope tests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51


FORBIDDEN_BODY_FREE_KEYS = {
    "raw_input",
    "raw_answer",
    "comment_text",
    "comment_text_body",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "current_input_review_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "question_body",
    "local_absolute_path",
    "body_content_hash",
    "packet_content_hash",
    "terminal_output",
    "traceback",
    "stdout",
    "stderr",
}


def _assert_no_body_payload_keys(value: object) -> None:
    if isinstance(value, Mapping):
        assert not (set(value) & FORBIDDEN_BODY_FREE_KEYS)
        for child in value.values():
            _assert_no_body_payload_keys(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _assert_no_body_payload_keys(child)


def _valid_purge_plan() -> dict[str, object]:
    return r51.build_p7_r51_default_local_only_purge_plan_bodyfree()


def _valid_preflight() -> dict[str, object]:
    return r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_valid_purge_plan(),
    )


def test_r51_r2_preflight_passes_only_with_external_root_allow_token_purge_plan_and_clean_exports() -> None:
    preflight = _valid_preflight()

    assert r51.assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(preflight) is True
    assert preflight["schema_version"] == r51.P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION
    assert set(preflight) == set(r51.P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert preflight["policy_section"] == "R51-2_local_root_explicit_allow_purge_plan_preflight"
    assert preflight["review_session_status"] == "READY_FOR_ACTUAL_REVIEW_SESSION_ENVELOPE"
    assert preflight["preflight_status"] == "PASSED"
    assert preflight["manual_run_decision"] == "GO_FOR_LOCAL_MANUAL_REVIEW"
    assert preflight["next_required_step"] == r51.P7_R51_R2_NEXT_REQUIRED_STEP_REF

    assert preflight["local_review_root_configured"] is True
    assert preflight["local_review_root_valid"] is True
    assert preflight["storage_root_ref"] == "external_local_review_root"
    assert preflight["root_path_exposed"] is False
    assert preflight["local_absolute_path_included"] is False

    assert preflight["explicit_allow_env_var"] == r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR
    assert preflight["explicit_allow_token_ref"] == r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF
    assert preflight["explicit_allow_present"] is True
    assert preflight["explicit_allow_token_body_stored_here"] is False

    assert preflight["purge_plan_present"] is True
    assert preflight["purge_plan_ready"] is True
    assert preflight["purge_plan_status"] == "READY"
    assert tuple(preflight["purge_plan_required_delete_target_refs"]) == r51.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS
    assert preflight["body_full_packet_retention_max_hours"] == 72
    assert preflight["reviewer_notes_retention_after_rating_finalized_max_hours"] == 24
    assert preflight["local_packet_exported_allowed"] is False
    assert preflight["content_hash_of_body_stored_allowed"] is False

    assert preflight["export_candidate_refs_checked_count"] == 0
    assert preflight["denied_export_candidate_count"] == 0
    assert preflight["export_denylist_violation_refs"] == []
    assert preflight["export_candidate_refs_stored_here"] is False
    assert preflight["export_candidate_body_stored_here"] is False
    assert preflight["body_full_packet_export_allowed"] is False
    assert preflight["reviewer_notes_export_allowed"] is False
    assert preflight["body_full_packet_zip_inclusion_allowed"] is False

    assert preflight["local_only_body_full_generation_allowed_before_preflight"] is False
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is True
    assert preflight["local_only_body_full_generation_allowed"] is True
    assert preflight["actual_human_review_run_here"] is False
    assert preflight["actual_manual_review_run_here"] is False
    assert preflight["body_full_packet_generated_here"] is False
    assert preflight["body_full_packets_created_local_only"] is False
    assert preflight["execution_blocker_ids"] == []
    assert tuple(preflight["implemented_steps"]) == r51.P7_R51_R2_IMPLEMENTED_STEPS
    assert tuple(preflight["not_yet_implemented_steps"]) == r51.P7_R51_R2_NOT_YET_IMPLEMENTED_STEPS
    assert preflight["p7_complete"] is False
    assert preflight["p8_start_allowed"] is False
    assert preflight["release_allowed"] is False
    _assert_no_body_payload_keys(preflight)


def test_r51_r2_preflight_blocks_without_local_root_allow_and_purge_plan() -> None:
    preflight = r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight()

    assert preflight["preflight_status"] == "BLOCKED"
    assert preflight["review_session_status"] == "PRECHECK_BLOCKED"
    assert preflight["next_required_step"] == r51.P7_R51_R2_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert preflight["manual_run_decision"] == "NO_GO_LOCAL_ROOT_UNSAFE"
    assert preflight["local_only_body_full_generation_allowed"] is False
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is False
    assert "r51_local_review_root_missing" in preflight["execution_blocker_ids"]
    assert "r51_explicit_allow_missing" in preflight["execution_blocker_ids"]
    assert "r51_disposal_plan_missing" in preflight["execution_blocker_ids"]
    assert preflight["body_full_packet_generated_here"] is False
    assert preflight["actual_manual_review_run_here"] is False
    assert preflight["p7_complete"] is False
    assert preflight["p8_start_allowed"] is False
    assert preflight["release_allowed"] is False
    _assert_no_body_payload_keys(preflight)


@pytest.mark.parametrize(
    "unsafe_root,expected_blocker",
    [
        ("/mnt/data/cocolon_r51_local_review_root", "r51_local_review_root_invalid"),
        ("/tmp/mashos-api/services/body_full_packets.local_only", "r51_local_review_root_invalid"),
    ],
)
def test_r51_r2_preflight_rejects_artifact_or_repo_like_roots(unsafe_root: str, expected_blocker: str) -> None:
    preflight = r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        local_review_root=unsafe_root,
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_valid_purge_plan(),
    )

    assert preflight["preflight_status"] == "BLOCKED"
    assert expected_blocker in preflight["execution_blocker_ids"]
    assert preflight["local_review_root_valid"] is False
    assert preflight["storage_root_ref"] == "not_configured_or_invalid"
    assert preflight["root_path_exposed"] is False
    assert preflight["local_absolute_path_included"] is False
    assert preflight["local_only_body_full_generation_allowed"] is False


def test_r51_r2_preflight_uses_env_allow_without_storing_token_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR,
        r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
    )
    preflight = r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        purge_plan=_valid_purge_plan(),
    )

    assert preflight["preflight_status"] == "PASSED"
    assert preflight["explicit_allow_present"] is True
    assert preflight["explicit_allow_token_body_stored_here"] is False
    assert preflight["manual_run_decision"] == "GO_FOR_LOCAL_MANUAL_REVIEW"


def test_r51_r2_preflight_rejects_incomplete_purge_plan() -> None:
    plan = _valid_purge_plan()
    plan["reviewer_notes_purge_required"] = False
    preflight = r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=plan,
    )

    assert preflight["preflight_status"] == "BLOCKED"
    assert preflight["purge_plan_status"] == "INCOMPLETE"
    assert preflight["purge_plan_ready"] is False
    assert "r51_disposal_plan_missing" in preflight["execution_blocker_ids"]
    assert preflight["manual_run_decision"] == "NO_GO_DISPOSAL_PLAN_UNSAFE"
    assert preflight["local_only_body_full_generation_allowed"] is False


def test_r51_r2_preflight_rejects_body_full_export_candidates_without_storing_candidate_refs() -> None:
    preflight = r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_valid_purge_plan(),
        export_candidate_refs=["body_full_packets.local_only/packet_case_001.json"],
    )

    assert preflight["preflight_status"] == "BLOCKED"
    assert preflight["export_candidate_refs_checked_count"] == 1
    assert preflight["denied_export_candidate_count"] == 1
    assert preflight["export_denylist_violation_refs"]
    assert "r51_body_full_packet_export_violation" in preflight["execution_blocker_ids"]
    assert preflight["manual_run_decision"] == "NO_GO_BODY_FREE_LEAK_RISK"
    assert preflight["export_candidate_refs_stored_here"] is False
    assert preflight["export_candidate_body_stored_here"] is False
    assert preflight["body_full_packet_export_allowed"] is False


def test_r51_r2_preflight_blocks_when_r1_validation_evidence_is_not_ready() -> None:
    r1 = r51.build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
        validation_evidence_overrides={
            "r49_split_matrix": {
                "evidence_status_ref": "MISSING",
                "evidence_present": False,
                "passed_count": 0,
            }
        }
    )
    preflight = r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        validation_evidence_r49_timeout_handling_freeze=r1,
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_valid_purge_plan(),
    )

    assert preflight["preflight_status"] == "BLOCKED"
    assert "r51_missing_r49_split_green_evidence" in preflight["execution_blocker_ids"]
    assert preflight["manual_run_decision"] == "NO_GO_TARGET_OR_REGRESSION_EVIDENCE_MISSING"
    assert preflight["local_only_body_full_generation_allowed"] is False


def test_r51_r3_session_envelope_is_ready_bodyfree_and_does_not_start_review() -> None:
    preflight = _valid_preflight()
    envelope = r51.build_p7_r51_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=preflight,
        reviewer_ref="reviewer_001",
    )

    assert r51.assert_p7_r51_actual_review_session_envelope_bodyfree_contract(envelope) is True
    assert envelope["schema_version"] == r51.P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION
    assert set(envelope) == set(r51.P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS)
    assert envelope["policy_section"] == "R51-3_actual_review_session_envelope"
    assert envelope["review_session_status"] == "ACTUAL_REVIEW_SESSION_ENVELOPE_READY"
    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    assert envelope["next_required_step"] == r51.P7_R51_R3_NEXT_REQUIRED_STEP_REF
    assert envelope["source_snapshot_refs"]["backend_zip_ref"] == "mashos-api(159).zip"
    assert envelope["r50_handoff_ref"] == r51.P7_R51_R50_HANDOFF_REF
    assert envelope["r2_preflight_ref"] == preflight["material_id"]
    assert envelope["required_case_count"] == 24
    assert envelope["reviewer_ref"] == "reviewer_001"
    assert envelope["reviewer_ref_pseudonymous"] is True
    assert envelope["reviewer_blind_policy"]["family_hidden_from_reviewer"] is True
    assert envelope["reviewer_blind_policy"]["question_text_created_here"] is False
    assert envelope["local_root_ref"] == "external_local_review_root"
    assert envelope["root_path_exposed"] is False
    assert envelope["local_absolute_path_included"] is False
    assert envelope["body_full_generation_allowed"] is True
    assert envelope["local_only_body_full_generation_allowed"] is True
    assert envelope["disposal_plan_ready"] is True
    assert tuple(envelope["session_controller_material_refs"]) == r51.P7_R51_SESSION_CONTROLLER_MATERIAL_REF_REFS
    assert envelope["actual_review_session_envelope_created_here"] is True
    assert envelope["p5_actual_review_still_not_run"] is True
    assert envelope["actual_human_review_run_here"] is False
    assert envelope["actual_manual_review_run_here"] is False
    assert envelope["body_full_packet_generated_here"] is False
    assert envelope["p7_complete"] is False
    assert envelope["p8_start_allowed"] is False
    assert envelope["release_allowed"] is False
    assert tuple(envelope["implemented_steps"]) == r51.P7_R51_R3_IMPLEMENTED_STEPS
    assert tuple(envelope["not_yet_implemented_steps"]) == r51.P7_R51_R3_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_body_payload_keys(envelope)


def test_r51_r3_session_envelope_remains_blocked_when_r2_preflight_is_blocked() -> None:
    preflight = r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight()
    envelope = r51.build_p7_r51_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=preflight,
        reviewer_ref="mash",
    )

    assert envelope["review_session_status"] == "PRECHECK_BLOCKED"
    assert envelope["envelope_status"] == "BLOCKED_BY_R51_2_PREFLIGHT"
    assert envelope["next_required_step"] == r51.P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert envelope["reviewer_ref"] == r51.P7_R51_DEFAULT_REVIEWER_REF
    assert envelope["local_root_ref"] == "not_configured_or_invalid"
    assert envelope["body_full_generation_allowed"] is False
    assert envelope["local_only_body_full_generation_allowed"] is False
    assert envelope["disposal_plan_ready"] is False
    assert "r51_local_review_root_missing" in envelope["execution_blocker_ids"]
    assert envelope["actual_human_review_run_here"] is False
    assert envelope["body_full_packet_generated_here"] is False
    assert envelope["p7_complete"] is False
    assert envelope["p8_start_allowed"] is False
    assert envelope["release_allowed"] is False
    _assert_no_body_payload_keys(envelope)


def test_r51_r0_to_r3_chain_returns_ready_envelope_without_bodyfull_generation() -> None:
    envelope = r51.build_p7_r51_r0_r3_preflight_session_envelope_chain(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
    )

    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    assert envelope["next_required_step"] == r51.P7_R51_R3_NEXT_REQUIRED_STEP_REF
    assert envelope["body_full_generation_allowed"] is True
    assert envelope["body_full_packet_generated_here"] is False
    assert envelope["actual_manual_review_run_here"] is False
    assert envelope["p7_complete"] is False
    assert envelope["p8_start_allowed"] is False
    assert envelope["release_allowed"] is False
