# -*- coding: utf-8 -*-
"""R54-AHR Post-RSR16 DRI-OP12 result memo / selected regression closure tests."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_op05_20260705 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_op11_20260705 import (
    _op10_ready,
)

_CHANGED_FILE_REFS = [
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705.py",
    "mashos-api/ai/tests/test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_20260705.py",
    "mashos-api/ai/tests/R54_AHR_PostRSR16_DHRActualSourceClaimReintake_DRI_OP00_OP12_Result_20260705.md",
]


def _target_summary(passed_count: int = 236, *, failed_count: int = 0, green: bool = True) -> dict[str, object]:
    return {
        "summary_ref": "dri_op00_op12_split_target_236_passed",
        "passed_count": passed_count,
        "failed_count": failed_count,
        "error_count": 0,
        "target_tests_all_required_green": green,
        "body_free": True,
    }


def _selected_regression_summary(
    passed_count: int = 477,
    *,
    failed_count: int = 0,
    green: bool = True,
) -> dict[str, object]:
    return {
        "summary_ref": "rsr_dhr_selected_regression_split_477_passed",
        "passed_count": passed_count,
        "failed_count": failed_count,
        "error_count": 0,
        "selected_regression_all_required_green": green,
        "rsr_selected_regression_passed_count": 338,
        "dhr_selected_regression_passed_count": 139,
        "body_free": True,
    }


def _compileall_summary(*, ok: bool = True) -> dict[str, object]:
    return {
        "summary_ref": "services_ai_inference_compileall_ok" if ok else "services_ai_inference_compileall_failed",
        "services_ai_inference_compileall_ok": ok,
        "body_free": True,
    }


@lru_cache(maxsize=1)
def _cached_op10_ready() -> dict[str, object]:
    return _op10_ready()


def _op11_clear(changed_file_refs: list[str] | None = None) -> dict[str, object]:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard(
        dri_op10_deterministic_branch_resolver=_cached_op10_ready(),
        changed_file_refs=changed_file_refs or _CHANGED_FILE_REFS,
    )
    assert material["dri_op11_no_touch_guard_clear"] is True
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(material) is True
    return material


@lru_cache(maxsize=1)
def _cached_op12_closed() -> dict[str, object]:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        target_tests_summary=_target_summary(),
        selected_regression_summary=_selected_regression_summary(),
        compileall_summary=_compileall_summary(),
        changed_file_refs=_CHANGED_FILE_REFS,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    return material


def _op12_closed() -> dict[str, object]:
    return deepcopy(_cached_op12_closed())


def test_dri_op12_closes_bodyfree_result_memo_tests_selected_regression_without_downstream_execution() -> None:
    material = _op12_closed()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP12_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF
    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF
    assert material["dri_op12_result_memo_bodyfree_closed"] is True
    assert material["target_tests_all_required_green"] is True
    assert material["selected_regression_all_required_green"] is True
    assert material["services_ai_inference_compileall_ok"] is True
    assert material["target_tests_passed_count"] == 236
    assert material["selected_regression_passed_count"] == 477
    assert material["rsr_selected_regression_passed_count"] == 338
    assert material["dhr_selected_regression_passed_count"] == 139
    assert material["final_changed_file_refs_bodyfree_scoped"] is True
    assert material["rn_no_touch_grep_match_refs"] == []
    assert material["result_memo_input_forbidden_payload_key_path_refs"] == []
    assert material["result_memo_input_body_like_value_path_refs"] == []
    assert material["result_memo_input_promotion_claim_refs"] == []
    assert material["dri_op12_blocker_refs"] == []
    assert material["op10_ready_for_dhr_material"] is True
    assert material["op11_no_touch_guard_clear"] is True
    assert material["selected_dri_next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF
    assert material["next_required_step"] == material["selected_dri_next_required_step"]
    assert material["implemented_steps"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP12_IMPLEMENTED_STEPS)
    assert material["implemented_steps"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_STEP_REFS)
    assert material["not_yet_implemented_steps"] == []
    assert material["dhr_op04_called_by_dri_op12"] is False
    assert material["dhr_actual_source_claim_confirmed_by_dri_op12"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op12"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op12_waits_when_target_summary_is_missing_without_promoting() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        selected_regression_summary=_selected_regression_summary(),
        compileall_summary=_compileall_summary(),
        changed_file_refs=_CHANGED_FILE_REFS,
    )

    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF
    assert material["dri_op12_waiting_for_op11_or_verification_summaries"] is True
    assert "target_tests_summary_missing" in material["dri_op12_blocker_refs"]
    assert material["dri_op12_result_memo_bodyfree_closed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP12_VERIFICATION_SUMMARIES_REF
    assert material["dhr_op04_called_by_dri_op12"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op12_repairs_non_green_selected_regression_summary_without_dhr_or_p8_promotion() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        target_tests_summary=_target_summary(),
        selected_regression_summary=_selected_regression_summary(failed_count=1, green=False),
        compileall_summary=_compileall_summary(),
        changed_file_refs=_CHANGED_FILE_REFS,
    )

    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF
    assert material["dri_op12_repair_required"] is True
    assert "selected_regression_summary_not_green" in material["dri_op12_blocker_refs"]
    assert material["dri_op12_result_memo_bodyfree_closed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP12_RESULT_MEMO_REF
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op12"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op12_repairs_when_compileall_is_not_ok_without_claiming_full_backend_green() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        target_tests_summary=_target_summary(),
        selected_regression_summary=_selected_regression_summary(),
        compileall_summary=_compileall_summary(ok=False),
        changed_file_refs=_CHANGED_FILE_REFS,
    )

    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF
    assert "services_ai_inference_compileall_not_ok" in material["dri_op12_blocker_refs"]
    assert material["services_ai_inference_compileall_ok"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op12_blocks_rn_no_touch_grep_matches_before_result_memo_closure() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        target_tests_summary=_target_summary(),
        selected_regression_summary=_selected_regression_summary(),
        compileall_summary=_compileall_summary(),
        changed_file_refs=_CHANGED_FILE_REFS,
        rn_no_touch_grep_match_refs=["Cocolon/src/screens/P8QuestionSurface.tsx:DRI-OP12"],
    )

    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF
    assert material["dri_op12_bodyfree_leak_or_promotion_blocked"] is True
    assert "rn_no_touch_grep_match_refs_present_before_result_memo_closure" in material["result_memo_input_promotion_claim_refs"]
    assert material["rn_no_touch_grep_match_refs"] == ["Cocolon/src/screens/P8QuestionSurface.tsx:DRI-OP12"]
    assert material["dhr_op04_called_by_dri_op12"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op12_blocks_changed_file_refs_outside_helper_tests_result_memo_scope() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        target_tests_summary=_target_summary(),
        selected_regression_summary=_selected_regression_summary(),
        compileall_summary=_compileall_summary(),
        changed_file_refs=[*_CHANGED_FILE_REFS, "Cocolon/src/screens/P8QuestionSurface.tsx"],
    )

    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF
    assert material["final_changed_file_refs_bodyfree_scoped"] is False
    assert "changed_file_refs_outside_helper_tests_result_memo_scope" in material["result_memo_input_promotion_claim_refs"]
    assert material["dhr_op04_called_by_dri_op12"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op12_blocks_question_text_in_input_summary_bodyfree_scan() -> None:
    target = _target_summary()
    target["question_text"] = "do not leak this OP12 question body"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        target_tests_summary=target,
        selected_regression_summary=_selected_regression_summary(),
        compileall_summary=_compileall_summary(),
        changed_file_refs=_CHANGED_FILE_REFS,
    )

    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF
    assert "dri_op12_inputs.target_tests_summary.question_text" in material["result_memo_input_forbidden_payload_key_path_refs"]
    assert "dri_op12_inputs.target_tests_summary.question_text" in material["result_memo_input_body_like_value_path_refs"]
    assert "do not leak this OP12 question body" not in repr(material)
    assert material["dhr_op04_called_by_dri_op12"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "wrong.schema"),
        ("dri_op12_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF),
        ("dri_op12_result_memo_bodyfree_closed", False),
        ("target_tests_all_required_green", False),
        ("selected_regression_all_required_green", False),
        ("services_ai_inference_compileall_ok", False),
        ("downstream_auto_execution_allowed", True),
        ("dhr_op04_called_by_dri_op12", True),
        ("dhr_actual_source_claim_confirmed_by_dri_op12", True),
        ("dhr_actual_source_claim_reintake_executed_by_dri_op12", True),
        ("p8_question_design_started", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op12_contract_rejects_result_memo_or_downstream_mutations(field: str, bad_value: object) -> None:
    material = _op12_closed()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(material)


def test_dri_op12_full_title_aliases_match_short_builders_and_asserts() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_memo_tests_selected_regression_closure(
        dri_op11_no_touch_selected_regression_guard=_op11_clear(),
        target_tests_summary=_target_summary(),
        selected_regression_summary=_selected_regression_summary(),
        compileall_summary=_compileall_summary(),
        changed_file_refs=_CHANGED_FILE_REFS,
    )

    assert material["dri_op12_result_memo_bodyfree_closed"] is True
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_memo_tests_selected_regression_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
