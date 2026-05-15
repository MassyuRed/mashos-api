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
    meta = scope.as_meta()
    assert meta["excluded_claims"]
    assert meta["included_claim_count"] == len(scope.included_claim_ids)
    assert meta["excluded_claim_count"] == len(scope.excluded_claims)
    assert meta["scope_diagnostic"]["version"] == "emlis.limited_scope_diagnostic.v1"
    assert meta["scope_diagnostic"]["coverage_matrix_hint"] in {
        "complexity_limit",
        "eligible_partial_observation",
        "eligible_current_input_core",
    }


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
    meta = scope.as_meta()
    assert meta["included_claim_count"] == 0
    assert meta["scope_diagnostic"]["minimum_coverage"]["meets_minimum_claim"] is False
    assert meta["scope_diagnostic"]["coverage_matrix_hint"] == "primary_state_grounding"
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
    meta = scope.as_meta()
    assert meta["safety_boundaries"] == ["safety_boundary"]
    assert meta["scope_diagnostic"]["coverage_matrix_hint"] == "safety_boundary"
    pre_generation = meta["scope_diagnostic"]["safety_pre_generation_block"]
    assert pre_generation["target_step"] == "Step10_safety_boundary"
    assert pre_generation["blocked_before_composer"] is True
    assert pre_generation["composer_generation_allowed"] is False
    assert pre_generation["fixed_reply_allowed"] is False
    assert limited_observation_scope_ready(scope, evidence) is False
    assert validate_limited_observation_scope(scope=scope, evidence_spans=evidence) == []


def test_step09_scope_expands_event_cues_into_partial_observation_meta():
    memo = "仕事が多すぎて焦っている。もう全部嫌だ。少しでも自分を大事にしたい。"
    evidence, graph = _graph_for(memo)
    assert graph.pressure_sources == []
    assert graph.limit_signals == []

    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    meta = scope.as_meta()

    assert scope.scope_status == "eligible"
    assert scope.coverage_scope == "partial_observation"
    assert limited_observation_scope_ready(scope, evidence) is True
    assert validate_limited_observation_scope(scope=scope, evidence_spans=evidence) == []
    assert scope.scoped_graph.primary_state.text == "少しでも自分を大事にしたい"
    assert [claim.text for claim in scope.scoped_graph.pressure_sources] == ["仕事が多すぎて焦っている"]
    assert [claim.text for claim in scope.scoped_graph.limit_signals] == ["もう全部嫌だ"]
    assert any(item.reason_code == "limited_scope_group_claim_limit" for item in scope.excluded_claims)

    expansion = meta["scope_expansion"]
    assert expansion["version"] == "emlis.scope_expansion.v1"
    assert expansion["target_step"] == "Step09_scope_expansion"
    assert expansion["allows_multiple_groups_per_span"] is True
    assert expansion["created_claim_count"] >= 3
    assert "pressure_sources" in expansion["created_claim_ids_by_group"]
    assert "limit_signals" in expansion["created_claim_ids_by_group"]
    assert expansion["span_groups"]["s2"] == ["limit_signals", "pressure_sources"]
    assert "anxiety" in meta["coverage_groups"]
    assert "limit_escape" in meta["coverage_groups"]
    assert "value_wish" in meta["coverage_groups"]
    assert meta["scope_diagnostic"]["coverage_groups"] == meta["coverage_groups"]
    assert meta["scope_diagnostic"]["scope_expansion"] == expansion


def test_step09_scope_keeps_plain_event_out_of_scope_without_inventing_claims():
    evidence, graph = _graph_for("今日はコンビニで買い物した。")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)

    assert scope.scope_status == "out_of_scope"
    assert "limited_scope_no_grounded_primary_state" in scope.rejection_reasons
    assert scope.scoped_graph.primary_state.text == ""
    meta = scope.as_meta()
    assert meta["scope_expansion"]["created_claim_count"] == 0
    assert meta["coverage_groups"] == []
