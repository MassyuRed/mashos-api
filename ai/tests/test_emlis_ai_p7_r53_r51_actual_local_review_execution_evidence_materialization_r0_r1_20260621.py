# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53


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
    '"r51_old_refs_allowed_as_actual_review_basis": true',
    '"r52_old_refs_allowed_as_actual_review_basis": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_r53_r0() -> tuple[dict[str, object]]:
    refreeze = r53.build_p7_r53_current_received_snapshot_refreeze()
    assert r53.assert_p7_r53_current_received_snapshot_refreeze_contract(refreeze) is True
    return (refreeze,)


def _r53_r0() -> dict[str, object]:
    return deepcopy(_cached_r53_r0()[0])


@lru_cache(maxsize=1)
def _cached_r53_r1() -> tuple[dict[str, object]]:
    delta = r53.build_p7_r53_r51_r52_source_delta_freeze(
        current_received_snapshot_refreeze=_r53_r0(),
    )
    assert r53.assert_p7_r53_r51_r52_source_delta_freeze_contract(delta) is True
    return (delta,)


def _r53_r1() -> dict[str, object]:
    return deepcopy(_cached_r53_r1()[0])


def test_r53_r0_refreezes_current_received_snapshot_and_keeps_r51_r52_helper_refs_historical() -> None:
    refreeze = _r53_r0()

    assert refreeze["schema_version"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert set(refreeze) == set(r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS)
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == r53.P7_R53_STEP
    assert refreeze["scope"] == r53.P7_R53_SCOPE
    assert refreeze["policy_section"] == "R53-0_scope_current_received_snapshot_refreeze"
    assert refreeze["source_mode"] == "local_snapshot"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True

    current_refs = refreeze["current_received_snapshot_refs"]
    r51_refs = refreeze["r51_helper_source_snapshot_refs"]
    r52_refs = refreeze["r52_helper_current_received_snapshot_refs"]
    assert current_refs == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert r51_refs == r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert r52_refs == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert current_refs["premise_zip_ref"] == "Cocolon_前提資料(245).zip"
    assert current_refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(75).zip"
    assert current_refs["rn_zip_ref"] == "Cocolon(248).zip"
    assert current_refs["backend_zip_ref"] == "mashos-api(161).zip"
    assert current_refs["roadmap_ref"].endswith("20260619(6).md")
    assert r51_refs["premise_zip_ref"] == "Cocolon_前提資料(241).zip"
    assert r51_refs["backend_zip_ref"] == "mashos-api(159).zip"
    assert r52_refs["premise_zip_ref"] == "Cocolon_前提資料(243).zip"
    assert r52_refs["backend_zip_ref"] == "mashos-api(160).zip"
    assert refreeze["current_received_snapshot_ref_count"] == len(r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS)
    assert refreeze["r51_helper_source_snapshot_ref_count"] == len(r51.P7_R51_SOURCE_SNAPSHOT_REFS)
    assert refreeze["r52_helper_current_received_snapshot_ref_count"] == len(r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS)
    assert refreeze["r51_helper_refs_are_current_received_refs"] is False
    assert refreeze["r52_helper_refs_are_current_received_refs"] is False
    assert refreeze["old_refs_allowed_as_actual_review_basis"] is False
    assert refreeze["r51_builder_snapshot_override_required"] is True
    assert refreeze["current_snapshot_can_override_r51_builder_snapshot_refs"] is True
    assert refreeze["r53_0_scope_current_received_snapshot_refrozen"] is True
    assert refreeze["r53_1_r51_r52_helper_source_delta_frozen"] is False
    assert tuple(refreeze["implemented_steps"]) == r53.P7_R53_R0_IMPLEMENTED_STEPS
    assert tuple(refreeze["not_yet_implemented_steps"]) == r53.P7_R53_R0_NOT_YET_IMPLEMENTED_STEPS
    assert refreeze["next_required_step"] == r53.P7_R53_R0_NEXT_REQUIRED_STEP_REF

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
        ("r51_helper_refs_are_current_received_refs", True),
        ("r52_helper_refs_are_current_received_refs", True),
        ("old_refs_allowed_as_actual_review_basis", True),
        ("r51_builder_snapshot_override_required", False),
        ("current_snapshot_can_override_r51_builder_snapshot_refs", False),
        ("r53_0_scope_current_received_snapshot_refrozen", False),
        ("r53_1_r51_r52_helper_source_delta_frozen", True),
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
def test_r53_r0_rejects_git_claim_source_mix_actual_review_or_p6_p8_release_promotion(key: str, value: object) -> None:
    material = _r53_r0()
    material[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_current_received_snapshot_refreeze_contract(material)


def test_r53_r0_rejects_r51_or_r52_historical_refs_relabelled_as_current_snapshot() -> None:
    with pytest.raises(ValueError):
        r53.build_p7_r53_current_received_snapshot_refreeze(
            current_received_snapshot_refs=r51.P7_R51_SOURCE_SNAPSHOT_REFS,
        )

    with pytest.raises(ValueError):
        r53.build_p7_r53_current_received_snapshot_refreeze(
            current_received_snapshot_refs=r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS,
        )


def test_r53_r1_freezes_r51_r52_source_delta_rows_without_allowing_old_refs_as_actual_review_basis() -> None:
    delta = _r53_r1()

    assert delta["schema_version"] == r53.P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION
    assert set(delta) == set(r53.P7_R53_R51_R52_SOURCE_DELTA_FREEZE_REQUIRED_FIELD_REFS)
    assert delta["phase"].startswith("P7_")
    assert delta["step"] == r53.P7_R53_STEP
    assert delta["scope"] == r53.P7_R53_SCOPE
    assert delta["policy_section"] == "R53-1_r51_r52_helper_source_delta_freeze"
    assert delta["source_mode"] == "local_snapshot"
    assert delta["git_connection_required"] is False
    assert delta["git_checked"] is False
    assert delta["r0_refreeze_schema_version"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION

    assert delta["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert delta["r51_helper_source_snapshot_refs"] == r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert delta["r52_helper_current_received_snapshot_refs"] == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert delta["current_received_snapshot_refs"]["backend_zip_ref"] == "mashos-api(161).zip"
    assert delta["r51_helper_source_snapshot_refs"]["backend_zip_ref"] == "mashos-api(159).zip"
    assert delta["r52_helper_current_received_snapshot_refs"]["backend_zip_ref"] == "mashos-api(160).zip"
    assert delta["r51_helper_refs_are_current_received_refs"] is False
    assert delta["r52_helper_refs_are_current_received_refs"] is False
    assert delta["r53_current_received_refs_frozen"] is True
    assert delta["old_refs_allowed_as_actual_review_basis"] is False
    assert delta["r51_old_refs_allowed_as_actual_review_basis"] is False
    assert delta["r52_old_refs_allowed_as_actual_review_basis"] is False
    assert delta["r51_builder_snapshot_override_required"] is True
    assert delta["current_snapshot_can_override_r51_builder_snapshot_refs"] is True
    assert delta["r51_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert delta["r52_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert delta["r53_0_scope_current_received_snapshot_refrozen"] is True
    assert delta["r53_1_r51_r52_helper_source_delta_frozen"] is True
    assert tuple(delta["implemented_steps"]) == r53.P7_R53_IMPLEMENTED_STEPS
    assert tuple(delta["not_yet_implemented_steps"]) == r53.P7_R53_NOT_YET_IMPLEMENTED_STEPS
    assert delta["next_required_step"] == r53.P7_R53_R1_NEXT_REQUIRED_STEP_REF

    rows = delta["source_delta_rows"]
    assert delta["source_delta_row_count"] == 2
    assert [row["helper_ref_group"] for row in rows] == [
        "r51_helper_source_snapshot_refs",
        "r52_helper_current_received_snapshot_refs",
    ]
    for row in rows:
        assert r53.assert_p7_r53_source_delta_row_contract(row) is True
        assert row["same_as_r53_current_received_refs"] is False
        assert row["actual_review_basis_allowed"] is False
        assert row["regression_helper_context_allowed"] is True
        assert row["snapshot_override_required_for_actual_review"] is True
        assert row["body_free"] is True

    assert rows[0]["helper_snapshot_refs"] == r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert rows[1]["helper_snapshot_refs"] == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS

    assert delta["p5_human_blind_qa_confirmed"] is False
    assert delta["p5_human_blind_qa_confirmed_candidate"] is False
    assert delta["p6_limited_human_readfeel_candidate"] is False
    assert delta["p6_limited_human_readfeel_start_allowed"] is False
    assert delta["p8_question_design_material_candidate"] is False
    assert delta["p8_start_allowed"] is False
    assert delta["p7_complete"] is False
    assert delta["release_allowed"] is False
    assert delta["api_db_rn_response_key_changed_here"] is False
    assert delta["runtime_changed_here"] is False

    _assert_body_free_no_promotion(delta)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r51_helper_refs_are_current_received_refs", True),
        ("r52_helper_refs_are_current_received_refs", True),
        ("r53_current_received_refs_frozen", False),
        ("old_refs_allowed_as_actual_review_basis", True),
        ("r51_old_refs_allowed_as_actual_review_basis", True),
        ("r52_old_refs_allowed_as_actual_review_basis", True),
        ("r51_builder_snapshot_override_required", False),
        ("current_snapshot_can_override_r51_builder_snapshot_refs", False),
        ("r51_helper_refs_can_be_used_for_helper_regression_only", False),
        ("r52_helper_refs_can_be_used_for_helper_regression_only", False),
        ("r53_0_scope_current_received_snapshot_refrozen", False),
        ("r53_1_r51_r52_helper_source_delta_frozen", False),
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
def test_r53_r1_rejects_source_relabelling_old_basis_actual_review_or_release_promotion(key: str, value: object) -> None:
    material = _r53_r1()
    material[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r52_source_delta_freeze_contract(material)


def test_r53_r1_rejects_current_refs_replaced_by_r51_or_r52_historical_helper_refs() -> None:
    material = _r53_r1()
    material["current_received_snapshot_refs"] = dict(r51.P7_R51_SOURCE_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r52_source_delta_freeze_contract(material)

    material = _r53_r1()
    material["current_received_snapshot_refs"] = dict(r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r52_source_delta_freeze_contract(material)


def test_r53_r1_rejects_source_delta_rows_relabelled_as_current_or_actual_review_basis() -> None:
    material = _r53_r1()
    material["source_delta_rows"][0]["same_as_r53_current_received_refs"] = True
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r52_source_delta_freeze_contract(material)

    material = _r53_r1()
    material["source_delta_rows"][0]["actual_review_basis_allowed"] = True
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r52_source_delta_freeze_contract(material)

    material = _r53_r1()
    material["source_delta_rows"][0]["helper_snapshot_refs"] = dict(r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        r53.assert_p7_r53_r51_r52_source_delta_freeze_contract(material)
