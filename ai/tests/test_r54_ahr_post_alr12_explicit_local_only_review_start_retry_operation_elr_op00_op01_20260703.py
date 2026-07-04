# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr

_CLOSED_RETRY_ALR_OP12_CACHE: dict[str, object] | None = None


def _alr_op12_pass_status_refs() -> dict[str, str]:
    return {
        key: alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF
        for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS
    }


def _alr_op12_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS}


def _alr_op12_regression_pass_status_refs() -> dict[str, str]:
    return {
        key: alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF
        for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS
    }


def _alr_op12_regression_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS}


def _closed_retry_alr_op12() -> dict[str, object]:
    global _CLOSED_RETRY_ALR_OP12_CACHE
    if _CLOSED_RETRY_ALR_OP12_CACHE is None:
        material = alr.build_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure(
            target_test_result_status_refs=_alr_op12_pass_status_refs(),
            target_test_result_count_refs=_alr_op12_pass_count_refs(),
            selected_regression_result_status_refs=_alr_op12_regression_pass_status_refs(),
            selected_regression_result_count_refs=_alr_op12_regression_pass_count_refs(),
            compileall_result_status_ref=alr.P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF,
            compileall_result_count_ref="passed",
        )
        assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
        assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
        assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF
        assert alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(material) is True
        _CLOSED_RETRY_ALR_OP12_CACHE = material
    return deepcopy(_CLOSED_RETRY_ALR_OP12_CACHE)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in elr.P7_R54_AHR_POST_ALR12_ELR_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_alr12_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_elr_op00_refreezes_scope_no_touch_no_promotion_after_alr_op12() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP00_SCHEMA_VERSION
    assert material["phase"] == elr.P7_R54_AHR_POST_ALR12_ELR_PHASE
    assert material["source_mode"] == elr.P7_R54_AHR_POST_ALR12_ELR_SOURCE_MODE
    assert material["selected_stage_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_SELECTED_STAGE_REF
    assert material["selected_step_prefix_ref"] == "ELR-OP"
    assert material["expected_current_alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
    assert material["expected_current_alr_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    assert material["expected_current_alr_next_required_step_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF
    assert material["current_default_next_required_step_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP02_STEP_REF
    assert material["elr_op00_scope_confirmed"] is True
    assert material["elr_op00_no_touch_boundary_confirmed"] is True
    assert material["elr_op00_no_promotion_boundary_confirmed"] is True
    assert material["elr_op00_does_not_intake_alr_op12_result_memo"] is True
    assert material["elr_op00_does_not_grant_explicit_local_only_allow"] is True
    assert material["elr_op00_does_not_generate_body_full_packet"] is True
    assert material["elr_op00_does_not_run_actual_local_human_review"] is True
    assert tuple(material["implemented_steps"]) == elr.P7_R54_AHR_POST_ALR12_ELR_OP00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == elr.P7_R54_AHR_POST_ALR12_ELR_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("body_free", False),
        ("git_checked", True),
        ("elr_op00_no_touch_boundary_confirmed", False),
        ("elr_op00_no_promotion_boundary_confirmed", False),
        ("elr_op00_does_not_start_p8_p6_r52_or_release", False),
        ("explicit_local_only_allow_granted_by_helper", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", elr.P7_R54_AHR_POST_ALR12_ELR_OP02_STEP_REF),
    ],
)
def test_elr_op00_contract_rejects_scope_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_elr_op00_contract_rejects_no_touch_marker_mutation() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze()
    material["post_alr12_no_touch_contract"]["p8_question_api_created"] = True

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_elr_op00_contract_rejects_forbidden_top_level_payload_key() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze()
    material["raw_input"] = "must never pass"

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_elr_op01_accepts_current_alr_op12_retry_or_start_selected_action_and_moves_to_explicit_allow_gate() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_SCHEMA_VERSION
    assert material["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_ACCEPTED_RETRY_OR_START_REQUIRED_REF
    assert material["elr_op01_ready"] is True
    assert material["alr_op12_contract_valid"] is True
    assert material["alr_op12_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
    assert material["alr_op12_result_memo_bodyfree_closed"] is True
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    assert material["alr_op12_next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF
    assert material["retry_or_start_required"] is True
    assert material["explicit_local_only_allow_required"] is True
    assert material["body_full_packet_generation_allowed_without_allow"] is False
    assert material["actual_review_execution_allowed_without_allow"] is False
    assert material["elr_op01_route_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_ROUTE_EXPLICIT_LOCAL_ONLY_ALLOW_GATE_REQUIRED_REF
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP02_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op01_preserves_alr_op12_not_executed_boundaries() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
    )

    assert material["alr_op12_not_executed_boundary_preserves_actual_review_unexecuted"] is True
    assert material["alr_op12_not_executed_boundary_preserves_p8_unstarted"] is True
    assert material["alr_op12_not_executed_boundary_preserves_release_undecided"] is True
    assert material["actual_body_full_packet_generation_run_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True


def test_elr_op01_missing_alr_op12_result_memo_goes_to_repair_without_claiming_review() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake()

    assert material["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert material["elr_op01_ready"] is False
    assert material["alr_op12_result_memo_present"] is False
    assert material["alr_op12_contract_valid"] is False
    assert material["elr_op01_route_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF
    assert "elr_op01_alr_op12_result_memo_missing" in material["elr_op01_blocker_refs"]
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert material["actual_local_human_review_executed_here"] is False
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op01_unclosed_alr_op12_result_memo_goes_to_repair() -> None:
    alr_op12 = _closed_retry_alr_op12()
    alr_op12["alr_op12_status_ref"] = alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=alr_op12,
    )

    assert material["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert "elr_op01_alr_op12_contract_invalid" in material["elr_op01_blocker_refs"]
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True


def test_elr_op01_forbidden_payload_in_alr_op12_goes_to_repair_without_leaking_body_value() -> None:
    alr_op12 = _closed_retry_alr_op12()
    alr_op12["raw_input"] = "this body must not appear in ELR output"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=alr_op12,
    )

    assert material["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert material["elr_op01_route_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF
    assert material["alr_op12_forbidden_payload_key_path_count"] == 1
    assert material["alr_op12_forbidden_payload_key_paths"] == ["alr_op12.raw_input"]
    assert "this body must not appear" not in repr(material)
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op01_promotion_claim_in_alr_op12_goes_to_repair_without_downstream_execution() -> None:
    alr_op12 = _closed_retry_alr_op12()
    alr_op12["p8_start_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=alr_op12,
    )

    assert material["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert "p8_start_allowed" in material["alr_op12_promotion_claim_refs"]
    assert material["p8_start_allowed"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op01_invalid_op00_goes_to_repair() -> None:
    op00 = elr.build_p7_r54_ahr_post_alr12_elr_op00_scope_no_touch_no_promotion_refreeze()
    op00["release_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        scope_no_touch_no_promotion_refreeze=op00,
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
    )

    assert material["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_INVALID_OR_MISSING_REF
    assert "elr_op01_op00_scope_no_touch_no_promotion_refreeze_invalid" in material["elr_op01_blocker_refs"]
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material) is True


def test_elr_op01_contract_rejects_alr_not_executed_boundary_mutation() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
    )
    material["alr_op12_not_executed_boundary_preserves_actual_review_unexecuted"] = False

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material)


def test_elr_op01_contract_rejects_explicit_allow_or_actual_review_promotion_mutation() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
    )
    material["explicit_local_only_allow_granted_by_helper"] = True

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material)

    material = elr.build_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
    )
    material["actual_review_execution_allowed_without_allow"] = True

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op01_alr_op12_result_memo_selected_action_intake_contract(material)


def test_elr_op00_op01_alias_builders_and_contracts_match_canonical_functions() -> None:
    op00 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op00_scope_no_touch_no_promotion_refreeze()
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op00_scope_no_touch_no_promotion_refreeze_contract(op00) is True

    op01 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op01_alr_op12_result_memo_selected_action_intake(
        alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure=_closed_retry_alr_op12(),
    )
    assert op01["elr_op01_intake_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_ACCEPTED_RETRY_OR_START_REQUIRED_REF
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op01_alr_op12_result_memo_selected_action_intake_contract(op01) is True


def test_elr_op00_op01_result_memo_is_bodyfree_and_limited_to_current_scope() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP01_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    for heading in (
        "## 1. Implementation scope",
        "## 2. Changed files",
        "## 3. ELR-OP00",
        "## 4. ELR-OP01",
        "## 5. Test results",
        "## 6. Not claimed",
        "## 7. Next required step",
    ):
        assert heading in text
    assert "ELR-OP02" in text
    assert "not implemented" in text
    forbidden_literals = (
        "raw_input:",
        "comment_text:",
        "question_text:",
        "draft_question_text:",
        "terminal output body",
    )
    for literal in forbidden_literals:
        assert literal not in text
