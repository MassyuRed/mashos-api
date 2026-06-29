# -*- coding: utf-8 -*-
"""R52-4/R52-5 tests for actual review evidence completeness and NO_GO."""

from __future__ import annotations

import pytest

import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52


def _minimal_r51_material(component_ref: str, **extra: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": r52.P7_R52_R51_REQUIRED_HANDOFF_SCHEMA_VERSION_BY_COMPONENT_REF[component_ref],
        "material_id": f"r51_bodyfree_{component_ref}",
        "r51_handoff_component_ref": component_ref,
        "body_free": True,
    }
    material.update(extra)
    return material


def _clean_r51_handoff_materials() -> list[dict[str, object]]:
    return [
        _minimal_r51_material(
            "r16_body_free_post_review_summary",
            actual_human_review_run_here=True,
            actual_rating_rows_materialized_here=True,
            actual_question_need_observation_rows_materialized_here=True,
            post_review_summary_materialized_here=True,
        ),
        _minimal_r51_material(
            "r17_p5_confirmed_repair_return_inconclusive_decision",
            p5_human_blind_qa_confirmed_candidate=True,
        ),
        _minimal_r51_material(
            "r18_p6_limited_human_readfeel_candidate_handoff",
            p6_limited_human_readfeel_start_allowed_candidate=True,
        ),
        _minimal_r51_material(
            "r19_p8_question_design_material_candidate_handoff",
            p8_question_design_material_candidate=True,
        ),
        _minimal_r51_material(
            "r20_no_body_leak_no_question_text_no_touch_boundary_validation",
            boundary_validation_status="R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED",
            next_required_step=r52.P7_R51_R20_NEXT_REQUIRED_STEP_REF,
        ),
    ]


def _clean_r3() -> dict[str, object]:
    return r52.build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials()
    )


def _complete_bodyfree_evidence() -> dict[str, object]:
    return {
        "review_session_status": "R51_POST_REVIEW_SUMMARY_READY",
        "rating_row_count": r52.P7_R51_REQUIRED_CASE_COUNT,
        "question_observation_row_count": r52.P7_R51_REQUIRED_CASE_COUNT,
        "r8_actual_human_review_run_recorded": True,
        "r9_rating_row_normalizer_built": True,
        "r10_readfeel_blocker_execution_blocker_ingestion_built": True,
        "r11_question_need_observation_row_normalizer_built": True,
        "r12_rating_question_observation_consistency_guard_built": True,
        "r14_body_full_packet_reviewer_notes_purge_built": True,
        "r15_disposal_receipt_builder_verifier_built": True,
        "r16_body_free_post_review_summary_builder_built": True,
        "r17_p5_confirmed_repair_return_inconclusive_decision_built": True,
        "r20_no_body_leak_no_question_text_no_touch_boundary_validation_built": True,
        "disposal_verified": True,
        "body_removed": True,
        "reviewer_notes_removed": True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "open_execution_blocker_count": 0,
        "body_free": True,
    }


def _assert_no_auto_allow(material: dict[str, object]) -> None:
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["question_trigger_logic_implemented_here"] is False
    assert material["r52_body_full_packet_generated_here"] is False
    assert material["r52_actual_human_review_run_here"] is False
    assert material["r52_actual_rating_rows_materialized_here"] is False
    assert material["r52_actual_question_need_observation_rows_materialized_here"] is False


