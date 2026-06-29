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
)
FORBIDDEN_TRUE_TOKENS = (
    '"actual_review_evidence_complete": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"p5_repair_return_candidate": true',
    '"p8_question_design_material_candidate": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_start_allowed": true',
    '"p7_complete": true',
    '"release_allowed": true',
    '"forbidden_payload_detected": true',
    '"question_text_detected": true',
    '"blocked_by_body_free_boundary_risk": true',
)


def _assert_no_body_or_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for token in FORBIDDEN_BODY_KEY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_TRUE_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_r3() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_r54_handoff_intake_bodyfree()
    assert r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material) is True
    return (material,)


def _r3() -> dict[str, object]:
    return deepcopy(_cached_r3()[0])


@lru_cache(maxsize=1)
def _cached_r4() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_bodyfree_forbidden_payload_scan_bodyfree(r54_handoff_intake=_r3())
    assert r55.assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(material) is True
    return (material,)


def _r4() -> dict[str, object]:
    return deepcopy(_cached_r4()[0])


@lru_cache(maxsize=1)
def _cached_r5() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_actual_review_evidence_gap_assessment_bodyfree(
        r54_handoff_intake=_r3(),
        bodyfree_forbidden_payload_scan=_r4(),
    )
    assert r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material) is True
    return (material,)


def _r5() -> dict[str, object]:
    return deepcopy(_cached_r5()[0])


def test_r55_r4_scans_bodyfree_material_chain_without_storing_forbidden_payloads() -> None:
    material = _r4()

    assert material["schema_version"] == r55.P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["policy_section"] == "R55-4_bodyfree_forbidden_payload_scan"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"

    assert material["r3_r54_handoff_intake_schema_version"] == r55.P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION
    assert material["scan_scope_ref"] == "r55_intake_intermediate_material_bodyfree_forbidden_payload_scan"
    assert material["scan_target_material_count"] == 4
    assert material["scan_target_policy_sections"] == [
        "R55-0_scope_current_received_snapshot_refreeze",
        "R55-1_prior_helper_source_reconcile",
        "R55-2_validation_evidence_reconcile",
        "R55-3_r54_default_handoff_intake",
    ]
    assert material["forbidden_payload_key_refs"] == []
    assert material["forbidden_payload_true_flag_refs"] == []
    assert material["forbidden_payload_key_ref_count"] == 0
    assert material["forbidden_payload_true_flag_ref_count"] == 0
    assert material["scan_result_ref"] == "R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_CLEAR"
    assert material["bodyfree_boundary_risk_ref"] == "NO_BODYFREE_BOUNDARY_RISK_DETECTED"
    assert material["blocked_by_body_free_boundary_risk"] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is True
    assert material["r55_4_bodyfree_forbidden_payload_scan_done"] is True
    assert material["r55_5_actual_review_evidence_gap_assessed"] is False
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R4_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R4_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == r55.P7_R55_R4_NEXT_REQUIRED_STEP_REF

    _assert_no_body_or_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("forbidden_payload_detected", True),
        ("body_full_payload_detected", True),
        ("raw_input_detected", True),
        ("returned_surface_detected", True),
        ("comment_text_detected", True),
        ("history_body_detected", True),
        ("reviewer_free_text_detected", True),
        ("question_text_detected", True),
        ("draft_question_text_detected", True),
        ("local_absolute_path_detected", True),
        ("body_content_hash_detected", True),
        ("packet_content_hash_detected", True),
        ("terminal_output_detected", True),
        ("blocked_by_body_free_boundary_risk", True),
        ("r55_5_actual_review_evidence_gap_assessed", True),
        ("actual_review_evidence_complete", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r55_r4_rejects_detection_or_promotion_claims(key: str, value: object) -> None:
    material = _r4()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("forbidden_payload_key_refs", ["raw_input"]),
        ("forbidden_payload_true_flag_refs", ["release_allowed"]),
        ("forbidden_payload_key_ref_count", 1),
        ("forbidden_payload_true_flag_ref_count", 1),
    ],
)
def test_r55_r4_rejects_nonzero_forbidden_payload_scan_findings(key: str, value: object) -> None:
    material = _r4()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(material)


def test_r55_r4_rejects_missing_reordered_or_incomplete_scan_target_refs() -> None:
    material = _r4()
    material["scan_target_material_refs"] = []
    material["scan_target_material_count"] = 0
    with pytest.raises(ValueError):
        r55.assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(material)

    material = _r4()
    material["scan_target_schema_versions"] = list(material["scan_target_schema_versions"][:-1])
    with pytest.raises(ValueError):
        r55.assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(material)

    material = _r4()
    material["scan_target_material_count"] = 999
    with pytest.raises(ValueError):
        r55.assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(material)


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
def test_r55_r4_builder_rejects_forbidden_payload_keys_in_scan_targets(forbidden_key: str) -> None:
    safe_target = {
        "schema_version": "cocolon.emlis.p7_r55.safe_target.bodyfree.v1",
        "material_id": "safe_scan_target",
        "policy_section": "safe_bodyfree_scan_target",
        "body_free": True,
        forbidden_key: "must_not_be_materialized",
    }
    with pytest.raises(ValueError):
        r55.build_p7_r55_bodyfree_forbidden_payload_scan_bodyfree(
            r54_handoff_intake=_r3(),
            scan_target_materials=[safe_target],
        )


