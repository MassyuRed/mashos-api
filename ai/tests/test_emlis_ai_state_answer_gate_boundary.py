from __future__ import annotations

import json

from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_runtime_surface_tone_engine_2_1 import build_runtime_surface_tone_engine_2_1_report
from emlis_ai_state_answer_gate_boundary import (
    EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_MATERIAL_ID,
    EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_PHASE,
    EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_SCHEMA_VERSION,
    build_state_answer_gate_boundary_report,
)
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report


def _input(*, memo: str, emotion: str, strength: str = "strong", action: str = "その場で考えていた", category: str = "生活") -> dict[str, object]:
    return {
        "id": f"phase8-{emotion}-{strength}",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": memo,
        "memo_action": action,
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "category": [category],
        "is_secret": False,
    }


def _contract(current_input: dict[str, object]) -> dict[str, object]:
    return build_emlis_state_answer_surface_contract(current_input).as_meta()


def test_phase8_gate_boundary_allows_grounded_self_denial_counter_opinion_without_public_payload() -> None:
    current_input = _input(
        memo="自分なんか価値がないと思ってしまう",
        emotion="悲しみ",
        action="一人で言葉にしていた",
    )
    contract = _contract(current_input)

    report = build_state_answer_gate_boundary_report(
        visible_surface="Emlisには、その言葉だけであなた全体を決めてよいようには見えません。",
        state_answer_surface_contract=contract,
    )
    dumped = json.dumps(report, ensure_ascii=False, sort_keys=True)

    assert report["schema_version"] == EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_SCHEMA_VERSION
    assert report["material_id"] == EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_MATERIAL_ID
    assert report["source_phase"] == EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_PHASE
    assert report["passed"] is True
    assert report["terminal_surface_block"] is False
    assert report["self_denial_limited_counter_opinion_allowed"] is True
    assert report["self_denial_exception_evidence_ready"] is True
    assert "self_denial_limited_counter_opinion_as_emlis_impression" in report["allowed_exception_ids"]
    assert report["public_meta_summary_only"] is True
    assert report["comment_text_body_included"] is False
    assert report["raw_input_included"] is False
    assert current_input["memo"] not in dumped
    assert current_input["memo_action"] not in dumped
    assert "Emlisには、その言葉だけであなた全体を決めてよいようには見えません。" not in dumped


def test_phase8_gate_boundary_blocks_self_denial_exception_when_it_becomes_diagnosis_or_absolute_comfort() -> None:
    contract = _contract(
        _input(
            memo="自分は最低だと思ってしまう",
            emotion="悲しみ",
            action="ミスを思い出していた",
        )
    )

    report = build_state_answer_gate_boundary_report(
        visible_surface="あなたは素晴らしい人です。もう大丈夫です。原因はこれです。",
        state_answer_surface_contract=contract,
    )

    assert report["passed"] is False
    assert report["terminal_surface_block"] is True
    assert "self_denial_over_comfort_or_personality_praise" in report["rejection_reasons"]
    assert "state_answer_personality_claim_surface" in report["forbidden_claim_reasons"]
    assert "state_answer_absolute_support_or_alliance_surface" in report["forbidden_claim_reasons"]
    assert "state_answer_cause_or_reason_overclaim_surface" in report["forbidden_claim_reasons"]


def test_phase8_runtime_visible_and_tone_gates_block_state_answer_forbidden_claims() -> None:
    contract = _contract(
        _input(
            memo="上司の扱いが理不尽で怒りが出た",
            emotion="怒り",
            action="急な対応を求められた",
            category="仕事",
        )
    )
    bad_surface = "相手が悪いです。距離を取った方がいいです。"

    runtime = build_runtime_surface_pre_return_gate_report(
        comment_text=bad_surface,
        composer_meta={"state_answer_surface_contract": contract},
        state_answer_surface_contract=contract,
        rerender_allowed=False,
    )
    visible = build_visible_surface_acceptance_gate_report(
        comment_text=bad_surface,
        composer_meta={"state_answer_surface_contract": contract},
        state_answer_surface_contract=contract,
        rerender_allowed=False,
    )
    tone = build_runtime_surface_tone_engine_2_1_report(
        comment_text=bad_surface,
        composer_meta={"state_answer_surface_contract": contract},
        state_answer_surface_contract=contract,
    )

    assert runtime["passed"] is False
    assert runtime["action"] == "block"
    assert "anger_target_judgement_agreement" in runtime["rejection_reasons"]
    assert runtime["state_answer_gate_boundary_terminal_surface_block"] is True
    assert runtime["comment_text_body_included"] is False

    assert visible["passed"] is False
    assert visible["classification"] == "red"
    assert "anger_target_judgement_agreement" in visible["rejection_reasons"]
    assert visible["state_answer_gate_boundary_terminal_surface_block"] is True
    assert visible["comment_text_body_included"] is False

    assert tone["passed"] is False
    assert "anger_target_judgement_agreement" in tone["tone_guard_reasons"]
    assert tone["state_answer_gate_boundary_terminal_surface_block"] is True
    assert tone["comment_text_body_included"] is False


def test_phase8_display_gate_carries_state_answer_boundary_trace_without_comment_body() -> None:
    from emlis_ai_display_gate import decide_emlis_observation_display
    from emlis_ai_types import GroundingReport, ListenerReaderReport, TemplateEchoReport

    contract = _contract(
        _input(
            memo="上司の扱いが理不尽で怒りが出た",
            emotion="怒り",
            action="急な対応を求められた",
            category="仕事",
        )
    )
    runtime = build_runtime_surface_pre_return_gate_report(
        comment_text="相手が悪いです。",
        composer_meta={"state_answer_surface_contract": contract},
        state_answer_surface_contract=contract,
        rerender_allowed=False,
    )
    decision = decide_emlis_observation_display(
        comment_text="相手が悪いです。",
        reader_report=ListenerReaderReport(
            understandable=True,
            addressee_clear=True,
            speaker_integrity_ok=True,
            conversational=True,
            report_like=False,
            confidence=1.0,
        ),
        grounding_report=GroundingReport(passed=True, confidence=1.0),
        template_echo_report=TemplateEchoReport(passed=True),
        composer_source="ai_generated",
        runtime_surface_pre_return_gate_report=runtime,
    )

    assert decision.observation_status != "passed"
    assert decision.comment_text == ""
    assert "anger_target_judgement_agreement" in decision.rejection_reasons
    assert decision.gate_trace["display_gate"]["state_answer_gate_boundary_runtime_blocked"] is True
    assert decision.gate_trace["display_gate"]["state_answer_contract_body_returned"] is False
    dumped = json.dumps(decision.gate_trace, ensure_ascii=False, sort_keys=True)
    assert "相手が悪いです" not in dumped
