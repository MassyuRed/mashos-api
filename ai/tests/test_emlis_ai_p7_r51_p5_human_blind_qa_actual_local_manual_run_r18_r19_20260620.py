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
FORBIDDEN_ALLOWED_PROMOTION_TOKENS = (
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
    '"p8_question_implementation_spec_finalized_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"full_backend_suite_green_confirmed": true',
)


def _assert_bodyfree_no_leak_or_allowed_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_BODY_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_ALLOWED_PROMOTION_TOKENS:
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


def _confirmed_r16_r17() -> tuple[dict[str, object], dict[str, object]]:
    r9, r10, r11, r12 = _pass_chain()
    r16 = _r16_from_chain(r9, r10, r11, r12)
    r17 = r51.build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        body_free_post_review_summary_builder_bodyfree=r16
    )
    assert r51.assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(r17) is True
    return r16, r17


def _repair_r17() -> dict[str, object]:
    rows = _base_pass_review_rows()
    rows[0]["verdict"] = "REPAIR_REQUIRED"
    rows[0]["blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["sanitized_reason_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["one_question_fit_ref"] = "repair_required_not_question"
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    r9, r10, r11, r12 = _r9_r10_r11_r12_from_rows(rows)
    r16 = _r16_from_chain(r9, r10, r11, r12)
    r17 = r51.build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        body_free_post_review_summary_builder_bodyfree=r16
    )
    assert r17["p5_decision_status"] == "P5_REPAIR_RETURN_CANDIDATE"
    return r17


def test_r51_r18_p6_candidate_handoff_ready_but_start_not_allowed() -> None:
    _, r17 = _confirmed_r16_r17()
    r18 = r51.build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree=r17
    )

    assert r18["schema_version"] == r51.P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert set(r18) == set(r51.P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS)
    assert r18["policy_section"] == "R51-18_p6_limited_human_readfeel_candidate_handoff"
    assert r18["p6_candidate_handoff_status"] == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY"
    assert r18["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert r18["p6_limited_human_readfeel_start_allowed"] is False
    assert r18["p5_weakness_not_hidden_by_p6"] is True
    assert r18["p5_repair_not_compensated_by_p6"] is True
    assert r18["p8_question_design_material_candidate"] is False
    assert r18["next_required_step"] == r51.P7_R51_R18_NEXT_REQUIRED_STEP_REF
    assert tuple(r18["implemented_steps"]) == r51.P7_R51_R18_IMPLEMENTED_STEPS
    assert tuple(r18["not_yet_implemented_steps"]) == r51.P7_R51_R18_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_allowed_promotion(r18)


def test_r51_r19_p8_material_candidate_ready_without_starting_p8_or_question_implementation() -> None:
    r16, r17 = _confirmed_r16_r17()
    r18 = r51.build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree=r17
    )
    r19 = r51.build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=r18,
        body_free_post_review_summary_builder_bodyfree=r16,
    )

    assert r19["schema_version"] == r51.P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert set(r19) == set(r51.P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_REQUIRED_FIELD_REFS)
    assert r19["policy_section"] == "R51-19_p8_question_design_material_candidate_handoff"
    assert r19["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    assert r19["p8_question_design_material_candidate"] is True
    assert r19["p8_start_allowed"] is False
    assert r19["question_implementation_not_started"] is True
    assert r19["question_trigger_logic_implemented_here"] is False
    assert r19["api_db_rn_response_key_changed_here"] is False
    assert r19["question_need_primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert r19["ambiguity_kind_counts"] == {"no_material_ambiguity": 24}
    assert r19["one_question_fit_counts"] == {"not_needed": 24}
    assert r19["repair_required_counts"] == {"no_repair_required": 24}
    assert r19["next_required_step"] == r51.P7_R51_R19_NEXT_REQUIRED_STEP_REF
    assert tuple(r19["implemented_steps"]) == r51.P7_R51_R19_IMPLEMENTED_STEPS
    assert tuple(r19["not_yet_implemented_steps"]) == r51.P7_R51_R19_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_allowed_promotion(r19)


def test_r51_r18_blocks_p6_candidate_when_p5_repair_return_is_required() -> None:
    r17 = _repair_r17()
    r18 = r51.build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree=r17
    )

    assert r18["p6_candidate_handoff_status"] == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION"
    assert r18["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert r18["p6_limited_human_readfeel_start_allowed"] is False
    assert r18["p5_repair_return_candidate"] is True
    assert "p5_repair_or_inconclusive_must_be_resolved_before_p6_candidate" in r18["missing_requirement_refs"]
    assert r18["next_required_step"] == r51.P7_R51_R18_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_allowed_promotion(r18)


def test_r51_r19_blocks_p8_material_when_summary_counts_are_missing_or_p5_is_repair() -> None:
    repair_r17 = _repair_r17()
    r18 = r51.build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree=repair_r17
    )
    r19 = r51.build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=r18
    )

    assert r19["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS"
    assert r19["p8_question_design_material_candidate"] is False
    assert r19["p8_start_allowed"] is False
    assert "p5_repair_or_inconclusive_must_not_feed_p8_material" in r19["missing_requirement_refs"]
    assert "bodyfree_question_observation_counts_required" in r19["missing_requirement_refs"]
    assert r19["next_required_step"] == r51.P7_R51_R19_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_allowed_promotion(r19)


def test_r51_r18_r19_contracts_reject_allowed_or_body_mutations() -> None:
    r16, r17 = _confirmed_r16_r17()
    r18 = r51.build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree=r17
    )
    r19 = r51.build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=r18,
        body_free_post_review_summary_builder_bodyfree=r16,
    )

    p6_start_claim = deepcopy(r18)
    p6_start_claim["p6_limited_human_readfeel_start_allowed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(p6_start_claim)

    p8_start_claim = deepcopy(r19)
    p8_start_claim["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(p8_start_claim)

    body_claim = deepcopy(r19)
    body_claim["raw_input"] = "body must not enter R51 P8 material handoff"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(body_claim)
