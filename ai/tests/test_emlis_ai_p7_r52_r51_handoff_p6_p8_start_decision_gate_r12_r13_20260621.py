# -*- coding: utf-8 -*-
"""R52-12/R52-13 tests for P8 material candidate and final decision composition."""

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


def _clean_r51_handoff_materials(*, include_p6_candidate: bool = True, include_p8_candidate: bool = True) -> list[dict[str, object]]:
    r18_extra: dict[str, object] = {}
    r19_extra: dict[str, object] = {}
    if include_p6_candidate:
        r18_extra["p6_limited_human_readfeel_start_allowed_candidate"] = True
    if include_p8_candidate:
        r19_extra["p8_question_design_material_candidate"] = True
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
            **r19_extra,
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
        "red_or_repair_required_treated_as_question_candidate": False,
        "repair_required_not_question_mixed_into_p8_candidate": False,
        "p5_repair_return_material_mixed_into_p8_candidate": False,
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
        "question_need_primary_class_counts": {
            "clarify_target_or_event": 9,
            "clarify_time_or_scope": 7,
            "clarify_desired_support": 8,
        },
        "ambiguity_kind_counts": {
            "object_ambiguous": 11,
            "time_scope_ambiguous": 6,
        },
        "one_question_fit_counts": {
            "one_question_fit": 18,
            "needs_more_than_one_question": 6,
        },
        "plan_candidate_flag_counts": {
            "plus_one_question_candidate": 12,
            "premium_deepening_candidate": 6,
        },
        "body_free": True,
    }
    evidence.update(overrides)
    return evidence


def _r12(
    evidence: dict[str, object] | None = None,
    *,
    include_p6_candidate: bool = True,
    include_p8_candidate: bool = True,
) -> dict[str, object]:
    return r52.build_p7_r52_r0_r12_p8_question_material_candidate_separation_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(
            include_p6_candidate=include_p6_candidate,
            include_p8_candidate=include_p8_candidate,
        ),
        r51_actual_review_evidence=evidence,
    )


def _r13(
    evidence: dict[str, object] | None = None,
    *,
    include_p6_candidate: bool = True,
    include_p8_candidate: bool = True,
) -> dict[str, object]:
    return r52.build_p7_r52_r0_r13_final_decision_composer_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(
            include_p6_candidate=include_p6_candidate,
            include_p8_candidate=include_p8_candidate,
        ),
        r51_actual_review_evidence=evidence,
    )


