# -*- coding: utf-8 -*-
"""DHC R2 OP00/OP01 target tests.

These tests cover only the Post-DHB scope refreeze and explicit DHB-OP08
closure-material intake boundary.  They deliberately stop before DHC-OP02 and
must not call DHB/DHR builders.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb

OP00_SCOPE_REFROZEN = dhc.P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS[0]
OP01_READY = dhc.P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[0]
OP01_ROUTE_PRESERVED = dhc.P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[1]
OP01_WAITING = dhc.P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[2]
OP01_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[3]
OP01_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[4]

DHB_OP08_CLOSED = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]
DHB_OP08_NON_DHR = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[1]
DHB_OP08_WAITING = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[2]
DHB_OP08_REPAIR = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[3]
DHB_OP08_BLOCKED = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[4]


def _op00() -> dict[str, object]:
    return dhc.build_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11()


def _dhb_op08(status: str = DHB_OP08_CLOSED, **updates: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": dhb.P7_R54_AHR_POST_PCM_DHB_OP08_SCHEMA_VERSION,
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
        "material_id": "fixture_explicit_dhb_op08_bodyfree_closure_material",
        "dhb_op08_status_ref": status,
        "bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref": status,
        "body_free": True,
        "git_connection_required": False,
        "git_checked": False,
        "dhr_op05_called_here": False,
        "existing_dhr_op05_builder_called_here": False,
        "dhr_op06_called_here": False,
        "p8_question_design_started": False,
        "release_allowed": False,
        "dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped": status == DHB_OP08_CLOSED,
        "dhr_op05_manual_handoff_envelope_ready": status == DHB_OP08_CLOSED,
        "dhr_op05_call_still_requires_separate_explicit_instruction": status == DHB_OP08_CLOSED,
        "dhb_op08_not_dhr_op05_lane_route_preserved_stopped": status == DHB_OP08_NON_DHR,
        "non_dhr_lane_route_preserved": status == DHB_OP08_NON_DHR,
    }
    data.update(updates)
    if "dhb_op08_status_ref" in updates and "bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref" not in updates:
        data["bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref"] = updates["dhb_op08_status_ref"]
    return data


def _no_downstream(data: dict[str, object]) -> None:
    for key in (
        "dhb_op08_material_synthesized_here",
        "dhb_builder_called_here",
        "manual_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created_here",
        "p7_complete",
        "release_allowed",
    ):
        assert data[key] is False, key


def test_r2_keeps_r0_r1_summary_valid_and_uncalled() -> None:
    r1 = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(r1) is True
    assert r1["existing_dhr_op05_builder_called_here"] is False
    assert r1["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF


def test_op00_refreezes_scope_without_execution_permission() -> None:
    op00 = _op00()
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11_contract(op00) is True
    assert op00["dhc_op00_status_ref"] == OP00_SCOPE_REFROZEN
    assert op00["dhb_closure_is_not_dhr_op05_execution"] is True
    assert op00["dhb_closure_is_not_p8_start"] is True
    assert op00["dhb_target_green_is_not_release_readiness"] is True
    assert op00["dhb_op08_material_synthesis_allowed_here"] is False
    assert op00["dhb_builder_call_allowed_here"] is False
    assert op00["existing_dhr_op05_builder_call_allowed_here"] is False
    assert op00["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF
    assert dhc.P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF in op00["not_yet_implemented_steps"]
    _no_downstream(op00)


@pytest.mark.parametrize(
    "key",
    [
        "body_free",
        "dhb_op08_material_synthesis_allowed_here",
        "dhb_builder_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op05_called_here",
        "dhr_op06_called_here",
        "p8_question_design_started",
        "release_allowed",
    ],
)
def test_op00_assert_rejects_bodyfree_execution_or_promotion_mutations(key: str) -> None:
    op00 = _op00()
    bad = deepcopy(op00)
    bad[key] = False if key == "body_free" else True
    with pytest.raises(ValueError):
        dhc.assert_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11_contract(bad)


def test_op01_missing_dhb_op08_waits_without_builder_call() -> None:
    op01 = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=None,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert op01["dhc_op01_status_ref"] == OP01_WAITING
    assert op01["dhc_op01_waiting_for_explicit_dhb_op08_closed_material"] is True
    assert op01["dhb_op08_material_present"] is False
    assert op01["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REF
    _no_downstream(op01)


def test_op01_closed_dhr_lane_intake_ready_stops_before_op02_execution() -> None:
    op01 = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=_dhb_op08(),
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert op01["dhc_op01_status_ref"] == OP01_READY
    assert op01["bodyfree_dhb_op08_closed_handoff_material_intake_status_ref"] == OP01_READY
    assert op01["dhr_lane_closed_intake_ready"] is True
    assert op01["dhr_op05_lane_confirmed_from_explicit_dhb_op08"] is True
    assert op01["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF
    assert dhc.P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF in op01["not_yet_implemented_steps"]
    _no_downstream(op01)


def test_op01_non_dhr_lane_route_preserved_without_dhr_call() -> None:
    op01 = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=_dhb_op08(DHB_OP08_NON_DHR),
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert op01["dhc_op01_status_ref"] == OP01_ROUTE_PRESERVED
    assert op01["dhc_op01_non_dhr_lane_route_preserved_stopped"] is True
    assert op01["dhr_lane_closed_intake_ready"] is False
    assert op01["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_PRESERVE_NON_DHR_LANE_ROUTE_REF
    _no_downstream(op01)


@pytest.mark.parametrize(
    ("material", "expected_status", "expected_next"),
    [
        (_dhb_op08(schema_version="wrong"), OP01_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF),
        (_dhb_op08(operation_step_ref="wrong"), OP01_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF),
        (_dhb_op08(body_free=False), OP01_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF),
        (_dhb_op08(git_checked=True), OP01_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF),
        (_dhb_op08(git_connection_required=True), OP01_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF),
        (_dhb_op08(bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref="mismatch"), OP01_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF),
        (_dhb_op08(DHB_OP08_WAITING), OP01_WAITING, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REF),
        (_dhb_op08(DHB_OP08_REPAIR), OP01_REPAIR, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF),
        (_dhb_op08(DHB_OP08_BLOCKED), OP01_BLOCKED, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF),
        (_dhb_op08(question_text="raw"), OP01_BLOCKED, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF),
        (_dhb_op08(comment_text="raw"), OP01_BLOCKED, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF),
        (_dhb_op08(dhr_op06_called_here=True), OP01_BLOCKED, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF),
        (_dhb_op08(api_changed=True), OP01_BLOCKED, dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF),
    ],
)
def test_op01_invalid_waiting_repair_or_blocked_materials_stop_without_call(
    material: dict[str, object],
    expected_status: str,
    expected_next: str,
) -> None:
    op01 = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=material,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert op01["dhc_op01_status_ref"] == expected_status
    assert op01["next_required_step"] == expected_next
    _no_downstream(op01)


def test_op01_rejects_missing_or_invalid_op00_scope_refreeze_as_repair() -> None:
    op01 = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=None,
        explicit_dhb_op08_bodyfree_closure_material=_dhb_op08(),
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert op01["op00_material_present"] is False
    assert op01["op00_contract_valid"] is False
    assert op01["dhc_op01_status_ref"] == OP01_REPAIR
    assert op01["existing_dhr_op05_builder_called_here"] is False


def test_op01_does_not_call_dhb_or_dhr_builders(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("DHC-OP01 must not call builders")

    monkeypatch.setattr(dhb, "build_p7_r54_ahr_post_pcm_dhb_op08_bodyfree_dhr_op05_manual_handoff_boundary_closure", explode)
    monkeypatch.setattr(dhr, "build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan", explode)
    op01 = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=_dhb_op08(),
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert op01["dhb_builder_called_here"] is False
    assert op01["existing_dhr_op05_builder_called_here"] is False
    assert op01["dhr_op05_called_here"] is False


@pytest.mark.parametrize(
    "key",
    [
        "body_free",
        "dhb_op08_material_synthesis_allowed_here",
        "dhb_builder_call_allowed_here",
        "dhb_op08_material_synthesized_here",
        "dhb_builder_called_here",
        "dhr_op05_manual_handoff_envelope_created_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op05_called_here",
        "dhr_op06_called_here",
        "p8_question_design_started",
        "release_allowed",
    ],
)
def test_op01_assert_rejects_boundary_mutations(key: str) -> None:
    op01 = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=_dhb_op08(),
    )
    bad = deepcopy(op01)
    bad[key] = False if key == "body_free" else True
    with pytest.raises(ValueError):
        dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(bad)
