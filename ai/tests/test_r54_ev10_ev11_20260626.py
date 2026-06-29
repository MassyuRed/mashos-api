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
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"disposal_verified": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"actual_review_evidence_complete": true',
    '"existing_op12_reused_as_actual_rating_basis": true',
    '"existing_op13_reused_as_actual_ingestion_basis": true',
)


def _assert_body_free_no_promotion(
    material: dict[str, object],
    *,
    allow_rating_rows: bool = False,
    allow_blocker_rows: bool = False,
) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped
    if not allow_rating_rows:
        assert '"actual_rating_rows_materialized_here": true' not in dumped
    if not allow_blocker_rows:
        assert '"actual_blocker_rows_materialized_here": true' not in dumped


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


def _selection_rows_with_readfeel_and_execution_blockers() -> list[dict[str, object]]:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["verdict"] = "YELLOW"
    rows[0]["sanitized_reason_ids"] = ["fixture_bodyfree_readfeel_blocker_reason"]
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]

    rows[1] = dict(rows[1])
    rows[1]["verdict"] = "NOT_REVIEWABLE"
    rows[1]["sanitized_reason_ids"] = ["fixture_bodyfree_execution_blocker_reason"]
    rows[1]["execution_blocker_ids"] = ["reviewer_not_assigned"]
    rows[1]["question_need_primary_class"] = "insufficient_material_execution_blocker"
    rows[1]["one_question_fit_ref"] = "insufficient_material"
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


@lru_cache(maxsize=1)
def _cached_ev09_ready_with_blockers() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev09_sanitized_review_result_row_intake(
        reviewer_selection_form_freeze=_ev08_ready(),
        reviewer_selection_rows=_selection_rows_with_readfeel_and_execution_blockers(),
    )
    assert ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material) is True
    return (material,)


def _ev09_ready_with_blockers() -> dict[str, object]:
    return deepcopy(_cached_ev09_ready_with_blockers()[0])


def _ev10_ready() -> dict[str, object]:
    material = ev.build_p7_r54_ev10_rating_row_normalization(
        sanitized_review_result_row_intake=_ev09_ready(),
    )
    assert ev.assert_p7_r54_ev10_rating_row_normalization_contract(material) is True
    return material


def _ev10_ready_with_blockers() -> dict[str, object]:
    material = ev.build_p7_r54_ev10_rating_row_normalization(
        sanitized_review_result_row_intake=_ev09_ready_with_blockers(),
    )
    assert ev.assert_p7_r54_ev10_rating_row_normalization_contract(material) is True
    return material


