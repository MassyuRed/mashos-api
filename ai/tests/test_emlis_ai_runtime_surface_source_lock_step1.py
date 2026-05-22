from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from emlis_ai_complete_composer_initial_meta import COMPLETE_COMPOSER_INITIAL_MODEL
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_GENERATION_METHOD
from emlis_ai_complete_product_quality_measurement_connection import (
    normalize_observation_row_to_product_quality_event,
)
from emlis_ai_complete_reply_diagnostics_service import build_complete_reply_service_diagnostics
from emlis_ai_runtime_surface_source_lock import (
    RUNTIME_SURFACE_SOURCE_LOCK_VERSION,
    RuntimeSurfaceSourceLockError,
    assert_runtime_surface_source_lock_meta_only,
    build_runtime_surface_source_lock,
    dump_runtime_surface_source_lock,
    resolve_runtime_composer_source,
)

_SECRET_COMMENT = "これはRuntime Surface Source Lockに出してはいけない観測本文です"


def _complete_candidate() -> dict:
    return {
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
        "coverage_scope": "short_daily",
        "used_evidence_span_ids": ["ev-1"],
        "used_relation_ids": ["rel-1"],
        "composer_meta": {
            "complete_composer_client_added": True,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "coverage_group": "short_daily",
            "sentence_plan": {"version": "sentence_plan.runtime.test"},
            "surface_realizer": {"version": "surface_realizer.runtime.test"},
            "tone_policy": {"version": "tone_policy.runtime.test"},
            "self_repair": {"version": "self_repair.runtime.test", "ready": True},
            "surface_signature": {"surface_signature_id": "sig-runtime-test"},
            "used_phrase_unit_ids": ["ph-1"],
            "relation_types": ["coexistence"],
            "grounding_input": {"binding_count": 1},
        },
    }


def test_step1_builds_complete_initial_source_lock_without_text_body() -> None:
    lock = build_runtime_surface_source_lock(
        trace_id="trace-step1",
        emotion_log_id="emotion-step1",
        observation_status="passed",
        comment_text=_SECRET_COMMENT,
        display_confirmed=True,
        coverage_group="short_daily",
        composer_candidate=_complete_candidate(),
        resolution_meta={"requested_composer": "complete_initial", "source": "complete_composer_registry"},
    )

    assert lock["schema_version"] == RUNTIME_SURFACE_SOURCE_LOCK_VERSION
    assert lock["runtime_surface_source_lock_ready"] is True
    assert lock["runtime_surface_source_locked"] is True
    assert lock["trace_id"] == "trace-step1"
    assert lock["emotion_log_id"] == "emotion-step1"
    assert lock["observation_status"] == "passed"
    assert lock["backend_comment_text_present"] is True
    assert lock["backend_comment_text_length"] == len(_SECRET_COMMENT)
    assert lock["display_confirmed"] is True
    assert lock["coverage_group"] == "short_daily"
    assert lock["composer_source"] == "complete_initial"
    assert lock["composer_resolved"] == "complete_initial"
    assert lock["complete_initial_client_used"] is True
    assert lock["sentence_plan_version"] == "sentence_plan.runtime.test"
    assert lock["surface_realizer_version"] == "surface_realizer.runtime.test"
    assert lock["tone_policy_version"] == "tone_policy.runtime.test"
    assert lock["self_repair_version"] == "self_repair.runtime.test"
    assert lock["surface_signature_id"] == "sig-runtime-test"
    assert lock["raw_text_included"] is False
    assert lock["comment_text_body_included"] is False

    dumped = dump_runtime_surface_source_lock(lock)
    assert _SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert json.loads(dumped)["comment_text_body_included"] is False


def test_step1_resolves_limited_and_a1_runtime_sources_separately() -> None:
    limited = resolve_runtime_composer_source(
        resolution_meta={
            "requested_composer": "limited",
            "source": "cocolon_limited_composer_registry",
            "composer_model": "cocolon_limited_composer.v1",
        },
        runtime_meta={"limited_reader_repair_applied": True},
    )
    assert limited["composer_source"] == "limited"
    assert limited["composer_resolved"] == "limited"
    assert limited["limited_reader_repair_applied"] is True
    assert limited["complete_initial_client_used"] is False

    a1 = resolve_runtime_composer_source(
        resolution_meta={
            "requested_composer": "a_plan_equivalent",
            "source": "cocolon_emlis_observation_composer_a1",
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        },
        runtime_meta={"generation_method": "a_plan_equivalent"},
    )
    assert a1["composer_source"] == "a1_equivalent"
    assert a1["composer_resolved"] == "a1_equivalent"
    assert a1["complete_initial_client_used"] is False


