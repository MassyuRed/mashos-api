from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from emlis_ai_conversation_composer_service import compose_emlis_conversation
from emlis_ai_display_gate import decide_emlis_observation_display
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_template_echo_guard import guard_template_echo


@dataclass
class MultiPerspectiveRun:
    current_input: Dict[str, Any]
    evidence: list
    reports: list
    board: Any
    graph: Any
    text: str
    reader: Any
    grounding: Any
    template: Any
    decision: Any


def run_multi_perspective_case(
    memo: str,
    *,
    display_name: str = "Mash",
    emotion: str = "自己理解",
    category: str = "生活",
    memo_action: str = "",
) -> MultiPerspectiveRun:
    current_input = {
        "id": "emo-test",
        "created_at": "2026-05-09T00:00:00Z",
        "memo": memo,
        "memo_action": memo_action,
        "emotion_details": [{"type": emotion, "strength": "medium"}],
        "emotions": [emotion],
        "category": [category],
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
    return MultiPerspectiveRun(current_input, evidence, reports, board, graph, text, reader, grounding, template, decision)


def assert_no_legacy_observation_text(text: str) -> None:
    banned = [
        "あなたは",
        "あなたの",
        "あなたが",
        "あなたに",
        "今の私は",
        "そこには",
        "含まれていました",
        "受け取りました",
        "と思います",
        "として見ています",
        "小さく扱いません",
        "軽く扱いません",
        "弱さではなく",
    ]
    for phrase in banned:
        assert phrase not in text
