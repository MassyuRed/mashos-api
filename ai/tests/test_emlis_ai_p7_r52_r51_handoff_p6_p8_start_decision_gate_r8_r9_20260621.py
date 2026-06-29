# -*- coding: utf-8 -*-
"""R52-8/R52-9 tests for rating-question consistency and P5 readfeel blockers."""

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
        "rating_question_consistency_status": "passed",
        "repair_required_not_question_count": 0,
        "p8_candidate_repair_required_not_question_count": 0,
        "red_or_repair_required_question_candidate_count": 0,
        "red_question_candidate_count": 0,
        "repair_required_question_candidate_count": 0,
        "repair_required_not_question_mixed_into_p8_candidate": False,
        "red_or_repair_required_treated_as_question_candidate": False,
        "p5_weakness_not_hidden_by_question_candidate": True,
        "red_count": 0,
        "repair_required_count": 0,
        "critical_repair_blocker_count": 0,
        "creepy_or_surveillance_blocker_count": 0,
        "overclaim_blocker_count": 0,
        "self_blame_amplification_blocker_count": 0,
        "p5_surface_or_gate_repair_observation_count": 0,
        "emlis_readfeel_repair_observation_count": 0,
        "history_connection_naturalness_below_target_count": 0,
        "all_axis_targets_met": True,
        "axis_target_missed_refs": [],
        "body_free": True,
    }
    evidence.update(overrides)
    return evidence


def _r7(evidence: dict[str, object] | None = None) -> dict[str, object]:
    return r52.build_p7_r52_r0_r7_disposal_execution_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
        r51_actual_review_evidence=evidence,
    )


def _r8(evidence: dict[str, object] | None = None) -> dict[str, object]:
    return r52.build_p7_r52_rating_question_consistency_gate(
        execution_blocker_gate=_r7(evidence),
        r51_actual_review_evidence=evidence,
    )


def _r9(evidence: dict[str, object] | None = None) -> dict[str, object]:
    return r52.build_p7_r52_r0_r9_rating_question_p5_readfeel_gate_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
        r51_actual_review_evidence=evidence,
    )


def _assert_no_auto_allow(material: dict[str, object]) -> None:
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    for false_key in r52.P7_R52_R8_R9_FALSE_KEY_REFS:
        assert material[false_key] is False


def test_r52_current_capability_constants_include_r0_to_r15_after_final_steps_are_added() -> None:
    assert tuple(r52.P7_R52_CURRENT_IMPLEMENTED_STEPS) == r52.P7_R52_R15_IMPLEMENTED_STEPS
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


def test_r52_r8_passes_clean_rating_question_consistency_without_p8_candidate() -> None:
    gate = _r8(_complete_bodyfree_evidence())

    assert r52.assert_p7_r52_rating_question_consistency_gate_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_R8_REQUIRED_FIELD_REFS)
    assert gate["rating_question_consistency_status"] == "passed"
    assert gate["rating_question_consistency_passed"] is True
    assert gate["rating_question_consistency_issue_detected"] is False
    assert gate["rating_question_consistency_gate_status"] == "R52_RATING_QUESTION_CONSISTENCY_GATE_PASSED"
    assert gate["decision_ref"] == "R52_NO_GO_P6_P8_START"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["next_required_step"] == r52.P7_R52_R8_NEXT_REQUIRED_STEP_REF
    assert gate["r52_8_rating_question_consistency_gate_built"] is True
    assert gate["r52_8_ready_for_r52_9_p5_readfeel_blocker_gate"] is True
    _assert_no_auto_allow(gate)


@pytest.mark.parametrize(
    "overrides, expected_reason",
    [
        ({"rating_question_consistency_status": "failed"}, "r51_rating_question_consistency_not_passed"),
        ({"repair_required_not_question_count": 2}, "repair_required_not_question_must_not_be_classified_as_p8_material"),
        ({"p8_candidate_repair_required_not_question_count": 1}, "repair_required_not_question_misclassified_as_p8_candidate"),
        ({"repair_required_not_question_mixed_into_p8_candidate": True}, "repair_required_not_question_mixed_into_p8_candidate"),
        ({"red_or_repair_required_question_candidate_count": 1}, "red_or_repair_required_routed_to_question_candidate"),
        ({"red_or_repair_required_treated_as_question_candidate": True}, "red_or_repair_required_treated_as_question_candidate"),
        ({"p5_weakness_not_hidden_by_question_candidate": False}, "p5_weakness_hidden_by_question_candidate"),
    ],
)
def test_r52_r8_blocks_rating_question_inconsistency_without_promoting_repair_to_p8(
    overrides: dict[str, object], expected_reason: str
) -> None:
    gate = _r8(_complete_bodyfree_evidence(**overrides))

    assert gate["rating_question_consistency_issue_detected"] is True
    assert gate["rating_question_consistency_gate_status"] == "R52_RATING_QUESTION_CONSISTENCY_GATE_BLOCKED_BY_CONSISTENCY_ISSUE"
    assert gate["decision_ref"] == "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["p5_decision_status"] == "R52_P5_BLOCKED_BY_CONSISTENCY_ISSUE"
    assert expected_reason in gate["rating_question_consistency_issue_reason_refs"]
    assert gate["next_required_step"] == r52.P7_R52_R8_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert gate["r52_8_ready_for_r52_9_p5_readfeel_blocker_gate"] is False
    _assert_no_auto_allow(gate)


