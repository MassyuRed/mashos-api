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
    '"p5_human_blind_qa_confirmed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed_candidate": true',
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
def _cached_manifest() -> tuple[dict[str, object]]:
    envelope = r51.build_p7_r51_r0_r3_preflight_session_envelope_chain(
        local_review_root="/tmp/cocolon_r51_local_review",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_purge_plan(),
    )
    manifest = r51.build_p7_r51_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=envelope)
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


def _r9_r10_r11_r12_from_rows(rows: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    r8 = _r8_from_rows(rows)
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
    return r9, r10, r11, r12


@lru_cache(maxsize=1)
def _cached_pass_chain() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    return _r9_r10_r11_r12_from_rows(_base_pass_review_rows())


def _pass_chain() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    return tuple(deepcopy(item) for item in _cached_pass_chain())  # type: ignore[return-value]


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


def _r15_from_r12(r12: dict[str, object], *, verified: bool = True) -> dict[str, object]:
    r13 = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=r12,
        review_lifecycle_status="REVIEW_COMPLETED",
        body_full_packet_age_hours=1,
        reviewer_notes_age_hours=1,
    )
    assert r51.assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(r13) is True
    r14 = r51.build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        pause_abort_expiration_protocol_bodyfree=r13,
        purge_evidence_rows=_verified_purge_rows() if verified else None,
    )
    assert r51.assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract(r14) is True
    r15 = r51.build_p7_r51_disposal_receipt_builder_verifier_bodyfree(
        body_full_packet_reviewer_notes_purge_bodyfree=r14
    )
    assert r51.assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(r15) is True
    return r15


def _r16_from_chain(
    r9: dict[str, object],
    r10: dict[str, object],
    r11: dict[str, object],
    r12: dict[str, object],
    *,
    verified_disposal: bool = True,
) -> dict[str, object]:
    r16 = r51.build_p7_r51_body_free_post_review_summary_builder_bodyfree(
        r15_disposal_receipt_builder_verifier_bodyfree=_r15_from_r12(r12, verified=verified_disposal),
        r9_rating_row_normalizer_bodyfree=r9,
        r10_readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
        r11_question_need_observation_row_normalizer_bodyfree=r11,
        r12_rating_question_observation_consistency_guard_bodyfree=r12,
    )
    assert r51.assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(r16) is True
    return r16


def test_r51_r16_builds_bodyfree_post_review_summary_after_disposal_verified() -> None:
    r9, r10, r11, r12 = _pass_chain()
    r16 = _r16_from_chain(r9, r10, r11, r12)

    assert r16["schema_version"] == r51.P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION
    assert set(r16) == set(r51.P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_BODYFREE_REQUIRED_FIELD_REFS)
    assert r16["policy_section"] == "R51-16_body_free_post_review_summary_builder"
    assert r16["post_review_summary_status"] == "READY_FOR_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION"
    assert r16["rating_row_count"] == 24
    assert r16["question_observation_row_count"] == 24
    assert r16["verdict_counts"] == {"PASS": 24}
    assert r16["axis_score_averages"] == {axis: 1.0 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES}
    assert r16["all_axis_targets_met"] is True
    assert r16["readfeel_blocker_counts"] == {}
    assert r16["execution_blocker_counts"] == {}
    assert r16["question_need_primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert r16["disposal_verified"] is True
    assert r16["post_review_summary_materialized_here"] is True
    assert r16["p5_human_blind_qa_confirmed_candidate"] is False
    assert r16["p5_repair_return_candidate"] is False
    assert r16["p5_review_inconclusive"] is False
    assert r16["next_required_step"] == r51.P7_R51_R16_NEXT_REQUIRED_STEP_REF
    assert tuple(r16["implemented_steps"]) == r51.P7_R51_R16_IMPLEMENTED_STEPS
    assert tuple(r16["not_yet_implemented_steps"]) == r51.P7_R51_R16_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_release_promotion(r16)


def test_r51_r17_confirmed_candidate_does_not_promote_release_p7_or_p8() -> None:
    r9, r10, r11, r12 = _pass_chain()
    r16 = _r16_from_chain(r9, r10, r11, r12)
    r17 = r51.build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        body_free_post_review_summary_builder_bodyfree=r16
    )

    assert r17["schema_version"] == r51.P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION
    assert set(r17) == set(r51.P7_R51_P5_DECISION_BODYFREE_REQUIRED_FIELD_REFS)
    assert r17["p5_decision_status"] == "P5_CONFIRMED_CANDIDATE"
    assert r17["p5_human_blind_qa_confirmed_candidate"] is True
    assert r17["p5_human_blind_qa_confirmed"] is False
    assert r17["p5_repair_return_candidate"] is False
    assert r17["p5_review_inconclusive"] is False
    assert r17["p5_decision_candidate_only"] is True
    assert r17["release_allowed"] is False
    assert r17["p7_complete"] is False
    assert r17["p8_start_allowed"] is False
    assert r17["p8_question_design_material_candidate"] is False
    assert r17["next_required_step"] == r51.P7_R51_R17_CONFIRMED_NEXT_REQUIRED_STEP_REF
    assert tuple(r17["implemented_steps"]) == r51.P7_R51_R17_IMPLEMENTED_STEPS
    assert tuple(r17["not_yet_implemented_steps"]) == r51.P7_R51_R17_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_release_promotion(r17)


