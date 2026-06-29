# -*- coding: utf-8 -*-
"""R52-2/R52-3 tests for R51 body-free handoff intake and deep scan."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52


def _r52_r0() -> dict[str, object]:
    return r52.build_p7_r52_current_received_snapshot_refreeze()


def _r52_r1(**overrides: object) -> dict[str, object]:
    return r52.build_p7_r52_validation_evidence_matrix_freeze(
        current_received_snapshot_refreeze=_r52_r0(),
        validation_evidence_overrides=overrides.get("validation_evidence_overrides"),
    )


def _minimal_r51_material(component_ref: str, **extra: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": r52.P7_R52_R51_REQUIRED_HANDOFF_SCHEMA_VERSION_BY_COMPONENT_REF[component_ref],
        "material_id": f"r51_bodyfree_{component_ref}",
        "r51_handoff_component_ref": component_ref,
        "body_free": True,
    }
    material.update(extra)
    return material


def _clean_r51_handoff_materials() -> list[dict[str, object]]:
    materials = [
        _minimal_r51_material(
            "r16_body_free_post_review_summary",
            actual_human_review_run_here=True,
            actual_rating_rows_materialized_here=True,
            actual_question_need_observation_rows_materialized_here=True,
            post_review_summary_materialized_here=True,
        ),
        _minimal_r51_material(
            "r17_p5_confirmed_repair_return_inconclusive_decision",
            p5_human_blind_qa_confirmed_candidate=True,
        ),
        _minimal_r51_material(
            "r18_p6_limited_human_readfeel_candidate_handoff",
            p6_limited_human_readfeel_start_allowed_candidate=True,
        ),
        _minimal_r51_material(
            "r19_p8_question_design_material_candidate_handoff",
            p8_question_design_material_candidate=True,
        ),
        _minimal_r51_material(
            "r20_no_body_leak_no_question_text_no_touch_boundary_validation",
            boundary_validation_status="R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED",
            next_required_step=r52.P7_R51_R20_NEXT_REQUIRED_STEP_REF,
        ),
    ]
    return materials


def _assert_no_auto_allow(material: dict[str, object]) -> None:
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["question_trigger_logic_implemented_here"] is False


def test_r52_r2_intakes_clean_r51_bodyfree_handoff_and_normalizes_r51_actual_flags_without_copying_payloads() -> None:
    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=_r52_r1(),
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
    )

    assert r52.assert_p7_r52_r51_bodyfree_handoff_intake_contract(intake) is True
    assert intake["schema_version"] == r52.P7_R52_R51_BODYFREE_HANDOFF_INTAKE_SCHEMA_VERSION
    assert set(intake) == set(r52.P7_R52_R51_BODYFREE_HANDOFF_INTAKE_REQUIRED_FIELD_REFS)
    assert intake["policy_section"] == r52.P7_R52_R2_STEP_REF
    assert intake["r1_validation_evidence_ready_for_r52_2_intake"] is True
    assert tuple(intake["r51_required_handoff_component_refs"]) == r52.P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS
    assert tuple(intake["r51_present_handoff_component_refs"]) == r52.P7_R52_R51_REQUIRED_HANDOFF_COMPONENT_REFS
    assert intake["r51_missing_handoff_component_refs"] == []
    assert intake["r51_handoff_material_ref_count"] == 5
    assert intake["r51_bodyfree_material_count_scanned"] == 5
    assert intake["r51_r20_boundary_validation_status"] == "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED"
    assert intake["r51_next_required_step"] == r52.P7_R51_R20_NEXT_REQUIRED_STEP_REF
    assert intake["r51_body_free"] is True
    assert intake["detected_forbidden_payload_key_paths"] == []
    assert intake["detected_forbidden_true_flag_paths"] == []
    assert intake["forbidden_payload_keys_absent"] is True
    assert intake["forbidden_true_flags_absent"] is True
    assert intake["body_free_boundary_passed"] is True
    assert intake["r51_handoff_intake_status"] == "R52_R51_BODYFREE_HANDOFF_INTAKE_ACCEPTED"
    assert intake["r51_handoff_intake_ready_for_r52_3_deep_scan"] is True
    assert intake["r52_2_r51_bodyfree_handoff_intake_contract_built"] is True
    assert intake["r52_3_forbidden_payload_deep_scan_built"] is False
    assert intake["next_required_step"] == r52.P7_R52_R2_NEXT_REQUIRED_STEP_REF
    assert tuple(intake["implemented_steps"]) == r52.P7_R52_R2_IMPLEMENTED_STEPS
    assert tuple(intake["not_yet_implemented_steps"]) == r52.P7_R52_R2_NOT_YET_IMPLEMENTED_STEPS

    normalized = set(intake["r51_reported_actual_true_flag_refs_normalized"])
    assert "r51_reported_actual_human_review_run_here" in normalized
    assert "r51_reported_actual_rating_rows_materialized_here" in normalized
    assert "r51_reported_actual_question_need_observation_rows_materialized_here" in normalized
    assert "r51_reported_p5_human_blind_qa_confirmed_candidate" in normalized
    assert "r51_reported_p6_limited_human_readfeel_start_allowed_candidate" in normalized
    assert "r51_reported_p8_question_design_material_candidate" in normalized
    assert intake["r51_unprefixed_actual_report_true_flag_paths_detected"]
    assert intake["r51_unprefixed_actual_report_flags_copied_to_output"] is False
    assert intake["r51_bodyfree_material_body_stored_here"] is False
    assert intake["r51_raw_material_payload_stored_here"] is False
    assert intake["r52_copied_r51_bodyfree_materials_to_output"] is False
    assert "raw_input" not in intake
    assert "question_text" not in intake
    assert "reviewer_free_text" not in intake
    _assert_no_auto_allow(intake)


def test_r52_r2_blocks_missing_required_r51_handoff_components_without_starting_p6_p8() -> None:
    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=_r52_r1(),
        r51_bodyfree_handoff_materials=[
            _minimal_r51_material(
                "r20_no_body_leak_no_question_text_no_touch_boundary_validation",
                boundary_validation_status="R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED",
                next_required_step=r52.P7_R51_R20_NEXT_REQUIRED_STEP_REF,
            )
        ],
    )

    assert r52.assert_p7_r52_r51_bodyfree_handoff_intake_contract(intake) is True
    assert intake["r51_handoff_intake_status"] == "R52_BLOCKED_BY_R51_HANDOFF_COMPONENTS_MISSING"
    assert "r16_body_free_post_review_summary" in intake["r51_missing_handoff_component_refs"]
    assert intake["r51_handoff_intake_ready_for_r52_3_deep_scan"] is False
    assert intake["next_required_step"] == r52.P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(intake)


def test_r52_r2_blocks_when_r1_validation_evidence_is_not_ready() -> None:
    blocked_r1 = _r52_r1(
        validation_evidence_overrides={
            "r51_target": {
                "evidence_status_ref": "MISSING",
                "evidence_present": False,
                "passed_count": 0,
                "collected_count": 0,
                "warning_count": 0,
            }
        }
    )
    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=blocked_r1,
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
    )

    assert intake["r1_validation_evidence_ready_for_r52_2_intake"] is False
    assert intake["r51_handoff_intake_status"] == "R52_BLOCKED_BY_R51_VALIDATION_EVIDENCE_NOT_READY"
    assert intake["r51_handoff_intake_ready_for_r52_3_deep_scan"] is False
    assert "r52_r1_validation_evidence_not_ready_for_r52_2_intake" in intake["r51_handoff_intake_reason_refs"]
    _assert_no_auto_allow(intake)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "raw_input",
        "raw_answer",
        "comment_text_body",
        "returned_emlis_surface",
        "reviewer_free_text",
        "question_text",
        "draft_question_text",
        "question_body",
        "local_absolute_path",
        "body_content_hash",
        "packet_content_hash",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
    ],
)
def test_r52_r2_detects_forbidden_payload_keys_recursively(forbidden_key: str) -> None:
    materials = _clean_r51_handoff_materials()
    materials[0]["nested_boundary_probe"] = {forbidden_key: "body must not be copied or accepted"}

    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=_r52_r1(),
        r51_bodyfree_handoff_materials=materials,
    )

    assert intake["r51_handoff_intake_status"] == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    assert intake["r51_body_free"] is False
    assert intake["forbidden_payload_keys_absent"] is False
    assert any(path.endswith(f".{forbidden_key}") for path in intake["detected_forbidden_payload_key_paths"])
    assert intake["r51_handoff_intake_ready_for_r52_3_deep_scan"] is False
    assert intake["next_required_step"] == r52.P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(intake)


@pytest.mark.parametrize(
    "forbidden_flag",
    [
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "public_response_top_level_key_added_here",
        "runtime_changed_here",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ],
)
def test_r52_r2_detects_forbidden_true_flags_recursively(forbidden_flag: str) -> None:
    materials = _clean_r51_handoff_materials()
    materials[-1]["nested_true_flag_probe"] = {forbidden_flag: True}

    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=_r52_r1(),
        r51_bodyfree_handoff_materials=materials,
    )

    assert intake["r51_handoff_intake_status"] == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    assert intake["forbidden_true_flags_absent"] is False
    assert any(path.endswith(f".{forbidden_flag}") for path in intake["detected_forbidden_true_flag_paths"])
    assert intake["r51_handoff_intake_ready_for_r52_3_deep_scan"] is False
    _assert_no_auto_allow(intake)


def test_r52_r3_passes_clean_deep_scan_and_points_only_to_actual_review_evidence_check() -> None:
    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=_r52_r1(),
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(),
    )
    scan = r52.build_p7_r52_forbidden_payload_deep_scan(r51_bodyfree_handoff_intake=intake)

    assert r52.assert_p7_r52_forbidden_payload_deep_scan_contract(scan) is True
    assert scan["schema_version"] == r52.P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_SCHEMA_VERSION
    assert set(scan) == set(r52.P7_R52_FORBIDDEN_PAYLOAD_DEEP_SCAN_REQUIRED_FIELD_REFS)
    assert scan["policy_section"] == r52.P7_R52_R3_STEP_REF
    assert scan["r2_intake_status"] == "R52_R51_BODYFREE_HANDOFF_INTAKE_ACCEPTED"
    assert scan["r2_intake_ready_for_r52_3_deep_scan"] is True
    assert scan["scan_material_ref_count"] == 5
    assert scan["scan_material_count"] == 5
    assert scan["detected_forbidden_payload_key_paths"] == []
    assert scan["detected_forbidden_true_flag_paths"] == []
    assert scan["forbidden_payload_keys_absent"] is True
    assert scan["forbidden_true_flags_absent"] is True
    assert scan["body_free_boundary_passed"] is True
    assert scan["boundary_risk_detected"] is False
    assert scan["decision_ref"] == "R52_R51_BODYFREE_HANDOFF_ACCEPTED_FOR_ACTUAL_REVIEW_EVIDENCE_CHECK"
    assert scan["decision_status"] == "CANDIDATE_ONLY"
    assert scan["r52_2_r51_bodyfree_handoff_intake_contract_built"] is True
    assert scan["r52_3_forbidden_payload_deep_scan_built"] is True
    assert tuple(scan["implemented_steps"]) == r52.P7_R52_R3_IMPLEMENTED_STEPS
    assert tuple(scan["not_yet_implemented_steps"]) == r52.P7_R52_R3_NOT_YET_IMPLEMENTED_STEPS
    assert scan["next_required_step"] == r52.P7_R52_R3_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(scan)


def test_r52_r3_boundary_risk_stays_blocked_and_does_not_mark_deep_scan_built() -> None:
    materials = _clean_r51_handoff_materials()
    materials[2]["nested_boundary_probe"] = {"question_text": "not allowed"}
    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=_r52_r1(),
        r51_bodyfree_handoff_materials=materials,
    )
    scan = r52.build_p7_r52_forbidden_payload_deep_scan(r51_bodyfree_handoff_intake=intake)

    assert r52.assert_p7_r52_forbidden_payload_deep_scan_contract(scan) is True
    assert scan["boundary_risk_detected"] is True
    assert scan["decision_ref"] == "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK"
    assert scan["decision_status"] == "BLOCKED"
    assert scan["r52_3_forbidden_payload_deep_scan_built"] is False
    assert any(path.endswith(".question_text") for path in scan["detected_forbidden_payload_key_paths"])
    assert scan["next_required_step"] == r52.P7_R52_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(scan)


def test_r52_r3_returns_to_r52_2_when_intake_is_not_ready_without_boundary_risk() -> None:
    intake = r52.build_p7_r52_r51_bodyfree_handoff_intake(
        validation_evidence_matrix_freeze=_r52_r1(),
        r51_bodyfree_handoff_materials=[
            _minimal_r51_material(
                "r20_no_body_leak_no_question_text_no_touch_boundary_validation",
                boundary_validation_status="R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED",
                next_required_step=r52.P7_R51_R20_NEXT_REQUIRED_STEP_REF,
            )
        ],
    )
    scan = r52.build_p7_r52_forbidden_payload_deep_scan(r51_bodyfree_handoff_intake=intake)

    assert scan["boundary_risk_detected"] is False
    assert scan["decision_ref"] == "R52_RETURN_TO_R51_BODYFREE_HANDOFF_INTAKE_REQUIRED"
    assert scan["decision_status"] == "RETURN_REQUIRED"
    assert scan["r52_3_forbidden_payload_deep_scan_built"] is True
    assert scan["next_required_step"] == r52.P7_R52_R2_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_auto_allow(scan)


@pytest.mark.parametrize(
    "key,value",
    [
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
        ("question_trigger_logic_implemented_here", True),
    ],
)
def test_r52_r3_contract_rejects_p6_p8_release_or_runtime_promotion(key: str, value: object) -> None:
    scan = r52.build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials()
    )
    scan[key] = value
    with pytest.raises(ValueError):
        r52.assert_p7_r52_forbidden_payload_deep_scan_contract(scan)


def test_r52_r3_contract_rejects_success_material_if_forbidden_paths_are_inserted() -> None:
    scan = r52.build_p7_r52_r0_r3_r51_bodyfree_intake_forbidden_scan_chain(
        r51_bodyfree_handoff_materials=_clean_r51_handoff_materials()
    )
    mutated = deepcopy(scan)
    mutated["detected_forbidden_payload_key_paths"] = ["r51_bodyfree_handoff_materials[0].raw_input"]
    mutated["boundary_risk_detected"] = False
    with pytest.raises(ValueError):
        r52.assert_p7_r52_forbidden_payload_deep_scan_contract(mutated)
