from __future__ import annotations

import json

import pytest

from emlis_ai_complete_product_quality_measurement_connection import (
    build_complete_product_quality_measurement_connection,
    dump_complete_product_quality_measurement_connection,
)
from emlis_ai_runtime_surface_exit_gate import (
    RUNTIME_SURFACE_EXIT_GATE_STEP,
    RUNTIME_SURFACE_EXIT_GATE_VERSION,
    assert_runtime_surface_exit_gate_meta_only,
    build_runtime_surface_exit_gate,
    dump_runtime_surface_exit_gate,
)
from emlis_ai_runtime_surface_source_lock import build_runtime_surface_source_lock

_REQUIRED_GROUPS = (
    "short_daily",
    "long_meaning_arc",
    "conflict",
    "recovery",
    "pressure",
    "desire_fear",
    "relationship",
)


def _source_lock(index: int, coverage_group: str) -> dict[str, object]:
    return build_runtime_surface_source_lock(
        trace_id=f"trace-step12-{index}",
        emotion_log_id=f"emotion-step12-{index}",
        observation_status="passed",
        backend_comment_text_length=120,
        display_confirmed=True,
        coverage_group=coverage_group,
        resolution_meta={"requested_composer": "complete_initial", "complete_initial_client_used": True},
        runtime_meta={
            "composer_source": "complete_initial",
            "composer_model": "cocolon.test.complete_initial",
            "sentence_plan_version": "sentence_plan.step12.test",
            "surface_realizer_version": "surface_realizer.step12.test",
            "tone_policy_version": "tone_policy.step12.test",
            "self_repair_version": "self_repair.step12.test",
        },
    )


def _row(index: int, coverage_group: str = "short_daily", signature: str | None = None) -> dict[str, object]:
    signature = signature or f"signature-{coverage_group}-{index}"
    return {
        "row_id": f"row-step12-{index}",
        "run_id": "run-step12",
        "trace_id": f"trace-step12-{index}",
        "emotion_log_id": f"emotion-step12-{index}",
        "coverage_group": coverage_group,
        "measurement_classification": "passed_displayed",
        "classification": "passed_displayed",
        "observation_status": "passed",
        "backend_status": "passed",
        "backend_len": 120,
        "backend_comment_text_present": True,
        "backend_public_passed": True,
        "frontend_joined": True,
        "frontend_join_status": "joined",
        "modal_opened": True,
        "public_passed": True,
        "display_confirmed": True,
        "diagnostic_capture_status": "captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured",
        "passed_display_count": 1,
        "eligible_count": 1,
        "candidate_generated_count": 1,
        "candidate_generated": True,
        "binding_count": 2,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "surface_signature_id": f"sig:{signature}",
        "surface_signature_family_key": signature,
        "surface_major_reasons": [],
        "grammar_warning_codes": [],
        "runtime_surface_source_lock": _source_lock(index, coverage_group),
        "step10_surface_aware_self_repair_connected": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _review(index: int, coverage_group: str = "short_daily") -> dict[str, object]:
    return {
        "review_id": f"review-step12-{index}",
        "candidate_id": f"row-step12-{index}",
        "coverage_group": coverage_group,
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
        "raw_input": "this must be stripped before Step12",
        "comment_text": "this public observation body must be stripped before Step12",
    }


def test_step12_exit_gate_connects_measurement_handoff_without_product_gate_release() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_row(1, "short_daily", "single-sig")],
        blind_qa_reviews=[_review(1, "short_daily")],
        run_id="run-step12-single",
    )
    summary = report["runtime_surface_quality_exit_gate"]

    assert report["runtime_surface_quality_latest_step"] == RUNTIME_SURFACE_EXIT_GATE_STEP
    assert report["runtime_surface_quality_exit_gate_step"] == RUNTIME_SURFACE_EXIT_GATE_STEP
    assert summary["version"] == RUNTIME_SURFACE_EXIT_GATE_VERSION
    assert summary["step"] == RUNTIME_SURFACE_EXIT_GATE_STEP
    assert summary["runtime_surface_quality_exit_gate_ready"] is True
    assert report["runtime_surface_quality_exit_gate_completed"] is True
    assert report["step12_exit_gate_completed"] is True
    assert summary["handoff_only"] is True
    assert summary["product_gate_achieved"] is False
    assert summary["product_gate_public_release_applied"] is False
    assert report["product_gate_achieved"] is False
    assert report["public_release_applied"] is False
    assert report["runtime_surface_quality_release_judgment"]["release_allowed"] is False
    assert "coverage_group_count_below_required" in summary["coverage_gaps"]
    assert summary["next_branch"]["target_layer"]
    assert summary["public_contract_unchanged"] is True
    assert summary["product_release_closed"] is True
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False

    dumped = json.loads(dump_complete_product_quality_measurement_connection(report))
    assert dumped["runtime_surface_quality_exit_gate"]["product_gate_achieved"] is False
    assert dumped["runtime_surface_quality_exit_gate"]["public_release_applied"] is False
    assert "this public observation body" not in json.dumps(dumped, ensure_ascii=False)
    assert "comment_text" not in dumped["runtime_surface_quality_exit_gate"]


