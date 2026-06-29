# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


FORBIDDEN_BODY_KEY_TOKENS = (
    '"raw_input":',
    '"comment_text":',
    '"returned_surface":',
    '"history_body":',
    '"reviewer_free_text":',
    '"question_text":',
    '"draft_question_text":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output":',
    '"command_full_output":',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"actual_review_evidence_complete": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"p5_repair_return_candidate": true',
    '"p6_limited_human_readfeel_candidate": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_question_design_material_candidate": true',
    '"p8_start_allowed": true',
    '"p7_complete": true',
    '"release_allowed": true',
    '"r52_existing_decision_enum_changed_here": true',
    '"r52_decision_written_here": true',
    '"r52_reintake_ready_claimed": true',
    '"p5_not_reviewed_reclassified_as_p8_question_material": true',
    '"p5_repair_required_escaped_to_p8_question_material": true',
    '"p5_candidate_auto_release_allowed": true',
    '"actual_review_complete_candidate_only_auto_release_allowed": true',
)


def _assert_no_body_or_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for token in FORBIDDEN_BODY_KEY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_TRUE_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_r5() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_actual_review_evidence_gap_assessment_bodyfree()
    assert r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material) is True
    return (material,)


def _r5() -> dict[str, object]:
    return deepcopy(_cached_r5()[0])


@lru_cache(maxsize=1)
def _cached_r6() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_r52_reintake_decision_materialization_bodyfree(
        actual_review_evidence_gap_assessment=_r5(),
    )
    assert r55.assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(material) is True
    return (material,)


def _r6() -> dict[str, object]:
    return deepcopy(_cached_r6()[0])


@lru_cache(maxsize=1)
def _cached_r7() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_p5_p6_p8_release_separation_bodyfree(
        r52_reintake_decision_materialization=_r6(),
    )
    assert r55.assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(material) is True
    return (material,)


def _r7() -> dict[str, object]:
    return deepcopy(_cached_r7()[0])


def test_r55_r6_materializes_default_r52_reintake_decision_without_r52_enum_or_release_promotion() -> None:
    material = _r6()

    assert material["schema_version"] == r55.P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["policy_section"] == "R55-6_r52_reintake_decision_materialization"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"

    assert material["r5_actual_review_evidence_gap_assessment_schema_version"] == r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION
    assert material["actual_review_evidence_gap_status_ref"] == "ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert material["r54_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert material["r54_review_operation_state_ref"] == "not_started"
    assert material["required_case_count"] == 24
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["missing_evidence_refs"]) == r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS
    assert material["missing_evidence_ref_count"] == len(r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS)

    assert material["r55_decision_ref"] == "R55_R52_RETURN_TO_R54_ACTUAL_REVIEW_REQUIRED"
    assert material["r52_existing_decision_equivalent"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert material["r52_equivalent_reason_ref"] == "actual_review_evidence_missing_before_p6_p8_start_decision"
    assert material["decision_status"] == "NO_GO"
    assert tuple(material["decision_reason_refs"]) == r55.P7_R55_DEFAULT_DECISION_REASON_REFS
    assert material["decision_reason_ref_count"] == len(r55.P7_R55_DEFAULT_DECISION_REASON_REFS)
    assert material["next_required_step"] == "R54_actual_local_only_human_review_operation_required_before_R52_reintake"
    assert material["r55_next_implementation_step_ref"] == "R55-7_p5_p6_p8_release_separation"

    assert material["p5_decision_status_ref"] == "R55_P5_NOT_REVIEWED_EVIDENCE_MISSING"
    assert material["p5_decision_candidate_ref"] == "P5_NOT_REVIEWED"
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False

    assert material["r52_existing_decision_enum_changed_here"] is False
    assert material["r52_existing_decision_enum_extended_here"] is False
    assert material["r52_decision_written_here"] is False
    assert material["r52_reintake_ready_claimed"] is False
    assert material["p5_not_reviewed_reclassified_as_p5_repair_required"] is False
    assert material["p5_not_reviewed_reclassified_as_p5_confirmed_candidate"] is False
    assert material["p5_not_reviewed_reclassified_as_p8_question_material"] is False
    assert material["p5_repair_required_escaped_to_p8_question_material"] is False
    assert material["decision_material_claimed_as_actual_review_completion"] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is True
    assert material["r55_4_bodyfree_forbidden_payload_scan_done"] is True
    assert material["r55_5_actual_review_evidence_gap_assessed"] is True
    assert material["r55_6_r52_reintake_decision_materialized"] is True
    assert material["r55_7_p5_p6_p8_release_separated"] is False
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R6_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R6_NOT_YET_IMPLEMENTED_STEPS

    _assert_no_body_or_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r55_decision_ref", "R55_R52_P5_CONFIRMED_CANDIDATE_ONLY"),
        ("r52_existing_decision_equivalent", "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE"),
        ("r52_equivalent_reason_ref", "different_reason"),
        ("decision_status", "CANDIDATE_ONLY"),
        ("decision_reason_refs", ["p8_start_allowed_without_review"]),
        ("decision_reason_ref_count", 1),
        ("next_required_step", "P8_question_design_start"),
        ("r55_next_implementation_step_ref", "R55-8_final_no_touch_boundary_validation"),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("p5_decision_status_ref", "R55_P5_REPAIR_REQUIRED"),
        ("p5_decision_candidate_ref", "P5_CONFIRMED_CANDIDATE"),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("r52_existing_decision_enum_changed_here", True),
        ("r52_existing_decision_enum_extended_here", True),
        ("r52_decision_written_here", True),
        ("r52_reintake_ready_claimed", True),
        ("p5_not_reviewed_reclassified_as_p5_repair_required", True),
        ("p5_not_reviewed_reclassified_as_p5_confirmed_candidate", True),
        ("p5_not_reviewed_reclassified_as_p8_question_material", True),
        ("decision_material_claimed_as_actual_review_completion", True),
        ("r55_7_p5_p6_p8_release_separated", True),
    ],
)
def test_r55_r6_rejects_decision_rewrite_enum_mutation_or_p6_p8_release_promotion(key: str, value: object) -> None:
    material = _r6()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("actual_review_evidence_gap_status_ref", "ACTUAL_REVIEW_EVIDENCE_COMPLETE"),
        ("r54_handoff_status", "R54_R52_REINTAKE_HANDOFF_READY"),
        ("r54_review_operation_state_ref", "completed"),
        ("required_case_count", 23),
        ("missing_evidence_refs", ["question_need_observation_actual_rows_missing"]),
        ("missing_evidence_ref_count", 1),
        ("r55_6_r52_reintake_decision_materialized", False),
    ],
)
def test_r55_r6_rejects_gap_reclassification_or_missing_evidence_rewrite(key: str, value: object) -> None:
    material = _r6()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(material)


