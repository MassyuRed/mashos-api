from __future__ import annotations

import json
from types import SimpleNamespace

from emlis_ai_complete_composer_initial_meta import COMPLETE_COMPOSER_INITIAL_MODEL
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_GENERATION_METHOD
from emlis_ai_complete_reply_diagnostics_service import (
    RUNTIME_SURFACE_STEP8_DIAGNOSTICS_VERSION,
    build_complete_reply_service_diagnostics,
    build_runtime_surface_step8_diagnostics_meta,
)
from emlis_ai_complete_scorecard_service import (
    aggregate_complete_scorecard_events,
    normalize_complete_scorecard_event,
)
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report


BAD_SURFACE = """Emlisです。
今までことが中心にあります。
その中でも、大丈夫ことも見えています。
その中でも、創作をする時にリアルさを求めることも重なっています。"""


def _complete_candidate() -> dict:
    return {
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
        "coverage_scope": "current_input_core",
        "used_evidence_span_ids": ["ev-1"],
        "used_relation_ids": ["rel-1"],
        "composer_meta": {
            "complete_composer_client_added": True,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "coverage_scope": "current_input_core",
            "coverage_group": "short_daily",
            "profile_key": "current_input_core",
            "shallow_observation_path": True,
            "used_phrase_unit_ids": ["ph-1"],
            "relation_types": ["coexistence"],
            "shallow_realizer_version": "shallow_surface_realizer.v2",
            "shallow_v2_used": True,
            "shallow_surface_realizer_v2": {
                "version": "emlis.shallow_surface_realizer_plan.v2",
                "realizer_version": "shallow_surface_realizer.v2",
                "eligible": True,
                "sentence_roles": ["receive_line", "state_arrangement_line"],
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            "low_information_specificity_plan": {
                "version": "emlis.low_information_specificity_plan.v1",
                "safe_anchor_count": 1,
                "uses_safe_anchor": True,
                "safe_anchor_role": "question",
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            "low_information_specificity_used": True,
            "malformed_phrase_unit_blocked_count": 2,
            "grounding_input": {"binding_count": 1},
        },
    }


def _surface_gate_report() -> dict:
    return build_runtime_surface_pre_return_gate_report(
        comment_text=BAD_SURFACE,
        composer_meta={
            "profile_key": "current_input_core",
            "coverage_scope": "current_input_core",
            "shallow_observation_path": True,
        },
        rerender_allowed=True,
        rerender_attempted=True,
    )


def test_step8_builds_meta_only_runtime_surface_diagnostics() -> None:
    meta = build_runtime_surface_step8_diagnostics_meta(
        runtime_meta=_complete_candidate()["composer_meta"],
        gate_trace={"runtime_surface_pre_return_gate": _surface_gate_report()},
        diagnostic_summary={"trace_id": "trace-step8"},
    )

    assert meta["version"] == RUNTIME_SURFACE_STEP8_DIAGNOSTICS_VERSION
    assert meta["runtime_surface_pre_return_gate_evaluated"] is True
    assert meta["runtime_surface_pre_return_gate_passed"] is False
    assert meta["runtime_surface_pre_return_gate_action"] in {"block", "fail_closed", "rerender_shallow_v2"}
    assert "surface_template_major" in meta["runtime_surface_pre_return_gate_rejection_reasons"]
    assert meta["surface_template_major_blocked"] is True
    assert meta["malformed_phrase_unit_blocked_count"] >= 2
    assert meta["shallow_realizer_version"] == "shallow_surface_realizer.v2"
    assert meta["shallow_v2_used"] is True
    assert meta["low_information_specificity_used"] is True
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    dumped = json.dumps(meta, ensure_ascii=False)
    assert BAD_SURFACE not in dumped
    assert "comment_text_body_included" in dumped


def test_step8_reply_diagnostics_exposes_surface_meta_without_text_payload() -> None:
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_complete_candidate(),
        display_decision=SimpleNamespace(observation_status="rejected", rejection_reasons=["runtime_surface_pre_return_gate_failed"], comment_text=""),
        gate_trace={"runtime_surface_pre_return_gate": _surface_gate_report()},
        resolution_meta={"requested_composer": "complete_initial", "source": "complete_composer_registry"},
        diagnostic_summary={"trace_id": "trace-step8", "emotion_log_id": "emotion-step8", "coverage_group": "short_daily"},
    )

    meta = diagnostics["runtime_surface_step8_diagnostics"]
    scorecard_event = diagnostics["scorecard_event"]
    assert meta["runtime_surface_pre_return_gate_evaluated"] is True
    assert meta["runtime_surface_pre_return_gate_passed"] is False
    assert diagnostics["surface_template_major_blocked"] is True
    assert scorecard_event["surface_template_major_blocked"] is True
    assert diagnostics["malformed_phrase_unit_blocked_count"] >= 2
    assert scorecard_event["shallow_v2_used"] is True
    assert scorecard_event["low_information_specificity_used"] is True
    dumped = json.dumps(diagnostics, ensure_ascii=False)
    assert BAD_SURFACE not in dumped
    assert BAD_SURFACE not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped


def test_step8_scorecard_normalizes_and_aggregates_runtime_surface_fields() -> None:
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_complete_candidate(),
        display_decision=SimpleNamespace(observation_status="rejected", rejection_reasons=["runtime_surface_pre_return_gate_failed"], comment_text=""),
        gate_trace={"runtime_surface_pre_return_gate": _surface_gate_report()},
        diagnostic_summary={"trace_id": "trace-step8", "emotion_log_id": "emotion-step8", "coverage_group": "short_daily"},
    )

    normalized = normalize_complete_scorecard_event(diagnostics["scorecard_event"])
    assert normalized["runtime_surface_pre_return_gate_evaluated"] is True
    assert normalized["runtime_surface_pre_return_gate_failed_count"] == 1
    assert normalized["surface_template_major_blocked_count"] == 1
    assert normalized["malformed_phrase_unit_blocked_count"] >= 2
    assert normalized["shallow_v2_used_count"] == 1
    assert normalized["low_information_specificity_used_count"] == 1
    assert normalized["raw_input_included"] is False
    assert normalized["comment_text_body_included"] is False

    aggregate = aggregate_complete_scorecard_events([diagnostics["scorecard_event"]])
    assert aggregate["runtime_surface_pre_return_gate_failed_count"] == 1
    assert aggregate["surface_template_major_blocked_count"] == 1
    assert aggregate["malformed_phrase_unit_blocked_count"] >= 2
    assert aggregate["shallow_v2_used_count"] == 1
    assert aggregate["low_information_specificity_used_count"] == 1
    assert "runtime_surface_gate_failed_detected" in aggregate["release_blockers"]
    assert "surface_template_major_blocked_detected" in aggregate["release_blockers"]
    assert aggregate["raw_input_included"] is False
    assert aggregate["comment_text_included"] is False
