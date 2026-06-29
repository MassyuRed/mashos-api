# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51


FORBIDDEN_BODY_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"bounded_owned_history_review_surface":',
    '"current_input_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_PROMOTION_TOKENS = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"hold004_close_allowed": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_trigger_logic_implemented": true',
    '"question_trigger_logic_implemented_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"post_review_summary_materialized_here": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_question_design_material_candidate": true',
    '"full_backend_suite_green_confirmed": true',
)


def _assert_bodyfree_no_leak_or_release_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_BODY_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_PROMOTION_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_purge_plan() -> tuple[dict[str, object]]:
    return (r51.build_p7_r51_default_local_only_purge_plan_bodyfree(),)


def _purge_plan() -> dict[str, object]:
    return deepcopy(_cached_purge_plan()[0])


@lru_cache(maxsize=1)
def _cached_envelope() -> tuple[dict[str, object]]:
    envelope = r51.build_p7_r51_r0_r3_preflight_session_envelope_chain(
        local_review_root="/tmp/cocolon_r51_local_review",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_purge_plan(),
    )
    assert r51.assert_p7_r51_actual_review_session_envelope_bodyfree_contract(envelope) is True
    return (envelope,)


def _envelope() -> dict[str, object]:
    return deepcopy(_cached_envelope()[0])


@lru_cache(maxsize=1)
def _cached_manifest() -> tuple[dict[str, object]]:
    manifest = r51.build_p7_r51_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=_envelope())
    assert r51.assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest) is True
    return (manifest,)


def _manifest() -> dict[str, object]:
    return deepcopy(_cached_manifest()[0])


@lru_cache(maxsize=1)
def _cached_freeze() -> tuple[dict[str, object]]:
    freeze = r51.build_p7_r51_r0_r7_reviewer_instruction_rating_form_chain(
        local_review_root="/tmp/cocolon_r51_local_review",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_purge_plan(),
    )
    assert r51.assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(freeze) is True
    return (freeze,)


def _freeze() -> dict[str, object]:
    return deepcopy(_cached_freeze()[0])


def _base_pass_review_rows() -> list[dict[str, object]]:
    axis_scores = {axis: 1.0 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES}
    rows: list[dict[str, object]] = []
    for case in _manifest()["case_rows"]:
        case_row = dict(case)
        rows.append(
            {
                "blind_case_id": case_row["blind_case_id"],
                "axis_scores": dict(axis_scores),
                "verdict": "PASS",
                "sanitized_reason_ids": [],
                "blocker_ids": [],
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": ["no_repair_required"],
                "reviewer_free_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "machine_auto_score_used": False,
                "machine_metrics_used_for_readfeel": False,
            }
        )
    return rows


def _r8_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    r8 = r51.build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=_freeze(),
        case_manifest_freeze=_manifest(),
        review_result_rows=rows,
        reviewer_ref="pseudonymous_reviewer_r51_contract",
        reviewed_at="2026-06-20T00:00:00+09:00",
    )
    assert r51.assert_p7_r51_actual_human_review_run_bodyfree_contract(r8) is True
    return r8


@lru_cache(maxsize=1)
def _cached_r12_pass() -> tuple[dict[str, object]]:
    r8 = _r8_from_rows(_base_pass_review_rows())
    r9 = r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=r8)
    assert r51.assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9) is True
    r10 = r51.build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=r9
    )
    assert r51.assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r10) is True
    r11 = r51.build_p7_r51_question_need_observation_row_normalizer_bodyfree(
        actual_human_review_run=r8,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
    )
    assert r51.assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(r11) is True
    r12 = r51.build_p7_r51_rating_question_observation_consistency_guard_bodyfree(
        r9_rating_row_normalizer_bodyfree=r9,
        r10_readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
        r11_question_need_observation_row_normalizer_bodyfree=r11,
    )
    assert r51.assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(r12) is True
    return (r12,)


def _r12_pass() -> dict[str, object]:
    return deepcopy(_cached_r12_pass()[0])


