# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
)
from emlis_ai_p7_r46_real_device_modal_review_closed_validation import (
    HOLD_DC_FULL_BACKEND_SUITE_REF,
    P7_HOLD_FULL_BACKEND_SUITE_REF,
    P7_HOLD_REAL_DEVICE_MODAL_REF,
    P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION,
    P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION,
    P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION,
    P7_RETURN_REAL_DEVICE_HOLD_REF,
    assert_p7_hold_release_p8_closed_validation_contract,
    assert_real_device_and_closed_validation_summary_contract,
    assert_real_device_submit_modal_readfeel_checklist_contract,
    build_p7_hold_release_p8_closed_validation,
    build_real_device_and_closed_validation_summary,
    build_real_device_submit_modal_readfeel_checklist,
)

SECRET_INPUT = "R12/R13 secret raw input must not enter body-free checklist"
SECRET_SURFACE = "R12/R13 secret modal surface must not enter body-free checklist"
SECRET_REVIEWER = "R12/R13 reviewer free prose must not enter body-free checklist"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_r12_real_device_modal_checklist_defaults_to_not_run_and_keeps_manual_hold() -> None:
    checklist = build_real_device_submit_modal_readfeel_checklist(
        device_context={
            "device_ref": "ios_manual_device_ref",
            "os_ref": "ios_ref",
            "app_build_ref": "local_build_ref",
            "screen_size_class": "medium",
        },
        runtime_context={
            "api_snapshot_ref": "mashos-api_7_60",
            "subscription_tier": "plus",
            "case_family": "plus_history_line_eligible",
            "display_contract_green_confirmed": True,
            "public_meta_final_source_consistency_confirmed": True,
        },
        case_refs=[
            {
                "case_id": "real_device_p5_history_case_ref",
                "family": "plus_history_line_eligible",
                "subscription_tier": "plus",
                "source_row_ref": "p5_review_row_ref",
            }
        ],
    )
    assert_real_device_submit_modal_readfeel_checklist_contract(checklist)

    assert checklist["schema_version"] == P7_R46_REAL_DEVICE_MODAL_REVIEW_CHECKLIST_SCHEMA_VERSION
    assert checklist["review_scope"] == "manual_real_device_review_not_automated_green"
    assert checklist["result"] == "NOT_RUN"
    assert checklist["manual_real_device_review_required"] is True
    assert checklist["real_device_modal_review_confirmed"] is False
    assert checklist["manual_review_completed"] is False
    assert checklist["automated_green_can_close_manual_review"] is False
    assert checklist["release_allowed"] is False
    assert checklist["p7_complete"] is False
    assert checklist["p8_start_allowed"] is False
    assert checklist["hold004_close_allowed"] is False
    assert checklist["body_free"] is True
    assert P7_HOLD_REAL_DEVICE_MODAL_REF in checklist["unresolved_hold_refs"]
    assert P7_RETURN_REAL_DEVICE_HOLD_REF in checklist["unresolved_hold_refs"]
    assert checklist["case_refs"][0]["local_payload_materialized_here"] is False

    dumped = _dumped(checklist)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_r12_real_device_modal_checklist_can_record_body_free_manual_pass_without_release_promotion() -> None:
    checklist = build_real_device_submit_modal_readfeel_checklist(
        manual_review_result={
            "result": "PASS",
            "modal_contract": {
                "submit_modal_opened": "passed",
                "title_emlis_observation_preserved": "passed",
                "visible_payload_source_confirmed": "passed",
                "passed_non_empty_only_confirmed": "passed",
                "non_passed_hidden_confirmed": "passed",
                "public_top_level_shape_preserved": "passed",
            },
            "readfeel_checks": {
                "phone_readability_reviewed": "passed",
                "length_pressure_reviewed": "passed",
                "line_break_reviewed": "passed",
                "section_weight_reviewed": "passed",
                "p5_history_line_creepy_absence_reviewed": "passed",
                "p6_structure_insight_overread_absence_reviewed": "passed",
                "wants_more_input_reviewed": "passed",
            },
            "readfeel_axes": {
                "readable_on_phone": 0.95,
                "length_pressure_absence": 0.95,
                "weight_absence": 0.95,
                "shallow_absence": 0.95,
                "p5_history_line_creepy_absence": 0.95,
                "p6_overread_absence": 0.95,
                "wants_more_input": 0.9,
            },
        }
    )
    assert_real_device_submit_modal_readfeel_checklist_contract(checklist)

    assert checklist["result"] == "PASS"
    assert checklist["real_device_modal_review_confirmed"] is True
    assert checklist["unresolved_hold_refs"] == []
    assert checklist["release_allowed"] is False
    assert checklist["p7_complete"] is False
    assert checklist["p8_start_allowed"] is False
    assert checklist["hold004_close_allowed"] is False
    assert checklist["body_free"] is True


