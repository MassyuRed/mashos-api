# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
from emlis_ai_two_stage_reception_gate import (
    EMLIS_AI_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID,
    EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION,
    assert_two_stage_reception_gate_contract,
    build_two_stage_reception_gate_report,
    two_stage_reception_gate_public_summary,
)
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report


def _a_input() -> dict:
    return {
        "memo": "この世で1番気持ち悪い瞬間に出くわしてしまいイライラが止まらなかった。＆恐怖",
        "memo_action": "立ちションのおじさんとすれ違ってしまった",
        "emotion_details": [("怒り", "medium")],
        "emotions": ["怒り"],
        "category": ["生活"],
    }


def _b_input() -> dict:
    return {
        "memo": (
            "毎日毎日時間が過ぎていく間に 私は私のここが好きだなって思える所がなくて、"
            "自信をつけたいけれど常に自信がなくて出来た達成感がある時は自信がつく。"
            "でも、いい所は全て中途半端。直したい、頑張りたいって気持ちになって、"
            "色々挑戦して見てるけどこれでいいのかな、大丈夫なのかな 頑張れてるかなって毎日不安。"
        ),
        "memo_action": "",
        "emotion_details": [("平穏", "medium")],
        "emotions": ["平穏"],
        "category": ["価値観"],
    }


def _assert_no_body_payload(report: dict) -> None:
    dumped = json.dumps(report, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "立ちションのおじさん",
        "この世で1番気持ち悪い",
        "うわ、それは嫌でしたね",
        "不快で怖さもある出来事",
        "自信をつけたいけれど",
        "直したい、頑張りたい",
    ):
        assert forbidden not in dumped
    assert report.get("public_response_key_added") is not True
    assert report.get("comment_text_body_included") is not True
    assert report.get("raw_input_included") is not True


def test_phase10_a_target_two_stage_surface_passes_and_stays_meta_only() -> None:
    surface = (
        "見えたこと：\n"
        "不快で怖さもある出来事に出くわして、怒りが残っているように見えます。\n\n"
        "Emlisから：\n"
        "うわ、それは嫌でしたね。\n"
        "怖さも怒りも残るのは自然です。"
    )

    report = build_two_stage_reception_gate_report(
        comment_text=surface,
        current_input=_a_input(),
        reception_mode="daily_unpleasant_reception",
        two_stage_required=True,
    )

    assert report["schema_version"] == EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION
    assert report["material_id"] == EMLIS_AI_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID
    assert report["passed"] is True
    assert report["labels_present"] is True
    assert report["label_order_valid"] is True
    assert report["observation_section_non_empty"] is True
    assert report["reception_section_non_empty"] is True
    assert report["daily_reception_question_escape_blocked"] is False
    assert report["event_hint_emotion_fabrication_blocked"] is False
    _assert_no_body_payload(report)
    assert_two_stage_reception_gate_contract(report)


def test_phase10_a_daily_reception_question_escape_is_blocked_through_visible_gate() -> None:
    surface = (
        "見えたこと：\n"
        "まだ詳しい出来事までは見えません。\n\n"
        "Emlisから：\n"
        "何があったか残してみませんか。"
    )

    report = build_visible_surface_acceptance_gate_report(
        comment_text=surface,
        current_input=_a_input(),
        reception_mode="daily_unpleasant_reception",
        two_stage_reception_gate_required=True,
    )

    assert report["passed"] is False
    assert report["classification"] == "red"
    assert "daily_reception_question_escape_when_event_fact_present" in report["rejection_reasons"]
    assert report["two_stage_reception_gate_terminal_surface_block"] is True


def test_phase10_event_hint_alone_cannot_create_fear_or_anger_surface() -> None:
    event_only = {
        "memo": "",
        "memo_action": "立ちションのおじさんとすれ違った",
        "emotion_details": [],
        "emotions": [],
        "category": ["生活"],
    }
    surface = (
        "見えたこと：\n"
        "怖さと怒りが残っているように見えます。\n\n"
        "Emlisから：\n"
        "怖かったですね。"
    )

    report = build_two_stage_reception_gate_report(
        comment_text=surface,
        current_input=event_only,
        reception_mode="daily_unpleasant_reception",
        two_stage_required=True,
    )

    assert report["passed"] is False
    assert report["event_hint_emotion_fabrication_blocked"] is True
    assert "event_hint_created_emotion" in report["rejection_reasons"]
    _assert_no_body_payload(report)