def test_r51_r17_repair_return_for_readfeel_blocker_or_axis_target_miss_without_p8_escape() -> None:
    rows = _base_pass_review_rows()
    rows[0]["axis_scores"] = {axis: 1.0 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES}
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.50
    rows[0]["verdict"] = "REPAIR_REQUIRED"
    rows[0]["blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["sanitized_reason_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["one_question_fit_ref"] = "repair_required_not_question"
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    r9, r10, r11, r12 = _r9_r10_r11_r12_from_rows(rows)
    assert r12["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    r16 = _r16_from_chain(r9, r10, r11, r12)
    r17 = r51.build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        body_free_post_review_summary_builder_bodyfree=r16
    )

    assert r17["p5_decision_status"] == "P5_REPAIR_RETURN_CANDIDATE"
    assert r17["p5_repair_return_candidate"] is True
    assert r17["p5_human_blind_qa_confirmed_candidate"] is False
    assert r17["p5_review_inconclusive"] is False
    assert r17["p5_repair_return_requirements_met"] is True
    assert r17["axis_target_missed_refs"] == []
    assert r17["readfeel_blocker_counts"] == {"p5_history_connection_too_generic": 1}
    assert r17["question_need_primary_class_counts"]["not_question_p5_surface_repair_required"] == 1
    assert r17["p8_question_design_material_candidate"] is False
    assert r17["next_required_step"] == r51.P7_R51_R17_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_release_promotion(r17)


def test_r51_r16_blocks_without_verified_disposal_and_r17_is_inconclusive() -> None:
    r9, r10, r11, r12 = _pass_chain()
    r16 = _r16_from_chain(r9, r10, r11, r12, verified_disposal=False)

    assert r16["post_review_summary_status"] == "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS"
    assert r16["disposal_verified"] is False
    assert r16["post_review_summary_materialized_here"] is False
    assert "r51_disposal" in r16["execution_blocker_ids"][0]
    assert r16["next_required_step"] == r51.P7_R51_R16_BLOCKED_NEXT_REQUIRED_STEP_REF

    r17 = r51.build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        body_free_post_review_summary_builder_bodyfree=r16
    )
    assert r17["p5_decision_status"] == "P5_REVIEW_INCONCLUSIVE"
    assert r17["p5_review_inconclusive"] is True
    assert r17["p5_human_blind_qa_confirmed_candidate"] is False
    assert r17["p5_repair_return_candidate"] is False
    assert r17["next_required_step"] == r51.P7_R51_R17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_release_promotion(r16)
    _assert_bodyfree_no_leak_or_release_promotion(r17)


def test_r51_r16_r17_contracts_reject_body_or_release_mutations() -> None:
    r9, r10, r11, r12 = _pass_chain()
    r16 = _r16_from_chain(r9, r10, r11, r12)
    r17 = r51.build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        body_free_post_review_summary_builder_bodyfree=r16
    )

    release_claim = deepcopy(r16)
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(release_claim)

    p8_claim = deepcopy(r17)
    p8_claim["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(p8_claim)

    body_claim = deepcopy(r17)
    body_claim["raw_input"] = "body must not enter R51 decision"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(body_claim)
