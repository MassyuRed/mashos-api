# -*- coding: utf-8 -*-
"""R52-6/R52-7 tests for disposal safety and execution blocker gates."""

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


def _complete_bodyfree_evidence(**overrides: object) -> dict[str, object]:
    evidence: dict[str, object] = {
        "review_session_status": "R51_POST_REVIEW_SUMMARY_READY",
        "rating_row_count": r52.P7_R51_REQUIRED_CASE_COUNT,
        "question_observation_row_count": r52.P7_R51_REQUIRED_CASE_COUNT,
        "r8_actual_human_review_run_recorded": True,
        "r51_actual_body_full_material_created": True,
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
    evidence.update(overrides)
    return evidence


def _r4(evidence: dict[str, object] | None = None) -> dict[str, object]:
    return r52.build_p7_r52_actual_review_evidence_completeness(
        forbidden_payload_deep_scan=_clean_r3(),
        r51_actual_review_evidence=evidence,
    )


def _r5(r4: dict[str, object]) -> dict[str, object]:
    return r52.build_p7_r52_evidence_missing_no_go_branch(actual_review_evidence_completeness=r4)


def _assert_no_auto_allow(material: dict[str, object]) -> None:
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["question_trigger_logic_implemented_here"] is False
    assert material["r52_body_full_packet_generated_here"] is False
    assert material["r52_actual_disposal_run_here"] is False
    assert material["r52_disposal_verification_created_here"] is False
    assert material["r52_disposal_gate_created_bodyfull_receipt_here"] is False
    assert material["r52_execution_blocker_rows_created_here"] is False
    assert material["r52_execution_blocker_resolution_run_here"] is False
    assert material["r51_disposal_receipt_created_here"] is False
    assert material["execution_blocker_cleared_here"] is False


def test_r52_r6_r7_steps_remain_in_current_capability_after_final_r52_steps_are_added() -> None:
    assert r52.P7_R52_R6_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R7_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R8_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R9_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R10_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R11_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R12_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R13_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R14_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R15_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert tuple(r52.P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS) == r52.P7_R52_R15_NOT_YET_IMPLEMENTED_STEPS
    assert r52.P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS == ()


def test_r52_r6_preserves_r5_return_to_r51_when_actual_review_has_not_started() -> None:
    r4 = _r4()
    r5 = _r5(r4)
    gate = r52.build_p7_r52_disposal_safety_gate(
        actual_review_evidence_completeness=r4,
        evidence_missing_no_go_branch=r5,
    )

    assert r52.assert_p7_r52_disposal_safety_gate_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_DISPOSAL_SAFETY_GATE_REQUIRED_FIELD_REFS)
    assert gate["schema_version"] == r52.P7_R52_DISPOSAL_SAFETY_GATE_SCHEMA_VERSION
    assert gate["policy_section"] == r52.P7_R52_R6_STEP_REF
    assert gate["r51_actual_review_or_body_full_material_created"] is False
    assert gate["disposal_safety_required"] is False
    assert gate["disposal_safety_gate_status"] == "R52_DISPOSAL_SAFETY_GATE_NOT_APPLICABLE_ACTUAL_REVIEW_NOT_STARTED"
    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["next_required_step"] == r52.P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF
    assert gate["r52_6_disposal_safety_gate_built"] is True
    assert gate["r52_6_ready_for_r52_7_execution_blocker_gate"] is False
    assert gate["r52_7_execution_blocker_gate_built"] is False
    _assert_no_auto_allow(gate)


def test_r52_r6_blocks_disposal_not_verified_when_bodyfull_material_was_created() -> None:
    evidence = _complete_bodyfree_evidence(
        disposal_verified=False,
        body_removed=False,
        reviewer_notes_removed=False,
    )
    r4 = _r4(evidence)
    r5 = _r5(r4)
    gate = r52.build_p7_r52_disposal_safety_gate(
        actual_review_evidence_completeness=r4,
        evidence_missing_no_go_branch=r5,
        r51_actual_review_evidence=evidence,
    )

    assert gate["r51_actual_body_full_material_created"] is True
    assert gate["r51_actual_review_or_body_full_material_created"] is True
    assert gate["disposal_safety_required"] is True
    assert gate["disposal_safety_gate_status"] == "R52_DISPOSAL_SAFETY_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
    assert gate["decision_ref"] == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["p5_decision_status"] == "R52_P5_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
    assert "r51_disposal_verified_missing_after_body_full_material_created" in gate["disposal_not_verified_reason_refs"]
    assert "r51_body_full_packet_body_removed_not_verified" in gate["disposal_not_verified_reason_refs"]
    assert "r51_reviewer_notes_removed_not_verified" in gate["disposal_not_verified_reason_refs"]
    assert "r51_actual_review_or_body_full_material_created_without_verified_disposal" in gate["decision_reason_refs"]
    assert gate["r52_6_ready_for_r52_7_execution_blocker_gate"] is False
    assert gate["next_required_step"] == r52.P7_R52_R6_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(gate)


