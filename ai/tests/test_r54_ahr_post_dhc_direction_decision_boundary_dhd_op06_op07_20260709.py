# -*- coding: utf-8 -*-
"""DHD R5 OP06/OP07 target tests.

OP06 is the no-touch/no-promotion/no-question-system guard for every stopped
direction decision. OP07 records count-only validation and result-memo plans.
Neither operation may execute commands, claim green, create memo files, call
builders, execute a selected direction, start P8, or claim completion/release.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any, Callable

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
import emlis_ai_p7_r54_ahr_post_dhc_direction_decision_boundary_20260709 as dhd
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op06_op07_20260709 import (
    _op05_waiting,
)
from test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op02_op03_20260709 import (
    _dhc_op08_from_op05_classification,
    _dhc_op08_non_dhr_lane,
    _op02,
    _op03,
)
from test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op04_op05_20260709 import (
    _op04,
    _op05,
    _r11_chain,
    _scan_clear_chain,
)


OP06_PASSED = dhd.P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[0]
OP06_REPAIR = dhd.P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[1]
OP06_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[2]
OP07_MATERIALIZED = dhd.P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[0]
OP07_REPAIR = dhd.P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[1]
OP07_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[2]


def _op06(op05: object) -> dict[str, Any]:
    material = dhd.build_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard(
        op05  # type: ignore[arg-type]
    )
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard_contract(
        material
    )
    return material


def _op07(op06: object) -> dict[str, Any]:
    material = dhd.build_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material(
        op06  # type: ignore[arg-type]
    )
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract(
        material
    )
    return material


def _repair_wait_op05() -> dict[str, Any]:
    op02 = _op02(
        dhc_op08=_dhc_op08_from_op05_classification(_op05_waiting())
    )
    op03 = _op03(op02)
    return _op05(op02, op03, _op04(op02, op03))


def _non_dhr_op05() -> dict[str, Any]:
    op02 = _op02(dhc_op08=_dhc_op08_non_dhr_lane())
    op03 = _op03(op02)
    return _op05(op02, op03, _op04(op02, op03))


def _no_touch_op05() -> dict[str, Any]:
    op08 = _scan_clear_chain()[0]
    poisoned = deepcopy(op08)
    poisoned["release_allowed"] = True
    op02 = _op02(dhc_op08=poisoned)
    op03 = _op03(op02)
    return _op05(op02, op03, _op04(op02, op03))


def _p7_op05() -> dict[str, Any]:
    return _r11_chain()[3]


def _dhr_op05() -> dict[str, Any]:
    return _scan_clear_chain()[5]


def _material_selection_op05() -> dict[str, Any]:
    return _r11_chain(axes=())[3]


DIRECTION_FACTORIES: tuple[Callable[[], dict[str, Any]], ...] = (
    _dhr_op05,
    _p7_op05,
    _material_selection_op05,
    _repair_wait_op05,
    _non_dhr_op05,
    _no_touch_op05,
)


def _assert_no_execution_green_memo_or_release(data: dict[str, Any]) -> None:
    for key in (
        "dhc_builder_called_here",
        "dhc_result_synthesized_here",
        "dhr_op05_runtime_call_started_here",
        "existing_dhr_op05_builder_runtime_called_here",
        "dhr_op06_builder_called_here",
        "dhr_op06_implicit_op05_fallback_used_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p7_readfeel_evaluation_started_here",
        "next_runtime_execution_allowed_here",
        "p8_start_allowed",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "api_changed",
        "db_changed",
        "rn_changed",
        "runtime_changed",
        "response_key_changed",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        assert data[key] is False, key
    for key in (
        "validation_commands_executed_here",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "optional_product_readfeel_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "result_memo_files_created_here",
    ):
        if key in data:
            assert data[key] is False, key
    assert data["body_free"] is True


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, (list, tuple)):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()


@pytest.mark.parametrize("op05_factory", DIRECTION_FACTORIES)
def test_op06_guard_passes_every_sanitized_stopped_direction_without_execution(
    op05_factory: Callable[[], dict[str, Any]],
) -> None:
    op05 = op05_factory()
    material = _op06(op05)

    assert material["dhd_op06_status_ref"] == OP06_PASSED
    assert material["dhd_op06_no_touch_no_promotion_no_question_system_guard_passed"] is True
    assert material["op05_direction_decision_ref"] == op05["direction_decision_ref"]
    assert material["op05_selected_next_design_candidate_ref"] == op05[
        "selected_next_design_candidate_ref"
    ]
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF
    assert material["op06_input_guard_true_field_path_count"] == 0
    _assert_no_execution_green_memo_or_release(material)


def test_op06_no_touch_decision_guard_pass_means_safe_stop_not_problem_resolution() -> None:
    op05 = _no_touch_op05()
    material = _op06(op05)

    assert op05["direction_decision_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5]
    assert material["dhd_op06_status_ref"] == OP06_PASSED
    assert material["op05_direction_decision_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5]
    assert material["op05_selected_next_design_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[5]
    assert material["dhd_op06_does_not_execute_selected_direction"] is True
    _assert_no_execution_green_memo_or_release(material)


@pytest.mark.parametrize("invalid_op05", [None, {}, {"material_id": "invalid", "body_free": True}])
def test_op06_missing_or_invalid_op05_requires_repair_without_builder_call(
    invalid_op05: object,
) -> None:
    material = _op06(invalid_op05)

    assert material["dhd_op06_status_ref"] == OP06_REPAIR
    assert material["op05_contract_valid"] is False
    assert material["dhd_op06_repair_required_for_no_touch_guard_inputs"] is True
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP06_GUARD_INPUTS_REF
    assert material["dhd_op06_does_not_call_dhc_or_dhr_builder"] is True
    _assert_no_execution_green_memo_or_release(material)


@pytest.mark.parametrize(
    "guard_field",
    [
        "dhc_builder_called_here",
        "dhc_result_synthesized_here",
        "dhr_op05_runtime_call_started_here",
        "existing_dhr_op05_builder_runtime_called_here",
        "dhr_op06_builder_called_here",
        "dhr_op06_implicit_op05_fallback_used_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p7_readfeel_evaluation_started_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "api_changed",
        "db_changed",
        "rn_changed",
        "runtime_changed",
        "response_key_changed",
        "json_schema_file_created",
        "p7_complete",
        "release_allowed",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ],
)
def test_op06_blocks_any_execution_promotion_question_system_or_green_claim(
    guard_field: str,
) -> None:
    poisoned = deepcopy(_p7_op05())
    poisoned[guard_field] = True
    material = _op06(poisoned)

    assert material["dhd_op06_status_ref"] == OP06_BLOCKED
    assert material["dhd_op06_blocked_no_touch_no_promotion_no_question_system_guard"] is True
    assert material["op06_input_guard_true_field_path_count"] >= 1
    assert any(guard_field in ref for ref in material["op06_input_guard_true_field_path_refs"])
    assert material.get(guard_field) is not True
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP06_GUARD_REF
    _assert_no_execution_green_memo_or_release(material)


@pytest.mark.parametrize(
    "payload_key",
    ["raw_input", "body", "comment_text", "question_text", "stdout", "stderr", "traceback"],
)
def test_op06_blocks_raw_or_body_payload_without_retaining_value(payload_key: str) -> None:
    poisoned = deepcopy(_p7_op05())
    poisoned[payload_key] = "must_not_be_retained"
    material = _op06(poisoned)

    assert material["dhd_op06_status_ref"] == OP06_BLOCKED
    assert material["op06_input_forbidden_payload_key_path_count"] >= 1
    assert material["op06_input_body_like_value_path_count"] >= 1
    assert payload_key not in material
    assert "must_not_be_retained" not in repr(material)
    _assert_no_execution_green_memo_or_release(material)


def test_op07_materializes_count_only_plan_after_passed_guard() -> None:
    op06 = _op06(_p7_op05())
    material = _op07(op06)

    assert material["dhd_op07_status_ref"] == OP07_MATERIALIZED
    assert material["dhd_op07_validation_plan_result_memo_draft_materialized_stopped"] is True
    assert material["op06_guard_passed"] is True
    assert material["validation_commands_executed_here"] is False
    assert material["validation_plan_is_not_validation_result"] is True
    assert material["validation_plan_does_not_claim_green"] is True
    assert material["result_memo_policy_count_only_bodyfree"] is True
    assert material["result_memo_files_created_here"] is False
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF
    _assert_no_execution_green_memo_or_release(material)


@pytest.mark.parametrize("op05_factory", DIRECTION_FACTORIES)
def test_op07_preserves_every_direction_as_plan_ref_without_executing_it(
    op05_factory: Callable[[], dict[str, Any]],
) -> None:
    op05 = op05_factory()
    material = _op07(_op06(op05))

    assert material["dhd_op07_status_ref"] == OP07_MATERIALIZED
    assert material["op06_upstream_direction_decision_ref"] == op05["direction_decision_ref"]
    assert material["op06_upstream_selected_next_design_candidate_ref"] == op05[
        "selected_next_design_candidate_ref"
    ]
    assert material["dhd_op07_does_not_execute_selected_direction"] is True
    _assert_no_execution_green_memo_or_release(material)


def test_op07_validation_commands_are_refs_only_and_no_green_is_claimed() -> None:
    material = _op07(_op06(_p7_op05()))

    assert material["target_validation_command_refs"] == (
        dhd.P7_R54_AHR_POST_DHC_DHD_OP07_TARGET_VALIDATION_COMMAND_REF,
    )
    assert material["selected_regression_command_refs"] == (
        dhd.P7_R54_AHR_POST_DHC_DHD_OP07_SELECTED_REGRESSION_COMMAND_REF,
    )
    assert material["optional_product_readfeel_regression_command_refs"] == (
        dhd.P7_R54_AHR_POST_DHC_DHD_OP07_OPTIONAL_PRODUCT_READFEEL_REGRESSION_COMMAND_REF,
    )
    assert material["compileall_command_refs"] == (
        dhd.P7_R54_AHR_POST_DHC_DHD_OP07_COMPILEALL_COMMAND_REF,
    )
    assert tuple(material["expected_validation_command_summary_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP07_EXPECTED_VALIDATION_COMMAND_SUMMARY_REFS
    assert material["validation_commands_executed_here"] is False
    assert material["target_validation_green_confirmed_here"] is False
    assert material["selected_regression_green_confirmed_here"] is False
    assert material["optional_product_readfeel_regression_green_confirmed_here"] is False
    assert material["compileall_green_confirmed_here"] is False


def test_op07_test_compile_and_result_memo_refs_are_count_only_expected_material() -> None:
    material = _op07(_op06(_p7_op05()))

    assert tuple(material["target_test_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS
    assert tuple(material["selected_regression_test_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R5_SELECTED_REGRESSION_TEST_REF_REFS
    assert tuple(material["optional_product_readfeel_regression_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
    assert tuple(material["compileall_target_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS
    assert tuple(material["result_memo_expected_file_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R5_RESULT_MEMO_EXPECTED_FILE_REFS
    assert tuple(material["next_work_decision_memo_draft_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R5_NEXT_WORK_DECISION_MEMO_DRAFT_REFS
    assert material["result_memo_files_created_here"] is False
    for field, count_field in (
        ("target_test_ref_refs", "target_test_ref_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count"),
        (
            "optional_product_readfeel_regression_ref_refs",
            "optional_product_readfeel_regression_ref_ref_count",
        ),
        ("compileall_target_ref_refs", "compileall_target_ref_ref_count"),
        ("result_memo_expected_file_refs", "result_memo_expected_file_ref_count"),
        ("next_work_decision_memo_draft_refs", "next_work_decision_memo_draft_ref_count"),
    ):
        assert material[count_field] == len(material[field])


def test_op07_keeps_backend_rn_and_real_device_state_explicitly_unconfirmed() -> None:
    material = _op07(_op06(_p7_op05()))

    assert material["full_backend_suite_green_confirmed"] is False
    assert material["full_backend_suite_green_claimed_here"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_contract_green_claimed_here"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    assert material["dhd_op07_keeps_full_backend_suite_unconfirmed"] is True
    assert material["dhd_op07_keeps_rn_contract_unconfirmed"] is True
    assert material["dhd_op07_keeps_rn_real_device_unconfirmed"] is True


@pytest.mark.parametrize("invalid_op06", [None, {}, {"material_id": "invalid", "body_free": True}])
def test_op07_missing_or_invalid_op06_requires_repair_without_validation_execution(
    invalid_op06: object,
) -> None:
    material = _op07(invalid_op06)

    assert material["dhd_op07_status_ref"] == OP07_REPAIR
    assert material["op06_contract_valid"] is False
    assert material["dhd_op07_repair_required_for_validation_plan_inputs"] is True
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP07_PLAN_INPUTS_REF
    assert material["validation_commands_executed_here"] is False
    assert material["result_memo_files_created_here"] is False


def test_op07_repair_op06_stays_repair_and_does_not_claim_plan_result() -> None:
    op06 = _op06(None)
    material = _op07(op06)

    assert op06["dhd_op06_status_ref"] == OP06_REPAIR
    assert material["dhd_op07_status_ref"] == OP07_REPAIR
    assert material["op06_contract_valid"] is True
    assert material["op06_guard_passed"] is False
    assert material["dhd_op07_validation_plan_result_memo_draft_materialized_stopped"] is False
    _assert_no_execution_green_memo_or_release(material)


def test_op07_sanitized_blocked_op06_becomes_repair_not_false_guard_pass() -> None:
    poisoned = deepcopy(_p7_op05())
    poisoned["release_allowed"] = True
    op06 = _op06(poisoned)
    material = _op07(op06)

    assert op06["dhd_op06_status_ref"] == OP06_BLOCKED
    assert material["dhd_op07_status_ref"] == OP07_REPAIR
    assert material["op06_blocked"] is True
    assert material["op06_guard_passed"] is False
    assert material["result_memo_files_created_here"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("question_text", "must_not_be_retained"),
        ("target_validation_green_confirmed_here", True),
        ("compileall_green_confirmed_here", True),
        ("full_backend_suite_green_claimed_here", True),
        ("release_allowed", True),
    ],
)
def test_op07_blocks_raw_or_green_claim_in_input_without_retaining_or_promoting(
    field: str, value: object
) -> None:
    poisoned = deepcopy(_op06(_p7_op05()))
    poisoned[field] = value
    material = _op07(poisoned)

    assert material["dhd_op07_status_ref"] == OP07_BLOCKED
    assert material["dhd_op07_blocked_validation_plan_bodyfree_leak_promotion_or_green_claim"] is True
    assert (
        material["op07_input_forbidden_payload_key_path_count"]
        + material["op07_input_guard_true_field_path_count"]
    ) >= 1
    assert "must_not_be_retained" not in repr(material)
    assert material.get(field) is not True
    _assert_no_execution_green_memo_or_release(material)


def test_op06_op07_do_not_call_upstream_downstream_builders_or_execute_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    op05 = _scan_clear_chain()[5]

    def explode(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("DHD R5 must not call builders or validation execution")

    monkeypatch.setattr(dhc, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF, explode)
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF, explode
    )
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF, explode
    )

    op06 = _op06(op05)
    op07 = _op07(op06)

    assert op06["dhd_op06_does_not_call_dhc_or_dhr_builder"] is True
    assert op07["dhd_op07_does_not_call_dhc_or_dhr_builder"] is True
    assert op07["dhd_op07_does_not_execute_validation_commands"] is True
    assert op07["validation_commands_executed_here"] is False


@pytest.mark.parametrize(
    ("builder", "assert_contract", "field", "bad_value"),
    [
        (
            lambda: _op06(_p7_op05()),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard_contract,
            "dhr_op06_builder_called_here",
            True,
        ),
        (
            lambda: _op06(_p7_op05()),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard_contract,
            "p8_question_design_started",
            True,
        ),
        (
            lambda: _op07(_op06(_p7_op05())),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract,
            "validation_commands_executed_here",
            True,
        ),
        (
            lambda: _op07(_op06(_p7_op05())),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract,
            "target_validation_green_confirmed_here",
            True,
        ),
        (
            lambda: _op07(_op06(_p7_op05())),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract,
            "result_memo_files_created_here",
            True,
        ),
        (
            lambda: _op07(_op06(_p7_op05())),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract,
            "p7_complete",
            True,
        ),
        (
            lambda: _op07(_op06(_p7_op05())),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract,
            "release_allowed",
            True,
        ),
    ],
)
def test_op06_op07_contracts_reject_execution_green_memo_or_release_mutations(
    builder: Callable[[], dict[str, Any]],
    assert_contract: Callable[[dict[str, Any]], bool],
    field: str,
    bad_value: object,
) -> None:
    material = deepcopy(builder())
    material[field] = bad_value

    with pytest.raises(ValueError):
        assert_contract(material)


def test_op06_op07_exact_fields_steps_counts_and_r6_stop_are_stable() -> None:
    op06 = _op06(_p7_op05())
    op07 = _op07(op06)

    assert set(op06) == set(dhd.P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FIELD_REFS)
    assert set(op07) == set(dhd.P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FIELD_REFS)
    assert tuple(op06["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP06_IMPLEMENTED_STEPS
    assert tuple(op07["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP07_IMPLEMENTED_STEPS
    assert tuple(op07["not_yet_implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP07_NOT_YET_IMPLEMENTED_STEPS
    assert op07["not_yet_implemented_steps"] == [dhd.P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF]
    assert op07["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF
    for material, pairs in (
        (
            op06,
            (
                ("op06_input_guard_true_field_path_refs", "op06_input_guard_true_field_path_count"),
                ("dhd_op06_reason_refs", "dhd_op06_reason_ref_count"),
                ("dhd_op06_blocker_refs", "dhd_op06_blocker_ref_count"),
            ),
        ),
        (
            op07,
            (
                ("expected_validation_command_summary_refs", "expected_validation_command_summary_ref_count"),
                ("dhd_op07_reason_refs", "dhd_op07_reason_ref_count"),
                ("dhd_op07_blocker_refs", "dhd_op07_blocker_ref_count"),
            ),
        ),
    ):
        for field, count_field in pairs:
            assert material[count_field] == len(material[field])


def test_op06_op07_outputs_never_include_raw_payload_comment_question_or_traceback_keys() -> None:
    op06 = _op06(_dhr_op05())
    op07 = _op07(op06)
    forbidden = {
        "raw_input",
        "raw_answer",
        "raw_evidence",
        "body",
        "comment_text",
        "question_text",
        "stdout",
        "stderr",
        "traceback",
    }

    assert not (_collect_keys(op06) & forbidden)
    assert not (_collect_keys(op07) & forbidden)
    assert op07["raw_pytest_stdout_included"] is False
    assert op07["raw_pytest_stderr_included"] is False
    assert op07["raw_traceback_included"] is False
    assert op07["raw_body_included"] is False
    assert op07["comment_text_body_included"] is False
    assert op07["question_text_body_included"] is False
