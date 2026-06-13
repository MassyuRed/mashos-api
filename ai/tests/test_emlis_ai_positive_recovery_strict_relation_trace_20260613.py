from __future__ import annotations

import json
from types import SimpleNamespace

from emlis_ai_complete_composer_initial_meta import COMPLETE_COMPOSER_INITIAL_MODEL
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_GENERATION_METHOD
from emlis_ai_complete_reply_diagnostics_service import build_positive_recovery_relation_diagnostic
from emlis_ai_relation_surface_contract import (
    RELATION_SURFACE_CONTRACT_VERSION,
    relation_surface_status_for_reader,
    required_relation_signal_keys_for_reader,
)


def _candidate_without_strict_relation_signal() -> SimpleNamespace:
    return SimpleNamespace(
        status="generated",
        composer_source="ai_generated",
        composer_model=COMPLETE_COMPOSER_INITIAL_MODEL,
        generation_method=COMPLETE_COMPOSER_GENERATION_METHOD,
        generation_scope="scoped_graph_evidence_composer",
        coverage_scope="positive_recovery",
        used_relation_ids=["recovery"],
        composer_meta={
            "complete_composer_client_added": True,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "coverage_group": "positive_recovery",
            "relation_types": ["recovery"],
            "used_relation_ids": ["recovery"],
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "surface_signature": {
                "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
                "expected_relation_types": ["recovery"],
                "reader_relation_signal_detected": False,
                "reader_relation_signal_count": 0,
                "reader_relation_signal_keys": [],
                "reader_relation_signal_relation_types": [],
                "raw_input_included": False,
            },
            "raw_input_included": False,
        },
    )


def _candidate_with_strict_relation_signal() -> SimpleNamespace:
    return SimpleNamespace(
        status="generated",
        composer_source="ai_generated",
        composer_model=COMPLETE_COMPOSER_INITIAL_MODEL,
        generation_method=COMPLETE_COMPOSER_GENERATION_METHOD,
        generation_scope="scoped_graph_evidence_composer",
        coverage_scope="positive_recovery",
        used_relation_ids=["recovery"],
        composer_meta={
            "complete_composer_client_added": True,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "coverage_group": "positive_recovery",
            "relation_types": ["recovery"],
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "surface_signature": {
                "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
                "expected_relation_types": ["recovery"],
                "reader_relation_signal_detected": True,
                "reader_relation_signal_count": 1,
                "reader_relation_signal_keys": ["recovery_load_bridge"],
                "reader_relation_signal_relation_types": ["recovery"],
                "raw_input_included": False,
            },
            "self_repair": {
                "self_repair_relation_marker_applied": True,
                "self_repair_relation_marker_key": "recovery_load_bridge_v1",
                "self_repair_relation_marker_keys": ["recovery_load_bridge_v1"],
                "self_repair_relation_marker_signal_detected": True,
                "self_repair_relation_marker_signal_keys": ["recovery_load_bridge"],
                "self_repair_relation_marker_signal_relation_types": ["recovery"],
                "self_repair_relation_marker_meaning_added": False,
                "self_repair_relation_marker_gate_relaxed": False,
                "raw_input_included": False,
            },
            "raw_input_included": False,
        },
    )


def _broad_only_gate_trace() -> dict[str, object]:
    return {
        "reader": {
            "passed": True,
            "relation_surface_contract_version": "cocolon.emlis.public_observation_recovery.p6.labelled_two_stage_surface_recomposition.reader.v1",
            "reader_relation_signal_detected": True,
            "reader_relation_signal_count": 1,
            "reader_relation_signal_keys": ["recovery"],
            "reader_relation_signal_relation_types": ["recovery"],
            "expected_relation_types": ["recovery"],
            "rejection_reasons": [],
            "reader_relation_signal_meta": {
                "source_phase": "Phase20-8_PublicObservationRecovery",
                "source": "gate_recovery_public_candidate_synthesized_reader",
                "raw_input_included": False,
            },
        }
    }


def _strict_gate_trace() -> dict[str, object]:
    return {
        "reader": {
            "passed": True,
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "reader_relation_signal_detected": True,
            "reader_relation_signal_count": 1,
            "reader_relation_signal_keys": ["recovery_load_bridge"],
            "reader_relation_signal_relation_types": ["recovery"],
            "expected_relation_types": ["recovery"],
            "rejection_reasons": [],
            "reader_relation_signal_meta": {"source_phase": "reader_gate", "raw_input_included": False},
        }
    }


