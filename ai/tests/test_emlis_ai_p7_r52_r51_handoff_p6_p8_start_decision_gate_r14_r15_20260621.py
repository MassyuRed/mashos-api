# -*- coding: utf-8 -*-
"""R52-14/R52-15 tests for no-touch validation and documentation output."""

from __future__ import annotations

import pytest

import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52


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
    return [
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


def _r13_missing_evidence() -> dict[str, object]:
    gate = r52.build_p7_r52_r0_r13_final_decision_composer_chain(r51_bodyfree_handoff_materials=_clean_r51_handoff_materials(), r51_actual_review_evidence=None)
    r52.assert_p7_r52_final_decision_composer_contract(gate)
    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    return gate


def _r14_validated(**overrides: object) -> dict[str, object]:
    gate = r52.build_p7_r52_no_touch_boundary_validation(
        final_decision_composer=_r13_missing_evidence(),
        **overrides,
    )
    r52.assert_p7_r52_no_touch_boundary_validation_contract(gate)
    return gate


def _r15_documented(**overrides: object) -> dict[str, object]:
    gate = r52.build_p7_r52_documentation_output(
        no_touch_boundary_validation=_r14_validated(),
        **overrides,
    )
    r52.assert_p7_r52_documentation_output_contract(gate)
    return gate


def test_r52_current_capability_constants_include_r0_to_r15_and_no_remaining_steps() -> None:
    assert tuple(r52.P7_R52_CURRENT_IMPLEMENTED_STEPS) == r52.P7_R52_R15_IMPLEMENTED_STEPS
    assert r52.P7_R52_R14_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_R15_STEP_REF in r52.P7_R52_CURRENT_IMPLEMENTED_STEPS
    assert r52.P7_R52_CURRENT_NOT_YET_IMPLEMENTED_STEPS == ()


def test_r52_r14_no_touch_boundary_passes_for_r52_helper_and_r52_tests_only() -> None:
    gate = _r14_validated()
    assert gate["schema_version"] == r52.P7_R52_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION
    assert gate["policy_section"] == r52.P7_R52_R14_STEP_REF
    assert gate["no_touch_boundary_passed"] is True
    assert gate["no_touch_validation_status"] == "R52_NO_TOUCH_BOUNDARY_VALIDATED"
    assert gate["prohibited_changed_file_ref_count"] == 0
    assert gate["production_helper_candidate_only_changed"] is True
    assert gate["r52_test_file_changes_only_outside_helper"] is True
    assert gate["rn_production_files_no_touch"] is True
    assert gate["rn_contract_tests_no_touch"] is True
    assert gate["api_route_no_touch"] is True
    assert gate["db_schema_no_touch"] is True
    assert gate["db_migration_no_touch"] is True
    assert gate["public_response_top_level_key_no_touch"] is True
    assert gate["emlis_runtime_no_touch"] is True
    assert gate["user_label_connection_runtime_no_touch"] is True
    assert gate["runtime_no_touch"] is True
    assert gate["p8_question_implementation_no_touch"] is True
    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["next_required_step"] == r52.P7_R52_R14_NEXT_REQUIRED_STEP_REF


@pytest.mark.parametrize(
    ("changed_ref", "expected_flag"),
    [
        ("Cocolon/screens/InputScreen.js", "rn_production_files_no_touch"),
        ("Cocolon/tests/rn-screen-contracts.test.js", "rn_contract_tests_no_touch"),
        ("services/ai_inference/api_emotion_submit.py", "api_route_no_touch"),
        ("alembic/versions/20260621_add_question.py", "db_schema_no_touch"),
        ("migrations/20260621_add_question.sql", "db_migration_no_touch"),
        ("services/ai_inference/emlis_ai_public_feedback_meta.py", "public_response_top_level_key_no_touch"),
        ("services/ai_inference/emlis_ai_reply_service.py", "emlis_runtime_no_touch"),
        ("services/ai_inference/emlis_ai_user_label_connection_surface.py", "user_label_connection_runtime_no_touch"),
        ("services/ai_inference/emlis_ai_question_trigger.py", "p8_question_implementation_no_touch"),
    ],
)
def test_r52_r14_blocks_rn_api_db_runtime_public_contract_and_p8_question_changes(changed_ref: str, expected_flag: str) -> None:
    gate = r52.build_p7_r52_no_touch_boundary_validation(
        final_decision_composer=_r13_missing_evidence(),
        changed_file_refs=(r52.P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF, changed_ref),
    )
    assert gate["no_touch_boundary_passed"] is False
    assert gate["decision_ref"] == "R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK"
    assert gate["decision_status"] == "BLOCKED"
    assert gate[expected_flag] is False
    r52.assert_p7_r52_no_touch_boundary_validation_contract(gate)


def test_r52_r14_blocks_non_r52_test_changes_even_when_no_runtime_file_is_touched() -> None:
    gate = r52.build_p7_r52_no_touch_boundary_validation(
        final_decision_composer=_r13_missing_evidence(),
        changed_file_refs=(
            r52.P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF,
            "tests/test_unrelated_contract.py",
        ),
    )
    assert gate["no_touch_boundary_passed"] is False
    assert gate["r52_test_file_changes_only_outside_helper"] is False
    assert gate["prohibited_changed_file_ref_count"] == 1
    assert gate["decision_ref"] == "R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK"


def test_r52_r14_preserves_no_auto_allow_and_body_free_boundaries() -> None:
    gate = _r14_validated()
    assert gate["p5_human_blind_qa_confirmed"] is False
    assert gate["p5_human_blind_qa_confirmed_final"] is False
    assert gate["p6_limited_human_readfeel_start_allowed"] is False
    assert gate["p8_start_allowed"] is False
    assert gate["p7_complete"] is False
    assert gate["release_allowed"] is False
    assert gate["body_free"] is True
    for key in r52.P7_R52_R14_FALSE_KEY_REFS:
        assert gate[key] is False


def test_r52_r14_rejects_forbidden_payload_keys() -> None:
    gate = _r14_validated()
    gate["question_text"] = "どのことを言っていますか"
    with pytest.raises(ValueError):
        r52.assert_p7_r52_no_touch_boundary_validation_contract(gate)


def test_r52_r14_rejects_auto_allow_mutation_flags() -> None:
    gate = _r14_validated()
    gate["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        r52.assert_p7_r52_no_touch_boundary_validation_contract(gate)


def test_r52_r15_documentation_output_records_existing_design_md_without_materializing_files() -> None:
    gate = _r15_documented()
    assert gate["schema_version"] == r52.P7_R52_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert gate["policy_section"] == r52.P7_R52_R15_STEP_REF
    assert gate["documentation_output_status"] == "R52_DOCUMENTATION_OUTPUT_RECORDED_WITH_NO_AUTO_ALLOW"
    assert gate["markdown_documentation_output_present"] is True
    assert gate["documentation_is_existing_design_md"] is True
    assert gate["documentation_file_materialized_here"] is False
    assert gate["json_schema_files_materialized_here"] is False
    assert gate["schema_files_materialized_here"] is False
    assert gate["documentation_acceptance_criteria_recorded"] is True
    assert gate["validation_matrix_recorded"] is True
    assert gate["schema_proposal_recorded"] is True
    assert gate["implementation_order_recorded"] is True
    assert gate["r52_15_documentation_output_built"] is True
    assert gate["implemented_steps"] == list(r52.P7_R52_R15_IMPLEMENTED_STEPS)
    assert gate["not_yet_implemented_steps"] == []


def test_r52_r15_preserves_return_to_r51_when_actual_review_evidence_is_missing() -> None:
    gate = _r15_documented()
    assert gate["r51_actual_review_evidence_complete"] is False
    assert gate["decision_ref"] == "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
    assert gate["decision_status"] == "RETURN_REQUIRED"
    assert gate["next_required_step"] == r52.P7_R52_R15_RETURN_TO_R51_NEXT_REQUIRED_STEP_REF


def test_r52_r15_preserves_no_auto_allow_and_no_touch_contracts() -> None:
    gate = _r15_documented()
    assert gate["p5_human_blind_qa_confirmed"] is False
    assert gate["p5_human_blind_qa_confirmed_final"] is False
    assert gate["p6_limited_human_readfeel_start_allowed"] is False
    assert gate["p8_start_allowed"] is False
    assert gate["p7_complete"] is False
    assert gate["release_allowed"] is False
    assert gate["r52_public_no_touch_contract"]["api_route_changed_here"] is False
    assert gate["r52_public_no_touch_contract"]["runtime_changed_here"] is False
    for key in r52.P7_R52_R15_FALSE_KEY_REFS:
        assert gate[key] is False


def test_r52_r15_blocks_documentation_when_r14_no_touch_is_blocked() -> None:
    blocked_r14 = r52.build_p7_r52_no_touch_boundary_validation(
        final_decision_composer=_r13_missing_evidence(),
        changed_file_refs=(
            r52.P7_R52_PRODUCTION_HELPER_CANDIDATE_FILE_REF,
            "services/ai_inference/api_emotion_submit.py",
        ),
    )
    gate = r52.build_p7_r52_documentation_output(no_touch_boundary_validation=blocked_r14)
    assert gate["documentation_output_status"] == "R52_DOCUMENTATION_OUTPUT_BLOCKED_BY_NO_TOUCH_BOUNDARY"
    assert gate["decision_ref"] == "R52_BLOCKED_BY_NO_TOUCH_BOUNDARY_RISK"
    assert gate["decision_status"] == "BLOCKED"
    assert gate["next_required_step"] == r52.P7_R52_R14_BLOCKED_NEXT_REQUIRED_STEP_REF
    r52.assert_p7_r52_documentation_output_contract(gate)


def test_r52_r15_rejects_forbidden_payload_keys() -> None:
    gate = _r15_documented()
    gate["raw_input"] = "body text must not be present"
    with pytest.raises(ValueError):
        r52.assert_p7_r52_documentation_output_contract(gate)


def test_r52_r15_rejects_schema_materialization_and_question_text_documentation() -> None:
    gate = _r15_documented()
    gate["json_schema_files_materialized_here"] = True
    with pytest.raises(ValueError):
        r52.assert_p7_r52_documentation_output_contract(gate)
    gate = _r15_documented()
    gate["question_text_documented_here"] = True
    with pytest.raises(ValueError):
        r52.assert_p7_r52_documentation_output_contract(gate)