def test_r52_r8_preserves_execution_blocker_before_consistency_check() -> None:
    gate = _r8(_complete_bodyfree_evidence(open_execution_blocker_count=1))

    assert gate["decision_ref"] == "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["r52_8_rating_question_consistency_gate_built"] is False
    assert gate["r52_8_ready_for_r52_9_p5_readfeel_blocker_gate"] is False
    _assert_no_auto_allow(gate)


@pytest.mark.parametrize(
    "overrides, expected_reason",
    [
        ({"red_count": 1}, "r51_red_count_positive"),
        ({"repair_required_count": 1}, "r51_repair_required_count_positive"),
        ({"critical_repair_blocker_count": 1}, "r51_critical_repair_blocker_count_positive"),
        ({"creepy_or_surveillance_blocker_count": 1}, "r51_creepy_or_surveillance_blocker_count_positive"),
        ({"overclaim_blocker_count": 1}, "r51_overclaim_blocker_count_positive"),
        ({"self_blame_amplification_blocker_count": 1}, "r51_self_blame_amplification_blocker_count_positive"),
        ({"p5_surface_or_gate_repair_observation_count": 1}, "r51_p5_surface_or_gate_repair_observation_count_positive"),
        ({"emlis_readfeel_repair_observation_count": 1}, "r51_emlis_readfeel_repair_observation_count_positive"),
        ({"history_connection_naturalness_below_target_count": 1}, "history_connection_naturalness_below_target"),
        ({"axis_target_missed_refs": ["read_feeling_target_missed"]}, "r51_axis_target_missed"),
        ({"all_axis_targets_met": False}, "r51_axis_targets_not_met"),
    ],
)
def test_r52_r9_returns_to_p5_repair_when_readfeel_blockers_exist(
    overrides: dict[str, object], expected_reason: str
) -> None:
    gate = _r9(_complete_bodyfree_evidence(**overrides))

    assert r52.assert_p7_r52_p5_readfeel_blocker_gate_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_R9_REQUIRED_FIELD_REFS)
    assert gate["p5_readfeel_blocker_present"] is True
    assert gate["p5_readfeel_blocker_detected"] is True
    assert gate["decision_ref"] == "R52_RETURN_TO_P5_REPAIR_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["p5_decision_status"] == "R52_P5_REPAIR_REQUIRED"
    assert expected_reason in gate["p5_readfeel_blocker_reason_refs"]
    assert gate["next_required_step"] == r52.P7_R52_R9_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert gate["r52_9_p5_readfeel_blocker_gate_built"] is True
    _assert_no_auto_allow(gate)


def test_r52_r9_clean_p5_readfeel_remains_no_go_candidate_only_not_release() -> None:
    gate = _r9(_complete_bodyfree_evidence())

    assert r52.assert_p7_r52_p5_readfeel_blocker_gate_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_R9_REQUIRED_FIELD_REFS)
    assert gate["p5_readfeel_blocker_present"] is False
    assert gate["p5_readfeel_blocker_detected"] is False
    assert gate["p5_readfeel_repair_required"] is False
    assert gate["p5_readfeel_blocker_gate_status"] == "R52_P5_READFEEL_BLOCKER_GATE_PASSED"
    assert gate["decision_ref"] == "R52_NO_GO_P6_P8_START"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["next_required_step"] == r52.P7_R52_R9_NEXT_REQUIRED_STEP_REF
    assert gate["p5_decision_status"] == "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
    assert gate["r52_9_p5_readfeel_blocker_gate_built"] is True
    _assert_no_auto_allow(gate)


def test_r52_r9_preserves_r8_rating_question_blocker_and_does_not_run_readfeel_gate() -> None:
    gate = _r9(_complete_bodyfree_evidence(repair_required_not_question_count=1))

    assert gate["decision_ref"] == "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["p5_decision_status"] == "R52_P5_BLOCKED_BY_CONSISTENCY_ISSUE"
    assert gate["p5_readfeel_blocker_gate_status"] == "R52_P5_READFEEL_BLOCKER_GATE_BLOCKED_BY_CONSISTENCY_ISSUE"
    assert gate["r52_9_p5_readfeel_blocker_gate_built"] is False
    _assert_no_auto_allow(gate)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "r52_p8_material_candidate_promoted_here",
        "repair_required_not_question_promoted_to_p8_candidate_here",
        "red_or_repair_required_question_candidate_promoted_here",
        "r52_p5_readfeel_blocker_resolved_here",
        "p5_readfeel_blocker_ignored_for_p6_p8_start_here",
        "p5_repair_required_hidden_by_p6_or_p8_candidate_here",
    ],
)
def test_r52_r8_r9_contracts_reject_auto_allow_p8_escape_or_repair_resolution_flags(forbidden_key: str) -> None:
    clean_gate = _r9(_complete_bodyfree_evidence())
    tampered = dict(clean_gate)
    tampered[forbidden_key] = True

    with pytest.raises(ValueError):
        r52.assert_p7_r52_p5_readfeel_blocker_gate_contract(tampered)


def test_r52_r8_r9_chain_blocks_forbidden_payload_without_copying_body() -> None:
    gate = _r9(_complete_bodyfree_evidence(raw_input="this raw body must not be copied"))

    assert gate["decision_ref"] == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["p5_decision_status"] == "R52_P5_BLOCKED_BY_BOUNDARY_RISK"
    assert "this raw body must not be copied" not in repr(gate)
    assert gate["p6_limited_human_readfeel_start_allowed"] is False
    assert gate["p8_start_allowed"] is False
    assert gate["release_allowed"] is False
