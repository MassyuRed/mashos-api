from __future__ import annotations

import pytest

from emlis_ai_evidence_ledger_service import build_evidence_ledger, source_text_for_span
from emlis_ai_perspective_observers import expected_phase4_observer_ids, phase4_observer_contract_ready, run_perspective_observers
from emlis_ai_perspective_board import build_perspective_board, phase5_board_contract_ready, validate_perspective_board
from emlis_ai_observation_integrator_service import integrate_perspective_board, phase5_integrator_contract_ready, validate_observation_graph
from emlis_ai_conversation_composer_service import (
    audit_runtime_fixed_string_renderer,
    build_conversation_composer_payload,
    compose_emlis_conversation,
    compose_emlis_conversation_candidate,
    phase6_composer_contract_ready,
)
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_display_gate import build_emlis_gate_trace, decide_emlis_observation_display, phase7_judge_contract_ready, phase8_display_gate_contract_ready
from emlis_ai_types import SafetyBoundaryReport


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _input(memo: str, *, display_name: str = "Mash"):
    return {
        "id": "emo-test",
        "created_at": "2026-05-09T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
        "display_name": display_name,
    }


def _run(memo: str, *, display_name: str = "Mash"):
    current_input = _input(memo, display_name=display_name)
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
        composer_source="phase_5_integrator_ready_composer_not_connected",
        phase_completion_ready=False,
    )
    return current_input, evidence, reports, graph, text, reader, grounding, template, decision


def test_phase3_evidence_ledger_keeps_source_spans_without_interpretation():
    current_input, evidence, *_ = _run(SAMPLE_MEMO)

    assert len(evidence) >= 6
    memo_spans = [span for span in evidence if span.source_field == "memo"]
    assert memo_spans
    for span in memo_spans:
        source = source_text_for_span(current_input, span)
        assert source
        assert span.raw_text == source.strip()
        assert 0 <= span.start_index < span.end_index <= len(current_input["memo"])
        assert 0.0 <= span.confidence <= 1.0
        assert "本当は" not in span.raw_text
        assert "つまり" not in span.raw_text

    assert {span.detected_type for span in evidence} & {"wish", "constraint", "self_awareness", "limit_signal", "emotion"}


def test_phase4_specialist_observers_return_structured_reports_without_body_text():
    _, evidence, reports, *_ = _run(SAMPLE_MEMO)

    assert len(evidence) >= 6
    assert tuple(report.observer_id for report in reports) == expected_phase4_observer_ids()
    assert phase4_observer_contract_ready(reports, evidence) is True

    reports_by_id = {report.observer_id: report for report in reports}
    assert reports_by_id["explicit_content"].claims
    assert reports_by_id["emotion_state"].claims
    assert reports_by_id["conflict_coexistence"].claims
    assert reports_by_id["conflict_coexistence"].relations
    assert reports_by_id["pressure_constraint"].claims
    assert reports_by_id["limit_signal"].claims
    assert reports_by_id["self_awareness"].claims
    assert reports_by_id["value_strength"].claims
    assert reports_by_id["addressee_model"].claims

    for report in reports:
        assert hasattr(report, "claims")
        assert hasattr(report, "relations")
        assert hasattr(report, "evidence_span_ids")
        assert not hasattr(report, "comment_text")
        assert not hasattr(report, "body")
        assert not hasattr(report, "reply_text")
        for claim in report.claims:
            assert claim.evidence_span_ids
            assert "Emlis" not in str(claim.object or "")
            assert "見ています" not in str(claim.object or "")
            assert "受け取りました" not in str(claim.object or "")
        for edge in report.relations:
            assert edge.evidence_span_ids