def test_r13_closed_validation_keeps_p7_release_and_p8_closed_after_r10_to_r12_handoff() -> None:
    validation = build_p7_hold_release_p8_closed_validation()
    assert_p7_hold_release_p8_closed_validation_contract(validation)

    assert validation["schema_version"] == P7_R46_HOLD_RELEASE_P8_CLOSED_VALIDATION_SCHEMA_VERSION
    assert validation["current_phase"] == "P7"
    assert validation["display_contract_status"]["red_classified"] is True
    assert validation["display_contract_status"]["display_contract_green"] is True
    assert validation["display_contract_status"]["body_leak_detected"] is False
    assert validation["p5_return_status"]["human_blind_qa_ready"] is True
    assert validation["p5_return_status"]["human_blind_qa_confirmed"] is False
    assert validation["p6_return_status"]["limited_review_ready"] is True
    assert validation["p6_return_status"]["human_readfeel_confirmed"] is False
    assert validation["real_device_modal_status"]["checklist_ready"] is True
    assert validation["real_device_modal_status"]["confirmed"] is False
    assert validation["real_device_modal_status"]["result"] == "NOT_RUN"
    assert validation["release_boundary"]["release_allowed"] is False
    assert validation["release_boundary"]["p7_complete"] is False
    assert validation["release_boundary"]["p8_start_allowed"] is False
    assert validation["release_boundary"]["hold004_close_allowed"] is False
    assert validation["release_allowed"] is False
    assert validation["p7_complete"] is False
    assert validation["p8_start_allowed"] is False
    assert validation["hold004_close_allowed"] is False
    assert validation["body_free"] is True
    assert P5_HUMAN_BLIND_QA_HOLD_REF in validation["unresolved_hold_refs"]
    assert P6_LIMITED_HUMAN_READFEEL_HOLD_REF in validation["unresolved_hold_refs"]
    assert P7_RETURN_REAL_DEVICE_HOLD_REF in validation["unresolved_hold_refs"]
    assert P7_HOLD_FULL_BACKEND_SUITE_REF in validation["unresolved_hold_refs"]
    assert HOLD_DC_FULL_BACKEND_SUITE_REF in validation["unresolved_hold_refs"]


def test_r12_r13_summary_is_body_free_and_does_not_convert_real_device_pass_to_release() -> None:
    checklist = build_real_device_submit_modal_readfeel_checklist(
        manual_review_result={
            "result": "PASS",
            "modal_contract": {
                "submit_modal_opened": "passed",
                "title_emlis_observation_preserved": "passed",
                "visible_payload_source_confirmed": "passed",
                "passed_non_empty_only_confirmed": "passed",
                "non_passed_hidden_confirmed": "passed",
                "public_top_level_shape_preserved": "passed",
            },
            "readfeel_checks": {
                "phone_readability_reviewed": "passed",
                "length_pressure_reviewed": "passed",
                "line_break_reviewed": "passed",
                "section_weight_reviewed": "passed",
                "p5_history_line_creepy_absence_reviewed": "passed",
                "p6_structure_insight_overread_absence_reviewed": "passed",
                "wants_more_input_reviewed": "passed",
            },
        }
    )
    validation = build_p7_hold_release_p8_closed_validation(real_device_checklist=checklist)
    summary = build_real_device_and_closed_validation_summary(
        checklist=checklist,
        closed_validation=validation,
    )
    assert_real_device_and_closed_validation_summary_contract(summary)

    assert summary["schema_version"] == P7_R46_REAL_DEVICE_AND_CLOSED_VALIDATION_SUMMARY_SCHEMA_VERSION
    assert summary["real_device_modal_review_confirmed"] is True
    assert summary["real_device_result"] == "PASS"
    assert summary["release_allowed"] is False
    assert summary["p7_complete"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["hold004_close_allowed"] is False
    assert P7_HOLD_FULL_BACKEND_SUITE_REF in summary["unresolved_hold_refs"]
    assert HOLD_DC_FULL_BACKEND_SUITE_REF in summary["unresolved_hold_refs"]


def test_r12_r13_builders_reject_manual_or_case_body_payloads() -> None:
    with pytest.raises(ValueError):
        build_real_device_submit_modal_readfeel_checklist(
            manual_review_result={
                "result": "YELLOW",
                "comment_text": SECRET_SURFACE,
                "reviewer_free_text": SECRET_REVIEWER,
            }
        )

    with pytest.raises(ValueError):
        build_real_device_submit_modal_readfeel_checklist(
            case_refs=[
                {
                    "case_id": "unsafe_case_ref",
                    "family": "plus_history_line_eligible",
                    "raw_input": SECRET_INPUT,
                    "surface_for_reviewer": SECRET_SURFACE,
                }
            ]
        )

    with pytest.raises(ValueError):
        build_p7_hold_release_p8_closed_validation(
            display_contract_status={"raw_input": SECRET_INPUT}
        )


def test_r12_r13_contracts_reject_false_completion_promotion() -> None:
    checklist = build_real_device_submit_modal_readfeel_checklist()
    checklist["real_device_modal_review_confirmed"] = True
    with pytest.raises(ValueError):
        assert_real_device_submit_modal_readfeel_checklist_contract(checklist)

    validation = build_p7_hold_release_p8_closed_validation()
    validation["release_boundary"]["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold_release_p8_closed_validation_contract(validation)

    summary = build_real_device_and_closed_validation_summary()
    summary["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_real_device_and_closed_validation_summary_contract(summary)
