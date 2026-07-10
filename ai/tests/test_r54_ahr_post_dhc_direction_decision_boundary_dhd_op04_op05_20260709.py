# -*- coding: utf-8 -*-
"""DHD R4 OP04/OP05 target tests.

The target records P7 product-readfeel reconnection eligibility and selects a
body-free next-design direction. It must not create/evaluate readfeel cases,
call DHC/DHR builders, execute the selected direction, start P8, materialize
question text, or claim P7 completion/release.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
import emlis_ai_p7_r54_ahr_post_dhc_direction_decision_boundary_20260709 as dhd
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op06_op07_20260709 import (
    _op05_not_called,
    _op05_repair,
    _op05_scan_clear,
    _op05_waiting,
)
from test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op02_op03_20260709 import (
    _dhc_op08_from_op05_classification,
    _dhc_op08_non_dhr_lane,
    _existing_dhr_op05_scan_clear,
    _op02,
    _op03,
)


OP04_ELIGIBLE = dhd.P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[0]
OP04_MIN_CASE = dhd.P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[1]
OP04_DEFERRED = dhd.P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[2]
OP04_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[3]

OP05_READY = dhd.P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[0]
OP05_REPAIR_WAIT = dhd.P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[1]
OP05_MATERIAL_SELECTION = dhd.P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[2]
OP05_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[3]

DECISION_DHR = dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[0]
DECISION_P7 = dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[1]
DECISION_MATERIAL = dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[2]
DECISION_REPAIR_WAIT = dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[3]
DECISION_NON_DHR = dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[4]
DECISION_NO_TOUCH = dhd.P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5]


def _op04(
    op02: object,
    op03: object,
    *,
    axes: object = None,
    runner_refs: object = None,
) -> dict[str, Any]:
    material = dhd.build_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility(
        op02,  # type: ignore[arg-type]
        op03,  # type: ignore[arg-type]
        p7_roadmap_readfeel_axis_refs=axes,  # type: ignore[arg-type]
        optional_existing_p7_runner_refs=runner_refs,  # type: ignore[arg-type]
    )
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility_contract(
        material
    )
    return material


def _op05(op02: object, op03: object, op04: object) -> dict[str, Any]:
    material = dhd.build_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator(
        op02,  # type: ignore[arg-type]
        op03,  # type: ignore[arg-type]
        op04,  # type: ignore[arg-type]
    )
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_contract(
        material
    )
    return material


def _r11_chain(*, axes: object = None) -> tuple[dict[str, Any], ...]:
    op02 = _op02()
    op03 = _op03(op02)
    op04 = _op04(op02, op03, axes=axes)
    op05 = _op05(op02, op03, op04)
    return op02, op03, op04, op05


def _scan_clear_chain() -> tuple[dict[str, Any], ...]:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    wrapper = _existing_dhr_op05_scan_clear()
    op02 = _op02(dhc_op08=op08, dhr_op05=wrapper)
    op03 = _op03(op02, dhr_op05=wrapper)
    op04 = _op04(op02, op03)
    op05 = _op05(op02, op03, op04)
    return op08, wrapper, op02, op03, op04, op05


def _assert_no_runtime_p8_or_release(data: dict[str, Any]) -> None:
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
    ):
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


def test_op04_r11_only_returns_to_p7_readfeel_candidate_with_minimum_case_set_required() -> None:
    _, op03, material, _ = _r11_chain()

    assert op03["dhr_op06_consideration_candidate"] is False
    assert material["dhd_op04_status_ref"] == OP04_MIN_CASE
    assert material["p7_readfeel_reconnection_candidate"] is True
    assert material["p7_roadmap_readfeel_axis_refs_complete"] is True
    assert tuple(material["p7_roadmap_readfeel_axis_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_AXIS_REFS
    assert material["minimum_case_set_required"] is True
    assert material["minimum_case_set_created_here"] is False
    assert material["blind_qa_return_required"] is True
    assert material["continued_input_observation_required"] is True
    assert material["pilot_readiness_observation_required"] is True
    assert material["p7_readfeel_actual_case_created_here"] is False
    assert material["p7_readfeel_actual_evaluation_started_here"] is False
    _assert_no_runtime_p8_or_release(material)


def test_op04_scan_clear_with_explicit_op05_keeps_both_design_candidates_comparable() -> None:
    _, _, _, op03, material, _ = _scan_clear_chain()

    assert op03["dhr_op06_consideration_candidate"] is True
    assert material["dhd_op04_status_ref"] == OP04_ELIGIBLE
    assert material["dhr_op06_consideration_candidate"] is True
    assert material["p7_readfeel_reconnection_candidate"] is True
    assert material["current_dhc_scan_clear_result_selected"] is True
    assert material["minimum_case_set_required"] is True
    _assert_no_runtime_p8_or_release(material)


def test_op04_question_need_is_bodyfree_observation_only_without_question_text_or_p8() -> None:
    _, _, material, _ = _r11_chain()

    assert material["question_need_observation_allowed_as_bodyfree"] is True
    assert material["question_need_observation_material_created_here"] is False
    assert material["question_need_observation_rows_created_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False


def test_op04_known_existing_runner_refs_are_refs_only_and_never_executed() -> None:
    op02 = _op02()
    op03 = _op03(op02)
    refs = dhd.P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
    material = _op04(op02, op03, runner_refs=refs)

    assert tuple(material["optional_existing_p7_runner_refs"]) == refs
    assert material["optional_existing_p7_runner_refs_recognized"] is True
    assert material["existing_p7_runner_executed_here"] is False
    assert material["p7_readfeel_actual_evaluation_started_here"] is False


@pytest.mark.parametrize(
    ("op05_builder", "expected_outcome"),
    [
        (_op05_waiting, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[3]),
        (_op05_repair, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[4]),
        (_op05_not_called, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[5]),
    ],
)
def test_op04_waiting_repair_and_not_called_defer_readfeel_until_boundary_closed(
    op05_builder: Any, expected_outcome: str
) -> None:
    op08 = _dhc_op08_from_op05_classification(op05_builder())
    op02 = _op02(dhc_op08=op08)
    op03 = _op03(op02)
    material = _op04(op02, op03)

    assert material["dhc_outcome_class_ref"] == expected_outcome
    assert material["dhd_op04_status_ref"] == OP04_DEFERRED
    assert material["p7_readfeel_reconnection_candidate"] is False
    assert material["blind_qa_return_required"] is False
    _assert_no_runtime_p8_or_release(material)


def test_op04_non_dhr_lane_defers_readfeel_and_preserves_route_for_comparator() -> None:
    op02 = _op02(dhc_op08=_dhc_op08_non_dhr_lane())
    op03 = _op03(op02)
    material = _op04(op02, op03)

    assert material["dhd_op04_status_ref"] == OP04_DEFERRED
    assert material["p7_readfeel_reconnection_candidate"] is False
    assert material["dhc_outcome_class_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[6]


@pytest.mark.parametrize(
    "bad_axes",
    [
        "not-a-sequence-of-refs",
        ["unknown_readfeel_axis"],
        [*dhd.P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_AXIS_REFS, "unknown_axis"],
    ],
)
def test_op04_invalid_or_unknown_readfeel_axes_block_without_inventing_product_evidence(
    bad_axes: object,
) -> None:
    op02 = _op02()
    op03 = _op03(op02)
    material = _op04(op02, op03, axes=bad_axes)

    assert material["dhd_op04_status_ref"] == OP04_BLOCKED
    assert material["p7_readfeel_reconnection_candidate"] is False
    assert material["p7_roadmap_readfeel_axis_refs_complete"] is False
    assert material["p7_readfeel_actual_evaluation_started_here"] is False


def test_op04_explicit_empty_axes_requires_material_without_blocked_unsafe_claim() -> None:
    op02 = _op02()
    op03 = _op03(op02)
    material = _op04(op02, op03, axes=())

    assert material["dhd_op04_status_ref"] == OP04_MIN_CASE
    assert material["p7_readfeel_reconnection_candidate"] is False
    assert material["p7_roadmap_readfeel_axis_refs_complete"] is False
    assert any("axis_refs_required" in ref for ref in material["dhd_op04_blocker_refs"])


def test_op04_unknown_runner_ref_blocks_and_does_not_retain_unknown_body_value() -> None:
    op02 = _op02()
    op03 = _op03(op02)
    material = _op04(op02, op03, runner_refs=["unknown private runner material"])

    assert material["dhd_op04_status_ref"] == OP04_BLOCKED
    assert material["optional_existing_p7_runner_refs"] == []
    assert "unknown private runner material" not in repr(material)
    assert material["existing_p7_runner_executed_here"] is False


def test_op05_r11_only_selects_p7_readfeel_design_first_never_dhr_consideration() -> None:
    _, op03, op04, material = _r11_chain()

    assert op03["dhr_op06_consideration_candidate"] is False
    assert op04["p7_readfeel_reconnection_candidate"] is True
    assert material["dhd_op05_status_ref"] == OP05_READY
    assert material["direction_decision_ref"] == DECISION_P7
    assert material["direction_decision_ref"] != DECISION_DHR
    assert material["dhr_op06_consideration_candidate"] is False
    assert material["p7_readfeel_reconnection_candidate"] is True
    assert material["selected_next_design_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[1]
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF
    _assert_no_runtime_p8_or_release(material)


def test_op05_r11_only_without_complete_readfeel_axes_stops_for_current_material_selection() -> None:
    _, _, op04, material = _r11_chain(axes=())

    assert op04["p7_readfeel_reconnection_candidate"] is False
    assert material["dhd_op05_status_ref"] == OP05_MATERIAL_SELECTION
    assert material["direction_decision_ref"] == DECISION_MATERIAL
    assert material["current_dhc_material_selection_required"] is True
    assert material["selected_next_design_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[2]
    assert material["dhr_op06_builder_called_here"] is False


def test_op05_explicit_scan_clear_and_current_op05_compare_both_then_select_dhr_design_only() -> None:
    _, _, op02, op03, op04, material = _scan_clear_chain()

    assert op02["current_dhc_scan_clear_result_selected"] is True
    assert op03["dhr_op06_consideration_candidate"] is True
    assert op04["p7_readfeel_reconnection_candidate"] is True
    assert material["dhd_op05_status_ref"] == OP05_READY
    assert material["direction_decision_ref"] == DECISION_DHR
    assert material["dhr_op06_consideration_candidate"] is True
    assert material["dhr_op06_consideration_has_direct_branch_resolution_reason"] is True
    assert material["p7_readfeel_reconnection_candidate"] is True
    assert material["selected_next_design_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[0]
    assert material["dhr_op06_builder_call_allowed_here"] is False
    assert material["dhr_op06_builder_called_here"] is False
    assert material["dhr_op06_implicit_op05_fallback_allowed_here"] is False
    assert material["dhr_op06_implicit_op05_fallback_used_here"] is False
    _assert_no_runtime_p8_or_release(material)


@pytest.mark.parametrize(
    "op05_builder",
    [_op05_waiting, _op05_repair, _op05_not_called],
)
def test_op05_waiting_repair_or_not_called_selects_repair_wait_boundary(
    op05_builder: Any,
) -> None:
    op02 = _op02(dhc_op08=_dhc_op08_from_op05_classification(op05_builder()))
    op03 = _op03(op02)
    op04 = _op04(op02, op03)
    material = _op05(op02, op03, op04)

    assert material["dhd_op05_status_ref"] == OP05_REPAIR_WAIT
    assert material["direction_decision_ref"] == DECISION_REPAIR_WAIT
    assert material["repair_or_wait_boundary_required"] is True
    assert material["dhr_op06_consideration_candidate"] is False
    assert material["p7_readfeel_reconnection_candidate"] is False
    _assert_no_runtime_p8_or_release(material)


def test_op05_non_dhr_lane_selects_route_preservation_without_other_direction() -> None:
    op02 = _op02(dhc_op08=_dhc_op08_non_dhr_lane())
    op03 = _op03(op02)
    op04 = _op04(op02, op03)
    material = _op05(op02, op03, op04)

    assert material["dhd_op05_status_ref"] == OP05_READY
    assert material["direction_decision_ref"] == DECISION_NON_DHR
    assert material["non_dhr_lane_route_preservation_required"] is True
    assert material["dhr_op06_consideration_candidate"] is False
    assert material["p7_readfeel_reconnection_candidate"] is False


def test_op05_blocked_upstream_selects_no_touch_hold() -> None:
    op08, _, _, _, _, _ = _scan_clear_chain()
    poisoned = deepcopy(op08)
    poisoned["release_allowed"] = True
    op02 = _op02(dhc_op08=poisoned)
    op03 = _op03(op02)
    op04 = _op04(op02, op03)
    material = _op05(op02, op03, op04)

    assert op04["dhd_op04_status_ref"] == OP04_BLOCKED
    assert material["dhd_op05_status_ref"] == OP05_BLOCKED
    assert material["direction_decision_ref"] == DECISION_NO_TOUCH
    assert material["no_touch_repair_or_hold_required"] is True
    assert material["next_runtime_execution_allowed_here"] is False
    _assert_no_runtime_p8_or_release(material)


def test_op05_invalid_op04_material_blocks_without_rebuilding_or_fallback() -> None:
    op02 = _op02()
    op03 = _op03(op02)
    invalid_op04 = {"material_id": "invalid_op04", "body_free": True}
    material = _op05(op02, op03, invalid_op04)

    assert material["op04_contract_valid"] is False
    assert material["dhd_op05_status_ref"] == OP05_BLOCKED
    assert material["direction_decision_ref"] == DECISION_NO_TOUCH
    assert material["dhr_op06_implicit_op05_fallback_used_here"] is False


def test_op04_op05_never_call_dhc_dhr_or_readfeel_execution_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    op08, wrapper, op02, op03, _, _ = _scan_clear_chain()

    def explode(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("DHD R4 must not call execution builders or runners")

    monkeypatch.setattr(dhc, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF, explode)
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF, explode
    )
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF, explode
    )

    op04 = _op04(
        op02,
        op03,
        runner_refs=dhd.P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS,
    )
    op05 = _op05(op02, op03, op04)

    assert op08["body_free"] is True
    assert wrapper["body_free"] is True
    assert op04["existing_p7_runner_executed_here"] is False
    assert op04["dhd_op04_does_not_call_dhc_or_dhr_builder"] is True
    assert op05["dhd_op05_does_not_call_dhc_or_dhr_builder"] is True
    assert op05["dhd_op05_does_not_execute_selected_direction"] is True


@pytest.mark.parametrize(
    ("builder", "assert_contract", "field", "bad_value"),
    [
        (
            lambda: _r11_chain()[2],
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility_contract,
            "p7_readfeel_actual_case_created_here",
            True,
        ),
        (
            lambda: _r11_chain()[2],
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility_contract,
            "question_text_materialized_here",
            True,
        ),
        (
            lambda: _r11_chain()[2],
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility_contract,
            "p7_complete",
            True,
        ),
        (
            lambda: _r11_chain()[3],
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_contract,
            "direction_decision_ref",
            DECISION_DHR,
        ),
        (
            lambda: _r11_chain()[3],
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_contract,
            "dhr_op06_builder_called_here",
            True,
        ),
        (
            lambda: _r11_chain()[3],
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_contract,
            "next_runtime_execution_allowed_here",
            True,
        ),
        (
            lambda: _r11_chain()[3],
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_contract,
            "release_allowed",
            True,
        ),
    ],
)
def test_op04_op05_contracts_reject_evaluation_execution_or_promotion_mutations(
    builder: Any, assert_contract: Any, field: str, bad_value: object
) -> None:
    material = deepcopy(builder())
    material[field] = bad_value

    with pytest.raises(ValueError):
        assert_contract(material)


def test_op05_blocks_raw_question_payload_in_upstream_without_retaining_value() -> None:
    op02, op03, op04, _ = _r11_chain()
    poisoned = deepcopy(op04)
    poisoned["question_text"] = "must_not_be_retained"
    material = _op05(op02, op03, poisoned)

    assert material["dhd_op05_status_ref"] == OP05_BLOCKED
    assert material["direction_decision_ref"] == DECISION_NO_TOUCH
    assert material["op05_input_forbidden_payload_key_path_count"] >= 1
    assert "must_not_be_retained" not in repr(material)


def test_op04_op05_exact_fields_steps_counts_and_r5_stop_are_stable() -> None:
    _, _, op04, op05 = _r11_chain()

    assert set(op04) == set(dhd.P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FIELD_REFS)
    assert set(op05) == set(dhd.P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FIELD_REFS)
    assert tuple(op04["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP04_IMPLEMENTED_STEPS
    assert tuple(op05["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP05_IMPLEMENTED_STEPS
    assert tuple(op05["not_yet_implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP05_NOT_YET_IMPLEMENTED_STEPS
    assert op05["not_yet_implemented_steps"][0] == dhd.P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF
    assert op05["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF
    assert tuple(op05["optional_product_readfeel_regression_ref_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
    for material, pairs in (
        (
            op04,
            (
                ("dhd_op04_reason_refs", "dhd_op04_reason_ref_count"),
                ("dhd_op04_blocker_refs", "dhd_op04_blocker_ref_count"),
            ),
        ),
        (
            op05,
            (
                ("decision_reason_refs", "decision_reason_ref_count"),
                ("decision_blocker_refs", "decision_blocker_ref_count"),
                ("direction_comparison_axis_refs", "direction_comparison_axis_ref_count"),
            ),
        ),
    ):
        for field, count_field in pairs:
            assert material[count_field] == len(material[field])


def test_op04_op05_outputs_never_include_raw_body_comment_question_or_traceback_keys() -> None:
    _, _, _, _, op04, op05 = _scan_clear_chain()
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

    assert not (_collect_keys(op04) & forbidden)
    assert not (_collect_keys(op05) & forbidden)
    assert op04["question_need_observation_allowed_as_bodyfree"] is True
    assert op04["question_text_materialized_here"] is False
    assert op05["p8_question_design_started"] is False
    assert op05["p7_complete"] is False
    assert op05["release_allowed"] is False
