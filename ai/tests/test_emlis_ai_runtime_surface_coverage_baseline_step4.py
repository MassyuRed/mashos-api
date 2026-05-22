from __future__ import annotations

import json

from emlis_ai_complete_product_quality_measurement_connection import (
    build_complete_product_quality_measurement_connection,
    normalize_observation_row_to_product_quality_event,
)
from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_complete_scorecard_service import normalize_complete_scorecard_event
from emlis_ai_complete_surface_quality_signature import build_surface_quality_signature
from emlis_ai_coverage_matrix_service import build_runtime_surface_coverage_matrix_contract
from emlis_ai_runtime_surface_coverage_baseline import (
    RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION,
    RUNTIME_SURFACE_COVERAGE_GROUP_MISSING,
    RUNTIME_SURFACE_COVERAGE_GROUP_ORDER,
    build_runtime_surface_coverage_baseline,
    normalize_runtime_surface_coverage_group,
)

_TEMPLATE_LIKE_TEXT = (
    "Emlisです。\n"
    "体調を整えることが中心にあります。\n"
    "その中でも、お仕事を頑張って今後の準備をすることも見えています。\n"
    "その中でも、だいぶ先になることも重なっています。"
)
_NATURAL_TEXT = (
    "Emlisです。\n"
    "今は、自分の内側を少し整え直したい時間が前に出ています。\n"
    "急いで決めるよりも、いま残っている疲れを見落とさないことが大事そうです。\n"
    "その奥には、次へ進みたい気持ちも一緒に残っています。"
)


def _signature(text: str = _NATURAL_TEXT) -> dict[str, object]:
    return build_surface_quality_signature(comment_text=text)


def _row(*, group: str, trace_id: str, signature: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "trace_id": trace_id,
        "emotion_log_id": f"emotion-{trace_id}",
        "coverage_group": group,
        "backend_status": "passed",
        "backend_len": 120,
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
        "surface_quality_signature": signature or _signature(),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _green_review(group: str) -> dict[str, object]:
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


def test_step4_coverage_runtime_baseline_reports_all_seven_groups_and_surface_repeat() -> None:
    template_signature = _signature(_TEMPLATE_LIKE_TEXT)
    events = []
    for group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER:
        signature = template_signature if group == "short_daily" else _signature(_NATURAL_TEXT)
        events.append(normalize_observation_row_to_product_quality_event(_row(group=group, trace_id=f"step4-{group}-1", signature=signature)))
    events.append(normalize_observation_row_to_product_quality_event(_row(group="short_daily", trace_id="step4-short-repeat", signature=template_signature)))

    baseline = build_runtime_surface_coverage_baseline(events=events)
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=events,
        blind_qa_reviews=[_green_review(group) for group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER],
    )

    assert baseline["version"] == RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION
    assert baseline["step4_coverage_runtime_baseline_ready"] is True
    assert tuple(baseline["required_coverage_groups"]) == tuple(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER)
    assert baseline["missing_coverage_groups"] == []
    assert baseline["coverage_group_missing_count"] == 0
    assert set(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER).issubset(set(baseline["by_coverage_group"]))
    assert baseline["by_coverage_group"]["short_daily"]["surface_signature_repeat_count"] >= 1
    assert "coverage_surface_signature_repeat_detected" in baseline["release_blockers"]

    assert scorecard["step4_coverage_runtime_baseline_ready"] is True
    assert scorecard["coverage_runtime_baseline"]["missing_coverage_groups"] == []
    assert scorecard["coverage_runtime_baseline"]["by_coverage_group"]["short_daily"]["surface_signature_repeat_count"] >= 1
    assert "coverage_surface_signature_repeat_detected" in scorecard["release_blockers"]

    dumped = json.dumps(scorecard, ensure_ascii=False)
    assert "体調を整える" not in dumped
    assert _TEMPLATE_LIKE_TEXT not in dumped
    assert '"comment_text"' not in dumped


def test_step4_coverage_group_missing_stays_separate_and_blocks_product_gate() -> None:
    event = normalize_observation_row_to_product_quality_event(_row(group="", trace_id="step4-missing", signature=_signature()))
    baseline = build_runtime_surface_coverage_baseline(events=[event])
    scorecard = build_complete_product_quality_scorecard(scorecard_events=[event], blind_qa_reviews=[])

    assert normalize_runtime_surface_coverage_group("", relation_types=[]) == RUNTIME_SURFACE_COVERAGE_GROUP_MISSING
    assert baseline["by_coverage_group"][RUNTIME_SURFACE_COVERAGE_GROUP_MISSING]["event_count"] == 1
    assert baseline["by_coverage_group"]["short_daily"]["event_count"] == 0
    assert baseline["coverage_group_missing_count"] == 1
    assert baseline["coverage_group_missing_blocker"] is True
    assert "coverage_group_missing" in baseline["release_blockers"]
    assert "coverage_group_missing" in scorecard["release_blockers"]


def test_step4_measurement_connection_carries_coverage_runtime_baseline_without_text_or_contract_changes() -> None:
    rows = [
        _row(group=group, trace_id=f"step4-report-{group}", signature=_signature())
        for group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER
    ]
    report = build_complete_product_quality_measurement_connection(
        rows=rows,
        blind_qa_reviews=[_green_review(group) for group in RUNTIME_SURFACE_COVERAGE_GROUP_ORDER],
        run_id="runtime-surface-step4",
    )

    assert report["coverage_runtime_baseline_version"] == RUNTIME_SURFACE_COVERAGE_BASELINE_VERSION
    assert report["step4_coverage_runtime_baseline_ready"] is True
    assert tuple(report["coverage_runtime_baseline"]["required_coverage_groups"]) == tuple(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER)
    assert report["coverage_runtime_baseline"]["missing_coverage_groups"] == []
    assert report["runtime_branching_uses_fixture_strings"] is False
    assert report["fixture_text_used_for_runtime_branching"] is False
    assert report["public_release_applied"] is False
    assert report["product_gate_public_release_applied"] is False
    assert report["api_route_changed"] is False
    assert report["db_physical_name_changed"] is False
    assert report["display_gate_relaxed"] is False

    dumped = json.dumps(report, ensure_ascii=False)
    assert "体調を整える" not in dumped
    assert '"comment_text"' not in dumped


def test_step4_coverage_matrix_contract_and_scorecard_normalizer_keep_missing_out_of_short_daily() -> None:
    contract = build_runtime_surface_coverage_matrix_contract()
    missing_event = normalize_complete_scorecard_event(
        {
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "complete_candidate_displayed": False,
            "eligible_count": 1,
            "observation_status": "rejected",
            "coverage_group": "",
            "relation_types": [],
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
        }
    )
    relation_event = normalize_complete_scorecard_event(
        {
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "complete_candidate_displayed": False,
            "eligible_count": 1,
            "observation_status": "rejected",
            "coverage_group": "",
            "relation_types": ["approach_avoidance"],
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
        }
    )

    assert tuple(contract["required_coverage_groups"]) == tuple(RUNTIME_SURFACE_COVERAGE_GROUP_ORDER)
    assert contract["coverage_group_missing_key"] == RUNTIME_SURFACE_COVERAGE_GROUP_MISSING
    assert contract["missing_group_falls_back_to_short_daily"] is False
    assert contract["runtime_branching_uses_fixture_strings"] is False
    assert missing_event["coverage_group"] == RUNTIME_SURFACE_COVERAGE_GROUP_MISSING
    assert relation_event["coverage_group"] == "desire_fear"
