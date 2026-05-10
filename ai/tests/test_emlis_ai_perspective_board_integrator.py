from __future__ import annotations

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_observation_integrator_service import (
    integrate_perspective_board,
    phase5_integrator_contract_ready,
    validate_observation_graph,
)
from emlis_ai_perspective_board import build_perspective_board, phase5_board_contract_ready, validate_perspective_board
from emlis_ai_perspective_observers import SPECIALIST_OBSERVER_IDS, run_perspective_observers


def _current_input():
    return {
        "id": "phase5-test",
        "memo": "普通に生活したい。でもそうしたらもっと悪化する。そんなの分かってる。たまに逃げ出したくなる。",
        "memo_action": "明日は少し休みたい。",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def test_phase5_board_aggregates_reports_without_display_body_fields():
    evidence = build_evidence_ledger(_current_input())
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)

    assert phase5_board_contract_ready(board) is True
    assert validate_perspective_board(board) == []
    assert tuple(board.report_ids) == tuple(SPECIALIST_OBSERVER_IDS)
    assert board.claim_count > 0
    assert board.relation_count > 0
    assert board.evidence_span_ids == [span.span_id for span in evidence]
    for report in board.reports:
        assert not hasattr(report, "comment_text")
        assert not hasattr(report, "body")
        assert not hasattr(report, "reply_text")


def test_phase5_integrator_builds_required_observation_graph_structures():
    evidence = build_evidence_ledger(_current_input())
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")

    assert phase5_integrator_contract_ready(board, graph) is True
    assert validate_observation_graph(graph, board) == []
    assert graph.primary_state.claim_type == "primary_state"
    assert graph.primary_state.evidence_span_ids
    assert graph.core_tensions
    assert graph.pressure_sources
    assert graph.limit_signals
    assert graph.self_awareness
    assert graph.forbidden_claims
    assert graph.addressee_notes.display_name_call == "Mashさん"
    assert graph.addressee_notes.avoid_report_like is True


def test_phase5_integrator_validation_rejects_incomplete_graph():
    evidence = build_evidence_ledger(_current_input())
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")

    broken = type(graph)(
        primary_state=graph.primary_state,
        core_tensions=[],
        pressure_sources=[],
        limit_signals=[],
        self_awareness=[],
        value_or_strength_signals=[],
        addressee_notes=graph.addressee_notes,
        safety_boundaries=[],
        forbidden_claims=[],
        missing_information=[],
    )
    issues = validate_observation_graph(broken, board)
    assert "graph_pressure_sources_missing" in issues
    assert "graph_limit_signals_missing" in issues
    assert "graph_self_awareness_missing" in issues
    assert "graph_value_or_strength_missing" in issues
    assert phase5_integrator_contract_ready(board, broken) is False
