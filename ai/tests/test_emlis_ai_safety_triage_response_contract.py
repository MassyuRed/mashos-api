# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-2 guard: safety triage is not a one-bit safety_blocked switch."""

from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_response_contract import EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY
from emlis_ai_safety_boundary_service import (
    build_emlis_safety_boundary_decision,
    classify_safety_boundary_text,
)
from emlis_ai_safety_triage import (
    assert_emlis_safety_triage_meta,
    build_emlis_internal_response_contract_from_safety_triage,
    build_emlis_safety_triage_decision,
)
from emlis_ai_response_contract import response_kind_for_safety_triage_kind
from emlis_ai_self_denial_safe_state_answer import build_self_denial_safe_state_answer_result
from emlis_ai_types import EvidenceSpan, GraphClaim, ObservationGraph


def test_bad_attributive_object_is_not_speaker_appraisal() -> None:
    from emlis_ai_grounded_observation_plan import _operator_codes_for_text
    from emlis_ai_safety_triage import is_bounded_self_denial_text, classify_emlis_safety_triage_text
    for subject in ('私', 'わたし', '僕', 'ぼく', '自分', '俺', 'おれ'):
        for noun in ('家族の悪い取り組み', '悪い取り組み', '悪い学びノートの長い振り返り',
                     '悪い資料の内容', '家族の悪い考え'):
            text = subject + 'は' + noun + 'を守りたいけれど、' + subject + 'はつらい。'
            assert not is_bounded_self_denial_text(text), text
            assert 'operator:self_evaluation' not in _operator_codes_for_text(text), text
            assert classify_emlis_safety_triage_text(text).safety_triage_kind == 'safe_observation'


def test_bad_object_does_not_hide_self_denial_or_emergency() -> None:
    from emlis_ai_grounded_observation_plan import _operator_codes_for_text
    from emlis_ai_safety_triage import is_bounded_self_denial_text, classify_emlis_safety_triage_text
    wish = '私は家族の悪い取り組みを守りたい。'
    for appraisal in ('私は悪い。', '私は悪いと思う。', '私は悪いから謝った。',
                      '私は悪い人間だ。', '私は悪い自分を変えたい。', '私は悪い人間をやめたい。',
                      '僕は悪い僕自身を変えたい。', '俺は悪い俺自身を変えたい。',
                      '私は悪い人間性を直したい。', '私は悪い人格を変えたい。',
                      '私はダメ。', '自分には価値がない。', '自分を責め続けている。'):
        for text in (appraisal, appraisal + wish, wish + appraisal):
            assert is_bounded_self_denial_text(text), text
            assert 'operator:self_evaluation' in _operator_codes_for_text(text), text
            assert classify_emlis_safety_triage_text(text).safety_triage_kind == 'self_denial_safe_state_answer'
    for text in ('私はダメだけど悪い取り組みを守りたい。',
                 '私は悪い取り組みを守りたいけれど私は悪い。',
                 '私は悪い取り組みを守りたいけれど自分には価値がない。'):
        assert is_bounded_self_denial_text(text), text
        assert 'operator:self_evaluation' in _operator_codes_for_text(text), text
    for unresolved in ('私は悪い取り組み。', '私は悪い取り組みの。', '私は悪いやり方を変えたい。'):
        assert is_bounded_self_denial_text(unresolved), unresolved
    for text in ('私は悪く思う。', '私は弱い。', '私は遅い。'):
        assert 'operator:self_evaluation' in _operator_codes_for_text(text), text
    for signal, kind in (('死にたい。', 'safety_blocked_emergency'),
                         ('助けが必要。', 'safety_support_required')):
        for text in (signal + wish, wish + signal):
            assert classify_emlis_safety_triage_text(text).safety_triage_kind == kind, text


def test_bad_past_location_is_not_speaker_appraisal() -> None:
    from emlis_ai_grounded_observation_plan import _operator_codes_for_text
    from emlis_ai_safety_triage import is_bounded_self_denial_text, classify_emlis_safety_triage_text
    for subject in ('私', 'わたし', '僕', 'ぼく', '自分', '俺', 'おれ'):
        for noun in ('悪い職場', '家族の悪い職場', '悪い会社の新しい職場'):
            for ending in ('いた', 'いました', 'いなかった', 'いなかったです', 'いませんでした'):
                for stop in ('', '。', '．', '.', '!', '！', '?', '？'):
                    text = subject + 'は' + noun + 'に' + ending + stop
                    assert not is_bounded_self_denial_text(text), text
                    assert 'operator:self_evaluation' not in _operator_codes_for_text(text), text
                    assert classify_emlis_safety_triage_text(text).safety_triage_kind == 'safe_observation'


