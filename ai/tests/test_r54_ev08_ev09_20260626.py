# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
from emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization import (
    P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
)


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
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"disposal_verified": true',
    '"existing_op09_reused_as_actual_form_basis": true',
    '"existing_op11_reused_as_actual_intake_basis": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"actual_review_evidence_complete": true',
    '"rating_row_normalization_allowed_next": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_ev04_ready() -> tuple[dict[str, object]]:
    ev03 = ev.build_p7_r54_ev03_r55_hold_intake_refreeze()
    material = ev.build_p7_r54_ev04_local_only_preflight_implementation_confirmation(
        r55_hold_intake_refreeze=ev03,
        local_review_root_presence_ref=ev.P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF,
        explicit_allow_token_ref=ev.P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF,
        purge_plan_ref=ev.P7_R54_EV04_PURGE_PLAN_READY_REF,
        retention_policy_ref=ev.P7_R54_EV04_RETENTION_POLICY_READY_REF,
        export_denylist_policy_ref=ev.P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF,
    )
    assert ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material) is True
    return (material,)


def _ev04_ready() -> dict[str, object]:
    return deepcopy(_cached_ev04_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev05_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev05_24_case_manifest_refreeze(
        local_only_preflight_implementation_confirmation=_ev04_ready(),
    )
    assert ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material) is True
    return (material,)


def _ev05_ready() -> dict[str, object]:
    return deepcopy(_cached_ev05_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev06_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev06_body_full_packet_generation_request_bodyfree(
        case_manifest_refreeze=_ev05_ready(),
    )
    assert ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material) is True
    return (material,)


def _ev06_ready() -> dict[str, object]:
    return deepcopy(_cached_ev06_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev07_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev07_local_operation_boundary_instruction(
        body_full_packet_generation_request_bodyfree=_ev06_ready(),
    )
    assert ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material) is True
    return (material,)


def _ev07_ready() -> dict[str, object]:
    return deepcopy(_cached_ev07_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev08_blocked() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev08_reviewer_selection_form_freeze()
    assert ev.assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(material) is True
    return (material,)


def _ev08_blocked() -> dict[str, object]:
    return deepcopy(_cached_ev08_blocked()[0])


@lru_cache(maxsize=1)
def _cached_ev08_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev08_reviewer_selection_form_freeze(
        local_operation_boundary_instruction=_ev07_ready(),
    )
    assert ev.assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(material) is True
    return (material,)


def _ev08_ready() -> dict[str, object]:
    return deepcopy(_cached_ev08_ready()[0])


def _selection_rows() -> list[dict[str, object]]:
    ev05 = _ev05_ready()
    ev08 = _ev08_ready()
    rows: list[dict[str, object]] = []
    controller_rows = ev05["controller_manifest_rows"]
    packet_refs = ev08["packet_ref_ids_for_review"]
    assert isinstance(controller_rows, list)
    assert isinstance(packet_refs, list)
    for index, (controller_row, packet_ref) in enumerate(zip(controller_rows, packet_refs), start=1):
        row = dict(controller_row)
        rows.append(
            {
                "review_result_row_ref": f"r54ev09-fixture-selection-row-{index:03d}",
                "case_ref_id": row["case_ref_id"],
                "blind_case_id": row["blind_case_id"],
                "packet_ref_id": packet_ref,
                "family": row["family"],
                "case_role": row["case_role"],
                "reviewer_ref": "reviewer_ref_local_001",
                "reviewed_at_ref": "coarse_reviewed_at_ref_20260626",
                "axis_scores": {axis: 1.0 for axis in ev.P7_R54_EV08_RATING_AXIS_REFS},
                "verdict": "PASS",
                "sanitized_reason_ids": ["fixture_selection_only_contract_row"],
                "readfeel_blocker_ids": [],
                "execution_blocker_ids": [],
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": ["no_repair_required"],
                "plan_candidate_flags": {
                    "plus_single_question_candidate_later": False,
                    "premium_deep_dive_candidate_later": False,
                    "p8_design_material_candidate": False,
                    "p8_implementation_spec_finalized_here": False,
                },
            }
        )
    assert len(rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    return rows


@lru_cache(maxsize=1)
def _cached_ev09_blocked() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev09_sanitized_review_result_row_intake(
        reviewer_selection_form_freeze=_ev08_ready(),
    )
    assert ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material) is True
    return (material,)


def _ev09_blocked() -> dict[str, object]:
    return deepcopy(_cached_ev09_blocked()[0])


@lru_cache(maxsize=1)
def _cached_ev09_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev09_sanitized_review_result_row_intake(
        reviewer_selection_form_freeze=_ev08_ready(),
        reviewer_selection_rows=_selection_rows(),
    )
    assert ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material) is True
    return (material,)


