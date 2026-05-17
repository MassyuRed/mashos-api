from __future__ import annotations

import json
from types import SimpleNamespace

from emlis_ai_complete_reply_diagnostics_service import (
    LIMITED_READER_REPAIR_DIAGNOSTIC_VERSION,
    build_complete_reply_service_diagnostics,
    build_positive_recovery_relation_diagnostic,
)
from emlis_ai_observation_diagnostic_lockdown import (
    build_observation_diagnostic_lockdown,
    dump_observation_diagnostic,
)
from emlis_ai_relation_surface_contract import RELATION_SURFACE_CONTRACT_VERSION
from emlis_ai_types import DisplayDecision

_SECRET_COMMENT = "これは Step7 ログへ出してはいけない観測本文です"
_SECRET_RAW_INPUT = "これは Step7 ログへ出してはいけない入力本文です"
_SECRET_MARKER_PHRASE = "これは Step7 ログへ出してはいけない marker phrase です"


def _limited_reader_repair_meta() -> dict:
    return {
        "version": "limited_reader_repair.v1",
        "target_step": "Step5_relation_surface_marker_repair",
        "attempted": True,
        "applied": True,
        "requires_limited_reader_repair": True,
        "previous_rejection_reasons": ["relation_not_expressed"],
        "reader_rejection_reasons": ["relation_not_expressed"],
        "repair_required_reasons": ["relation_not_expressed"],
        "operations": ["relation_marker_appended"],
        "pending_operations": [],
        "addressee_repaired": False,
        "relation_surface_repaired": True,
        "relation_type": "recovery",
        "relation_marker_key": "recovery_load_bridge_v1",
        "relation_marker_signal_detected": True,
        "relation_marker_signal_keys": ["recovery_load_bridge"],
        "relation_marker_signal_relation_types": ["recovery"],
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "comment_text_changed": True,
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
        "complete_client_self_repair_touched": False,
        "coverage_scope": "current_input_core",
        "profile_key": "positive_recovery",
        # Hostile accidental fields: diagnostic output must not copy them.
        "comment_text": _SECRET_COMMENT,
        "raw_input": _SECRET_RAW_INPUT,
        "relation_marker_phrase": _SECRET_MARKER_PHRASE,
    }


def _reader_passed_gate_trace() -> dict:
    return {
        "reader": {
            "passed": True,
            "primary_reason": "passed",
            "rejection_reasons": [],
            "reader_relation_signal_detected": True,
            "reader_relation_signal_count": 1,
            "reader_relation_signal_keys": ["recovery_load_bridge"],
            "reader_relation_signal_relation_types": ["recovery"],
            "expected_relation_types": ["recovery"],
            "raw_input_included": False,
        }
    }


def _limited_candidate() -> SimpleNamespace:
    repair_meta = _limited_reader_repair_meta()
    return SimpleNamespace(
        status="generated",
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        coverage_scope="current_input_core",
        used_relation_ids=["recovery"],
        composer_meta={
            "limited_reader_repair": repair_meta,
            "limited_reader_repair_step5": repair_meta,
            "relation_types": ["recovery"],
            "expected_relation_types": ["recovery"],
            "raw_input_included": False,
        },
    )