def test_bad_past_location_does_not_hide_self_appraisal_or_unclosed_hosts() -> None:
    from emlis_ai_grounded_observation_plan import _operator_codes_for_text
    from emlis_ai_safety_triage import is_bounded_self_denial_text, classify_emlis_safety_triage_text
    scene = '私は悪い職場にいた。'
    for appraisal in ('私は悪い。', '私は悪いと思う。', '私はダメ。',
                      '自分には価値がない。', '自分を責め続けている。'):
        for text in (scene + appraisal, appraisal + scene):
            assert is_bounded_self_denial_text(text), text
            assert 'operator:self_evaluation' in _operator_codes_for_text(text), text
            assert classify_emlis_safety_triage_text(text).safety_triage_kind == 'self_denial_safe_state_answer'
    for unresolved in ('私は悪い職場にいたい。', '私は悪い職場にいたら。',
                      '私は悪い職場にいたと思う。', '私は悪い職場にいたずらした。',
                      '私は悪い医者になった。', '私は悪い自分にいた。',
                      '僕は悪い僕自身にいた。', '私は悪い人間にいた。',
                      '私は悪いやり方にいた。', '私は悪い職場に。',
                      '私は悪い職場にいたけれど私は悪い。'):
        assert is_bounded_self_denial_text(unresolved), unresolved
        assert 'operator:self_evaluation' in _operator_codes_for_text(unresolved), unresolved
    for signal, kind in (('死にたい。', 'safety_blocked_emergency'),
                         ('助けが必要。', 'safety_support_required')):
        for text in (signal + scene, scene + signal):
            assert classify_emlis_safety_triage_text(text).safety_triage_kind == kind, text


def _span(text: str, *, detected_type: str = "event", span_id: str = "memo.1") -> EvidenceSpan:
    return EvidenceSpan(
        span_id=span_id,
        raw_text=text,
        detected_type=detected_type,
        source_field="memo",
    )


def _graph(boundaries=None) -> ObservationGraph:
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="p1",
            claim_type="primary_state",
            text="",
            evidence_span_ids=[],
            confidence=0.0,
        ),
        safety_boundaries=list(boundaries or []),
    )


def test_phase20_2_self_denial_non_emergency_becomes_safe_state_answer_not_pre_composer_block() -> None:
    current_input = {
        "memo": "1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない",
        "memo_action": "",
        "emotions": ["悲しみ"],
        "category": ["人生", "価値観"],
    }
    decision = build_emlis_safety_triage_decision(
        current_input=current_input,
        graph=_graph(),
        evidence_spans=[_span(current_input["memo"])],
    )
    meta = decision.as_meta()

    assert meta["safety_triage_kind"] == "self_denial_safe_state_answer"
    assert meta["response_kind"] == "self_denial_safe_state_answer"
    assert meta["public_emlis_observation_allowed"] is True
    assert meta["safe_state_answer_allowed"] is True
    assert meta["requires_separate_safety_surface"] is False
    assert meta["must_not_accept_identity_claim_as_fact"] is True
    assert meta["continuation_refusal_detected"] is True
    assert "自分を傷つけ" not in str(meta)
    assert_emlis_safety_triage_meta(meta)

    boundary = build_emlis_safety_boundary_decision(graph=_graph(), evidence_spans=[_span(current_input["memo"])])
    boundary_meta = boundary.as_meta()
    assert boundary_meta["requires_block"] is False
    assert boundary_meta["safety_triage_kind"] == "self_denial_safe_state_answer"
    assert boundary_meta["safe_state_answer_allowed"] is True
    assert classify_safety_boundary_text(current_input["memo"]) == []

    contract = decision.build_internal_response_contract(reason="phase20_2_self_denial_safe_state")
    assert contract["response_kind"] == "self_denial_safe_state_answer"
    assert contract["public_observation_status"] == "passed"
    assert contract["comment_text_required"] is True

    answer = build_self_denial_safe_state_answer_result(
        current_input=current_input,
        safety_triage_decision=decision,
        evidence_spans=[_span(current_input["memo"])],
        trace_id="phase20-2-test",
    )
    assert answer.candidate.composer_source == "ai_generated"
    assert answer.grounding_report.passed is True
    assert answer.template_echo_report.passed is True
    assert answer.as_meta()["must_not_accept_identity_claim_as_fact"] is True
    assert "1番自分を傷つけてるのは私だ" not in answer.candidate.comment_text