def test_r52_r6_passes_complete_disposed_evidence_only_to_execution_blocker_gate() -> None:
    evidence = _complete_bodyfree_evidence()
    r4 = _r4(evidence)
    r5 = _r5(r4)
    gate = r52.build_p7_r52_disposal_safety_gate(
        actual_review_evidence_completeness=r4,
        evidence_missing_no_go_branch=r5,
        r51_actual_review_evidence=evidence,
    )

    assert gate["r51_actual_review_evidence_complete"] is True
    assert gate["r51_actual_body_full_material_created"] is True
    assert gate["disposal_verified"] is True
    assert gate["body_removed"] is True
    assert gate["reviewer_notes_removed"] is True
    assert gate["disposal_safety_gate_status"] == "R52_DISPOSAL_SAFETY_GATE_PASSED"
    assert gate["decision_ref"] == "R52_NO_GO_P6_P8_START"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["next_required_step"] == r52.P7_R52_R6_NEXT_REQUIRED_STEP_REF
    assert gate["r52_6_ready_for_r52_7_execution_blocker_gate"] is True
    assert tuple(gate["implemented_steps"]) == r52.P7_R52_R6_IMPLEMENTED_STEPS
    assert tuple(gate["not_yet_implemented_steps"]) == r52.P7_R52_R6_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_auto_allow(gate)


def test_r52_r7_blocks_open_execution_blocker_after_disposal_is_safe() -> None:
    evidence = _complete_bodyfree_evidence(open_execution_blocker_count=2)
    gate = r52.build_p7_r52_r0_r7_disposal_execution_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
        r51_actual_review_evidence=evidence,
    )

    assert r52.assert_p7_r52_execution_blocker_gate_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_EXECUTION_BLOCKER_GATE_REQUIRED_FIELD_REFS)
    assert gate["schema_version"] == r52.P7_R52_EXECUTION_BLOCKER_GATE_SCHEMA_VERSION
    assert gate["policy_section"] == r52.P7_R52_R7_STEP_REF
    assert gate["r6_disposal_gate_status"] == "R52_DISPOSAL_SAFETY_GATE_PASSED"
    assert gate["r6_ready_for_r52_7_execution_blocker_gate"] is True
    assert gate["open_execution_blocker_count"] == 2
    assert gate["execution_blocker_gate_status"] == "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
    assert gate["decision_ref"] == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["p5_decision_status"] == "R52_P5_BLOCKED_BY_EXECUTION_BLOCKER"
    assert "r51_execution_blocker_open" in gate["execution_blocker_reason_refs"]
    assert gate["next_required_step"] == r52.P7_R52_R7_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert gate["r52_7_execution_blocker_gate_built"] is True
    _assert_no_auto_allow(gate)


def test_r52_r7_passes_clean_execution_blocker_gate_to_r8_candidate_only_without_auto_allow() -> None:
    gate = r52.build_p7_r52_r0_r7_disposal_execution_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
        r51_actual_review_evidence=_complete_bodyfree_evidence(),
    )

    assert gate["r51_actual_review_evidence_complete"] is True
    assert gate["open_execution_blocker_count"] == 0
    assert gate["execution_blocker_gate_status"] == "R52_EXECUTION_BLOCKER_GATE_PASSED"
    assert gate["decision_ref"] == "R52_NO_GO_P6_P8_START"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["p5_decision_status"] == "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
    assert gate["next_required_step"] == r52.P7_R52_R7_NEXT_REQUIRED_STEP_REF
    assert tuple(gate["implemented_steps"]) == r52.P7_R52_R7_IMPLEMENTED_STEPS
    assert tuple(gate["not_yet_implemented_steps"]) == r52.P7_R52_R7_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_auto_allow(gate)


