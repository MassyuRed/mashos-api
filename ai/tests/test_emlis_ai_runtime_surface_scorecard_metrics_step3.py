from __future__ import annotations

import json

from emlis_ai_complete_product_quality_measurement_connection import (
    build_complete_product_quality_measurement_connection,
    normalize_observation_row_to_product_quality_event,
)
from emlis_ai_complete_product_quality_scorecard_service import (
    COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION,
    build_complete_product_quality_scorecard,
)
from emlis_ai_complete_release_ladder_service import build_complete_product_quality_release_ladder
from emlis_ai_complete_surface_quality_signature import build_surface_quality_signature

_TEMPLATE_LIKE_TEXT = (
    "Emlisです。\n"
    "体調を整えることが中心にあります。\n"
    "その中でも、お仕事頑張ってお金を貯めて今後一人暮らしをすることも見えています。\n"
    "その中でも、だいぶ先になることも重なっています。"
)
_GRAMMAR_RISK_TEXT = (
    "Emlisです。\n"
    "最近仲良くなった男の人にはなんて事ない日を大切にしてもらえることが中心にあります。\n"
    "その中でも、だからこそ私から離れことも見えています。\n"
    "同じ時間の中に重なっていることも残っています。"
)


def _row(signature: dict[str, object], *, trace_id: str, group: str = "short_daily") -> dict[str, object]:
    return {
        "trace_id": trace_id,
        "emotion_log_id": f"emotion-{trace_id}",
        "coverage_group": group,
        "backend_status": "passed",
        "backend_len": 140,
        "backend_comment_text_present": True,
        "backend_public_passed": True,
        "frontend_joined": True,
        "frontend_join_status": "joined",
        "modal_opened": True,
        "display_confirmed": True,
        "diagnostic_capture_status": "captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured",
        "classification": "passed_displayed",
        "measurement_classification": "passed_displayed",
        "candidate_generated": True,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "surface_quality_signature": signature,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _green_review(group: str = "short_daily") -> dict[str, object]:
    return {
        "review_id": f"green-{group}",
        "coverage_group": group,
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def test_step3_scorecard_event_accepts_surface_signature_meta_without_comment_body() -> None:
    signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)
    event = normalize_observation_row_to_product_quality_event(_row(signature, trace_id="surface-event-1"))

    assert event["surface_scorecard_metrics_version"] == COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION
    assert event["step3_scorecard_surface_metrics_event_ready"] is True
    assert event["surface_signature_id"] == signature["surface_signature_id"]
    assert event["surface_major_reasons"]
    assert "same_connector_run" in event["surface_major_reasons"]
    assert event["surface_template_major_count"] == 1
    assert event["template_major_count"] == 1
    assert event["read_feeling_score"] is None
    assert event["raw_input_included"] is False
    assert event["comment_text_body_included"] is False

    dumped = json.dumps(event, ensure_ascii=False)
    assert _TEMPLATE_LIKE_TEXT not in dumped
    assert "体調を整える" not in dumped
    assert '"comment_text"' not in dumped


def test_step3_scorecard_aggregates_surface_repeat_connector_and_grammar_rates() -> None:
    template_signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)
    grammar_signature = build_surface_quality_signature(comment_text=_GRAMMAR_RISK_TEXT)
    events = [
        normalize_observation_row_to_product_quality_event(_row(template_signature, trace_id="surface-score-1")),
        normalize_observation_row_to_product_quality_event(_row(template_signature, trace_id="surface-score-2")),
        normalize_observation_row_to_product_quality_event(_row(grammar_signature, trace_id="surface-score-3", group="relationship")),
    ]

    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=events,
        blind_qa_reviews=[_green_review("short_daily"), _green_review("relationship")],
    )

    assert scorecard["surface_metrics_ready"] is True
    assert scorecard["step3_scorecard_surface_metrics_connected"] is True
    assert scorecard["surface_metrics"]["version"] == COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION
    assert scorecard["surface_signature_count"] == 3
    assert scorecard["surface_signature_unique_count"] == 2
    assert scorecard["surface_signature_repeat_count"] == 1
    assert scorecard["surface_signature_repeat_rate"] > 0
    assert scorecard["connector_repetition_rate"] > 0
    assert scorecard["generic_opening_rate"] > 0
    assert scorecard["grammar_warning_rate"] > 0
    assert "stem_koto_hanareru" in scorecard["surface_grammar_warning_codes"]
    assert "template_major_detected" in scorecard["release_blockers"]
    assert "surface_template_major_detected" in scorecard["release_blockers"]
    assert scorecard["read_feeling_score"] == 1.0
    assert scorecard["machine_metrics"]["read_feeling_score"] is None
    assert scorecard["machine_metrics_used_for_read_feeling"] is False


def test_step3_without_blind_qa_keeps_read_feeling_unfilled_but_reports_surface_metrics() -> None:
    signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)
    event = normalize_observation_row_to_product_quality_event(_row(signature, trace_id="surface-no-qa"))
    event["read_feeling_score"] = 1.0

    scorecard = build_complete_product_quality_scorecard(scorecard_events=[event], blind_qa_reviews=[])

    assert scorecard["surface_metrics_ready"] is True
    assert scorecard["read_feeling_requires_blind_qa"] is True
    assert scorecard["read_feeling_score"] is None
    assert scorecard["read_feeling_source"] == "blind_qa_required_not_evaluated"
    assert scorecard["machine_metrics"]["read_feeling_score"] is None
    assert scorecard["read_feeling_auto_filled_from_machine_metrics"] is False
    assert "blind_qa_missing" in scorecard["release_blockers"]
    assert "template_major_detected" in scorecard["release_blockers"]


def test_step3_release_ladder_and_measurement_report_carry_surface_metrics_as_release_blockers() -> None:
    signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)
    event = normalize_observation_row_to_product_quality_event(_row(signature, trace_id="surface-ladder"))
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[event],
        blind_qa_reviews=[_green_review("short_daily")],
    )
    ladder = build_complete_product_quality_release_ladder(product_quality_scorecard=scorecard)

    assert ladder["metrics"]["surface_metrics_version"] == COMPLETE_PRODUCT_QUALITY_SURFACE_METRICS_VERSION
    assert ladder["metrics"]["surface_template_major_count"] == 1
    assert ladder["stop_conditions"]["surface_template_major_detected"] is True
    assert "template_major_detected" in ladder["release_blockers"]
    assert "surface_template_major_detected" in ladder["release_blockers"]
    assert ladder["product_gate_public_release_applied"] is False

    report = build_complete_product_quality_measurement_connection(
        rows=[_row(signature, trace_id="surface-report")],
        blind_qa_reviews=[_green_review("short_daily")],
        run_id="runtime-surface-step3",
    )

    assert report["surface_metrics_ready"] is True
    assert report["step3_scorecard_surface_metrics_connected"] is True
    assert report["surface_metrics"]["surface_template_major_count"] == 1
    assert "surface_template_major_detected" in report["release_blockers"]
    assert report["public_release_applied"] is False
    assert report["product_gate_public_release_applied"] is False
