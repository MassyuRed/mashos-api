from __future__ import annotations

import pytest

from emlis_ai_conversation_composer_service import build_conversation_composer_payload, compose_emlis_conversation_candidate
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_types import EvidenceSpan


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _scoped_case():
    current_input = {
        "id": "phase4-emotion",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": SAMPLE_MEMO,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    full_graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=full_graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    scoped_ids = []
    for value in list(scope.scoped_graph.primary_state.evidence_span_ids or []):
        if value not in scoped_ids:
            scoped_ids.append(value)
    for group in (
        scope.scoped_graph.pressure_sources,
        scope.scoped_graph.limit_signals,
        scope.scoped_graph.self_awareness,
        scope.scoped_graph.value_or_strength_signals,
    ):
        for claim in group:
            for value in list(claim.evidence_span_ids or []):
                if value not in scoped_ids:
                    scoped_ids.append(value)
    for edge in scope.scoped_graph.core_tensions:
        for value in list(edge.evidence_span_ids or []):
            if value not in scoped_ids:
                scoped_ids.append(value)
    return evidence, full_graph, scope, scoped_ids


def test_grounding_uses_scoped_graph_for_partial_observation():
    evidence, full_graph, scope, scoped_ids = _scoped_case()
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="phase4-scoped-grounding",
        limited_observation_scope=scope,
    )
    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=CocolonLimitedComposerClient(),
        trace_id="phase4-scoped-grounding",
        limited_observation_scope=scope,
    )

    assert payload["limited_observation_scope"]["scope_status"] == "eligible"
    assert scope.excluded_claims
    assert candidate.comment_text

    grounding = judge_grounding(
        comment_text=candidate.comment_text,
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        allowed_evidence_span_ids=scoped_ids,
        grounding_scope="limited_scoped_graph",
    )

    assert grounding.passed is True
    assert grounding.grounding_scope == "limited_scoped_graph"
    assert grounding.allowed_evidence_span_ids == scoped_ids
    assert set(grounding.ignored_evidence_span_ids).issubset({span.span_id for span in evidence})
    assert set(candidate.used_evidence_span_ids).issubset(set(scoped_ids))
    assert set(candidate.used_claim_ids).issubset(set(scope.included_claim_ids))
    assert set(candidate.used_relation_ids).issubset(set(scope.included_relation_ids))


def test_scoped_grounding_does_not_allow_excluded_evidence_to_ground_overclaim():
    evidence, _full_graph, scope, scoped_ids = _scoped_case()
    excluded_span = EvidenceSpan(
        span_id="excluded-overclaim",
        raw_text="本当は誰かに頼りたい",
        start_index=0,
        end_index=10,
        detected_type="wish",
        confidence=1.0,
        source_field="memo",
    )
    text = "Mashさん、Emlisです。\n本当は誰かに頼りたい気持ちが重なっています。"

    scoped = judge_grounding(
        comment_text=text,
        graph=scope.scoped_graph,
        evidence_spans=[*evidence, excluded_span],
        allowed_evidence_span_ids=scoped_ids,
        grounding_scope="limited_scoped_graph",
    )

    assert scoped.passed is False
    assert "unsupported_sentence" in scoped.rejection_reasons
    assert "excluded-overclaim" in scoped.ignored_evidence_span_ids
    assert all("excluded-overclaim" not in claim.evidence_span_ids for claim in scoped.sentence_claims)


@pytest.mark.asyncio
async def test_render_records_scoped_grounding_when_default_limited_composer_enabled(monkeypatch):
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase4-render-user",
        subscription_tier="free",
        current_input={
            "id": "phase4-render-emotion",
            "created_at": "2026-05-10T00:00:00Z",
            "memo": SAMPLE_MEMO,
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    scoped_grounding = multi["scoped_grounding"]
    grounding_report = multi["grounding_report"]

    assert scoped_grounding["enabled"] is True
    assert scoped_grounding["grounding_scope"] == "limited_scoped_graph"
    assert scoped_grounding["allowed_evidence_span_ids"]
    assert scoped_grounding["excluded_claims_retained_for_meta"]
    assert grounding_report["grounding_scope"] == "limited_scoped_graph"
    assert grounding_report["allowed_evidence_span_ids"] == scoped_grounding["allowed_evidence_span_ids"]
    assert grounding_report["ignored_evidence_span_ids"]
    assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable"}

@pytest.mark.asyncio
async def test_step07_default_route_keeps_scoped_grounding_and_passed_only_comment(monkeypatch):
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step07-render-user",
        subscription_tier="free",
        current_input={
            "id": "step07-render-emotion",
            "created_at": "2026-05-10T00:00:00Z",
            "memo": SAMPLE_MEMO,
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    phase_gate = multi["phase_gate"]
    scoped_grounding = multi["scoped_grounding"]
    grounding_report = multi["grounding_report"]
    grounding_gate = phase_gate["gate_trace"]["grounding"]
    summary = reply.meta["diagnostic_summary"]
    grounding_diagnostics = summary["gate_results"]["grounding"]["diagnostics"]

    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()
    assert summary["normal_connection"]["decision"] == "default_composer_connected"
    assert scoped_grounding["enabled"] is True
    assert scoped_grounding["grounding_scope"] == "limited_scoped_graph"
    assert scoped_grounding["allowed_evidence_span_ids"]
    assert scoped_grounding["excluded_claims_retained_for_meta"]
    assert grounding_report["grounding_scope"] == "limited_scoped_graph"
    assert grounding_report["allowed_evidence_span_ids"] == scoped_grounding["allowed_evidence_span_ids"]
    assert grounding_gate["grounding_scope"] == "limited_scoped_graph"
    assert grounding_gate["allowed_evidence_span_count"] == len(scoped_grounding["allowed_evidence_span_ids"])
    assert grounding_gate["ignored_evidence_span_count"] > 0
    assert grounding_diagnostics["grounding_scope"] == "limited_scoped_graph"
    assert grounding_diagnostics["allowed_evidence_span_count"] == len(scoped_grounding["allowed_evidence_span_ids"])
    assert grounding_diagnostics["ignored_evidence_span_count"] == grounding_gate["ignored_evidence_span_count"]

    assert phase_gate["comment_text_allowed"] is True
    assert phase_gate["frontend_display_control_ready"] is True
    assert phase_gate["phase9_frontend_display_control_ready"] is True
    assert phase_gate["release_ready"] is True

