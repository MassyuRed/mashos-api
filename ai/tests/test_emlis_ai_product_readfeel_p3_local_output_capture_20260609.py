from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_current_output_inventory import (
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
    assert_product_readfeel_current_output_inventory_meta_only,
    build_product_readfeel_current_output_inventory,
)
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_cases_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_local_output_capture_20260609 import (
    PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609,
    PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_VERSION_20260609,
    PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609,
    assert_product_readfeel_p3_local_review_packet_local_only_20260609,
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609,
    build_product_readfeel_p3_local_output_capture_20260609,
    dump_product_readfeel_p3_local_output_capture_public_summary_20260609,
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _fake_reply_meta(*, observation_status: str = "passed") -> dict[str, Any]:
    return {
        "schema_version": "fake.local.renderer.meta.v1",
        "version": "fake.local.renderer.meta.v1",
        "kernel_version": "fake-kernel",
        "observation_status": observation_status,
        "observation_reply_kind": "normal_observation",
        "diagnostic_summary": {
            "material_quality": "synthetic_local_qa",
            "binding_supported_sentence_count": 2,
            "expected_binding_count": 2,
        },
        "visible_surface_acceptance_gate": {
            "classification": "accepted",
            "action": "allow_public_feedback",
            "passed": True,
        },
        "product_surface_validation": {
            "product_surface_valid": True,
            "passed": True,
        },
        "public_surface_lineage": {
            "candidate_source_kind": "fake_renderer_current_output_capture",
        },
        "composer_model": "fake_renderer",
        "rejection_reasons": [],
    }


async def _fake_renderer(**kwargs: Any) -> dict[str, Any]:
    current_input = kwargs["current_input"]
    return {
        "comment_text": f"Emlisです。synthetic local QA output for {current_input['id']}.",
        "meta": _fake_reply_meta(),
    }


async def _raising_renderer(**kwargs: Any) -> dict[str, Any]:
    current_input = kwargs["current_input"]
    if current_input["id"].endswith("001"):
        raise RuntimeError("synthetic renderer failure")
    return {
        "comment_text": "Emlisです。synthetic local QA output.",
        "meta": _fake_reply_meta(),
    }


def test_p3_2_local_output_capture_builds_local_packet_and_sanitized_events_for_60_cases() -> None:
    cases = build_product_readfeel_baseline_cases_20260609()
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        input_cases=cases,
        renderer=_fake_renderer,
        run_id="p3-2-local-output-capture-test",
    )
    packet = capture["local_review_packet"]
    events = capture["sanitized_current_output_events"]
    summary = capture["public_summary"]

    assert capture["source_step"] == PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609
    assert packet["schema_version"] == PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_VERSION_20260609
    assert packet["visibility"] == "local_qa_only"
    assert packet["contains_raw_input"] is True
    assert packet["contains_comment_text_body"] is True
    assert packet["item_count"] == 60
    assert len(packet["items"]) == 60
    assert len(events) == 60
    assert summary["schema_version"] == PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609
    assert summary["case_count"] == 60
    assert summary["output_row_count"] == 60
    assert summary["all_cases_have_output_rows"] is True
    assert summary["missing_families"] == []
    assert summary["p3_2_local_output_capture_completed"] is True
    assert summary["output_capture_completed"] is True
    assert summary["sanitized_current_output_event_created"] is True
    assert summary["scorecard_event_created"] is False
    assert summary["product_gate_ready"] is False
    assert summary["public_release_applied"] is False

    assert_product_readfeel_p3_local_review_packet_local_only_20260609(packet)
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(events)

    for local_item, event in zip(packet["items"], events, strict=True):
        assert local_item["current_input"]["memo"].strip()
        assert local_item["comment_text"].strip()
        assert local_item["comment_text_present"] is True
        assert local_item["public_reached"] is True
        assert local_item["rn_visible_actual"] is True
        assert event["schema_version"] == PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609
        assert event["case_id"] == local_item["case_id"]
        assert event["comment_text_present"] is True
        assert event["comment_text_length"] == len(local_item["comment_text"])
        assert event["comment_text_fingerprint"].startswith("sha256:")
        assert event["comment_text_body_included"] is False
        assert event["raw_input_included"] is False
        assert event["candidate_body_included"] is False
        assert "current_input" not in event
        assert "comment_text" not in event
        assert "memo" not in event
        assert event["verdict"] == "NOT_EVALUATED"
        assert event["product_gate_ready"] is False
        assert event["public_release_applied"] is False