def test_step7_relation_diagnostic_exposes_limited_repair_state_without_text_payload() -> None:
    diagnostic = build_positive_recovery_relation_diagnostic(
        composer_candidate=_limited_candidate(),
        gate_trace=_reader_passed_gate_trace(),
    )

    assert diagnostic["limited_reader_repair_diagnostic"]["version"] == LIMITED_READER_REPAIR_DIAGNOSTIC_VERSION
    assert diagnostic["limited_reader_repair_attempted"] is True
    assert diagnostic["limited_reader_repair_applied"] is True
    assert diagnostic["limited_reader_repair_operations"] == ["relation_marker_appended"]
    assert diagnostic["limited_reader_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert diagnostic["limited_reader_repair_relation_marker_signal_keys"] == ["recovery_load_bridge"]
    assert diagnostic["limited_reader_repair_relation_type"] == "recovery"
    assert diagnostic["limited_reader_repair_meaning_added"] is False
    assert diagnostic["limited_reader_repair_gate_relaxed"] is False
    assert diagnostic["limited_reader_repair_raw_input_included"] is False
    assert diagnostic["reader_gate_relation_not_expressed"] is False
    assert diagnostic["self_repair_relation_marker_applied"] is True
    assert diagnostic["self_repair_relation_marker_key"] == "recovery_load_bridge_v1"

    serialized = json.dumps(diagnostic, ensure_ascii=False, sort_keys=True)
    assert _SECRET_COMMENT not in serialized
    assert _SECRET_RAW_INPUT not in serialized
    assert _SECRET_MARKER_PHRASE not in serialized
    assert "relation_marker_phrase" not in serialized
    assert "comment_text\":" not in serialized
    assert "raw_input\":" not in serialized


def test_step7_complete_reply_diagnostics_carries_limited_repair_top_level_meta() -> None:
    display_decision = DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["display_gate_rejected"],
        gate_trace=_reader_passed_gate_trace(),
    )

    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_limited_candidate(),
        display_decision=display_decision,
        gate_trace=_reader_passed_gate_trace(),
        diagnostic_summary={"coverage_group": "positive_recovery"},
    )

    assert diagnostics["limited_reader_repair_attempted"] is True
    assert diagnostics["limited_reader_repair_applied"] is True
    assert diagnostics["limited_reader_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert diagnostics["limited_reader_repair_relation_marker_signal_keys"] == ["recovery_load_bridge"]
    assert diagnostics["limited_reader_repair_relation_type"] == "recovery"
    assert diagnostics["connected_parts"]["limited_reader_repair"] is True
    assert diagnostics["display_gate_relaxed"] is False
    assert diagnostics["raw_input_included"] is False
    assert diagnostics["comment_text_included"] is False

    serialized = json.dumps(diagnostics, ensure_ascii=False, sort_keys=True)
    assert _SECRET_COMMENT not in serialized
    assert _SECRET_RAW_INPUT not in serialized
    assert _SECRET_MARKER_PHRASE not in serialized
    assert "relation_marker_phrase" not in serialized
    assert "comment_text\":" not in serialized
    assert "raw_input\":" not in serialized


def test_step7_observation_lockdown_log_distinguishes_limited_reader_repair_from_complete_self_repair() -> None:
    repair_meta = _limited_reader_repair_meta()
    meta = {
        "observation_status": "rejected",
        "observation_trace_id": "emlisobs-step7-limited-repair",
        "diagnostic_summary": {
            "observation_status": "rejected",
            "stage": "display",
            "primary_reason": "display_gate_rejected",
            "coverage_group": "positive_recovery",
            "gate_results": {
                "reader": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
                "grounding": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
                "template_echo": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
                "display": {"passed": False, "primary_reason": "display_gate_rejected", "rejection_reasons": ["display_gate_rejected"]},
            },
            "complete_reply_service_diagnostics": {
                "complete_candidate_seen": True,
                "complete_candidate_generated": True,
                "composer_status": "generated",
                "composer_source": "ai_generated",
                "relation_types": ["recovery"],
                "limited_reader_repair": repair_meta,
                "limited_reader_repair_attempted": True,
                "limited_reader_repair_applied": True,
                "limited_reader_repair_relation_marker_key": "recovery_load_bridge_v1",
                "limited_reader_repair_relation_type": "recovery",
            },
        },
    }

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta=meta,
        emotion_log_id="emotion-step7-limited-repair",
        created_at="2026-05-17T12:00:00Z",
    )

    assert record["limited_reader_repair_attempted"] is True
    assert record["limited_reader_repair_applied"] is True
    assert record["limited_reader_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert record["limited_reader_repair_relation_marker_signal_keys"] == ["recovery_load_bridge"]
    assert record["limited_reader_repair_relation_type"] == "recovery"
    assert record["limited_reader_repair_meaning_added"] is False
    assert record["limited_reader_repair_gate_relaxed"] is False
    assert record["self_repair"]["attempted"] is True
    assert record["self_repair"]["status"] == "limited_reader_repair_applied"
    assert record["self_repair"]["limited_reader_repair_applied"] is True

    dumped = dump_observation_diagnostic(record)
    assert _SECRET_COMMENT not in dumped
    assert _SECRET_RAW_INPUT not in dumped
    assert _SECRET_MARKER_PHRASE not in dumped
    assert "relation_marker_phrase" not in dumped
    assert json.loads(dumped)["comment_text_included"] is False
    assert json.loads(dumped)["raw_input_included"] is False