def _ev09_ready() -> dict[str, object]:
    return deepcopy(_cached_ev09_ready()[0])


def test_r54_ev08_blocks_without_ready_ev07_boundary_and_keeps_form_absent() -> None:
    material = _ev08_blocked()

    assert material["schema_version"] == ev.P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV08_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV08_STEP_REF
    assert material["body_free"] is True
    assert material["ev07_instruction_ready"] is False
    assert material["reviewer_selection_form_status"] == ev.P7_R54_EV08_FORM_BLOCKED_STATUS_REF
    assert material["reviewer_selection_form_ref"] == "reviewer_selection_form_not_frozen_until_ev07_boundary_ready"
    assert material["packet_ref_ids_for_review"] == []
    assert material["packet_ref_count_for_review"] == 0
    assert material["required_selection_field_refs"] == []
    assert material["verdict_option_refs"] == []
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["execution_blocker_ids"] == material["open_execution_blocker_ids"]
    assert "r54_ev08_blocked_until_ev07_local_operation_boundary_ready" in material["execution_blocker_ids"]
    assert material["next_required_step"] == ev.P7_R54_EV08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["existing_op09_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op09_operation_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["existing_op09_current_refs_are_historical_here"] is True
    assert material["existing_op09_reused_as_actual_form_basis"] is False
    assert material["existing_op09_structural_contract_reused"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev08_ready_freezes_selection_only_form_after_ev07_without_running_review() -> None:
    material = _ev08_ready()

    assert material["reviewer_selection_form_status"] == ev.P7_R54_EV08_FORM_READY_STATUS_REF
    assert material["reviewer_selection_form_ref"] == ev.P7_R54_EV08_REVIEWER_SELECTION_FORM_REF
    assert material["reviewer_selection_form_policy_ref"] == ev.P7_R54_EV08_REVIEWER_SELECTION_FORM_POLICY_REF
    assert material["reviewer_selection_form_reason_refs"] == [ev.P7_R54_EV08_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["ev07_instruction_ready"] is True
    assert material["ev07_next_required_step"] == ev.P7_R54_EV08_STEP_REF
    assert material["packet_ref_count_for_review"] == 24
    assert material["packet_ref_ids_for_review_unique"] is True
    assert len(material["packet_ref_ids_for_review"]) == 24

    assert material["reviewer_identity_policy_ref"] == ev.P7_R54_EV08_REVIEWER_IDENTITY_POLICY_REF
    assert material["reviewer_ref_pseudonymous_required"] is True
    assert tuple(material["required_selection_field_refs"]) == ev.P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS
    assert tuple(material["prohibited_selection_field_refs"]) == ev.P7_R54_EV08_PROHIBITED_SELECTION_FIELD_REFS
    assert tuple(material["rating_axis_refs"]) == ev.P7_R54_EV08_RATING_AXIS_REFS
    assert material["rating_axis_target_thresholds"] == ev.P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS
    assert tuple(material["score_option_refs"]) == ev.P7_R54_EV08_SCORE_OPTION_REFS
    assert tuple(material["verdict_option_refs"]) == ev.P7_R54_EV08_VERDICT_OPTION_REFS
    assert "NOT_REVIEWABLE" in material["verdict_option_refs"]
    assert tuple(material["readfeel_blocker_id_option_refs"]) == ev.P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS
    assert tuple(material["execution_blocker_id_option_refs"]) == ev.P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS
    assert tuple(material["question_need_primary_class_options"]) == ev.P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(material["ambiguity_kind_option_refs"]) == ev.P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS
    assert tuple(material["one_question_fit_option_refs"]) == ev.P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS
    assert tuple(material["repair_required_option_refs"]) == ev.P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS
    assert tuple(material["plan_candidate_flag_refs"]) == ev.P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS

    assert material["selection_form_is_bodyfree_only"] is True
    assert material["selection_form_contains_free_text_field"] is False
    assert material["selection_form_contains_raw_body_copy_field"] is False
    assert material["selection_form_contains_question_text_field"] is False
    assert material["selection_form_contains_local_path_field"] is False
    assert material["selection_form_contains_hash_field"] is False
    assert material["reviewer_free_text_export_allowed"] is False
    assert material["body_full_packet_generation_run_here"] is False
    assert material["actual_body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["sanitized_review_result_row_intake_allowed_next"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV09_STEP_REF
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev09_blocks_until_24_selection_only_rows_are_supplied() -> None:
    material = _ev09_blocked()

    assert material["schema_version"] == ev.P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV09_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV09_STEP_REF
    assert material["body_free"] is True
    assert material["ev08_form_ready"] is True
    assert material["ev08_next_required_step"] == ev.P7_R54_EV09_STEP_REF
    assert material["sanitized_review_result_intake_status"] == ev.P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF
    assert material["incoming_selection_row_count"] == 0
    assert material["sanitized_review_result_rows"] == []
    assert material["sanitized_review_result_row_count"] == 0
    assert material["reviewed_case_count"] == 0
    assert material["selection_rows_are_bodyfree_only"] is False
    assert material["sanitized_review_result_rows_materialized_here"] is False
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["execution_blocker_ids"] == material["open_execution_blocker_ids"]
    assert "sanitized_review_result_row_count_must_be_24" in material["execution_blocker_ids"]
    assert material["next_required_step"] == ev.P7_R54_EV09_BLOCKED_NEXT_REQUIRED_STEP_REF
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev09_ready_intakes_24_sanitized_rows_without_rating_normalization_or_completion_claim() -> None:
    material = _ev09_ready()

    assert material["sanitized_review_result_intake_status"] == ev.P7_R54_EV09_INTAKE_READY_STATUS_REF
    assert material["sanitized_review_result_intake_ref"] == ev.P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_REF
    assert material["sanitized_review_result_intake_policy_ref"] == ev.P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_POLICY_REF
    assert material["sanitized_review_result_intake_reason_refs"] == [ev.P7_R54_EV09_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["incoming_selection_row_count"] == 24
    assert material["expected_packet_ref_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["packet_ref_count"] == 24
    assert material["case_ref_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["reviewer_ref_ids"] == ["reviewer_ref_local_001"]
    assert material["reviewer_ref_count"] == 1
    assert material["packet_ref_ids"] == material["expected_packet_ref_ids"]

    assert material["selection_rows_are_bodyfree_only"] is True
    assert material["sanitized_rows_contain_reviewer_free_text"] is False
    assert material["sanitized_rows_contain_raw_body"] is False
    assert material["sanitized_rows_contain_comment_text"] is False
    assert material["sanitized_rows_contain_question_text"] is False
    assert material["sanitized_rows_contain_local_path"] is False
    assert material["sanitized_rows_contain_body_hash"] is False
    assert material["sanitized_rows_contain_packet_content"] is False
    assert material["sanitized_review_result_rows_materialized_here"] is True
    assert material["rating_row_normalization_allowed_next"] is True
    assert material["actual_human_review_run_by_helper"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV10_NEXT_REQUIRED_STEP_REF

    rows = material["sanitized_review_result_rows"]
    assert isinstance(rows, list)
    for row in rows:
        assert set(row) == set(ev.P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == ev.P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION
        assert row["selection_only_row"] is True
        assert tuple(row["axis_scores"].keys()) == ev.P7_R54_EV08_RATING_AXIS_REFS
        assert row["axis_score_count"] == len(ev.P7_R54_EV08_RATING_AXIS_REFS)
        assert row["verdict"] == "PASS"
        assert row["question_need_primary_class"] == "no_question_needed_emlis_can_observe"
        assert row["repair_required_refs"] == ["no_repair_required"]
        assert row["source_body_not_materialized_in_row"] is True
        assert row["reviewer_free_text_included"] is False
        assert row["raw_body_included"] is False
        assert row["question_text_included"] is False
        assert row["local_path_included"] is False
        assert row["body_hash_included"] is False
        assert row["packet_content_included"] is False
        assert row["body_free"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    # Rows are intaken to validate the helper, but this is not actual review completion evidence.
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        if forbidden == '"rating_row_normalization_allowed_next": true':
            continue
        assert forbidden not in dumped


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op09_current_refs_are_historical_here", False),
        ("existing_op09_reused_as_actual_form_basis", True),
        ("existing_op09_structural_contract_reused", False),
        ("existing_op09_verdict_options_are_historical_here", False),
        ("required_case_count", 23),
        ("reviewer_selection_form_status", ev.P7_R54_EV08_FORM_BLOCKED_STATUS_REF),
        ("packet_ref_count_for_review", 23),
        ("packet_ref_ids_for_review_unique", False),
        ("required_selection_field_count", 0),
        ("verdict_option_refs", list(r54op.P7_R54_OP09_VERDICT_OPTION_REFS)),
        ("selection_form_is_bodyfree_only", False),
        ("selection_form_contains_free_text_field", True),
        ("selection_form_contains_raw_body_copy_field", True),
        ("selection_form_contains_question_text_field", True),
        ("selection_form_contains_local_path_field", True),
        ("selection_form_contains_hash_field", True),
        ("reviewer_free_text_export_allowed", True),
        ("body_full_packet_generation_run_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("actual_human_review_run_here", True),
        ("sanitized_review_result_row_intake_allowed_next", False),
        ("p5_actual_review_still_not_run", False),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev08_rejects_selection_form_boundary_mutations(key: str, value: object) -> None:
    material = _ev08_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(material)


def test_r54_ev08_rejects_old_refs_or_body_leak_keys() -> None:
    material = _ev08_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(material)

    material = _ev08_ready()
    material["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op11_current_refs_are_historical_here", False),
        ("existing_op11_reused_as_actual_intake_basis", True),
        ("existing_op11_structural_contract_reused", False),
        ("required_case_count", 23),
        ("sanitized_review_result_intake_status", ev.P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF),
        ("incoming_selection_row_count", 23),
        ("sanitized_review_result_row_count", 23),
        ("reviewed_case_count", 23),
        ("packet_ref_count", 23),
        ("packet_ref_ids_unique", False),
        ("case_ref_ids_unique", False),
        ("blind_case_ids_unique", False),
        ("reviewer_ref_count", 0),
        ("selection_rows_are_bodyfree_only", False),
        ("sanitized_rows_contain_reviewer_free_text", True),
        ("sanitized_rows_contain_raw_body", True),
        ("sanitized_rows_contain_comment_text", True),
        ("sanitized_rows_contain_question_text", True),
        ("sanitized_rows_contain_local_path", True),
        ("sanitized_rows_contain_body_hash", True),
        ("sanitized_rows_contain_packet_content", True),
        ("sanitized_review_result_rows_materialized_here", False),
        ("rating_row_normalization_allowed_next", False),
        ("actual_human_review_run_by_helper", True),
        ("actual_human_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev09_rejects_sanitized_intake_boundary_mutations(key: str, value: object) -> None:
    material = _ev09_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material)


def test_r54_ev09_rejects_tampered_rows_old_refs_or_body_leak_keys() -> None:
    material = _ev09_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material)

    material = _ev09_ready()
    material["sanitized_review_result_rows"] = material["sanitized_review_result_rows"][:-1]
    material["sanitized_review_result_row_count"] = 23
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material)

    material = _ev09_ready()
    material["sanitized_review_result_rows"][0]["question_text_included"] = True
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material)

    rows = _selection_rows()
    rows[0]["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.build_p7_r54_ev09_sanitized_review_result_row_intake(
            reviewer_selection_form_freeze=_ev08_ready(),
            reviewer_selection_rows=rows,
        )

    rows = _selection_rows()
    rows[0]["packet_ref_id"] = "wrong_packet_ref"
    blocked = ev.build_p7_r54_ev09_sanitized_review_result_row_intake(
        reviewer_selection_form_freeze=_ev08_ready(),
        reviewer_selection_rows=rows,
    )
    assert blocked["sanitized_review_result_intake_status"] == ev.P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF
    assert "sanitized_review_packet_refs_must_match_ev08_packet_refs" in blocked["execution_blocker_ids"]
