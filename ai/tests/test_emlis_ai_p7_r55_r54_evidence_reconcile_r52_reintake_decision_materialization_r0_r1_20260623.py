# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
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
    '"history_body":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"question_body":',
    '"answer_text":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"command_full_output":',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_final": true',
    '"actual_review_evidence_complete": true',
    '"actual_review_evidence_claimed": true',
    '"question_implementation_started_here": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"api_db_rn_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"api_route_changed_here": true',
    '"db_schema_changed_here": true',
    '"rn_visible_contract_changed_here": true',
    '"public_response_top_level_key_added_here": true',
    '"gate_threshold_changed_here": true',
    '"actual_human_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"prior_helper_refs_used_as_actual_review_basis": true',
    '"used_as_actual_review_basis": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_r55_r0() -> tuple[dict[str, object]]:
    refreeze = r55.build_p7_r55_current_received_snapshot_refreeze()
    assert r55.assert_p7_r55_current_received_snapshot_refreeze_contract(refreeze) is True
    return (refreeze,)


def _r55_r0() -> dict[str, object]:
    return deepcopy(_cached_r55_r0()[0])


@lru_cache(maxsize=1)
def _cached_r55_r1() -> tuple[dict[str, object]]:
    reconcile = r55.build_p7_r55_prior_helper_source_reconcile_bodyfree(
        current_received_snapshot_refreeze=_r55_r0(),
    )
    assert r55.assert_p7_r55_prior_helper_source_reconcile_bodyfree_contract(reconcile) is True
    return (reconcile,)


def _r55_r1() -> dict[str, object]:
    return deepcopy(_cached_r55_r1()[0])