def test_phase5_perspective_board_and_integrator_create_graph_without_body_text():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)

    assert phase5_board_contract_ready(board) is True
    assert validate_perspective_board(board) == []
    assert board.report_ids == list(expected_phase4_observer_ids())
    assert board.claim_ids
    assert board.relation_ids
    assert board.evidence_span_ids == [span.span_id for span in evidence]

    assert phase5_integrator_contract_ready(board, graph) is True
    assert validate_observation_graph(graph, board) == []
    assert graph.primary_state.text
    assert graph.core_tensions
    assert graph.pressure_sources
    assert graph.limit_signals
    assert graph.self_awareness
    assert graph.forbidden_claims
    assert graph.addressee_notes.avoid_report_like is True
    graph_surface = "\n".join([
        graph.primary_state.text,
        *(claim.text for claim in graph.pressure_sources),
        *(claim.text for claim in graph.limit_signals),
        *(claim.text for claim in graph.self_awareness),
    ])
    assert "Emlisです" not in graph_surface
    assert "一緒に見ます" not in graph_surface
    assert "そこには" not in graph_surface


def test_multi_perspective_reports_and_graph_are_created_but_body_remains_closed_until_composer_phase():
    _, evidence, reports, graph, text, reader, grounding, template, decision = _run(SAMPLE_MEMO)

    assert len(evidence) >= 6
    assert {report.observer_id for report in reports} >= set(expected_phase4_observer_ids())
    assert graph.primary_state.text
    assert graph.core_tensions
    assert graph.pressure_sources
    assert graph.limit_signals
    assert graph.self_awareness
    assert text == ""
    assert reader.understandable is False
    assert grounding.passed is False
    assert template.passed is True
    assert decision.observation_status == "unavailable"
    assert decision.comment_text == ""
    assert "phase_not_complete" in decision.rejection_reasons
    assert "composer_source_not_ai_generated" in decision.rejection_reasons




def test_phase6_composer_contract_builds_structural_payload_without_fixed_body_text():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    payload = build_conversation_composer_payload(
        graph=graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
    )

    assert phase6_composer_contract_ready() is True
    assert payload["schema_version"] == "emlis.composer.request.v1"
    assert payload["composition_contract"]["do_not_use_fixed_templates"] is True
    assert payload["composition_contract"]["do_not_use_examples"] is True
    assert payload["composition_contract"]["do_not_use_fallback_observation"] is True
    assert payload["observation_graph"]["primary_state"]["text"]
    assert len(payload["evidence_spans"]) >= 6

    structural_surface = str({
        "observation_graph": payload["observation_graph"],
        "evidence_spans": payload["evidence_spans"],
    })
    for banned in ("含まれていました", "受け取りました", "と思います", "一緒に見ます"):
        assert banned not in structural_surface
    assert "そこには" in payload["composition_contract"]["forbidden_output_surfaces"]


def test_phase6_composer_accepts_ai_generated_candidate_but_display_stays_closed_until_judges_complete():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    assert phase5_board_contract_ready(board) is True
    assert phase5_integrator_contract_ready(board, graph) is True

    class FakeComposerAI:
        def generate(self, payload):
            assert payload["schema_version"] == "emlis.composer.request.v1"
            assert payload["composition_contract"]["do_not_use_fixed_templates"] is True
            return {
                "response_schema_version": "emlis.composer.response.v1",
                "composer_source": "ai_generated",
                "confidence": 0.91,
                "comment_text": "Mashさん、Emlisです。\n家で整えたい気持ちと、現実に戻る重さが同じ中にあります。\n普通に過ごしたい願いと、悪化すると分かっている自覚が並んでいます。\n逃げたい感覚も、その二つの間で張りつめてきた反応として置かれています。",
                "used_evidence_span_ids": [span.span_id for span in evidence[:3]],
            }

    candidate = compose_emlis_conversation_candidate(
        graph=graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=FakeComposerAI(),
        trace_id="phase6-test",
    )
    assert candidate.composer_source == "ai_generated"
    assert candidate.status == "generated"
    assert candidate.comment_text
    assert candidate.trace_id == "phase6-test"

    reader = judge_listener_readability(candidate.comment_text)
    grounding = judge_grounding(comment_text=candidate.comment_text, graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text=candidate.comment_text, evidence_spans=evidence)
    decision = decide_emlis_observation_display(
        comment_text=candidate.comment_text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        trace_id="phase6-test",
        composer_source=candidate.composer_source,
        phase_completion_ready=False,
    )

    assert "そこには" not in candidate.comment_text
    assert "と思います" not in candidate.comment_text
    assert decision.observation_status == "unavailable"
    assert decision.comment_text == ""
    assert "phase_not_complete" in decision.rejection_reasons

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

    assert text == ""
    assert decision.observation_status == "safety_blocked"
    assert decision.comment_text == ""
    assert "safety_boundary" in decision.rejection_reasons


