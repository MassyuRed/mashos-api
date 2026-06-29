# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


FORBIDDEN_BODY_KEY_TOKENS = (
    '"raw_input":',
    '"comment_text":',
    '"returned_surface":',
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
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_start_allowed": true',
    '"p7_complete": true',
    '"release_allowed": true',
    '"full_backend_suite_green_confirmed": true',
    '"rn_contract_claimed_as_real_device_modal_readfeel": true',
)


def _assert_no_body_or_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for token in FORBIDDEN_BODY_KEY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_TRUE_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_r2() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_validation_evidence_reconcile_bodyfree()
    assert r55.assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(material) is True
    return (material,)


def _r2() -> dict[str, object]:
    return deepcopy(_cached_r2()[0])


@lru_cache(maxsize=1)
def _cached_r3() -> tuple[dict[str, object]]:
    material = r55.build_p7_r55_r54_handoff_intake_bodyfree(validation_evidence_reconcile=_r2())
    assert r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material) is True
    return (material,)


def _r3() -> dict[str, object]:
    return deepcopy(_cached_r3()[0])


def test_r55_r2_reconciles_validation_evidence_claim_levels_without_p5_review_promotion() -> None:
    material = _r2()

    assert material["schema_version"] == r55.P7_R55_VALIDATION_EVIDENCE_RECONCILE_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_VALIDATION_EVIDENCE_RECONCILE_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["policy_section"] == "R55-2_validation_evidence_reconcile"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"

    assert material["validation_evidence_row_count"] == 8
    assert material["validation_evidence_group_refs"] == list(r55.P7_R55_VALIDATION_EVIDENCE_GROUP_REFS)
    assert material["claim_level_refs_present"] is True
    assert material["passed_target_row_count"] == 2
    assert material["passed_split_target_row_count"] == 2
    assert material["collect_only_row_count"] == 1
    assert material["timeout_one_shot_row_count"] == 2
    assert material["not_run_or_unconfirmed_row_count"] == 1
    assert material["green_allowed_row_count"] == 4
    assert material["green_claim_allowed_passed_count_total"] == 855

    assert material["one_shot_timeout_claimed_as_green"] is False
    assert material["collect_only_claimed_as_green"] is False
    assert material["rn_contract_claimed_as_real_device_modal_readfeel"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["split_green_claimed_as_actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is False
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R2_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R2_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == r55.P7_R55_R2_NEXT_REQUIRED_STEP_REF

    _assert_no_body_or_promotion(material)


def test_r55_r2_validation_rows_keep_split_green_collect_only_timeout_and_not_run_separate() -> None:
    rows = {row["evidence_group_ref"]: row for row in _r2()["validation_evidence_rows"]}

    assert rows["rn_contract"]["claim_level_ref"] == "PASSED_TARGET"
    assert rows["rn_contract"]["passed_count"] == 36
    assert rows["rn_contract"]["green_claim_allowed"] is True
    assert rows["rn_contract"]["rn_real_device_modal_readfeel_claimed"] is False

    assert rows["r52_target"]["claim_level_ref"] == "PASSED_TARGET"
    assert rows["r52_target"]["passed_count"] == 219
    assert rows["r52_target"]["p6_p8_start_allowed_claim"] is False

    assert rows["r53_target_split"]["claim_level_ref"] == "PASSED_SPLIT_TARGET"
    assert rows["r53_target_split"]["passed_count"] == 291
    assert rows["r53_target_split"]["green_claim_allowed"] is True

    assert rows["r53_one_shot_timeout"]["claim_level_ref"] == "TIMEOUT_ONE_SHOT"
    assert rows["r53_one_shot_timeout"]["timeout_observed"] is True
    assert rows["r53_one_shot_timeout"]["green_claim_allowed"] is False
    assert rows["r53_one_shot_timeout"]["one_shot_timeout_claimed_as_green"] is False

    assert rows["r54_collect_only"]["claim_level_ref"] == "COLLECT_ONLY"
    assert rows["r54_collect_only"]["collected_count"] == 309
    assert rows["r54_collect_only"]["passed_count"] == 0
    assert rows["r54_collect_only"]["green_claim_allowed"] is False
    assert rows["r54_collect_only"]["collect_only_claimed_as_green"] is False

    assert rows["r54_target_split"]["claim_level_ref"] == "PASSED_SPLIT_TARGET"
    assert rows["r54_target_split"]["passed_count"] == 309
    assert rows["r54_target_split"]["p5_actual_review_completion_claimed"] is False

    assert rows["r54_one_shot_timeout"]["claim_level_ref"] == "TIMEOUT_ONE_SHOT"
    assert rows["r54_one_shot_timeout"]["timeout_observed"] is True
    assert rows["r54_one_shot_timeout"]["green_claim_allowed"] is False

    assert rows["full_backend_suite"]["claim_level_ref"] == "NOT_RUN"
    assert rows["full_backend_suite"]["full_backend_suite_green_claimed"] is False
    assert rows["full_backend_suite"]["green_claim_allowed"] is False


@pytest.mark.parametrize(
    "key,value",
    [
        ("one_shot_timeout_claimed_as_green", True),
        ("collect_only_claimed_as_green", True),
        ("rn_contract_claimed_as_real_device_modal_readfeel", True),
        ("full_backend_suite_green_confirmed", True),
        ("split_green_claimed_as_actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("r55_3_r54_default_handoff_intake_done", True),
    ],
)
def test_r55_r2_rejects_validation_claim_inflation_actual_review_or_p6_p8_release_promotion(
    key: str, value: object
) -> None:
    material = _r2()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(material)


@pytest.mark.parametrize(
    "row_index,key,value",
    [
        (3, "green_claim_allowed", True),
        (3, "one_shot_timeout_claimed_as_green", True),
        (4, "green_claim_allowed", True),
        (4, "collect_only_claimed_as_green", True),
        (5, "p5_actual_review_completion_claimed", True),
        (7, "full_backend_suite_green_claimed", True),
        (0, "rn_real_device_modal_readfeel_claimed", True),
        (1, "p6_p8_start_allowed_claim", True),
        (2, "release_allowed_claimed", True),
    ],
)
def test_r55_r2_rejects_row_level_green_or_product_claim_inflation(row_index: int, key: str, value: object) -> None:
    material = _r2()
    rows = list(material["validation_evidence_rows"])
    row = dict(rows[row_index])
    row[key] = value
    rows[row_index] = row
    material["validation_evidence_rows"] = rows
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(material)


def test_r55_r2_rejects_missing_unclassified_or_reordered_validation_rows() -> None:
    material = _r2()
    material["validation_evidence_rows"] = list(material["validation_evidence_rows"][:-1])
    material["validation_evidence_row_count"] = 7
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(material)

    material = _r2()
    material["validation_evidence_rows"] = list(reversed(material["validation_evidence_rows"]))
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(material)

    material = _r2()
    rows = list(material["validation_evidence_rows"])
    rows[0] = dict(rows[0], claim_level_ref="UNKNOWN")
    material["validation_evidence_rows"] = rows
    with pytest.raises(ValueError):
        r55.assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(material)


def test_r55_r3_intakes_r54_default_handoff_as_actual_review_evidence_missing_without_current_basis_confusion() -> None:
    material = _r3()

    assert material["schema_version"] == r55.P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION
    assert set(material) == set(r55.P7_R55_R54_HANDOFF_INTAKE_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["policy_section"] == "R55-3_r54_default_handoff_intake"
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["r54_handoff_current_received_snapshot_refs"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["r54_handoff_current_snapshot_used_as_actual_review_basis"] is False
    assert material["current_received_snapshot_used_as_actual_review_basis"] is True
    assert material["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"

    assert material["r54_handoff_schema_version"] == r54.P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION
    assert material["r54_handoff_policy_section_ref"] == r54.P7_R54_R22_STEP_REF
    assert material["r54_handoff_status"] == "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
    assert material["r54_handoff_reason_refs"] == ["r54_21_final_validation_not_ready"]
    assert material["r54_review_operation_state_ref"] == "not_started"
    assert material["r54_p5_decision_candidate_ref"] == "P5_NOT_REVIEWED"
    assert material["r54_actual_review_evidence_complete"] is False
    assert material["r54_r52_reintake_ready"] is False
    assert material["r54_r52_reintake_materialized_here"] is False

    assert material["r54_validation_documentation_schema_version"] == r54.P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert material["r54_validation_documentation_policy_section_ref"] == r54.P7_R54_R23_STEP_REF
    assert material["r54_validation_documentation_status"] == "VALIDATION_DOCUMENTATION_BLOCKED_BY_R54_22_R52_REINTAKE_HANDOFF"
    assert material["r54_validation_documentation_materialized_here"] is False

    assert material["forbidden_payload_detected"] is False
    assert material["question_text_detected"] is False
    assert material["no_touch_violation_detected"] is False
    assert material["no_touch_touched_refs"] == []
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False

    assert material["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert material["r55_1_prior_helper_source_reconciled"] is True
    assert material["r55_2_validation_evidence_reconciled"] is True
    assert material["r55_3_r54_default_handoff_intake_done"] is True
    assert tuple(material["implemented_steps"]) == r55.P7_R55_R3_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r55.P7_R55_R3_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == r55.P7_R55_R3_NEXT_REQUIRED_STEP_REF

    _assert_no_body_or_promotion(material)


def test_r55_r3_accepts_explicit_default_r54_handoff_and_documentation_materials() -> None:
    handoff = r54.build_p7_r54_r52_reintake_handoff_bodyfree()
    assert r54.assert_p7_r54_r52_reintake_handoff_bodyfree_contract(handoff) is True
    documentation = r54.build_p7_r54_validation_command_matrix_documentation_output_bodyfree(
        r52_reintake_handoff=handoff,
    )
    assert r54.assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract(documentation) is True

    intake = r55.build_p7_r55_r54_handoff_intake_bodyfree(
        validation_evidence_reconcile=_r2(),
        r54_r52_reintake_handoff=handoff,
        r54_validation_documentation_output=documentation,
    )

    assert intake["r54_handoff_material_ref"] == handoff["material_id"]
    assert intake["r54_validation_documentation_material_ref"] == documentation["material_id"]
    assert intake["r54_handoff_status"] == handoff["r52_reintake_handoff_status"]
    assert intake["r54_validation_documentation_status"] == documentation["validation_documentation_status"]
    assert intake["r54_actual_review_evidence_complete"] is False
    assert intake["r54_review_operation_state_ref"] == "not_started"


@pytest.mark.parametrize(
    "key,value",
    [
        ("current_received_snapshot_used_as_actual_review_basis", False),
        ("r54_handoff_current_snapshot_used_as_actual_review_basis", True),
        ("r54_actual_review_evidence_complete", True),
        ("r54_r52_reintake_ready", True),
        ("r54_r52_reintake_materialized_here", True),
        ("r54_validation_documentation_materialized_here", True),
        ("forbidden_payload_detected", True),
        ("question_text_detected", True),
        ("no_touch_violation_detected", True),
        ("actual_review_evidence_complete", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_r55_r3_rejects_r54_handoff_intake_promotion_body_risk_or_release_claims(key: str, value: object) -> None:
    material = _r3()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)


def test_r55_r3_rejects_ready_or_non_default_r54_handoff_status_as_current_default_intake() -> None:
    material = _r3()
    material["r54_handoff_status"] = "R54_R52_REINTAKE_HANDOFF_READY"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)

    material = _r3()
    material["r54_validation_documentation_status"] = "VALIDATION_COMMAND_MATRIX_DOCUMENTATION_READY"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)

    material = _r3()
    material["r54_review_operation_state_ref"] = "completed"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)

    material = _r3()
    material["r54_p5_decision_candidate_ref"] = "P5_CONFIRMED_CANDIDATE"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)


def test_r55_r3_rejects_body_or_question_payload_keys_inside_intake_material() -> None:
    material = _r3()
    material["raw_input"] = "must not be stored"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)

    material = _r3()
    material["question_text"] = "must not be designed here"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)

    material = _r3()
    material["terminal_output"] = "must not be stored"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)
