from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_product_readfeel_current_output_inventory import (
    FAILURE_CONTRACT_VIOLATION,
    FAILURE_DISPLAY_NOT_REACHED,
    FAILURE_READFEEL_GAP,
    FAILURE_STRUCTURE_INSIGHT_GAP,
    PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
    PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
    VERDICT_PASS,
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_YELLOW,
    assert_product_readfeel_current_output_inventory_meta_only,
    build_product_readfeel_current_output_inventory,
    normalize_product_readfeel_current_output_inventory_to_scorecard_fields,
    normalize_product_readfeel_current_output_item,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in (
            "raw_input",
            "raw_text",
            "input_text",
            "user_input",
            "comment_text",
            "reply_text",
            "surface_text",
            "display_text",
            "accepted_surface_probe",
            "body",
            "text",
        ):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        assert payload.get("public_response_key_change") is not True
        assert payload.get("rn_visible_contract_changed") is not True
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _displayed_event(row_id: str, family: str) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "fixture_family": family,
        "coverage_group": family,
        "observation_status": "passed",
        "display_confirmed": True,
        "comment_text_present": True,
        "eligible_count": 1,
        "passed_display_count": 1,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "relation_types": ["coexistence"],
        "surface_signature_family_key": f"sig-{row_id}",
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def test_phase1_normalizes_current_output_item_without_retaining_display_body() -> None:
    item = normalize_product_readfeel_current_output_item(
        {
            "row_id": "daily-unpleasant-not-displayed",
            "fixture_family": "daily_unpleasant",
            "observation_status": "rejected",
            "eligible_count": 1,
            "passed_display_count": 0,
            "display_confirmed": False,
            "raw_input": "ユーザー本文は棚卸しmetaへ保持しない",
            "comment_text": "表示本文も棚卸しmetaへ保持しない",
        }
    )

    assert item["source_step"] == PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP
    assert item["product_readfeel_family"] == "daily_unpleasant"
    assert item["display_not_reached"] is True
    assert item["verdict"] == VERDICT_REPAIR_REQUIRED
    assert FAILURE_DISPLAY_NOT_REACHED in item["failure_buckets"]
    assert item["source_display_body_seen"] is True
    assert item["source_display_body_retained"] is False
    assert item["exact_comment_text_required"] is False
    _assert_meta_only(item)


def test_phase1_inventory_classifies_family_verdicts_and_separates_v1_v2() -> None:
    inventory = build_product_readfeel_current_output_inventory(
        events=[
            _displayed_event("positive-pass", "daily_positive"),
            {
                **_displayed_event("long-mirror", "long_meaning_arc"),
                "mirror_only_detected": True,
                "material_slot_count": 4,
            },
            {
                **_displayed_event("relationship-contract", "relationship_boundary"),
                "public_response_key_change": True,
            },
        ],
        blind_qa_reviews=[
            {
                "review_id": "review-positive-yellow",
                "fixture_family": "daily_positive",
                "ratings": {
                    "read_feeling": "yellow",
                    "self_report_retention": "green",
                    "state_structure_retention": "green",
                    "emotion_temperature_retention": "green",
                    "follow_depth": "yellow",
                    "evidence_boundary": "green",
                    "naturalness": "green",
                    "non_template": "green",
                },
                "comment_text": "Blind QAに表示本文が渡っても棚卸しmetaへ保持しない",
            }
        ],
        run_id="phase1-inventory-test",
    )

    assert inventory["version"] == PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION
    assert inventory["phase1_current_output_inventory_ready"] is True
    assert inventory["family_verdicts"]["daily_positive"] == VERDICT_YELLOW
    assert inventory["family_verdicts"]["long_meaning_arc"] == VERDICT_REPAIR_REQUIRED
    assert inventory["family_verdicts"]["relationship_boundary"] == VERDICT_RED
    assert inventory["failure_bucket_counts"][FAILURE_READFEEL_GAP] == 1
    assert inventory["failure_bucket_counts"][FAILURE_STRUCTURE_INSIGHT_GAP] == 1
    assert inventory["failure_bucket_counts"][FAILURE_CONTRACT_VIOLATION] == 1
    assert inventory["mirror_only_detected_count"] == 1
    assert "long_meaning_arc" in inventory["v1_fix_families"]
    assert "long_meaning_arc" in inventory["v2_structure_insight_backlog_families"]
    assert inventory["runtime_branching_uses_fixture_strings"] is False
    assert inventory["product_gate_ready"] is False
    _assert_meta_only(inventory)


def test_phase1_inventory_scorecard_fields_are_meta_only_and_compact() -> None:
    inventory = build_product_readfeel_current_output_inventory(
        events=[_displayed_event("low-info-pass", "low_information_short")],
    )
    fields = normalize_product_readfeel_current_output_inventory_to_scorecard_fields(inventory)

    assert fields["product_readfeel_current_output_inventory_version"] == PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION
    assert fields["phase1_product_readfeel_current_output_inventory_ready"] is True
    assert fields["product_readfeel_item_count"] == 1
    assert fields["product_readfeel_family_verdicts"] == {"low_information_short": VERDICT_PASS}
    assert fields["product_readfeel_v1_fix_families"] == []
    assert fields["product_readfeel_v2_structure_insight_backlog_families"] == []
    _assert_meta_only(fields)


def test_phase1_inventory_connects_to_complete_product_quality_scorecard_without_release_or_public_contract_change() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            _displayed_event("phase1-short", "low_information_short"),
            {
                **_displayed_event("phase1-structure", "structure_question"),
                "mirror_only_detected": True,
                "material_slot_count": 4,
            },
        ],
        blind_qa_reviews=[
            {
                "review_id": "phase1-review",
                "fixture_family": "structure_question",
                "ratings": {
                    "read_feeling": "green",
                    "self_report_retention": "green",
                    "state_structure_retention": "green",
                    "emotion_temperature_retention": "green",
                    "follow_depth": "green",
                    "evidence_boundary": "green",
                    "insight_delta": "yellow",
                    "naturalness": "green",
                    "non_template": "green",
                },
            }
        ],
    )

    assert scorecard["phase1_product_readfeel_current_output_inventory_ready"] is True
    assert scorecard["product_readfeel_current_output_inventory_version"] == PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION
    assert scorecard["product_readfeel_family_verdicts"]["low_information_short"] == VERDICT_PASS
    assert scorecard["product_readfeel_family_verdicts"]["structure_question"] == VERDICT_REPAIR_REQUIRED
    assert "structure_question" in scorecard["product_readfeel_v1_fix_families"]
    assert "structure_question" in scorecard["product_readfeel_v2_structure_insight_backlog_families"]
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False
    assert scorecard["public_response_key_change"] is False
    _assert_meta_only(scorecard["phase1_product_readfeel_current_output_inventory"])


def test_phase1_meta_only_assert_rejects_text_keys_and_contract_relaxation() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_current_output_inventory_meta_only({"comment_text": "出してはいけない"})
    with pytest.raises(ValueError):
        assert_product_readfeel_current_output_inventory_meta_only({"display_gate_relaxed": True})