def test_r55_r6_builder_rejects_non_default_gap_before_decision_materialization() -> None:
    r5 = _r5()
    r5["gap_status_ref"] = "ACTUAL_REVIEW_EVIDENCE_COMPLETE"
    with pytest.raises(ValueError):
        r55.build_p7_r55_r52_reintake_decision_materialization_bodyfree(
            actual_review_evidence_gap_assessment=r5,
        )


def test_r55_r7_separates_p5_candidate_final_p6_p8_and_release_without_promotion() -> None:
    material = _r7()

    assert material["schema_version"] == r55.P7_R55_P5_P6_P8_RELEASE_SEPARATION_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_P5_P6_P8_RELEASE_SEPARATION_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["policy_section"] == "R55-7_p5_p6_p8_release_separation"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"

    assert material["r6_r52_reintake_decision_schema_version"] == r55.P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION
    assert material["r55_decision_ref"] == "R55_R52_RETURN_TO_R54_ACTUAL_REVIEW_REQUIRED"
    assert material["r52_existing_decision_equivalent"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert material["decision_status"] == "NO_GO"
    assert tuple(material["decision_reason_refs"]) == r55.P7_R55_DEFAULT_DECISION_REASON_REFS
    assert material["decision_next_required_step"] == "R54_actual_local_only_human_review_operation_required_before_R52_reintake"
    assert material["separation_status_ref"] == "P5_P6_P8_RELEASE_HELD_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert material["candidate_only_policy_ref"] == r55.P7_R55_CANDIDATE_ONLY_POLICY_REF
    assert material["p8_material_escape_blocked_ref"] == r55.P7_R55_P8_MATERIAL_ESCAPE_BLOCKED_REF

    assert material["actual_review_evidence_complete"] is False
    assert material["p5_decision_status_ref"] == "R55_P5_NOT_REVIEWED_EVIDENCE_MISSING"
    assert material["p5_decision_candidate_ref"] == "P5_NOT_REVIEWED"
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p5_repair_return_candidate"] is False
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False

    assert material["p5_candidate_auto_finalization_allowed"] is False
    assert material["p5_candidate_auto_p6_start_allowed"] is False
    assert material["p5_candidate_auto_p8_start_allowed"] is False
    assert material["p5_candidate_auto_release_allowed"] is False
    assert material["actual_review_complete_candidate_only_auto_finalization_allowed"] is False
    assert material["actual_review_complete_candidate_only_auto_p6_p8_start_allowed"] is False
    assert material["actual_review_complete_candidate_only_auto_release_allowed"] is False
    assert material["p5_repair_required_escaped_to_p8_question_material"] is False
    assert material["p5_not_reviewed_escaped_to_p8_question_material"] is False
    assert material["p8_question_design_material_allowed_from_missing_evidence"] is False
    assert material["p8_question_design_material_allowed_from_p5_repair_required"] is False
    assert material["p6_start_allowed_from_target_green_only"] is False
    assert material["release_allowed_from_target_green_only"] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is True
    assert material["r55_4_bodyfree_forbidden_payload_scan_done"] is True
    assert material["r55_5_actual_review_evidence_gap_assessed"] is True
    assert material["r55_6_r52_reintake_decision_materialized"] is True
    assert material["r55_7_p5_p6_p8_release_separated"] is True
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R7_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R7_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == "R54_actual_local_only_human_review_operation_required_before_R52_reintake"
    assert material["r55_next_implementation_step_ref"] == "R55-8_final_no_touch_boundary_validation"

    _assert_no_body_or_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("actual_review_evidence_complete", True),
        ("p5_decision_status_ref", "R55_P5_CONFIRMED_CANDIDATE_ONLY"),
        ("p5_decision_candidate_ref", "P5_CONFIRMED_CANDIDATE"),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p5_repair_return_candidate", True),
        ("p6_limited_human_readfeel_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_question_design_material_candidate", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("p5_candidate_auto_finalization_allowed", True),
        ("p5_candidate_auto_p6_start_allowed", True),
        ("p5_candidate_auto_p8_start_allowed", True),
        ("p5_candidate_auto_release_allowed", True),
        ("actual_review_complete_candidate_only_auto_finalization_allowed", True),
        ("actual_review_complete_candidate_only_auto_p6_p8_start_allowed", True),
        ("actual_review_complete_candidate_only_auto_release_allowed", True),
        ("p5_repair_required_escaped_to_p8_question_material", True),
        ("p5_not_reviewed_escaped_to_p8_question_material", True),
        ("p8_question_design_material_allowed_from_missing_evidence", True),
        ("p8_question_design_material_allowed_from_p5_repair_required", True),
        ("p6_start_allowed_from_target_green_only", True),
        ("release_allowed_from_target_green_only", True),
    ],
)
def test_r55_r7_rejects_p5_final_p6_p8_material_or_release_promotion(key: str, value: object) -> None:
    material = _r7()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r55_decision_ref", "R55_R52_P5_CONFIRMED_CANDIDATE_ONLY"),
        ("r52_existing_decision_equivalent", "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE"),
        ("decision_status", "CANDIDATE_ONLY"),
        ("decision_reason_refs", ["candidate_only"]),
        ("decision_next_required_step", "P6_limited_human_readfeel_start"),
        ("separation_status_ref", "P5_FINAL_READY"),
        ("candidate_only_policy_ref", "candidate_only_can_release"),
        ("p8_material_escape_blocked_ref", "p8_material_allowed"),
        ("next_required_step", "P8_question_design_start"),
        ("r55_next_implementation_step_ref", "R55-9_validation_command_matrix_documentation_output"),
        ("r55_7_p5_p6_p8_release_separated", False),
    ],
)
def test_r55_r7_rejects_decision_or_separation_policy_rewrite(key: str, value: object) -> None:
    material = _r7()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(material)


def test_r55_r7_builder_rejects_non_default_r6_decision_material_before_separation() -> None:
    r6 = _r6()
    r6["decision_status"] = "CANDIDATE_ONLY"
    with pytest.raises(ValueError):
        r55.build_p7_r55_p5_p6_p8_release_separation_bodyfree(
            r52_reintake_decision_materialization=r6,
        )


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "raw_input",
        "comment_text",
        "returned_emlis_surface",
        "history_body",
        "reviewer_free_text",
        "question_text",
        "draft_question_text",
        "local_absolute_path",
        "body_content_hash",
        "packet_content_hash",
        "terminal_output",
        "command_full_output",
    ],
)
def test_r55_r6_r7_reject_body_or_question_payload_keys(forbidden_key: str) -> None:
    r6 = _r6()
    r6[forbidden_key] = "must not be stored"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(r6)

    r7 = _r7()
    r7[forbidden_key] = "must not be stored"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(r7)
