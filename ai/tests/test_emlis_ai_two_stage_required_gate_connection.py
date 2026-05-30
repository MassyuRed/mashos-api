# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from types import SimpleNamespace

from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report


UNLABELLED_COMPLETE_SURFACE = (
    "今回の入力では、先を考え続ける流れが前面にあります。"
    "重なりとしてpressure or limitとして重なりを保っています。"
)

TWO_STAGE_SURFACE = (
    "見えたこと：\n"
    "不快で怖さもある出来事に出くわして、怒りが残っているように見えます。\n\n"
    "Emlisから：\n"
    "うわ、それは嫌でしたね。\n"
    "怖さも怒りも残るのは自然です。"
)

REQUIRED_COMPOSER_META = {
    "composer_source": "ai_generated",
    "state_answer_composer_role_plan_connected": True,
    "state_answer_two_stage_display_required": True,
    "state_answer_section_labels_required": True,
    "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
    "composition_contract": {
        "two_stage_reception_surface_required": True,
        "section_labels_required": True,
        "expected_comment_text_shape": "labelled_two_stage_text",
    },
}

EXPECTED_SHAPE_ONLY_COMPOSER_META = {
    "composer_source": "ai_generated",
    "state_answer_composer_role_plan_connected": True,
    "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
}

A_CURRENT_INPUT = {
    "memo": "この世で1番気持ち悪い瞬間に出くわしてしまいイライラが止まらなかった。＆恐怖",
    "memo_action": "立ちションのおじさんとすれ違ってしまった",
    "emotion_details": [{"type": "怒り", "strength": "medium"}],
    "emotions": ["怒り"],
    "category": ["生活"],
}


def _assert_meta_only(report: dict) -> None:
    dumped = json.dumps(report, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "立ちションのおじさん",
        "この世で1番気持ち悪い",
        "うわ、それは嫌でしたね",
        "不快で怖さもある出来事",
        UNLABELLED_COMPLETE_SURFACE,
    ):
        assert forbidden not in dumped
    assert report.get("comment_text_body_included") is not True
    assert report.get("raw_input_included") is not True
    assert report.get("display_gate_relaxed") is not True


def test_phase16_1_visible_gate_blocks_required_two_stage_when_labels_are_missing_from_composer_meta() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text=UNLABELLED_COMPLETE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_meta=REQUIRED_COMPOSER_META,
        rerender_allowed=False,
    )

    assert report["passed"] is False
    assert report["classification"] == "red"
    assert report["action"] == "block"
    assert report["two_stage_reception_gate_required"] is True
    assert report["two_stage_reception_gate_terminal_surface_block"] is True
    assert "two_stage_label_missing" in report["rejection_reasons"]
    assert "two_stage_labels_missing_or_duplicated" in report["rejection_reasons"]
    gate = report["two_stage_reception_gate"]
    assert gate["evaluated"] is True
    assert gate["two_stage_required"] is True
    assert gate["labels_present"] is False
    _assert_meta_only(report)


def test_phase16_1_state_answer_gate_blocks_required_two_stage_when_labels_are_missing_from_composer_meta() -> None:
    report = build_state_answer_gate_boundary_report(
        visible_surface=UNLABELLED_COMPLETE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_meta=REQUIRED_COMPOSER_META,
    )

    assert report["passed"] is False
    assert report["two_stage_reception_gate_evaluated"] is True
    assert report["two_stage_reception_gate_terminal_surface_block"] is True
    assert "two_stage_label_missing" in report["rejection_reasons"]
    assert report["two_stage_reception_gate"]["two_stage_required"] is True
    _assert_meta_only(report)


def test_phase16_1_expected_labelled_shape_also_makes_missing_labels_terminal() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text=UNLABELLED_COMPLETE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_meta=EXPECTED_SHAPE_ONLY_COMPOSER_META,
        rerender_allowed=False,
    )

    assert report["passed"] is False
    assert report["two_stage_reception_gate_required"] is True
    assert report["two_stage_reception_gate_terminal_surface_block"] is True
    assert "two_stage_label_missing" in report["rejection_reasons"]
    _assert_meta_only(report)


def test_phase16_1_reply_service_visible_gate_builder_carries_candidate_composer_meta() -> None:
    from emlis_ai_reply_service import _build_visible_surface_acceptance_report_for_candidate

    candidate = SimpleNamespace(
        composer_source="ai_generated",
        composer_model="cocolon.complete_composer.initial.v1",
        generation_method="complete_composer_initial",
        generation_scope="current_input_core",
        coverage_scope="current_input_core",
        status="generated",
        composer_meta=REQUIRED_COMPOSER_META,
    )

    report = _build_visible_surface_acceptance_report_for_candidate(
        comment_text=UNLABELLED_COMPLETE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_candidate=candidate,
        composer_source="ai_generated",
        rerender_attempted=False,
    )

    assert report["passed"] is False
    assert report["classification"] == "red"
    assert report["two_stage_reception_gate_required"] is True
    assert report["two_stage_reception_gate_terminal_surface_block"] is True
    assert "two_stage_label_missing" in report["rejection_reasons"]
    _assert_meta_only(report)


def test_phase16_1_two_stage_positive_surface_still_passes_when_required_by_meta() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text=TWO_STAGE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_meta=REQUIRED_COMPOSER_META,
        reception_mode="daily_unpleasant_reception",
        rerender_allowed=False,
    )

    assert report["passed"] is True, report["rejection_reasons"]
    assert report["classification"] == "pass"
    assert report["two_stage_reception_gate_required"] is True
    assert report["two_stage_reception_gate_terminal_surface_block"] is False
    assert report["two_stage_reception_gate"]["labels_present"] is True
    _assert_meta_only(report)