class _FakeComposerAI:
    def __init__(self, text: str):
        self.text = text
        self.payload = None

    def generate(self, payload):
        self.payload = payload
        return {
            "comment_text": self.text,
            "used_evidence_span_ids": ["s2", "s5", "s9"],
            "confidence": 0.91,
        }


def test_phase6_composer_ai_candidate_is_generated_but_display_stays_closed_until_judges_complete():
    current_input = _input(SAMPLE_MEMO, display_name="Mash")
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")

    ai_text = (
        "Mashさん、Emlisです。\n"
        "リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
        "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
    )
    fake_ai = _FakeComposerAI(ai_text)

    assert phase5_integrator_contract_ready(board, graph) is True
    assert phase6_composer_contract_ready() is True
    assert audit_runtime_fixed_string_renderer() == []

    payload = build_conversation_composer_payload(
        graph=graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="phase6-test",
    )
    assert payload["schema_version"] == "emlis.composer.request.v1"
    assert payload["composition_contract"]["do_not_use_examples"] is True
    assert payload["composition_contract"]["do_not_use_fixed_templates"] is True
    assert payload["composition_contract"]["return_schema_version"] == "emlis.composer.response.v1"

    candidate = compose_emlis_conversation_candidate(
        graph=graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=fake_ai,
        trace_id="phase6-test",
    )

    assert candidate.comment_text == ai_text
    assert candidate.composer_source == "ai_generated"
    assert candidate.status == "generated"
    assert candidate.ai_generated is True
    assert candidate.fixed_string_renderer_used is False
    assert fake_ai.payload is not None
    assert "reply_examples" not in fake_ai.payload
    assert "sample_reply" not in fake_ai.payload

    reader = judge_listener_readability(candidate.comment_text)
    grounding = judge_grounding(comment_text=candidate.comment_text, graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text=candidate.comment_text, evidence_spans=evidence)
    decision = decide_emlis_observation_display(
        comment_text=candidate.comment_text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        trace_id="phase6-test",
        composer_source=candidate.composer_source,
        phase_completion_ready=False,
    )

    assert reader.understandable is True
    assert grounding.passed is True
    assert template.passed is True
    assert decision.observation_status == "unavailable"
    assert decision.comment_text == ""
    assert "phase_not_complete" in decision.rejection_reasons
    assert "composer_source_not_ai_generated" not in decision.rejection_reasons


def test_phase6_no_composer_client_remains_fail_closed_without_static_body():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    candidate = compose_emlis_conversation_candidate(
        graph=graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=None,
        trace_id="phase6-no-client",
    )

    assert candidate.comment_text == ""
    assert candidate.composer_source == "unavailable"
    assert candidate.status == "unavailable"
    assert candidate.ai_generated is False
    assert "composer_client_not_connected" in candidate.rejection_reasons



def test_phase7_judges_create_traceable_pass_fail_for_grounded_ai_candidate():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    text = (
        "Mashさん、Emlisです。\n"
        "リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
        "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
    )
    reader = judge_listener_readability(text)
    grounding = judge_grounding(comment_text=text, graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text=text, evidence_spans=evidence, composer_source="ai_generated")
    trace = build_emlis_gate_trace(
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        composer_source="ai_generated",
        phase_completion_ready=False,
    )

    assert reader.understandable is True
    assert grounding.passed is True
    assert template.passed is True
    assert phase7_judge_contract_ready(
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        composer_source="ai_generated",
    ) is True
    assert trace["reader"]["passed"] is True
    assert trace["grounding"]["passed"] is True
    assert trace["template_echo"]["passed"] is True
    assert trace["generation_source"]["passed"] is True
    assert trace["phase_completion"]["passed"] is False
    assert trace["phase_completion"]["rejection_reasons"] == ["phase_not_complete"]

    decision = decide_emlis_observation_display(
        comment_text=text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        trace_id="phase7-test",
        composer_source="ai_generated",
        phase_completion_ready=False,
    )
    assert decision.observation_status == "unavailable"
    assert decision.comment_text == ""
    assert decision.gate_trace["reader"]["passed"] is True
    assert "phase_not_complete" in decision.rejection_reasons


