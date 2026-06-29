# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
import test_r54_ev18_ev19_20260626 as prev19


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text": "',
    '"draft_question_text": "',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_storage_schema_implemented": true',
    '"question_answer_persistence_implemented": true',
    '"question_plan_guard_implemented": true',
    '"question_text_materialized_here": true',
    '"draft_question_text_materialized_here": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"existing_op22_reused_as_actual_final_validation_basis": true',
    '"existing_op23_reused_as_actual_r52_handoff_basis": true',
)


def _assert_ev20_ev21_body_free_no_promotion(
    material: dict[str, object],
    *,
    allow_actual_review_evidence_complete: bool = False,
    allow_p5_candidate: bool = True,
    allow_p6_candidate: bool = True,
    allow_p8_material_candidate: bool = False,
) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped
    if not allow_actual_review_evidence_complete:
        assert '"actual_review_evidence_complete": true' not in dumped
    if not allow_p5_candidate:
        assert '"p5_human_blind_qa_confirmed_candidate": true' not in dumped
    if not allow_p6_candidate:
        assert '"p6_limited_human_readfeel_candidate": true' not in dumped
    if not allow_p8_material_candidate:
        assert '"p8_question_design_material_candidate": true' not in dumped


def _ev19_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    _, _, material = prev19._ev19_ready(rows)
    return material


def _ev20_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    ev19 = _ev19_ready(rows)
    material = ev.build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=ev19
    )
    assert ev.assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    return material


def _ev21_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    ev20 = _ev20_ready(rows)
    material = ev.build_p7_r54_ev21_r52_reintake_handoff(final_validation=ev20)
    assert ev.assert_p7_r54_ev21_r52_reintake_handoff_contract(material) is True
    return material


