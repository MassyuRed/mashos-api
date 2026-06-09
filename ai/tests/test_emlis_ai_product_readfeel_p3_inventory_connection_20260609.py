from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_current_output_inventory import (
    FAILURE_READFEEL_GAP,
    FAILURE_STRUCTURE_INSIGHT_GAP,
    FAILURE_SURFACE_BREAKAGE,
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
    assert_product_readfeel_current_output_inventory_meta_only,
)
from emlis_ai_product_readfeel_scorecard import assert_product_readfeel_scorecard_meta_only
from fixtures.emlis_ai_product_readfeel_p3_inventory_connection_20260609 import (
    PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_STEP_20260609,
    PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_VERSION_20260609,
    assert_product_readfeel_p3_inventory_connection_meta_only_20260609,
    build_product_readfeel_p3_inventory_connection_20260609,
    dump_product_readfeel_p3_inventory_connection_summary_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_local_output_capture_20260609 import (
    build_product_readfeel_p3_local_output_capture_20260609,
)


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
            "reason_required_count": 1,
            "reason_covered_count": 1,
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


def test_p3_3_connects_p3_2_sanitized_events_to_inventory_and_scorecard() -> None:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-3-inventory-connection-capture-test",
    )
    connection = build_product_readfeel_p3_inventory_connection_20260609(
        capture=capture,
        run_id="p3-3-inventory-connection-test",
    )
    summary = connection["summary"]
    inventory = connection["current_output_inventory"]
    scorecard = connection["product_readfeel_scorecard"]

    assert connection["schema_version"] == PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_VERSION_20260609
    assert connection["source_step"] == PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_STEP_20260609
    assert summary["schema_version"] == PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SUMMARY_VERSION_20260609
    assert summary["sanitized_event_count"] == 60
    assert summary["inventory_item_count"] == 60
    assert summary["scorecard_family_result_count"] == len(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert set(summary["observed_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert summary["missing_families"] == []
    assert inventory["item_count"] == 60
    assert inventory["missing_families"] == []
    assert set(inventory["observed_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert scorecard["product_readfeel_scorecard_ready"] is True
    assert summary["p3_3_inventory_connected"] is True
    assert summary["p3_3_scorecard_connected"] is True
    assert summary["p3_4_verdict_split_applied"] is False
    assert summary["blind_qa_ratings_applied"] is False
    assert summary["local_review_packet_retained"] is False
    assert connection["product_gate_ready"] is False
    assert connection["public_release_applied"] is False

    assert_product_readfeel_current_output_inventory_meta_only(inventory)
    assert_product_readfeel_scorecard_meta_only(scorecard)
    assert_product_readfeel_p3_inventory_connection_meta_only_20260609(connection)


def test_p3_3_summary_dump_excludes_local_review_packet_and_text_bodies() -> None:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-3-summary-dump-capture-test",
    )
    connection = build_product_readfeel_p3_inventory_connection_20260609(capture=capture)
    dumped = dump_product_readfeel_p3_inventory_connection_summary_20260609(connection)
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SUMMARY_VERSION_20260609
    assert parsed["sanitized_event_count"] == 60
    assert parsed["local_review_packet_retained"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert_product_readfeel_p3_inventory_connection_meta_only_20260609(parsed)

    assert "疲れた" not in dumped
    assert "今日は小さなことで" not in dumped
    assert "synthetic local QA output" not in dumped
    assert '"local_review_packet":' not in dumped
    assert '"sanitized_current_output_events":' not in dumped
    assert '"current_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"memo":' not in dumped


def test_p3_3_reason_codes_route_to_existing_inventory_failure_buckets() -> None:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-3-reason-code-capture-test",
    )
    events = [dict(event) for event in capture["sanitized_current_output_events"]]
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    self_denial = next(event for event in events if event["family"] == "self_denial")
    structure_question = next(event for event in events if event["family"] == "structure_question")

    daily_unpleasant["reason_codes"] = [
        *daily_unpleasant["reason_codes"],
        "rich_input_low_information_overroute",
    ]
    self_denial["reason_codes"] = [
        *self_denial["reason_codes"],
        "self_denial_identity_claim_risk",
    ]
    structure_question["reason_codes"] = [
        *structure_question["reason_codes"],
        "mirror_only_or_self_report_only",
    ]

    connection = build_product_readfeel_p3_inventory_connection_20260609(
        sanitized_events=events,
        run_id="p3-3-reason-code-test",
    )
    inventory = connection["current_output_inventory"]
    bucket_counts = inventory["failure_bucket_counts"]

    assert bucket_counts[FAILURE_READFEEL_GAP] >= 1
    assert bucket_counts[FAILURE_SURFACE_BREAKAGE] >= 1
    assert bucket_counts[FAILURE_STRUCTURE_INSIGHT_GAP] >= 1
    assert inventory["family_verdicts"]["daily_unpleasant"] == "YELLOW"
    assert inventory["family_verdicts"]["self_denial"] == "RED"
    assert inventory["family_verdicts"]["structure_question"] == "REPAIR_REQUIRED"
    assert "daily_unpleasant" in inventory["v1_fix_families"]
    assert "structure_question" in inventory["v2_structure_insight_backlog_families"]
    assert_product_readfeel_p3_inventory_connection_meta_only_20260609(connection)


def test_p3_3_guard_rejects_body_keys_and_forbidden_contract_flags() -> None:
    connection = build_product_readfeel_p3_inventory_connection_20260609(
        renderer=_fake_renderer,
        run_id="p3-3-guard-test",
    )
    unsafe_body = dict(connection["summary"])
    unsafe_body["comment_text"] = "summary must never retain a display body"
    unsafe_flag = dict(connection["summary"])
    unsafe_flag["gate_relaxed"] = True

    with pytest.raises(ValueError):
        assert_product_readfeel_p3_inventory_connection_meta_only_20260609(unsafe_body)
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_inventory_connection_meta_only_20260609(unsafe_flag)
