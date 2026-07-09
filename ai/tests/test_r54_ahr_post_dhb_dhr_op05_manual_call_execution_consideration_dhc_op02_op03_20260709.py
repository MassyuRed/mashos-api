# -*- coding: utf-8 -*-
"""DHC R3 OP02/OP03 target tests.

These tests cover only explicit DHR-OP04 material eligibility and the manual-call
permission gate.  They deliberately stop before DHC-OP04 and must not call the
existing DHR-OP05 builder.
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
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704 import (
    _op04_confirmed_separation,
    _op04_not_confirmed_separation,
)

OP02_ELIGIBLE = dhc.P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[0]
OP02_WAITING = dhc.P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[1]
OP02_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[2]
OP02_ENVELOPE_ONLY = dhc.P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[3]
OP02_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[4]

OP03_ALLOWED = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[0]
OP03_NOT_REQUESTED = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[1]
OP03_WAITING_REQUEST = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[2]
OP03_WAITING_OP04 = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[3]
OP03_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[4]
OP03_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[5]

DHB_OP08_CLOSED = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]
DHB_OP08_NON_DHR = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[1]


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
    return data


def _op01_ready() -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=_dhb_op08(),
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(material) is True
    return material


def _op01_waiting() -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
        op00_scope_refreeze=_op00(),
        explicit_dhb_op08_bodyfree_closure_material=None,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(material) is True
    return material


def _op02_eligible(op04: dict[str, object] | None = None) -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=op04 or _op04_not_confirmed_separation(),
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(material) is True
    assert material["dhc_op02_status_ref"] == OP02_ELIGIBLE
    return material


def _no_downstream(data: dict[str, object], *, permission_allowed: bool = False) -> None:
    if not permission_allowed:
        assert data.get("manual_call_allowed_here") is False
        assert data.get("existing_dhr_op05_builder_call_allowed_here") is False
    for key in (
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_result_present",
        "existing_dhr_op05_contract_valid",
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


def test_r3_keeps_r0_r1_r2_materials_present_and_valid() -> None:
    r1 = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()
    op00 = _op00()
    op01 = _op01_ready()

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(r1) is True
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11_contract(op00) is True
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert op01["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF


def test_op02_missing_explicit_dhr_op04_waits_without_builder_call() -> None:
    op02 = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=None,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert op02["dhc_op02_status_ref"] == OP02_WAITING
    assert op02["explicit_dhr_op04_material_present"] is False
    assert op02["existing_dhr_op04_assert_called_here"] is False
    assert op02["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF
    _no_downstream(op02)


def test_op02_dhb_handoff_envelope_only_is_not_builder_input() -> None:
    envelope = {
        "schema_version": "bodyfree_dhb_op04_envelope_ref_only",
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
        "body_free": True,
        "dhr_op05_manual_handoff_envelope_ready": True,
    }
    op02 = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=None,
        optional_dhb_op04_manual_handoff_envelope=envelope,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert op02["dhc_op02_status_ref"] == OP02_ENVELOPE_ONLY
    assert op02["dhb_envelope_only_without_explicit_op04"] is True
    assert op02["dhb_handoff_envelope_used_as_dhr_op04_input_here"] is False
    assert op02["existing_dhr_op04_assert_called_here"] is False
    assert op02["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_DHB_ENVELOPE_ONLY_NOT_BUILDER_INPUT_REF
    _no_downstream(op02)


@pytest.mark.parametrize("op04_factory", [_op04_not_confirmed_separation, _op04_confirmed_separation])
def test_op02_explicit_dhr_op04_contract_valid_becomes_eligible(op04_factory: object) -> None:
    op04 = op04_factory()
    op02 = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=op04,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert op02["dhc_op02_status_ref"] == OP02_ELIGIBLE
    assert op02["explicit_dhr_op04_contract_valid"] is True
    assert op02["explicit_dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan"] is True
    assert op02["existing_dhr_op04_assert_called_here"] is True
    assert op02["dhc_op02_existing_dhr_op05_builder_input_eligible_explicit_op04"] is True
    assert op02["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF
    _no_downstream(op02)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "wrong"),
        ("operation_step_ref", "wrong"),
        ("body_free", False),
        ("dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan", False),
    ],
)
def test_op02_invalid_explicit_dhr_op04_contract_repairs_without_builder_call(field: str, value: object) -> None:
    op04 = _op04_not_confirmed_separation()
    op04[field] = value

    op02 = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=op04,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert op02["dhc_op02_status_ref"] == OP02_REPAIR
    assert op02["explicit_dhr_op04_contract_valid"] is False
    assert op02["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF
    _no_downstream(op02)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("question_text", "raw question must not be retained"),
        ("comment_text", "raw comment must not be retained"),
        ("helper_green_promoted_to_actual_source", True),
        ("actual_operation_receipt_created_by_helper_here", True),
        ("dhr_op06_called_here", True),
        ("release_allowed", True),
    ],
)
def test_op02_body_leak_promotion_or_autorun_blocks_without_raw_value(field: str, value: object) -> None:
    op04 = _op04_not_confirmed_separation()
    op04[field] = value

    op02 = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=op04,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert op02["dhc_op02_status_ref"] == OP02_BLOCKED
    assert op02["dhc_op02_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert op02["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHR_OP04_INPUT_BODY_LEAK_PROMOTION_OR_AUTORUN_REF
    assert "raw question must not be retained" not in repr(op02)
    assert "raw comment must not be retained" not in repr(op02)
    _no_downstream(op02)


def test_op02_non_ready_op01_repairs_before_dhr_op04_eligibility() -> None:
    op02 = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_waiting(),
        explicit_dhr_op04_actual_source_claim_separation=_op04_not_confirmed_separation(),
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert op02["op01_contract_valid"] is True
    assert op02["op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check"] is False
    assert op02["dhc_op02_status_ref"] == OP02_REPAIR
    _no_downstream(op02)


def test_op02_does_not_call_dhr_op04_builder_or_dhr_op05_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    op04 = _op04_not_confirmed_separation()

    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("DHC-OP02 must not call builders")

    monkeypatch.setattr(dhr, "build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification", explode)
    monkeypatch.setattr(dhr, "build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan", explode)

    op02 = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=op04,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert op02["dhr_op04_builder_called_here"] is False
    assert op02["existing_dhr_op05_builder_called_here"] is False
    assert op02["existing_dhr_op04_assert_called_here"] is True


def test_op03_manual_call_not_requested_stops_before_builder_permission() -> None:
    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(),
        manual_call_requested=False,
        allow_existing_dhr_op05_builder_call=True,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True
    assert op03["dhc_op03_status_ref"] == OP03_NOT_REQUESTED
    assert op03["manual_call_allowed"] is False
    assert op03["existing_dhr_op05_builder_call_allowed_here"] is False
    assert op03["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_MANUAL_CALL_NOT_REQUESTED_STOP_REF
    _no_downstream(op03)


@pytest.mark.parametrize(
    ("request_ref", "allow_builder"),
    [
        (None, True),
        ("", True),
        ("manual_request_without_builder_allow", False),
    ],
)
def test_op03_waits_for_explicit_manual_request_ref_and_builder_allow_flag(
    request_ref: str | None,
    allow_builder: bool,
) -> None:
    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(),
        manual_call_requested=True,
        manual_call_request_ref=request_ref,
        allow_existing_dhr_op05_builder_call=allow_builder,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True
    assert op03["dhc_op03_status_ref"] == OP03_WAITING_REQUEST
    assert op03["manual_call_requested_here"] is True
    assert op03["manual_call_allowed_here"] is False
    assert op03["existing_dhr_op05_builder_call_allowed_here"] is False
    assert op03["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_MANUAL_CALL_REQUEST_REF
    _no_downstream(op03)


def test_op03_allows_only_future_dhc_op04_call_and_does_not_call_builder() -> None:
    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(_op04_confirmed_separation()),
        manual_call_requested=True,
        manual_call_request_ref="r3_explicit_manual_call_request_ref",
        allow_existing_dhr_op05_builder_call=True,
        allow_implicit_op04_builder_fallback=False,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True
    assert op03["dhc_op03_status_ref"] == OP03_ALLOWED
    assert op03["manual_call_allowed"] is True
    assert op03["manual_call_allowed_here"] is True
    assert op03["existing_dhr_op05_builder_call_allowed_here"] is True
    assert op03["permission_allowed_but_existing_builder_not_called_until_dhc_op04"] is True
    assert op03["existing_dhr_op05_builder_called_here"] is False
    assert op03["existing_dhr_op05_result_generated_here"] is False
    assert op03["implicit_op04_builder_fallback_allowed_here"] is False
    assert op03["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF
    _no_downstream(op03, permission_allowed=True)


def test_op03_waits_for_explicit_dhr_op04_when_op02_is_waiting() -> None:
    op02_waiting = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=None,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02_waiting) is True

    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=op02_waiting,
        manual_call_requested=True,
        manual_call_request_ref="manual_request_waits_for_op04",
        allow_existing_dhr_op05_builder_call=True,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True
    assert op03["dhc_op03_status_ref"] == OP03_WAITING_OP04
    assert op03["op02_existing_dhr_op05_builder_input_eligible_explicit_op04"] is False
    assert op03["manual_call_allowed"] is False
    _no_downstream(op03)


def test_op03_repairs_invalid_op02_permission_input() -> None:
    op02 = _op02_eligible()
    bad_op02 = deepcopy(op02)
    bad_op02["schema_version"] = "wrong"

    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=bad_op02,
        manual_call_requested=True,
        manual_call_request_ref="manual_request_ref",
        allow_existing_dhr_op05_builder_call=True,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True
    assert op03["dhc_op03_status_ref"] == OP03_REPAIR
    assert op03["op02_contract_valid"] is False
    assert op03["manual_call_allowed"] is False
    _no_downstream(op03)


def test_op03_blocks_implicit_op04_builder_fallback_request() -> None:
    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(),
        manual_call_requested=True,
        manual_call_request_ref="manual_request_ref",
        allow_existing_dhr_op05_builder_call=True,
        allow_implicit_op04_builder_fallback=True,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True
    assert op03["dhc_op03_status_ref"] == OP03_BLOCKED
    assert op03["allow_implicit_op04_builder_fallback_input"] is True
    assert op03["implicit_op04_builder_fallback_allowed_here"] is False
    assert op03["manual_call_allowed"] is False
    _no_downstream(op03)


def test_op03_does_not_call_existing_dhr_op05_builder_even_when_permission_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("DHC-OP03 must not call existing DHR-OP05 builder")

    monkeypatch.setattr(dhr, "build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan", explode)
    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(),
        manual_call_requested=True,
        manual_call_request_ref="manual_request_ref",
        allow_existing_dhr_op05_builder_call=True,
        allow_implicit_op04_builder_fallback=False,
    )

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True
    assert op03["dhc_op03_status_ref"] == OP03_ALLOWED
    assert op03["existing_dhr_op05_builder_called_here"] is False
    assert op03["existing_dhr_op05_result_present"] is False


@pytest.mark.parametrize(
    "key",
    [
        "body_free",
        "manual_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op05_called_here",
        "dhr_op06_called_here",
        "p8_question_design_started",
        "release_allowed",
    ],
)
def test_op02_assert_rejects_execution_or_promotion_mutations(key: str) -> None:
    op02 = _op02_eligible()
    bad = deepcopy(op02)
    bad[key] = False if key == "body_free" else True
    with pytest.raises(ValueError):
        dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(bad)


@pytest.mark.parametrize(
    "key",
    [
        "body_free",
        "implicit_op04_builder_fallback_allowed_here",
        "implicit_op04_builder_fallback_used_here",
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_result_present",
        "dhr_op06_called_here",
        "p8_question_design_started",
        "release_allowed",
    ],
)
def test_op03_assert_rejects_execution_or_promotion_mutations(key: str) -> None:
    op03 = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(),
        manual_call_requested=True,
        manual_call_request_ref="manual_request_ref",
        allow_existing_dhr_op05_builder_call=True,
    )
    bad = deepcopy(op03)
    bad[key] = False if key == "body_free" else True
    with pytest.raises(ValueError):
        dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(bad)