def test_r54_ev20_final_validation_ready_without_body_question_text_or_no_touch_mutation() -> None:
    ev19 = _ev19_ready()
    material = ev.build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=ev19
    )

    assert material["schema_version"] == ev.P7_R54_EV20_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV20_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV20_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV20_STEP_REF
    assert material["final_validation_status"] == ev.P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF
    assert material["final_validation_ref"] == ev.P7_R54_EV20_FINAL_VALIDATION_REF
    assert material["final_validation_decision_ref"] == ev.P7_R54_EV20_READY_DECISION_REF
    assert material["final_validation_reason_refs"] == [ev.P7_R54_EV20_READY_REASON_REF]
    assert material["final_validation_issue_refs"] == []
    assert material["final_validation_passed"] is True
    assert material["r52_reintake_handoff_allowed_next"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["body_leak_or_question_text_violation_detected"] is False
    assert material["no_touch_violation_detected"] is False
    assert material["open_execution_blocker_ids"] == []
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["question_need_observation_rows_aggregated_count"] == 24
    assert material["disposal_verified"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["existing_op22_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op22_current_refs_are_historical_here"] is True
    assert material["existing_op22_reused_as_actual_final_validation_basis"] is False
    assert material["existing_op22_structural_contract_reused"] is True
    assert material["next_required_step"] == ev.P7_R54_EV21_STEP_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV20_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV20_NOT_YET_IMPLEMENTED_STEPS
    _assert_ev20_ev21_body_free_no_promotion(material)


def test_r54_ev21_r52_reintake_handoff_ready_is_bodyfree_and_does_not_promote_p5_p6_p8_release() -> None:
    material = _ev21_ready()

    assert material["schema_version"] == ev.P7_R54_EV21_R52_REINTAKE_HANDOFF_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV21_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV21_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV21_STEP_REF
    assert material["handoff_status"] == ev.P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    assert material["r52_reintake_handoff_status"] == ev.P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    assert material["handoff_ref"] == ev.P7_R54_EV21_R52_REINTAKE_HANDOFF_REF
    assert material["r52_reintake_handoff_ref"] == ev.P7_R54_EV21_R52_REINTAKE_HANDOFF_REF
    assert material["handoff_reason_refs"] == [ev.P7_R54_EV21_READY_REASON_REF]
    assert material["r52_reintake_handoff_reason_refs"] == [ev.P7_R54_EV21_READY_REASON_REF]
    assert material["r52_reintake_decision_ref"] == ev.P7_R54_EV21_R52_REINTAKE_DECISION_REF
    assert material["r52_reintake_required_ref"] == ev.P7_R54_EV21_R52_REINTAKE_REQUIRED_REF
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_bodyfree_receipts"] is True
    assert material["r52_bodyfree_actual_review_evidence_complete"] is True
    assert material["r52_bodyfree_evidence_handoff_ready"] is True
    assert material["body_free_evidence_handoff_materialized_here"] is True
    assert material["r52_reintake_required"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_manual_review_run_here"] is False
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["rating_rows_bodyfree_handoff_count"] == 24
    assert material["question_observation_rows_bodyfree_handoff_count"] == 24
    assert material["disposal_verified"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["p5_decision_candidate"] == ev.P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_candidate_only"] is True
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["release_allowed"] is False
    assert material["p7_complete"] is False
    assert material["r52_handoff_preserves_candidate_only_boundaries"] is True
    assert material["r52_handoff_contains_body_full_packet"] is False
    assert material["r52_handoff_contains_question_text"] is False
    assert material["r52_handoff_contains_local_path"] is False
    assert material["r52_handoff_contains_payload_hash"] is False
    assert material["r52_handoff_contains_reviewer_free_text"] is False
    assert material["r52_handoff_contains_raw_payload"] is False
    assert material["handoff_evidence_ref_count"] == len(material["handoff_evidence_refs"])
    assert material["open_execution_blocker_ids"] == []
    assert material["existing_op23_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op23_current_refs_are_historical_here"] is True
    assert material["existing_op23_reused_as_actual_r52_handoff_basis"] is False
    assert material["existing_op23_structural_contract_reused"] is True
    assert material["next_required_step"] == ev.P7_R54_EV22_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV21_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV21_NOT_YET_IMPLEMENTED_STEPS
    _assert_ev20_ev21_body_free_no_promotion(material, allow_actual_review_evidence_complete=True)


def test_r54_ev20_carries_p8_material_candidate_without_starting_p8_or_materializing_question_text() -> None:
    rows = prev19._rows_with_p8_material_candidate()
    material = _ev20_ready(rows)

    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_material_candidate_row_count"] == 1
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    _assert_ev20_ev21_body_free_no_promotion(material, allow_p8_material_candidate=True)


def test_r54_ev21_carries_p8_material_candidate_only_handoff_without_starting_p8() -> None:
    rows = prev19._rows_with_p8_material_candidate()
    material = _ev21_ready(rows)

    assert material["p8_material_candidate_only"] is True
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_material_candidate_row_count"] == 1
    assert material["p8_design_material_candidate_only_not_start"] is True
    assert material["p8_start_allowed"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["question_api_implemented"] is False
    assert material["question_db_schema_implemented"] is False
    assert material["question_rn_ui_implemented"] is False
    assert material["question_response_key_implemented"] is False
    _assert_ev20_ev21_body_free_no_promotion(
        material,
        allow_actual_review_evidence_complete=True,
        allow_p8_material_candidate=True,
    )


@pytest.mark.parametrize(
    ("validation_evidence", "expected_status", "expected_next", "expected_issue"),
    [
        (
            {"body_full_packet_artifact_detected": True},
            ev.P7_R54_EV20_BODY_LEAK_BLOCKED_STATUS_REF,
            ev.P7_R54_EV20_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF,
            "body_full_packet_artifact_detected",
        ),
        (
            {"question_text_artifact_detected": True},
            ev.P7_R54_EV20_BODY_LEAK_BLOCKED_STATUS_REF,
            ev.P7_R54_EV20_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF,
            "question_text_artifact_detected",
        ),
        (
            {"api_changed_detected": True},
            ev.P7_R54_EV20_NO_TOUCH_BLOCKED_STATUS_REF,
            ev.P7_R54_EV20_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF,
            "api_changed_detected",
        ),
    ],
)
def test_r54_ev20_blocks_body_question_and_no_touch_violations(
    validation_evidence: dict[str, object],
    expected_status: str,
    expected_next: str,
    expected_issue: str,
) -> None:
    ev19 = _ev19_ready()
    material = ev.build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=ev19,
        validation_evidence=validation_evidence,
    )

    assert ev.assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    assert material["final_validation_status"] == expected_status
    assert material["final_validation_passed"] is False
    assert material["r52_reintake_handoff_allowed_next"] is False
    assert material["actual_review_evidence_complete"] is False
    assert expected_issue in material["final_validation_issue_refs"]
    assert expected_issue in material["open_execution_blocker_ids"]
    assert material["next_required_step"] == expected_next
    _assert_ev20_ev21_body_free_no_promotion(material, allow_actual_review_evidence_complete=False, allow_p5_candidate=False, allow_p6_candidate=False)


def test_r54_ev21_blocks_r52_handoff_when_ev20_body_leak_validation_is_blocked() -> None:
    ev19 = _ev19_ready()
    ev20 = ev.build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=ev19,
        validation_evidence={"question_text_artifact_detected": True},
    )
    material = ev.build_p7_r54_ev21_r52_reintake_handoff(final_validation=ev20)

    assert ev.assert_p7_r54_ev21_r52_reintake_handoff_contract(material) is True
    assert material["handoff_status"] == ev.P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF
    assert material["r52_reintake_handoff_ready"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_evidence_handoff_materialized_here"] is False
    assert material["r52_reintake_required"] is False
    assert material["handoff_evidence_refs"] == []
    assert material["next_required_step"] == ev.P7_R54_EV21_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert ev.P7_R54_EV21_BODY_LEAK_BLOCKED_REASON_REF in material["handoff_reason_refs"]
    assert material["open_execution_blocker_ids"]
    _assert_ev20_ev21_body_free_no_promotion(material, allow_p5_candidate=False, allow_p6_candidate=False)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("existing_op22_current_refs_are_historical_here", False),
        ("existing_op22_reused_as_actual_final_validation_basis", True),
        ("final_validation_passed", False),
        ("r52_reintake_handoff_allowed_next", False),
        ("actual_review_evidence_complete", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_implementation_started_here", True),
        ("p8_implementation_spec_finalized_here", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
        ("raw_body_included", True),
    ],
)
def test_r54_ev20_contract_rejects_promotion_and_boundary_mutations(key: str, value: object) -> None:
    material = _ev20_ready()
    mutated = deepcopy(material)
    mutated[key] = value

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract(mutated)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("existing_op23_current_refs_are_historical_here", False),
        ("existing_op23_reused_as_actual_r52_handoff_basis", True),
        ("actual_review_evidence_complete", False),
        ("r52_reintake_handoff_ready", False),
        ("body_free_evidence_handoff_materialized_here", False),
        ("r52_reintake_required", False),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("p7_complete", True),
        ("question_implementation_started_here", True),
        ("p8_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented", True),
        ("question_api_implemented", True),
        ("question_db_schema_implemented", True),
        ("question_rn_ui_implemented", True),
        ("question_response_key_implemented", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
        ("raw_body_included", True),
        ("r52_handoff_contains_body_full_packet", True),
        ("r52_handoff_contains_question_text", True),
        ("r52_handoff_contains_local_path", True),
        ("r52_handoff_contains_payload_hash", True),
        ("r52_handoff_contains_reviewer_free_text", True),
        ("r52_handoff_contains_raw_payload", True),
    ],
)
def test_r54_ev21_contract_rejects_promotion_question_implementation_and_leak_mutations(
    key: str,
    value: object,
) -> None:
    material = _ev21_ready()
    mutated = deepcopy(material)
    mutated[key] = value

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev21_r52_reintake_handoff_contract(mutated)


def test_r54_ev20_rejects_inline_body_payload_or_unexpected_question_text_key() -> None:
    material = _ev20_ready()
    mutated = deepcopy(material)
    mutated["comment_text"] = "body must never be placed in body-free evidence"

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract(mutated)


def test_r54_ev21_rejects_inline_body_payload_or_unexpected_question_text_key() -> None:
    material = _ev21_ready()
    mutated = deepcopy(material)
    mutated["question_text"] = "What should Cocolon ask next?"

    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev21_r52_reintake_handoff_contract(mutated)