def test_phase7_grounding_rejects_unsupported_claim_even_when_relation_words_exist():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    unsupported_text = (
        "Mashさん、Emlisです。\n"
        "本当は誰かに頼りたい気持ちと、前向きに変われる強さが同じ場所にあります。\n"
        "それでも関係を整える力が残っています。"
    )
    reader = judge_listener_readability(unsupported_text)
    grounding = judge_grounding(comment_text=unsupported_text, graph=graph, evidence_spans=evidence)

    assert reader.addressee_clear is True
    assert grounding.passed is False
    assert "unsupported_sentence" in grounding.rejection_reasons
    assert any(claim.unsupported_reason for claim in grounding.sentence_claims)


def test_phase7_template_guard_rejects_rule_rendered_and_new_template_surfaces():
    evidence = build_evidence_ledger(_input("悲しい。何かしてあげたいけど出来なくてゲンナリする。"))
    rule_rendered = (
        "Mashさん、Emlisです。\n"
        "入力全体では、「何かしてあげたいけど出来なくてゲンナリ」が中心に出ています。\n"
        "言葉の流れには、外からは見えにくい緊張が含まれています。\n"
        "Emlisは、「何かしてあげたいけど出来なくてゲンナリ」を急いで片づけず、今の言葉として一緒に見ます。"
    )
    template = guard_template_echo(
        comment_text=rule_rendered,
        evidence_spans=evidence,
        composer_source="rule_rendered",
    )

    assert template.passed is False
    assert "composer_source_not_ai_generated" in template.rejection_reasons
    assert "rule_rendered_or_fallback_source" in template.rejection_reasons
    assert "banned_legacy_pattern" in template.rejection_reasons
    assert template.matched_banned_patterns


