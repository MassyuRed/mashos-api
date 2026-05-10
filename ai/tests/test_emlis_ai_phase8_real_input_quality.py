# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from emlis_ai_conversation_composer_service import build_conversation_composer_payload
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_limited_sentence_quality_guard import detect_phase8_profile
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_template_echo_guard import guard_template_echo
from fixtures.emlis_ai_phase8_cases import PHASE8_CASES, PHASE8_FORBIDDEN_SURFACES


def _current_input(case: dict) -> dict:
    return {
        "id": f"phase8-{case['case_id']}",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": case["memo"],
        "memo_action": "",
        "emotion_details": [{"type": case.get("emotion") or "自己理解", "strength": "medium"}],
        "emotions": [case.get("emotion") or "自己理解"],
        "category": [case.get("category") or "生活"],
    }


def _candidate_for(case: dict):
    evidence = build_evidence_ledger(_current_input(case))
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id=f"phase8-{case['case_id']}",
    )
    return CocolonLimitedComposerClient().generate(payload), evidence, scope


def _compact(value: str) -> str:
    for ch in "\n\r\t 　、,。.!！?？『』「」（）()[]【】":
        value = value.replace(ch, "")
    return value


@pytest.mark.parametrize("case", PHASE8_CASES, ids=[case["case_id"] for case in PHASE8_CASES])
def test_phase8_real_input_profiles_and_output_quality(case):
    candidate, evidence, scope = _candidate_for(case)
    assert detect_phase8_profile(evidence) == case["expected_profile"]

    if not case["expected_passed"]:
        assert candidate["composer_source"] == "unavailable"
        assert candidate["comment_text"] == ""
        assert "short_ambiguous" in " ".join(candidate.get("rejection_reasons") or [candidate.get("composer_meta", {}).get("profile_key", "")])
        return

    assert scope.scope_status == "eligible"
    assert candidate["composer_source"] == "ai_generated"
    assert candidate["composer_model"] == "cocolon_limited_composer.v1"
    assert candidate["comment_text"]
    assert candidate["composer_meta"]["profile_key"] == case["expected_profile"]
    assert candidate["composer_meta"]["body_line_count"] >= 2

    text = candidate["comment_text"]
    compact = _compact(text)
    for forbidden in PHASE8_FORBIDDEN_SURFACES:
        assert forbidden not in text
    for alternatives in case["must_contain_any"]:
        assert any(_compact(term) in compact for term in alternatives), (case["case_id"], alternatives, text)

    guard = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )
    assert guard.passed is True
    assert not guard.phase8_quality_rejection_reasons


def test_phase8_current_bad_outputs_are_rejected_by_guard():
    evidence = build_evidence_ledger(_current_input(PHASE8_CASES[-1]))
    bad_outputs = [
        "Emlisです。\n不安。\nまた急に不安になったがつながっています。",
        "Emlisです。\n怒り。\nこっちはちゃんと考えて話してるのに、なんであがつながっています。",
        "Emlisです。\n自己理解。\n先のことを考え始めがつながっています。",
        "Emlisです。\n生活したい、そうしたらもっと悪化するが同じ中にあります。",
    ]
    for output in bad_outputs:
        guard = guard_template_echo(
            comment_text=output,
            evidence_spans=evidence,
            composer_source="ai_generated",
            composer_model="cocolon_limited_composer.v1",
            generation_method="scoped_graph_evidence_composer",
            generation_scope="scoped_graph_only",
            coverage_scope="partial_observation",
            composer_meta={"limited_composer": True},
            used_evidence_span_ids=[],
        )
        assert guard.passed is False
        assert any(str(reason).startswith("phase8_") for reason in guard.rejection_reasons)