def test_p3_2_sanitized_events_are_inventory_compatible_without_body_leak() -> None:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-2-inventory-compat-test",
    )
    events = capture["sanitized_current_output_events"]
    inventory = build_product_readfeel_current_output_inventory(
        events=events,
        run_id="p3-2-inventory-compat-test",
    )
    dumped = _dump({"events": events, "inventory": inventory, "summary": capture["public_summary"]})

    assert inventory["item_count"] == 60
    assert set(inventory["observed_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert inventory["missing_families"] == []
    assert inventory["product_gate_ready"] is False
    assert inventory["public_release_applied"] is False
    assert_product_readfeel_current_output_inventory_meta_only(inventory)
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(events)

    assert "疲れた" not in dumped
    assert "今日は小さなことで" not in dumped
    assert "synthetic local QA output" not in dumped
    assert '"current_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"memo":' not in dumped
    assert '"candidate_body":' not in dumped


def test_p3_2_public_summary_dump_keeps_local_review_packet_body_out() -> None:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-2-public-summary-test",
    )
    dumped = dump_product_readfeel_p3_local_output_capture_public_summary_20260609(capture)
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609
    assert parsed["case_count"] == 60
    assert parsed["local_review_packet_created"] is True
    assert parsed["local_review_packet_retained_in_public_summary"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609([parsed])

    assert "疲れた" not in dumped
    assert "今日は小さなことで" not in dumped
    assert "synthetic local QA output" not in dumped
    assert '"local_review_packet":' not in dumped
    assert '"current_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"memo":' not in dumped


def test_p3_2_capture_fail_closed_renderer_exception_still_creates_body_free_output_rows() -> None:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_raising_renderer,
        run_id="p3-2-renderer-exception-test",
    )
    events = capture["sanitized_current_output_events"]
    failed_events = [event for event in events if event["renderer_exception"]]
    failed_local_items = [item for item in capture["local_review_packet"]["items"] if item["renderer_exception"]]

    assert len(events) == 60
    assert len(failed_events) == 12
    assert len(failed_local_items) == 12
    assert capture["public_summary"]["renderer_exception_count"] == 12
    assert capture["public_summary"]["all_cases_have_output_rows"] is True
    for event in failed_events:
        assert event["observation_status"] == "unavailable"
        assert event["public_reached"] is False
        assert event["comment_text_present"] is False
        assert event["comment_text_body_included"] is False
        assert "renderer_exception" in event["reason_codes"]
    for item in failed_local_items:
        assert item["comment_text"] == ""
        assert item["public_reached"] is False
        assert item["current_input"]["synthetic_case_material"] is True
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(events)


def test_p3_2_guards_reject_body_keys_and_forbidden_contract_flags_in_sanitized_events() -> None:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-2-guard-test",
    )
    event = dict(capture["sanitized_current_output_events"][0])

    unsafe_body = dict(event)
    unsafe_body["comment_text"] = "sanitized event must not retain display body"
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609([unsafe_body])

    unsafe_current_input = dict(event)
    unsafe_current_input["current_input"] = {"memo": "raw input must not be retained here"}
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609([unsafe_current_input])

    unsafe_flag = dict(event)
    unsafe_flag["gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609([unsafe_flag])

    unsafe_release = dict(event)
    unsafe_release["public_release_applied"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609([unsafe_release])
