# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_complete_product_quality_measurement_connection import (
    build_complete_product_quality_measurement_connection,
    normalize_observation_row_to_product_quality_event,
)
from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_complete_surface_realizer import CompleteSurfaceRealizationV2
from emlis_ai_complete_self_repair_service import run_complete_self_repair_loop
from emlis_ai_runtime_surface_self_repair import (
    REPAIR_REASON_MALFORMED_NOMINALIZATION,
    REPAIR_REASON_TEMPLATE_LIKE,
    RUNTIME_SURFACE_SELF_REPAIR_VERSION,
    assert_runtime_surface_aware_self_repair_meta_only,
    build_runtime_surface_self_repair_measurement_summary,
    build_surface_aware_self_repair_request,
    derive_surface_aware_repair_reasons,
    normalize_runtime_surface_self_repair_to_scorecard_event,
)


def _realization_with_optional_malformed_line() -> CompleteSurfaceRealizationV2:
    return CompleteSurfaceRealizationV2(
        plan_id="step10_surface_repair_plan",
        coverage_group="relationship",
        surface_lines=(
            {
                "sentence_id": "s1",
                "line_role": "opening",
                "relation_type": "center",
                "surface_text": "距離感の揺れが中心にあります。",
                "phrase_unit_ids": ("p1",),
                "evidence_span_ids": ("e1",),
                "role_phrase_key": "relationship_distance",
                "predicate_key": "center",
                "ending_key": "tail_a",
                "source_sentence_plan_line": {"sentence_id": "s1", "must_include_roles": ("center",)},
            },
            {
                "sentence_id": "s2",
                "line_role": "support",
                "relation_type": "coexistence",
                "surface_text": "私から離れことも見えています。",
                "phrase_unit_ids": ("p2",),
                "evidence_span_ids": ("e2",),
                "role_phrase_key": "self_side_response",
                "predicate_key": "visible",
                "ending_key": "tail_a",
                "source_sentence_plan_line": {"sentence_id": "s2", "optional_roles": ("support",)},
            },
            {
                "sentence_id": "s3",
                "line_role": "relation",
                "relation_type": "coexistence",
                "surface_text": "近づきたい気持ちと止まる気持ちが同じ線上に残っています。",
                "phrase_unit_ids": ("p3",),
                "evidence_span_ids": ("e3",),
                "role_phrase_key": "relation_pair",
                "predicate_key": "overlap",
                "ending_key": "tail_b",
                "source_sentence_plan_line": {"sentence_id": "s3", "must_include_roles": ("relation",)},
            },
        ),
    )