def test_step12_keeps_product_gate_candidate_as_internal_handoff_only() -> None:
    rows = [_row(index, group, f"signature-{index}") for index, group in enumerate(_REQUIRED_GROUPS, start=1)]
    reviews = [_review(index, group) for index, group in enumerate(_REQUIRED_GROUPS, start=1)]

    report = build_complete_product_quality_measurement_connection(
        rows=rows,
        blind_qa_reviews=reviews,
        run_id="run-step12-product-candidate",
    )
    summary = report["runtime_surface_quality_exit_gate"]

    assert report["coverage_group_count"] == len(_REQUIRED_GROUPS)
    assert report["missing_coverage_groups"] == []
    assert report["step11_blind_qa_long_run_ready"] is True
    assert report["release_ladder"]["product_gate_candidate_ready"] is True
    assert summary["product_gate_candidate_ready_from_release_ladder"] is True
    assert summary["product_gate_candidate_ready_but_public_release_not_applied"] is True
    assert summary["release_blockers"] == []
    assert summary["qa_gaps"] == []
    assert summary["coverage_gaps"] == []
    assert summary["runtime_surface_quality_exit_gate_blockers"] == []
    assert report["runtime_surface_quality_handoff_blockers"] == []
    assert report["product_gate_ready"] is False
    assert report["product_gate_reached"] is False
    assert report["product_gate_achieved"] is False
    assert report["product_gate_public_release_applied"] is False
    assert report["public_release_applied"] is False
    assert report["runtime_surface_quality_release_judgment"]["release_allowed"] is False


def test_step12_exit_gate_meta_only_rejects_text_payload_and_release_side_effects() -> None:
    with pytest.raises(ValueError):
        assert_runtime_surface_exit_gate_meta_only({"comment_text": "must not be persisted"})
    with pytest.raises(ValueError):
        assert_runtime_surface_exit_gate_meta_only({"runtime_surface_exit_gate_applies_public_release": True})
    with pytest.raises(ValueError):
        build_runtime_surface_exit_gate({"public_release_applied": True})

    safe = build_runtime_surface_exit_gate({
        "scorecard_event_connection_ready": True,
        "step3_scorecard_surface_metrics_connected": True,
        "coverage_runtime_baseline_ready": True,
        "step5_runtime_surface_quality_branch_resolver_ready": True,
        "runtime_surface_quality_branch": {
            "runtime_surface_quality_branch_resolver_ready": True,
            "target_layer": "blind_qa_long_run",
        },
        "step6_runtime_surface_complete_activation_branch_ready": True,
        "runtime_surface_complete_activation_branch": {
            "runtime_surface_complete_activation_branch_ready": True,
            "activation_status": "not_required_complete_runtime_already_measurable_or_next_branch_not_runtime",
        },
        "step10_surface_aware_self_repair_connected": True,
        "release_ladder_connected": True,
        "release_ladder": {"release_ladder_connected": True, "product_gate_candidate_ready": True},
        "runtime_surface_blind_qa_long_run_summary": {
            "version": "emlis.runtime_surface_blind_qa_long_run.v1",
            "step11_blind_qa_long_run_ready": True,
        },
        "raw_input_included": False,
        "comment_text_body_included": False,
    })
    dumped = dump_runtime_surface_exit_gate(safe)
    assert safe["runtime_surface_quality_exit_gate_ready"] is True
    assert safe["product_gate_candidate_ready_from_release_ladder"] is True
    assert safe["product_gate_achieved"] is False
    assert "must not be persisted" not in dumped
