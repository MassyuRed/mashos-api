from __future__ import annotations

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_conversation_composer_service import compose_emlis_conversation
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_display_gate import decide_emlis_observation_display
from emlis_ai_types import SafetyBoundaryReport


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _run(memo: str, *, display_name: str = "Mash"):
    current_input = {
        "id": "emo-test",
        "created_at": "2026-05-09T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name=display_name)
    text = compose_emlis_conversation(
        graph=graph,
        evidence_spans=evidence,
        display_name=display_name,
        greeting_text="Emlisです。",
    )
    reader = judge_listener_readability(text)
    grounding = judge_grounding(comment_text=text, graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text=text, evidence_spans=evidence)
    decision = decide_emlis_observation_display(
        comment_text=text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        trace_id="test-trace",
    )
    return evidence, reports, graph, text, reader, grounding, template, decision


def test_multi_perspective_reports_and_graph_are_created_without_legacy_phrases():
    evidence, reports, graph, text, reader, grounding, template, decision = _run(SAMPLE_MEMO)

    assert len(evidence) >= 6
    assert {report.observer_id for report in reports} >= {
        "explicit_content",
        "emotion_state",
        "conflict_coexistence",
        "pressure_constraint",
        "limit_signal",
        "self_awareness",
        "value_strength",
        "addressee_model",
        "safety_boundary",
    }
    assert graph.primary_state.text
    assert graph.core_tensions
    assert graph.pressure_sources
    assert graph.limit_signals
    assert graph.self_awareness
    assert "Mashさん、Emlisです。" in text
    assert "あなた" not in text
    assert "今の私は" not in text
    assert "そこには" not in text
    assert "含まれていました" not in text
    assert "受け取りました" not in text
    assert "と思います" not in text
    assert reader.understandable is True
    assert grounding.passed is True
    assert template.passed is True
    assert decision.observation_status == "passed"
    assert decision.comment_text == text


def test_reader_and_template_guard_reject_broken_legacy_text():
    broken = """
Emlisです。
今の私は、誰かと繋がっていたい気持ちとここを入口にしながら、そこには、ここにいていいんだってことも含まれていました。
そこには、心細さもありました。
""".strip()
    evidence = build_evidence_ledger({"memo": "誰かと繋がりたいけど一人で静かにしたい", "emotion_details": []})
    reader = judge_listener_readability(broken)
    template = guard_template_echo(comment_text=broken, evidence_spans=evidence)

    assert reader.understandable is False
    assert "first_person_hijack" in reader.rejection_reasons
    assert template.passed is False
    assert template.matched_banned_patterns


def test_display_gate_is_fail_closed_for_safety_boundary():
    evidence = build_evidence_ledger({"memo": "消えたい気持ちが強い", "emotion_details": [{"type": "不安"}]})
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    text = compose_emlis_conversation(graph=graph, evidence_spans=evidence, display_name="Mash")
    reader = judge_listener_readability(text)
    grounding = judge_grounding(comment_text=text, graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text=text, evidence_spans=evidence)
    decision = decide_emlis_observation_display(
        comment_text=text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        safety_report=SafetyBoundaryReport(requires_block=True, reasons=["safety_boundary"]),
        trace_id="safety-test",
    )

    assert decision.observation_status == "safety_blocked"
    assert decision.comment_text == ""
    assert "safety_boundary" in decision.rejection_reasons
