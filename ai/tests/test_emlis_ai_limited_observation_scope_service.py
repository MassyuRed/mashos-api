from __future__ import annotations

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_observation_scope_service import (
    build_limited_observation_scope,
    limited_observation_scope_ready,
    validate_limited_observation_scope,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_types import AddresseeNotes, GraphClaim, ObservationGraph


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _current_input(memo: str = SAMPLE_MEMO):
    return {
        "id": "limited-scope-test",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _graph_for(memo: str = SAMPLE_MEMO):
    evidence = build_evidence_ledger(_current_input(memo))
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    return evidence, graph


def test_limited_scope_selects_grounded_partial_graph_without_body_text():
    evidence, graph = _graph_for()
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)

    assert scope.scope_status == "eligible"
    assert limited_observation_scope_ready(scope, evidence) is True
    assert validate_limited_observation_scope(scope=scope, evidence_spans=evidence) == []
    assert scope.scoped_graph.primary_state.text
    assert scope.scoped_graph.primary_state.evidence_span_ids
    assert len(scope.scoped_graph.core_tensions) <= 1
    assert len(scope.scoped_graph.pressure_sources) <= 1
    assert len(scope.scoped_graph.limit_signals) <= 1
    assert len(scope.scoped_graph.self_awareness) <= 1
    assert len(scope.scoped_graph.value_or_strength_signals) <= 1
    assert scope.included_claim_ids
    assert scope.coverage_scope in {"partial_observation", "current_input_core"}
    assert scope.max_reply_sentence_count <= 4

    scoped_surface = "\n".join(
        [
            scope.scoped_graph.primary_state.text,
            *(claim.text for claim in scope.scoped_graph.pressure_sources),
            *(claim.text for claim in scope.scoped_graph.limit_signals),
            *(claim.text for claim in scope.scoped_graph.self_awareness),
            *(claim.text for claim in scope.scoped_graph.value_or_strength_signals),
        ]
    )
    assert "Emlisです" not in scoped_surface
    assert "そこには" not in scoped_surface
    assert "一緒に見ます" not in scoped_surface


def test_limited_scope_keeps_full_graph_outside_scope_instead_of_forcing_every_claim():
    evidence, graph = _graph_for()
    scope = build_limited_observation_scope(
        graph=graph,
        evidence_spans=evidence,
        max_core_tensions=1,
        max_claims_per_group=1,
        max_optional_claims=1,
    )

    full_graph_claim_count = 1 + sum(
        len(group)
        for group in (
            graph.pressure_sources,
            graph.limit_signals,
            graph.self_awareness,
            graph.value_or_strength_signals,
        )
    )
    scoped_graph_claim_count = 1 + sum(
        len(group)
        for group in (
            scope.scoped_graph.pressure_sources,
            scope.scoped_graph.limit_signals,
            scope.scoped_graph.self_awareness,
            scope.scoped_graph.value_or_strength_signals,
        )
    )

    assert scope.scope_status == "eligible"
    assert scoped_graph_claim_count <= full_graph_claim_count
    assert scoped_graph_claim_count <= 2
    assert any(item.reason_code.endswith("claim_limit") for item in scope.excluded_claims)
    assert scope.as_meta()["excluded_claims"]


def test_limited_scope_returns_out_of_scope_when_primary_state_has_no_grounding():
    graph = ObservationGraph(
        primary_state=GraphClaim(
            claim_id="graph.primary.missing",
            claim_type="primary_state",
            text="",
            evidence_span_ids=[],
            confidence=0.0,
        ),
        addressee_notes=AddresseeNotes(display_name_call="Mashさん"),
    )
    scope = build_limited_observation_scope(graph=graph, evidence_spans=[])

    assert scope.scope_status == "out_of_scope"
    assert scope.scoped_graph.primary_state.text == ""
    assert scope.scoped_graph.core_tensions == []
    assert "limited_scope_no_grounded_primary_state" in scope.rejection_reasons
    assert limited_observation_scope_ready(scope, []) is False
    assert validate_limited_observation_scope(scope=scope, evidence_spans=[]) == []


def test_limited_scope_blocks_safety_boundary_before_composer():
    evidence, graph = _graph_for("消えたい気持ちが強い。")
    safety_graph = ObservationGraph(
        primary_state=graph.primary_state,
        core_tensions=graph.core_tensions,
        pressure_sources=graph.pressure_sources,
        limit_signals=graph.limit_signals,
        self_awareness=graph.self_awareness,
        value_or_strength_signals=graph.value_or_strength_signals,
        addressee_notes=graph.addressee_notes,
        safety_boundaries=["safety_boundary"],
        forbidden_claims=graph.forbidden_claims,
        missing_information=graph.missing_information,
    )
    scope = build_limited_observation_scope(graph=safety_graph, evidence_spans=evidence)

    assert scope.scope_status == "safety_blocked"
    assert scope.scoped_graph.primary_state.text == ""
    assert scope.scoped_graph.core_tensions == []
    assert "limited_scope_safety_boundary" in scope.rejection_reasons
    assert limited_observation_scope_ready(scope, evidence) is False
    assert validate_limited_observation_scope(scope=scope, evidence_spans=evidence) == []
