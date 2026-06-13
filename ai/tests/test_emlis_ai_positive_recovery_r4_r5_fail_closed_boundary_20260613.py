from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_complete_reply_diagnostics_service import build_positive_recovery_relation_diagnostic
from emlis_ai_gate_recovery_loop import (
    _strict_relation_fail_closed_boundary_from_reader,
    _synthesize_reader_report_from_public_surface,
)

_MISSING_RECOVERY_SURFACE = "\n".join(
    [
        "Emlisです。",
        "小さな回復が少し戻ってきています。",
        "中心にある感覚として形を取り直しています。",
    ]
)

_STRICT_RECOVERY_SURFACE = "\n".join(
    [
        "Emlisです。",
        "疲れのあとにも、小さな回復が少し戻ってきています。",
        "戻ってくる動きとその前の重さが同じ流れの中でつながっています。",
    ]
)

_TEXT_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "comment_text",
    "commentText",
    "candidate_comment_text",
    "public_comment_text",
    "body",
    "text",
    "candidate_body",
    "surface_body",
}


def _serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_body_free(value: Any) -> None:
    if isinstance(value, Mapping):
        assert not (set(str(key) for key in value.keys()) & _TEXT_KEYS)
        for item in value.values():
            _assert_body_free(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_body_free(item)


def test_r4_boundary_applies_fail_closed_when_recovered_surface_still_misses_strict_signal() -> None:
    reader = _synthesize_reader_report_from_public_surface(
        comment_text=_MISSING_RECOVERY_SURFACE,
        relation_values=("recovery",),
        source_phase="phase20_8_normal_observation_rebuild",
        source_name="gate_recovery_public_candidate_synthesized_reader",
        relation_surface_contract_version="cocolon.emlis.phase20_8.normal_observation_rebuild.reader.v1",
        summary_of_output="phase20_8_normal_observation_rebuild",
        confidence=0.8,
        strict_relation_required=True,
    )
    boundary = _strict_relation_fail_closed_boundary_from_reader(
        reader,
        source_phase="phase20_8_normal_observation_rebuild",
        fallback_public_recovery_attempted=True,
    )

    assert reader.understandable is False
    assert reader.reader_relation_signal_detected is False
    assert reader.reader_relation_signal_keys == []
    assert "relation_not_expressed" in reader.rejection_reasons
    assert boundary["strict_relation_fail_closed_evaluated"] is True
    assert boundary["strict_relation_fail_closed_applied"] is True
    assert boundary["strict_relation_type"] == "recovery"
    assert boundary["strict_relation_surface_present_after_repair"] is False
    assert boundary["fallback_public_recovery_attempted"] is True
    assert boundary["fallback_public_recovery_allowed_for_this_candidate"] is False
    assert boundary["final_observation_status"] == "rejected"
    assert boundary["final_primary_reason"] == "relation_not_expressed"
    assert boundary["comment_text_allowed"] is False
    assert "strict_relation_surface_missing_after_repair" in boundary["blocked_reasons"]
    assert "relation_not_expressed" in boundary["blocked_reasons"]
    _assert_body_free(boundary)
    assert _MISSING_RECOVERY_SURFACE not in _serialized(boundary)


def test_r4_boundary_allows_positive_recovery_only_when_strict_signal_is_visible() -> None:
    reader = _synthesize_reader_report_from_public_surface(
        comment_text=_STRICT_RECOVERY_SURFACE,
        relation_values=("recovery",),
        source_phase="phase20_8_normal_observation_rebuild",
        source_name="gate_recovery_public_candidate_synthesized_reader",
        relation_surface_contract_version="cocolon.emlis.phase20_8.normal_observation_rebuild.reader.v1",
        summary_of_output="phase20_8_normal_observation_rebuild",
        confidence=0.8,
        strict_relation_required=True,
    )
    boundary = _strict_relation_fail_closed_boundary_from_reader(
        reader,
        source_phase="phase20_8_normal_observation_rebuild",
        fallback_public_recovery_attempted=True,
    )

    assert reader.understandable is True
    assert reader.reader_relation_signal_detected is True
    assert "recovery_load_bridge" in reader.reader_relation_signal_keys
    assert "recovery" not in reader.reader_relation_signal_keys
    assert boundary["strict_relation_fail_closed_evaluated"] is True
    assert boundary["strict_relation_fail_closed_applied"] is False
    assert boundary["strict_relation_type"] == "recovery"
    assert boundary["strict_relation_surface_present_after_repair"] is True
    assert boundary["fallback_public_recovery_allowed_for_this_candidate"] is True
    assert boundary["blocked_reasons"] == []
    _assert_body_free(boundary)
    assert _STRICT_RECOVERY_SURFACE not in _serialized(boundary)


def test_r5_diagnostic_records_fail_closed_closure_without_comment_body() -> None:
    gate_trace = {
        "reader": {
            "passed": False,
            "rejection_reasons": ["relation_not_expressed"],
            "relation_surface_contract_version": "cocolon.emlis.phase20_8.normal_observation_rebuild.reader.v1",
            "reader_relation_signal_detected": False,
            "reader_relation_signal_count": 0,
            "reader_relation_signal_keys": [],
            "reader_relation_signal_relation_types": [],
            "expected_relation_types": ["recovery"],
            "reader_relation_signal_meta": {
                "source_phase": "phase20_8_normal_observation_rebuild",
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        },
        "display_gate": {
            "passed": False,
            "observation_status": "rejected",
            "comment_text_allowed": False,
            "rejection_reasons": ["relation_not_expressed"],
        },
    }

    diagnostic = build_positive_recovery_relation_diagnostic(
        composer_candidate=None,
        gate_trace=gate_trace,
    )
    strict = diagnostic["strict_relation_fail_closed"]

    assert diagnostic["strict_relation_signal_required"] is True
    assert diagnostic["strict_relation_fail_closed_evaluated"] is True
    assert diagnostic["strict_relation_fail_closed_triggered"] is True
    assert diagnostic["strict_relation_fail_closed_applied"] is True
    assert diagnostic["strict_relation_type"] == "recovery"
    assert diagnostic["relation_not_expressed_retained"] is True
    assert "strict_relation_surface_missing_after_repair" in diagnostic["strict_relation_fail_closed_blocked_reasons"]
    assert strict["final_observation_status"] == "rejected"
    assert strict["final_primary_reason"] == "relation_not_expressed"
    assert strict["comment_text_allowed"] is False
    assert strict["fallback_public_recovery_allowed_for_this_candidate"] is False
    _assert_body_free(strict)
    serialized = _serialized(diagnostic)
    assert _MISSING_RECOVERY_SURFACE not in serialized
    assert '"comment_text":' not in serialized
    assert '"raw_input":' not in serialized


def test_r5_diagnostic_keeps_type_and_signal_separate_for_repaired_surface() -> None:
    gate_trace = {
        "reader": {
            "passed": True,
            "rejection_reasons": [],
            "relation_surface_contract_version": "cocolon.emlis.phase20_8.normal_observation_rebuild.reader.v1",
            "reader_relation_signal_detected": True,
            "reader_relation_signal_count": 1,
            "reader_relation_signal_keys": ["recovery_load_bridge"],
            "reader_relation_signal_relation_types": ["recovery"],
            "expected_relation_types": ["recovery"],
            "reader_relation_signal_meta": {
                "source_phase": "phase20_8_normal_observation_rebuild",
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        },
        "display_gate": {
            "passed": True,
            "observation_status": "passed",
            "comment_text_allowed": True,
            "rejection_reasons": [],
        },
    }

    diagnostic = build_positive_recovery_relation_diagnostic(
        composer_candidate=None,
        gate_trace=gate_trace,
    )
    strict = diagnostic["strict_relation_fail_closed"]

    assert diagnostic["strict_relation_signal_required"] is True
    assert diagnostic["strict_relation_fail_closed_evaluated"] is True
    assert diagnostic["strict_relation_fail_closed_triggered"] is False
    assert diagnostic["strict_relation_fail_closed_applied"] is False
    assert diagnostic["strict_relation_type"] == "recovery"
    assert diagnostic["matched_relation_signal_keys"] == ["recovery_load_bridge"]
    assert diagnostic["reader_relation_signal_relation_types"] == ["recovery"]
    assert "recovery" not in diagnostic["reader_relation_signal_keys"]
    assert strict["fallback_public_recovery_allowed_for_this_candidate"] is True
    assert strict["comment_text_allowed"] is True
    assert strict["blocked_reasons"] == []
    _assert_body_free(strict)
    serialized = _serialized(diagnostic)
    assert _STRICT_RECOVERY_SURFACE not in serialized
    assert '"comment_text":' not in serialized
