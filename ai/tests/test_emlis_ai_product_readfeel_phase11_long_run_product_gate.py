from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_long_run_product_gate import (
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
    PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
    ProductReadFeelLongRunProductGateMetaOnlyError,
    assert_product_readfeel_long_run_product_gate_meta_only,
    build_product_readfeel_long_run_product_gate,
    normalize_product_readfeel_long_run_product_gate_to_scorecard_fields,
)
from emlis_ai_runtime_surface_blind_qa_long_run import (
    build_runtime_surface_blind_qa_long_run_summary,
    normalize_runtime_surface_blind_qa_long_run_to_scorecard_fields,
)

_INSIGHT_FAMILIES = {"structure_question", "long_meaning_arc", "self_understanding_follow"}


def _ratings() -> dict[str, str]:
    return {
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
        # Existing Step11 Blind QA aliases.
        "evidence_retention": "green",
        "distance": "green",
    }


def _event(
    family: str,
    index: int,
    *,
    surface_signature: str | None = None,
    insight_signature: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "row_id": f"phase11-{index}-{family}",
        "trace_id": f"trace-phase11-{index}",
        "emotion_log_id": f"emotion-phase11-{index}",
        "product_readfeel_family": family,
        "fixture_family": family,
        "coverage_group": family,
        "observation_status": "passed",
        "backend_public_passed": True,
        "public_passed": True,
        "display_confirmed": True,
        "comment_text_present": True,
        "eligible_count": 1,
        "passed_display_count": 1,
        "candidate_generated_count": 1,
        "binding_count": 2,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "reason_required_count": 1,
        "reason_covered_count": 1,
        "surface_signature_id": surface_signature or f"surface-sig-{index}-{family}",
        "surface_signature_key": surface_signature or f"surface-sig-{index}-{family}",
        "surface_signature_family_key": surface_signature or f"surface-sig-{index}-{family}",
        "surface_major_reasons": [],
        "grammar_warning_codes": [],
        "template_major_count": 0,
        "safety_major_count": 0,
        "mirror_only_detected": False,
        "self_report_only_detected": False,
        "material_slot_count": 5,
        "evidence_slot_count": 5,
        "source_field_ids": ["memo", "memo_action", "selected_emotions"],
        "product_readfeel_v1_verdict": "PASS",
        "product_readfeel_v2_verdict": "STRUCTURE_INSIGHT_READY",
        "ratings": _ratings(),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    if family in _INSIGHT_FAMILIES:
        event.update(
            {
                "phase10_structure_insight_surface_connected": True,
                "structure_insight_surface_applied": True,
                "structure_insight_surface_family": family,
                "structure_insight_surface_signature_key": insight_signature
                or f"insight-sig-{index}-{family}",
                "structure_insight_surface_overclaim_count": 0,
                "structure_insight_surface_diagnosis_count": 0,
                "structure_insight_surface_personality_claim_count": 0,
            }
        )
    return event


def _events(*, same_family_surface: bool = False, same_insight_surface: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, family in enumerate(PRODUCT_READFEEL_REQUIRED_FAMILIES, start=1):
        surface_signature = "shared-family-cross-surface" if same_family_surface and index in {1, 2} else None
        insight_signature = "shared-insight-syntax" if same_insight_surface and family in _INSIGHT_FAMILIES else None
        rows.append(_event(family, index, surface_signature=surface_signature, insight_signature=insight_signature))
    return rows


def _reviews(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "review_id": f"review-{event['row_id']}",
            "candidate_id": event["row_id"],
            "row_id": event["row_id"],
            "product_readfeel_family": event["product_readfeel_family"],
            "fixture_family": event["fixture_family"],
            "ratings": _ratings(),
            "raw_input_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
        for event in events
    ]


def _scorecard_ready() -> dict[str, Any]:
    return {
        "v1_product_pass_ready": True,
        "v2_structure_insight_ready": True,
        "blind_qa_ready": True,
        "release_blockers": [],
    }


def _assert_meta_only(payload: Any) -> None:
    dumped = json.dumps(payload, ensure_ascii=False)
    assert "raw input body" not in dumped
    assert "comment display body" not in dumped
    if isinstance(payload, dict):
        for forbidden in (
            "raw_input",
            "raw_text",
            "input",
            "memo",
            "memo_action",
            "comment_text",
            "surface_text",
            "body",
            "text",
        ):
            assert forbidden not in payload
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        assert payload.get("public_response_key_added") is not True
        assert payload.get("comment_text_generated") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def test_phase11_direct_gate_builds_v1_product_pass_candidate_without_release_application() -> None:
    report = build_product_readfeel_long_run_product_gate(
        events=_events(),
        product_readfeel_scorecard=_scorecard_ready(),
        runtime_long_run_summary={"runtime_surface_blind_qa_long_run_ready": True},
        blind_qa_aggregate={"blind_qa_ready": True},
    )
    fields = normalize_product_readfeel_long_run_product_gate_to_scorecard_fields(report)

    assert report["version"] == PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION
    assert report["step"] == PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP
    assert fields["product_readfeel_phase11_v1_product_pass_candidate"] is True
    assert fields["product_readfeel_phase11_consecutive_5_v1_product_pass_ready"] is True
    assert fields["product_readfeel_phase11_consecutive_10_v1_product_pass_ready"] is True
    assert fields["product_readfeel_phase11_family_cross_surface_repetition_detected"] is False
    assert fields["product_readfeel_phase11_product_gate_ready"] is False
    assert fields["product_readfeel_phase11_public_release_applied"] is False
    _assert_meta_only(report)
    _assert_meta_only(fields)


def test_phase11_keeps_structure_insight_v2_separate_from_v1_product_pass() -> None:
    report = build_product_readfeel_long_run_product_gate(
        events=_events(same_insight_surface=True),
        product_readfeel_scorecard=_scorecard_ready(),
        runtime_long_run_summary={"runtime_surface_blind_qa_long_run_ready": True},
        blind_qa_aggregate={"blind_qa_ready": True},
    )
    fields = normalize_product_readfeel_long_run_product_gate_to_scorecard_fields(report)

    assert fields["product_readfeel_phase11_v1_product_pass_candidate"] is True
    assert fields["product_readfeel_phase11_insight_surface_same_syntax_repetition_detected"] is True
    assert fields["product_readfeel_phase11_v2_structure_insight_ready"] is False
    assert "insight_surface_same_syntax_repetition_detected" in fields[
        "product_readfeel_phase11_v2_structure_insight_ready_blockers"
    ]
    assert fields["product_readfeel_phase11_product_gate_ready"] is False
    assert fields["product_readfeel_phase11_public_release_applied"] is False


def test_phase11_family_cross_surface_repetition_blocks_v1_candidate() -> None:
    report = build_product_readfeel_long_run_product_gate(
        events=_events(same_family_surface=True),
        product_readfeel_scorecard=_scorecard_ready(),
        runtime_long_run_summary={"runtime_surface_blind_qa_long_run_ready": True},
        blind_qa_aggregate={"blind_qa_ready": True},
    )
    fields = normalize_product_readfeel_long_run_product_gate_to_scorecard_fields(report)

    assert fields["product_readfeel_phase11_family_cross_surface_repetition_detected"] is True
    assert fields["product_readfeel_phase11_v1_product_pass_candidate"] is False
    assert "family_cross_surface_repetition_detected" in fields[
        "product_readfeel_phase11_v1_product_pass_blockers"
    ]
    assert fields["product_readfeel_phase11_product_gate_ready"] is False
    assert fields["product_readfeel_phase11_public_release_applied"] is False


def test_phase11_runtime_and_complete_scorecard_expose_gate_material_but_do_not_release() -> None:
    events = _events()
    reviews = _reviews(events)
    summary = build_runtime_surface_blind_qa_long_run_summary(
        events=events,
        blind_qa_reviews=reviews,
        run_id="phase11-runtime-connect",
    )
    runtime_fields = normalize_runtime_surface_blind_qa_long_run_to_scorecard_fields(summary)

    assert runtime_fields["phase11_product_readfeel_long_run_product_gate_ready"] is True
    assert runtime_fields["product_readfeel_phase11_consecutive_10_v1_product_pass_ready"] is True
    assert runtime_fields["product_readfeel_phase11_product_gate_ready"] is False
    assert runtime_fields["product_readfeel_phase11_public_release_applied"] is False

    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=events,
        blind_qa_reviews=reviews,
    )
    assert scorecard["phase11_product_readfeel_long_run_product_gate_ready"] is True
    assert scorecard["product_readfeel_phase11_consecutive_10_v1_product_pass_ready"] is True
    assert scorecard["product_readfeel_phase11_release_judgment_deferred"] is True
    assert scorecard["product_readfeel_phase11_product_gate_ready"] is False
    assert scorecard["product_readfeel_phase11_public_release_applied"] is False
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False


def test_phase11_meta_only_rejects_text_keys_and_gate_relaxation() -> None:
    with pytest.raises(ProductReadFeelLongRunProductGateMetaOnlyError):
        assert_product_readfeel_long_run_product_gate_meta_only({"comment_text": "comment display body"})
    with pytest.raises(ProductReadFeelLongRunProductGateMetaOnlyError):
        assert_product_readfeel_long_run_product_gate_meta_only({"gate_relaxed": True})
