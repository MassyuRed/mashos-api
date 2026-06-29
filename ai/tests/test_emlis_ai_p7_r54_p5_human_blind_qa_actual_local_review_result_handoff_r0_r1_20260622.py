# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54


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
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"hold004_close_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"api_db_rn_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"old_refs_allowed_as_actual_review_basis": true',
    '"r53_old_refs_allowed_as_actual_review_basis": true',
    '"r53_source_refs_can_be_used_for_actual_review_basis": true',
    '"prior_ref_allowed_as_actual_review_basis": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_r54_r0() -> tuple[dict[str, object]]:
    refreeze = r54.build_p7_r54_current_received_snapshot_refreeze()
    assert r54.assert_p7_r54_current_received_snapshot_refreeze_contract(refreeze) is True
    return (refreeze,)


def _r54_r0() -> dict[str, object]:
    return deepcopy(_cached_r54_r0()[0])


@lru_cache(maxsize=1)
def _cached_r54_r1() -> tuple[dict[str, object]]:
    adoption = r54.build_p7_r54_r53_source_delta_and_override_adoption(
        current_received_snapshot_refreeze=_r54_r0(),
    )
    assert r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(adoption) is True
    return (adoption,)


def _r54_r1() -> dict[str, object]:
    return deepcopy(_cached_r54_r1()[0])