def test_step10_surface_signature_reasons_become_bounded_self_repair_reasons() -> None:
    signature = {
        "surface_signature_id": "sig-step10",
        "template_major": True,
        "same_connector_run_max": 2,
        "malformed_nominalization_risk": True,
        "grammar_warning_codes": ["malformed_nominalization", "stem_koto_hanareru"],
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    reasons = derive_surface_aware_repair_reasons(surface_quality_signature=signature)

    assert REPAIR_REASON_TEMPLATE_LIKE in reasons
    assert REPAIR_REASON_MALFORMED_NOMINALIZATION in reasons

    request = build_surface_aware_self_repair_request(surface_quality_signature=signature)
    assert request["version"] == RUNTIME_SURFACE_SELF_REPAIR_VERSION
    assert request["repair_allowed"] is True
    assert request["repair_attempt_limit"] == 2
    assert request["must_keep_evidence_preserved"] is True
    assert request["meaning_added"] is False
    assert request["comment_text_body_included"] is False
    assert_runtime_surface_aware_self_repair_meta_only(request)
    dumped = json.dumps(request, ensure_ascii=False)
    assert "私から離れこと" not in dumped
    assert "これは出してはいけない本文" not in dumped


def test_step10_runtime_surface_self_repair_runs_meta_only_and_drops_optional_malformed_line() -> None:
    signature = {
        "surface_signature_id": "sig-step10-malformed",
        "malformed_nominalization_risk": True,
        "grammar_warning_codes": ["malformed_nominalization"],
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    result = run_complete_self_repair_loop(
        surface_realization=_realization_with_optional_malformed_line(),
        meta={"surface_quality_signature": signature},
    )
    report = normalize_runtime_surface_self_repair_to_scorecard_event(
        {
            "surface_aware_repair_reasons": list(result.gate_reasons),
            "repair_attempt_count": len(result.repair_trace),
            "repaired": result.repaired,
            "surface_aware_repair_fail_closed": result.aborted,
            "meaning_added": False,
            "new_meaning_added": False,
            "comment_text_body_included": False,
        }
    )

    assert result.repaired is True
    assert report["step10_surface_aware_self_repair_ready"] is True
    assert report["surface_aware_self_repair_attempted"] is True
    assert report["surface_aware_self_repair_success"] is True
    assert report["runtime_surface_self_repair_attempt_count"] == 1
    assert report["runtime_surface_self_repair_success_count"] == 1
    assert report["meaning_added"] is False
    assert report["new_meaning_added"] is False
    assert report["gate_relaxed"] is False
    assert report["comment_text_body_included"] is False
    assert_runtime_surface_aware_self_repair_meta_only(report)
    dumped = json.dumps(report, ensure_ascii=False)
    assert "私から離れこと" not in dumped
    assert "surface_text" not in dumped
    assert "realized_text" not in dumped


def test_step10_max_attempts_fail_closed_without_public_contract_change() -> None:
    signature = {
        "surface_signature_id": "sig-step10-fail-closed",
        "malformed_nominalization_risk": True,
        "grammar_warning_codes": ["malformed_nominalization"],
    }
    result = run_complete_self_repair_loop(
        surface_realization=_realization_with_optional_malformed_line(),
        meta={"surface_quality_signature": signature},
        max_attempts=0,
    )
    report = normalize_runtime_surface_self_repair_to_scorecard_event(
        {
            "surface_aware_repair_reasons": list(result.gate_reasons),
            "repair_attempt_count": len(result.repair_trace),
            "repaired": result.repaired,
            "surface_aware_repair_fail_closed": result.aborted,
            "aborted": result.aborted,
            "meaning_added": False,
            "new_meaning_added": False,
        }
    )

    assert result.aborted is True
    assert report["surface_aware_self_repair_aborted"] is True
    assert report["public_release_applied"] is False
    assert report["product_gate_achieved"] is False
    assert report["response_shape_changed"] is False
    assert report["api_route_changed"] is False
    assert report["db_physical_name_changed"] is False
    assert report["rn_visible_contract_changed"] is False


def test_step10_scorecard_and_measurement_connection_receive_surface_self_repair_metrics() -> None:
    signature = {
        "surface_signature_id": "sig-step10-scorecard",
        "template_major": True,
        "malformed_nominalization_risk": True,
        "grammar_warning_codes": ["malformed_nominalization"],
    }
    result = run_complete_self_repair_loop(
        surface_realization=_realization_with_optional_malformed_line(),
        meta={"surface_quality_signature": signature},
    )
    report = {
        "surface_aware_repair_reasons": list(result.gate_reasons),
        "repair_attempt_count": len(result.repair_trace),
        "repaired": result.repaired,
        "surface_aware_repair_fail_closed": result.aborted,
        "meaning_added": False,
        "new_meaning_added": False,
        "comment_text_body_included": False,
    }
    event_fields = normalize_runtime_surface_self_repair_to_scorecard_event(report)
    assert event_fields["step10_surface_aware_self_repair_connected"] is True
    assert event_fields["runtime_surface_self_repair_attempt_count"] >= 1
    assert event_fields["runtime_surface_self_repair_success_count"] >= 1

    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            {
                "row_id": "step10-row",
                "coverage_group": "relationship",
                "observation_status": "passed",
                "eligible_count": 1,
                "candidate_generated_count": 1,
                "passed_display_count": 1,
                "binding_supported_sentence_count": 3,
                "expected_binding_count": 3,
                **event_fields,
            }
        ],
        blind_qa_reviews=[],
    )
    assert scorecard["step10_surface_aware_self_repair_connected"] is True
    assert scorecard["runtime_surface_self_repair_attempt_count"] >= 1
    assert scorecard["runtime_surface_self_repair_success_count"] >= 1

    summary = build_runtime_surface_self_repair_measurement_summary(events=[event_fields])
    assert summary["runtime_surface_self_repair_attempt_count"] >= 1
    assert summary["runtime_surface_self_repair_success_count"] >= 1

    row_event = normalize_observation_row_to_product_quality_event(
        {
            "row_id": "step10-measurement-row",
            "trace_id": "trace-step10",
            "emotion_log_id": "emotion-step10",
            "coverage_group": "relationship",
            "observation_status": "passed",
            "backend_observation_status": "passed",
            "candidate_generated": True,
            "display_confirmed": True,
            "backend_comment_text_present": True,
            "backend_comment_text_length": 120,
            "surface_aware_self_repair_report": report,
            "surface_quality_signature": {
                "surface_signature_id": "sig-step10-measurement",
                "surface_quality_signature_ready": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        }
    )
    assert row_event["step10_surface_aware_self_repair_connected"] is True
    assert row_event["runtime_surface_self_repair_attempt_count"] == 1
    assert row_event["repair_attempt_count"] == 1

    connection = build_complete_product_quality_measurement_connection(rows=[row_event])
    assert connection["step10_surface_aware_self_repair_connected"] is True
    assert connection["runtime_surface_self_repair_attempt_count"] >= 1
