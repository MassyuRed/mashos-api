# -*- coding: utf-8 -*-
"""R52-10/R52-11 tests for P5 confirmed candidate and P6 candidate separation."""

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


def _clean_r51_handoff_materials(*, include_p6_candidate: bool = True) -> list[dict[str, object]]:
    r18_extra: dict[str, object] = {}
    if include_p6_candidate:
        r18_extra["p6_limited_human_readfeel_start_allowed_candidate"] = True
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
            **r18_extra,
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
        "p6_limited_family_scope_supported": True,
        "p5_weakness_not_hidden_by_p6_candidate": True,
        "body_free": True,
    }
    evidence.update(overrides)
    return evidence


def _r10(evidence: dict[str, object] | None = None, *, include_p6_candidate: bool = True) -> dict[str, object]:
    return r52.build_p7_r52_r0_r10_p5_confirmed_candidate_decision_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(include_p6_candidate=include_p6_candidate),
        r51_actual_review_evidence=evidence,
    )


def _r11(evidence: dict[str, object] | None = None, *, include_p6_candidate: bool = True) -> dict[str, object]:
    return r52.build_p7_r52_r0_r11_p6_limited_human_readfeel_candidate_separation_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(include_p6_candidate=include_p6_candidate),
        r51_actual_review_evidence=evidence,
    )


def _assert_never_auto_allows(material: dict[str, object]) -> None:
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["p5_human_blind_qa_confirmed"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False


def test_r52_current_capability_constants_include_r10_to_r15_after_final_steps_are_added() -> None:
    assert r52.P7_R52_R10_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R11_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R12_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R13_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R14_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R15_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert tuple(r52.P7_R52_CURRENT_IMPLEMENTED_STEPS) == r52.P7_R52_R15_IMPLEMENTED_STEPS
    assert tuple(r52.P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS) == r52.P7_R52_R15_NOT_YET_IMPLEMENTED_STEPS
    assert r52.P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS == ()


def test_r52_r10_promotes_clean_reviewed_p5_to_candidate_but_not_final_or_release() -> None:
    gate = _r10(_complete_bodyfree_evidence())

    assert r52.assert_p7_r52_p5_confirmed_candidate_decision_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_R10_REQUIRED_FIELD_REFS)
    assert gate["p5_confirmed_candidate_decision_status"] == "R52_P5_CONFIRMED_CANDIDATE_DECISION_PASSED"
    assert gate["decision_ref"] == "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["p5_decision_status"] == "R52_P5_CONFIRMED_CANDIDATE_REVIEWED_NOT_FINAL"
    assert gate["p5_human_blind_qa_confirmed_candidate"] is True
    assert gate["r52_10_p5_confirmed_candidate_decision_built"] is True
    assert gate["r52_10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation"] is True
    assert gate["next_required_step"] == r52.P7_R52_R10_NEXT_REQUIRED_STEP_REF
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False
    _assert_never_auto_allows(gate)


@pytest.mark.parametrize(
    "overrides, expected_ref",
    [
        ({"red_count": 1}, "R52_RETURN_TO_P5_REPAIR_REQUIRED"),
        ({"repair_required_count": 1}, "R52_RETURN_TO_P5_REPAIR_REQUIRED"),
        ({"rating_question_consistency_status": "failed"}, "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"),
        ({"open_execution_blocker_count": 1}, "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN"),
        ({"disposal_verified": False}, "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED"),
    ],
)
def test_r52_r10_preserves_prior_no_go_or_blocked_decisions_without_p5_candidate(
    overrides: dict[str, object], expected_ref: str
) -> None:
    gate = _r10(_complete_bodyfree_evidence(**overrides))

    assert gate["decision_ref"] == expected_ref
    assert gate["p5_human_blind_qa_confirmed_candidate"] is False
    assert gate["r52_10_p5_confirmed_candidate_decision_built"] is False
    assert gate["r52_10_ready_for_r52_11_p6_limited_human_readfeel_candidate_separation"] is False
    _assert_never_auto_allows(gate)


def test_r52_r10_returns_to_r51_when_actual_review_evidence_is_missing() -> None:
    gate = _r10(None)

    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["p5_decision_status"] == "R52_P5_NOT_REVIEWED_EVIDENCE_MISSING"
    assert gate["p5_human_blind_qa_confirmed_candidate"] is False
    assert gate["r52_10_p5_confirmed_candidate_decision_built"] is False
    _assert_never_auto_allows(gate)


