# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from types import ModuleType

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51


FORBIDDEN_BODY_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"bounded_owned_history_review_surface":',
    '"current_input_review_surface":',
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
FORBIDDEN_ALLOWED_PROMOTION_TOKENS = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"hold004_close_allowed": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_trigger_logic_implemented": true',
    '"question_trigger_logic_implemented_here": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"full_backend_suite_green_confirmed": true',
)


def _assert_bodyfree_no_leak_or_allowed_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_BODY_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_ALLOWED_PROMOTION_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _r18_r19_helpers() -> ModuleType:
    path = Path(__file__).with_name(
        "test_emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run_r18_r19_20260620.py"
    )
    spec = importlib.util.spec_from_file_location("_r51_r18_r19_helpers_for_r20", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ready_r19() -> dict[str, object]:
    helpers = _r18_r19_helpers()
    r16, r17 = helpers._confirmed_r16_r17()
    r18 = r51.build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree=r17
    )
    assert r51.assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(r18) is True
    r19 = r51.build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=r18,
        body_free_post_review_summary_builder_bodyfree=r16,
    )
    assert r51.assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(r19) is True
    assert r19["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    return r19


def test_r51_r20_validates_final_bodyfree_material_without_p7_p8_or_release_promotion() -> None:
    r20 = r51.build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(
        p8_question_design_material_candidate_handoff_bodyfree=_ready_r19()
    )

    assert r20["schema_version"] == r51.P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION
    assert set(r20) == set(r51.P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_BODYFREE_REQUIRED_FIELD_REFS)
    assert r20["policy_section"] == "R51-20_no_body_leak_no_question_text_no_touch_boundary_validation"
    assert r20["boundary_validation_status"] == "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED"
    assert r20["r20_no_body_leak_no_question_text_no_touch_boundary_validation_built"] is True
    assert r20["body_free_no_leak_scan_passed"] is True
    assert r20["no_touch_boundary_validated"] is True
    assert r20["p8_question_design_material_candidate"] is True
    assert r20["p8_start_allowed"] is False
    assert r20["p7_complete"] is False
    assert r20["release_allowed"] is False
    assert r20["p6_limited_human_readfeel_start_allowed"] is False
    assert r20["p8_question_implementation_not_started"] is True
    assert r20["question_trigger_logic_implemented_here"] is False
    assert r20["api_db_rn_response_key_changed_here"] is False
    assert tuple(r20["implemented_steps"]) == r51.P7_R51_R20_IMPLEMENTED_STEPS
    assert tuple(r20["not_yet_implemented_steps"]) == r51.P7_R51_R20_NOT_YET_IMPLEMENTED_STEPS
    assert r20["next_required_step"] == r51.P7_R51_R20_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_allowed_promotion(r20)


def test_r51_r20_blocks_bodyfree_handoff_when_question_text_material_is_seen() -> None:
    r20 = r51.build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(
        p8_question_design_material_candidate_handoff_bodyfree=_ready_r19(),
        additional_body_free_materials={
            "material_id": "leaky_question_text_material",
            "body_free": True,
            "question_text": "this question text must not enter R51 body-free material",
        },
    )

    assert r20["boundary_validation_status"] == "BLOCKED_BY_R51_BODY_LEAK_OR_NO_TOUCH_BOUNDARY_VIOLATION"
    assert r20["r20_no_body_leak_no_question_text_no_touch_boundary_validation_built"] is False
    assert r20["question_text_key_scan_passed"] is False
    assert r20["body_free_no_leak_scan_passed"] is False
    assert any("question_text" in path for path in r20["detected_forbidden_body_key_paths"])
    assert r20["p8_question_design_material_candidate"] is False
    assert r20["p8_start_allowed"] is False
    assert tuple(r20["implemented_steps"]) == r51.P7_R51_R19_IMPLEMENTED_STEPS
    assert r20["next_required_step"] == r51.P7_R51_R20_BLOCKED_NEXT_REQUIRED_STEP_REF


def test_r51_r20_blocks_no_touch_boundary_when_diff_reaches_rn_api_db_or_runtime_files() -> None:
    r20 = r51.build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(
        p8_question_design_material_candidate_handoff_bodyfree=_ready_r19(),
        actual_touched_file_refs=(
            "services/ai_inference/emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run.py",
            "tests/test_emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run_r20_20260621.py",
            "Cocolon/screens/InputScreen.js",
        ),
    )

    assert r20["boundary_validation_status"] == "BLOCKED_BY_R51_BODY_LEAK_OR_NO_TOUCH_BOUNDARY_VIOLATION"
    assert r20["no_touch_boundary_validated"] is False
    assert r20["forbidden_actual_touched_refs_detected_here"] is True
    assert "Cocolon/screens/InputScreen.js" in r20["forbidden_actual_touched_file_refs"]
    assert r20["rn_no_touch_preserved"] is False
    assert r20["p8_start_allowed"] is False
    assert r20["p7_complete"] is False
    assert r20["release_allowed"] is False
    assert r20["next_required_step"] == r51.P7_R51_R20_BLOCKED_NEXT_REQUIRED_STEP_REF


def test_r51_r20_contract_rejects_direct_p8_start_release_or_body_mutation() -> None:
    r20 = r51.build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(
        p8_question_design_material_candidate_handoff_bodyfree=_ready_r19()
    )

    p8_start_claim = deepcopy(r20)
    p8_start_claim["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(p8_start_claim)

    release_claim = deepcopy(r20)
    release_claim["release_allowed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(release_claim)

    body_claim = deepcopy(r20)
    body_claim["raw_input"] = "body must not enter R51-20 final validation"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(body_claim)


def test_r51_r20_keeps_schema_runtime_api_db_rn_and_p8_question_implementation_closed() -> None:
    r20 = r51.build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(
        p8_question_design_material_candidate_handoff_bodyfree=_ready_r19()
    )

    assert tuple(r20["allowed_actual_touched_file_refs"]) == r51.P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS
    assert tuple(r20["expected_touched_file_refs"]) == r51.P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS
    assert not (set(r20["allowed_actual_touched_file_refs"]) & set(r20["explicit_no_touch_file_refs"]))
    assert r20["rn_contract_changed_here"] is False
    assert r20["rn_production_files_touched_here"] is False
    assert r20["rn_contract_test_files_touched_here"] is False
    assert r20["api_route_changed_here"] is False
    assert r20["db_schema_changed_here"] is False
    assert r20["db_migration_changed_here"] is False
    assert r20["emlis_reply_runtime_changed_here"] is False
    assert r20["user_label_connection_runtime_changed_here"] is False
    assert r20["runtime_changed_here"] is False
    assert r20["public_response_top_level_key_added_here"] is False
    assert r20["question_trigger_logic_implemented_here"] is False
    assert r20["p8_question_implementation_spec_finalized_here"] is False
    assert r20["p8_question_implementation_not_started"] is True
