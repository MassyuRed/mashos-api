# -*- coding: utf-8 -*-
"""DHD R2 OP00/OP01 target tests.

The target stops after Post-DHC no-execution refreeze and explicit DHC R11
body-free intake. It must not select a current DHC result, call DHC/DHR
builders, decide DHR-OP06 consideration, run P7 readfeel, or start P8/release.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
import emlis_ai_p7_r54_ahr_post_dhc_direction_decision_boundary_20260709 as dhd
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr


OP00_REFROZEN = dhd.P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS[0]
OP01_READY = dhd.P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[0]
OP01_READY_WITH_DHC_OP08 = dhd.P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[1]
OP01_WAITING = dhd.P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[2]
OP01_REPAIR = dhd.P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[3]
OP01_BLOCKED = dhd.P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[4]


def _op00() -> dict[str, object]:
    return dhd.build_p7_r54_ahr_post_dhc_dhd_op00_post_dhc_basis_no_execution_refreeze()


def _dhc_r11(**updates: object) -> dict[str, object]:
    material: dict[str, object] = {
        "material_id": "fixture_dhc_r11_bodyfree_next_work_decision_material",
        "source_mode": "local_received_zip_only",
        "current_execution_allowance": "none",
        "dhr_op06_call": "none",
        "dhr_op07_materialization": "none",
        "p8_question_design": "none",
        "release_decision": "none",
        "recommended_next_work_candidate": dhd.P7_R54_AHR_POST_DHC_DHD_DHC_R11_RECOMMENDED_NEXT_WORK_CANDIDATE_REF,
        "body_free": True,
    }
    material.update(updates)
    return material


def _op01(
    r11: object = None,
    *,
    op00: object = None,
    dhc_op08: object = None,
    dhr_op05: object = None,
) -> dict[str, object]:
    op00_material = _op00() if op00 is None else op00
    return dhd.build_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake(
        op00_post_dhc_basis_refreeze=op00_material,  # type: ignore[arg-type]
        explicit_dhc_r11_bodyfree_next_work_decision_material=r11,  # type: ignore[arg-type]
        optional_explicit_dhc_op08_result_memo_closure_material=dhc_op08,  # type: ignore[arg-type]
        optional_current_existing_dhr_op05_result_wrapper=dhr_op05,  # type: ignore[arg-type]
    )


def _assert_no_execution_or_promotion(data: dict[str, object]) -> None:
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


def test_r2_keeps_r0_r1_summary_valid_and_stopped_before_op00_execution() -> None:
    r1 = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(r1) is True
    assert r1["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF
    assert r1["dhr_op06_builder_called_here"] is False
    assert r1["p7_readfeel_evaluation_started_here"] is False


def test_op00_refreezes_post_dhc_scope_with_execution_allowance_none() -> None:
    op00 = _op00()

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op00_post_dhc_basis_no_execution_refreeze_contract(op00) is True
    assert op00["dhd_op00_status_ref"] == OP00_REFROZEN
    assert op00["current_execution_allowance_ref"] == "none"
    assert op00["dhc_r11_is_not_dhr_op06_permission"] is True
    assert op00["dhc_validation_green_is_not_current_runtime_execution"] is True
    assert op00["dhd_does_not_call_dhr_op06"] is True
    assert op00["dhd_op00_does_not_use_dhr_op06_implicit_op05_fallback"] is True
    assert op00["dhd_op00_does_not_run_p7_readfeel_evaluation"] is True
    assert op00["dhd_does_not_start_p8"] is True
    assert op00["dhd_does_not_claim_p7_complete_or_release"] is True
    assert op00["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF
    assert tuple(op00["implemented_steps"]) == dhd.P7_R54_AHR_POST_DHC_DHD_OP00_IMPLEMENTED_STEPS
    assert dhd.P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF in op00["not_yet_implemented_steps"]
    _assert_no_execution_or_promotion(op00)


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("body_free", False),
        ("current_execution_allowance_ref", "DHR_OP06"),
        ("dhc_builder_call_allowed_here", True),
        ("dhc_result_synthesis_allowed_here", True),
        ("dhr_op06_builder_call_allowed_here", True),
        ("dhr_op06_implicit_op05_fallback_allowed_here", True),
        ("p7_readfeel_evaluation_execution_allowed_here", True),
        ("p8_question_design_allowed_here", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_op00_assert_rejects_execution_fallback_or_promotion_mutations(
    key: str, bad_value: object
) -> None:
    bad = deepcopy(_op00())
    bad[key] = bad_value

    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op00_post_dhc_basis_no_execution_refreeze_contract(bad)


def test_op01_missing_dhc_r11_material_waits_without_synthesis_or_builder_call() -> None:
    op01 = _op01(None)

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_status_ref"] == OP01_WAITING
    assert op01["dhc_r11_material_supplied"] is False
    assert op01["dhc_r11_contract_valid"] is False
    assert op01["dhd_op01_waiting_for_explicit_dhc_r11_material"] is True
    assert op01["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_WAIT_FOR_EXPLICIT_DHC_R11_MATERIAL_REF
    _assert_no_execution_or_promotion(op01)


def test_op01_accepts_explicit_dhc_r11_bodyfree_material_without_dhr_op06_permission() -> None:
    op01 = _op01(_dhc_r11())

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_status_ref"] == OP01_READY
    assert op01["dhc_r11_contract_valid"] is True
    assert op01["dhd_op01_intake_ready"] is True
    assert op01["dhd_op01_ready_for_op02_dhc_outcome_check"] is True
    assert op01["current_dhc_result_selected_here"] is False
    assert op01["dhr_op06_consideration_decided_here"] is False
    assert op01["dhr_op06_builder_called_here"] is False
    assert op01["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF
    _assert_no_execution_or_promotion(op01)


def test_op01_records_optional_dhc_op08_presence_without_validation_or_selection() -> None:
    explicit_op08 = {
        "material_id": "explicit_current_dhc_op08_material_for_future_op02",
        "body_free": True,
    }
    op01 = _op01(_dhc_r11(), dhc_op08=explicit_op08)

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_status_ref"] == OP01_READY_WITH_DHC_OP08
    assert op01["explicit_dhc_op08_material_present"] is True
    assert op01["dhd_op01_intake_ready_with_explicit_dhc_op08_material"] is True
    assert op01["current_dhc_result_selected_here"] is False
    assert op01["dhd_op01_does_not_select_current_dhc_result"] is True
    assert op01["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF
    _assert_no_execution_or_promotion(op01)


def test_op01_records_optional_dhr_op05_wrapper_presence_without_selection_or_op06_call() -> None:
    wrapper = {
        "material_id": "current_existing_dhr_op05_wrapper_for_future_op02",
        "body_free": True,
    }
    op01 = _op01(_dhc_r11(), dhr_op05=wrapper)

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_status_ref"] == OP01_READY
    assert op01["current_existing_dhr_op05_result_wrapper_present"] is True
    assert op01["current_existing_dhr_op05_result_wrapper_selected_here"] is False
    assert op01["dhd_op01_does_not_select_current_dhr_op05_wrapper"] is True
    assert op01["dhr_op06_builder_called_here"] is False
    _assert_no_execution_or_promotion(op01)


@pytest.mark.parametrize(
    "material",
    [
        "not-a-mapping",
        _dhc_r11(source_mode="wrong"),
        _dhc_r11(body_free=False),
        _dhc_r11(recommended_next_work_candidate="direct DHR-OP06 call"),
        {
            "source_mode": "local_received_zip_only",
            "current_execution_allowance": "none",
            "body_free": True,
        },
    ],
)
def test_op01_invalid_dhc_r11_shape_requires_repair_without_downstream(
    material: object,
) -> None:
    op01 = _op01(material)

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_status_ref"] == OP01_REPAIR
    assert op01["dhd_op01_repair_required"] is True
    assert op01["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_DHC_R11_INTAKE_REF
    _assert_no_execution_or_promotion(op01)


@pytest.mark.parametrize(
    ("updates", "expected_path_fragment"),
    [
        ({"raw_input": "body"}, "raw_input"),
        ({"question_text": "question"}, "question_text"),
        ({"dhr_op06_call": "called"}, "dhr_op06_call"),
        ({"release_decision": "allowed"}, "release_decision"),
        ({"current_execution_allowance": "runtime"}, "current_execution_allowance"),
        ({"api_changed": True}, "api_changed"),
        ({"nested": {"stdout": "output"}}, "stdout"),
    ],
)
def test_op01_blocks_body_like_promotion_autorun_or_no_touch_claims(
    updates: dict[str, object], expected_path_fragment: str
) -> None:
    op01 = _op01(_dhc_r11(**updates))

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_status_ref"] == OP01_BLOCKED
    assert op01["dhd_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert op01["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_DHC_R11_INTAKE_REF
    paths = (
        tuple(op01["dhc_r11_input_forbidden_payload_key_path_refs"])
        + tuple(op01["dhc_r11_input_body_like_value_path_refs"])
        + tuple(op01["dhc_r11_input_promotion_or_autorun_claim_path_refs"])
        + tuple(op01["dhc_r11_input_no_touch_mutation_path_refs"])
    )
    assert any(expected_path_fragment in path for path in paths)
    _assert_no_execution_or_promotion(op01)


def test_op01_blocks_forbidden_payload_in_optional_material_without_carrying_body() -> None:
    optional_op08 = {
        "material_id": "unsafe_optional_dhc_op08",
        "comment_text": "must not be carried",
    }
    op01 = _op01(_dhc_r11(), dhc_op08=optional_op08)

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_status_ref"] == OP01_BLOCKED
    assert "comment_text" not in op01
    assert any(
        "optional_explicit_dhc_op08.comment_text" in path
        for path in op01["dhc_r11_input_forbidden_payload_key_path_refs"]
    )
    _assert_no_execution_or_promotion(op01)


def test_op01_invalid_or_missing_op00_refreeze_requires_repair() -> None:
    invalid_op00 = deepcopy(_op00())
    invalid_op00["current_execution_allowance_ref"] = "DHR_OP06"
    op01 = _op01(_dhc_r11(), op00=invalid_op00)

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["op00_contract_valid"] is False
    assert op01["dhd_op01_status_ref"] == OP01_REPAIR
    assert op01["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_DHC_R11_INTAKE_REF
    _assert_no_execution_or_promotion(op01)


def test_op01_does_not_call_dhc_dhr_op05_or_dhr_op06_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("DHD-OP01 must not call DHC/DHR builders")

    monkeypatch.setattr(dhc, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF, explode)
    monkeypatch.setattr(dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF, explode)
    monkeypatch.setattr(dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF, explode)

    op01 = _op01(_dhc_r11())

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True
    assert op01["dhd_op01_does_not_call_dhc_builder"] is True
    assert op01["dhd_op01_does_not_call_existing_dhr_op05_builder"] is True
    assert op01["dhd_op01_does_not_call_dhr_op06_builder"] is True
    assert op01["dhd_op01_does_not_use_dhr_op06_implicit_op05_fallback"] is True
    _assert_no_execution_or_promotion(op01)


def test_op01_output_contains_only_bodyfree_metadata_not_input_materials() -> None:
    op01 = _op01(_dhc_r11(), dhc_op08={"material_id": "safe_op08"})

    for forbidden_key in dhd.P7_R54_AHR_POST_DHC_DHD_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in op01
    assert "explicit_dhc_r11_bodyfree_next_work_decision_material" not in op01
    assert "optional_explicit_dhc_op08_result_memo_closure_material" not in op01
    assert "optional_current_existing_dhr_op05_result_wrapper" not in op01
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(op01) is True


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("body_free", False),
        ("dhc_builder_call_allowed_here", True),
        ("dhc_result_synthesis_allowed_here", True),
        ("current_dhc_result_selected_here", True),
        ("current_existing_dhr_op05_result_wrapper_selected_here", True),
        ("dhr_op06_consideration_decided_here", True),
        ("dhr_op06_builder_called_here", True),
        ("dhr_op06_implicit_op05_fallback_used_here", True),
        ("p7_readfeel_evaluation_started_here", True),
        ("p8_question_design_started", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_op01_assert_rejects_execution_selection_fallback_or_promotion_mutations(
    key: str, bad_value: object
) -> None:
    bad = deepcopy(_op01(_dhc_r11()))
    bad[key] = bad_value

    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(bad)


def test_op01_assert_rejects_unplanned_field_addition() -> None:
    bad = deepcopy(_op01(_dhc_r11()))
    bad["unexpected_runtime_execution"] = True

    with pytest.raises(ValueError, match="field set changed"):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(bad)