def test_r54_ev10_blocks_without_ev09_ready_rows_and_keeps_rating_rows_absent() -> None:
    material = ev.build_p7_r54_ev10_rating_row_normalization(
        sanitized_review_result_row_intake=_ev09_blocked(),
    )

    assert material["schema_version"] == ev.P7_R54_EV10_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV10_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV10_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV10_STEP_REF
    assert material["body_free"] is True
    assert material["rating_row_normalization_status"] == ev.P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF
    assert material["ev09_rating_row_normalization_allowed_next"] is False
    assert material["rating_rows"] == []
    assert material["rating_row_count"] == 0
    assert material["reviewed_case_count"] == 0
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is False
    assert "ev09_sanitized_review_result_rows_not_ready_for_rating_normalization" in material["execution_blocker_ids"]
    assert material["next_required_step"] == ev.P7_R54_EV10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["existing_op12_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op12_operation_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["existing_op12_current_refs_are_historical_here"] is True
    assert material["existing_op12_reused_as_actual_rating_basis"] is False
    assert material["existing_op12_structural_contract_reused"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev10_ready_normalizes_24_rating_rows_bodyfree_without_review_completion() -> None:
    material = _ev10_ready()

    assert material["rating_row_normalization_status"] == ev.P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
    assert material["rating_row_normalization_ref"] == ev.P7_R54_EV10_RATING_ROW_NORMALIZATION_REF
    assert material["rating_row_normalization_policy_ref"] == ev.P7_R54_EV10_RATING_ROW_NORMALIZATION_POLICY_REF
    assert material["rating_row_normalization_reason_refs"] == [ev.P7_R54_EV10_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_ref_count"] == 24
    assert material["packet_ref_count"] == 24
    assert material["case_ref_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["rating_row_refs_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["all_required_rating_rows_present"] is True
    assert material["rating_case_ref_sets_match_sanitized_intake"] is True
    assert tuple(material["allowed_verdict_refs"]) == ev.P7_R54_EV08_VERDICT_OPTION_REFS
    assert material["rating_consistency_issue_count"] == 0
    assert material["verdict_counts"] == {"PASS": 24, "YELLOW": 0, "REPAIR_REQUIRED": 0, "RED": 0, "NOT_REVIEWABLE": 0}
    for axis in ev.P7_R54_EV08_RATING_AXIS_REFS:
        assert material["axis_score_averages"][axis] == 1.0
    assert material["readfeel_blocker_row_candidate_count"] == 0
    assert material["execution_blocker_row_candidate_count"] == 0
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is True
    assert material["rating_rows_normalized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV10_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV11_STEP_REF

    rows = material["rating_rows"]
    assert isinstance(rows, list)
    for row in rows:
        assert set(row) == set(ev.P7_R54_EV10_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == ev.P7_R54_EV10_RATING_ROW_SCHEMA_VERSION
        assert row["rating_source_ref"] == ev.P7_R54_EV10_RATING_ROW_SOURCE_REF
        assert tuple(row["axis_scores"].keys()) == ev.P7_R54_EV08_RATING_AXIS_REFS
        assert row["axis_score_count"] == len(ev.P7_R54_EV08_RATING_AXIS_REFS)
        assert row["verdict"] == "PASS"
        assert row["below_target_axis_count"] == 0
        assert row["readfeel_blocker_count"] == 0
        assert row["execution_blocker_count"] == 0
        assert row["machine_auto_score_used"] is False
        assert row["machine_metrics_used_for_readfeel"] is False
        assert row["reviewer_free_text_included"] is False
        assert row["raw_body_included"] is False
        assert row["question_text_included"] is False
        assert row["local_path_included"] is False
        assert row["body_hash_included"] is False
        assert row["packet_content_included"] is False
        assert row["body_free"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        if key == "actual_rating_rows_materialized_here":
            assert material[key] is True
        else:
            assert material[key] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True)


def test_r54_ev10_blocks_pass_with_blocker_consistency_issue_and_does_not_materialize_rating_rows() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    ev09 = ev.build_p7_r54_ev09_sanitized_review_result_row_intake(
        reviewer_selection_form_freeze=_ev08_ready(),
        reviewer_selection_rows=rows,
    )
    assert ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(ev09) is True
    material = ev.build_p7_r54_ev10_rating_row_normalization(
        sanitized_review_result_row_intake=ev09,
    )

    assert material["rating_row_normalization_status"] == ev.P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF
    assert material["rating_rows"] == []
    assert material["rating_row_count"] == 0
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is False
    assert "rating_row_verdict_blocker_consistency_failed" in material["execution_blocker_ids"]
    assert material["pass_with_any_blocker_detected"] is True
    assert material["rating_consistency_issue_count"] == 1
    assert material["next_required_step"] == ev.P7_R54_EV10_BLOCKED_NEXT_REQUIRED_STEP_REF
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev11_ready_ingests_zero_blockers_separately_after_clean_ev10() -> None:
    ev10 = _ev10_ready()
    material = ev.build_p7_r54_ev11_blocker_ingestion(
        rating_row_normalization=ev10,
    )

    assert material["schema_version"] == ev.P7_R54_EV11_BLOCKER_INGESTION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV11_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV11_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV11_STEP_REF
    assert material["blocker_ingestion_status"] == ev.P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF
    assert material["blocker_ingestion_ref"] == ev.P7_R54_EV11_BLOCKER_INGESTION_REF
    assert material["blocker_ingestion_policy_ref"] == ev.P7_R54_EV11_BLOCKER_INGESTION_POLICY_REF
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["ev10_blocker_ingestion_allowed_next"] is True
    assert material["rating_row_count"] == 24
    assert material["rating_rows_preserved_from_ev10"] is True
    assert material["readfeel_blocker_rows"] == []
    assert material["execution_blocker_rows"] == []
    assert material["readfeel_blocker_row_count"] == 0
    assert material["execution_blocker_row_count"] == 0
    assert material["open_readfeel_blocker_count"] == 0
    assert material["open_execution_blocker_count"] == 0
    assert material["readfeel_blocker_row_builder_ready"] is True
    assert material["execution_blocker_row_builder_ready"] is True
    assert material["readfeel_and_execution_blockers_separated"] is True
    assert material["execution_blocker_not_mixed_into_readfeel_verdict"] is True
    assert material["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["question_need_observation_row_normalization_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV12_NEXT_REQUIRED_STEP_REF
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        if key == "actual_rating_rows_materialized_here":
            assert material[key] is True
        else:
            assert material[key] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True)


def test_r54_ev11_ready_separates_readfeel_and_execution_blockers_without_mixing_verdicts() -> None:
    ev10 = _ev10_ready_with_blockers()
    assert ev10["readfeel_blocker_row_candidate_count"] == 1
    assert ev10["execution_blocker_row_candidate_count"] == 1

    material = ev.build_p7_r54_ev11_blocker_ingestion(
        rating_row_normalization=ev10,
    )

    assert material["blocker_ingestion_status"] == ev.P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF
    assert material["readfeel_blocker_row_count"] == 1
    assert material["execution_blocker_row_count"] == 1
    assert material["open_readfeel_blocker_count"] == 1
    assert material["open_execution_blocker_count"] == 1
    assert material["readfeel_blocker_counts"] == {"p5_history_connection_too_generic": 1}
    assert material["execution_blocker_counts"] == {"reviewer_not_assigned": 1}
    assert material["p5_confirmed_candidate_blocked_by_open_execution_blockers"] is True
    assert material["readfeel_and_execution_blockers_separated"] is True
    assert material["execution_blocker_not_mixed_into_readfeel_verdict"] is True
    assert material["execution_blockers_do_not_assign_readfeel_verdict"] is True

    readfeel_rows = material["readfeel_blocker_rows"]
    execution_rows = material["execution_blocker_rows"]
    assert isinstance(readfeel_rows, list)
    assert isinstance(execution_rows, list)
    assert set(readfeel_rows[0]) == set(ev.P7_R54_EV11_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert set(execution_rows[0]) == set(ev.P7_R54_EV11_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert readfeel_rows[0]["schema_version"] == ev.P7_R54_EV11_READFEEL_BLOCKER_ROW_SCHEMA_VERSION
    assert execution_rows[0]["schema_version"] == ev.P7_R54_EV11_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION
    assert readfeel_rows[0]["blocker_kind_ref"] == ev.P7_R54_EV11_READFEEL_BLOCKER_KIND_REF
    assert execution_rows[0]["execution_blocker_kind_ref"] == ev.P7_R54_EV11_EXECUTION_BLOCKER_KIND_REF
    assert readfeel_rows[0]["source_verdict"] == "YELLOW"
    assert "source_verdict" not in execution_rows[0]
    assert execution_rows[0]["execution_blocker_does_not_assign_readfeel_verdict"] is True
    assert readfeel_rows[0]["body_free"] is True
    assert execution_rows[0]["body_free"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op12_current_refs_are_historical_here", False),
        ("existing_op12_reused_as_actual_rating_basis", True),
        ("existing_op12_structural_contract_reused", False),
        ("required_case_count", 23),
        ("rating_row_normalization_status", ev.P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF),
        ("rating_row_count", 23),
        ("reviewed_case_count", 23),
        ("rating_row_refs_unique", False),
        ("all_axes_present", False),
        ("axis_score_range_valid", False),
        ("verdict_allowed", False),
        ("rating_rows_are_bodyfree", False),
        ("actual_rating_rows_materialized_here", False),
        ("actual_blocker_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("question_observation_row_count", 24),
        ("disposal_verified", True),
        ("actual_human_review_run_here", True),
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
def test_r54_ev10_rejects_rating_normalization_boundary_mutations(key: str, value: object) -> None:
    material = _ev10_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev10_rating_row_normalization_contract(material)


def test_r54_ev10_rejects_old_refs_or_body_leak_keys() -> None:
    material = _ev10_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev10_rating_row_normalization_contract(material)

    material = _ev10_ready()
    material["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev10_rating_row_normalization_contract(material)

    material = _ev10_ready()
    material["rating_rows"][0]["question_text"] = "question text must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev10_rating_row_normalization_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op13_current_refs_are_historical_here", False),
        ("existing_op13_reused_as_actual_ingestion_basis", True),
        ("existing_op13_structural_contract_reused", False),
        ("required_case_count", 23),
        ("blocker_ingestion_status", ev.P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF),
        ("rating_row_count", 23),
        ("rating_row_refs_preserved", False),
        ("readfeel_blocker_rows_normalized", False),
        ("execution_blocker_rows_normalized", False),
        ("readfeel_and_execution_blockers_separated", False),
        ("execution_blocker_not_mixed_into_readfeel_verdict", False),
        ("execution_blocker_rows_do_not_assign_readfeel_verdict", False),
        ("actual_rating_rows_materialized_here", False),
        ("actual_blocker_rows_materialized_here", False),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("question_observation_row_count", 24),
        ("disposal_verified", True),
        ("question_need_observation_row_normalization_allowed_next", False),
        ("actual_human_review_run_here", True),
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
def test_r54_ev11_rejects_blocker_ingestion_boundary_mutations(key: str, value: object) -> None:
    material = ev.build_p7_r54_ev11_blocker_ingestion(rating_row_normalization=_ev10_ready())
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev11_blocker_ingestion_contract(material)


def test_r54_ev11_rejects_old_refs_or_body_leak_keys() -> None:
    material = ev.build_p7_r54_ev11_blocker_ingestion(rating_row_normalization=_ev10_ready())
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev11_blocker_ingestion_contract(material)

    material = ev.build_p7_r54_ev11_blocker_ingestion(rating_row_normalization=_ev10_ready())
    material["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev11_blocker_ingestion_contract(material)

    material = ev.build_p7_r54_ev11_blocker_ingestion(rating_row_normalization=_ev10_ready_with_blockers())
    material["readfeel_blocker_rows"][0]["reviewer_free_text"] = "free text must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev11_blocker_ingestion_contract(material)