def test_r52_r11_separates_p6_candidate_from_p6_start_permission() -> None:
    gate = _r11(_complete_bodyfree_evidence())

    assert r52.assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_R11_REQUIRED_FIELD_REFS)
    assert gate["decision_ref"] == "R52_P6_LIMITED_READFEEL_START_CANDIDATE_ONLY"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["p6_limited_human_readfeel_candidate_separation_status"] == "R52_P6_LIMITED_READFEEL_CANDIDATE_SEPARATION_PASSED_WITH_CANDIDATE"
    assert gate["p5_human_blind_qa_confirmed_candidate"] is True
    assert gate["p6_limited_human_readfeel_candidate_supported"] is True
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert gate["p6_limited_human_readfeel_start_allowed"] is False
    assert gate["r52_11_p6_limited_human_readfeel_candidate_separation_built"] is True
    assert gate["r52_11_ready_for_r52_12_p8_question_material_candidate_separation"] is True
    assert gate["next_required_step"] == r52.P7_R52_R11_NEXT_REQUIRED_STEP_REF
    _assert_never_auto_allows(gate)


@pytest.mark.parametrize(
    "overrides, expected_reason",
    [
        ({"critical_repair_blocker_count": 1}, "p6_candidate_blocked_by_critical_repair_blocker"),
        ({"creepy_or_surveillance_blocker_count": 1}, "p6_candidate_blocked_by_creepy_or_surveillance_blocker"),
        ({"overclaim_blocker_count": 1}, "p6_candidate_blocked_by_overclaim_blocker"),
        ({"self_blame_amplification_blocker_count": 1}, "p6_candidate_blocked_by_self_blame_amplification_blocker"),
        ({"p6_limited_family_scope_supported": False}, "p6_limited_family_scope_not_supported"),
        ({"p5_weakness_not_hidden_by_p6_candidate": False}, "p5_weakness_would_be_hidden_by_p6_candidate"),
    ],
)
def test_r52_r11_refuses_p6_candidate_when_limited_readfeel_would_hide_p5_or_safety_blocker(
    overrides: dict[str, object], expected_reason: str
) -> None:
    gate = _r11(_complete_bodyfree_evidence(**overrides))

    assert gate["decision_ref"] in {"R52_NO_GO_P6_P8_START", "R52_RETURN_TO_P5_REPAIR_REQUIRED"}
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert gate["p6_limited_human_readfeel_start_allowed"] is False
    assert expected_reason in gate["p6_limited_human_readfeel_candidate_reason_refs"] or expected_reason in gate["decision_reason_refs"]
    _assert_never_auto_allows(gate)


def test_r52_r11_refuses_p6_candidate_when_r51_handoff_candidate_is_not_reported() -> None:
    gate = _r11(_complete_bodyfree_evidence(), include_p6_candidate=False)

    assert gate["decision_ref"] == "R52_NO_GO_P6_P8_START"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["p6_limited_human_readfeel_candidate_supported"] is False
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert "r51_p6_limited_human_readfeel_candidate_handoff_not_reported" in gate["p6_limited_human_readfeel_candidate_reason_refs"]
    assert gate["next_required_step"] == r52.P7_R52_R11_NEXT_REQUIRED_STEP_REF
    _assert_never_auto_allows(gate)


def test_r52_r11_preserves_r51_evidence_missing_without_p6_candidate() -> None:
    gate = _r11(None)

    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert gate["r52_11_p6_limited_human_readfeel_candidate_separation_built"] is False
    _assert_never_auto_allows(gate)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "p6_limited_human_readfeel_start_allowed_promoted_here",
        "p6_limited_human_readfeel_runtime_started_here",
        "p6_limited_human_readfeel_review_run_here",
        "p6_limited_human_readfeel_notes_materialized_here",
    ],
)
def test_r52_r11_contract_rejects_p6_start_release_or_runtime_mutation_flags(forbidden_key: str) -> None:
    clean_gate = _r11(_complete_bodyfree_evidence())
    tampered = dict(clean_gate)
    tampered[forbidden_key] = True

    with pytest.raises(ValueError):
        r52.assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(tampered)


@pytest.mark.parametrize("forbidden_key", ["raw_input", "comment_text_body", "reviewer_free_text", "question_text", "local_absolute_path", "packet_content_hash", "terminal_output"])
def test_r52_r10_r11_contracts_reject_forbidden_body_or_local_payload_keys(forbidden_key: str) -> None:
    clean_r10 = _r10(_complete_bodyfree_evidence())
    clean_r11 = _r11(_complete_bodyfree_evidence())

    tampered_r10 = dict(clean_r10)
    tampered_r11 = dict(clean_r11)
    tampered_r10[forbidden_key] = "forbidden"
    tampered_r11[forbidden_key] = "forbidden"

    with pytest.raises(ValueError):
        r52.assert_p7_r52_p5_confirmed_candidate_decision_contract(tampered_r10)
    with pytest.raises(ValueError):
        r52.assert_p7_r52_p6_limited_human_readfeel_candidate_separation_contract(tampered_r11)


def test_r52_r10_r11_chain_blocks_forbidden_payload_without_copying_body() -> None:
    gate = _r11(_complete_bodyfree_evidence(raw_input="this raw body must not appear in R52 output"))

    assert gate["decision_ref"] == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert "this raw body must not appear" not in repr(gate)
    _assert_never_auto_allows(gate)