@pytest.mark.parametrize(
    "flag",
    [
        "raw_input_included",
        "comment_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_absolute_path_included",
        "terminal_output_included",
        "p5_human_blind_qa_confirmed_final",
        "p8_start_allowed",
        "release_allowed",
    ],
)
def test_r55_r4_builder_rejects_forbidden_true_flags_in_scan_targets(flag: str) -> None:
    unsafe_target = {
        "schema_version": "cocolon.emlis.p7_r55.unsafe_true_flag_target.bodyfree.v1",
        "material_id": "unsafe_true_flag_target",
        "policy_section": "unsafe_true_flag_target",
        "body_free": True,
        flag: True,
    }
    with pytest.raises(ValueError):
        r55.build_p7_r55_bodyfree_forbidden_payload_scan_bodyfree(
            r54_handoff_intake=_r3(),
            scan_target_materials=[unsafe_target],
        )


def test_r55_r5_assesses_actual_review_evidence_gap_as_missing_without_repair_or_p8_promotion() -> None:
    material = _r5()

    assert material["schema_version"] == r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["policy_section"] == "R55-5_actual_review_evidence_gap_assessment"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"

    assert material["r4_bodyfree_forbidden_payload_scan_schema_version"] == r55.P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_SCHEMA_VERSION
    assert material["r3_r54_handoff_intake_schema_version"] == r55.P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION
    assert material["actual_review_evidence_source_ref"] == "r54_default_handoff_intake_actual_review_evidence_missing"
    assert material["r54_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert material["r54_review_operation_state_ref"] == "not_started"
    assert material["r54_p5_decision_candidate_ref"] == "P5_NOT_REVIEWED"

    assert material["actual_review_evidence_complete"] is False
    assert material["required_case_count"] == 24
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["missing_evidence_refs"]) == r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS
    assert material["missing_evidence_ref_count"] == len(r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS)
    assert material["gap_status_ref"] == "ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert material["p5_decision_status_ref"] == "R55_P5_NOT_REVIEWED_EVIDENCE_MISSING"
    assert material["p5_decision_candidate_ref"] == "P5_NOT_REVIEWED"

    assert material["evidence_missing_classified_as_p5_repair_required"] is False
    assert material["evidence_missing_classified_as_p8_material_candidate"] is False
    assert material["p5_repair_return_candidate"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["bodyfree_forbidden_payload_scan_clear"] is True
    assert material["blocked_by_body_free_boundary_risk"] is False
    assert material["blocked_by_no_touch_violation"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is True
    assert material["r55_4_bodyfree_forbidden_payload_scan_done"] is True
    assert material["r55_5_actual_review_evidence_gap_assessed"] is True
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R5_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R5_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == r55.P7_R55_R5_NEXT_REQUIRED_STEP_REF

    _assert_no_body_or_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("evidence_missing_classified_as_p5_repair_required", True),
        ("evidence_missing_classified_as_p8_material_candidate", True),
        ("p5_repair_return_candidate", True),
        ("p8_question_design_material_candidate", True),
        ("blocked_by_body_free_boundary_risk", True),
        ("blocked_by_no_touch_violation", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_r55_r5_rejects_actual_review_completion_repair_p8_or_release_claims(key: str, value: object) -> None:
    material = _r5()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("gap_status_ref", "ACTUAL_REVIEW_EVIDENCE_COMPLETE"),
        ("p5_decision_status_ref", "R55_P5_REPAIR_REQUIRED"),
        ("p5_decision_candidate_ref", "P5_CONFIRMED_CANDIDATE"),
        ("r54_handoff_status", "R54_R52_REINTAKE_HANDOFF_READY"),
        ("r54_review_operation_state_ref", "completed"),
        ("r54_p5_decision_candidate_ref", "P5_CONFIRMED_CANDIDATE"),
        ("required_case_count", 23),
        ("missing_evidence_refs", ["question_need_observation_actual_rows_missing"]),
        ("missing_evidence_ref_count", 1),
        ("bodyfree_forbidden_payload_scan_clear", False),
        ("r55_4_bodyfree_forbidden_payload_scan_done", False),
    ],
)
def test_r55_r5_rejects_gap_reclassification_or_missing_evidence_rewrite(key: str, value: object) -> None:
    material = _r5()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material)


def test_r55_r5_rejects_body_or_question_payload_keys_inside_gap_assessment() -> None:
    material = _r5()
    material["raw_input"] = "must not be stored"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material)

    material = _r5()
    material["question_text"] = "must not be designed here"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material)

    material = _r5()
    material["terminal_output"] = "must not be stored"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material)


def test_r55_r5_builder_rejects_blocked_r4_scan_before_gap_assessment() -> None:
    r4 = _r4()
    r4["blocked_by_body_free_boundary_risk"] = True
    with pytest.raises(ValueError):
        r55.build_p7_r55_actual_review_evidence_gap_assessment_bodyfree(
            r54_handoff_intake=_r3(),
            bodyfree_forbidden_payload_scan=r4,
        )
