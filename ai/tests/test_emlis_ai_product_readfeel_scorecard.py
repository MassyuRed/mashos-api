from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_rubric import aggregate_product_readfeel_blind_qa_reviews
from emlis_ai_product_readfeel_scorecard import (
    PRODUCT_READFEEL_SCORECARD_STEP,
    PRODUCT_READFEEL_SCORECARD_VERSION,
    VERDICT_PRODUCT_PASS,
    assert_product_readfeel_scorecard_meta_only,
    build_product_readfeel_scorecard,
    normalize_product_readfeel_scorecard_to_scorecard_fields,
)
from fixtures.emlis_ai_product_readfeel_fixture_families import (
    build_product_readfeel_fixture_family_scorecard_events,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in (
            "raw_input",
            "raw_text",
            "input_text",
            "user_input",
            "memo",
            "memo_action",
            "emotion_details",
            "comment_text",
            "reply_text",
            "surface_text",
            "display_text",
            "candidate_body",
            "body",
            "text",
        ):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("input_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        assert payload.get("candidate_body_included") is not True
        assert payload.get("machine_metrics_used_for_read_feeling") is not True
        assert payload.get("read_feeling_auto_filled_from_machine_metrics") is not True
        assert payload.get("comment_text_written_by_scorecard") is not True
        assert payload.get("public_response_key_added") is not True
        assert payload.get("public_response_key_change") is not True
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _all_green_product_pass_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for family in PRODUCT_READFEEL_REQUIRED_FAMILIES:
        events.append(
            {
                "row_id": f"phase4-product-pass-{family}",
                "fixture_family": family,
                "coverage_group": family,
                "product_readfeel_family": family,
                "observation_status": "passed",
                "display_confirmed": True,
                "comment_text_present": True,
                "eligible_count": 1,
                "passed_display_count": 1,
                "binding_supported_sentence_count": 2,
                "expected_binding_count": 2,
                "reason_required_count": 1,
                "reason_covered_count": 1,
                "reason_codes": [],
                "mirror_only_detected": False,
                "self_report_only_detected": False,
                "material_slot_count": 5,
                "evidence_slot_count": 5,
                "source_field_ids": ["memo", "memo_action", "selected_emotions"],
                "ratings": {
                    "read_feeling": "green",
                    "self_report_retention": "green",
                    "state_structure_retention": "green",
                    "emotion_temperature_retention": "green",
                    "follow_depth": "green",
                    "evidence_boundary": "green",
                    "soft_inference_surface": "green",
                    "naturalness": "green",
                    "non_template": "green",
                    "insight_delta": "green",
                    "structure_insight_candidate_quality": "green",
                },
            }
        )
    assert len(events) == len(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    return events


def _green_v1_red_v2_review() -> dict[str, Any]:
    return {
        "review_id": "phase4-product-pass-v1-only",
        "fixture_family": "structure_question",
        "ratings": {
            "read_feeling": "green",
            "self_report_retention": "green",
            "state_structure_retention": "green",
            "emotion_temperature_retention": "green",
            "follow_depth": "green",
            "evidence_boundary": "green",
            "soft_inference_surface": "green",
            "naturalness": "green",
            "non_template": "green",
            "insight_delta": "red",
            "structure_insight_candidate_quality": "red",
        },
        "raw_input_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _passing_machine_metrics() -> dict[str, Any]:
    return {
        "display_reach_rate": 1.0,
        "binding_pass_rate": 1.0,
        "reason_coverage_rate": 1.0,
        "template_major_count": 0,
        "safety_major_count": 0,
        "surface_signature_repeat_rate": 0.0,
    }


def test_phase4_scorecard_aggregates_family_verdicts_and_keeps_v2_out_of_release_blockers() -> None:
    scorecard = build_product_readfeel_scorecard(
        events=build_product_readfeel_fixture_family_scorecard_events(),
        machine_metrics=_passing_machine_metrics(),
    )
    fields = normalize_product_readfeel_scorecard_to_scorecard_fields(scorecard)

    assert scorecard["version"] == PRODUCT_READFEEL_SCORECARD_VERSION
    assert scorecard["step"] == PRODUCT_READFEEL_SCORECARD_STEP
    assert scorecard["product_readfeel_scorecard_ready"] is True
    assert fields["product_readfeel_scorecard_ready"] is True
    assert fields["product_readfeel_family_verdict_counts"]["REPAIR_REQUIRED"] == 1
    assert fields["product_readfeel_family_verdict_counts"]["PASS"] == 11
    assert "input_self_report_only_failure" in scorecard["v2_structure_insight_backlog_families"]
    assert scorecard["insight_delta_release_blocker"] is False
    assert not any("insight_delta" in blocker for blocker in scorecard["release_blockers"])
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False
    _assert_meta_only(scorecard)
    _assert_meta_only(fields)


def test_phase4_machine_read_feeling_never_fills_blind_qa_read_feeling() -> None:
    scorecard = build_product_readfeel_scorecard(
        events=[_all_green_product_pass_events()[0]],
        machine_metrics={**_passing_machine_metrics(), "read_feeling_score": 1.0},
        blind_qa_reviews=[],
    )

    assert scorecard["blind_qa_ready"] is False
    assert scorecard["read_feeling_score"] is None
    assert scorecard["machine_metrics"]["read_feeling_score"] is None
    assert scorecard["machine_metrics_used_for_read_feeling"] is False
    assert scorecard["read_feeling_auto_filled_from_machine_metrics"] is False
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False


def test_phase4_can_aggregate_product_pass_candidate_without_public_release_or_v2_gate() -> None:
    events = _all_green_product_pass_events()
    inventory = {
        "version": "test.product_readfeel.phase4.all_pass_inventory",
        "observed_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "missing_families": [],
        "family_verdicts": {family: "PASS" for family in PRODUCT_READFEEL_REQUIRED_FAMILIES},
        "family_summaries": [
            {
                "family": family,
                "verdict": "PASS",
                "item_count": 1,
                "failure_bucket_counts": {},
                "v1_repair_required": False,
                "v2_structure_insight_backlog": False,
            }
            for family in PRODUCT_READFEEL_REQUIRED_FAMILIES
        ],
        "failure_bucket_counts": {},
        "v1_fix_families": [],
        "v2_structure_insight_backlog_families": [],
    }
    blind_qa = aggregate_product_readfeel_blind_qa_reviews([_green_v1_red_v2_review()])
    scorecard = build_product_readfeel_scorecard(
        events=events,
        current_output_inventory=inventory,
        blind_qa_aggregate=blind_qa,
        machine_metrics=_passing_machine_metrics(),
    )
    fields = normalize_product_readfeel_scorecard_to_scorecard_fields(scorecard)

    assert scorecard["aggregate_verdict"] == VERDICT_PRODUCT_PASS
    assert fields["product_readfeel_product_pass_candidate"] is True
    assert fields["product_readfeel_product_pass_count"] >= 1
    assert fields["product_readfeel_v2_structure_insight_ready"] is False
    assert fields["product_readfeel_insight_delta_release_blocker"] is False
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False
    assert scorecard["comment_text_written_by_scorecard"] is False
    assert scorecard["public_response_key_added"] is False
    _assert_meta_only(scorecard)


def test_phase4_connects_to_complete_product_quality_scorecard_without_contract_change() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=build_product_readfeel_fixture_family_scorecard_events(),
    )

    assert scorecard["phase4_product_readfeel_scorecard_ready"] is True
    assert scorecard["product_readfeel_scorecard_ready"] is True
    assert scorecard["product_readfeel_scorecard_version"] == PRODUCT_READFEEL_SCORECARD_VERSION
    assert scorecard["product_readfeel_aggregate_verdict"] == "REPAIR_REQUIRED"
    assert scorecard["product_readfeel_family_verdict_counts"]["REPAIR_REQUIRED"] == 1
    assert scorecard["product_readfeel_insight_delta_release_blocker"] is False
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False
    assert scorecard["public_response_key_change"] is False
    _assert_meta_only(scorecard["phase4_product_readfeel_scorecard"])
    _assert_meta_only(scorecard["phase4_product_readfeel_scorecard_fields"])


def test_phase4_meta_only_guard_rejects_text_keys_release_and_public_key_mutation() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_scorecard_meta_only({"comment_text": "出してはいけない"})
    with pytest.raises(ValueError):
        assert_product_readfeel_scorecard_meta_only({"product_gate_ready": True})
    with pytest.raises(ValueError):
        assert_product_readfeel_scorecard_meta_only({"public_response_key_added": True})