def test_r1_relation_surface_status_separates_recovery_type_from_strict_signal() -> None:
    required = required_relation_signal_keys_for_reader("positive_recovery")
    status = relation_surface_status_for_reader(
        expected_relation_types=("recovery",),
        detected_signal_keys=("recovery",),
    )

    assert "recovery_load_bridge" in required
    assert status["strict_relation_signal_required"] is True
    assert "recovery_load_bridge" in status["required_relation_signal_keys"]
    assert status["matched_relation_signal_keys"] == []
    assert status["broad_relation_type_only"] is True
    assert status["broad_relation_type_only_keys"] == ["recovery"]
    assert status["relation_surface_missing"] is True
    assert status["relation_surface_status"] == "missing"
    assert status["raw_input_included"] is False
    assert status["comment_text_body_included"] is False


def test_r1_relation_surface_status_marks_strict_signal_present() -> None:
    status = relation_surface_status_for_reader(
        expected_relation_types=("recovery",),
        detected_signal_keys=("recovery_load_bridge",),
    )

    assert status["strict_relation_signal_required"] is True
    assert status["matched_relation_signal_keys"] == ["recovery_load_bridge"]
    assert status["broad_relation_type_only"] is False
    assert status["relation_surface_missing"] is False
    assert status["relation_surface_status"] == "present"


def test_r1_positive_recovery_trace_records_broad_type_only_without_changing_gate_result() -> None:
    diagnostic = build_positive_recovery_relation_diagnostic(
        composer_candidate=_candidate_without_strict_relation_signal(),
        gate_trace=_broad_only_gate_trace(),
    )
    trace = diagnostic["strict_relation_trace"]

    assert diagnostic["diagnostic_connected"] is True
    assert diagnostic["reader_relation_signal_detected"] is True
    assert diagnostic["reader_relation_signal_keys"] == ["recovery"]
    assert diagnostic["selected_relation_signal_source"] == "reader_gate"
    assert diagnostic["gate_recovery_synthesized_reader_report"] is True
    assert diagnostic["strict_relation_signal_required"] is True
    assert "recovery_load_bridge" in diagnostic["required_relation_signal_keys"]
    assert diagnostic["matched_relation_signal_keys"] == []
    assert diagnostic["broad_relation_type_only"] is True
    assert diagnostic["broad_relation_type_only_keys"] == ["recovery"]
    assert diagnostic["relation_surface_missing"] is True
    assert diagnostic["relation_surface_missing_after_repair"] is True
    assert trace["reader_relation_signal_keys"] == ["recovery"]
    assert trace["strict_relation_surface_present_anywhere"] is False
    assert trace["response_shape_changed"] is False
    assert trace["public_response_key_change"] is False
    assert trace["api_route_changed"] is False
    assert trace["db_physical_name_changed"] is False
    assert trace["rn_visible_title_changed"] is False

    serialized = json.dumps(diagnostic, ensure_ascii=False, sort_keys=True)
    assert '"raw_text":' not in serialized
    assert '"raw_input":' not in serialized
    assert '"current_input":' not in serialized
    assert '"comment_text":' not in serialized
    assert '"candidate_body":' not in serialized
    assert '"surface_body":' not in serialized


def test_r1_positive_recovery_trace_marks_strict_surface_when_present() -> None:
    diagnostic = build_positive_recovery_relation_diagnostic(
        composer_candidate=_candidate_with_strict_relation_signal(),
        gate_trace=_strict_gate_trace(),
    )

    assert diagnostic["strict_relation_signal_required"] is True
    assert diagnostic["matched_relation_signal_keys"] == ["recovery_load_bridge"]
    assert diagnostic["broad_relation_type_only"] is False
    assert diagnostic["relation_surface_missing"] is False
    assert diagnostic["relation_surface_missing_after_repair"] is False
    assert diagnostic["strict_relation_surface_present_anywhere"] is True
    assert diagnostic["self_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert diagnostic["self_repair_relation_marker_meaning_added"] is False
    assert diagnostic["self_repair_relation_marker_gate_relaxed"] is False
