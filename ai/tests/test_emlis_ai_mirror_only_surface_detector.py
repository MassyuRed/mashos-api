from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_mirror_only_surface_detector import (
    MIRROR_ONLY_SURFACE_DETECTOR_STEP,
    MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
    VERDICT_PASS,
    VERDICT_REPAIR_REQUIRED,
    assert_mirror_only_surface_detector_meta_only,
    build_mirror_only_surface_detector_summary,
    detect_mirror_only_surface,
    enrich_events_with_mirror_only_surface_detection,
    normalize_mirror_only_surface_to_scorecard_event,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    FAILURE_STRUCTURE_INSIGHT_GAP,
    VERDICT_REPAIR_REQUIRED as INVENTORY_REPAIR_REQUIRED,
    build_product_readfeel_current_output_inventory,
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
            "commentText",
            "reply_text",
            "surface_text",
            "display_text",
            "visible_text",
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
        assert payload.get("comment_text_written_by_detector") is not True
        assert payload.get("comment_text_written_by_scorecard") is not True
        assert payload.get("public_response_key_added") is not True
        assert payload.get("public_response_key_change") is not True
        assert payload.get("response_shape_changed") is not True
        assert payload.get("rn_visible_contract_changed") is not True
        assert payload.get("rn_visible_title_changed") is not True
        assert payload.get("gate_relaxed") is not True
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _strict_structure_event(row_id: str = "phase6-long-mirror") -> dict[str, Any]:
    return {
        "row_id": row_id,
        "fixture_family": "long_meaning_arc",
        "coverage_group": "long_meaning_arc",
        "observation_status": "passed",
        "display_confirmed": True,
        "comment_text_present": True,
        "eligible_count": 1,
        "passed_display_count": 1,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "material_slot_count": 5,
        "evidence_slot_count": 5,
        "source_field_ids": ["memo", "memo_action", "selected_emotions", "emotion_details", "category"],
        "input_material_flags": {
            "memo_present": True,
            "memo_action_present": True,
            "selected_emotions_present": True,
            "emotion_details_present": True,
            "category_present": True,
            "long_input": True,
        },
        "comment_text": "見えたこと：たくさん考えて、大変だったんですね。\n\nEmlisから：しんどかったですね。",
    }


def test_phase6_detects_mirror_only_for_sufficient_strict_structure_surface_meta_only() -> None:
    report = detect_mirror_only_surface(_strict_structure_event(), run_id="phase6-detector-test")
    fields = normalize_mirror_only_surface_to_scorecard_event(report)

    assert report["version"] == MIRROR_ONLY_SURFACE_DETECTOR_VERSION
    assert report["step"] == MIRROR_ONLY_SURFACE_DETECTOR_STEP
    assert report["phase6_mirror_only_detector_ready"] is True
    assert report["product_readfeel_family"] == "long_meaning_arc"
    assert report["input_material_sufficient_for_insight"] is True
    assert report["strict_mirror_only_family"] is True
    assert report["mirror_only_detected"] is True
    assert report["v1_classification"] == VERDICT_REPAIR_REQUIRED
    assert report["v1_yellow_or_repair_connected"] is True
    assert report["v2_insight_delta_gap"] is True
    assert "mirror_only_detected" in report["mirror_only_reason_codes"]
    assert fields["mirror_only_detected"] is True
    assert fields["mirror_only_v1_classification"] == VERDICT_REPAIR_REQUIRED
    assert fields["mirror_only_v2_insight_delta_gap"] is True
    _assert_meta_only(report)
    _assert_meta_only(fields)


def test_phase6_does_not_over_detect_low_information_or_daily_light_reception() -> None:
    low_information = detect_mirror_only_surface(
        {
            "fixture_family": "low_information_short",
            "comment_text": "見えたこと：疲れが出ているんですね。\n\nEmlisから：詳しく残せそうなら、少しだけ残してみませんか。",
            "input_material_flags": {"memo_present": True},
            "material_slot_count": 1,
        }
    )
    daily_reception = detect_mirror_only_surface(
        {
            "fixture_family": "daily_unpleasant",
            "comment_text": "見えたこと：嫌なことがあったんですね。\n\nEmlisから：つらかったですね。",
            "input_material_flags": {"memo_present": True, "memo_action_present": True},
            "material_slot_count": 2,
        }
    )

    assert low_information["mirror_only_detected"] is False
    assert low_information["protected_light_reception"] is True
    assert low_information["v1_classification"] == VERDICT_PASS
    assert daily_reception["mirror_only_detected"] is False
    assert daily_reception["protected_light_reception"] is True
    assert daily_reception["v1_classification"] == VERDICT_PASS
    _assert_meta_only(low_information)
    _assert_meta_only(daily_reception)


def test_phase6_relation_or_soft_insight_seed_avoids_mirror_only_detection() -> None:
    report = detect_mirror_only_surface(
        {
            "fixture_family": "structure_question",
            "input_material_flags": {
                "memo_present": True,
                "memo_action_present": True,
                "selected_emotions_present": True,
                "emotion_details_present": True,
            },
            "source_field_ids": ["memo", "memo_action", "selected_emotions", "emotion_details"],
            "evidence_slot_count": 4,
            "comment_text": "見えたこと：変えたい気持ちと動けない状態がぶつかっていて、疲れとして残っているように見えます。\n\nEmlisから：その分だけ重く感じているのかもしれません。",
        }
    )

    assert report["product_readfeel_family"] == "structure_question"
    assert report["mirror_only_detected"] is False
    assert report["relation_marker_count"] >= 1
    assert report["insight_marker_count"] >= 1
    assert report["v1_classification"] == VERDICT_PASS
    _assert_meta_only(report)


def test_phase6_enriches_events_and_summary_without_retaining_comment_body() -> None:
    events = [
        _strict_structure_event(),
        {
            "row_id": "phase6-daily-guard",
            "fixture_family": "daily_positive",
            "comment_text": "見えたこと：嬉しいことがあったんですね。\n\nEmlisから：よかったですね。",
            "input_material_flags": {"memo_present": True, "memo_action_present": True},
        },
    ]

    enriched = enrich_events_with_mirror_only_surface_detection(events)
    summary = build_mirror_only_surface_detector_summary(events=events, run_id="phase6-summary-test")

    assert enriched[0]["mirror_only_detected"] is True
    assert enriched[0]["mirror_only_v2_insight_delta_gap"] is True
    assert "comment_text" not in enriched[0]
    assert enriched[1]["mirror_only_detected"] is False
    assert summary["phase6_mirror_only_detector_ready"] is True
    assert summary["mirror_only_detected_count"] == 1
    assert summary["mirror_only_v1_yellow_or_repair_connected_count"] >= 1
    assert summary["mirror_only_v2_insight_delta_gap_count"] == 1
    assert summary["completion_conditions"]["comment_text_body_retained"] is False
    _assert_meta_only(enriched)
    _assert_meta_only(summary)


def test_phase6_connects_to_current_output_inventory_v1_and_v2_without_body_leak() -> None:
    inventory = build_product_readfeel_current_output_inventory(
        events=[_strict_structure_event("phase6-inventory-long")],
        run_id="phase6-inventory-test",
    )

    assert inventory["phase6_mirror_only_detector_ready"] is True
    assert inventory["mirror_only_detected_count"] == 1
    assert inventory["family_verdicts"]["long_meaning_arc"] == INVENTORY_REPAIR_REQUIRED
    assert FAILURE_STRUCTURE_INSIGHT_GAP in inventory["failure_bucket_counts"]
    assert "long_meaning_arc" in inventory["v1_fix_families"]
    assert "long_meaning_arc" in inventory["v2_structure_insight_backlog_families"]
    _assert_meta_only(inventory)


def test_phase6_connects_to_complete_scorecard_without_public_contract_or_release_change() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[_strict_structure_event("phase6-complete-long")],
        blind_qa_reviews=[],
    )

    assert scorecard["phase6_mirror_only_detector_ready"] is True
    assert scorecard["phase6_product_readfeel_mirror_only_detector_ready"] is True
    assert scorecard["product_readfeel_mirror_only_surface_detected_count"] == 1
    assert scorecard["product_readfeel_mirror_only_v1_yellow_or_repair_connected_count"] >= 1
    assert scorecard["product_readfeel_mirror_only_v2_insight_delta_gap_count"] == 1
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False
    assert scorecard["public_response_key_change"] is False
    assert scorecard.get("comment_text_written_by_scorecard") is not True
    _assert_meta_only(scorecard["phase6_product_readfeel_mirror_only_surface_detector"])
    _assert_meta_only(scorecard["phase6_product_readfeel_mirror_only_surface_detector_fields"])


def test_phase6_meta_only_assert_rejects_comment_body_and_contract_changes() -> None:
    with pytest.raises(ValueError):
        assert_mirror_only_surface_detector_meta_only({"comment_text": "本文は保持しない"})
    with pytest.raises(ValueError):
        assert_mirror_only_surface_detector_meta_only({"public_response_key_added": True})
