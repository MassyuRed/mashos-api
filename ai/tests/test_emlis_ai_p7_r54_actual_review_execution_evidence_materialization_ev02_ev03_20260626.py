# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
from emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization import (
    P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF,
    P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R55_DEFAULT_DECISION_STATUS_REF,
    P7_R55_DEFAULT_MISSING_EVIDENCE_REFS,
    P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF,
    P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF,
    P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
    P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
    P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
    P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
    P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF,
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
    '"existing_helper_refs_can_be_used_for_actual_review_basis": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"actual_review_evidence_complete": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_ev00() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev00_scope_no_touch_boundary_confirmation()
    assert ev.assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(material) is True
    return (material,)


def _ev00() -> dict[str, object]:
    return deepcopy(_cached_ev00()[0])


@lru_cache(maxsize=1)
def _cached_ev01() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev01_existing_helper_capability_inspection(
        scope_no_touch_boundary_confirmation=_ev00(),
    )
    assert ev.assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material) is True
    return (material,)


def _ev01() -> dict[str, object]:
    return deepcopy(_cached_ev01()[0])


@lru_cache(maxsize=1)
def _cached_ev02() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev02_operation_current_refs_20260626_refreeze(
        existing_helper_capability_inspection=_ev01(),
    )
    assert ev.assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(material) is True
    return (material,)


def _ev02() -> dict[str, object]:
    return deepcopy(_cached_ev02()[0])


@lru_cache(maxsize=1)
def _cached_ev03() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev03_r55_hold_intake_refreeze(
        operation_current_refs_refreeze=_ev02(),
    )
    assert ev.assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material) is True
    return (material,)


def _ev03() -> dict[str, object]:
    return deepcopy(_cached_ev03()[0])