def test_r52_r4_marks_current_missing_actual_review_evidence_without_creating_review_materials() -> None:
    completeness = r52.build_p7_r52_actual_review_evidence_completeness(forbidden_payload_deep_scan=_clean_r3())

    assert r52.assert_p7_r52_actual_review_evidence_completeness_contract(completeness) is True
    assert set(completeness) == set(r52.P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_REQUIRED_FIELD_REFS)
    assert completeness["schema_version"] == r52.P7_R52_ACTUAL_REVIEW_EVIDENCE_COMPLETENESS_SCHEMA_VERSION
    assert completeness["policy_section"] == r52.P7_R52_R4_STEP_REF
    assert completeness["r3_scan_ready_for_r52_4_evidence_check"] is True
    assert completeness["r51_actual_review_evidence_complete"] is False
    assert completeness["r51_actual_review_evidence_completeness_status"] == "R52_R51_ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert completeness["next_required_step"] == r52.P7_R52_R4_NEXT_REQUIRED_STEP_REF
    assert completeness["r52_4_actual_review_evidence_completeness_checker_built"] is True
    assert completeness["r52_5_evidence_missing_no_go_branch_built"] is False
    assert "r51_actual_human_review_run_missing" in completeness["missing_evidence_refs"]
    assert "r51_rating_rows_missing" in completeness["missing_evidence_refs"]
    assert "r51_question_need_observation_rows_missing" in completeness["missing_evidence_refs"]
    assert "r51_disposal_receipt_missing" in completeness["missing_evidence_refs"]
    assert completeness["r51_target_green_claimed_as_actual_review_complete"] is False
    assert completeness["r51_helper_ready_claimed_as_actual_review_complete"] is False
    assert tuple(completeness["implemented_steps"]) == r52.P7_R52_R4_IMPLEMENTED_STEPS
    assert tuple(completeness["not_yet_implemented_steps"]) == r52.P7_R52_R4_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_auto_allow(completeness)