def test_phase8_display_gate_passes_only_when_all_gates_pass_and_phase_ready():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    text = (
        "Mashさん、Emlisです。\n"
        "リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
        "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
    )
    reader = judge_listener_readability(text)
    grounding = judge_grounding(comment_text=text, graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text=text, evidence_spans=evidence, composer_source="ai_generated")

    decision = decide_emlis_observation_display(
        comment_text=text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        trace_id="phase8-pass",
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    assert reader.understandable is True
    assert grounding.passed is True
    assert template.passed is True
    assert decision.observation_status == "passed"
    assert decision.comment_text == text
    assert decision.rejection_reasons == []
    assert decision.gate_trace["display_gate"]["passed"] is True
    assert decision.gate_trace["phase_completion"]["passed"] is True
    assert phase8_display_gate_contract_ready(decision) is True


def test_phase8_display_gate_blocks_any_failed_gate_with_empty_comment_text():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    template_text = (
        "Mashさん、Emlisです。\n"
        "入力全体では、『悲しみ』が中心に出ています。\n"
        "言葉の流れには、外からは見えにくい緊張が含まれています。\n"
        "Emlisは、『悲しみ』を急いで片づけず、今の言葉として一緒に見ます。"
    )
    reader = judge_listener_readability(template_text)
    grounding = judge_grounding(comment_text=template_text, graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text=template_text, evidence_spans=evidence, composer_source="ai_generated")

    decision = decide_emlis_observation_display(
        comment_text=template_text,
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        trace_id="phase8-block",
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    assert decision.observation_status == "rejected"
    assert decision.comment_text == ""
    assert decision.rejection_reasons
    assert decision.gate_trace["display_gate"]["passed"] is False
    assert phase8_display_gate_contract_ready(decision) is True


def test_phase8_display_gate_treats_unavailable_composer_as_unavailable_without_fallback():
    _, evidence, reports, graph, *_ = _run(SAMPLE_MEMO)
    reader = judge_listener_readability("")
    grounding = judge_grounding(comment_text="", graph=graph, evidence_spans=evidence)
    template = guard_template_echo(comment_text="", evidence_spans=evidence, composer_source="unavailable")

    decision = decide_emlis_observation_display(
        comment_text="",
        reader_report=reader,
        grounding_report=grounding,
        template_echo_report=template,
        trace_id="phase8-unavailable",
        composer_source="unavailable",
        phase_completion_ready=True,
    )

    assert decision.observation_status == "unavailable"
    assert decision.comment_text == ""
    assert "composer_source_not_ai_generated" in decision.rejection_reasons
    assert "empty_comment_text" in decision.rejection_reasons
    assert phase8_display_gate_contract_ready(decision) is True


@pytest.mark.asyncio
async def test_phase8_reply_orchestrator_allows_comment_text_only_after_display_gate_passes():
    from emlis_ai_reply_service import render_emlis_ai_reply

    text = (
        "Mashさん、Emlisです。\n"
        "リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
        "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
    )

    class FakeComposerAI:
        def generate(self, payload):
            return {
                "response_schema_version": "emlis.composer.response.v1",
                "composer_source": "ai_generated",
                "confidence": 0.91,
                "comment_text": text,
                "used_evidence_span_ids": [item["span_id"] for item in payload["evidence_spans"][:4]],
            }

    envelope = await render_emlis_ai_reply(
        user_id="phase8-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO, display_name="Mash"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=FakeComposerAI(),
    )

    phase_gate = envelope.meta["multi_perspective"]["phase_gate"]
    assert envelope.comment_text == text
    assert envelope.meta["observation_status"] == "passed"
    assert phase_gate["completed_phases"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert phase_gate["current_phase"] == 10
    assert phase_gate["next_phase"] is None
    assert phase_gate["display_gate_ready"] is True
    assert phase_gate["display_gate_release_ready"] is True
    assert phase_gate["frontend_display_control_ready"] is True
    assert phase_gate["phase9_frontend_display_control_ready"] is True
    assert phase_gate["phase10_regression_release_ready"] is True
    assert phase_gate["comment_text_allowed"] is True
    assert phase_gate["release_ready"] is True
    assert phase_gate["release_blockers"] == []
    assert phase_gate["gate_trace"]["display_gate"]["passed"] is True


@pytest.mark.asyncio
async def test_phase8_reply_orchestrator_keeps_empty_comment_when_composer_is_unavailable():
    from emlis_ai_reply_service import render_emlis_ai_reply

    envelope = await render_emlis_ai_reply(
        user_id="phase8-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO, display_name="Mash"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=None,
    )

    phase_gate = envelope.meta["multi_perspective"]["phase_gate"]
    assert envelope.comment_text == ""
    assert envelope.meta["observation_status"] == "unavailable"
    assert phase_gate["completed_phases"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert phase_gate["current_phase"] == 10
    assert phase_gate["next_phase"] is None
    assert phase_gate["display_gate_ready"] is True
    assert phase_gate["frontend_display_control_ready"] is True
    assert phase_gate["phase10_regression_release_ready"] is True
    assert phase_gate["release_ready"] is True
    assert phase_gate["comment_text_allowed"] is False
    assert phase_gate["gate_trace"]["display_gate"]["passed"] is False
    assert "composer_source_unavailable" in envelope.meta["rejection_reasons"]



def test_phase10_release_readiness_requires_frontend_and_regression_contracts():
    from emlis_ai_display_gate import build_phase10_release_readiness, phase10_release_readiness_contract_ready

    ready = build_phase10_release_readiness(frontend_display_control_ready=True)
    assert ready["release_ready"] is True
    assert ready["required_completed_phases"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert ready["phase9_frontend_display_control_ready"] is True
    assert ready["phase10_regression_release_ready"] is True
    assert ready["release_blockers"] == []
    assert phase10_release_readiness_contract_ready(frontend_display_control_ready=True) is True

    blocked = build_phase10_release_readiness(
        frontend_display_control_ready=False,
        release_checks={"phase10_screenshot_regression": False},
    )
    assert blocked["release_ready"] is False
    assert "frontend_passed_only_display_not_verified" in blocked["release_blockers"]
    assert "phase10_screenshot_regression" in blocked["release_blockers"]
    assert phase10_release_readiness_contract_ready(
        frontend_display_control_ready=False,
        release_checks={"phase10_screenshot_regression": False},
    ) is False
