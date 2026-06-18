# -*- coding: utf-8 -*-
"""P7-R47 R2/R3 local review packet storage/export policy contracts."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_EXPORT_DENYLIST_PATTERNS,
    P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
    P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION,
    P7_R47_R2_R3_IMPLEMENTED_STEPS,
    P7_R47_R2_R3_NEXT_REQUIRED_STEP_REF,
    P7_R47_R2_R3_NOT_YET_IMPLEMENTED_STEPS,
    P7_R47_R2_R3_STORAGE_EXPORT_POLICY_SCHEMA_VERSION,
    P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION,
    assert_p7_r47_export_denylist_policy_contract,
    assert_p7_r47_local_review_storage_root_policy_contract,
    assert_p7_r47_r2_r3_storage_export_policy_contract,
    build_p7_r47_export_denylist_policy,
    build_p7_r47_local_review_storage_root_policy,
    build_p7_r47_r2_r3_storage_export_policy,
    p7_r47_export_candidate_deny_reasons,
)

SECRET_ROOT = "/tmp/cocolon_emlis_r47_local_review_root"
SECRET_INPUT = "R47 R2/R3 secret raw input must not enter body-free material"
SECRET_SURFACE = "R47 R2/R3 secret Emlis surface must not enter body-free material"
SECRET_REVIEWER = "R47 R2/R3 reviewer free text must not enter body-free material"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_or_local_path(value: dict[str, object]) -> None:
    dumped = _dumped(value)
    assert SECRET_ROOT not in dumped
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


def test_r47_r2_missing_local_review_root_blocks_body_full_generation_without_blocking_policy_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR, raising=False)

    storage = build_p7_r47_local_review_storage_root_policy()
    assert_p7_r47_local_review_storage_root_policy_contract(storage)

    assert storage["schema_version"] == P7_R47_LOCAL_REVIEW_STORAGE_ROOT_POLICY_SCHEMA_VERSION
    assert storage["policy_section"] == "R2_local_only_storage_root_policy"
    assert storage["env_var"] == P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR
    assert storage["storage_mode"] == "external_local_only"
    assert storage["local_review_root_source"] == "missing"
    assert storage["local_review_root_configured"] is False
    assert storage["local_review_root_status"] == "missing"
    assert storage["storage_root_ref"] == "not_configured_or_invalid"
    assert storage["root_path_exposed"] is False
    assert storage["local_absolute_path_included"] is False
    assert storage["local_body_packet_generation_allowed"] is False
    assert storage["generation_block_reason_ids"] == ["local_review_root_not_configured"]
    assert storage["repo_local_storage_allowed"] is False
    assert storage["artifact_export_path_allowed"] is False
    assert storage["p5_human_blind_qa_start_allowed_after_r2"] is False
    assert storage["actual_body_full_packet_generated_here"] is False
    assert storage["release_allowed"] is False

    _assert_no_body_or_local_path(storage)


def test_r47_r2_valid_external_root_allows_only_storage_policy_not_actual_packet_generation() -> None:
    storage = build_p7_r47_local_review_storage_root_policy(
        local_review_root=SECRET_ROOT,
        repo_roots=("/workspaces/mashos-api",),
        export_roots=("/mnt/data",),
    )
    assert_p7_r47_local_review_storage_root_policy_contract(storage)

    assert storage["local_review_root_source"] == "provided_argument"
    assert storage["local_review_root_configured"] is True
    assert storage["local_review_root_status"] == "valid"
    assert storage["storage_root_ref"] == "external_local_review_root"
    assert storage["root_is_absolute"] is True
    assert storage["local_body_packet_generation_allowed"] is True
    assert storage["generation_block_reason_ids"] == []
    assert storage["actual_body_full_packet_generated_here"] is False
    assert storage["body_full_writer_created_here"] is False
    assert storage["p5_human_blind_qa_start_allowed_after_r2"] is False
    assert storage["release_allowed"] is False

    _assert_no_body_or_local_path(storage)


@pytest.mark.parametrize(
    ("bad_root", "reason_id"),
    [
        ("relative/local_review_root", "local_review_root_not_absolute"),
        ("/mnt/data", "local_review_root_under_mnt_data_artifact_root"),
        ("/mnt/data/local_review_root", "local_review_root_under_mnt_data_artifact_root"),
        ("/tmp/Cocolon_前提資料/local_review_root", "local_review_root_contains_forbidden_name_fragment"),
        ("/tmp/EmlisAIの実装済み資料/local_review_root", "local_review_root_contains_forbidden_name_fragment"),
        ("/tmp/release/local_review_root", "local_review_root_contains_forbidden_name_fragment"),
        ("/tmp/public_meta/local_review_root", "local_review_root_contains_forbidden_name_fragment"),
        ("/tmp/repo/docs/local_review_root", "local_review_root_contains_repo_or_git_component"),
        ("/tmp/repo/tests/local_review_root", "local_review_root_contains_repo_or_git_component"),
        ("/tmp/repo/services/local_review_root", "local_review_root_contains_repo_or_git_component"),
        ("/tmp/repo/.git/local_review_root", "local_review_root_contains_repo_or_git_component"),
    ],
)
def test_r47_r2_rejects_repo_artifact_docs_git_and_premise_roots(bad_root: str, reason_id: str) -> None:
    storage = build_p7_r47_local_review_storage_root_policy(local_review_root=bad_root)
    assert_p7_r47_local_review_storage_root_policy_contract(storage)

    assert storage["local_review_root_configured"] is True
    assert storage["local_review_root_status"] == "invalid"
    assert storage["local_body_packet_generation_allowed"] is False
    assert reason_id in storage["generation_block_reason_ids"]
    assert storage["actual_body_full_packet_generated_here"] is False

    _assert_no_body_or_local_path(storage)


def test_r47_r2_rejects_explicit_repo_and_export_roots_without_exposing_paths() -> None:
    storage = build_p7_r47_local_review_storage_root_policy(
        local_review_root="/tmp/cocolon_repo/local_review_root",
        repo_roots=("/tmp/cocolon_repo",),
        export_roots=("/tmp/cocolon_export",),
    )
    assert_p7_r47_local_review_storage_root_policy_contract(storage)
    assert storage["local_review_root_status"] == "invalid"
    assert "local_review_root_under_repo_root" in storage["generation_block_reason_ids"]
    _assert_no_body_or_local_path(storage)

    export_storage = build_p7_r47_local_review_storage_root_policy(
        local_review_root="/tmp/cocolon_export/local_review_root",
        repo_roots=("/tmp/cocolon_repo",),
        export_roots=("/tmp/cocolon_export",),
    )
    assert_p7_r47_local_review_storage_root_policy_contract(export_storage)
    assert export_storage["local_review_root_status"] == "invalid"
    assert "local_review_root_under_export_root" in export_storage["generation_block_reason_ids"]
    _assert_no_body_or_local_path(export_storage)


def test_r47_r3_export_denylist_and_git_zip_policy_are_fixed_body_free() -> None:
    export = build_p7_r47_export_denylist_policy()
    assert_p7_r47_export_denylist_policy_contract(export)

    assert export["schema_version"] == P7_R47_EXPORT_DENYLIST_POLICY_SCHEMA_VERSION
    assert export["policy_section"] == "R3_export_denylist_git_zip_mixing_prevention"
    assert tuple(export["export_denylist_patterns"]) == P7_R47_EXPORT_DENYLIST_PATTERNS
    assert export["git_zip_mixing_prevention_policy_fixed"] is True
    assert export["body_full_packet_export_allowed"] is False
    assert export["body_full_packet_git_tracking_allowed"] is False
    assert export["body_full_packet_zip_inclusion_allowed"] is False
    assert export["reviewer_notes_export_allowed"] is False
    assert export["release_material_body_full_allowed"] is False
    assert export["premise_zip_inclusion_allowed"] is False
    assert export["implemented_docs_zip_inclusion_allowed"] is False
    assert export["standard_patch_zip_body_full_inclusion_allowed"] is False
    assert export["body_free_summary_export_allowed"] is True
    assert export["release_allowed"] is False

    _assert_no_body_or_local_path(export)


@pytest.mark.parametrize(
    "candidate_ref",
    [
        ".local_review_packets/session/case.local_review_packet.json",
        "body_full_packets.local_only/case.local_review_packet.json",
        "reviewer_notes.local_only/case.reviewer_notes.json",
        "case.local_only.json",
        "Cocolon_EmlisAI_P7_R47_LocalReviewPacket_case_body_full.zip",
        ".git/local_review_packet.json",
        "Cocolon_前提資料/review_packet.local_review_packet.json",
        "EmlisAIの実装済み資料/review_packet.local_review_packet.json",
    ],
)
def test_r47_r3_export_candidate_deny_reasons_match_body_full_and_docs_patterns(candidate_ref: str) -> None:
    reasons = p7_r47_export_candidate_deny_reasons(candidate_ref)
    assert reasons
    assert any(
        reason in reasons
        for reason in (
            "r47_export_denylist_pattern_match",
            "r47_git_tracked_or_git_metadata_path",
            "r47_body_full_packet_zip_inclusion_blocked",
            "r47_premise_or_implemented_docs_zip_inclusion_blocked",
        )
    )


def test_r47_r2_r3_combined_policy_fixes_storage_and_export_but_does_not_start_review_or_release() -> None:
    combined = build_p7_r47_r2_r3_storage_export_policy(local_review_root=SECRET_ROOT)
    assert_p7_r47_r2_r3_storage_export_policy_contract(combined)

    assert combined["schema_version"] == P7_R47_R2_R3_STORAGE_EXPORT_POLICY_SCHEMA_VERSION
    assert tuple(combined["implemented_steps"]) == P7_R47_R2_R3_IMPLEMENTED_STEPS
    assert tuple(combined["not_yet_implemented_steps"]) == P7_R47_R2_R3_NOT_YET_IMPLEMENTED_STEPS
    assert combined["next_required_step"] == P7_R47_R2_R3_NEXT_REQUIRED_STEP_REF
    assert combined["local_review_packet_storage_policy_fixed"] is True
    assert combined["export_denylist_policy_fixed"] is True
    assert combined["git_zip_mixing_prevention_policy_fixed"] is True
    assert combined["local_body_packet_generation_allowed"] is True
    assert combined["local_review_packet_policy_ready"] is False
    assert combined["policy_ready"] is False
    assert combined["r47_policy_ready"] is False
    assert combined["p5_human_blind_qa_start_allowed_after_r2_r3"] is False
    assert combined["p5_human_blind_qa_confirmed"] is False
    assert combined["p6_limited_human_readfeel_start_allowed"] is False
    assert combined["real_device_modal_review_start_allowed"] is False
    assert combined["actual_body_full_packet_generated_here"] is False
    assert combined["body_full_writer_created_here"] is False
    assert combined["body_full_packet_schema_created_here"] is False
    assert combined["body_free_manifest_schema_created_here"] is False
    assert combined["rating_row_schema_created_here"] is False
    assert combined["disposal_policy_created_here"] is False
    assert combined["release_allowed"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["hold004_close_allowed"] is False

    _assert_no_body_or_local_path(combined)


def test_r47_r2_r3_contracts_reject_body_payload_contract_mutation_and_release_promotion() -> None:
    storage = build_p7_r47_local_review_storage_root_policy(local_review_root=SECRET_ROOT)
    storage["root_path_exposed"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_local_review_storage_root_policy_contract(storage)

    export = build_p7_r47_export_denylist_policy()
    export["body_full_packet_export_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_export_denylist_policy_contract(export)

    combined = build_p7_r47_r2_r3_storage_export_policy(local_review_root=SECRET_ROOT)
    combined["p5_human_blind_qa_start_allowed_after_r2_r3"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_r2_r3_storage_export_policy_contract(combined)

    combined = build_p7_r47_r2_r3_storage_export_policy(local_review_root=SECRET_ROOT)
    combined["storage_policy"]["reviewer_free_text"] = SECRET_REVIEWER
    with pytest.raises(ValueError):
        assert_p7_r47_r2_r3_storage_export_policy_contract(combined)
