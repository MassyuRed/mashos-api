# -*- coding: utf-8 -*-
"""P7-R53 R4/R5 tests for local-only preflight and session envelope."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53


def _assert_body_free_no_release_or_runtime_promotion(material: dict[str, object]) -> None:
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
    assert material["actual_human_review_run_here"] is False
    assert material["actual_manual_review_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_export_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["local_absolute_path_included"] is False


@lru_cache(maxsize=1)
def _cached_r53_r3_blocked() -> tuple[dict[str, object]]:
    adoption = r53.build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override()
    assert r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption) is True
    return (adoption,)


def _r53_r3_blocked() -> dict[str, object]:
    return deepcopy(_cached_r53_r3_blocked()[0])


@lru_cache(maxsize=1)
def _cached_r53_r3_green_override() -> tuple[dict[str, object]]:
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
    adoption = r53.build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override(
        validation_evidence_preflight=preflight,
    )
    assert r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption) is True
    return (adoption,)


def _r53_r3_green_override() -> dict[str, object]:
    return deepcopy(_cached_r53_r3_green_override()[0])


def _r53_r4_ready(tmp_path: Path) -> dict[str, object]:
    local_root = tmp_path / "r53_local_review_root"
    local_root.mkdir()
    preflight = r53.build_p7_r53_local_root_explicit_allow_purge_plan_preflight(
        current_snapshot_override_adoption=_r53_r3_green_override(),
        local_review_root=str(local_root),
        repo_roots=[str(Path.cwd())],
        export_roots=[str(tmp_path / "export_root")],
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=r53.build_p7_r53_default_local_only_purge_plan_bodyfree(),
    )
    assert r53.assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(preflight) is True
    return preflight


def test_r53_r4_default_preflight_is_blocked_without_split_green_local_root_allow_and_purge_plan() -> None:
    preflight = r53.build_p7_r53_local_root_explicit_allow_purge_plan_preflight(
        current_snapshot_override_adoption=_r53_r3_blocked(),
    )

    assert preflight["schema_version"] == r53.P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION
    assert set(preflight) == set(r53.P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert preflight["phase"].startswith("P7_")
    assert preflight["step"] == r53.P7_R53_STEP
    assert preflight["scope"] == r53.P7_R53_SCOPE
    assert preflight["policy_section"] == "R53-4_explicit_allow_local_root_purge_plan_preflight"
    assert preflight["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert preflight["r51_default_source_snapshot_refs"] == r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert preflight["r51_r0_source_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert preflight["r51_r0_uses_r53_current_snapshot_refs"] is True
    assert preflight["r51_default_source_refs_allowed_as_actual_review_basis"] is False

    assert preflight["r3_adoption_status"] == "ADOPTED_BLOCKED_BY_VALIDATION_EVIDENCE"
    assert preflight["r3_validation_ready_for_local_root_preflight"] is False
    assert preflight["preflight_status"] == "BLOCKED"
    assert preflight["r51_r2_preflight_status"] == "BLOCKED"
    assert preflight["local_review_root_configured"] is False
    assert preflight["local_review_root_valid"] is False
    assert preflight["explicit_allow_env_var"] == r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR
    assert preflight["explicit_allow_token_ref"] == r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF
    assert preflight["explicit_allow_present"] is False
    assert preflight["explicit_allow_token_body_stored_here"] is False
    assert preflight["purge_plan_present"] is False
    assert preflight["purge_plan_ready"] is False
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is False
    assert preflight["local_only_body_full_generation_allowed"] is False
    assert preflight["actual_review_session_envelope_allowed_after_r53_4"] is False
    assert preflight["manual_run_decision"] == "NO_GO_TARGET_OR_REGRESSION_EVIDENCE_MISSING"
    assert preflight["execution_blocker_ids"] == [
        "r53_missing_r49_split_green_evidence",
        "r53_local_review_root_missing",
        "r53_explicit_allow_missing",
        "r53_disposal_plan_missing",
    ]
    assert preflight["open_execution_blocker_ids"] == preflight["execution_blocker_ids"]
    assert preflight["next_required_step"] == r53.P7_R53_R4_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(preflight["implemented_steps"]) == r53.P7_R53_R4_IMPLEMENTED_STEPS
    assert tuple(preflight["not_yet_implemented_steps"]) == r53.P7_R53_R4_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(
        preflight["r51_r2_preflight_bodyfree"]
    ) is True

    _assert_body_free_no_release_or_runtime_promotion(preflight)


def test_r53_r4_passes_only_with_split_green_override_valid_local_root_explicit_allow_and_purge_plan(tmp_path: Path) -> None:
    preflight = _r53_r4_ready(tmp_path)

    assert preflight["r3_adoption_status"] == "ADOPTED_READY_FOR_R53_4_PREFLIGHT"
    assert preflight["r3_validation_ready_for_local_root_preflight"] is True
    assert preflight["preflight_status"] == "PASSED"
    assert preflight["r51_r2_preflight_status"] == "PASSED"
    assert preflight["r51_r2_next_required_step"] == r51.P7_R51_R2_NEXT_REQUIRED_STEP_REF
    assert preflight["local_review_root_configured"] is True
    assert preflight["local_review_root_valid"] is True
    assert preflight["storage_root_ref"] != "not_configured_or_invalid"
    assert preflight["root_path_exposed"] is False
    assert preflight["local_absolute_path_included"] is False
    assert preflight["explicit_allow_present"] is True
    assert preflight["explicit_allow_token_body_stored_here"] is False
    assert preflight["purge_plan_present"] is True
    assert preflight["purge_plan_status"] == "READY"
    assert preflight["purge_plan_ready"] is True
    assert tuple(preflight["purge_plan_required_delete_target_refs"]) == r51.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS
    assert preflight["denied_export_candidate_count"] == 0
    assert preflight["export_denylist_violation_refs"] == []
    assert preflight["body_full_packet_export_allowed"] is False
    assert preflight["reviewer_notes_export_allowed"] is False
    assert preflight["body_full_packet_zip_inclusion_allowed"] is False
    assert preflight["local_only_body_full_generation_allowed_before_preflight"] is False
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is True
    assert preflight["local_only_body_full_generation_allowed"] is True
    assert preflight["actual_review_session_envelope_allowed_after_r53_4"] is True
    assert preflight["manual_run_decision"] == "GO_FOR_LOCAL_MANUAL_REVIEW"
    assert preflight["execution_blocker_ids"] == []
    assert preflight["next_required_step"] == r53.P7_R53_R4_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_release_or_runtime_promotion(preflight)


@pytest.mark.parametrize(
    "key,value",
    [
        ("root_path_exposed", True),
        ("local_absolute_path_included", True),
        ("explicit_allow_token_body_stored_here", True),
        ("export_candidate_refs_stored_here", True),
        ("export_candidate_body_stored_here", True),
        ("body_full_packet_export_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("premise_or_implemented_docs_inclusion_allowed", True),
        ("local_only_body_full_generation_allowed_before_preflight", True),
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
    ],
)
def test_r53_r4_rejects_path_token_export_body_generation_review_or_release_promotion(
    key: str,
    value: object,
) -> None:
    preflight = r53.build_p7_r53_local_root_explicit_allow_purge_plan_preflight()
    preflight[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(preflight)


def test_r53_r4_rejects_passed_status_when_r3_validation_or_r51_blockers_are_not_ready() -> None:
    preflight = r53.build_p7_r53_local_root_explicit_allow_purge_plan_preflight()
    preflight["preflight_status"] = "PASSED"
    preflight["local_only_body_full_generation_allowed_after_preflight"] = True
    preflight["local_only_body_full_generation_allowed"] = True
    preflight["actual_review_session_envelope_allowed_after_r53_4"] = True
    preflight["next_required_step"] = r53.P7_R53_R4_NEXT_REQUIRED_STEP_REF
    with pytest.raises(ValueError):
        r53.assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(preflight)


def test_r53_r5_default_envelope_is_blocked_and_does_not_run_actual_review_or_generate_body_full() -> None:
    envelope = r53.build_p7_r53_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=r53.build_p7_r53_local_root_explicit_allow_purge_plan_preflight(),
    )

    assert envelope["schema_version"] == r53.P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION
    assert set(envelope) == set(r53.P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS)
    assert envelope["phase"].startswith("P7_")
    assert envelope["step"] == r53.P7_R53_STEP
    assert envelope["scope"] == r53.P7_R53_SCOPE
    assert envelope["policy_section"] == "R53-5_actual_review_session_envelope"
    assert envelope["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert envelope["r4_preflight_status"] == "BLOCKED"
    assert envelope["r4_preflight_ready_for_envelope"] is False
    assert envelope["review_session_status"] == "PRECHECK_BLOCKED"
    assert envelope["envelope_status"] == "BLOCKED_BY_R53_4_PREFLIGHT"
    assert envelope["r51_r3_envelope_status"] == "BLOCKED_BY_R51_2_PREFLIGHT"
    assert envelope["r51_r3_next_required_step"] == r51.P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert envelope["required_case_count"] == r51.P7_R51_REQUIRED_CASE_COUNT
    assert envelope["reviewer_ref_pseudonymous"] is True
    assert envelope["reviewer_blind_policy"]["reviewer_faces_blind_case_id_only"] is True
    assert envelope["reviewer_blind_policy"]["question_text_created_here"] is False
    assert envelope["body_full_generation_allowed"] is False
    assert envelope["local_only_body_full_generation_allowed"] is False
    assert envelope["actual_review_session_envelope_bodyfree_materialized_here"] is True
    assert envelope["p5_actual_review_still_not_run"] is True
    assert envelope["execution_blocker_ids"] == [
        "r53_missing_r49_split_green_evidence",
        "r53_local_review_root_missing",
        "r53_explicit_allow_missing",
        "r53_disposal_plan_missing",
    ]
    assert envelope["next_required_step"] == r53.P7_R53_R5_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(envelope["implemented_steps"]) == r53.P7_R53_R5_IMPLEMENTED_STEPS
    assert tuple(envelope["not_yet_implemented_steps"]) == r53.P7_R53_R5_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_actual_review_session_envelope_bodyfree_contract(
        envelope["r51_r3_envelope_bodyfree"]
    ) is True

    _assert_body_free_no_release_or_runtime_promotion(envelope)


def test_r53_r5_ready_envelope_creates_body_free_controller_material_only(tmp_path: Path) -> None:
    envelope = r53.build_p7_r53_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=_r53_r4_ready(tmp_path),
    )

    assert envelope["r4_preflight_status"] == "PASSED"
    assert envelope["r4_preflight_ready_for_envelope"] is True
    assert envelope["review_session_status"] == "ACTUAL_REVIEW_SESSION_ENVELOPE_READY"
    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    assert envelope["r51_r3_envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    assert envelope["r51_r3_next_required_step"] == r51.P7_R51_R3_NEXT_REQUIRED_STEP_REF
    assert envelope["reviewer_ref_pseudonymous"] is True
    assert envelope["reviewer_blind_policy"]["reviewer_faces_blind_case_id_only"] is True
    assert envelope["reviewer_blind_policy"]["family_hidden_from_reviewer"] is True
    assert envelope["reviewer_blind_policy"]["subscription_tier_hidden_from_reviewer"] is True
    assert envelope["reviewer_blind_policy"]["expected_boundary_hidden_from_reviewer"] is True
    assert envelope["reviewer_blind_policy"]["question_text_created_here"] is False
    assert envelope["local_absolute_path_included"] is False
    assert envelope["body_full_generation_allowed"] is True
    assert envelope["local_only_body_full_generation_allowed"] is True
    assert envelope["body_full_packet_generated_here"] is False
    assert envelope["actual_human_review_run_here"] is False
    assert envelope["actual_manual_review_run_here"] is False
    assert envelope["disposal_plan_ready"] is True
    assert envelope["execution_blocker_ids"] == []
    assert envelope["next_required_step"] == r53.P7_R53_R5_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_release_or_runtime_promotion(envelope)


@pytest.mark.parametrize(
    "key,value",
    [
        ("root_path_exposed", True),
        ("local_absolute_path_included", True),
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_export_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r5_rejects_path_body_generation_actual_review_or_release_promotion(key: str, value: object) -> None:
    envelope = r53.build_p7_r53_actual_review_session_envelope_bodyfree()
    envelope[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_actual_review_session_envelope_bodyfree_contract(envelope)


def test_r53_r5_rejects_ready_envelope_when_blockers_remain_visible() -> None:
    envelope = r53.build_p7_r53_actual_review_session_envelope_bodyfree()
    envelope["envelope_status"] = "READY_FOR_24_CASE_MANIFEST_FREEZE"
    envelope["body_full_generation_allowed"] = True
    envelope["local_only_body_full_generation_allowed"] = True
    envelope["next_required_step"] = r53.P7_R53_R5_NEXT_REQUIRED_STEP_REF
    with pytest.raises(ValueError):
        r53.assert_p7_r53_actual_review_session_envelope_bodyfree_contract(envelope)
