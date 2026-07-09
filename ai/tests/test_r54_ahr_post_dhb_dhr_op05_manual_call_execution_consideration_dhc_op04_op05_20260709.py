# -*- coding: utf-8 -*-
"""DHC R4 OP04/OP05 target tests.

These tests cover only the controlled existing DHR-OP05 manual call boundary and
DHC-side stopped result classification. They must not execute DHR-OP06, DHR-OP07,
DMD/R52, actual review, P8, release, API/DB/RN/runtime/response-key changes, or
json/schema file creation.
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
OP03_ALLOWED = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[0]
OP03_NOT_REQUESTED = dhc.P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[1]

OP04_CALLED = dhc.P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[0]
OP04_NOT_CALLED = dhc.P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[1]
OP04_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[2]
OP04_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[3]

OP05_SCAN_CLEAR = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]
OP05_WAITING = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[1]
OP05_REPAIR = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2]
OP05_NOT_CALLED = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[3]
OP05_BLOCKED = dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[4]

DHB_OP08_CLOSED = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]


def _op00() -> dict[str, object]:
    return dhc.build_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11()


def _dhb_op08(**updates: object) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": dhb.P7_R54_AHR_POST_PCM_DHB_OP08_SCHEMA_VERSION,
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
        "material_id": "fixture_explicit_dhb_op08_bodyfree_closure_material",
        "dhb_op08_status_ref": DHB_OP08_CLOSED,
        "bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref": DHB_OP08_CLOSED,
        "body_free": True,
        "git_connection_required": False,
        "git_checked": False,
        "dhr_op05_called_here": False,
        "existing_dhr_op05_builder_called_here": False,
        "dhr_op06_called_here": False,
        "p8_question_design_started": False,
        "release_allowed": False,
        "dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped": True,
        "dhr_op05_manual_handoff_envelope_ready": True,
        "dhr_op05_call_still_requires_separate_explicit_instruction": True,
        "dhb_op08_not_dhr_op05_lane_route_preserved_stopped": False,
        "non_dhr_lane_route_preserved": False,
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


def _op02_eligible(op04: dict[str, object] | None = None) -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
        op01_dhb_op08_intake=_op01_ready(),
        explicit_dhr_op04_actual_source_claim_separation=op04 or _op04_confirmed_separation(),
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(material) is True
    assert material["dhc_op02_status_ref"] == OP02_ELIGIBLE
    return material


def _op03_allowed(op04: dict[str, object] | None = None) -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(op04 or _op04_confirmed_separation()),
        manual_call_requested=True,
        manual_call_request_ref="r4_explicit_manual_call_request_ref",
        allow_existing_dhr_op05_builder_call=True,
        allow_implicit_op04_builder_fallback=False,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(material) is True
    assert material["dhc_op03_status_ref"] == OP03_ALLOWED
    return material


def _op03_not_requested(op04: dict[str, object] | None = None) -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
        op02_input_eligibility=_op02_eligible(op04 or _op04_confirmed_separation()),
        manual_call_requested=False,
        manual_call_request_ref="r4_manual_call_not_requested_ref",
        allow_existing_dhr_op05_builder_call=True,
        allow_implicit_op04_builder_fallback=False,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(material) is True
    assert material["dhc_op03_status_ref"] == OP03_NOT_REQUESTED
    return material


def _build_op04(
    op03: dict[str, object] | None = None,
    op04: dict[str, object] | None = None,
    *,
    allow_implicit_op04_builder_fallback: bool = False,
) -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op04_existing_dhr_op05_preflight_scan_manual_call_boundary(
        op03_manual_call_permission=op03,
        explicit_dhr_op04_actual_source_claim_separation=op04,
        allow_implicit_op04_builder_fallback=allow_implicit_op04_builder_fallback,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op04_existing_dhr_op05_preflight_scan_manual_call_boundary_contract(material) is True
    return material


def _classify(op04: dict[str, object], explicit_result: dict[str, object] | None = None) -> dict[str, object]:
    material = dhc.build_p7_r54_ahr_post_dhb_dhc_op05_existing_dhr_op05_result_classification(
        op04_existing_dhr_op05_preflight_scan_manual_call_boundary=op04,
        existing_dhr_op05_preflight_scan_result=explicit_result,
    )
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op05_existing_dhr_op05_result_classification_contract(material) is True
    return material


def _assert_no_downstream(data: dict[str, object]) -> None:
    for key in (
        "dhr_op06_call_allowed_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_r52_execution_allowed_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_allowed_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "release_decision_allowed_here",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created_here",
        "p7_complete",
        "release_allowed",
    ):
        assert data[key] is False, key


def test_r4_keeps_r0_to_r3_present_and_valid() -> None:
    r1 = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()
    op00 = _op00()
    op01 = _op01_ready()
    op02 = _op02_eligible(_op04_confirmed_separation())
    op03 = _op03_allowed(_op04_confirmed_separation())

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(r1) is True
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11_contract(op00) is True
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(op01) is True
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(op02) is True
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(op03) is True


def test_op04_without_permission_does_not_call_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    op04_input = _op04_confirmed_separation()

    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("DHC-OP04 must not call builder without OP03 permission")

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF, explode)
    op04 = _build_op04(_op03_not_requested(op04_input), op04_input)

    assert op04["dhc_op04_status_ref"] == OP04_NOT_CALLED
    assert op04["existing_dhr_op05_builder_called_here"] is False
    assert op04["existing_dhr_op05_result_present"] is False
    assert op04["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_NOT_CALLED_STOP_REF
    _assert_no_downstream(op04)


def test_op04_missing_explicit_op04_does_not_use_implicit_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    op03 = _op03_allowed(_op04_confirmed_separation())

    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("DHC-OP04 must not call existing builder with None OP04 input")

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF, explode)
    op04 = _build_op04(op03, None)

    assert op04["dhc_op04_status_ref"] == OP04_NOT_CALLED
    assert op04["explicit_dhr_op04_material_present"] is False
    assert op04["existing_dhr_op04_assert_called_here"] is False
    assert op04["existing_dhr_op05_builder_called_here"] is False
    assert op04["implicit_op04_builder_fallback_used_here"] is False
    assert op04["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_NOT_CALLED_STOPPED_REF
    _assert_no_downstream(op04)


def test_op04_permission_allowed_with_explicit_op04_calls_existing_builder_once(monkeypatch: pytest.MonkeyPatch) -> None:
    op04_input = _op04_confirmed_separation()
    op03 = _op03_allowed(op04_input)
    real_builder = getattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF)
    call_log: list[dict[str, object]] = []

    def wrapped_builder(*args: object, **kwargs: object) -> dict[str, object]:
        call_log.append(dict(kwargs))
        return real_builder(*args, **kwargs)

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF, wrapped_builder)
    op04 = _build_op04(op03, op04_input)

    assert len(call_log) == 1
    assert call_log[0]["actual_source_claim_separation"] is op04_input
    assert call_log[0].get("op04_actual_source_claim_separation") is None
    assert isinstance(call_log[0]["additional_bodyfree_materials"], list)
    assert op04["dhc_op04_status_ref"] == OP04_CALLED
    assert op04["existing_dhr_op05_builder_called_here"] is True
    assert op04["existing_dhr_op05_builder_called_count"] == 1
    assert op04["existing_dhr_op05_contract_valid"] is True
    assert op04["existing_dhr_op05_status_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF
    assert op04["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF
    _assert_no_downstream(op04)


def test_op04_waiting_existing_result_is_called_but_not_downstream() -> None:
    op04_input = _op04_not_confirmed_separation()
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)

    assert op04["dhc_op04_status_ref"] == OP04_CALLED
    assert op04["existing_dhr_op05_builder_called_here"] is True
    assert op04["existing_dhr_op05_contract_valid"] is True
    assert op04["existing_dhr_op05_status_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_WAITING_OR_INCOMPLETE_STATUS_REF
    assert op04["existing_dhr_op05_preflight_waiting_or_incomplete"] is True
    _assert_no_downstream(op04)


def test_op04_blocks_implicit_op04_builder_fallback_request(monkeypatch: pytest.MonkeyPatch) -> None:
    op04_input = _op04_confirmed_separation()

    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("implicit OP04 fallback request must block before existing builder")

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF, explode)
    op04 = _build_op04(_op03_allowed(op04_input), op04_input, allow_implicit_op04_builder_fallback=True)

    assert op04["dhc_op04_status_ref"] == OP04_BLOCKED
    assert op04["allow_implicit_op04_builder_fallback_input"] is True
    assert op04["implicit_op04_builder_fallback_allowed_here"] is False
    assert op04["existing_dhr_op05_builder_called_here"] is False
    assert op04["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_BLOCKED_REF
    _assert_no_downstream(op04)


def test_op04_builder_exception_is_sanitized_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    op04_input = _op04_confirmed_separation()

    def fail_builder(*args: object, **kwargs: object) -> dict[str, object]:
        raise RuntimeError("raw secret body / traceback should not be retained")

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF, fail_builder)
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)

    assert op04["dhc_op04_status_ref"] == OP04_REPAIR
    assert op04["existing_dhr_op05_builder_called_here"] is True
    assert op04["existing_dhr_op05_builder_called_count"] == 1
    assert op04["existing_dhr_op05_result_present"] is False
    assert op04["existing_dhr_op05_contract_valid"] is False
    assert op04["existing_dhr_op05_builder_exception_type_ref"] == "RuntimeError"
    assert "raw secret body" not in repr(op04)
    assert "traceback should not be retained" not in repr(op04)
    _assert_no_downstream(op04)


def test_op04_assert_exception_is_sanitized_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    op04_input = _op04_confirmed_separation()

    def fail_assert(data: object) -> None:
        raise ValueError("raw assert body must not be retained")

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF, fail_assert)
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)

    assert op04["dhc_op04_status_ref"] == OP04_REPAIR
    assert op04["existing_dhr_op05_builder_called_here"] is True
    assert op04["existing_dhr_op05_assert_called_here"] is True
    assert op04["existing_dhr_op05_result_present"] is True
    assert op04["existing_dhr_op05_contract_valid"] is False
    assert op04["existing_dhr_op05_assert_exception_type_ref"] == "ValueError"
    assert "raw assert body" not in repr(op04)
    _assert_no_downstream(op04)


def test_op04_body_like_or_raw_key_blocks_before_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    op04_input = _op04_confirmed_separation()
    op04_input["question_text"] = "raw question body must not be retained"

    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("body-like OP04 input must block before existing builder")

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF, explode)
    op04 = _build_op04(_op03_allowed(_op04_confirmed_separation()), op04_input)

    assert op04["dhc_op04_status_ref"] == OP04_BLOCKED
    assert op04["existing_dhr_op05_builder_called_here"] is False
    assert op04["dhc_op04_call_input_forbidden_payload_key_path_count"] >= 1
    assert "raw question body" not in repr(op04)
    _assert_no_downstream(op04)


def test_op05_classifies_scan_clear_stopped_without_dhr_op06_call() -> None:
    op04_input = _op04_confirmed_separation()
    op05 = _classify(_build_op04(_op03_allowed(op04_input), op04_input))

    assert op05["dhc_result_classification_ref"] == OP05_SCAN_CLEAR
    assert op05["existing_dhr_op05_status_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF
    assert op05["existing_dhr_op05_next_required_step_is_not_dhc_execution_permission"] is True
    assert op05["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_SCAN_CLEAR_STOPPED_REF
    _assert_no_downstream(op05)


def test_op05_classifies_waiting_or_incomplete_stopped() -> None:
    op04_input = _op04_not_confirmed_separation()
    op05 = _classify(_build_op04(_op03_allowed(op04_input), op04_input))

    assert op05["dhc_result_classification_ref"] == OP05_WAITING
    assert op05["existing_dhr_op05_status_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_WAITING_OR_INCOMPLETE_STATUS_REF
    assert op05["existing_dhr_op05_preflight_waiting_or_incomplete"] is True
    assert op05["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAITING_OR_INCOMPLETE_STOPPED_REF
    _assert_no_downstream(op05)


def test_op05_classifies_repair_required_stopped_from_explicit_existing_result() -> None:
    op04_input = _op04_confirmed_separation()
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)
    explicit_repair_result = getattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF)(
        actual_source_claim_separation=op04_input,
        additional_bodyfree_materials=[{"body_free": True, "helper_green_promoted_to_actual_source": True}],
        review_session_id="r4_repair_result_fixture",
    )
    assert explicit_repair_result["dhr_op05_status_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_REPAIR_REQUIRED_STATUS_REF

    op05 = _classify(op04, explicit_repair_result)

    assert op05["dhc_result_classification_ref"] == OP05_REPAIR
    assert op05["explicit_existing_dhr_op05_result_present"] is True
    assert op05["explicit_existing_dhr_op05_result_contract_valid"] is True
    assert op05["existing_dhr_op05_status_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_REPAIR_REQUIRED_STATUS_REF
    assert op05["existing_dhr_op05_preflight_repair_required"] is True
    assert op05["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_REQUIRED_STOPPED_REF
    _assert_no_downstream(op05)


def test_op05_classifies_not_called_stopped() -> None:
    op04_input = _op04_confirmed_separation()
    op05 = _classify(_build_op04(_op03_not_requested(op04_input), op04_input))

    assert op05["dhc_result_classification_ref"] == OP05_NOT_CALLED
    assert op05["existing_dhr_op05_builder_called_here"] is False
    assert op05["existing_dhr_op05_result_present"] is False
    assert op05["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_NOT_CALLED_STOPPED_REF
    _assert_no_downstream(op05)


def test_op05_classifies_blocked_stopped() -> None:
    op04_input = _op04_confirmed_separation()
    op05 = _classify(_build_op04(_op03_allowed(op04_input), op04_input, allow_implicit_op04_builder_fallback=True))

    assert op05["dhc_result_classification_ref"] == OP05_BLOCKED
    assert op05["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_STOPPED_REF
    assert op05["dhr_op06_called_here"] is False
    _assert_no_downstream(op05)


def test_op05_does_not_call_existing_builder_again(monkeypatch: pytest.MonkeyPatch) -> None:
    op04_input = _op04_confirmed_separation()
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)

    def explode(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("DHC-OP05 must not call existing DHR-OP05 builder again")

    monkeypatch.setattr(dhr, dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF, explode)
    op05 = _classify(op04)

    assert op05["dhc_result_classification_ref"] == OP05_SCAN_CLEAR
    assert op05["dhc_op05_does_not_call_existing_dhr_op05_builder_again"] is True


@pytest.mark.parametrize(
    "key",
    [
        "body_free",
        "dhr_op06_called_here",
        "dmd_execution_started_here",
        "p8_question_design_started",
        "release_allowed",
        "json_schema_file_created_here",
    ],
)
def test_op04_assert_rejects_execution_or_promotion_mutations(key: str) -> None:
    op04_input = _op04_confirmed_separation()
    op04 = _build_op04(_op03_allowed(op04_input), op04_input)
    bad = deepcopy(op04)
    bad[key] = False if key == "body_free" else True
    with pytest.raises(ValueError):
        dhc.assert_p7_r54_ahr_post_dhb_dhc_op04_existing_dhr_op05_preflight_scan_manual_call_boundary_contract(bad)


@pytest.mark.parametrize(
    "key",
    [
        "body_free",
        "dhr_op06_called_here",
        "dmd_execution_started_here",
        "p8_question_design_started",
        "release_allowed",
        "json_schema_file_created_here",
    ],
)
def test_op05_assert_rejects_execution_or_promotion_mutations(key: str) -> None:
    op04_input = _op04_confirmed_separation()
    op05 = _classify(_build_op04(_op03_allowed(op04_input), op04_input))
    bad = deepcopy(op05)
    bad[key] = False if key == "body_free" else True
    with pytest.raises(ValueError):
        dhc.assert_p7_r54_ahr_post_dhb_dhc_op05_existing_dhr_op05_result_classification_contract(bad)