def test_phase20_2_emergency_safety_boundary_is_never_public_passed() -> None:
    text = "もう消えたい。今日で終わりにしたい。"
    decision = build_emlis_safety_triage_decision(graph=_graph(), evidence_spans=[_span(text, detected_type="safety_risk")])
    meta = decision.as_meta()
    assert meta["safety_triage_kind"] == "safety_blocked_emergency"
    assert meta["response_kind"] == "safety_blocked_emergency"
    assert meta["public_emlis_observation_allowed"] is False
    assert meta["requires_separate_safety_surface"] is True
    assert "消えたい" not in str(meta)

    boundary = build_emlis_safety_boundary_decision(graph=_graph(), evidence_spans=[_span(text, detected_type="safety_risk")])
    boundary_meta = boundary.as_meta()
    assert boundary_meta["requires_block"] is True
    assert "self_harm_emergency" in boundary_meta["reason_codes"]

    contract = decision.build_internal_response_contract(reason="phase20_2_emergency_boundary")
    assert contract["public_observation_status"] == "safety_blocked"
    public_meta = build_public_emlis_input_feedback_meta(
        {EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: contract},
        comment_text_present=True,
        subscription_tier="free",
    )
    assert public_meta["observation_status"] == "safety_blocked"
    assert should_include_public_input_feedback("緊急安全境界を通常観測にしない。", public_meta) is False


def test_phase20_2_support_required_is_separate_from_safe_state_answer_and_emergency() -> None:
    text = "安全が保てない。助けが必要。"
    decision = build_emlis_safety_triage_decision(graph=_graph(), evidence_spans=[_span(text)])
    meta = decision.as_meta()

    assert meta["safety_triage_kind"] == "safety_support_required"
    assert meta["response_kind"] == "safety_support_required"
    assert meta["public_emlis_observation_allowed"] is False
    assert meta["requires_separate_safety_surface"] is True
    assert meta["safe_state_answer_allowed"] is False

    support_contract = build_emlis_internal_response_contract_from_safety_triage(
        "safety_support_required",
        reason="phase20_2_support_required",
    )
    assert support_contract["public_observation_status"] == "safety_blocked"
    assert support_contract["public_input_feedback_allowed"] is False


def test_self_worth_additive_particle_cannot_override_stronger_safety_boundaries() -> None:
    # Use a grammatical variant of the existing public self-worth input.
    denial = "自分には価値がない。".replace("価値が", "価値も")
    for stronger, expected in (
        ("安全が保てない。助けが必要。", "safety_support_required"),
        ("もう消えたい。今日で終わりにしたい。", "safety_blocked_emergency"),
    ):
        for combined in (denial + stronger, stronger + denial):
            decision = build_emlis_safety_triage_decision(
                current_input={"memo": combined},
                evidence_spans=[_span(denial), _span(stronger, span_id="memo.2")],
            )
            assert decision.safety_triage_kind == expected
            assert decision.requires_block is True
            assert decision.public_emlis_observation_allowed is False
            assert decision.must_not_accept_identity_claim_as_fact is True
    graph_boundary = build_emlis_safety_triage_decision(
        current_input={"memo": denial},
        graph=_graph(["safety_boundary"]),
        evidence_spans=[_span(denial)],
    )
    assert graph_boundary.safety_triage_kind == "safety_support_required"
    assert graph_boundary.requires_block is True
    assert graph_boundary.public_emlis_observation_allowed is False


def test_phase20_2_safe_observation_maps_to_normal_observation_contract() -> None:
    decision = build_emlis_safety_triage_decision(
        current_input={"memo": "今日は少し落ち着いて、部屋を片付けた。", "emotions": ["平穏"]},
        graph=_graph(),
        evidence_spans=[_span("今日は少し落ち着いて、部屋を片付けた。")],
    )
    meta = decision.as_meta()
    assert meta["safety_triage_kind"] == "safe_observation"
    assert meta["response_kind"] == "normal_observation"
    assert meta["normal_observation_allowed"] is True
    assert meta["public_emlis_observation_allowed"] is True
    assert response_kind_for_safety_triage_kind("safe_observation") == "normal_observation"