def test_step1_reply_diagnostics_carries_runtime_source_lock_without_changing_composer_source() -> None:
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_complete_candidate(),
        display_decision=SimpleNamespace(
            observation_status="passed",
            rejection_reasons=[],
            comment_text=_SECRET_COMMENT,
        ),
        gate_trace={"reader": {"passed": True}},
        resolution_meta={"requested_composer": "complete_initial", "source": "complete_composer_registry"},
        diagnostic_summary={"trace_id": "trace-diag", "emotion_log_id": "emotion-diag", "coverage_group": "short_daily"},
    )

    lock = diagnostics["runtime_surface_source_lock"]
    assert diagnostics["runtime_surface_source_lock_ready"] is True
    assert diagnostics["runtime_composer_source"] == "complete_initial"
    assert diagnostics["composer_source"] == "ai_generated"
    assert lock["composer_source"] == "complete_initial"
    assert diagnostics["scorecard_event"]["runtime_surface_source_lock"]["composer_source"] == "complete_initial"
    dumped = json.dumps(diagnostics, ensure_ascii=False)
    assert _SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped


def test_step1_measurement_connection_normalizes_row_with_runtime_source_lock() -> None:
    source_lock = build_runtime_surface_source_lock(
        trace_id="trace-row",
        emotion_log_id="emotion-row",
        observation_status="passed",
        backend_comment_text_length=42,
        display_confirmed=True,
        coverage_group="short_daily",
        resolution_meta={"requested_composer": "complete_initial", "complete_initial_client_used": True},
        runtime_meta={"surface_realizer_version": "surface.realizer.row"},
    )
    row = {
        "trace_id": "trace-row",
        "emotion_log_id": "emotion-row",
        "coverage_group": "short_daily",
        "backend_status": "passed",
        "backend_len": 42,
        "backend_comment_text_present": True,
        "backend_public_passed": True,
        "frontend_joined": True,
        "modal_opened": True,
        "display_confirmed": True,
        "classification": "passed_displayed",
        "measurement_classification": "passed_displayed",
        "diagnostic_capture_status": "captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured",
        "candidate_generated": True,
        "binding_supported_sentence_count": 1,
        "expected_binding_count": 1,
        "runtime_surface_source_lock": source_lock,
        "raw_input_included": False,
        "comment_text_included": False,
    }

    event = normalize_observation_row_to_product_quality_event(row)

    assert event["runtime_surface_source_lock_version"] == RUNTIME_SURFACE_SOURCE_LOCK_VERSION
    assert event["runtime_surface_source_lock_ready"] is True
    assert event["runtime_composer_source"] == "complete_initial"
    assert event["runtime_surface_source_complete_initial_client_used"] is True
    assert event["runtime_surface_source_lock"]["backend_comment_text_length"] == 42
    assert event["display_confirmed"] is True
    assert event["passed_display_count"] == 1
    dumped = json.dumps(event, ensure_ascii=False)
    assert _SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped


def test_step1_source_lock_rejects_text_payload_keys() -> None:
    lock = build_runtime_surface_source_lock(observation_status="passed", backend_comment_text_length=1)
    unsafe = dict(lock)
    unsafe["commentText"] = _SECRET_COMMENT
    with pytest.raises(RuntimeSurfaceSourceLockError):
        assert_runtime_surface_source_lock_meta_only(unsafe)


def test_step1_complete_initial_request_alone_does_not_mark_source_when_ap0_blocked() -> None:
    source = resolve_runtime_composer_source(
        resolution_meta={
            "requested_composer": "complete_initial",
            "connection_status": "blocked_ap0",
            "default_client_used": False,
            "complete_initial_client_used": False,
            "resolution_source": "cocolon_complete_composer_initial",
        },
        runtime_meta={},
        diagnostic_meta={"observation_status": "unavailable"},
    )

    assert source["composer_requested"] == "complete_initial"
    assert source["composer_source"] == "unavailable"
    assert source["composer_resolved"] == "unavailable"
    assert source["complete_initial_client_used"] is False

    lock = build_runtime_surface_source_lock(
        observation_status="unavailable",
        backend_comment_text_length=0,
        display_confirmed=False,
        resolution_meta={
            "requested_composer": "complete_initial",
            "connection_status": "blocked_ap0",
            "default_client_used": False,
            "complete_initial_client_used": False,
            "resolution_source": "cocolon_complete_composer_initial",
        },
    )

    assert lock["composer_requested"] == "complete_initial"
    assert lock["composer_source"] == "unavailable"
    assert lock["complete_initial_client_used"] is False
    assert lock["display_confirmed"] is False