def test_r52_r5_returns_to_r51_actual_review_when_evidence_is_missing() -> None:
    completeness = r52.build_p7_r52_actual_review_evidence_completeness(forbidden_payload_deep_scan=_clean_r3())
    branch = r52.build_p7_r52_evidence_missing_no_go_branch(actual_review_evidence_completeness=completeness)

    assert r52.assert_p7_r52_evidence_missing_no_go_branch_contract(branch) is True
    assert set(branch) == set(r52.P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_REQUIRED_FIELD_REFS)
    assert branch["schema_version"] == r52.P7_R52_EVIDENCE_MISSING_NO_GO_BRANCH_SCHEMA_VERSION
    assert branch["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert branch["decision_status"] == "RETURN_REQUIRED"
    assert branch["p5_decision_status"] == "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING"
    assert branch["next_required_step"] == r52.P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF
    assert branch["r51_actual_review_evidence_complete"] is False
    assert branch["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert branch["p8_question_design_material_candidate"] is False
    assert "r51_p5_confirmed_final_missing" in branch["decision_reason_refs"]
    assert branch["r52_5_evidence_missing_no_go_branch_built"] is True
    assert tuple(branch["implemented_steps"]) == r52.P7_R52_R5_IMPLEMENTED_STEPS
    assert tuple(branch["not_yet_implemented_steps"]) == r52.P7_R52_R5_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_auto_allow(branch)


def test_r52_r4_accepts_complete_bodyfree_evidence_but_does_not_create_release_or_start_candidates() -> None:
    completeness = r52.build_p7_r52_actual_review_evidence_completeness(
        forbidden_payload_deep_scan=_clean_r3(),
        r51_actual_review_evidence=_complete_bodyfree_evidence(),
    )

    assert completeness["r51_actual_review_evidence_complete"] is True
    assert completeness["r51_actual_review_evidence_completeness_status"] == "R52_R51_ACTUAL_REVIEW_EVIDENCE_COMPLETE"
    assert completeness["missing_evidence_refs"] == []
    assert completeness["rating_row_count"] == r52.P7_R51_REQUIRED_CASE_COUNT
    assert completeness["question_observation_row_count"] == r52.P7_R51_REQUIRED_CASE_COUNT
    assert completeness["disposal_verified"] is True
    assert completeness["body_removed"] is True
    assert completeness["reviewer_notes_removed"] is True
    assert completeness["local_packet_exported"] is False
    assert completeness["content_hash_of_body_stored"] is False
    assert completeness["r52_4_actual_review_evidence_completeness_checker_built"] is True
    _assert_no_auto_allow(completeness)


def test_r52_r5_complete_evidence_still_keeps_p6_p8_p7_release_as_no_auto_allow() -> None:
    completeness = r52.build_p7_r52_actual_review_evidence_completeness(
        forbidden_payload_deep_scan=_clean_r3(),
        r51_actual_review_evidence=_complete_bodyfree_evidence(),
    )
    branch = r52.build_p7_r52_evidence_missing_no_go_branch(actual_review_evidence_completeness=completeness)

    assert branch["r51_actual_review_evidence_complete"] is True
    assert branch["decision_ref"] == "R52_NO_GO_P6_P8_START"
    assert branch["decision_status"] == "CANDIDATE_ONLY"
    assert branch["next_required_step"] == r52.P7_R52_R5_NEXT_REQUIRED_STEP_REF
    assert branch["p5_decision_status"] == "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
    assert branch["missing_evidence_refs"] == []
    assert branch["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert branch["p8_question_design_material_candidate"] is False
    _assert_no_auto_allow(branch)


@pytest.mark.parametrize("forbidden_key", ["raw_input", "comment_text_body", "reviewer_free_text", "question_text", "local_absolute_path", "body_content_hash", "terminal_output"])
def test_r52_r4_blocks_forbidden_actual_review_evidence_payloads_without_copying_body(forbidden_key: str) -> None:
    evidence = dict(_complete_bodyfree_evidence())
    evidence[forbidden_key] = "this body must not be accepted or copied"

    completeness = r52.build_p7_r52_actual_review_evidence_completeness(
        forbidden_payload_deep_scan=_clean_r3(),
        r51_actual_review_evidence=evidence,
    )
    branch = r52.build_p7_r52_evidence_missing_no_go_branch(actual_review_evidence_completeness=completeness)

    assert completeness["r51_actual_review_evidence_complete"] is False
    assert completeness["r51_actual_review_evidence_completeness_status"] == "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_BODY_FREE_BOUNDARY_RISK"
    assert completeness["forbidden_payload_keys_absent"] is False
    assert any(path.endswith(f".{forbidden_key}") for path in completeness["detected_forbidden_payload_key_paths"])
    assert completeness["r52_4_actual_review_evidence_completeness_checker_built"] is False
    assert forbidden_key not in completeness
    assert branch["decision_ref"] == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    assert branch["decision_status"] == "BLOCKED"
    assert branch["r52_5_evidence_missing_no_go_branch_built"] is False
    _assert_no_auto_allow(completeness)
    _assert_no_auto_allow(branch)


@pytest.mark.parametrize("forbidden_flag", ["p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "release_allowed", "api_db_rn_response_key_changed_here"])
def test_r52_r4_blocks_forbidden_true_flags_inside_actual_review_evidence(forbidden_flag: str) -> None:
    evidence = dict(_complete_bodyfree_evidence())
    evidence[forbidden_flag] = True

    completeness = r52.build_p7_r52_actual_review_evidence_completeness(
        forbidden_payload_deep_scan=_clean_r3(),
        r51_actual_review_evidence=evidence,
    )

    assert completeness["r51_actual_review_evidence_completeness_status"] == "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_BODY_FREE_BOUNDARY_RISK"
    assert completeness["forbidden_true_flags_absent"] is False
    assert any(path.endswith(f".{forbidden_flag}") for path in completeness["detected_forbidden_true_flag_paths"])
    assert completeness["r52_4_actual_review_evidence_completeness_checker_built"] is False
    _assert_no_auto_allow(completeness)


def test_r52_r4_blocks_when_r3_handoff_scan_is_not_ready() -> None:
    r3 = r52.build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(r51_bodyfree_handoff_materials=[])
    completeness = r52.build_p7_r52_actual_review_evidence_completeness(forbidden_payload_deep_scan=r3)

    assert completeness["r3_scan_ready_for_r52_4_evidence_check"] is False
    assert completeness["r51_actual_review_evidence_completeness_status"] == "R52_R51_ACTUAL_REVIEW_EVIDENCE_BLOCKED_BY_R3"
    assert completeness["r52_4_actual_review_evidence_completeness_checker_built"] is False
    assert tuple(completeness["implemented_steps"]) == r52.P7_R52_R3_IMPLEMENTED_STEPS
    assert tuple(completeness["not_yet_implemented_steps"]) == r52.P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_auto_allow(completeness)


def test_r52_r0_r5_chain_uses_bodyfree_clean_handoff_and_returns_to_r51_when_actual_review_rows_are_missing() -> None:
    branch = r52.build_p7_r52_r0_r5_actual_review_evidence_missing_no_go_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials()
    )

    assert branch["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert branch["next_required_step"] == r52.P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF
    assert branch["r51_actual_review_evidence_complete"] is False
    assert "r51_actual_human_review_run_missing" in branch["missing_evidence_refs"]
    _assert_no_auto_allow(branch)
