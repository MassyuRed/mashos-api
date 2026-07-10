# -*- coding: utf-8 -*-
"""DHD R3 OP02/OP03 target tests.

The target classifies only explicit, already-existing DHC material and decides
whether DHR-OP06 consideration is a candidate. It must not call DHC, existing
DHR-OP05, or DHR-OP06 builders; use implicit OP05 fallback; execute downstream
work; start P7 readfeel evaluation/P8; or claim P7 completion/release.
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
    _op06,
    _op07,
)
from test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op00_op01_20260709 import (
    _dhc_r11,
    _op01,
)
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704 import (
    _op04_confirmed_separation,
    _op04_not_confirmed_separation,
)


OP02_CLASSIFIED = dhd.P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[0]
OP02_R11_ONLY = dhd.P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[1]
OP02_WAITING = dhd.P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[2]
OP02_REPAIR = dhd.P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[3]
OP02_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[4]

OUTCOME_SCAN_CLEAR = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[0]
OUTCOME_R11_ONLY = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[1]
OUTCOME_TEST_ONLY = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[2]
OUTCOME_WAITING = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[3]
OUTCOME_REPAIR = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[4]
OUTCOME_NOT_CALLED = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[5]
OUTCOME_NON_DHR = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[6]
OUTCOME_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7]

OP03_ELIGIBLE = dhd.P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[0]
OP03_DEFERRED = dhd.P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[1]
OP03_NOT_ALLOWED = dhd.P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[2]
OP03_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[3]


def _existing_dhr_op05_scan_clear() -> dict[str, Any]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_confirmed_separation()
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(
        material
    )
    assert material["dhr_op05_status_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF
    return material


def _existing_dhr_op05_waiting() -> dict[str, Any]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
        actual_source_claim_separation=_op04_not_confirmed_separation()
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(
        material
    )
    assert material["dhr_op05_status_ref"] != dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF
    return material


def _dhc_op08_from_op05_classification(op05: dict[str, Any]) -> dict[str, Any]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate(
        _op07(_op06(op05)),
        op05_existing_dhr_op05_result_classification=op05,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate_contract(
        material
    )
    return material


def _dhc_op08_non_dhr_lane() -> dict[str, Any]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate(
        non_dhr_lane_route_preserved=True
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate_contract(
        material
    )
    return material


def _op02(
    *,
    dhc_op08: object = None,
    dhr_op05: object = None,
    test_validation_only: object = False,
    op01_material: object = None,
) -> dict[str, Any]:
    intake = (
        _op01(_dhc_r11(), dhc_op08=dhc_op08, dhr_op05=dhr_op05)
        if op01_material is None
        else op01_material
    )
    material = dhd.build_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check(
        intake,  # type: ignore[arg-type]
        optional_explicit_dhc_op08_result_memo_closure_material=dhc_op08,  # type: ignore[arg-type]
        optional_current_existing_dhr_op05_result_wrapper=dhr_op05,  # type: ignore[arg-type]
        scan_clear_capable_test_validation_only=test_validation_only,  # type: ignore[arg-type]
    )
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_contract(
        material
    )
    return material


def _op03(
    op02: object,
    *,
    dhr_op05: object = None,
    allow_candidate: object = True,
    allow_builder: object = False,
    allow_fallback: object = False,
) -> dict[str, Any]:
    material = dhd.build_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call(
        op02,  # type: ignore[arg-type]
        optional_current_existing_dhr_op05_result_wrapper=dhr_op05,  # type: ignore[arg-type]
        allow_dhr_op06_consideration_candidate=allow_candidate,  # type: ignore[arg-type]
        allow_dhr_op06_builder_call=allow_builder,  # type: ignore[arg-type]
        allow_dhr_op06_implicit_op05_fallback=allow_fallback,  # type: ignore[arg-type]
    )
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_contract(
        material
    )
    return material


def _assert_no_execution_or_promotion(data: dict[str, Any]) -> None:
    for key in (
        "dhc_builder_called_here",
        "dhc_result_synthesized_here",
        "current_dhc_result_selected_here",
        "current_existing_dhr_op05_result_wrapper_selected_here",
        "dhr_op05_runtime_call_started_here",
        "existing_dhr_op05_builder_runtime_called_here",
        "dhr_op06_consideration_decided_here",
        "dhr_op06_builder_called_here",
        "dhr_op06_implicit_op05_fallback_used_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p7_readfeel_reconnection_decided_here",
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


def test_op02_r11_only_stays_without_current_selected_result_or_op06_permission() -> None:
    material = _op02()

    assert material["dhd_op02_status_ref"] == OP02_R11_ONLY
    assert material["dhc_outcome_class_ref"] == OUTCOME_R11_ONLY
    assert material["current_dhc_result_selected"] is False
    assert material["current_dhc_scan_clear_result_selected"] is False
    assert material["scan_clear_capable_test_validation_only"] is False
    assert material["dhr_op06_permission_produced_here"] is False
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF
    _assert_no_execution_or_promotion(material)


def test_op02_scan_clear_capable_validation_is_not_current_runtime_result() -> None:
    material = _op02(test_validation_only=True)

    assert material["dhd_op02_status_ref"] == OP02_R11_ONLY
    assert material["dhc_outcome_class_ref"] == OUTCOME_TEST_ONLY
    assert material["scan_clear_capable_test_validation_only"] is True
    assert material["current_dhc_result_selected"] is False
    assert material["current_dhc_scan_clear_result_selected"] is False
    assert material["current_material_sufficient_for_dhr_op06_consideration"] is False
    _assert_no_execution_or_promotion(material)


def test_op02_op01_presence_record_without_repeated_explicit_material_does_not_select() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    op01 = _op01(_dhc_r11(), dhc_op08=op08)
    material = _op02(op01_material=op01)

    assert material["dhc_outcome_class_ref"] == OUTCOME_R11_ONLY
    assert material["explicit_current_dhc_op08_material_present"] is False
    assert material["current_dhc_result_selected"] is False
    assert any("presence_record" in ref for ref in material["dhd_op02_reason_refs"])


def test_op02_explicit_current_scan_clear_op08_is_selected_but_not_op06_permission() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    material = _op02(dhc_op08=op08)

    assert material["dhd_op02_status_ref"] == OP02_CLASSIFIED
    assert material["dhc_outcome_class_ref"] == OUTCOME_SCAN_CLEAR
    assert material["explicit_current_dhc_op08_material_contract_valid"] is True
    assert material["current_dhc_result_selected"] is True
    assert material["current_dhc_scan_clear_result_selected"] is True
    assert material["current_material_sufficient_for_dhr_op06_consideration"] is False
    assert material["dhr_op06_permission_produced_here"] is False
    _assert_no_execution_or_promotion(material)


@pytest.mark.parametrize(
    ("op05_builder", "expected_status", "expected_outcome"),
    [
        (_op05_waiting, OP02_WAITING, OUTCOME_WAITING),
        (_op05_repair, OP02_REPAIR, OUTCOME_REPAIR),
        (_op05_not_called, OP02_WAITING, OUTCOME_NOT_CALLED),
    ],
)
def test_op02_preserves_waiting_repair_and_not_called_outcomes(
    op05_builder: Any, expected_status: str, expected_outcome: str
) -> None:
    op08 = _dhc_op08_from_op05_classification(op05_builder())
    material = _op02(dhc_op08=op08)

    assert material["dhd_op02_status_ref"] == expected_status
    assert material["dhc_outcome_class_ref"] == expected_outcome
    assert material["current_dhc_result_selected"] is True
    assert material["current_dhc_scan_clear_result_selected"] is False
    assert material["current_material_sufficient_for_dhr_op06_consideration"] is False
    _assert_no_execution_or_promotion(material)


def test_op02_preserves_non_dhr_lane_without_op06_consideration_permission() -> None:
    material = _op02(dhc_op08=_dhc_op08_non_dhr_lane())

    assert material["dhd_op02_status_ref"] == OP02_CLASSIFIED
    assert material["dhc_outcome_class_ref"] == OUTCOME_NON_DHR
    assert material["current_dhc_result_selected"] is True
    assert material["current_dhc_scan_clear_result_selected"] is False
    assert material["dhr_op06_permission_produced_here"] is False


def test_op02_invalid_explicit_current_op08_requires_repair_without_builder_fallback() -> None:
    invalid = {"material_id": "not_a_complete_DHC_OP08_material", "body_free": True}
    material = _op02(dhc_op08=invalid)

    assert material["dhd_op02_status_ref"] == OP02_REPAIR
    assert material["dhc_outcome_class_ref"] == OUTCOME_REPAIR
    assert material["explicit_current_dhc_op08_material_contract_valid"] is False
    assert material["current_dhc_result_selected"] is False
    assert material["dhd_op02_does_not_call_dhc_builder"] is True
    assert material["dhd_op02_does_not_use_dhr_op06_implicit_op05_fallback"] is True


@pytest.mark.parametrize(
    ("field", "value", "path_fragment"),
    [
        ("question_text", "must_not_be_retained", "question_text"),
        ("release_allowed", True, "release_allowed"),
        ("api_changed", True, "api_changed"),
    ],
)
def test_op02_blocks_body_leak_promotion_or_no_touch_claim_without_retaining_value(
    field: str, value: object, path_fragment: str
) -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    poisoned = deepcopy(op08)
    poisoned[field] = value
    material = _op02(dhc_op08=poisoned)

    assert material["dhd_op02_status_ref"] == OP02_BLOCKED
    assert material["dhc_outcome_class_ref"] == OUTCOME_BLOCKED
    assert any(
        path_fragment in ref
        for ref in (
            material["op02_input_forbidden_payload_key_path_refs"]
            + material["op02_input_promotion_or_autorun_claim_path_refs"]
            + material["op02_input_no_touch_mutation_path_refs"]
        )
    )
    assert "must_not_be_retained" not in repr(material)
    _assert_no_execution_or_promotion(material)


def test_op03_scan_clear_op08_without_explicit_current_op05_wrapper_is_deferred() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    material = _op03(_op02(dhc_op08=op08))

    assert material["dhd_op03_status_ref"] == OP03_DEFERRED
    assert material["explicit_current_material_required"] is True
    assert material["explicit_current_material_satisfied"] is False
    assert material["dhr_op06_consideration_candidate"] is False
    assert material["dhr_op06_builder_called_here"] is False
    _assert_no_execution_or_promotion(material)


def test_op03_explicit_current_op05_without_selected_scan_clear_op08_is_deferred() -> None:
    wrapper = _existing_dhr_op05_scan_clear()
    material = _op03(_op02(dhr_op05=wrapper), dhr_op05=wrapper)

    assert material["dhd_op03_status_ref"] == OP03_DEFERRED
    assert material["current_dhc_scan_clear_result_selected"] is False
    assert material["explicit_current_op05_material_scan_clear_stopped"] is True
    assert material["explicit_current_material_satisfied"] is False
    assert material["dhr_op06_consideration_candidate"] is False


def test_op03_requires_both_selected_scan_clear_op08_and_current_scan_clear_op05() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    wrapper = _existing_dhr_op05_scan_clear()
    op02 = _op02(dhc_op08=op08, dhr_op05=wrapper)
    material = _op03(op02, dhr_op05=wrapper)

    assert material["dhd_op03_status_ref"] == OP03_ELIGIBLE
    assert material["explicit_current_material_satisfied"] is True
    assert material["current_dhc_scan_clear_result_selected"] is True
    assert material["explicit_current_op05_material_contract_valid_ref"] is True
    assert material["explicit_current_op05_material_scan_clear_stopped"] is True
    assert material["unresolved_branch_reason_confirmed"] is True
    assert material["dhr_op06_consideration_is_not_based_only_on_next_operation_order"] is True
    assert dhd.P7_R54_AHR_POST_DHC_DHD_DHR_OP06_UNRESOLVED_BRANCH_REASON_REF in material[
        "why_dhr_op06_consideration_may_be_needed_refs"
    ]
    assert material["dhr_op06_consideration_candidate"] is True
    assert material["dhr_op06_builder_call_allowed_here"] is False
    assert material["dhr_op06_builder_called_here"] is False
    assert material["dhr_op06_implicit_op05_fallback_allowed_here"] is False
    assert material["dhr_op06_implicit_op05_fallback_used_here"] is False
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF
    _assert_no_execution_or_promotion(material)


def test_op03_current_op05_waiting_wrapper_is_not_enough_for_eligibility() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    wrapper = _existing_dhr_op05_waiting()
    material = _op03(_op02(dhc_op08=op08, dhr_op05=wrapper), dhr_op05=wrapper)

    assert material["dhd_op03_status_ref"] == OP03_DEFERRED
    assert material["explicit_current_op05_material_contract_valid_ref"] is True
    assert material["explicit_current_op05_material_scan_clear_stopped"] is False
    assert material["explicit_current_material_satisfied"] is False
    assert material["dhr_op06_consideration_candidate"] is False


def test_op03_explicit_material_still_requires_consideration_candidate_allowance() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    wrapper = _existing_dhr_op05_scan_clear()
    material = _op03(
        _op02(dhc_op08=op08, dhr_op05=wrapper),
        dhr_op05=wrapper,
        allow_candidate=False,
    )

    assert material["dhd_op03_status_ref"] == OP03_DEFERRED
    assert material["explicit_current_material_satisfied"] is True
    assert material["allow_dhr_op06_consideration_candidate"] is False
    assert material["dhr_op06_consideration_candidate"] is False


@pytest.mark.parametrize(
    "dhc_op08",
    [
        pytest.param("waiting", id="waiting"),
        pytest.param("repair", id="repair"),
        pytest.param("not_called", id="not_called"),
        pytest.param("non_dhr", id="non_dhr"),
    ],
)
def test_op03_waiting_repair_not_called_and_non_dhr_outcomes_are_not_allowed(
    dhc_op08: str,
) -> None:
    builders = {
        "waiting": _op05_waiting,
        "repair": _op05_repair,
        "not_called": _op05_not_called,
    }
    explicit_op08 = (
        _dhc_op08_non_dhr_lane()
        if dhc_op08 == "non_dhr"
        else _dhc_op08_from_op05_classification(builders[dhc_op08]())
    )
    material = _op03(_op02(dhc_op08=explicit_op08))

    assert material["dhd_op03_status_ref"] == OP03_NOT_ALLOWED
    assert material["dhr_op06_consideration_candidate"] is False
    assert material["dhr_op06_builder_called_here"] is False
    _assert_no_execution_or_promotion(material)


def test_op03_scan_clear_capable_test_validation_only_is_deferred_not_eligible() -> None:
    material = _op03(_op02(test_validation_only=True))

    assert material["op02_dhc_outcome_class_ref"] == OUTCOME_TEST_ONLY
    assert material["scan_clear_capable_test_validation_only"] is True
    assert material["dhd_op03_status_ref"] == OP03_DEFERRED
    assert material["dhr_op06_consideration_candidate"] is False


@pytest.mark.parametrize(
    ("allow_builder", "allow_fallback", "expected_blocker"),
    [
        (True, False, "builder_call_request"),
        (False, True, "implicit_OP05_fallback_request"),
        (True, True, "builder_call_request"),
    ],
)
def test_op03_builder_call_or_implicit_fallback_request_is_blocked(
    allow_builder: bool, allow_fallback: bool, expected_blocker: str
) -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    wrapper = _existing_dhr_op05_scan_clear()
    material = _op03(
        _op02(dhc_op08=op08, dhr_op05=wrapper),
        dhr_op05=wrapper,
        allow_builder=allow_builder,
        allow_fallback=allow_fallback,
    )

    assert material["dhd_op03_status_ref"] == OP03_BLOCKED
    assert material["dhr_op06_consideration_candidate"] is False
    assert any(expected_blocker in ref for ref in material["dhr_op06_consideration_blocker_refs"])
    assert material["dhr_op06_builder_call_allowed_here"] is False
    assert material["dhr_op06_builder_called_here"] is False
    assert material["dhr_op06_implicit_op05_fallback_allowed_here"] is False
    assert material["dhr_op06_implicit_op05_fallback_used_here"] is False
    assert material["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP03_REF
    _assert_no_execution_or_promotion(material)


@pytest.mark.parametrize("bad_allow_value", [None, "false", 0, 1])
def test_op03_non_boolean_allow_input_is_blocked_without_coercion(bad_allow_value: object) -> None:
    material = _op03(
        _op02(),
        allow_candidate=bad_allow_value,
    )

    assert material["dhd_op03_status_ref"] == OP03_BLOCKED
    assert material["allow_input_types_valid"] is False
    assert material["dhr_op06_consideration_candidate"] is False


def test_op02_and_op03_do_not_call_any_dhc_op08_dhr_op05_or_dhr_op06_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    wrapper = _existing_dhr_op05_scan_clear()

    def explode(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("DHD R3 must not call upstream/downstream builders")

    monkeypatch.setattr(dhc, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF, explode)
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF, explode
    )
    monkeypatch.setattr(
        dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF, explode
    )

    op01 = _op01(_dhc_r11(), dhc_op08=op08, dhr_op05=wrapper)
    op02 = _op02(dhc_op08=op08, dhr_op05=wrapper, op01_material=op01)
    op03 = _op03(op02, dhr_op05=wrapper)

    assert op02["dhd_op02_does_not_call_dhc_builder"] is True
    assert op02["dhd_op02_does_not_call_existing_dhr_op05_builder"] is True
    assert op03["dhd_op03_does_not_call_dhr_op06_builder"] is True
    assert op03["dhr_op06_consideration_candidate"] is True


def test_op03_invalid_current_op05_wrapper_is_deferred_without_implicit_fallback() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    invalid_wrapper = {"material_id": "invalid_current_DHR_OP05", "body_free": True}
    material = _op03(
        _op02(dhc_op08=op08, dhr_op05=invalid_wrapper),
        dhr_op05=invalid_wrapper,
    )

    assert material["dhd_op03_status_ref"] == OP03_DEFERRED
    assert material["explicit_current_op05_material_present"] is True
    assert material["explicit_current_op05_material_contract_valid_ref"] is False
    assert material["explicit_current_material_satisfied"] is False
    assert material["dhr_op06_implicit_op05_fallback_used_here"] is False


def test_op03_blocked_op02_outcome_remains_blocked() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    poisoned = deepcopy(op08)
    poisoned["release_allowed"] = True
    material = _op03(_op02(dhc_op08=poisoned))

    assert material["op02_dhc_outcome_class_ref"] == OUTCOME_BLOCKED
    assert material["dhd_op03_status_ref"] == OP03_BLOCKED
    assert material["dhr_op06_consideration_candidate"] is False


@pytest.mark.parametrize(
    ("builder", "assert_contract", "field", "bad_value"),
    [
        (
            lambda: _op02(),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_contract,
            "current_dhc_result_selected",
            True,
        ),
        (
            lambda: _op02(test_validation_only=True),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_contract,
            "dhr_op06_permission_produced_here",
            True,
        ),
        (
            lambda: _op03(_op02()),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_contract,
            "dhr_op06_builder_called_here",
            True,
        ),
        (
            lambda: _op03(_op02()),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_contract,
            "dhr_op06_implicit_op05_fallback_used_here",
            True,
        ),
        (
            lambda: _op03(_op02()),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_contract,
            "p8_question_design_started",
            True,
        ),
        (
            lambda: _op03(_op02()),
            dhd.assert_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_contract,
            "release_allowed",
            True,
        ),
    ],
)
def test_op02_op03_contracts_reject_selection_execution_fallback_or_promotion_mutations(
    builder: Any, assert_contract: Any, field: str, bad_value: object
) -> None:
    material = deepcopy(builder())
    material[field] = bad_value

    with pytest.raises(ValueError):
        assert_contract(material)


def test_op02_op03_exact_fields_steps_counts_and_r4_stop_are_stable() -> None:
    op02 = _op02()
    op03 = _op03(op02)

    assert set(op02) == set(dhd.P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FIELD_REFS)
    assert set(op03) == set(dhd.P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FIELD_REFS)
    assert tuple(op02["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP02_IMPLEMENTED_STEPS
    assert tuple(op03["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP03_IMPLEMENTED_STEPS
    assert tuple(op03["not_yet_implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP03_NOT_YET_IMPLEMENTED_STEPS
    assert dhd.P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF in op03["not_yet_implemented_steps"]
    assert op03["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF
    for material, pairs in (
        (
            op02,
            (
                ("dhd_op02_reason_refs", "dhd_op02_reason_ref_count"),
                ("dhd_op02_blocker_refs", "dhd_op02_blocker_ref_count"),
            ),
        ),
        (
            op03,
            (
                (
                    "why_dhr_op06_consideration_may_be_needed_refs",
                    "why_dhr_op06_consideration_may_be_needed_ref_count",
                ),
                (
                    "why_dhr_op06_consideration_is_not_enough_refs",
                    "why_dhr_op06_consideration_is_not_enough_ref_count",
                ),
                (
                    "dhr_op06_consideration_blocker_refs",
                    "dhr_op06_consideration_blocker_ref_count",
                ),
            ),
        ),
    ):
        for field, count_field in pairs:
            assert material[count_field] == len(material[field])


def test_op02_op03_outputs_never_include_raw_body_comment_question_or_traceback_keys() -> None:
    op08 = _dhc_op08_from_op05_classification(_op05_scan_clear())
    wrapper = _existing_dhr_op05_scan_clear()
    op02 = _op02(dhc_op08=op08, dhr_op05=wrapper)
    op03 = _op03(op02, dhr_op05=wrapper)
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

    assert not (_collect_keys(op02) & forbidden)
    assert not (_collect_keys(op03) & forbidden)
    assert op03["dhr_op07_materialized_here"] is False
    assert op03["dmd_execution_started_here"] is False
    assert op03["p8_question_design_started"] is False
    assert op03["p7_complete"] is False
    assert op03["release_allowed"] is False
