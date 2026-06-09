from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_blind_qa_ratings_review import (
    PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609,
    PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609,
    PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609,
    PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609,
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609,
    build_product_readfeel_p3_blind_qa_ratings_review_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
    build_product_readfeel_p3_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609 import (
    build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609,
    build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609,
    dump_product_readfeel_p3_blind_qa_ratings_summary_from_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_local_output_capture_20260609 import (
    build_product_readfeel_p3_local_output_capture_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_verdict_split_20260609 import (
    build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609,
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
        run_id="p3-5-capture-test",
    )
    return [dict(event) for event in capture["sanitized_current_output_events"]]


def _append_reason(event: dict[str, Any], reason: str) -> None:
    event["reason_codes"] = [*list(event.get("reason_codes") or []), reason]


def test_p3_5_builds_ratings_only_material_and_connects_to_scorecard() -> None:
    split = build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
        renderer=_fake_renderer,
        run_id="p3-5-ratings-scorecard-split-test",
    )
    reviews = build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(verdict_split=split)
    material = build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
        verdict_split=split,
        blind_qa_reviews=reviews,
        run_id="p3-5-ratings-scorecard-test",
    )
    summary = material["summary"]
    scorecard = material["product_readfeel_scorecard"]

    assert material["schema_version"] == PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609
    assert material["source_step"] == PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609
    assert summary["schema_version"] == PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609
    assert len(material["review_rows"]) == 60
    assert material["review_row_count"] == 60
    assert summary["expected_review_count"] == 60
    assert summary["review_count"] == 60
    assert summary["all_expected_cases_reviewed"] is True
    assert set(summary["observed_review_families"]) == set(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    assert summary["missing_review_families"] == []
    assert summary["family_score_minimums_visible"] is True
    assert summary["family_score_averages_visible"] is True
    assert summary["red_repair_yellow_reasons_connected_to_ratings"] is True
    assert summary["read_feeling_score"] is not None
    assert summary["naturalness_score"] is not None
    assert summary["non_template_score"] is not None
    assert summary["machine_metrics_used_for_read_feeling"] is False
    assert summary["read_feeling_auto_filled_from_machine_metrics"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["product_gate_ready"] is False
    assert summary["public_release_applied"] is False
    assert scorecard["blind_qa_ready"] is True
    assert scorecard["read_feeling_source"] == "blind_qa_review_ratings"
    assert scorecard["machine_metrics_used_for_read_feeling"] is False
    assert scorecard["public_release_applied"] is False

    for row in material["review_rows"]:
        assert row["schema_version"] == PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609
        assert row["ratings_only_payload"] is True
        assert row["comment_text_body_included"] is False
        assert row["raw_input_included"] is False
        assert row["candidate_body_included"] is False
        assert row["read_feeling_auto_filled_from_machine_metrics"] is False
        assert row["verdict_reason_rating_connected"] is True
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(material)


def test_p3_5_without_reviews_keeps_read_feeling_not_evaluated_and_never_autofills_from_verdicts() -> None:
    split = build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
        renderer=_fake_renderer,
        run_id="p3-5-no-review-split-test",
    )
    material = build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
        verdict_split=split,
        blind_qa_reviews=[],
        run_id="p3-5-no-review-test",
    )
    summary = material["summary"]
    scorecard = material["product_readfeel_scorecard"]

    assert material["review_row_count"] == 0
    assert material["blind_qa_aggregate"]["blind_qa_ready"] is False
    assert material["blind_qa_aggregate"]["read_feeling_score"] is None
    assert summary["review_count"] == 0
    assert summary["unreviewed_case_count"] == 60
    assert summary["all_expected_cases_reviewed"] is False
    assert summary["decision"] == "wait_for_blind_qa_ratings"
    assert summary["read_feeling_score"] is None
    assert summary["read_feeling_source"] == "blind_qa_required_not_evaluated"
    assert summary["machine_metrics_used_for_read_feeling"] is False
    assert summary["read_feeling_auto_filled_from_machine_metrics"] is False
    assert scorecard["blind_qa_ready"] is False
    assert scorecard["read_feeling_score"] is None
    assert scorecard["read_feeling_auto_filled_from_machine_metrics"] is False
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(material)


def test_p3_5_keeps_p2_red_separate_from_ratings_and_connects_repair_yellow_context() -> None:
    events = _events_from_fake_capture()
    self_denial = next(event for event in events if event["family"] == "self_denial")
    daily_unpleasant = next(event for event in events if event["family"] == "daily_unpleasant")
    mixed_emotion = next(event for event in events if event["family"] == "mixed_emotion")
    _append_reason(self_denial, "self_denial_identity_claim_risk")
    _append_reason(daily_unpleasant, "rich_input_low_information_overroute")
    _append_reason(mixed_emotion, "generic_reception_surface")

    split = build_product_readfeel_p3_verdict_split_20260609(
        sanitized_current_output_events=events,
        run_id="p3-5-red-repair-yellow-split-test",
    )
    reviews = build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(verdict_split=split)
    material = build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
        verdict_split=split,
        blind_qa_reviews=reviews,
        run_id="p3-5-red-repair-yellow-test",
    )
    summary = material["summary"]
    red_review = next(row for row in material["review_rows"] if row["case_id"] == self_denial["case_id"])
    repair_review = next(row for row in material["review_rows"] if row["case_id"] == daily_unpleasant["case_id"])
    yellow_review = next(row for row in material["review_rows"] if row["case_id"] == mixed_emotion["case_id"])

    assert summary["p2_red_count"] >= 1
    assert summary["p2_red_present"] is True
    assert summary["p2_red_blocks_product_readfeel_repair"] is True
    assert summary["ratings_do_not_override_p2_red"] is True
    assert summary["decision"] == "return_to_p2_surface_safety"
    assert red_review["source_verdict_layer"] == VERDICT_LAYER_P2_RED
    assert red_review["p2_red_review_context"] is True
    assert repair_review["source_verdict_layer"] == VERDICT_LAYER_P3_REPAIR_REQUIRED
    assert "rich_input_low_information_overroute" in repair_review["source_blocker_ids"]
    assert yellow_review["source_verdict_layer"] == VERDICT_LAYER_P3_YELLOW
    assert "generic_reception_surface" in yellow_review["source_blocker_ids"]
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(material)