def test_phase10_b_koto_splice_surface_is_blocked() -> None:
    surface = (
        "見えたこと：\n"
        "自信をつけたいって気持ちになってことが見えます。\n\n"
        "Emlisから：\n"
        "直したい気持ちも残っています。"
    )

    report = build_two_stage_reception_gate_report(
        comment_text=surface,
        current_input=_b_input(),
        reception_mode="self_denial_support",
        two_stage_required=True,
    )

    assert report["passed"] is False
    assert report["koto_splice_or_malformed_nominalization_blocked"] is True
    assert "two_stage_bad_grammar_or_koto_splice_surface" in report["rejection_reasons"]
    _assert_no_body_payload(report)


def test_phase10_target_judgement_agreement_is_blocked_without_adding_public_keys() -> None:
    surface = (
        "見えたこと：\n"
        "不快な出来事に怒りが残っているように見えます。\n\n"
        "Emlisから：\n"
        "相手が悪いです。あなたの怒りは正しいです。"
    )

    report = build_state_answer_gate_boundary_report(
        visible_surface=surface,
        current_input=_a_input(),
        composer_meta={"two_stage_reception_gate_required": True},
        state_answer_surface_contract={},
    )
    summary = two_stage_reception_gate_public_summary(report["two_stage_reception_gate"])

    assert report["passed"] is False
    assert report["two_stage_reception_gate_terminal_surface_block"] is True
    assert "target_judgement_agreement" in report["rejection_reasons"]
    assert summary["target_judgement_agreement_blocked"] is True
    _assert_no_body_payload(report)
    _assert_no_body_payload(summary)


def test_phase16_5_daily_unpleasant_skeleton_leak_is_blocked_by_two_stage_gate() -> None:
    surface = (
        "見えたこと：\n"
        "先を考え続ける流れが前面にあります。\n\n"
        "Emlisから：\n"
        "重なりとしてpressure or limitとして重なりを保っています。"
    )

    report = build_two_stage_reception_gate_report(
        comment_text=surface,
        current_input=_a_input(),
        reception_mode="daily_unpleasant_reception",
        two_stage_required=True,
    )

    assert report["passed"] is False
    assert report["relation_skeleton_leak_blocked"] is True
    assert "two_stage_relation_skeleton_leak" in report["rejection_reasons"]
    _assert_no_body_payload(report)


def test_phase17_5_internal_role_label_leak_is_blocked_by_two_stage_gate() -> None:
    surface = (
        "見えたこと：\n"
        "positive state と perfection fear が並んでいます。\n\n"
        "Emlisから：\n"
        "achievement が残っています。"
    )

    report = build_two_stage_reception_gate_report(
        comment_text=surface,
        current_input=_b_input(),
        reception_mode="self_understanding_follow",
        two_stage_required=True,
    )
    summary = two_stage_reception_gate_public_summary(report)

    assert report["passed"] is False
    assert report["internal_role_label_leak_blocked"] is True
    assert report["complete_surface_internal_label_leak_blocked"] is True
    assert "two_stage_internal_role_label_leak" in report["rejection_reasons"]
    assert "two_stage_complete_surface_internal_label_leak" in report["rejection_reasons"]
    assert summary["internal_role_label_leak_blocked"] is True
    assert summary["complete_surface_internal_label_leak_blocked"] is True
    _assert_no_body_payload(report)
    _assert_no_body_payload(summary)


def test_phase17_5_relation_skeleton_expanded_fragments_are_blocked_by_two_stage_gate() -> None:
    surface = (
        "見えたこと：\n"
        "別々の向きで並んでいます。\n\n"
        "Emlisから：\n"
        "片方だけに寄らず、重なりを保っています。"
    )

    report = build_two_stage_reception_gate_report(
        comment_text=surface,
        current_input=_b_input(),
        reception_mode="self_understanding_follow",
        two_stage_required=True,
    )

    assert report["passed"] is False
    assert report["relation_skeleton_leak_blocked"] is True
    assert "two_stage_relation_skeleton_leak" in report["rejection_reasons"]
    assert "two_stage_relation_skeleton_leak_surface" in report["rejection_reasons"]
    _assert_no_body_payload(report)
