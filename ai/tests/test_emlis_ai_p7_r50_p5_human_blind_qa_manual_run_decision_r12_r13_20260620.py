# -*- coding: utf-8 -*-
"""R50-12/R50-13 tests for P5 human Blind QA manual-run decision.

These tests stop at the pause/abort/expiration protocol and body-free disposal
receipt builder/verifier. They do not run human review, do not generate or purge
body-full packets, do not write files, do not touch API/DB/RN contracts, do not
start P8, do not complete P7, and do not claim release readiness.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_VALID_LOCAL_ROOT_REF = "/tmp/cocolon_emlis_r50_local_review"
_SAFE_BODYFREE_EXPORT_CANDIDATE_REF = "summary.bodyfree/post_review_decision_summary.bodyfree.json"

_FALSE_RUNTIME_AND_PRODUCT_FLAGS = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
)

_BODY_LEAK_FIELD_REFS = (
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
    "stdout",
    "stderr",
    "traceback",
)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _assert_body_free_no_leak(value):
    keys = set(_walk_keys(value))
    assert not (keys & set(_BODY_LEAK_FIELD_REFS))


def _assert_no_runtime_or_product_completion(material):
    for key in _FALSE_RUNTIME_AND_PRODUCT_FLAGS:
        if key in material:
            assert material[key] is False
    assert material["body_free"] is True
    _assert_body_free_no_leak(material)


def _r3_go():
    return r50.build_p7_r50_manual_run_decision_bodyfree(
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
    )


def _r4_passed():
    return r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token=r50.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
        export_candidate_refs=[_SAFE_BODYFREE_EXPORT_CANDIDATE_REF],
    )


def _r5_ready():
    return r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=_r4_passed()
    )


def _r6_ready():
    return r50.build_p7_r50_local_only_body_full_packet_generation_request(
        review_session_protocol_bodyfree=_r5_ready()
    )


def _r7_ready():
    return r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
        local_only_body_full_packet_generation_request=_r6_ready()
    )


def _r8_ready():
    return r50.build_p7_r50_rating_row_normalizer_bodyfree(
        reviewer_instruction_rating_form_freeze=_r7_ready()
    )


def _r9_ready():
    return r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=_r8_ready()
    )


def _r10_ready():
    return r50.build_p7_r50_question_need_observation_row_normalizer_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=_r9_ready()
    )


def _r11_ready():
    return r50.build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=_r10_ready()
    )


def _r12_ready():
    return r50.build_p7_r50_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r11_ready()
    )


def _valid_receipt(status="DISPOSAL_VERIFIED"):
    return r50.build_p7_r50_disposal_receipt_bodyfree(
        review_session_id="p7_r50_review_session_001",
        case_count=24,
        deleted_file_count=48,
        disposal_status=status,
        body_removed=True,
        reviewer_notes_removed=True,
        purge_started_at="2026-06-20T10:00:00+09:00",
        purge_completed_at="2026-06-20T10:01:00+09:00",
    )


def test_r50_received_source_contains_r0_to_r11_before_r12_r13_progression():
    assert r50.P7_R50_R11_IMPLEMENTED_STEPS[-1] == "R50-11_rating_question_observation_consistency_guard"
    assert r50.P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS[0] == "R50-12_pause_abort_expiration_protocol"
    assert r50.P7_R50_R11_NEXT_REQUIRED_STEP_REF == "R50-12_pause_abort_expiration_protocol"
    assert r50.P7_R50_R12_NEXT_REQUIRED_STEP_REF == "R50-13_disposal_receipt_builder_verifier"
    assert r50.P7_R50_R13_NEXT_REQUIRED_STEP_REF == "R50-14_body_free_post_review_summary_builder"


def test_r50_r12_builds_pause_abort_expiration_protocol_without_running_review_or_disposal():
    protocol = _r12_ready()

    assert r50.assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract(protocol) is True
    assert protocol["schema_version"] == r50.P7_R50_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_SCHEMA_VERSION
    assert protocol["policy_section"] == "R50-12_pause_abort_expiration_protocol"
    assert protocol["consistency_guard_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    assert protocol["pause_abort_expiration_protocol_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    assert protocol["retention_deadline_continues_while_paused"] is True
    assert protocol["pause_does_not_extend_body_full_retention"] is True
    assert protocol["review_aborted_requires_purge"] is True
    assert protocol["expiration_requires_purge_even_if_rating_incomplete"] is True
    assert protocol["expired_purged_prioritizes_body_removed"] is True
    assert protocol["aborted_or_expired_forbid_p5_confirmed_candidate"] is True
    assert protocol["body_full_packet_retention_max_hours"] == r50.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS
    assert protocol["reviewer_notes_retention_after_rating_hours"] == r50.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    assert protocol["local_packet_export_allowed_during_pause_abort_expiration"] is False
    assert protocol["content_hash_storage_allowed_during_pause_abort_expiration"] is False
    assert protocol["body_free_summary_finalize_allowed_without_disposal_receipt"] is False
    assert protocol["next_required_step"] == r50.P7_R50_R12_NEXT_REQUIRED_STEP_REF
    assert protocol["implemented_steps"] == list(r50.P7_R50_R12_IMPLEMENTED_STEPS)
    assert protocol["not_yet_implemented_steps"] == list(r50.P7_R50_R12_NOT_YET_IMPLEMENTED_STEPS)
    _assert_no_runtime_or_product_completion(protocol)


def test_r50_r12_blocks_when_r11_consistency_guard_is_not_ready():
    blocked_r4 = r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token="WRONG_TOKEN",
    )
    blocked_r11 = r50.build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=r50.build_p7_r50_question_need_observation_row_normalizer_bodyfree(
            readfeel_blocker_execution_blocker_ingestion_bodyfree=r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
                rating_row_normalizer_bodyfree=r50.build_p7_r50_rating_row_normalizer_bodyfree(
                    reviewer_instruction_rating_form_freeze=r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
                        local_only_body_full_packet_generation_request=r50.build_p7_r50_local_only_body_full_packet_generation_request(
                            review_session_protocol_bodyfree=r50.build_p7_r50_review_session_protocol_bodyfree(
                                local_only_root_explicit_allow_export_preflight=blocked_r4
                            )
                        )
                    )
                )
            )
        )
    )
    protocol = r50.build_p7_r50_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=blocked_r11
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "BLOCKED_BY_R50_11_CONSISTENCY_GUARD"
    assert protocol["local_only_body_full_generation_allowed"] is False
    assert "r50_explicit_allow_missing" in protocol["execution_blocker_ids"]
    assert protocol["next_required_step"] == r50.P7_R50_R12_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(protocol)


def test_r50_r13_builds_and_verifies_bodyfree_disposal_receipt_without_file_ops():
    receipt = _valid_receipt()
    verifier = r50.build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r12_ready(),
        disposal_receipt_bodyfree=receipt,
    )

    assert r50.assert_p7_r50_disposal_receipt_bodyfree_contract(receipt) is True
    assert r50.assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract(verifier) is True
    assert receipt["schema_version"] == r50.P7_R50_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION
    assert receipt["disposal_status"] == "DISPOSAL_VERIFIED"
    assert receipt["body_removed"] is True
    assert receipt["reviewer_notes_removed"] is True
    assert receipt["local_packet_exported"] is False
    assert receipt["content_hash_of_body_stored"] is False
    assert verifier["disposal_receipt_builder_status"] == "DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
    assert verifier["disposal_receipt_verification_status"] == "VERIFIED"
    assert verifier["disposal_receipt_verified_for_summary"] is True
    assert verifier["disposal_verified_for_candidate"] is True
    assert verifier["body_free_summary_finalize_allowed_without_disposal_receipt"] is False
    assert verifier["actual_disposal_run_here"] is False
    assert verifier["actual_disposal_receipt_materialized_here"] is False
    assert verifier["next_required_step"] == r50.P7_R50_R13_NEXT_REQUIRED_STEP_REF
    assert verifier["implemented_steps"] == list(r50.P7_R50_R13_IMPLEMENTED_STEPS)
    assert verifier["not_yet_implemented_steps"] == list(r50.P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS)
    _assert_body_free_no_leak(receipt)
    _assert_no_runtime_or_product_completion(verifier)


def test_r50_r13_pending_builder_is_ready_but_does_not_claim_disposal_verified():
    verifier = r50.build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r12_ready()
    )

    assert verifier["disposal_receipt_builder_status"] == "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER"
    assert verifier["disposal_receipt_verification_status"] == "PENDING"
    assert verifier["disposal_receipt_verified_for_summary"] is False
    assert verifier["disposal_verified_for_candidate"] is False
    assert verifier["disposal_receipt_bodyfree"] == {}
    assert verifier["next_required_step"] == r50.P7_R50_R13_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(verifier)


def test_r50_r13_expired_purged_verifies_body_removed_but_forbids_candidate():
    receipt = _valid_receipt(status="EXPIRED_PURGED")
    verifier = r50.build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r12_ready(),
        disposal_receipt_bodyfree=receipt,
    )

    assert verifier["disposal_receipt_verification_status"] == "VERIFIED"
    assert verifier["disposal_receipt_verified_for_summary"] is True
    assert verifier["disposal_verified_for_candidate"] is False
    assert verifier["expired_purged_body_removed_but_candidate_forbidden"] is True
    assert verifier["p5_human_blind_qa_confirmed_candidate"] is False
    _assert_no_runtime_or_product_completion(verifier)


def test_r50_r13_disposal_failed_is_bodyfree_but_not_verified():
    failed_receipt = r50.build_p7_r50_disposal_receipt_bodyfree(
        review_session_id="p7_r50_review_session_001",
        case_count=24,
        deleted_file_count=10,
        disposal_status="DISPOSAL_FAILED",
        body_removed=True,
        reviewer_notes_removed=False,
    )
    verifier = r50.build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r12_ready(),
        disposal_receipt_bodyfree=failed_receipt,
    )

    assert verifier["disposal_receipt_verification_status"] == "FAILED"
    assert verifier["disposal_receipt_verified_for_summary"] is False
    assert verifier["disposal_verified_for_candidate"] is False
    assert verifier["disposal_failed_blocks_p5_p6_p8_candidates"] is True
    _assert_no_runtime_or_product_completion(verifier)


def test_r50_r13_rejects_export_hash_body_leak_and_invalid_verified_receipt():
    receipt = _valid_receipt()
    exported = copy.deepcopy(receipt)
    exported["local_packet_exported"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_disposal_receipt_bodyfree_contract(exported)

    hashed = copy.deepcopy(receipt)
    hashed["content_hash_of_body_stored"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_disposal_receipt_bodyfree_contract(hashed)

    leaked = copy.deepcopy(receipt)
    leaked["deleted_body_preview"] = "body preview must never be stored in receipt"
    with pytest.raises(ValueError):
        r50.assert_p7_r50_disposal_receipt_bodyfree_contract(leaked)

    with pytest.raises(ValueError):
        r50.build_p7_r50_disposal_receipt_bodyfree(
            disposal_status="DISPOSAL_VERIFIED",
            body_removed=True,
            reviewer_notes_removed=False,
        )

    with pytest.raises(ValueError):
        r50.build_p7_r50_disposal_receipt_bodyfree(
            disposal_status="EXPIRED_PURGED",
            body_removed=False,
            reviewer_notes_removed=True,
        )


def test_r50_r12_r13_combined_freeze_matches_nested_materials_and_keeps_product_closed():
    receipt = _valid_receipt()
    combined = r50.build_p7_r50_r12_r13_disposal_protocol_freeze(
        rating_question_observation_consistency_guard_bodyfree=_r11_ready(),
        disposal_receipt_bodyfree=receipt,
    )

    assert r50.assert_p7_r50_r12_r13_disposal_protocol_freeze_contract(combined) is True
    assert combined["schema_version"] == r50.P7_R50_R12_R13_DISPOSAL_PROTOCOL_FREEZE_SCHEMA_VERSION
    assert combined["policy_section"] == "R50-12_R50-13_disposal_protocol_freeze"
    assert combined["pause_abort_expiration_protocol_status"] == combined["r12_pause_abort_expiration_protocol"]["pause_abort_expiration_protocol_status"]
    assert combined["disposal_receipt_builder_status"] == combined["r13_disposal_receipt_builder_verifier"]["disposal_receipt_builder_status"]
    assert combined["disposal_receipt_verification_status"] == combined["r13_disposal_receipt_builder_verifier"]["disposal_receipt_verification_status"]
    assert combined["disposal_receipt_verified_for_summary"] is True
    assert combined["actual_manual_review_run_here"] is False
    assert combined["body_full_packet_generated_here"] is False
    assert combined["actual_disposal_run_here"] is False
    assert combined["actual_disposal_receipt_materialized_here"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False
    assert combined["implemented_steps"] == list(r50.P7_R50_R13_IMPLEMENTED_STEPS)
    assert combined["not_yet_implemented_steps"] == list(r50.P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS)
    assert combined["next_required_step"] == r50.P7_R50_R13_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_leak(combined)


def test_r50_r12_r13_contracts_reject_policy_drift():
    protocol = _r12_ready()
    drifted_protocol = copy.deepcopy(protocol)
    drifted_protocol["retention_deadline_continues_while_paused"] = False
    with pytest.raises(ValueError):
        r50.assert_p7_r50_pause_abort_expiration_protocol_bodyfree_contract(drifted_protocol)

    verifier = r50.build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=protocol,
        disposal_receipt_bodyfree=_valid_receipt(),
    )
    drifted_verifier = copy.deepcopy(verifier)
    drifted_verifier["body_free_summary_finalize_allowed_without_disposal_receipt"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_disposal_receipt_builder_verifier_bodyfree_contract(drifted_verifier)

    combined = r50.build_p7_r50_r12_r13_disposal_protocol_freeze(
        pause_abort_expiration_protocol_bodyfree=protocol,
        disposal_receipt_bodyfree=_valid_receipt(),
    )
    drifted_combined = copy.deepcopy(combined)
    drifted_combined["actual_disposal_run_here"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_r12_r13_disposal_protocol_freeze_contract(drifted_combined)