def test_p3_5_public_summary_dump_excludes_review_rows_inventory_source_rows_and_bodies() -> None:
    split = build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
        renderer=_fake_renderer,
        run_id="p3-5-summary-dump-split-test",
    )
    reviews = build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(verdict_split=split)
    dumped = dump_product_readfeel_p3_blind_qa_ratings_summary_from_verdict_split_20260609(
        verdict_split=split,
        blind_qa_reviews=reviews,
        run_id="p3-5-summary-dump-test",
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609
    assert parsed["review_count"] == 60
    assert parsed["blind_qa_ratings_applied"] is True
    assert parsed["comment_text_body_included"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["candidate_body_included"] is False
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(parsed)

    assert "疲れた" not in dumped
    assert "今日は小さなことで" not in dumped
    assert "synthetic local QA output" not in dumped
    assert '"review_rows":' not in dumped
    assert '"verdict_rows":' not in dumped
    assert '"source_current_output_inventory":' not in dumped
    assert '"product_readfeel_scorecard":' not in dumped
    assert '"current_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"memo":' not in dumped


def test_p3_5_guard_rejects_body_keys_and_forbidden_contract_flags() -> None:
    split = build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
        renderer=_fake_renderer,
        run_id="p3-5-guard-split-test",
    )
    reviews = build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(verdict_split=split)
    unsafe_review = dict(reviews[0])
    unsafe_review["comment_text"] = "actual display body must never enter P3-5 ratings"
    with pytest.raises(ValueError):
        build_product_readfeel_p3_blind_qa_ratings_review_20260609(
            verdict_split=split,
            blind_qa_reviews=[unsafe_review],
            run_id="p3-5-review-body-guard-test",
        )

    material = build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
        verdict_split=split,
        blind_qa_reviews=reviews,
        run_id="p3-5-guard-test",
    )
    unsafe_summary_body = dict(material["summary"])
    unsafe_summary_body["memo"] = "raw input must not be retained"
    unsafe_flag = dict(material["summary"])
    unsafe_flag["gate_relaxed"] = True
    unsafe_machine = dict(material["summary"])
    unsafe_machine["read_feeling_auto_filled_from_machine_metrics"] = True

    with pytest.raises(ValueError):
        assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(unsafe_summary_body)
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(unsafe_flag)
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(unsafe_machine)
