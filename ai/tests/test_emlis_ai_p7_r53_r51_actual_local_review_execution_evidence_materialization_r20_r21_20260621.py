# -*- coding: utf-8 -*-
"""P7-R53 R20/R21 tests for P8 material candidate and R52 re-intake handoff."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

_R53_R20_READY_CACHE: dict[str, object] | None = None
_R53_R21_READY_CACHE: dict[str, object] | None = None

sys.path.append(str(Path(__file__).resolve().parent))

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r14_r15_20260621 import (
    _assert_common_no_p8_release_or_runtime_change,
    _assert_no_body_payload_key_like_values,
)
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r16_r17_20260621 import (
    _r53_r17_ready,
)
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r18_r19_20260621 import (
    _r53_r18_repair_return,
    _r53_r19_ready,
)


def _assert_no_p8_start_release_or_question_implementation(material: dict[str, object]) -> None:
    _assert_common_no_p8_release_or_runtime_change(material)
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented_here"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packets_created_local_only"] is False
    if "local_packet_exported" in material:
        assert material["local_packet_exported"] is False
    if "content_hash_of_body_stored" in material:
        assert material["content_hash_of_body_stored"] is False
    _assert_no_body_payload_key_like_values(material)


def _r53_r20_ready() -> dict[str, object]:
    global _R53_R20_READY_CACHE
    if _R53_R20_READY_CACHE is None:
        material = r53.build_p7_r53_p8_question_design_material_candidate_handoff_bodyfree(
            p6_limited_human_readfeel_candidate_handoff_bodyfree=_r53_r19_ready(),
            body_free_post_review_summary_bodyfree=_r53_r17_ready(),
        )
        assert r53.assert_p7_r53_p8_question_design_material_candidate_handoff_bodyfree_contract(material) is True
        _R53_R20_READY_CACHE = material
    return deepcopy(_R53_R20_READY_CACHE)


def _r53_r21_ready() -> dict[str, object]:
    global _R53_R21_READY_CACHE
    if _R53_R21_READY_CACHE is None:
        material = r53.build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree(
            p8_question_design_material_candidate_handoff_bodyfree=_r53_r20_ready(),
        )
        assert r53.assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree_contract(material) is True
        _R53_R21_READY_CACHE = material
    return deepcopy(_R53_R21_READY_CACHE)


def test_r53_r20_default_blocks_p8_material_until_p5_p6_and_bodyfree_counts_are_ready() -> None:
    material = r53.build_p7_r53_p8_question_design_material_candidate_handoff_bodyfree()

    assert material["schema_version"] == r53.P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert set(material) == set(r53.P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == "R53-20_p8_question_design_material_candidate_handoff"
    assert material["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS"
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_question_design_material_candidate_requirements_met"] is False
    assert material["r17_summary_provided_for_p8_counts"] is False
    assert material["missing_requirement_refs"]
    assert material["next_required_step"] == r53.P7_R53_R20_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_no_p8_start_release_or_question_implementation(material)


def test_r53_r20_ready_hands_off_only_bodyfree_p8_question_design_material_candidate() -> None:
    material = _r53_r20_ready()

    assert material["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    assert material["review_session_status"] == "R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY_BODYFREE"
    assert material["r19_ready_for_p8_material_candidate_handoff"] is True
    assert material["r17_summary_provided_for_p8_counts"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_repair_return_candidate"] is False
    assert material["p5_review_inconclusive"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_start_allowed"] is False
    assert material["question_observation_rows_complete"] is True
    assert material["body_free_question_observation_material_available"] is True
    assert material["repair_required_not_question_misclassified_as_p8_candidate"] is False
    assert material["p5_repair_return_material_mixed_into_p8_candidate"] is False
    assert material["question_implementation_not_started"] is True
    assert material["question_text_absent"] is True
    assert material["draft_question_text_absent"] is True
    assert material["missing_requirement_refs"] == []
    assert tuple(material["implemented_steps"]) == r53.P7_R53_R20_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r53.P7_R53_R20_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == r53.P7_R53_R20_NEXT_REQUIRED_STEP_REF
    assert r51.assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(
        material["r51_r19_p8_question_design_material_candidate_handoff_bodyfree"],
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    ) is True

    _assert_no_p8_start_release_or_question_implementation(material)


def test_r53_r20_blocks_repair_return_material_from_becoming_p8_question_material() -> None:
    r19_blocked = r53.build_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_decision_candidate_separation_bodyfree=_r53_r18_repair_return(),
    )
    material = r53.build_p7_r53_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=r19_blocked,
        body_free_post_review_summary_bodyfree=_r53_r17_ready(),
    )

    assert material["p8_question_design_material_candidate_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS"
    assert material["p5_repair_return_candidate"] is True
    assert material["p8_question_design_material_candidate"] is False
    assert "p5_confirmed_candidate_required_for_p8_material" in material["missing_requirement_refs"]
    assert "p5_repair_or_inconclusive_must_not_feed_p8_material" in material["missing_requirement_refs"]
    assert material["p5_repair_return_material_mixed_into_p8_candidate"] is False

    _assert_no_p8_start_release_or_question_implementation(material)


def test_r53_r20_rejects_question_text_p8_start_release_or_runtime_mutations() -> None:
    base = _r53_r20_ready()
    forbidden_pairs = [
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("hold004_close_allowed", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented_here", True),
        ("api_db_rn_response_key_changed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("question_text_absent", False),
        ("draft_question_text_absent", False),
    ]
    for key, value in forbidden_pairs:
        material = deepcopy(base)
        material[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_p8_question_design_material_candidate_handoff_bodyfree_contract(material)


def test_r53_r21_ready_validates_no_body_no_question_no_touch_and_builds_r52_reintake_handoff_without_auto_allow() -> None:
    material = _r53_r21_ready()

    assert material["schema_version"] == r53.P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_R52_REINTAKE_SCHEMA_VERSION
    assert set(material) == set(r53.P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_R52_REINTAKE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == "R53-21_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff"
    assert material["final_boundary_validation_status"] == "R53_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATED_AND_R52_REINTAKE_HANDOFF_READY"
    assert material["r20_ready_for_final_validation"] is True
    assert material["r51_r20_boundary_validation_status"] == "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED"
    assert material["body_free_no_leak_scan_passed"] is True
    assert material["no_touch_boundary_validated"] is True
    assert material["actual_touched_file_refs"] == list(r53.P7_R53_R21_EXPECTED_TOUCHED_FILE_REFS)
    assert material["forbidden_actual_touched_file_refs"] == []
    assert material["not_allowed_actual_touched_file_refs"] == []
    assert material["detected_forbidden_body_key_paths"] == []
    assert material["detected_forbidden_true_flag_paths"] == []
    assert material["question_text_absent"] is True
    assert material["draft_question_text_absent"] is True
    assert material["raw_input_absent"] is True
    assert material["returned_surface_absent"] is True
    assert material["reviewer_free_text_absent"] is True
    assert material["local_path_absent"] is True
    assert material["body_hash_absent"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == r53.P7_R53_R21_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == r53.P7_R53_R21_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r53.P7_R53_R21_NOT_YET_IMPLEMENTED_STEPS

    reintake = material["r52_reintake_handoff_bodyfree"]
    assert reintake["schema_version"] == r53.P7_R53_R52_REINTAKE_HANDOFF_SCHEMA_VERSION
    assert reintake["r51_actual_review_evidence_complete"] is True
    assert reintake["p8_question_design_material_candidate"] is True
    assert reintake["p8_start_allowed"] is False
    assert reintake["p7_complete"] is False
    assert reintake["release_allowed"] is False
    assert reintake["question_implementation_started_here"] is False
    assert "p8_question_design_material_candidate_handoff" in reintake["r51_bodyfree_handoff_components"]
    assert r51.assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(
        material["r51_r20_no_body_leak_no_question_text_no_touch_bodyfree"],
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_question_design_material_candidate",
        ),
    ) is True

    _assert_no_p8_start_release_or_question_implementation(material)


def test_r53_r21_blocks_r52_reintake_when_no_touch_refs_include_runtime_or_rn_files() -> None:
    material = r53.build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree(
        p8_question_design_material_candidate_handoff_bodyfree=_r53_r20_ready(),
        actual_touched_file_refs=(
            "services/ai_inference/emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization.py",
            "services/ai_inference/api_emotion_submit.py",
            "Cocolon/screens/InputScreen.js",
        ),
    )

    assert material["final_boundary_validation_status"] == "BLOCKED_BY_R53_BODY_LEAK_QUESTION_TEXT_NO_TOUCH_OR_R52_REINTAKE_BOUNDARY"
    assert material["no_touch_boundary_validated"] is False
    assert "services/ai_inference/api_emotion_submit.py" in material["forbidden_actual_touched_file_refs"]
    assert "Cocolon/screens/InputScreen.js" in material["forbidden_actual_touched_file_refs"]
    assert material["r52_reintake_handoff_bodyfree"]["r51_actual_review_evidence_complete"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == r53.P7_R53_R21_BLOCKED_NEXT_REQUIRED_STEP_REF


def test_r53_r21_blocks_bodyfree_material_with_raw_or_question_text_like_keys_without_exporting_body() -> None:
    material = r53.build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree(
        p8_question_design_material_candidate_handoff_bodyfree=_r53_r20_ready(),
        additional_body_free_materials={
            "material_id": "synthetic_bad_bodyfree_material",
            "raw_input": "must-never-be-exported",
            "question_text": "must-never-be-exported",
        },
    )

    assert material["final_boundary_validation_status"] == "BLOCKED_BY_R53_BODY_LEAK_QUESTION_TEXT_NO_TOUCH_OR_R52_REINTAKE_BOUNDARY"
    assert material["body_free_no_leak_scan_passed"] is False
    assert material["detected_forbidden_body_key_paths"]
    assert material["r52_reintake_handoff_bodyfree"]["r51_actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False


def test_r53_r21_rejects_p8_start_release_question_spec_or_body_payload_mutations() -> None:
    base = _r53_r21_ready()
    forbidden_pairs = [
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("hold004_close_allowed", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented_here", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
        ("rn_contract_changed_here", True),
        ("api_route_changed_here", True),
        ("db_schema_changed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("question_text_absent", False),
        ("raw_input_absent", False),
    ]
    for key, value in forbidden_pairs:
        material = deepcopy(base)
        material[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree_contract(material)

    leaked = deepcopy(base)
    leaked["raw_input"] = "body must never appear in body-free R53 R21 material"
    with pytest.raises(ValueError):
        r53.assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree_contract(leaked)
