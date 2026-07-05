# -*- coding: utf-8 -*-
"""R54-AHR Post-DRI / DHR-OP04 manual re-intake MRB-OP08 tests."""

from __future__ import annotations

from pathlib import Path
import sys

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_op03_20260705 import (
    _mrb_op01_ready,
)
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_op05_20260705 import (
    _mrb_op02_ready,
    _mrb_op03_ready,
    _mrb_op04_ready,
)
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
    _op06_from_op05,
    _op07_ready,
)


def _validation_summary(*, combined_run_status_ref: str = "not_run", combined_green: bool = False) -> dict[str, object]:
    return {
        "summary_kind": "mrb_op08_validation_summary_bodyfree",
        "mrb_target_tests_status_ref": "recorded_split_targets_bodyfree",
        "dri_selected_regression_status_ref": "recorded_selected_regression_bodyfree",
        "dhr_selected_regression_status_ref": "recorded_selected_regression_bodyfree",
        "compileall_status_ref": "passed",
        "combined_run_status_ref": combined_run_status_ref,
        "combined_mrb_dri_dhr_green_confirmed": combined_green,
        "full_backend_suite_green_confirmed": False,
        "full_backend_suite_status_ref": "not_run",
        "body_free": True,
    }


def _result_memo(branch_ref: str = "mrb_branch_recorded_bodyfree") -> dict[str, object]:
    return {
        "memo_kind": "mrb_op08_bodyfree_result_memo",
        "mrb_selected_branch_ref": branch_ref,
        "dhr_op05_called_here": False,
        "dhr_op06_called_here": False,
        "dmd_execution_started_here": False,
        "r52_actual_execution_started_here": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "combined_green_claimed": False,
        "body_free": True,
    }


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object], *, allow_confirmed: bool = False) -> None:
    assert material["source_mode"] == mrb.P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["mrb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    allowed_true = {"actual_source_claim_confirmed_for_downstream_handoff"} if allow_confirmed else set()
    for key in mrb.P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS:
        if key not in allowed_true:
            assert material[key] is False, key


def _op08_from_op05(op05: dict[str, object], **overrides: object) -> dict[str, object]:
    op06 = _op06_from_op05(op05)
    kwargs = {
        "mrb_op01_dri_result_memo_op10_branch_intake": _mrb_op01_ready(),
        "mrb_op02_dri_op09_adapter_candidate_extraction_and_scan": _mrb_op02_ready(),
        "mrb_op03_dhr_op03_ready_material_intake": _mrb_op03_ready(),
        "mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope": _mrb_op04_ready(),
        "mrb_op05_explicit_manual_dhr_op04_call_and_result_capture": op05,
        "mrb_op06_dhr_op04_result_classifier_stop_boundary": op06,
        "mrb_op07_no_touch_selected_regression_guard": _op07_ready(),
        "validation_summary_bodyfree": _validation_summary(),
        "result_memo_bodyfree": _result_memo(op06["mrb_branch_ref"]),
    }
    kwargs.update(overrides)
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure(**kwargs)
    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP08_REQUIRED_FIELD_REFS)
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure_contract(material) is True
    return material


def test_mrb_op08_result_memo_closes_bodyfree_when_targets_and_selected_regression_recorded() -> None:
    material = _op08_from_op05(_op05_confirmed())

    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF
    assert material["mrb_op08_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
    assert material["bodyfree_result_memo_closure_status_ref"] == material["mrb_op08_status_ref"]
    assert material["mrb_op08_closed_bodyfree_stopped"] is True
    assert material["validation_summary_bodyfree_accepted"] is True
    assert material["result_memo_bodyfree_accepted"] is True
    assert material["op06_contract_valid"] is True
    assert material["op07_contract_valid"] is True
    assert material["op07_ready_for_op08"] is True
    assert material["validation_command_summary_refs"] == list(mrb.P7_R54_AHR_POST_DRI_MRB_OP08_VALIDATION_COMMAND_SUMMARY_REFS)
    assert material["combined_run_status_ref"] == "not_run"
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["combined_mrb_dri_dhr_green_confirmed"] is False
    assert material["combined_green_claim_not_made_when_not_passed"] is True
    assert material["next_required_step"] == material["op06_mrb_next_required_step"]
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_confirmed=True)


