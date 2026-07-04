# -*- coding: utf-8 -*-
"""R54-AHR Post-DMD08 actual local review operation ALR-OP04/OP05 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_op03_20260703 import (
    _assert_common_bodyfree_no_touch_no_promotion,
    _complete_receipt_for_alr,
    _continuable_session,
    _op01_complete,
    _op01_evidence_incomplete,
)


def _op02_missing() -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
    )


def _op02_continuable() -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=_continuable_session(),
    )


def _op02_complete() -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_complete(),
        existing_actual_operation_receipt_bodyfree=_complete_receipt_for_alr(),
    )


def _op02_repair_from_body_leak() -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=_continuable_session(raw_input="body-value-must-not-survive"),
    )


def _op02_repair_from_promotion() -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=_continuable_session(p8_start_allowed=True),
    )


def _op03(op02: dict[str, object]) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
        alr_op02_existing_operation_material_inventory=op02,
    )


def _op04(op02: dict[str, object]) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver(
        alr_op03_bodyfree_leak_invalid_source_promotion_scan=_op03(op02),
    )


def _op05(op04: dict[str, object]) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization(
        alr_op04_continue_retry_repair_complete_action_resolver=op04,
    )


def test_alr_op04_resolves_missing_clean_inventory_to_retry_or_start_required() -> None:
    material = _op04(_op02_missing())

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP04_SCHEMA_VERSION
    assert tuple(material["action_resolver_priority_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RESOLVER_PRIORITY_REFS
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    assert material["continue_allowed"] is False
    assert material["retry_or_start_required"] is True
    assert material["repair_stop_required"] is False
    assert material["complete_receipt_manual_decision_required"] is False
    assert material["exactly_one_action_flag_true"] is True
    assert material["operation_plan_required"] is True
    assert material["selected_action_next_step_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF
    assert material["actual_local_human_review_executed_here"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op04_resolves_continuable_session_to_continue_allowed() -> None:
    material = _op04(_op02_continuable())

    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF
    assert material["continue_allowed"] is True
    assert material["retry_or_start_required"] is False
    assert material["operation_plan_required"] is True
    assert material["selected_action_next_step_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_CONTINUE_EXISTING_REVIEW_REF
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op04_resolves_complete_receipt_candidate_to_downstream_manual_decision() -> None:
    material = _op04(_op02_complete())

    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF
    assert material["complete_receipt_manual_decision_required"] is True
    assert material["operation_plan_required"] is False
    assert material["selected_action_next_step_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize("op02_builder", [_op02_repair_from_body_leak, _op02_repair_from_promotion])
def test_alr_op04_gives_repair_priority_over_other_action_candidates(op02_builder) -> None:
    material = _op04(op02_builder())

    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
    assert material["repair_stop_required"] is True
    assert material["operation_plan_required"] is False
    assert material["selected_action_next_step_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF
    assert "body-value-must-not-survive" not in repr(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op04_contract_rejects_multiple_action_flags() -> None:
    material = _op04(_op02_missing())
    material["continue_allowed"] = True
    material["exactly_one_action_flag_true"] = False

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(material)


def test_alr_op04_contract_rejects_wrong_selected_action_next_step() -> None:
    material = _op04(_op02_missing())
    material["selected_action_next_step_ref"] = alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(material)


def test_alr_op05_materializes_retry_action_to_retry_state_and_op06_boundary() -> None:
    material = _op05(_op04(_op02_missing()))

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP05_SCHEMA_VERSION
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    assert material["operation_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_RETRY_OR_START_REQUIRED_REF
    assert material["next_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED_REF
    assert material["operation_state_materialized"] is True
    assert material["operation_plan_required"] is True
    assert material["explicit_local_only_allow_required_next"] is True
    assert material["body_full_packet_generation_allowed_here"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF
    assert any("P8_START" in ref for ref in material["forbidden_transition_refs"])
    assert any("R52_ACTUAL_EXECUTION" in ref for ref in material["forbidden_transition_refs"])
    assert any("RELEASE_ALLOWED" in ref for ref in material["forbidden_transition_refs"])
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op05_materializes_continue_action_without_claiming_execution() -> None:
    material = _op05(_op04(_op02_continuable()))

    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF
    assert material["operation_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED_REF
    assert material["next_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_IN_PROGRESS_BODYFREE_TRACKED_REF
    assert material["explicit_local_only_allow_required_next"] is True
    assert material["body_full_packet_generation_allowed_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op05_materializes_complete_receipt_candidate_without_auto_promotion() -> None:
    material = _op05(_op04(_op02_complete()))

    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF
    assert material["operation_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_EVIDENCE_COMPLETE_CANDIDATE_REF
    assert material["next_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF
    assert material["operation_plan_required"] is False
    assert material["explicit_local_only_allow_required_next"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op05_materializes_repair_action_to_repair_stop_state() -> None:
    material = _op05(_op04(_op02_repair_from_body_leak()))

    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
    assert material["operation_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF
    assert material["next_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF
    assert material["operation_plan_required"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert material["not_claimed_boundary"]["actual_local_human_review_execution"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op05_contract_rejects_forbidden_transition_loss() -> None:
    material = _op05(_op04(_op02_missing()))
    material["forbidden_transition_refs"] = [
        ref for ref in material["forbidden_transition_refs"] if "P8_START" not in ref
    ]
    material["forbidden_transition_ref_count"] = len(material["forbidden_transition_refs"])

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(material)


def test_alr_op04_op05_aliases_match_full_design_title_names() -> None:
    op03 = _op03(_op02_missing())
    op04 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op04_continue_retry_repair_complete_action_resolver(
        alr_op03_bodyfree_leak_invalid_source_promotion_scan=op03,
    )
    op05 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op05_operation_state_machine_materialization(
        alr_op04_continue_retry_repair_complete_action_resolver=op04,
    )

    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op04_continue_retry_repair_complete_action_resolver_contract(op04) is True
    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op05_operation_state_machine_materialization_contract(op05) is True
    assert op04["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_ACTION_IF_NO_EXTERNAL_RECEIPT_REF
    assert op05["operation_state_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_STATE_RETRY_OR_START_REQUIRED_REF


def test_alr_op00_to_op05_default_path_stays_bodyfree_retry_without_review_execution() -> None:
    op04 = _op04(_op02_missing())
    op05 = _op05(op04)

    assert tuple(op04["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP04_IMPLEMENTED_STEPS
    assert tuple(op05["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP05_IMPLEMENTED_STEPS
    assert tuple(op04["not_yet_implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP04_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(op05["not_yet_implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP05_NOT_YET_IMPLEMENTED_STEPS
    assert op04["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_ACTION_IF_NO_EXTERNAL_RECEIPT_REF
    assert op05["not_claimed_boundary"]["actual_body_full_packet_generation"] is False
    assert op05["not_claimed_boundary"]["actual_local_human_review_execution"] is False
    assert op05["not_claimed_boundary"]["actual_rows_creation"] is False
    assert op05["not_claimed_boundary"]["actual_disposal_purge_execution"] is False
    assert op05["not_claimed_boundary"]["p8_question_design"] is False
    assert op05["not_claimed_boundary"]["release_decision"] is False


def test_alr_op04_op05_result_memo_exists_and_remains_bodyfree() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP05_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    assert "ALR-OP04: continue / retry / repair / complete action resolver" in text
    assert "ALR-OP05: operation state machine materialization" in text
    assert "actual_local_human_review_execution: false" in text
    assert "p8_question_design: false" in text
    assert "release_decision: false" in text
    assert "raw_input:" not in text
    assert "comment_text:" not in text
