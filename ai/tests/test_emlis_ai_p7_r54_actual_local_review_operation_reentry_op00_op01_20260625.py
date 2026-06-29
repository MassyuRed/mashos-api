# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


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
    '"question_text":',
    '"draft_question_text":',
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
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"historical_helper_refs_can_be_used_for_actual_review_basis": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_op00() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op00_scope_no_touch_boundary_freeze()
    assert op.assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract(material) is True
    return (material,)


def _op00() -> dict[str, object]:
    return deepcopy(_cached_op00()[0])


@lru_cache(maxsize=1)
def _cached_op01() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op01_operation_current_snapshot_refs_refreeze(
        scope_no_touch_boundary_freeze=_op00(),
    )
    assert op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material) is True
    return (material,)


def _op01() -> dict[str, object]:
    return deepcopy(_cached_op01()[0])


def test_r54_op00_freezes_scope_and_no_touch_boundary_without_starting_p8_or_review() -> None:
    material = _op00()

    assert material["schema_version"] == op.P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["step"] == op.P7_R54_OPERATION_REENTRY_STEP
    assert material["scope"] == op.P7_R54_OPERATION_REENTRY_SCOPE
    assert material["policy_section"] == op.P7_R54_OP00_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP00_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["allowed_operation_step_refs"] == [op.P7_R54_OP00_STEP_REF, op.P7_R54_OP01_STEP_REF]
    assert material["no_touch_boundary_frozen"] is True
    assert material["operation_current_refs_required_before_actual_review"] is True
    assert material["historical_helper_refs_must_be_separated"] is True
    assert material["body_full_generation_blocked_until_preflight"] is True
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["actual_review_basis_ref"] == "operation_current_refs_only"
    assert material["actual_review_basis_allowed"] == "current_ref_only"
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP01_STEP_REF

    assert material["api_changed"] is False
    assert material["db_changed"] is False
    assert material["rn_changed"] is False
    assert material["runtime_changed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False

    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("no_touch_boundary_frozen", False),
        ("operation_current_refs_required_before_actual_review", False),
        ("historical_helper_refs_must_be_separated", False),
        ("body_full_generation_blocked_until_preflight", False),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_implementation_started_here", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op00_rejects_contract_mutation_actual_review_p8_release_or_body_boundary_claims(key: str, value: object) -> None:
    material = _op00()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract(material)


def test_r54_op01_refreezes_operation_current_refs_and_separates_historical_helper_refs() -> None:
    material = _op01()

    assert material["schema_version"] == op.P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["step"] == op.P7_R54_OPERATION_REENTRY_STEP
    assert material["scope"] == op.P7_R54_OPERATION_REENTRY_SCOPE
    assert material["policy_section"] == op.P7_R54_OP01_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP01_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["op00_schema_version"] == op.P7_R54_OPERATION_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["op00_next_required_step"] == op.P7_R54_OP01_STEP_REF

    current_refs = material["operation_current_refs"]
    assert current_refs == op.P7_R54_OPERATION_CURRENT_REFS
    assert current_refs["premise_zip_ref"] == "Cocolon_前提資料(254).zip"
    assert current_refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(80).zip"
    assert current_refs["rn_zip_ref"] == "Cocolon(253).zip"
    assert current_refs["backend_zip_ref"] == "mashos-api(166).zip"
    assert current_refs["roadmap_ref"].endswith("20260619(13).md")
    assert current_refs["pre_design_memo_ref"].endswith("PreDesignMemo_20260625.md")
    assert current_refs["detailed_design_ref"].endswith("ImplementationOrder_20260625.md")
    assert material["operation_current_ref_count"] == len(op.P7_R54_OPERATION_CURRENT_REFS)
    assert material["actual_review_basis_ref"] == "operation_current_refs_only"
    assert material["actual_review_basis_allowed"] == "current_ref_only"
    assert material["operation_current_refs_are_actual_review_basis"] is True

    helper_refs = material["historical_helper_refs"]
    assert material["historical_helper_ref_groups"] == list(op.P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS)
    assert helper_refs["r54_helper_current_received_snapshot_refs"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert helper_refs["r55_helper_current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert helper_refs["r54_helper_current_received_snapshot_refs"]["backend_zip_ref"] == "mashos-api(162).zip"
    assert helper_refs["r55_helper_current_received_snapshot_refs"]["backend_zip_ref"] == "mashos-api(163).zip"
    assert material["historical_helper_refs_separated"] is True
    assert material["historical_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_helper_refs_can_be_used_for_actual_review_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_review_basis"] is False
    assert material["historical_helper_refs_used_as_actual_review_basis"] is False
    assert material["operation_current_refs_used_as_actual_review_basis"] is True
    assert material["source_delta_rows_required_next"] is True
    assert material["source_delta_rows_materialized_here"] is False

    assert tuple(material["implemented_steps"]) == op.P7_R54_OP01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP02_NEXT_REQUIRED_STEP_REF

    assert material["api_changed"] is False
    assert material["db_changed"] is False
    assert material["rn_changed"] is False
    assert material["runtime_changed"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False

    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("historical_helper_refs_separated", False),
        ("historical_helper_refs_can_be_used_for_helper_regression_only", False),
        ("historical_helper_refs_can_be_used_for_actual_review_basis", True),
        ("old_helper_refs_allowed_as_actual_review_basis", True),
        ("historical_helper_refs_used_as_actual_review_basis", True),
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("operation_current_refs_are_actual_review_basis", False),
        ("source_delta_rows_required_next", False),
        ("source_delta_rows_materialized_here", True),
        ("body_full_generation_blocked_until_preflight", False),
        ("human_review_completion_claim_blocked_here", False),
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
def test_r54_op01_rejects_old_helper_basis_actual_review_schema_p8_release_or_body_boundary_claims(key: str, value: object) -> None:
    material = _op01()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material)


def test_r54_op01_rejects_operation_current_refs_replaced_by_r54_or_r55_historical_refs() -> None:
    material = _op01()
    material["operation_current_refs"] = dict(r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material)

    material = _op01()
    material["operation_current_refs"] = dict(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material)


def test_r54_op01_rejects_historical_helper_refs_relabelled_or_removed() -> None:
    material = _op01()
    material["historical_helper_refs"]["r54_helper_current_received_snapshot_refs"] = dict(op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material)

    material = _op01()
    material["historical_helper_ref_groups"] = list(reversed(material["historical_helper_ref_groups"]))
    with pytest.raises(ValueError):
        op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material)

    material = _op01()
    del material["historical_helper_refs"]["r55_helper_current_received_snapshot_refs"]
    with pytest.raises(ValueError):
        op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material)


def test_r54_op01_rejects_current_refs_override_to_unknown_current_zip() -> None:
    with pytest.raises(ValueError):
        op.build_p7_r54_op01_operation_current_snapshot_refs_refreeze(
            scope_no_touch_boundary_freeze=_op00(),
            operation_current_refs={"backend_zip_ref": "mashos-api(999).zip"},
        )
