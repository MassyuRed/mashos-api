# -*- coding: utf-8 -*-
"""DHD R6 OP08 stopped next-design decision closure target tests.

OP08 closes exactly one body-free next-design direction selected by OP05 and
carried through passed OP06 / materialized OP07.  It never executes that
direction, calls a DHC/DHR builder, runs validation, creates result memos,
starts P8, or claims P7 completion/release.
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
from test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op06_op07_20260709 import (
    DIRECTION_FACTORIES,
    _assert_no_execution_green_memo_or_release,
    _dhr_op05,
    _no_touch_op05,
    _op06,
    _op07,
    _p7_op05,
)


OP08_CLOSURE_FLAG_REFS: tuple[str, ...] = (
    "dhd_op08_dhr_op06_consideration_design_closed_stopped",
    "dhd_op08_p7_readfeel_reconnection_design_closed_stopped",
    "dhd_op08_explicit_current_dhc_material_selection_required_closed_stopped",
    "dhd_op08_repair_or_wait_boundary_closed_stopped",
    "dhd_op08_non_dhr_lane_route_preserved_closed_stopped",
    "dhd_op08_blocked_no_touch_no_promotion",
)


def _op08(op07: object, op05: object = None) -> dict[str, Any]:
    material = dhd.build_p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure(
        op07,  # type: ignore[arg-type]
        optional_op05_direction_comparator=op05,  # type: ignore[arg-type]
    )
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure_contract(
        material
    )
    return material


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


def _assert_op08_stopped_without_execution(material: dict[str, Any]) -> None:
    _assert_no_execution_green_memo_or_release(material)
    for key in (
        "op07_validation_commands_executed_here",
        "op07_result_memo_files_created_here",
        "validation_commands_executed_here",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "optional_product_readfeel_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "result_memo_files_created_here",
        "next_runtime_execution_allowed_here",
    ):
        assert material[key] is False, key
    for key in (
        "dhd_op08_closed_stopped",
        "closure_is_not_validation_result",
        "closure_does_not_claim_green",
        "dhd_op08_does_not_call_dhc_or_dhr_builder",
        "dhd_op08_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op08_does_not_execute_selected_direction",
        "dhd_op08_does_not_materialize_dhr_op07_or_execute_dmd_r52",
        "dhd_op08_does_not_start_actual_review_or_create_rows",
        "dhd_op08_does_not_create_question_need_observation_rows",
        "dhd_op08_does_not_start_p8_or_materialize_question_text",
        "dhd_op08_does_not_change_api_db_rn_runtime_response_key",
        "dhd_op08_does_not_create_json_schema_file",
        "dhd_op08_does_not_create_result_memo_files",
        "dhd_op08_does_not_claim_validation_or_environment_green",
        "dhd_op08_does_not_claim_p7_complete_or_release",
    ):
        assert material[key] is True, key


@pytest.mark.parametrize(
    ("op05_factory", "expected_index"),
    tuple((factory, index) for index, factory in enumerate(DIRECTION_FACTORIES)),
)
def test_op08_closes_each_carried_direction_with_exact_matching_status_and_candidate(
    op05_factory: Callable[[], dict[str, Any]], expected_index: int
) -> None:
    op05 = op05_factory()
    material = _op08(_op07(_op06(op05)), op05)

    assert material["dhd_op08_status_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS[
        expected_index
    ]
    assert material["direction_decision_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[
        expected_index
    ]
    assert material["selected_next_design_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[
        expected_index
    ]
    assert material["next_required_step"] == material[
        "selected_next_design_candidate_ref"
    ]
    assert [material[key] for key in OP08_CLOSURE_FLAG_REFS] == [
        index == expected_index for index in range(6)
    ]
    assert material["op08_input_repair_or_blocked"] is False
    assert material["dhd_op08_blocker_ref_count"] == 0
    assert material["optional_op05_contract_valid"] is True
    assert material["optional_op05_matches_op07"] is True
    _assert_op08_stopped_without_execution(material)


@pytest.mark.parametrize(
    ("op05_factory", "expected_index"),
    tuple((factory, index) for index, factory in enumerate(DIRECTION_FACTORIES)),
)
def test_op08_can_close_materialized_op07_without_requiring_repeated_op05_input(
    op05_factory: Callable[[], dict[str, Any]], expected_index: int
) -> None:
    op05 = op05_factory()
    material = _op08(_op07(_op06(op05)))

    assert material["direction_decision_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[
        expected_index
    ]
    assert material["optional_op05_material_supplied"] is False
    assert material["optional_op05_consistency_required"] is False
    assert material["optional_op05_consistency_satisfied"] is True
    assert material["optional_op05_matches_op07"] is False
    assert material["op08_input_repair_or_blocked"] is False
    _assert_op08_stopped_without_execution(material)


def test_op08_dhr_consideration_closes_without_dhr_op06_call_or_implicit_fallback() -> None:
    op05 = _dhr_op05()
    material = _op08(_op07(_op06(op05)), op05)

    assert material["dhd_op08_dhr_op06_consideration_design_closed_stopped"] is True
    assert material["dhr_op06_builder_called_here"] is False
    assert material["dhr_op06_implicit_op05_fallback_used_here"] is False
    assert material["dhr_op07_materialized_here"] is False
    _assert_op08_stopped_without_execution(material)


def test_op08_p7_readfeel_closes_without_evaluation_completion_or_release() -> None:
    op05 = _p7_op05()
    material = _op08(_op07(_op06(op05)), op05)

    assert material["dhd_op08_p7_readfeel_reconnection_design_closed_stopped"] is True
    assert material["p7_readfeel_evaluation_started_here"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    _assert_op08_stopped_without_execution(material)


def test_op08_current_material_selection_closes_without_dhc_result_synthesis() -> None:
    op05 = DIRECTION_FACTORIES[2]()
    material = _op08(_op07(_op06(op05)), op05)

    assert material[
        "dhd_op08_explicit_current_dhc_material_selection_required_closed_stopped"
    ] is True
    assert material["dhc_builder_called_here"] is False
    assert material["dhc_result_synthesized_here"] is False
    _assert_op08_stopped_without_execution(material)


@pytest.mark.parametrize("expected_index", (3, 4, 5))
def test_op08_repair_wait_non_dhr_and_no_touch_keep_their_exact_stopped_candidate(
    expected_index: int,
) -> None:
    op05 = DIRECTION_FACTORIES[expected_index]()
    material = _op08(_op07(_op06(op05)), op05)

    assert material[OP08_CLOSURE_FLAG_REFS[expected_index]] is True
    assert material["selected_next_design_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[
        expected_index
    ]
    assert material["op08_input_repair_or_blocked"] is False
    assert material["op08_upstream_no_touch_decision_preserved"] is (
        expected_index == 5
    )
    _assert_op08_stopped_without_execution(material)


@pytest.mark.parametrize(
    "invalid_op07", [None, {}, {"material_id": "invalid", "body_free": True}]
)
def test_op08_missing_or_invalid_op07_fails_closed_to_blocked_no_touch(
    invalid_op07: object,
) -> None:
    material = _op08(invalid_op07)

    assert material["op07_contract_valid"] is False
    assert material["op08_input_repair_or_blocked"] is True
    assert material["dhd_op08_blocked_no_touch_no_promotion"] is True
    assert material["direction_decision_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5]
    assert material["selected_next_design_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[5]
    assert material["dhd_op08_blocker_ref_count"] >= 1
    _assert_op08_stopped_without_execution(material)


def test_op08_valid_but_non_materialized_repair_op07_fails_closed() -> None:
    op07 = _op07(_op06(None))
    material = _op08(op07)

    assert material["op07_contract_valid"] is True
    assert material["op07_validation_plan_materialized_stopped"] is False
    assert material["op08_input_repair_or_blocked"] is True
    assert material["dhd_op08_blocked_no_touch_no_promotion"] is True
    _assert_op08_stopped_without_execution(material)


def test_op08_mismatched_optional_op05_and_op07_fails_closed_without_new_decision() -> None:
    p7_op05 = _p7_op05()
    material = _op08(_op07(_op06(p7_op05)), _dhr_op05())

    assert material["op07_contract_valid"] is True
    assert material["optional_op05_contract_valid"] is True
    assert material["optional_op05_matches_op07"] is False
    assert material["optional_op05_consistency_satisfied"] is False
    assert material["op08_input_repair_or_blocked"] is True
    assert material["dhd_op08_blocked_no_touch_no_promotion"] is True
    assert any(
        "OP05_and_OP07_direction_consistency" in ref
        for ref in material["dhd_op08_blocker_refs"]
    )
    _assert_op08_stopped_without_execution(material)


@pytest.mark.parametrize(
    "invalid_op05", [{}, {"material_id": "invalid", "body_free": True}, "invalid"]
)
def test_op08_supplied_invalid_optional_op05_fails_closed(
    invalid_op05: object,
) -> None:
    material = _op08(_op07(_op06(_p7_op05())), invalid_op05)

    assert material["optional_op05_material_supplied"] is True
    assert material["optional_op05_contract_valid"] is False
    assert material["optional_op05_consistency_satisfied"] is False
    assert material["op08_input_repair_or_blocked"] is True
    assert material["dhd_op08_blocked_no_touch_no_promotion"] is True
    _assert_op08_stopped_without_execution(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("question_text", "must_not_be_retained"),
        ("target_validation_green_confirmed_here", True),
        ("validation_commands_executed_here", True),
        ("release_allowed", True),
    ],
)
def test_op08_poisoned_op07_fails_closed_without_retaining_raw_or_claiming_green(
    field: str, bad_value: object
) -> None:
    poisoned = deepcopy(_op07(_op06(_p7_op05())))
    poisoned[field] = bad_value
    material = _op08(poisoned)

    assert material["op07_contract_valid"] is False
    assert material["op08_input_repair_or_blocked"] is True
    assert material["dhd_op08_blocked_no_touch_no_promotion"] is True
    assert "must_not_be_retained" not in repr(material)
    assert material.get(field) is not True
    _assert_op08_stopped_without_execution(material)


def test_op08_does_not_call_upstream_or_downstream_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    op05 = _dhr_op05()
    op07 = _op07(_op06(op05))

    def explode(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("DHD R6 must not call DHC/DHR builders")

    monkeypatch.setattr(
        dhc, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF, explode
    )
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF, explode
    )
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF, explode
    )

    material = _op08(op07, op05)

    assert material["dhd_op08_does_not_call_dhc_or_dhr_builder"] is True
    assert material["dhd_op08_does_not_execute_selected_direction"] is True
    _assert_op08_stopped_without_execution(material)


def test_op08_records_r6_test_compile_and_memo_refs_as_count_only_material() -> None:
    material = _op08(_op07(_op06(_p7_op05())))

    assert tuple(material["target_test_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R6_TARGET_TEST_REF_REFS
    assert tuple(material["selected_regression_test_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R6_SELECTED_REGRESSION_TEST_REF_REFS
    assert tuple(material["optional_product_readfeel_regression_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
    assert tuple(material["compileall_target_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R6_COMPILEALL_TARGET_REF_REFS
    assert tuple(material["result_memo_expected_file_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R6_RESULT_MEMO_EXPECTED_FILE_REFS
    assert material["validation_commands_executed_here"] is False
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
    ):
        assert material[count_field] == len(material[field])


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dhd_op08_status_ref", dhd.P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS[0]),
        (
            "selected_next_design_candidate_ref",
            dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[0],
        ),
        ("dhd_op08_p7_readfeel_reconnection_design_closed_stopped", False),
        ("dhd_op08_dhr_op06_consideration_design_closed_stopped", True),
        ("dhr_op06_builder_called_here", True),
        ("dhr_op07_materialized_here", True),
        ("dmd_r52_executed_here", True),
        ("actual_review_started_here", True),
        ("p8_question_design_started", True),
        ("validation_commands_executed_here", True),
        ("target_validation_green_confirmed_here", True),
        ("result_memo_files_created_here", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_op08_contract_rejects_pair_execution_green_memo_or_promotion_mutations(
    field: str, bad_value: object
) -> None:
    material = deepcopy(_op08(_op07(_op06(_p7_op05()))))
    material[field] = bad_value

    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure_contract(
            material
        )


def test_op08_contract_rejects_a_self_consistent_new_decision_not_carried_by_op07() -> None:
    material = deepcopy(_op08(_op07(_op06(_p7_op05()))))
    material["dhd_op08_status_ref"] = dhd.P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS[0]
    material["bodyfree_stopped_next_design_decision_closure_status_ref"] = material[
        "dhd_op08_status_ref"
    ]
    material["direction_decision_ref"] = dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[0]
    material["selected_next_design_candidate_ref"] = dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[0]
    material["next_required_step"] = material["selected_next_design_candidate_ref"]
    material["dhd_op08_p7_readfeel_reconnection_design_closed_stopped"] = False
    material["dhd_op08_dhr_op06_consideration_design_closed_stopped"] = True

    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure_contract(
            material
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("op08_upstream_no_touch_decision_preserved", True),
        ("optional_op05_consistency_required", True),
        ("optional_op05_consistency_satisfied", False),
        ("optional_op05_matches_op07", True),
    ],
)
def test_op08_contract_rejects_closure_lineage_marker_mutations(
    field: str, bad_value: object
) -> None:
    material = deepcopy(_op08(_op07(_op06(_p7_op05()))))
    material[field] = bad_value

    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure_contract(
            material
        )


def test_r5_op06_and_op07_contracts_reject_mutated_carried_decision_candidate_pairs() -> None:
    op06 = deepcopy(_op06(_p7_op05()))
    op06["op05_selected_next_design_candidate_ref"] = dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[0]
    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard_contract(
            op06
        )

    op07 = deepcopy(_op07(_op06(_p7_op05())))
    op07["op06_upstream_selected_next_design_candidate_ref"] = dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[0]
    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract(
            op07
        )


def test_op08_exact_fields_steps_and_all_implemented_stop_are_stable() -> None:
    material = _op08(_op07(_op06(_p7_op05())))

    assert set(material) == set(dhd.P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FIELD_REFS)
    assert tuple(material["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP08_NOT_YET_IMPLEMENTED_STEPS
    assert material["not_yet_implemented_steps"] == []
    assert material["dhd_op08_implemented"] is True
    for index in range(9):
        assert material[f"dhd_op0{index}_implemented"] is True
    for field, count_field in (
        ("dhd_op08_reason_refs", "dhd_op08_reason_ref_count"),
        ("dhd_op08_blocker_refs", "dhd_op08_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        assert material[count_field] == len(material[field])


def test_op08_output_never_contains_raw_payload_comment_question_or_traceback_keys() -> None:
    material = _op08(_op07(_op06(_no_touch_op05())))
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

    assert not (_collect_keys(material) & forbidden)
    assert material["raw_pytest_stdout_included"] is False
    assert material["raw_pytest_stderr_included"] is False
    assert material["raw_traceback_included"] is False
    assert material["raw_body_included"] is False
    assert material["comment_text_body_included"] is False
    assert material["question_text_body_included"] is False