def test_r52_r7_keeps_return_to_r51_when_no_review_started_and_r6_not_ready() -> None:
    gate = r52.build_p7_r52_r0_r7_disposal_execution_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
    )

    assert gate["r6_disposal_gate_status"] == "R52_DISPOSAL_SAFETY_GATE_NOT_APPLICABLE_ACTUAL_REVIEW_NOT_STARTED"
    assert gate["r6_ready_for_r52_7_execution_blocker_gate"] is False
    assert gate["execution_blocker_gate_status"] == "R52_EXECUTION_BLOCKER_GATE_NOT_REACHED_BY_R6"
    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["next_required_step"] == r52.P7_R52_R5_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF
    assert gate["r52_6_disposal_safety_gate_built"] is True
    assert gate["r52_7_execution_blocker_gate_built"] is False
    _assert_no_auto_allow(gate)


def test_r52_r7_preserves_disposal_blocker_and_does_not_resolve_it() -> None:
    evidence = _complete_bodyfree_evidence(disposal_verified=False)
    gate = r52.build_p7_r52_r0_r7_disposal_execution_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
        r51_actual_review_evidence=evidence,
    )

    assert gate["r6_disposal_gate_status"] == "R52_DISPOSAL_SAFETY_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
    assert gate["execution_blocker_gate_status"] == "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
    assert gate["decision_ref"] == "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["r52_7_execution_blocker_gate_built"] is False
    assert gate["execution_blocker_cleared_here"] is False
    _assert_no_auto_allow(gate)


def test_r52_r7_returns_to_r51_when_disposal_is_safe_but_non_execution_evidence_is_missing() -> None:
    evidence = _complete_bodyfree_evidence(rating_row_count=1)
    gate = r52.build_p7_r52_r0_r7_disposal_execution_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
        r51_actual_review_evidence=evidence,
    )

    assert gate["r6_disposal_gate_status"] == "R52_DISPOSAL_SAFETY_GATE_PASSED"
    assert gate["execution_blocker_open"] is False
    assert gate["execution_blocker_gate_status"] == "R52_EXECUTION_BLOCKER_GATE_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["r52_7_execution_blocker_gate_built"] is True
    _assert_no_auto_allow(gate)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "execution_blocker_cleared_here",
        "r52_disposal_verification_created_here",
        "r52_execution_blocker_resolution_run_here",
    ],
)
def test_r52_r6_r7_contracts_reject_forbidden_auto_allow_or_resolution_flags(forbidden_key: str) -> None:
    evidence = _complete_bodyfree_evidence()
    r6 = r52.build_p7_r52_disposal_safety_gate(
        actual_review_evidence_completeness=_r4(evidence),
        r51_actual_review_evidence=evidence,
    )
    bad_r6 = dict(r6)
    bad_r6[forbidden_key] = True
    with pytest.raises(ValueError):
        r52.assert_p7_r52_disposal_safety_gate_contract(bad_r6)

    r7 = r52.build_p7_r52_execution_blocker_gate(
        disposal_safety_gate=r6,
        actual_review_evidence_completeness=_r4(evidence),
        r51_actual_review_evidence=evidence,
    )
    bad_r7 = dict(r7)
    bad_r7[forbidden_key] = True
    with pytest.raises(ValueError):
        r52.assert_p7_r52_execution_blocker_gate_contract(bad_r7)


@pytest.mark.parametrize("forbidden_key", ["raw_input", "comment_text_body", "reviewer_free_text", "question_text", "local_absolute_path", "body_content_hash", "terminal_output"])
def test_r52_r6_r7_chain_blocks_forbidden_payload_without_copying_body(forbidden_key: str) -> None:
    evidence = _complete_bodyfree_evidence(**{forbidden_key: "SHOULD_NOT_SURFACE"})
    gate = r52.build_p7_r52_r0_r7_disposal_execution_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
        r51_actual_review_evidence=evidence,
    )

    rendered = repr(gate)
    assert "SHOULD_NOT_SURFACE" not in rendered
    assert gate["decision_ref"] == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["execution_blocker_gate_status"] == "R52_EXECUTION_BLOCKER_GATE_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    _assert_no_auto_allow(gate)