def _r13_completed() -> dict[str, object]:
    protocol = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r12_pass(),
        review_lifecycle_status="REVIEW_COMPLETED",
        body_full_packet_age_hours=1,
        reviewer_notes_age_hours=1,
    )
    assert r51.assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(protocol) is True
    assert protocol["pause_abort_expiration_protocol_status"] == "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    return protocol


def _verified_purge_rows() -> list[dict[str, object]]:
    return [
        r51.build_p7_r51_purge_evidence_row_bodyfree(
            review_session_id=r51.P7_R51_DEFAULT_REVIEW_SESSION_ID,
            purge_target_ref=target,
            purge_target_kind=target,
            purge_required=True,
            purge_attempted=True,
            removed=True,
            removed_count=24,
        )
        for target in r51.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS
    ]


def test_r51_r14_requires_explicit_bodyfree_purge_evidence_before_disposal_receipt() -> None:
    r14 = r51.build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r13_completed()
    )

    assert r14["schema_version"] == r51.P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION
    assert set(r14) == set(r51.P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_BODYFREE_REQUIRED_FIELD_REFS)
    assert r14["policy_section"] == "R51-14_body_full_packet_reviewer_notes_purge"
    assert r14["purge_status"] == "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    assert r14["purge_evidence_row_count"] == 0
    assert r14["missing_purge_target_refs"] == list(r51.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS)
    assert r14["body_removed"] is False
    assert r14["reviewer_notes_removed"] is False
    assert r14["actual_disposal_run_here"] is False
    assert r14["actual_disposal_receipt_materialized_here"] is False
    assert r14["r14_body_full_packet_reviewer_notes_purge_built"] is False
    assert r14["execution_blocker_ids"] == ["r51_disposal_not_verified"]
    assert r14["next_required_step"] == r51.P7_R51_R14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(r14["implemented_steps"]) == r51.P7_R51_R13_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_release_promotion(r14)


def test_r51_r14_verified_purge_evidence_advances_to_receipt_without_exporting_body() -> None:
    r14 = r51.build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r13_completed(),
        purge_evidence_rows=_verified_purge_rows(),
    )

    assert r14["purge_status"] == "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER"
    assert r14["review_session_status"] == "R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_VERIFIED_BODYFREE"
    assert r14["disposal_status"] == "BODY_PURGED"
    assert r14["purge_evidence_row_count"] == 3
    assert r14["verified_purge_target_count"] == 3
    assert r14["deleted_file_count"] == 72
    assert r14["body_removed"] is True
    assert r14["reviewer_forms_removed"] is True
    assert r14["reviewer_notes_removed"] is True
    assert r14["local_packet_exported"] is False
    assert r14["content_hash_of_body_stored"] is False
    assert r14["local_absolute_path_included"] is False
    assert r14["body_content_hash_included"] is False
    assert r14["local_file_delete_ops_executed_by_helper"] is False
    assert r14["actual_disposal_run_here"] is True
    assert r14["actual_disposal_receipt_materialized_here"] is False
    assert r14["post_review_summary_materialized_here"] is False
    assert tuple(r14["implemented_steps"]) == r51.P7_R51_R14_IMPLEMENTED_STEPS
    assert tuple(r14["not_yet_implemented_steps"]) == r51.P7_R51_R14_NOT_YET_IMPLEMENTED_STEPS
    assert r14["next_required_step"] == r51.P7_R51_R14_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_release_promotion(r14)


def test_r51_r14_failed_or_partial_purge_keeps_disposal_blocker_and_does_not_advance() -> None:
    rows = _verified_purge_rows()
    rows[-1] = r51.build_p7_r51_purge_evidence_row_bodyfree(
        review_session_id=r51.P7_R51_DEFAULT_REVIEW_SESSION_ID,
        purge_target_ref=r51.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS[-1],
        purge_target_kind=r51.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS[-1],
        purge_required=True,
        purge_attempted=True,
        removed=False,
        removed_count=0,
    )
    r14 = r51.build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r13_completed(),
        purge_evidence_rows=rows,
    )

    assert r14["purge_status"] == "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    assert r14["disposal_status"] == "DISPOSAL_FAILED"
    assert r14["failed_purge_target_refs"] == [r51.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS[-1]]
    assert r14["body_removed"] is False
    assert r14["actual_disposal_run_here"] is True
    assert r14["execution_blocker_ids"] == ["r51_disposal_failed"]
    assert r14["r14_body_full_packet_reviewer_notes_purge_built"] is False
    assert r14["next_required_step"] == r51.P7_R51_R14_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_release_promotion(r14)