def test_mrb_op08_records_dhr_op04_result_but_not_dhr_op05_execution() -> None:
    material = _op08_from_op05(_op05_not_confirmed())

    assert material["mrb_op08_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
    assert material["dhr_op04_manual_call_performed_by_mrb"] is True
    assert material["op05_dhr_op04_manual_call_performed_by_mrb"] is True
    assert material["op06_dhr_op04_result_captured"] is True
    assert material["dhr_op04_result_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF
    assert material["mrb_selected_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_op05_not_called"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert material["result_memo_bodyfree_ref"]["dhr_op05_called_here"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op08_keeps_p8_p7_release_false_for_all_dhr_op04_result_branches() -> None:
    for op05 in (_op05_confirmed(), _op05_not_confirmed(), _op05_waiting_result(), _op05_invalid_result()):
        material = _op08_from_op05(op05)
        assert material["mrb_op08_closed_bodyfree_stopped"] is True
        assert material["dhr_op05_not_called"] is True
        assert material["dmd_r52_not_executed"] is True
        assert material["p5_p6_p8_p7_release_not_started"] is True
        assert material["p5_final_allowed"] is False
        assert material["p6_start_allowed"] is False
        assert material["p8_start_allowed"] is False
        assert material["p8_question_design_started"] is False
        assert material["p8_question_implementation_started"] is False
        assert material["p7_complete"] is False
        assert material["release_allowed"] is False
        assert material["mrb_op08_does_not_materialize_p8_question_spec"] is True


def test_mrb_op08_rejects_result_memo_with_raw_body_or_question_text() -> None:
    material = _op08_from_op05(
        _op05_confirmed(),
        result_memo_bodyfree={
            "question_text": "sensitive body must never be copied",
            "body_free": True,
        },
    )

    assert material["mrb_op08_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["mrb_op08_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert material["result_memo_bodyfree_accepted"] is False
    assert material["result_memo_forbidden_payload_key_path_refs"] == ["mrb_op08.result_memo.question_text"]
    assert material["result_memo_body_like_value_path_refs"] == ["mrb_op08.result_memo.question_text"]
    assert material["result_memo_bodyfree_ref"] == {}
    assert "sensitive body must never be copied" not in repr(material)
    assert material["dhr_op05_called_here"] is False
    assert material["p8_start_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_confirmed=True)


def test_mrb_op08_does_not_claim_full_backend_suite_green_when_not_run_or_timeout() -> None:
    not_run_material = _op08_from_op05(
        _op05_confirmed(),
        validation_summary_bodyfree=_validation_summary(
            combined_run_status_ref="not_run",
            combined_green=True,
        ),
    )
    assert not_run_material["combined_run_status_ref"] == "not_run"
    assert not_run_material["full_backend_suite_green_confirmed"] is False
    assert not_run_material["combined_mrb_dri_dhr_green_confirmed"] is False
    assert not_run_material["combined_green_claim_not_made_when_not_passed"] is True

    timeout_material = _op08_from_op05(
        _op05_confirmed(),
        validation_summary_bodyfree=_validation_summary(
            combined_run_status_ref="timeout",
            combined_green=True,
        ),
    )
    assert timeout_material["combined_run_status_ref"] == "timeout"
    assert timeout_material["full_backend_suite_green_confirmed"] is False
    assert timeout_material["combined_mrb_dri_dhr_green_confirmed"] is False
    assert timeout_material["combined_green_claim_not_made_when_not_passed"] is True


def test_mrb_op08_waits_when_validation_or_result_memo_is_missing() -> None:
    op05 = _op05_confirmed()
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure(
        mrb_op05_explicit_manual_dhr_op04_call_and_result_capture=op05,
        mrb_op06_dhr_op04_result_classifier_stop_boundary=_op06_from_op05(op05),
        mrb_op07_no_touch_selected_regression_guard=_op07_ready(),
        validation_summary_bodyfree=_validation_summary(),
    )

    assert material["mrb_op08_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_WAITING_FOR_OP06_OP07_OR_VALIDATION_REF
    assert material["mrb_op08_waiting_for_op06_op07_or_validation"] is True
    assert material["result_memo_bodyfree_present"] is False
    assert material["result_memo_bodyfree_accepted"] is False
    assert "result_memo_bodyfree_missing" in material["mrb_op08_blocker_refs"]
    assert material["dhr_op05_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure_contract(material) is True


def test_mrb_op08_full_title_aliases_match_canonical_builders() -> None:
    op05 = _op05_confirmed()
    kwargs = {
        "mrb_op01_dri_result_memo_op10_branch_intake": _mrb_op01_ready(),
        "mrb_op02_dri_op09_adapter_candidate_extraction_and_scan": _mrb_op02_ready(),
        "mrb_op03_dhr_op03_ready_material_intake": _mrb_op03_ready(),
        "mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope": _mrb_op04_ready(),
        "mrb_op05_explicit_manual_dhr_op04_call_and_result_capture": op05,
        "mrb_op06_dhr_op04_result_classifier_stop_boundary": _op06_from_op05(op05),
        "mrb_op07_no_touch_selected_regression_guard": _op07_ready(),
        "validation_summary_bodyfree": _validation_summary(),
        "result_memo_bodyfree": _result_memo(),
    }
    canonical = mrb.build_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure(**kwargs)
    alias = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_bodyfree_result_memo_closure(**kwargs)
    assert canonical == alias