def test_r55_r0_refreezes_current_received_snapshot_without_git_or_runtime_changes() -> None:
    refreeze = _r55_r0()

    assert refreeze["schema_version"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert set(refreeze) == set(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS)
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == r55.P7_R55_STEP
    assert refreeze["scope"] == r55.P7_R55_SCOPE
    assert refreeze["policy_section"] == "R55-0_scope_current_received_snapshot_refreeze"
    assert refreeze["source_mode"] == "local_snapshot"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True

    current_refs = refreeze["current_received_snapshot_refs"]
    assert current_refs == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert current_refs["premise_zip_ref"] == "Cocolon_前提資料(248).zip"
    assert current_refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(77).zip"
    assert current_refs["rn_zip_ref"] == "Cocolon(250).zip"
    assert current_refs["backend_zip_ref"] == "mashos-api(163).zip"
    assert current_refs["roadmap_ref"].endswith("20260619(9).md")
    assert current_refs["pre_design_memo_ref"].endswith("PreDesignMemo_20260623.md")
    assert current_refs["detailed_design_ref"].endswith("ImplementationOrder_20260623.md")

    assert refreeze["current_received_snapshot_ref_count"] == 7
    assert refreeze["current_snapshot_refrozen_here"] is True
    assert refreeze["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"
    assert refreeze["actual_review_basis_allowed"] == "current_received_snapshot_only"
    assert refreeze["prior_helper_refs_used_as_actual_review_basis"] is False
    assert refreeze["current_received_snapshot_used_as_actual_review_basis"] is True
    assert refreeze["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert refreeze["r55_1_prior_helper_source_reconciled"] is False
    assert tuple(refreeze["implemented_steps"]) == r55.P7_R55_R0_IMPLEMENTED_STEPS
    assert tuple(refreeze["not_yet_implemented_steps"]) == r55.P7_R55_R0_NOT_YET_IMPLEMENTED_STEPS
    assert refreeze["next_required_step"] == r55.P7_R55_R0_NEXT_REQUIRED_STEP_REF

    assert refreeze["p5_human_blind_qa_confirmed"] is False
    assert refreeze["p5_human_blind_qa_confirmed_candidate"] is False
    assert refreeze["p5_human_blind_qa_confirmed_final"] is False
    assert refreeze["actual_review_evidence_complete"] is False
    assert refreeze["p6_limited_human_readfeel_start_allowed"] is False
    assert refreeze["p8_question_design_material_candidate"] is False
    assert refreeze["p8_start_allowed"] is False
    assert refreeze["p7_complete"] is False
    assert refreeze["release_allowed"] is False
    assert refreeze["api_db_rn_response_key_changed_here"] is False
    assert refreeze["runtime_changed_here"] is False
    assert refreeze["question_implementation_started_here"] is False

    _assert_body_free_no_promotion(refreeze)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("current_snapshot_refrozen_here", False),
        ("prior_helper_refs_used_as_actual_review_basis", True),
        ("current_received_snapshot_used_as_actual_review_basis", False),
        ("r55_0_scope_current_received_snapshot_refrozen", False),
        ("r55_1_prior_helper_source_reconciled", True),
        ("actual_review_evidence_complete", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("question_implementation_started_here", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
    ],
)
def test_r55_r0_rejects_git_claim_old_basis_actual_review_or_p6_p8_release_promotion(key: str, value: object) -> None:
    material = _r55_r0()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_current_received_snapshot_refreeze_contract(material)


def test_r55_r0_rejects_prior_helper_refs_relabelled_as_current_snapshot() -> None:
    with pytest.raises(ValueError):
        r55.build_p7_r55_current_received_snapshot_refreeze(
            current_received_snapshot_refs=r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS,
        )

    material = _r55_r0()
    material["current_received_snapshot_refs"] = dict(r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        r55.assert_p7_r55_current_received_snapshot_refreeze_contract(material)


def test_r55_r1_reconciles_r52_r53_r54_helper_refs_as_historical_regression_context_only() -> None:
    reconcile = _r55_r1()

    assert reconcile["schema_version"] == r55.P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_SCHEMA_VERSION
    assert set(reconcile) == set(r55.P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_REQUIRED_FIELD_REFS)
    assert reconcile["phase"].startswith("P7_")
    assert reconcile["step"] == r55.P7_R55_STEP
    assert reconcile["scope"] == r55.P7_R55_SCOPE
    assert reconcile["policy_section"] == "R55-1_prior_helper_source_reconcile"
    assert reconcile["source_mode"] == "local_snapshot"
    assert reconcile["git_connection_required"] is False
    assert reconcile["git_checked"] is False
    assert reconcile["body_free"] is True
    assert reconcile["r0_refreeze_schema_version"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert reconcile["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert reconcile["current_received_snapshot_ref_count"] == 7
    assert reconcile["actual_review_basis_ref"] == "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"
    assert reconcile["actual_review_basis_allowed"] == "current_received_snapshot_only"

    assert reconcile["prior_helper_ref_keys"] == ["R52", "R53", "R54"]
    assert reconcile["prior_helper_source_row_count"] == 3
    assert reconcile["all_prior_helper_refs_classified"] is True
    assert reconcile["prior_helper_refs_used_as_actual_review_basis"] is False
    assert reconcile["prior_helper_refs_used_as_regression_context_only"] is True
    assert reconcile["current_received_snapshot_used_as_actual_review_basis"] is True
    assert reconcile["r55_0_scope_current_received_snapshot_refrozen"] is True
    assert reconcile["r55_1_prior_helper_source_reconciled"] is True
    assert tuple(reconcile["implemented_steps"]) == r55.P7_R55_IMPLEMENTED_STEPS
    assert tuple(reconcile["not_yet_implemented_steps"]) == r55.P7_R55_NOT_YET_IMPLEMENTED_STEPS
    assert reconcile["next_required_step"] == r55.P7_R55_R1_NEXT_REQUIRED_STEP_REF

    rows = reconcile["prior_helper_source_rows"]
    assert [row["helper_ref"] for row in rows] == ["R52", "R53", "R54"]
    expected_refs = {
        "R52": r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS,
        "R53": r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS,
        "R54": r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS,
    }
    expected_step_refs = {
        "R52": r52.P7_R52_STEP,
        "R53": r53.P7_R53_STEP,
        "R54": r54.P7_R54_STEP,
    }
    for row in rows:
        assert set(row) == set(r55.P7_R55_PRIOR_HELPER_SOURCE_ROW_REQUIRED_FIELD_REFS)
        assert r55.assert_p7_r55_prior_helper_source_row_contract(row) is True
        helper_ref = row["helper_ref"]
        assert row["schema_version"] == r55.P7_R55_PRIOR_HELPER_SOURCE_ROW_SCHEMA_VERSION
        assert row["helper_step_ref"] == expected_step_refs[helper_ref]
        assert row["helper_snapshot_refs"] == expected_refs[helper_ref]
        assert row["helper_snapshot_ref_count"] == 7
        assert row["current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
        assert row["current_received_snapshot_ref_count"] == 7
        assert row["refs_match_current_received_snapshot"] is False
        assert row["comparison_status_ref"] == "OLDER_THAN_R55_CURRENT_RECEIVED_SNAPSHOT"
        assert row["classification_ref"] == "historical_regression_context"
        assert row["used_as_actual_review_basis"] is False
        assert row["used_as_regression_context_only"] is True
        assert row["current_snapshot_used_as_actual_review_basis"] is True
        assert row["body_free"] is True

    by_ref = {row["helper_ref"]: row for row in rows}
    assert by_ref["R52"]["helper_snapshot_refs"]["premise_zip_ref"] == "Cocolon_前提資料(243).zip"
    assert by_ref["R52"]["helper_snapshot_refs"]["backend_zip_ref"] == "mashos-api(160).zip"
    assert by_ref["R52"]["helper_snapshot_refs"]["roadmap_ref"].endswith("20260619(4).md")
    assert by_ref["R53"]["helper_snapshot_refs"]["premise_zip_ref"] == "Cocolon_前提資料(245).zip"
    assert by_ref["R53"]["helper_snapshot_refs"]["backend_zip_ref"] == "mashos-api(161).zip"
    assert by_ref["R53"]["helper_snapshot_refs"]["roadmap_ref"].endswith("20260619(6).md")
    assert by_ref["R54"]["helper_snapshot_refs"]["premise_zip_ref"] == "Cocolon_前提資料(246).zip"
    assert by_ref["R54"]["helper_snapshot_refs"]["backend_zip_ref"] == "mashos-api(162).zip"
    assert by_ref["R54"]["helper_snapshot_refs"]["roadmap_ref"].endswith("20260619(8).md")

    assert reconcile["p5_human_blind_qa_confirmed_final"] is False
    assert reconcile["p6_limited_human_readfeel_start_allowed"] is False
    assert reconcile["p8_start_allowed"] is False
    assert reconcile["p7_complete"] is False
    assert reconcile["release_allowed"] is False

    _assert_body_free_no_promotion(reconcile)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("all_prior_helper_refs_classified", False),
        ("prior_helper_refs_used_as_actual_review_basis", True),
        ("prior_helper_refs_used_as_regression_context_only", False),
        ("current_received_snapshot_used_as_actual_review_basis", False),
        ("r55_0_scope_current_received_snapshot_refrozen", False),
        ("r55_1_prior_helper_source_reconciled", False),
        ("actual_review_evidence_complete", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("question_trigger_logic_implemented", True),
        ("api_db_rn_response_key_changed_here", True),
    ],
)
def test_r55_r1_rejects_old_basis_unclassified_refs_or_promotion_mutation(key: str, value: object) -> None:
    material = _r55_r1()
    material[key] = value
    with pytest.raises(ValueError):
        r55.assert_p7_r55_prior_helper_source_reconcile_bodyfree_contract(material)


@pytest.mark.parametrize(
    "helper_ref,patch",
    [
        ("R52", {"used_as_actual_review_basis": True}),
        ("R53", {"used_as_regression_context_only": False}),
        ("R54", {"current_snapshot_used_as_actual_review_basis": False}),
        ("R52", {"classification_ref": "current_work_basis"}),
        ("R53", {"refs_match_current_received_snapshot": True}),
        ("R54", {"comparison_status_ref": "CURRENT_WORK_BASIS"}),
    ],
)
def test_r55_r1_rejects_prior_helper_row_promotion_or_misclassification(helper_ref: str, patch: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        r55.build_p7_r55_prior_helper_source_reconcile_bodyfree(
            current_received_snapshot_refreeze=_r55_r0(),
            prior_helper_row_overrides={helper_ref: patch},
        )


def test_r55_r1_rejects_forbidden_payload_key_inside_reconcile_material() -> None:
    material = _r55_r1()
    material["prior_helper_source_rows"][0]["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        r55.assert_p7_r55_prior_helper_source_reconcile_bodyfree_contract(material)