def test_r51_r15_verified_disposal_receipt_allows_only_bodyfree_summary_next_not_release_or_p8() -> None:
    r14 = r51.build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r13_completed(),
        purge_evidence_rows=_verified_purge_rows(),
    )
    r15 = r51.build_p7_r51_disposal_receipt_builder_verifier_bodyfree(
        body_full_packet_reviewer_notes_purge_bodyfree=r14
    )

    assert r15["schema_version"] == r51.P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION
    assert set(r15) == set(r51.P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_BODYFREE_REQUIRED_FIELD_REFS)
    assert r15["policy_section"] == "R51-15_disposal_receipt_builder_verifier"
    assert r15["review_session_status"] == "R51_DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
    assert r15["disposal_receipt_verifier_status"] == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER"
    assert r15["disposal_status"] == "DISPOSAL_VERIFIED"
    assert r15["disposal_verified"] is True
    assert r15["summary_finalize_allowed"] is True
    assert r15["actual_disposal_run_here"] is True
    assert r15["disposal_receipt_materialized_here"] is True
    assert r15["actual_disposal_receipt_materialized_here"] is True
    assert r15["post_review_summary_materialized_here"] is False
    assert r15["release_allowed"] is False
    assert r15["p7_complete"] is False
    assert r15["p8_start_allowed"] is False
    assert r15["p8_question_design_material_candidate"] is False
    assert tuple(r15["implemented_steps"]) == r51.P7_R51_R15_IMPLEMENTED_STEPS
    assert tuple(r15["not_yet_implemented_steps"]) == r51.P7_R51_R15_NOT_YET_IMPLEMENTED_STEPS
    assert r15["next_required_step"] == r51.P7_R51_R15_NEXT_REQUIRED_STEP_REF

    receipt = r15["disposal_receipt"]
    assert isinstance(receipt, dict)
    assert receipt["schema_version"] == r51.P7_R51_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION
    assert receipt["disposal_status"] == "DISPOSAL_VERIFIED"
    assert receipt["body_removed"] is True
    assert receipt["reviewer_notes_removed"] is True
    assert receipt["local_packet_exported"] is False
    assert receipt["content_hash_of_body_stored"] is False
    assert receipt["body_free"] is True
    _assert_bodyfree_no_leak_or_release_promotion(r15)


def test_r51_r15_blocks_when_r14_purge_is_not_verified_and_rejects_body_or_release_mutations() -> None:
    r14 = r51.build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r13_completed()
    )
    r15 = r51.build_p7_r51_disposal_receipt_builder_verifier_bodyfree(
        body_full_packet_reviewer_notes_purge_bodyfree=r14
    )

    assert r15["disposal_receipt_verifier_status"] == "BLOCKED_BY_R51_14_PURGE"
    assert r15["review_session_status"] == "R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY"
    assert r15["disposal_status"] == "DISPOSAL_FAILED"
    assert r15["body_removed"] is False
    assert r15["disposal_verified"] is False
    assert r15["summary_finalize_allowed"] is False
    assert r15["actual_disposal_run_here"] is False
    assert r15["disposal_receipt_materialized_here"] is True
    assert r15["actual_disposal_receipt_materialized_here"] is True
    assert r15["r15_disposal_receipt_builder_verifier_built"] is False
    assert r15["next_required_step"] == r51.P7_R51_R15_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_release_promotion(r15)

    release_claim = deepcopy(r15)
    release_claim["p7_complete"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(release_claim)

    body_claim = deepcopy(r15)
    body_claim["disposal_receipt"]["raw_input"] = "body must not enter the disposal receipt"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(body_claim)

    export_claim = r51.build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r13_completed(),
        purge_evidence_rows=_verified_purge_rows(),
    )
    export_claim["local_packet_exported"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract(export_claim)
