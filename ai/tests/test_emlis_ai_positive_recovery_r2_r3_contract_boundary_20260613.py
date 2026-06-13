from __future__ import annotations

import json

from emlis_ai_gate_recovery_loop import _synthesize_reader_report_from_public_surface
from emlis_ai_relation_surface_contract import (
    detect_relation_surface,
    relation_marker_keys_for_signal_key,
    relation_surface_status_for_reader,
    required_relation_marker_keys_for_reader,
    required_relation_signal_keys_for_reader,
)

_MISSING_RECOVERY_SURFACE = "\n".join(
    [
        "Emlisです。",
        "今回の入力では、疲れのあとにも、小さな回復が少し戻ってきています。",
    ]
)

_STRICT_RECOVERY_SURFACE = "\n".join(
    [
        "Emlisです。",
        "今回の入力では、疲れのあとにも、小さな回復が少し戻ってきています。",
        "戻ってくる動きとその前の重さが同じ流れの中でつながっています。",
    ]
)


def _serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_r2_contract_separates_relation_type_signal_key_and_marker_key() -> None:
    required_signals = required_relation_signal_keys_for_reader("positive_recovery")
    required_markers = required_relation_marker_keys_for_reader("positive_recovery")
    status = relation_surface_status_for_reader(
        expected_relation_types=("recovery",),
        detected_signal_keys=("recovery",),
        detected_marker_keys=("recovery_load_bridge_v1",),
    )

    assert "recovery_load_bridge" in required_signals
    assert "recovery_load_bridge_v1" in required_markers
    assert relation_marker_keys_for_signal_key("recovery_load_bridge") == ("recovery_load_bridge_v1",)
    assert status["expected_relation_types"] == ["recovery"]
    assert status["detected_relation_signal_keys"] == ["recovery"]
    assert status["detected_relation_marker_keys"] == ["recovery_load_bridge_v1"]
    assert status["matched_relation_signal_keys"] == []
    assert status["matched_relation_marker_keys"] == ["recovery_load_bridge_v1"]
    assert status["broad_relation_type_only"] is True
    assert status["relation_surface_missing"] is True
    assert status["comment_text_body_included"] is False


def test_r2_recovery_words_without_bridge_do_not_satisfy_strict_signal() -> None:
    missing = detect_relation_surface(_MISSING_RECOVERY_SURFACE, expected_relation_types=("recovery",))
    strict = detect_relation_surface(_STRICT_RECOVERY_SURFACE, expected_relation_types=("recovery",))

    assert missing["reader_relation_signal_detected"] is False
    assert missing["reader_relation_signal_keys"] == []
    assert strict["reader_relation_signal_detected"] is True
    assert "recovery_load_bridge" in strict["reader_relation_signal_keys"]
    assert "recovery" in strict["reader_relation_signal_relation_types"]


def test_r3_gate_recovery_synthesized_reader_does_not_promote_recovery_type_to_signal_key() -> None:
    reader = _synthesize_reader_report_from_public_surface(
        comment_text=_MISSING_RECOVERY_SURFACE,
        relation_values=("recovery",),
        source_phase="Phase20-8_PublicObservationRecovery",
        source_name="gate_recovery_public_candidate_synthesized_reader",
        relation_surface_contract_version="cocolon.emlis.phase20_8.reader.v1",
        summary_of_output="phase20_8_normal_observation_rebuild",
        confidence=0.8,
    )
    meta = reader.reader_relation_signal_meta
    trace = meta["strict_relation_trace"]

    assert reader.understandable is False
    assert reader.reader_relation_signal_detected is False
    assert reader.reader_relation_signal_keys == []
    assert reader.reader_relation_signal_relation_types == []
    assert reader.expected_relation_types == ["recovery"]
    assert "relation_not_expressed" in reader.rejection_reasons
    assert meta["relation_type_values_from_used_relation_ids"] == ["recovery"]
    assert meta["relation_type_values_not_promoted_to_signal_keys"] is True
    assert trace["broad_relation_type_only"] is True
    assert trace["broad_relation_type_only_keys"] == ["recovery"]
    assert trace["relation_surface_missing"] is True
    assert trace["matched_relation_signal_keys"] == []
    assert trace["comment_text_body_included"] is False

    serialized = _serialized(meta)
    assert _MISSING_RECOVERY_SURFACE not in serialized
    assert '"comment_text":' not in serialized
    assert '"raw_input":' not in serialized
    assert '"candidate_body":' not in serialized


def test_r3_gate_recovery_synthesized_reader_uses_detected_strict_surface_signal_only() -> None:
    reader = _synthesize_reader_report_from_public_surface(
        comment_text=_STRICT_RECOVERY_SURFACE,
        relation_values=("recovery",),
        source_phase="Phase20-8_PublicObservationRecovery",
        source_name="gate_recovery_public_candidate_synthesized_reader",
        relation_surface_contract_version="cocolon.emlis.phase20_8.reader.v1",
        summary_of_output="phase20_8_normal_observation_rebuild",
        confidence=0.8,
    )
    trace = reader.reader_relation_signal_meta["strict_relation_trace"]

    assert reader.understandable is True
    assert reader.reader_relation_signal_detected is True
    assert "recovery_load_bridge" in reader.reader_relation_signal_keys
    assert "recovery" not in reader.reader_relation_signal_keys
    assert reader.reader_relation_signal_relation_types == ["recovery"]
    assert trace["relation_surface_missing"] is False
    assert "recovery_load_bridge" in trace["matched_relation_signal_keys"]
    assert trace["relation_type_values_from_used_relation_ids"] == ["recovery"]
    assert trace["relation_type_values_not_promoted_to_signal_keys"] is True

    serialized = _serialized(reader.reader_relation_signal_meta)
    assert _STRICT_RECOVERY_SURFACE not in serialized
    assert '"comment_text":' not in serialized
    assert '"surface_body":' not in serialized
