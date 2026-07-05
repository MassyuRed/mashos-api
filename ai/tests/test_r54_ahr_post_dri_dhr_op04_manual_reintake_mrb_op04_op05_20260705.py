# -*- coding: utf-8 -*-
"""R54-AHR Post-DRI / DHR-OP04 manual re-intake MRB-OP04/OP05 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_op03_20260705 import (
    _mrb_op02_ready as _imported_mrb_op02_ready,
    _dhr_op03_ready as _imported_dhr_op03_ready,
    _dhr_op03_waiting as _imported_dhr_op03_waiting,
)

_CACHED_READY_MATERIALS: dict[str, dict[str, object]] = {}


def _mrb_op02_ready() -> dict[str, object]:
    if "mrb_op02_ready" not in _CACHED_READY_MATERIALS:
        _CACHED_READY_MATERIALS["mrb_op02_ready"] = _imported_mrb_op02_ready()
    return deepcopy(_CACHED_READY_MATERIALS["mrb_op02_ready"])


def _dhr_op03_ready() -> dict[str, object]:
    if "dhr_op03_ready" not in _CACHED_READY_MATERIALS:
        _CACHED_READY_MATERIALS["dhr_op03_ready"] = _imported_dhr_op03_ready()
    return deepcopy(_CACHED_READY_MATERIALS["dhr_op03_ready"])


def _dhr_op03_waiting() -> dict[str, object]:
    if "dhr_op03_waiting" not in _CACHED_READY_MATERIALS:
        _CACHED_READY_MATERIALS["dhr_op03_waiting"] = _imported_dhr_op03_waiting()
    return deepcopy(_CACHED_READY_MATERIALS["dhr_op03_waiting"])


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object], *, allow_op05_call: bool = False) -> None:
    assert material["source_mode"] == mrb.P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["mrb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    allowed_true = set()
    if allow_op05_call:
        allowed_true.update({
            "dhr_op04_called_here",
            "dhr_op04_called_by_mrb",
            "actual_source_claim_confirmed_for_downstream_handoff",
        })
    for key in mrb.P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS:
        if key not in allowed_true:
            assert material[key] is False, key


def _mrb_op03_ready() -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=_dhr_op03_ready(),
    )
    assert material["mrb_op03_ready_for_mrb_op04"] is True
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(material) is True
    return material


def _manual_request() -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree()
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree_contract(material) is True
    return material


def _mrb_op04_ready() -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=_mrb_op03_ready(),
        manual_reintake_request_bodyfree=_manual_request(),
    )
    assert material["mrb_op04_ready_for_mrb_op05"] is True
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(material) is True
    return material


def test_mrb_manual_reintake_request_bodyfree_contract_targets_dhr_op04_only() -> None:
    material = _manual_request()

    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_SCHEMA_VERSION
    assert material["manual_reintake_requested"] is True
    assert material["requested_operation_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF
    assert material["requested_source_material_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_REQUESTED_SOURCE_MATERIAL_REF
    assert material["manual_request_bodyfree"] is True
    assert material["dhr_op04_only"] is True
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["body_free"] is True


def test_mrb_op04_builds_dhr_op04_input_envelope_without_calling_dhr_op04() -> None:
    material = _mrb_op04_ready()
    envelope = material["dhr_op04_input_envelope_bodyfree"]

    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP04_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF
    assert material["mrb_op04_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_READY_FOR_OP05_REF
    assert material["manual_reintake_request_contract_valid"] is True
    assert material["manual_reintake_requested"] is True
    assert material["dri_op09_candidate_present"] is True
    assert material["dhr_op03_ready"] is True
    assert material["dhr_op04_input_envelope_ready"] is True
    assert envelope["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_DHR_OP04_INPUT_ENVELOPE_SCHEMA_VERSION
    assert envelope["external_actual_operation_evidence_claim_bodyfree_optional"] == material["external_actual_operation_evidence_claim_bodyfree_optional"]
    assert envelope["op03_elr_op17_dmd_compatible_receipt_candidate_extraction"] == material["op03_elr_op17_dmd_compatible_receipt_candidate_extraction"]
    assert envelope["dhr_op04_called_here"] is False
    assert material["mrb_op04_does_not_call_dhr_op04"] is True
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op04_called_by_mrb"] is False
    assert material["dhr_op04_called_by_manual_reintake_boundary"] is False
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op04_waits_without_manual_request_and_does_not_copy_inputs() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=_mrb_op03_ready(),
    )

    assert material["mrb_op04_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_WAITING_FOR_MANUAL_REQUEST_OR_MATERIAL_REF
    assert material["mrb_op04_waiting_for_manual_request_or_material"] is True
    assert material["manual_reintake_request_present"] is False
    assert material["dhr_op04_input_envelope_bodyfree"] == {}
    assert material["external_actual_operation_evidence_claim_bodyfree_optional"] == {}
    assert material["op03_elr_op17_dmd_compatible_receipt_candidate_extraction"] == {}
    assert "manual_reintake_request_missing" in material["mrb_op04_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op04_repairs_manual_request_target_step_mismatch() -> None:
    request = _manual_request()
    request["requested_operation_step_ref"] = "DHR-OP05_must_not_be_targeted_here"

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=_mrb_op03_ready(),
        manual_reintake_request_bodyfree=request,
    )

    assert material["mrb_op04_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_REPAIR_INPUT_ENVELOPE_REF
    assert material["mrb_op04_repair_required"] is True
    assert "manual_reintake_request_contract_invalid" in material["mrb_op04_blocker_refs"]
    assert material["dhr_op04_input_envelope_bodyfree"] == {}
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op05_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op04_blocks_manual_request_with_raw_body_key_without_copying_value() -> None:
    request = _manual_request()
    request["raw_input"] = "do not copy this raw body"

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=_mrb_op03_ready(),
        manual_reintake_request_bodyfree=request,
    )

    assert material["mrb_op04_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["mrb_op04_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert "mrb_op04_forbidden_payload_key_detected_before_envelope" in material["mrb_op04_blocker_refs"]
    assert material["dhr_op04_input_envelope_bodyfree"] == {}
    assert "do not copy this raw body" not in repr(material)
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op05_calls_existing_dhr_op04_with_ready_envelope_captures_confirmed_result_and_stops() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=_mrb_op04_ready(),
    )

    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP05_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF
    assert material["op04_contract_valid"] is True
    assert material["op04_ready_for_mrb_op05"] is True
    assert material["dhr_op04_called_by_manual_reintake_boundary"] is True
    assert material["dhr_op04_called_by_mrb"] is True
    assert material["dhr_op04_called_here"] is True
    assert material["dhr_op04_called_by_dri"] is False
    assert material["dhr_op04_contract_valid"] is True
    assert material["dhr_op04_result_captured"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["actual_source_claim_bodyfree"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_CONFIRMED_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_op05_call=True)


def test_mrb_op05_does_not_call_dhr_op04_when_op04_is_waiting() -> None:
    op03_waiting = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=_dhr_op03_waiting(),
    )
    op04_waiting = mrb.build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=op03_waiting,
        manual_reintake_request_bodyfree=_manual_request(),
    )

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04_waiting,
    )

    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_WAITING_BEFORE_DHR_OP04_CALL_REF
    assert material["mrb_op05_waiting_before_dhr_op04_call"] is True
    assert material["dhr_op04_called_by_manual_reintake_boundary"] is False
    assert material["dhr_op04_called_by_mrb"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op04_result_captured"] is False
    assert material["dhr_op04_result_bodyfree"] == {}
    assert material["dhr_op05_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op05_never_calls_dhr_op05_or_downstream_after_capture() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=_mrb_op04_ready(),
    )

    assert material["mrb_op05_does_not_call_dhr_op05"] is True
    assert material["mrb_op05_does_not_call_dhr_op06"] is True
    assert material["mrb_op05_does_not_execute_dmd_r52_or_release"] is True
    assert material["mrb_op05_does_not_start_p5_p6_p8_p7_or_release"] is True
    assert material["dhr_op05_auto_call_allowed"] is False
    assert material["dhr_op06_auto_call_allowed"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p8_question_implementation_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True


def test_mrb_op04_op05_full_title_aliases_match_canonical_builders() -> None:
    request_a = mrb.build_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree()
    request_b = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_bodyfree_request()
    assert request_a == request_b

    op04_a = _mrb_op04_ready()
    op04_b = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        mrb_op03_dhr_op03_ready_material_intake=_mrb_op03_ready(),
        manual_reintake_request_bodyfree=_manual_request(),
    )
    assert op04_a == op04_b

    op05_a = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04_a,
    )
    op05_b = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04_a,
    )
    assert op05_a == op05_b


def _op04_ready_with_mutated_envelope(*, candidate_updates: dict[str, object] | None = None, op03_material: dict[str, object] | None = None) -> dict[str, object]:
    material = deepcopy(_mrb_op04_ready())
    envelope = deepcopy(material["dhr_op04_input_envelope_bodyfree"])
    if candidate_updates:
        candidate = deepcopy(envelope["external_actual_operation_evidence_claim_bodyfree_optional"])
        candidate.update(candidate_updates)
        envelope["external_actual_operation_evidence_claim_bodyfree_optional"] = candidate
    if op03_material is not None:
        envelope["op03_elr_op17_dmd_compatible_receipt_candidate_extraction"] = op03_material
    material["dhr_op04_input_envelope_bodyfree"] = envelope
    # OP04 remains an already assembled, body-free MRB envelope; OP05 lets DHR-OP04 classify body-free source mismatch/waiting.
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(material) is True
    return material


def test_mrb_op05_maps_dhr_op04_not_confirmed_result_and_stops() -> None:
    op04 = _op04_ready_with_mutated_envelope(
        candidate_updates={"actual_local_only_human_review_by_person_confirmed": False, "actual_human_review_executed_by_person": False}
    )

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04,
    )

    assert material["dhr_op04_called_by_manual_reintake_boundary"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True


def test_mrb_op05_maps_dhr_op04_waiting_result_and_stops() -> None:
    op04 = _op04_ready_with_mutated_envelope(op03_material=_dhr_op03_waiting())

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04,
    )

    assert material["dhr_op04_called_by_manual_reintake_boundary"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True


def test_mrb_op05_maps_dhr_op04_invalid_result_and_stops() -> None:
    op04 = _op04_ready_with_mutated_envelope(
        candidate_updates={
            "source_kind_ref": "helper_green",
            "actual_source_claim_source_kind_ref": "helper_green",
        }
    )

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04,
    )

    assert material["dhr_op04_called_by_manual_reintake_boundary"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True


def _dhr_op04_result_with_external_claim_mutation(*, mutation_ref: str) -> dict[str, object]:
    op02 = _mrb_op02_ready()
    claim = deepcopy(op02["external_actual_operation_evidence_claim_bodyfree_optional"])
    op03 = _dhr_op03_ready()
    if mutation_ref == "not_confirmed_without_human_confirmation":
        claim["actual_local_only_human_review_by_person_confirmed"] = False
        claim["actual_human_review_executed_by_person"] = False
    elif mutation_ref == "waiting_for_external_claim":
        op03 = _dhr_op03_waiting()
    elif mutation_ref == "invalid_source_repair_required":
        claim["source_kind_ref"] = "fixture_generated_helper_output"
        claim["actual_source_claim_source_kind_ref"] = "fixture_generated_helper_output"
    else:
        raise AssertionError(f"unknown mutation_ref: {mutation_ref}")
    result = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
        op03_elr_op17_dmd_compatible_receipt_candidate_extraction=op03,
        external_actual_operation_evidence_claim_bodyfree_optional=claim,
    )
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(result) is True
    return result


def _op05_with_forced_dhr_op04_result(monkeypatch, dhr_op04_result: dict[str, object]) -> dict[str, object]:
    op04_ready = _mrb_op04_ready()

    def _fake_dhr_op04_builder(**kwargs: object) -> dict[str, object]:
        assert (
            kwargs.get("op03_elr_op17_dmd_compatible_receipt_candidate_extraction")
            or kwargs.get("elr_op17_dmd_compatible_receipt_candidate_extraction")
        )
        assert kwargs["external_actual_operation_evidence_claim_bodyfree_optional"]
        return dhr_op04_result

    monkeypatch.setattr(
        mrb.dhr,
        "build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification",
        _fake_dhr_op04_builder,
    )
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
        mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope=op04_ready,
    )
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material, allow_op05_call=True)
    return material


def test_mrb_op05_captures_dhr_op04_not_confirmed_result_and_stops(monkeypatch) -> None:
    dhr_result = _dhr_op04_result_with_external_claim_mutation(mutation_ref="not_confirmed_without_human_confirmation")
    material = _op05_with_forced_dhr_op04_result(monkeypatch, dhr_result)

    assert material["dhr_op04_result_captured"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF
    assert material["mrb_op05_dhr_op04_not_confirmed_retry_or_start_required_stopped"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF
    assert material["dhr_op05_called_here"] is False
    assert material["downstream_auto_execution_allowed"] is False


def test_mrb_op05_captures_dhr_op04_waiting_result_and_stops(monkeypatch) -> None:
    dhr_result = _dhr_op04_result_with_external_claim_mutation(mutation_ref="waiting_for_external_claim")
    material = _op05_with_forced_dhr_op04_result(monkeypatch, dhr_result)

    assert material["dhr_op04_result_captured"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF
    assert material["mrb_op05_dhr_op04_waiting_external_claim_stopped"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF
    assert material["dhr_op05_called_here"] is False
    assert material["downstream_auto_execution_allowed"] is False


def test_mrb_op05_captures_dhr_op04_invalid_result_and_stops(monkeypatch) -> None:
    dhr_result = _dhr_op04_result_with_external_claim_mutation(mutation_ref="invalid_source_repair_required")
    material = _op05_with_forced_dhr_op04_result(monkeypatch, dhr_result)

    assert material["dhr_op04_result_captured"] is True
    assert material["dhr_op04_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert material["mrb_op05_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF
    assert material["mrb_op05_dhr_op04_invalid_repair_required_stopped"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF
    assert material["dhr_op05_called_here"] is False
    assert material["downstream_auto_execution_allowed"] is False
