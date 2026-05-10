from __future__ import annotations

import inspect

from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _payload_for(memo: str = SAMPLE_MEMO):
    current_input = {
        "id": "limited-composer-test",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="limited-composer-test",
    )
    return payload, evidence, scope


def test_limited_composer_generates_from_scoped_payload_without_external_ai():
    payload, evidence, scope = _payload_for()
    result = CocolonLimitedComposerClient().generate(payload)

    assert result["response_schema_version"] == "emlis.composer.response.v1"
    assert result["composer_source"] == "ai_generated"
    assert result["composer_model"] == "cocolon_limited_composer.v1"
    assert result["fixed_string_renderer_used"] is False
    assert result["coverage_scope"] in {"partial_observation", "current_input_core"}
    assert result["comment_text"]
    assert set(result["used_evidence_span_ids"]).issubset({span.span_id for span in evidence})
    assert set(result["used_claim_ids"]).issubset(set(scope.included_claim_ids))
    assert set(result["used_relation_ids"]).issubset(set(scope.included_relation_ids))

    for banned in ("そこには", "もありました", "も含まれていました", "と思います", "一緒に見ます", "今の私は", "あなたは"):
        assert banned not in result["comment_text"]


def test_limited_composer_candidate_passes_conversation_composer_contract():
    payload, evidence, scope = _payload_for()
    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=CocolonLimitedComposerClient(),
        trace_id="limited-composer-contract",
    )

    assert candidate.composer_source == "ai_generated"
    assert candidate.status == "generated"
    assert candidate.ai_generated is True
    assert candidate.fixed_string_renderer_used is False
    assert candidate.composer_model == "cocolon_limited_composer.v1"
    assert candidate.generation_method == "scoped_graph_evidence_composer"
    assert candidate.coverage_scope in {"partial_observation", "current_input_core"}
    assert candidate.used_evidence_span_ids
    assert set(candidate.used_evidence_span_ids).issubset({span.span_id for span in evidence})
    assert set(candidate.used_claim_ids).issubset(set(scope.included_claim_ids))
    assert set(candidate.used_relation_ids).issubset(set(scope.included_relation_ids))


def test_limited_composer_returns_unavailable_for_non_scoped_or_unsafe_payload():
    payload, *_ = _payload_for()
    unsafe_payload = dict(payload)
    unsafe_graph = dict(payload["observation_graph"])
    unsafe_graph["safety_boundaries"] = ["safety_boundary"]
    unsafe_payload["observation_graph"] = unsafe_graph

    result = CocolonLimitedComposerClient().generate(unsafe_payload)

    assert result["composer_source"] == "unavailable"
    assert result["comment_text"] == ""
    assert "limited_composer_safety_boundary" in result["rejection_reasons"]


def test_limited_composer_source_has_no_runtime_fixed_observation_surfaces():
    source = inspect.getsource(CocolonLimitedComposerClient)
    for banned in ("そこには", "もありました", "も含まれていました", "と思います", "として見ています", "一緒に見ます"):
        assert banned not in source
    assert "fallback" not in source.lower()
