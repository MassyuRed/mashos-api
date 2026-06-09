from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_verdict_split import (
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_ROW_VERSION_20260609,
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609,
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609,
    VERDICT_LAYER_NOT_EVALUATED,
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
    assert_product_readfeel_p3_verdict_split_meta_only_20260609,
    build_product_readfeel_p3_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_inventory_connection_20260609 import (
    build_product_readfeel_p3_inventory_connection_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_local_output_capture_20260609 import (
    build_product_readfeel_p3_local_output_capture_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_verdict_split_20260609 import (
    build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609,
    dump_product_readfeel_p3_verdict_split_summary_from_inventory_connection_20260609,
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


def _events_from_fake_capture() -> list[dict[str, Any]]:
    capture = build_product_readfeel_p3_local_output_capture_20260609(
        renderer=_fake_renderer,
        run_id="p3-4-verdict-split-capture-test",
    )
    return [dict(event) for event in capture["sanitized_current_output_events"]]


def _append_reason(event: dict[str, Any], reason: str) -> None:
    event["reason_codes"] = [*list(event.get("reason_codes") or []), reason]


def test_p3_4_verdict_split_builds_60_body_free_rows_from_p3_3_connection() -> None:
    connection = build_product_readfeel_p3_inventory_connection_20260609(
        renderer=_fake_renderer,
        run_id="p3-4-verdict-split-connection-test",
    )
    split = build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
        connection=connection,
        run_id="p3-4-verdict-split-test",
    )
    summary = split["summary"]
    rows = split["verdict_rows"]

    assert split["schema_version"] == PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609
    assert split["source_step"] == PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609
    assert summary["schema_version"] == PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609
    assert len(rows) == 60
    assert summary["verdict_row_count"] == 60
    assert summary["sanitized_event_count"] == 60
    assert summary["source_inventory_item_count"] == 60
    assert summary["all_rows_have_verdict"] is True
    assert set(summary["observed_required_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert summary["missing_required_families"] == []
    assert summary["all_required_families_have_verdict"] is True
    assert summary["red_and_repair_required_separated"] is True
    assert summary["p2_red_count"] == 0
    assert summary["can_continue_p3_repair"] is True
    assert summary["p3_4_verdict_split_applied"] is True
    assert summary["blind_qa_ratings_applied"] is False
    assert split["product_gate_ready"] is False
    assert split["public_release_applied"] is False

    for row in rows:
        assert row["schema_version"] == PRODUCT_READFEEL_P3_VERDICT_SPLIT_ROW_VERSION_20260609
        assert row["verdict"] in {"RED", "REPAIR_REQUIRED", "YELLOW", "PASS", "NOT_EVALUATED"}
        assert row["comment_text_body_included"] is False
        assert row["raw_input_included"] is False
        assert row["candidate_body_included"] is False
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(split)


def test_p3_4_classifies_p2_red_separately_from_p3_repair() -> None:
    events = _events_from_fake_capture()
    self_denial = next(event for event in events if event["family"] == "self_denial")
    relationship = next(event for event in events if event["family"] == "relationship_boundary")
    structure = next(event for event in events if event["family"] == "structure_question")
    _append_reason(self_denial, "self_denial_identity_claim_risk")
    _append_reason(relationship, "malformed_nominalization_surface")
    _append_reason(structure, "public_response_key_change_detected")

    split = build_product_readfeel_p3_verdict_split_20260609(
        sanitized_current_output_events=events,
        run_id="p3-4-red-split-test",
    )
    summary = split["summary"]
    red_rows = [row for row in split["verdict_rows"] if row["verdict_layer"] == VERDICT_LAYER_P2_RED]

    assert len(red_rows) >= 3
    assert summary["p2_red_count"] >= 3
    assert summary["p2_red_present"] is True
    assert summary["can_continue_p3_repair"] is False
    assert summary["p3_repair_should_not_start_until_p2_red_cleared"] is True
    assert summary["decision"] == "return_to_p2_surface_safety"
    assert summary["first_repair_targets"]
    assert summary["first_repair_targets"][0]["verdict_layer"] == VERDICT_LAYER_P2_RED
    assert all(row["verdict"] == "RED" for row in red_rows)
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(split)


def test_p3_4_classifies_p3_repair_required_and_yellow_without_p2_red() -> None:
    events = _events_from_fake_capture()
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    mixed_emotion = next(event for event in events if event["family"] == "mixed_emotion")
    positive_only = next(event for event in events if event["family"] == "positive_only")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    _append_reason(mixed_emotion, "generic_reception_surface")
    _append_reason(positive_only, "family_temperature_flattened")

    split = build_product_readfeel_p3_verdict_split_20260609(
        sanitized_current_output_events=events,
        run_id="p3-4-repair-yellow-test",
    )
    summary = split["summary"]
    daily_row = next(row for row in split["verdict_rows"] if row["case_id"] == daily_unpleasant["case_id"])
    mixed_row = next(row for row in split["verdict_rows"] if row["case_id"] == mixed_emotion["case_id"])
    positive_row = next(row for row in split["verdict_rows"] if row["case_id"] == positive_only["case_id"])

    assert summary["p2_red_count"] == 0
    assert summary["can_continue_p3_repair"] is True
    assert daily_row["verdict"] == "REPAIR_REQUIRED"
    assert daily_row["verdict_layer"] == VERDICT_LAYER_P3_REPAIR_REQUIRED
    assert "rich_input_low_information_overroute" in daily_row["blocker_ids"]
    assert mixed_row["verdict"] == "YELLOW"
    assert mixed_row["verdict_layer"] == VERDICT_LAYER_P3_YELLOW
    assert positive_row["verdict"] == "YELLOW"
    assert positive_row["verdict_layer"] == VERDICT_LAYER_P3_YELLOW
    assert "rich_input_low_information_overroute" in summary["first_repair_target_blocker_ids"]
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(split)


def test_p3_4_excludes_safety_infra_and_true_unavailable_from_p3_repair() -> None:
    events = _events_from_fake_capture()
    event = next(event for event in events if event["family"] == "daily_positive")
    event["observation_status"] = "unavailable"
    event["public_reached"] = False
    event["rn_visible"] = False
    event["comment_text_present"] = False
    event["comment_text_length"] = 0
    event["comment_text_fingerprint"] = ""
    event["renderer_exception"] = "RuntimeError"
    _append_reason(event, "renderer_exception")

    split = build_product_readfeel_p3_verdict_split_20260609(
        sanitized_current_output_events=events,
        run_id="p3-4-not-evaluated-test",
    )
    row = next(row for row in split["verdict_rows"] if row["case_id"] == event["case_id"])

    assert row["verdict"] == "NOT_EVALUATED"
    assert row["verdict_layer"] == VERDICT_LAYER_NOT_EVALUATED
    assert row["not_evaluated"] is True
    assert row["excluded_from_p3_readfeel_repair"] is True
    assert split["summary"]["not_evaluated_count"] >= 1
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(split)


def test_p3_4_summary_dump_excludes_source_events_inventory_and_bodies() -> None:
    connection = build_product_readfeel_p3_inventory_connection_20260609(
        renderer=_fake_renderer,
        run_id="p3-4-summary-dump-connection-test",
    )
    dumped = dump_product_readfeel_p3_verdict_split_summary_from_inventory_connection_20260609(
        connection=connection,
        run_id="p3-4-summary-dump-test",
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609
    assert parsed["verdict_row_count"] == 60
    assert parsed["p3_4_verdict_split_applied"] is True
    assert parsed["comment_text_body_included"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(parsed)

    assert "疲れた" not in dumped
    assert "今日は小さなことで" not in dumped
    assert "synthetic local QA output" not in dumped
    assert '"sanitized_current_output_events":' not in dumped
    assert '"source_current_output_inventory":' not in dumped
    assert '"verdict_rows":' not in dumped
    assert '"current_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"memo":' not in dumped


def test_p3_4_guard_rejects_actual_body_keys_and_forbidden_contract_flags() -> None:
    events = _events_from_fake_capture()
    unsafe_source = dict(events[0])
    unsafe_source["comment_text"] = "actual display body must not enter P3-4 source"
    with pytest.raises(ValueError):
        build_product_readfeel_p3_verdict_split_20260609(
            sanitized_current_output_events=[unsafe_source],
            run_id="p3-4-source-body-guard-test",
        )

    split = build_product_readfeel_p3_verdict_split_20260609(
        sanitized_current_output_events=events,
        run_id="p3-4-guard-test",
    )
    unsafe_summary_body = dict(split["summary"])
    unsafe_summary_body["comment_text"] = "summary must never retain display body"
    unsafe_summary_flag = dict(split["summary"])
    unsafe_summary_flag["gate_relaxed"] = True

    with pytest.raises(ValueError):
        assert_product_readfeel_p3_verdict_split_meta_only_20260609(unsafe_summary_body)
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_verdict_split_meta_only_20260609(unsafe_summary_flag)