def test_r54_ev02_refreezes_20260626_operation_current_refs_without_rewriting_existing_helper() -> None:
    material = _ev02()

    assert material["schema_version"] == ev.P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["step"] == ev.P7_R54_EV_STEP
    assert material["scope"] == ev.P7_R54_EV_SCOPE
    assert material["policy_section"] == ev.P7_R54_EV02_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV02_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["ev01_schema_version"] == ev.P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION
    assert material["ev01_next_required_step"] == ev.P7_R54_EV02_STEP_REF
    assert material["ev01_thin_boundary_layer_required"] is True
    assert material["current_refs_refreeze_status_ref"] == ev.P7_R54_EV02_CURRENT_REFS_REFREEZE_STATUS_REF

    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs"]["premise_zip_ref"] == "Cocolon_前提資料(256).zip"
    assert material["operation_current_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(81).zip"
    assert material["operation_current_refs"]["rn_zip_ref"] == "Cocolon(254).zip"
    assert material["operation_current_refs"]["backend_zip_ref"] == "mashos-api(167).zip"
    assert tuple(material["operation_current_ref_keys"]) == tuple(ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.keys())
    assert material["all_required_operation_current_refs_present"] is True
    assert material["operation_current_refs_match_20260626_snapshot"] is True
    assert material["actual_review_basis_ref"] == ev.P7_R54_EV_ACTUAL_REVIEW_BASIS_REF
    assert material["actual_review_basis_allowed"] == ev.P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["operation_current_refs_used_as_actual_review_basis"] is True

    assert material["historical_helper_refs_separated"] is True
    assert material["historical_helper_refs_used_as_actual_review_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_review_basis"] is False
    assert material["existing_helper_module_ref"] == r54op.__name__
    assert material["existing_helper_schema_step_ref"] == r54op.P7_R54_OPERATION_REENTRY_STEP
    assert material["existing_helper_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_helper_current_refs"]["premise_zip_ref"] == "Cocolon_前提資料(254).zip"
    assert material["existing_helper_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["existing_helper_current_refs_are_historical_here"] is True
    assert material["existing_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["existing_helper_refs_can_be_used_for_actual_review_basis"] is False
    assert material["existing_helper_current_refs_match_20260626_snapshot"] is False
    assert set(material["differing_operation_current_ref_keys"]) == set(ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.keys())
    assert material["differing_operation_current_ref_key_count"] == len(ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS)
    assert "backend_zip_ref" in material["differing_operation_current_ref_keys"]

    assert material["current_refs_override_uses_thin_20260626_boundary_layer"] is True
    assert material["existing_op01_override_not_used_as_actual_review_basis"] is True
    assert material["downstream_20260625_constant_not_rewritten"] is True
    assert material["new_full_operation_helper_required"] is False
    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV03_STEP_REF

    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("ev01_thin_boundary_layer_required", False),
        ("all_required_operation_current_refs_present", False),
        ("operation_current_refs_match_20260626_snapshot", False),
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("historical_helper_refs_separated", False),
        ("historical_helper_refs_used_as_actual_review_basis", True),
        ("old_helper_refs_allowed_as_actual_review_basis", True),
        ("existing_helper_current_refs_are_historical_here", False),
        ("existing_helper_refs_can_be_used_for_actual_review_basis", True),
        ("existing_helper_current_refs_match_20260626_snapshot", True),
        ("current_refs_override_uses_thin_20260626_boundary_layer", False),
        ("existing_op01_override_not_used_as_actual_review_basis", False),
        ("downstream_20260625_constant_not_rewritten", False),
        ("new_full_operation_helper_required", True),
        ("body_full_generation_blocked_until_later_preflight", False),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev02_rejects_refreeze_no_touch_actual_review_p8_release_or_body_boundary_mutation(key: str, value: object) -> None:
    material = _ev02()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(material)


def test_r54_ev02_rejects_old_or_tampered_current_refs_as_actual_review_basis() -> None:
    material = _ev02()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(material)

    material = _ev02()
    material["operation_current_refs"] = dict(ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS)
    material["operation_current_refs"]["backend_zip_ref"] = "mashos-api(999).zip"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(material)

    material = _ev02()
    material["differing_operation_current_ref_keys"] = ["roadmap_ref"]
    material["differing_operation_current_ref_key_count"] = 1
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(material)


def test_r54_ev03_reintakes_r55_hold_without_mixing_r55_refs_into_20260626_actual_review_basis() -> None:
    material = _ev03()

    assert material["schema_version"] == ev.P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["step"] == ev.P7_R54_EV_STEP
    assert material["scope"] == ev.P7_R54_EV_SCOPE
    assert material["policy_section"] == ev.P7_R54_EV03_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV03_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["ev02_schema_version"] == ev.P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION
    assert material["ev02_next_required_step"] == ev.P7_R54_EV03_STEP_REF
    assert material["ev02_current_refs_refrozen"] is True
    assert material["r55_hold_intake_status_ref"] == ev.P7_R54_EV03_R55_HOLD_INTAKE_STATUS_REF

    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs"]["backend_zip_ref"] == "mashos-api(167).zip"
    assert material["actual_review_basis_ref"] == ev.P7_R54_EV_ACTUAL_REVIEW_BASIS_REF
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["operation_current_refs_used_as_actual_review_basis"] is True

    assert material["r55_decision_material_schema_version"] == P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION
    assert material["r55_current_received_snapshot_refs"] == P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["r55_current_received_snapshot_refs"]["backend_zip_ref"] == "mashos-api(163).zip"
    assert material["r55_current_refs_are_historical_hold_material_here"] is True
    assert material["r55_current_refs_used_as_actual_review_basis"] is False
    assert material["r55_decision_ref"] == P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF
    assert material["r55_decision_status"] == P7_R55_DEFAULT_DECISION_STATUS_REF
    assert material["r55_next_required_step"] == P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF
    assert material["r55_existing_r52_decision_equivalent"] == P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF
    assert material["r55_actual_review_evidence_gap_status_ref"] == P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF
    assert material["r55_actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["required_case_count"] == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT == 24
    assert material["rating_row_count_before_review"] == 0
    assert material["question_observation_row_count_before_review"] == 0
    assert material["disposal_verified_before_review"] is False
    assert tuple(material["missing_evidence_refs"]) == P7_R55_DEFAULT_MISSING_EVIDENCE_REFS
    assert material["missing_evidence_ref_count"] == len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS)
    assert material["r54_review_operation_state_ref"] == P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF
    assert material["p5_decision_status_ref"] == P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF
    assert material["p5_decision_candidate_ref"] == P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF
    assert material["p6_hold"] is True
    assert material["p8_hold"] is True
    assert material["release_hold"] is True
    assert material["r54_actual_local_only_human_review_operation_required_before_r52_reintake"] is True
    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV04_NEXT_REQUIRED_STEP_REF

    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("ev02_current_refs_refrozen", False),
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("r55_current_refs_are_historical_hold_material_here", False),
        ("r55_current_refs_used_as_actual_review_basis", True),
        ("r55_actual_review_evidence_complete", True),
        ("actual_review_evidence_complete", True),
        ("required_case_count", 23),
        ("rating_row_count_before_review", 1),
        ("question_observation_row_count_before_review", 1),
        ("disposal_verified_before_review", True),
        ("p6_hold", False),
        ("p8_hold", False),
        ("release_hold", False),
        ("r54_actual_local_only_human_review_operation_required_before_r52_reintake", False),
        ("body_full_generation_blocked_until_later_preflight", False),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev03_rejects_r55_hold_no_touch_actual_review_p8_release_or_body_boundary_mutation(key: str, value: object) -> None:
    material = _ev03()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material)


def test_r54_ev03_rejects_using_r55_or_old_refs_as_20260626_actual_review_basis() -> None:
    material = _ev03()
    material["operation_current_refs"] = dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material)

    material = _ev03()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material)

    material = _ev03()
    material["r55_decision_ref"] = "R55_FAKE_P8_START"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material)

    material = _ev03()
    material["missing_evidence_refs"] = []
    material["missing_evidence_ref_count"] = 0
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material)
