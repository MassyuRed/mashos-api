from __future__ import annotations

import json

from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_runtime_surface_tone_engine_2_1 import build_runtime_surface_tone_engine_2_1_report
from emlis_ai_state_answer_special_cases import (
    EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID,
    EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE,
    EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION,
    build_emlis_ai_state_answer_special_cases,
    state_answer_special_cases_composer_payload,
    state_answer_special_cases_forward_meta,
    state_answer_special_cases_gate_report,
    state_answer_special_cases_surface_gate_check,
)
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report


def _input(
    *,
    memo: str,
    emotion: str,
    strength: str = "strong",
    action: str = "その場で考えていた",
    category: str = "生活",
) -> dict[str, object]:
    return {
        "id": f"special-{emotion}-{strength}",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": memo,
        "memo_action": action,
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "category": [category],
        "is_secret": False,
    }


def test_phase5_self_denial_material_separates_felt_state_identity_claim_and_requires_evidence() -> None:
    current_input = _input(
        memo="自分はダメな人間だと思ってしまう",
        emotion="悲しみ",
        action="ミスを何度も思い出していた",
        category="仕事",
    )

    meta = build_emlis_ai_state_answer_special_cases(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["schema_version"] == EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION
    assert meta["material_id"] == EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID
    assert meta["source_phase"] == EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE
    assert meta["state_answer_special_cases_connected"] is True
    assert meta["self_denial_special_handling_enabled"] is True
    assert meta["felt_state_is_real"] is True
    assert meta["identity_claim_is_not_accepted"] is True
    assert meta["emlis_impression_has_evidence"] is True
    assert meta["limited_counter_opinion_allowed"] is True
    assert meta["self_denial"]["requires_input_evidence_for_counter_opinion"] is True
    assert meta["self_denial"]["identity_claim_as_fact_allowed"] is False
    assert meta["self_denial"]["blanket_personality_praise_allowed"] is False
    assert meta["self_denial"]["absolute_support_or_alliance_allowed"] is False
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"comment_text":' not in encoded
    assert '"raw_text":' not in encoded


def test_phase5_self_denial_surface_allows_limited_counter_opinion_but_blocks_over_comfort() -> None:
    special_cases = build_emlis_ai_state_answer_special_cases(
        _input(
            memo="自分なんか価値がないと思ってしまう",
            emotion="悲しみ",
            action="一人で言葉にしていた",
        )
    ).as_meta()

    allowed = state_answer_special_cases_surface_gate_check(
        "Emlisには、その言葉だけであなた全体を決めてよいようには見えません。",
        special_cases,
    )
    blocked = state_answer_special_cases_surface_gate_check(
        "あなたは素晴らしい人です。もう大丈夫です。",
        special_cases,
    )

    assert allowed["passed"] is True
    assert allowed["self_denial_limited_counter_opinion_allowed"] is True
    assert "self_denial_limited_counter_opinion_as_emlis_impression" in allowed["allowed_exception_ids_detected"]
    assert allowed["comment_text_body_included"] is False

    assert blocked["passed"] is False
    assert "self_denial_over_comfort_or_personality_praise" in blocked["rejection_reasons"]
    assert blocked["blanket_personality_praise_allowed"] is False
    assert blocked["absolute_support_or_alliance_allowed"] is False


def test_phase5_anger_material_blocks_target_judgement_and_allows_inner_value_line() -> None:
    current_input = _input(
        memo="上司の扱いが理不尽で怒りが出た",
        emotion="怒り",
        action="急な対応を求められた",
        category="仕事",
    )

    meta = build_emlis_ai_state_answer_special_cases(current_input).as_meta()
    allowed = state_answer_special_cases_surface_gate_check(
        "その怒りの近くに、大事にしていた線を越えられた感覚があったのかもしれません。",
        meta,
    )
    blocked = state_answer_special_cases_surface_gate_check("相手が悪いです。", meta)

    assert meta["anger_special_handling_enabled"] is True
    assert meta["anger"]["inner_value_line_receiving_allowed"] is True
    assert meta["anger"]["target_judgement_agreement_allowed"] is False
    assert meta["anger"]["target_attack_amplification_allowed"] is False
    assert allowed["passed"] is True
    assert allowed["anger_inner_value_line_receiving_detected"] is True
    assert blocked["passed"] is False
    assert "anger_target_judgement_agreement" in blocked["rejection_reasons"]


def test_phase5_special_cases_are_connected_into_state_answer_surface_contract() -> None:
    self_denial_contract = build_emlis_state_answer_surface_contract(
        _input(memo="自分はダメな人間だと思ってしまう", emotion="悲しみ", action="ミスを思い出していた")
    ).as_meta()
    anger_contract = build_emlis_state_answer_surface_contract(
        _input(memo="不公平な扱いで怒りが出た", emotion="怒り", action="急な対応を求められた", category="仕事")
    ).as_meta()

    self_handling = self_denial_contract["special_handling"]
    anger_handling = anger_contract["special_handling"]

    assert self_handling["state_answer_special_cases_connected"] is True
    assert self_handling["material_id"] == EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID
    assert self_handling["self_denial"]["enabled"] is True
    assert self_handling["self_denial"]["identity_claim_is_not_accepted"] is True
    assert self_handling["self_denial"]["emlis_impression_has_evidence"] is True
    assert self_handling["self_denial"]["identity_claim_as_fact_allowed"] is False
    assert self_handling["state_answer_special_cases_gate_report"]["self_denial_special_handling_enabled"] is True

    assert anger_handling["anger"]["enabled"] is True
    assert anger_handling["anger"]["target_judgement_agreement_allowed"] is False
    assert anger_handling["anger"]["inner_value_line_receiving_allowed"] is True
    assert anger_handling["state_answer_special_cases_payload"]["comment_text_generated"] is False


def test_phase5_tone_engine_allows_self_denial_counter_exception_without_relaxing_blockers() -> None:
    special_cases = build_emlis_ai_state_answer_special_cases(
        _input(memo="自分は最低だと思ってしまう", emotion="悲しみ", action="言葉を置いていた")
    ).as_meta()

    allowed_report = build_runtime_surface_tone_engine_2_1_report(
        comment_text="その言葉だけで本質は全体を決めてよいようには見えません。",
        state_answer_special_cases=special_cases,
    )
    blocked_report = build_runtime_surface_tone_engine_2_1_report(
        comment_text="あなたは素晴らしい人です。もう大丈夫です。",
        state_answer_special_cases=special_cases,
    )

    assert allowed_report["passed"] is True
    assert allowed_report["state_answer_special_case_allowed_tone_hit_count"] >= 1
    assert allowed_report["self_denial_limited_counter_opinion_allowed_by_special_case"] is True
    assert allowed_report["tone_guard_reasons"] == []
    assert allowed_report["display_gate_relaxed"] is False

    assert blocked_report["passed"] is False
    assert "self_denial_over_comfort_or_personality_praise" in blocked_report["tone_guard_reasons"]
    assert blocked_report["state_answer_special_case_surface_guard"]["passed"] is False


def test_phase5_visible_and_pre_return_gates_block_anger_target_agreement() -> None:
    special_cases = build_emlis_ai_state_answer_special_cases(
        _input(memo="上司の扱いが理不尽で怒りが出た", emotion="怒り", action="急な対応を求められた", category="仕事")
    ).as_meta()

    visible = build_visible_surface_acceptance_gate_report(
        comment_text="相手が悪いです。",
        state_answer_special_cases=special_cases,
        rerender_allowed=False,
    )
    pre_return = build_runtime_surface_pre_return_gate_report(
        comment_text="相手が悪いです。",
        state_answer_special_cases=special_cases,
        rerender_allowed=False,
    )

    assert visible["passed"] is False
    assert visible["classification"] == "red"
    assert "anger_target_judgement_agreement" in visible["rejection_reasons"]
    assert visible["anger_target_judgement_agreement_blocked_by_special_case"] is True
    assert visible["comment_text_body_included"] is False

    assert pre_return["passed"] is False
    assert pre_return["action"] == "block"
    assert "anger_target_judgement_agreement" in pre_return["rejection_reasons"]
    assert pre_return["state_answer_special_case_terminal_surface_block"] is True
    assert pre_return["comment_text_body_included"] is False


def test_phase5_helpers_return_forward_gate_and_composer_payloads() -> None:
    special_cases = build_emlis_ai_state_answer_special_cases(
        _input(memo="自分はダメだと思ってしまう", emotion="悲しみ", action="今日の出来事を考えていた")
    )

    forward_meta = state_answer_special_cases_forward_meta(special_cases)
    gate_report = state_answer_special_cases_gate_report(forward_meta)
    composer_payload = state_answer_special_cases_composer_payload(forward_meta)

    assert forward_meta["material_id"] == EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID
    assert gate_report["state_answer_special_cases_connected"] is True
    assert gate_report["self_denial_special_handling_enabled"] is True
    assert gate_report["self_denial_identity_claim_as_fact_allowed"] is False
    assert gate_report["target_judgement_agreement_allowed"] is False
    assert composer_payload["state_answer_special_cases_connected"] is True
    assert composer_payload["state_answer_special_cases_material_only"] is True
    assert composer_payload["comment_text_generated"] is False
    assert composer_payload["raw_text_included"] is False
