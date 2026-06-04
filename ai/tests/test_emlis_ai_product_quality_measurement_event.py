# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_product_quality_measurement_event import (
    PRODUCT_QUALITY_EVENT_SCHEMA_VERSION,
    assert_product_quality_measurement_event_meta_only,
    build_product_quality_event_schema_material,
    dump_product_quality_measurement_event,
    normalize_product_quality_event,
    normalize_product_quality_family,
    product_quality_event_to_scorecard_row,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_types import ReplyEnvelope

VISIBLE_COMMENT = "これは表示条件確認用のcomment_textで、event本体には入れてはいけない。"
SECRET_RAW_INPUT = "phase2 secret raw input must never be serialized"
SECRET_COMMENT_BODY = "phase2 secret comment body must never be serialized"


def _passed_public_meta() -> dict[str, object]:
    return build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": "free",
            "observation_status": "passed",
            "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
            "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
            "state_answer_gate_boundary": {"passed": True},
        },
        comment_text_present=True,
        subscription_tier="free",
    )


def test_phase2_product_quality_event_normalizes_public_display_without_body_payload() -> None:
    event = normalize_product_quality_event(
        run_id="pq_phase2_run",
        row_id="row_001",
        source_type="fixture_family",
        source_case_id="daily_001",
        source_revision="local",
        family="daily_negative",
        comment_text=VISIBLE_COMMENT,
        public_meta=_passed_public_meta(),
        machine_metrics={
            "binding_required_count": 2,
            "binding_supported_sentence_count": 2,
            "reason_required_count": 1,
            "reason_covered_count": 1,
            "surface_signature_key": "daily_unpleasant_state_v1",
            "template_major_count": 0,
            "safety_major_count": 0,
        },
        composer_resolution={
            "default_limited_enabled": True,
            "resolution_source": "cocolon_limited_composer",
            "composer_model": "cocolon_limited_composer.v1",
            "requested_composer": "limited",
            "default_client_used": True,
            "rejection_reasons": [],
            "qa_profile": "local_product_qa",
        },
    )

    assert event["schema_version"] == PRODUCT_QUALITY_EVENT_SCHEMA_VERSION
    assert event["family"] == "daily_unpleasant"
    assert event["observation_status"] == "passed"
    assert event["public_display_reached"] is True
    assert event["comment_text_present"] is True
    assert event["comment_text_length"] == len(VISIBLE_COMMENT)
    assert event["public_contract"] == {
        "api_route_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }
    assert event["binding"]["binding_passed"] is True
    assert event["reason_coverage"]["reason_coverage_passed"] is True
    assert event["surface_quality"]["surface_signature_key"] == "daily_unpleasant_state_v1"
    assert event["composer_resolution"]["default_client_used"] is True
    assert event["product_gate_ready"] is False
    assert event["public_release_applied"] is False
    assert event["blockers"] == []

    dumped = dump_product_quality_measurement_event(event)
    assert VISIBLE_COMMENT not in dumped
    assert "comment_text\":" not in dumped
    assert "raw_input\":" not in dumped
    assert_product_quality_measurement_event_meta_only(event)


def test_phase2_event_uses_same_public_display_condition_as_api_boundary() -> None:
    no_comment_event = normalize_product_quality_event(
        run_id="pq_phase2_run",
        row_id="row_empty",
        source_type="manual_internal_case",
        source_case_id="empty_comment_case",
        family="daily_unpleasant",
        comment_text="   ",
        public_meta=_passed_public_meta(),
    )
    assert no_comment_event["public_display_reached"] is False
    assert "comment_text_missing" in no_comment_event["blockers"]
    assert "public_display_not_reached" in no_comment_event["blockers"]

    rejected_event = normalize_product_quality_event(
        run_id="pq_phase2_run",
        row_id="row_rejected",
        source_type="manual_internal_case",
        source_case_id="rejected_case",
        family="daily_unpleasant",
        comment_text=VISIBLE_COMMENT,
        public_meta={"observation_status": "rejected"},
    )
    assert rejected_event["observation_status"] == "rejected"
    assert rejected_event["public_display_reached"] is False
    assert "observation_status_not_passed" in rejected_event["blockers"]
    assert "public_display_not_reached" in rejected_event["blockers"]


def test_phase2_normalizer_strips_forbidden_source_keys_and_keeps_only_warnings_or_blockers() -> None:
    event = normalize_product_quality_event(
        run_id="pq_phase2_run",
        row_id="row_forbidden_source",
        source_type="manual_internal_case",
        source_case_id="forbidden_source_case",
        family="self_denial",
        comment_text=VISIBLE_COMMENT,
        public_meta=_passed_public_meta(),
        internal_meta={
            "observation_status": "passed",
            "raw_input": SECRET_RAW_INPUT,
            "diagnostic_summary": {"comment_text": SECRET_COMMENT_BODY},
            "public_response_key_added": True,
        },
    )

    dumped = json.dumps(event, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT_BODY not in dumped
    assert "forbidden_text_payload_key_detected_in_source" in event["blockers"]
    assert "forbidden_contract_or_release_flag_true_in_source" in event["blockers"]
    assert any(item.startswith("stripped_forbidden_text_key:") for item in event["warnings"])
    assert any(item.startswith("blocked_forbidden_true_flag:") for item in event["warnings"])
    assert_product_quality_measurement_event_meta_only(event)


def test_phase2_event_rejects_body_payload_or_release_flags_inside_event_material() -> None:
    event = normalize_product_quality_event(
        run_id="pq_phase2_run",
        row_id="row_valid",
        source_type="fixture_family",
        source_case_id="valid_case",
        family="low_info",
        comment_text=VISIBLE_COMMENT,
        public_meta=_passed_public_meta(),
    )

    unsafe_body = dict(event)
    unsafe_body["comment_text"] = SECRET_COMMENT_BODY
    with pytest.raises(ValueError):
        assert_product_quality_measurement_event_meta_only(unsafe_body)

    unsafe_release = dict(event)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_product_quality_measurement_event_meta_only(unsafe_release)

    unsafe_contract = dict(event)
    unsafe_contract["public_contract"] = dict(event["public_contract"])
    unsafe_contract["public_contract"]["public_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_product_quality_measurement_event_meta_only(unsafe_contract)


def test_phase2_event_can_normalize_reply_envelope_and_flatten_for_scorecard_without_text() -> None:
    reply = ReplyEnvelope(
        comment_text=VISIBLE_COMMENT,
        meta={
            "observation_status": "passed",
            "multi_perspective": {
                "composer_client_resolution": {
                    "default_limited_enabled": True,
                    "source": "cocolon_limited_composer",
                    "composer_model": "cocolon_limited_composer.v1",
                    "requested_composer": "limited",
                    "default_client_used": True,
                    "rejection_reasons": [],
                }
            },
        },
    )

    event = normalize_product_quality_event(
        run_id="pq_phase2_run",
        row_id="row_reply",
        source_type="regression_fixture",
        source_case_id="reply_fixture",
        family="meaning_arc",
        reply=reply,
        public_meta=_passed_public_meta(),
        machine_metrics={
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 0,
            "template_major_count": 0,
            "safety_major_count": 0,
        },
    )
    row = product_quality_event_to_scorecard_row(event)

    assert event["family"] == "long_meaning_arc"
    assert row["source_schema_version"] == PRODUCT_QUALITY_EVENT_SCHEMA_VERSION
    assert row["public_display_reached"] is True
    assert row["binding_supported_sentence_count"] == 1
    assert row["product_gate_ready"] is False
    dumped = json.dumps(row, ensure_ascii=False, sort_keys=True)
    assert VISIBLE_COMMENT not in dumped
    assert "comment_text\":" not in dumped
    assert "raw_input\":" not in dumped


def test_phase2_schema_material_is_meta_only_and_does_not_release_product_gate() -> None:
    material = build_product_quality_event_schema_material()
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True)

    assert material["event_schema_version"] == PRODUCT_QUALITY_EVENT_SCHEMA_VERSION
    assert material["product_gate_ready"] is False
    assert material["public_release_applied"] is False
    assert "comment_text_body\":" not in dumped
    assert "raw_input\":" not in dumped
    assert "candidate_body\":" not in dumped


def test_phase2_family_normalizer_is_limited_to_required_family_set() -> None:
    assert normalize_product_quality_family("low_info") == "low_information_short"
    assert normalize_product_quality_family("daily_negative") == "daily_unpleasant"
    assert normalize_product_quality_family("meaning_arc") == "long_meaning_arc"
    assert normalize_product_quality_family("unwritten_new_family") == "unknown"