def test_r54_r0_refreezes_current_received_snapshot_and_keeps_r53_refs_historical() -> None:
    refreeze = _r54_r0()

    assert refreeze["schema_version"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert set(refreeze) == set(r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS)
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == r54.P7_R54_STEP
    assert refreeze["scope"] == r54.P7_R54_SCOPE
    assert refreeze["policy_section"] == "R54-0_scope_current_received_snapshot_refreeze"
    assert refreeze["source_mode"] == "local_snapshot"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True

    current_refs = refreeze["current_received_snapshot_refs"]
    r53_refs = refreeze["r53_source_snapshot_refs"]
    assert current_refs == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert r53_refs == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert current_refs["premise_zip_ref"] == "Cocolon_前提資料(246).zip"
    assert current_refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(76).zip"
    assert current_refs["rn_zip_ref"] == "Cocolon(249).zip"
    assert current_refs["backend_zip_ref"] == "mashos-api(162).zip"
    assert current_refs["roadmap_ref"].endswith("20260619(8).md")
    assert r53_refs["premise_zip_ref"] == "Cocolon_前提資料(245).zip"
    assert r53_refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(75).zip"
    assert r53_refs["rn_zip_ref"] == "Cocolon(248).zip"
    assert r53_refs["backend_zip_ref"] == "mashos-api(161).zip"
    assert r53_refs["roadmap_ref"].endswith("20260619(6).md")

    assert refreeze["current_received_snapshot_ref_count"] == len(r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS)
    assert refreeze["r53_source_snapshot_ref_count"] == len(r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS)
    assert refreeze["r53_refs_are_current_received_refs"] is False
    assert refreeze["old_refs_allowed_as_actual_review_basis"] is False
    assert refreeze["r53_source_refs_can_be_used_for_helper_regression_only"] is True
    assert refreeze["r53_source_refs_can_be_used_for_actual_review_basis"] is False
    assert refreeze["r54_current_snapshot_override_required"] is True
    assert refreeze["current_snapshot_can_override_r53_source_refs"] is True
    assert refreeze["actual_review_basis_ref"] == "r54_current_received_snapshot_refs"
    assert refreeze["actual_review_basis_allowed"] == "current_ref_only"
    assert refreeze["r54_0_scope_current_received_snapshot_refrozen"] is True
    assert refreeze["r54_1_r53_source_delta_current_snapshot_override_adopted"] is False
    assert tuple(refreeze["implemented_steps"]) == r54.P7_R54_R0_IMPLEMENTED_STEPS
    assert tuple(refreeze["not_yet_implemented_steps"]) == r54.P7_R54_R0_NOT_YET_IMPLEMENTED_STEPS
    assert refreeze["next_required_step"] == r54.P7_R54_R0_NEXT_REQUIRED_STEP_REF

    assert refreeze["p5_human_blind_qa_confirmed"] is False
    assert refreeze["p5_human_blind_qa_confirmed_candidate"] is False
    assert refreeze["p6_limited_human_readfeel_start_allowed"] is False
    assert refreeze["p8_question_design_material_candidate"] is False
    assert refreeze["p8_start_allowed"] is False
    assert refreeze["p7_complete"] is False
    assert refreeze["release_allowed"] is False
    assert refreeze["api_db_rn_response_key_changed_here"] is False
    assert refreeze["runtime_changed_here"] is False

    _assert_body_free_no_promotion(refreeze)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("r53_refs_are_current_received_refs", True),
        ("old_refs_allowed_as_actual_review_basis", True),
        ("r53_source_refs_can_be_used_for_helper_regression_only", False),
        ("r53_source_refs_can_be_used_for_actual_review_basis", True),
        ("r54_current_snapshot_override_required", False),
        ("current_snapshot_can_override_r53_source_refs", False),
        ("r54_0_scope_current_received_snapshot_refrozen", False),
        ("r54_1_r53_source_delta_current_snapshot_override_adopted", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
    ],
)
def test_r54_r0_rejects_git_claim_source_mix_actual_review_or_p6_p8_release_promotion(key: str, value: object) -> None:
    material = _r54_r0()
    material[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_current_received_snapshot_refreeze_contract(material)


def test_r54_r0_rejects_r53_historical_refs_relabelled_as_current_snapshot() -> None:
    with pytest.raises(ValueError):
        r54.build_p7_r54_current_received_snapshot_refreeze(
            current_received_snapshot_refs=r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS,
        )

    material = _r54_r0()
    material["r53_source_snapshot_refs"] = dict(r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        r54.assert_p7_r54_current_received_snapshot_refreeze_contract(material)


def test_r54_r1_adopts_current_snapshot_override_without_allowing_r53_refs_as_actual_review_basis() -> None:
    adoption = _r54_r1()

    assert adoption["schema_version"] == r54.P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_SCHEMA_VERSION
    assert set(adoption) == set(r54.P7_R54_R53_SOURCE_DELTA_CURRENT_SNAPSHOT_OVERRIDE_ADOPTION_REQUIRED_FIELD_REFS)
    assert adoption["phase"].startswith("P7_")
    assert adoption["step"] == r54.P7_R54_STEP
    assert adoption["scope"] == r54.P7_R54_SCOPE
    assert adoption["policy_section"] == "R54-1_r53_source_delta_current_snapshot_override_adoption"
    assert adoption["source_mode"] == "local_snapshot"
    assert adoption["git_connection_required"] is False
    assert adoption["git_checked"] is False
    assert adoption["r0_refreeze_schema_version"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION

    assert adoption["r53_step"] == r53.P7_R53_STEP
    assert adoption["r53_scope"] == r53.P7_R53_SCOPE
    assert adoption["r53_refreeze_schema_version"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert adoption["r53_source_delta_schema_version"] == r53.P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION
    assert adoption["current_received_snapshot_refs"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert adoption["r53_source_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert adoption["current_received_snapshot_refs"]["backend_zip_ref"] == "mashos-api(162).zip"
    assert adoption["r53_source_snapshot_refs"]["backend_zip_ref"] == "mashos-api(161).zip"
    assert adoption["r53_refs_are_current_received_refs"] is False
    assert adoption["r54_current_received_refs_frozen"] is True
    assert adoption["old_refs_allowed_as_actual_review_basis"] is False
    assert adoption["r53_old_refs_allowed_as_actual_review_basis"] is False
    assert adoption["r53_source_refs_can_be_used_for_helper_regression_only"] is True
    assert adoption["r53_source_refs_can_be_used_for_actual_review_basis"] is False
    assert adoption["r54_current_snapshot_override_required"] is True
    assert adoption["r54_current_snapshot_override_applied"] is True
    assert adoption["current_snapshot_can_override_r53_source_refs"] is True
    assert adoption["actual_review_basis_ref"] == "r54_current_received_snapshot_refs"
    assert adoption["actual_review_basis_allowed"] == "current_ref_only"
    assert adoption["r54_0_scope_current_received_snapshot_refrozen"] is True
    assert adoption["r54_1_r53_source_delta_current_snapshot_override_adopted"] is True
    assert tuple(adoption["implemented_steps"]) == r54.P7_R54_IMPLEMENTED_STEPS
    assert tuple(adoption["not_yet_implemented_steps"]) == r54.P7_R54_NOT_YET_IMPLEMENTED_STEPS
    assert adoption["next_required_step"] == r54.P7_R54_R1_NEXT_REQUIRED_STEP_REF

    rows = adoption["source_delta_rows"]
    expected_keys = list(r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS.keys())
    assert adoption["source_delta_ref_keys"] == expected_keys
    assert adoption["source_delta_row_count"] == len(expected_keys)
    assert [row["source_ref_key"] for row in rows] == expected_keys
    for row in rows:
        key = row["source_ref_key"]
        assert r54.assert_p7_r54_source_delta_row_contract(row) is True
        assert row["prior_snapshot_ref_group"] == "p7_r53_current_received_snapshot_refs"
        assert row["current_snapshot_ref_group"] == "p7_r54_current_received_snapshot_refs"
        assert row["prior_ref"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS[key]
        assert row["current_ref"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS[key]
        assert row["refs_match"] is False
        assert row["override_required"] is True
        assert row["override_applied_in_r54"] is True
        assert row["actual_review_basis_allowed"] == "current_ref_only"
        assert row["prior_ref_allowed_as_actual_review_basis"] is False
        assert row["prior_ref_regression_context_allowed"] is True
        assert row["body_free"] is True

    assert adoption["p5_human_blind_qa_confirmed"] is False
    assert adoption["p5_human_blind_qa_confirmed_candidate"] is False
    assert adoption["p6_limited_human_readfeel_candidate"] is False
    assert adoption["p6_limited_human_readfeel_start_allowed"] is False
    assert adoption["p8_question_design_material_candidate"] is False
    assert adoption["p8_start_allowed"] is False
    assert adoption["p7_complete"] is False
    assert adoption["release_allowed"] is False
    assert adoption["api_db_rn_response_key_changed_here"] is False
    assert adoption["runtime_changed_here"] is False

    _assert_body_free_no_promotion(adoption)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r53_refs_are_current_received_refs", True),
        ("r54_current_received_refs_frozen", False),
        ("old_refs_allowed_as_actual_review_basis", True),
        ("r53_old_refs_allowed_as_actual_review_basis", True),
        ("r53_source_refs_can_be_used_for_helper_regression_only", False),
        ("r53_source_refs_can_be_used_for_actual_review_basis", True),
        ("r54_current_snapshot_override_required", False),
        ("r54_current_snapshot_override_applied", False),
        ("current_snapshot_can_override_r53_source_refs", False),
        ("r54_0_scope_current_received_snapshot_refrozen", False),
        ("r54_1_r53_source_delta_current_snapshot_override_adopted", False),
        ("actual_manual_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("runtime_changed_here", True),
    ],
)
def test_r54_r1_rejects_source_relabelling_old_basis_actual_review_or_release_promotion(key: str, value: object) -> None:
    material = _r54_r1()
    material[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)


def test_r54_r1_rejects_current_refs_replaced_by_r53_historical_refs() -> None:
    material = _r54_r1()
    material["current_received_snapshot_refs"] = dict(r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)

    material = _r54_r1()
    material["r53_source_snapshot_refs"] = dict(r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)


def test_r54_r1_rejects_source_delta_rows_relabelled_as_current_or_actual_review_basis() -> None:
    material = _r54_r1()
    material["source_delta_rows"][0]["refs_match"] = True
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)

    material = _r54_r1()
    material["source_delta_rows"][0]["prior_ref_allowed_as_actual_review_basis"] = True
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)

    material = _r54_r1()
    material["source_delta_rows"][0]["actual_review_basis_allowed"] = "prior_ref_allowed"
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)

    material = _r54_r1()
    material["source_delta_rows"][0]["current_ref"] = material["source_delta_rows"][0]["prior_ref"]
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)


def test_r54_r1_rejects_source_delta_row_key_order_or_unknown_key_mutation() -> None:
    material = _r54_r1()
    material["source_delta_rows"] = list(reversed(material["source_delta_rows"]))
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)

    material = _r54_r1()
    material["source_delta_rows"][0]["source_ref_key"] = "unknown_ref"
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)

    material = _r54_r1()
    material["source_delta_ref_keys"][0] = "unknown_ref"
    with pytest.raises(ValueError):
        r54.assert_p7_r54_r53_source_delta_and_override_adoption_contract(material)
