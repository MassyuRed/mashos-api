from __future__ import annotations

import ast
import inspect

import emlis_ai_limited_composer_client as limited_composer_module
from emlis_ai_conversation_composer_service import (
    compose_emlis_conversation_candidate,
    phase6_composer_contract_ready,
)
from emlis_ai_display_gate import (
    build_phase10_release_readiness,
    decide_emlis_observation_display,
    phase8_display_gate_contract_ready,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient, audit_limited_composer_contract
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_types import GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


_ALLOWED_STATIC_GUARD_TABLES = {"_FORBIDDEN_SURFACES", "_MARKER_NAMES"}


def _limited_composer_source_without_static_guard_tables() -> str:
    source = inspect.getsource(limited_composer_module)
    tree = ast.parse(source)
    suppressed_lines: set[int] = set()
    for node in tree.body:
        target_names: set[str] = set()
        if isinstance(node, ast.Assign):
            target_names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_names = {node.target.id}
        if not target_names.intersection(_ALLOWED_STATIC_GUARD_TABLES):
            continue
        start = int(getattr(node, "lineno", 0) or 0)
        end = int(getattr(node, "end_lineno", start) or start)
        suppressed_lines.update(range(start, end + 1))
    return "\n".join(
        line
        for line_no, line in enumerate(source.splitlines(), start=1)
        if line_no not in suppressed_lines
    )


def _scoped_case():
    current_input = {
        "id": "phase6-emotion",
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
    assert scope.excluded_claims
    return evidence, full_graph, scope


def _allowed_ids_from_scope(scope) -> list[str]:
    out: list[str] = []
    for value in list(scope.scoped_graph.primary_state.evidence_span_ids or []):
        if value not in out:
            out.append(value)
    for group in (
        scope.scoped_graph.pressure_sources,
        scope.scoped_graph.limit_signals,
        scope.scoped_graph.self_awareness,
        scope.scoped_graph.value_or_strength_signals,
    ):
        for claim in group:
            for value in list(claim.evidence_span_ids or []):
                if value not in out:
                    out.append(value)
    for edge in scope.scoped_graph.core_tensions:
        for value in list(edge.evidence_span_ids or []):
            if value not in out:
                out.append(value)
    return out


def test_phase6_limited_composer_static_renderer_contract_stays_sealed():
    assert phase6_composer_contract_ready() is True
    assert audit_limited_composer_contract() == []

    source = _limited_composer_source_without_static_guard_tables()
    class_source = inspect.getsource(CocolonLimitedComposerClient)

    assert "class CocolonLimitedComposerClient" in source
    assert "def _compress_text" in source
    assert "def _compress_text" not in class_source

    forbidden_runtime_markers = (
        "_line_primary",
        "_line_pressure",
        "_line_limit",
        "_line_closing",
        "closing_template",
        "role_template",
        "static_observation_text",
        "fallback_observation",
    )
    for marker in forbidden_runtime_markers:
        assert marker not in source

    forbidden_surfaces = (
        "そこには",
        "もありました",
        "も含まれていました",
        "として見ています",
        "一緒に見ます",
        "今の私は",
        "あなたは",
    )
    for surface in forbidden_surfaces:
        assert surface not in source


def test_phase6_b_can_pass_partial_observation_and_keep_a_expansion_meta():
    evidence, full_graph, scope = _scoped_case()
    scoped_ids = _allowed_ids_from_scope(scope)
    full_claim_ids = {
        full_graph.primary_state.claim_id,
        *(claim.claim_id for claim in full_graph.pressure_sources),
        *(claim.claim_id for claim in full_graph.limit_signals),
        *(claim.claim_id for claim in full_graph.self_awareness),
        *(claim.claim_id for claim in full_graph.value_or_strength_signals),
    }

    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=CocolonLimitedComposerClient(),
        trace_id="phase6-partial-pass",
        limited_observation_scope=scope,
    )

    assert candidate.composer_source == "ai_generated"
    assert candidate.composer_model == "cocolon_limited_composer.v1"
    assert candidate.fixed_string_renderer_used is False
    assert candidate.coverage_scope == "partial_observation"
    assert set(candidate.used_evidence_span_ids).issubset(set(scoped_ids))
    assert set(candidate.used_claim_ids).issubset(set(scope.included_claim_ids))
    assert set(candidate.used_relation_ids).issubset(set(scope.included_relation_ids))
    assert set(candidate.used_claim_ids) != full_claim_ids
    assert [item.reason_code for item in scope.excluded_claims]

    reader = judge_listener_readability(candidate.comment_text)
    grounding = judge_grounding(
        comment_text=candidate.comment_text,
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        allowed_evidence_span_ids=scoped_ids,
        grounding_scope="limited_scoped_graph",
    )
    template = guard_template_echo(
        comment_text=candidate.comment_text,
        evidence_spans=evidence,
        composer_source=candidate.composer_source,
        composer_model=candidate.composer_model,
        generation_method=candidate.generation_method,
        generation_scope=candidate.generation_scope,
        coverage_scope=candidate.coverage_scope,
        composer_meta=candidate.composer_meta,
        used_evidence_span_ids=candidate.used_evidence_span_ids,
    )
    decision = decide_emlis_observation_display(
        comment_text=candidate.comment_text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        composer_source=candidate.composer_source,
        phase_completion_ready=True,
        trace_id="phase6-partial-pass",
    )

    assert reader.understandable is True
    assert grounding.passed is True
    assert grounding.grounding_scope == "limited_scoped_graph"
    assert grounding.allowed_evidence_span_ids == scoped_ids
    assert template.passed is True
    assert template.raw_quote_span_count <= 1
    assert template.raw_quote_char_ratio < 0.25
    assert not template.matched_limited_surface_patterns
    assert decision.observation_status == "passed"
    assert decision.comment_text == candidate.comment_text
    assert phase8_display_gate_contract_ready(decision) is True


def test_phase6_non_passed_observation_never_exposes_comment_text():
    passing_reader = ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        confidence=1.0,
    )
    passing_grounding = GroundingReport(passed=True, coverage_ratio=1.0, confidence=1.0)
    passing_template = TemplateEchoReport(passed=True)

    rule_rendered = decide_emlis_observation_display(
        comment_text="固定文で作った候補です。",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        composer_source="rule_rendered",
        phase_completion_ready=True,
    )
    unavailable = decide_emlis_observation_display(
        comment_text="",
        reader_report=ListenerReaderReport(
            understandable=False,
            addressee_clear=False,
            speaker_integrity_ok=False,
            conversational=False,
            report_like=True,
            rejection_reasons=["reader_cannot_understand"],
        ),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["empty_text"]),
        template_echo_report=passing_template,
        composer_source="unavailable",
        phase_completion_ready=True,
    )
    safety = decide_emlis_observation_display(
        comment_text="安全境界でも本文を出すべきではありません。",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        safety_report=SafetyBoundaryReport(requires_block=True, reasons=["safety_boundary"]),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    for decision in (rule_rendered, unavailable, safety):
        assert decision.observation_status in {"rejected", "unavailable", "safety_blocked"}
        assert decision.comment_text == ""
        assert decision.gate_trace["display_gate"]["comment_text_allowed"] is False
        assert phase8_display_gate_contract_ready(decision) is True


def test_phase6_release_readiness_requires_regression_checklist():
    passing_decision = decide_emlis_observation_display(
        comment_text="Mashさん、Emlisです。\n今の生活の不便さ、そんなの分かっている自覚がつながっています。",
        reader_report=ListenerReaderReport(
            understandable=True,
            addressee_clear=True,
            speaker_integrity_ok=True,
            conversational=True,
            report_like=False,
            confidence=1.0,
        ),
        grounding_report=GroundingReport(passed=True, coverage_ratio=1.0, confidence=1.0),
        template_echo_report=TemplateEchoReport(passed=True),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    ready = build_phase10_release_readiness(
        display_decision=passing_decision,
        frontend_display_control_ready=True,
    )
    blocked_by_frontend = build_phase10_release_readiness(
        display_decision=passing_decision,
        frontend_display_control_ready=False,
    )
    blocked_by_regression = build_phase10_release_readiness(
        display_decision=passing_decision,
        frontend_display_control_ready=True,
        release_checks={"phase10_fixed_string_regression": False},
    )

    assert ready["phase10_regression_release_ready"] is True
    assert ready["release_ready"] is True
    assert blocked_by_frontend["release_ready"] is False
    assert "frontend_passed_only_display_not_verified" in blocked_by_frontend["release_blockers"]
    assert blocked_by_regression["release_ready"] is False
    assert "phase10_fixed_string_regression" in blocked_by_regression["release_blockers"]