def _assert_no_auto_allow(material: dict[str, object]) -> None:
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["p5_human_blind_qa_confirmed"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False


def test_r52_current_capability_constants_include_r0_to_r15_and_has_no_remaining_r52_steps() -> None:
    assert tuple(r52.P7_R52_CURRENT_IMPLEMENTED_STEPS) == r52.P7_R52_R15_IMPLEMENTED_STEPS
    assert r52.P7_R52_R12_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R13_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R14_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R15_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert tuple(r52.P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS) == r52.P7_R52_R15_NOT_YET_IMPLEMENTED_STEPS
    assert r52.P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS == ()


def test_r52_r12_separates_p8_question_material_candidate_from_p8_start_permission() -> None:
    gate = _r12(_complete_bodyfree_evidence())

    assert r52.assert_p7_r52_p8_question_material_candidate_separation_contract(gate) is True
    assert set(gate) == set(r52.P7_R52_R12_REQUIRED_FIELD_REFS)
    assert gate["decision_ref"] == "R52_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY"
    assert gate["decision_status"] == "CANDIDATE_ONLY"
    assert gate["p8_question_material_candidate_separation_status"] == "R52_P8_QUESTION_MATERIAL_CANDIDATE_SEPARATION_PASSED_WITH_CANDIDATE"
    assert gate["p8_question_design_material_candidate"] is True
    assert gate["p8_question_design_material_candidate_supported"] is True
    assert gate["p8_start_allowed"] is False
    assert gate["question_observation_row_count"] == r52.P7_R51_REQUIRED_CASE_COUNT
    assert gate["question_need_primary_class_counts"]
    assert gate["question_need_primary_class_counts_body_free"] is True
    assert gate["question_need_primary_class_counts_present"] is True
    assert gate["next_required_step"] == r52.P7_R52_R12_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(gate)


def test_r52_r12_can_find_p8_material_even_when_p6_candidate_is_absent() -> None:
    gate = _r12(_complete_bodyfree_evidence(), include_p6_candidate=False)

    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert gate["p8_question_design_material_candidate"] is True
    assert gate["decision_ref"] == "R52_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY"
    assert gate["p8_start_allowed"] is False
    _assert_no_auto_allow(gate)


@pytest.mark.parametrize(
    "overrides, expected_reason",
    [
        ({"question_observation_row_count": 23}, "r51_question_observation_rows_missing_or_below_required_case_count"),
        ({"question_need_primary_class_counts": {}}, "question_need_primary_class_counts_missing"),
        ({"repair_required_not_question_count": 1}, "repair_required_not_question_mixed_or_present_for_p8_candidate"),
        ({"red_or_repair_required_question_candidate_count": 1}, "red_or_repair_required_treated_as_question_candidate"),
        ({"p5_repair_target_mixed_into_p8_candidate": True}, "p5_repair_target_mixed_into_p8_candidate"),
        ({"p5_weakness_not_hidden_by_question_candidate": False}, "p5_weakness_would_be_hidden_by_p8_question_candidate"),
    ],
)
def test_r52_r12_refuses_p8_candidate_when_material_would_hide_repair_or_needs_bodyfree_counts(
    overrides: dict[str, object], expected_reason: str
) -> None:
    gate = _r12(_complete_bodyfree_evidence(**overrides))

    assert gate["p8_question_design_material_candidate"] is False
    assert gate["p8_start_allowed"] is False
    assert expected_reason in gate["p8_question_design_material_candidate_reason_refs"]
    _assert_no_auto_allow(gate)


def test_r52_r12_refuses_p8_candidate_when_r51_handoff_candidate_is_not_reported() -> None:
    gate = _r12(_complete_bodyfree_evidence(), include_p8_candidate=False)

    assert gate["p8_question_design_material_candidate"] is False
    assert gate["p8_start_allowed"] is False
    assert "r51_p8_question_design_material_candidate_handoff_not_reported" in gate["p8_question_design_material_candidate_reason_refs"]
    _assert_no_auto_allow(gate)


def test_r52_r12_preserves_r51_evidence_missing_without_question_candidate() -> None:
    gate = _r12(None)

    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["p8_question_design_material_candidate"] is False
    assert gate["r52_12_p8_question_material_candidate_separation_built"] is False
    _assert_no_auto_allow(gate)


def test_r52_r13_composes_final_candidate_summary_without_any_auto_allow() -> None:
    final = _r13(_complete_bodyfree_evidence())

    assert r52.assert_p7_r52_final_decision_composer_contract(final) is True
    assert set(final) == set(r52.P7_R52_R13_REQUIRED_FIELD_REFS)
    assert final["decision_ref"] == "R52_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY"
    assert final["decision_status"] == "CANDIDATE_ONLY"
    assert final["final_decision_composer_status"] == "R52_FINAL_DECISION_COMPOSED_CANDIDATE_ONLY_WITH_P8_MATERIAL"
    assert final["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert final["p6_limited_human_readfeel_start_allowed"] is False
    assert final["p8_question_design_material_candidate"] is True
    assert final["p8_start_allowed"] is False
    assert "p6_candidate_is_not_p6_start_allowed" in final["no_auto_allow_summary_refs"]
    assert "p8_material_candidate_is_not_p8_start_allowed" in final["no_auto_allow_summary_refs"]
    assert final["next_required_step"] == r52.P7_R52_R13_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(final)


def test_r52_r13_preserves_return_to_r51_when_actual_review_evidence_is_missing() -> None:
    final = _r13(None)

    assert final["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert final["decision_status"] == "RETURN_REQUIRED"
    assert final["final_decision_composer_status"] == "R52_FINAL_DECISION_COMPOSED_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert final["r51_actual_review_evidence_complete"] is False
    assert final["p8_question_design_material_candidate"] is False
    assert final["r52_13_final_decision_composer_built"] is True
    _assert_no_auto_allow(final)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "question_text",
        "draft_question_text",
        "raw_input",
        "comment_text_body",
        "reviewer_free_text",
        "local_absolute_path",
        "packet_content_hash",
        "terminal_output",
    ],
)
def test_r52_r12_r13_contracts_reject_body_question_path_hash_and_terminal_keys(forbidden_key: str) -> None:
    clean_r12 = _r12(_complete_bodyfree_evidence())
    clean_r13 = _r13(_complete_bodyfree_evidence())
    tampered_r12 = dict(clean_r12)
    tampered_r13 = dict(clean_r13)
    tampered_r12[forbidden_key] = "forbidden"
    tampered_r13[forbidden_key] = "forbidden"

    with pytest.raises(ValueError):
        r52.assert_p7_r52_p8_question_material_candidate_separation_contract(tampered_r12)
    with pytest.raises(ValueError):
        r52.assert_p7_r52_final_decision_composer_contract(tampered_r13)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "p8_question_detail_design_started_here",
        "question_trigger_logic_implemented_here",
        "p8_api_db_rn_response_key_design_finalized_here",
        "final_decision_claimed_as_p8_start_allowed_here",
    ],
)
def test_r52_r12_r13_contracts_reject_p8_start_release_question_design_or_runtime_mutation_flags(forbidden_key: str) -> None:
    clean_r12 = _r12(_complete_bodyfree_evidence())
    clean_r13 = _r13(_complete_bodyfree_evidence())
    if forbidden_key in clean_r12:
        tampered_r12 = dict(clean_r12)
        tampered_r12[forbidden_key] = True
        with pytest.raises(ValueError):
            r52.assert_p7_r52_p8_question_material_candidate_separation_contract(tampered_r12)
    if forbidden_key in clean_r13:
        tampered_r13 = dict(clean_r13)
        tampered_r13[forbidden_key] = True
        with pytest.raises(ValueError):
            r52.assert_p7_r52_final_decision_composer_contract(tampered_r13)
