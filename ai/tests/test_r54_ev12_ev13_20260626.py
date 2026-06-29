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
    '"actual_disposal_receipt_materialized_here": true',
    '"disposal_verified": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"actual_review_evidence_complete": true',
    '"existing_op14_reused_as_actual_question_observation_basis": true',
    '"existing_op14_reused_as_actual_normalization_basis": true',
    '"existing_op15_reused_as_actual_consistency_guard_basis": true',
)


def _assert_body_free_no_promotion(
    material: dict[str, object],
    *,
    allow_rating_rows: bool = False,
    allow_blocker_rows: bool = False,
    allow_question_rows: bool = False,
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
    if not allow_question_rows:
        assert '"actual_question_need_observation_rows_materialized_here": true' not in dumped


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
def _cached_ev08_ready() -> tuple[dict[str, object]]:
    ev05 = _ev05_ready()
    ev06 = ev.build_p7_r54_ev06_body_full_packet_generation_request_bodyfree(case_manifest_refreeze=ev05)
    assert ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(ev06) is True
    ev07 = ev.build_p7_r54_ev07_local_operation_boundary_instruction(
        body_full_packet_generation_request_bodyfree=ev06,
    )
    assert ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(ev07) is True
    material = ev.build_p7_r54_ev08_reviewer_selection_form_freeze(
        local_operation_boundary_instruction=ev07,
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
                "review_result_row_ref": f"r54ev12-fixture-selection-row-{index:03d}",
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


def _ev09_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    material = ev.build_p7_r54_ev09_sanitized_review_result_row_intake(
        reviewer_selection_form_freeze=_ev08_ready(),
        reviewer_selection_rows=rows if rows is not None else _selection_rows(),
    )
    assert ev.assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material) is True
    return material


def _ev10_ready(rows: list[dict[str, object]] | None = None) -> tuple[dict[str, object], dict[str, object]]:
    ev09 = _ev09_ready(rows)
    material = ev.build_p7_r54_ev10_rating_row_normalization(
        sanitized_review_result_row_intake=ev09,
    )
    assert ev.assert_p7_r54_ev10_rating_row_normalization_contract(material) is True
    return ev09, material


def _ev11_ready(rows: list[dict[str, object]] | None = None) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ev09, ev10 = _ev10_ready(rows)
    material = ev.build_p7_r54_ev11_blocker_ingestion(
        rating_row_normalization=ev10,
    )
    assert ev.assert_p7_r54_ev11_blocker_ingestion_contract(material) is True
    return ev09, ev10, material


def _ev12_ready(rows: list[dict[str, object]] | None = None) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    ev09, ev10, ev11 = _ev11_ready(rows)
    material = ev.build_p7_r54_ev12_question_need_observation_row_normalization(
        blocker_ingestion=ev11,
        rating_row_normalization=ev10,
        sanitized_review_result_row_intake=ev09,
    )
    assert ev.assert_p7_r54_ev12_question_need_observation_row_normalization_contract(material) is True
    return ev09, ev10, ev11, material


def test_r54_ev12_ready_normalizes_24_question_need_rows_bodyfree() -> None:
    _, ev10, ev11, material = _ev12_ready()

    assert material["schema_version"] == ev.P7_R54_EV12_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV12_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV12_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV12_STEP_REF
    assert material["question_observation_normalization_status"] == ev.P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    assert material["question_observation_normalization_ref"] == ev.P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_REF
    assert material["question_observation_normalization_policy_ref"] == ev.P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_POLICY_REF
    assert material["ev11_question_observation_normalization_allowed_next"] is True
    assert material["ev11_next_required_step"] == ev.P7_R54_EV12_STEP_REF
    assert material["ev10_rating_row_normalization_status"] == ev.P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
    assert material["required_case_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["question_observation_row_refs_unique"] is True
    assert material["case_ref_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["row_case_ref_sets_match_review_intake"] is True
    assert material["row_case_ref_sets_match_rating_rows"] is True
    assert material["all_required_question_need_observation_rows_present"] is True
    assert material["primary_class_ambiguity_one_question_fit_are_canonical_refs"] is True
    assert material["rating_rows_preserved_from_ev10"] is True
    assert material["blocker_rows_preserved_from_ev11"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_verified"] is False
    assert material["rating_question_consistency_guard_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV13_STEP_REF
    assert ev10["actual_rating_rows_materialized_here"] is True
    assert ev11["actual_blocker_rows_materialized_here"] is True

    rows = material["question_observation_rows"]
    assert isinstance(rows, list)
    for row in rows:
        assert set(row) == set(ev.P7_R54_EV12_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == ev.P7_R54_EV12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
        assert row["question_need_primary_class"] == "no_question_needed_emlis_can_observe"
        assert row["ambiguity_kind_refs"] == ["no_material_ambiguity"]
        assert row["one_question_fit_ref"] == "not_needed"
        assert row["repair_required_refs"] == ["no_repair_required"]
        assert row["p8_material_candidate_requested"] is False
        assert row["p8_material_candidate_allowed"] is False
        assert row["not_question_repair_required"] is False
        assert row["insufficient_material_execution_blocker"] is False
        assert row["question_text_included"] is False
        assert row["draft_question_text_included"] is False
        assert row["reviewer_free_text_included"] is False
        assert row["raw_body_included"] is False
        assert row["local_path_included"] is False
        assert row["body_hash_included"] is False
        assert row["packet_content_included"] is False
        assert row["body_free"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        if key in {"actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}:
            assert material[key] is True
        else:
            assert material[key] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


def test_r54_ev12_preserves_selection_only_p8_candidate_flags_without_creating_question_text() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["question_need_primary_class"] = "plus_single_question_candidate_later"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"] = {
        "plus_single_question_candidate_later": True,
        "premium_deep_dive_candidate_later": False,
        "p8_design_material_candidate": True,
        "p8_implementation_spec_finalized_here": False,
    }
    _, _, _, material = _ev12_ready(rows)

    assert material["p8_material_candidate_requested_row_count"] == 1
    assert material["p8_material_candidate_allowed_row_count"] == 1
    first = material["question_observation_rows"][0]
    assert first["p8_material_candidate_requested"] is True
    assert first["p8_material_candidate_allowed"] is True
    assert first["p8_material_candidate_safe_for_handoff"] is True
    assert first["plan_candidate_flags"]["plus_single_question_candidate_later"] is True
    assert first["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["question_api_implemented"] is False
    assert material["question_db_schema_implemented"] is False
    assert material["question_rn_ui_implemented"] is False
    assert material["p8_start_allowed"] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


def test_r54_ev12_blocked_when_ev11_not_ready_and_does_not_materialize_question_rows() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    ev09 = _ev09_ready(rows)
    ev10 = ev.build_p7_r54_ev10_rating_row_normalization(sanitized_review_result_row_intake=ev09)
    assert ev10["rating_row_normalization_status"] == ev.P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF
    ev11 = ev.build_p7_r54_ev11_blocker_ingestion(rating_row_normalization=ev10)
    assert ev11["blocker_ingestion_status"] == ev.P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF

    material = ev.build_p7_r54_ev12_question_need_observation_row_normalization(
        blocker_ingestion=ev11,
        rating_row_normalization=ev10,
        sanitized_review_result_row_intake=ev09,
    )

    assert material["question_observation_normalization_status"] == ev.P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF
    assert material["question_observation_rows"] == []
    assert material["question_observation_row_count"] == 0
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["rating_question_consistency_guard_allowed_next"] is False
    assert material["next_required_step"] == ev.P7_R54_EV12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "blocker_ingestion_not_ready_for_question_need_observation_rows" in material["execution_blocker_ids"]
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev13_ready_passes_clean_rating_question_consistency_guard() -> None:
    _, ev10, _, ev12 = _ev12_ready()
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )

    assert material["schema_version"] == ev.P7_R54_EV13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV13_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV13_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV13_STEP_REF
    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF
    assert material["rating_question_consistency_guard_ref"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_REF
    assert material["rating_question_consistency_guard_policy_ref"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_POLICY_REF
    assert material["ev12_consistency_guard_allowed_next"] is True
    assert material["ev12_next_required_step"] == ev.P7_R54_EV13_STEP_REF
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["rating_question_case_ref_sets_match"] is True
    assert material["all_required_rating_and_question_rows_present"] is True
    assert material["rating_question_consistency_issue_rows"] == []
    assert material["consistency_issue_count"] == 0
    assert material["ready_for_pause_abort_expiration_protocol"] is True
    assert material["p5_confirmed_candidate_blocked_by_consistency_issues"] is False
    assert material["p5_decision_candidate_not_materialized_here"] is True
    assert material["p8_material_candidates_do_not_hide_p5_repair_here"] is True
    assert material["p5_surface_repair_not_promoted_to_p8_material"] is True
    assert material["not_question_repair_not_promoted_to_p8_material"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV14_NEXT_REQUIRED_STEP_REF
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        if key in {"actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}:
            assert material[key] is True
        else:
            assert material[key] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


def test_r54_ev13_blocks_red_or_repair_required_with_no_question_needed() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["verdict"] = "RED"
    rows[0]["sanitized_reason_ids"] = ["fixture_red_readfeel_reason"]
    rows[0]["readfeel_blocker_ids"] = ["p5_history_creepy_or_surveillance_feeling"]
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    rows[0]["question_need_primary_class"] = "no_question_needed_emlis_can_observe"
    _, ev10, _, ev12 = _ev12_ready(rows)
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )

    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert material["red_or_repair_with_no_question_needed_count"] == 1
    assert material["repair_required_with_p8_material_candidate_count"] == 0
    assert material["consistency_issue_count"] == 1
    assert material["rating_question_consistency_issue_rows"][0]["issue_id"] == "r54_ev13_red_or_repair_with_no_question_needed_observation"
    assert material["ready_for_pause_abort_expiration_protocol"] is False
    assert material["next_required_step"] == ev.P7_R54_EV13_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


def test_r54_ev13_blocks_p5_surface_repair_when_promoted_to_p8_material_candidate() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["verdict"] = "REPAIR_REQUIRED"
    rows[0]["sanitized_reason_ids"] = ["fixture_repair_required_reason"]
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["question_need_primary_class"] = "plus_single_question_candidate_later"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    rows[0]["plan_candidate_flags"] = {
        "plus_single_question_candidate_later": True,
        "premium_deep_dive_candidate_later": False,
        "p8_design_material_candidate": True,
        "p8_implementation_spec_finalized_here": False,
    }
    _, ev10, _, ev12 = _ev12_ready(rows)
    first_question_row = ev12["question_observation_rows"][0]
    assert first_question_row["p8_material_candidate_requested"] is True
    assert first_question_row["p8_material_candidate_allowed"] is False
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )

    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert material["repair_required_with_p8_material_candidate_count"] == 1
    assert material["consistency_issue_count"] == 1
    assert material["rating_question_consistency_issue_rows"][0]["issue_id"] == "r54_ev13_repair_required_with_p8_material_candidate"
    assert material["p5_surface_repair_not_promoted_to_p8_material"] is False
    assert material["p8_material_candidates_do_not_hide_p5_repair_here"] is True
    assert material["p8_start_allowed"] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


def test_r54_ev13_blocks_pass_with_not_question_repair_required() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["one_question_fit_ref"] = "repair_required_not_question"
    rows[0]["repair_required_refs"] = ["no_repair_required"]
    _, ev10, _, ev12 = _ev12_ready(rows)
    assert ev12["question_observation_rows"][0]["not_question_repair_required"] is True
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )

    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert material["pass_with_not_question_repair_required_count"] == 1
    assert material["consistency_issue_count"] == 1
    assert material["rating_question_consistency_issue_rows"][0]["issue_id"] == "r54_ev13_pass_with_not_question_repair_required"
    assert material["not_question_repair_not_promoted_to_p8_material"] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


def test_r54_ev13_blocks_insufficient_material_with_pass() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["question_need_primary_class"] = "insufficient_material_execution_blocker"
    rows[0]["one_question_fit_ref"] = "insufficient_material"
    rows[0]["ambiguity_kind_refs"] = ["low_information_current_input"]
    _, ev10, _, ev12 = _ev12_ready(rows)
    assert ev12["question_observation_rows"][0]["insufficient_material_execution_blocker"] is True
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )

    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert material["insufficient_material_with_pass_or_no_execution_blocker_count"] == 1
    assert material["consistency_issue_count"] == 1
    assert material["rating_question_consistency_issue_rows"][0]["issue_id"] == "r54_ev13_insufficient_material_with_pass_or_no_execution_blocker"
    assert material["next_required_step"] == ev.P7_R54_EV13_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


def test_r54_ev13_allows_insufficient_material_when_not_reviewable_execution_blocker_exists() -> None:
    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["verdict"] = "NOT_REVIEWABLE"
    rows[0]["sanitized_reason_ids"] = ["fixture_execution_blocker_reason"]
    rows[0]["execution_blocker_ids"] = ["reviewer_not_assigned"]
    rows[0]["question_need_primary_class"] = "insufficient_material_execution_blocker"
    rows[0]["one_question_fit_ref"] = "insufficient_material"
    rows[0]["ambiguity_kind_refs"] = ["low_information_current_input"]
    _, ev10, _, ev12 = _ev12_ready(rows)
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )

    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF
    assert material["insufficient_material_with_pass_or_no_execution_blocker_count"] == 0
    assert material["consistency_issue_count"] == 0
    assert material["ready_for_pause_abort_expiration_protocol"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    _assert_body_free_no_promotion(material, allow_rating_rows=True, allow_blocker_rows=True, allow_question_rows=True)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op14_current_refs_are_historical_here", False),
        ("existing_op14_reused_as_actual_question_observation_basis", True),
        ("existing_op14_reused_as_actual_normalization_basis", True),
        ("existing_op14_structural_contract_reused", False),
        ("required_case_count", 23),
        ("question_observation_normalization_status", ev.P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF),
        ("question_observation_row_count", 23),
        ("question_observation_row_refs_unique", False),
        ("case_ref_ids_unique", False),
        ("row_case_ref_sets_match_review_intake", False),
        ("row_case_ref_sets_match_rating_rows", False),
        ("all_required_question_need_observation_rows_present", False),
        ("primary_class_ambiguity_one_question_fit_are_canonical_refs", False),
        ("question_text_absent_for_all_rows", False),
        ("draft_question_text_absent_for_all_rows", False),
        ("actual_question_need_observation_rows_materialized_here", False),
        ("actual_review_evidence_complete", True),
        ("disposal_verified", True),
        ("rating_question_consistency_guard_allowed_next", False),
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
def test_r54_ev12_rejects_question_observation_boundary_mutations(key: str, value: object) -> None:
    _, _, _, material = _ev12_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev12_question_need_observation_row_normalization_contract(material)


def test_r54_ev12_rejects_old_refs_or_body_leak_keys() -> None:
    _, _, _, material = _ev12_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev12_question_need_observation_row_normalization_contract(material)

    _, _, _, material = _ev12_ready()
    material["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev12_question_need_observation_row_normalization_contract(material)

    _, _, _, material = _ev12_ready()
    material["question_observation_rows"][0]["question_text"] = "question text must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev12_question_need_observation_row_normalization_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op15_current_refs_are_historical_here", False),
        ("existing_op15_reused_as_actual_consistency_guard_basis", True),
        ("existing_op15_structural_contract_reused", False),
        ("required_case_count", 23),
        ("rating_question_consistency_guard_status", ev.P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF),
        ("rating_row_count", 23),
        ("question_observation_row_count", 23),
        ("rating_question_case_ref_sets_match", False),
        ("all_required_rating_and_question_rows_present", False),
        ("consistency_issue_count", 1),
        ("p5_decision_candidate_not_materialized_here", False),
        ("p8_material_candidates_do_not_hide_p5_repair_here", False),
        ("p5_surface_repair_not_promoted_to_p8_material", False),
        ("not_question_repair_not_promoted_to_p8_material", False),
        ("ready_for_pause_abort_expiration_protocol", False),
        ("actual_question_need_observation_rows_materialized_here", False),
        ("actual_review_evidence_complete", True),
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
def test_r54_ev13_rejects_consistency_guard_boundary_mutations(key: str, value: object) -> None:
    _, ev10, _, ev12 = _ev12_ready()
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev13_rating_question_consistency_guard_contract(material)


def test_r54_ev13_rejects_old_refs_or_question_text_leak_keys() -> None:
    _, ev10, _, ev12 = _ev12_ready()
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev13_rating_question_consistency_guard_contract(material)

    _, ev10, _, ev12 = _ev12_ready()
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )
    material["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev13_rating_question_consistency_guard_contract(material)

    rows = _selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["verdict"] = "RED"
    rows[0]["sanitized_reason_ids"] = ["fixture_red_readfeel_reason"]
    rows[0]["readfeel_blocker_ids"] = ["p5_history_creepy_or_surveillance_feeling"]
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    _, ev10, _, ev12 = _ev12_ready(rows)
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )
    material["rating_question_consistency_issue_rows"][0]["question_text"] = "question text must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev13_rating_question_consistency_guard_contract(material)
