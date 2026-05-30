# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from helpers.emlis_ai_two_stage_product_visible_fixture_assertions import (
    PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS,
    _required_two_stage_composer_meta,
    generate_phase17_two_stage_product_visible_candidate,
)
from emlis_ai_visible_readability_quality import (
    VISIBLE_READABILITY_QUALITY_SCHEMA_VERSION,
    VISIBLE_READABILITY_QUALITY_SOURCE_PHASE,
    assert_visible_readability_quality_meta_only,
    build_visible_readability_quality_report,
    visible_readability_quality_public_summary,
)
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report


_FORBIDDEN_BODY_KEYS = {
    "comment_text",
    "commentText",
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "input_text",
    "inputText",
    "surface_text",
    "realized_text",
    "line_text",
    "body",
    "text",
    "sentence",
    "sentences",
    "raw_quote",
    "evidence_text",
}


def _contains_forbidden_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_BODY_KEYS:
                return True
            if _contains_forbidden_body_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_body_key(item) for item in value)
    return False


def test_phase18_8_visible_readability_quality_helper_is_meta_only() -> None:
    report = build_visible_readability_quality_report(
        comment_text=(
            "見えたこと：\n不安と直したい気持ちが同時に残っています。\n\n"
            "Emlisから：\n一方で、挑戦したい気持ちが残っています。"
        )
    )
    summary = visible_readability_quality_public_summary(report)

    assert report["schema_version"] == VISIBLE_READABILITY_QUALITY_SCHEMA_VERSION
    assert report["source_phase"] == VISIBLE_READABILITY_QUALITY_SOURCE_PHASE
    assert report["exact_match_required"] is False
    assert report["comment_text_body_included"] is False
    assert report["comment_text_body_included_in_meta"] is False
    assert report["raw_input_included"] is False
    assert report["public_response_key_added"] is False
    assert report["rn_visible_contract_changed"] is False
    assert report["display_gate_relaxed"] is False
    assert report["grounding_gate_relaxed"] is False
    assert _contains_forbidden_body_key(report) is False
    assert _contains_forbidden_body_key(summary) is False
    assert_visible_readability_quality_meta_only(report)
    assert_visible_readability_quality_meta_only(summary)


@pytest.mark.parametrize("case_id", PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS)
def test_phase18_8_phase17_product_visible_fixtures_pass_visible_readability_quality(case_id: str) -> None:
    candidate = generate_phase17_two_stage_product_visible_candidate(case_id)
    comment_text = str(candidate.get("comment_text") or "")
    report = build_visible_readability_quality_report(comment_text=comment_text)
    gate = build_visible_surface_acceptance_gate_report(
        comment_text=comment_text,
        current_input={},
        composer_meta=dict(candidate.get("composer_meta") or {}),
        rerender_allowed=False,
    )

    assert candidate.get("status") == "generated", candidate
    assert report["passed"] is True, report
    assert report["classification"] == "passed", report
    assert report["hard_block_reasons"] == []
    assert report["soft_repair_reasons"] == []
    assert gate["visible_readability_quality_passed"] is True, gate
    assert gate["visible_readability_quality_rejection_reasons"] == []
    assert gate["visible_readability_quality_repair_reasons"] == []
    assert gate["passed"] is True, gate
    assert gate["visible_readability_quality_comment_text_body_included"] is False
    assert gate["visible_readability_quality_raw_input_included"] is False
    assert gate["visible_readability_quality_public_response_key_added"] is False
    assert gate["visible_readability_quality_rn_visible_contract_changed"] is False
    assert gate["display_gate_relaxed"] is False
    assert gate["grounding_gate_relaxed"] is False


def test_phase18_8_repeated_connector_is_soft_repair_not_gate_relaxation() -> None:
    surface = (
        "見えたこと：\n不安と直したい気持ちが同時に残っています。\n\n"
        "Emlisから：\n一方で、挑戦したい気持ちが残っています。\n"
        "一方で、試している動きも残っています。"
    )
    report = build_visible_readability_quality_report(comment_text=surface)
    gate = build_visible_surface_acceptance_gate_report(
        comment_text=surface,
        current_input={},
        composer_meta=_required_two_stage_composer_meta(),
        rerender_allowed=True,
    )

    assert report["classification"] == "repair_required", report
    assert "visible_readability_soft_repetition:connector_ippoude" in report["soft_repair_reasons"]
    assert report["hard_block_reasons"] == []
    assert gate["passed"] is False, gate
    assert gate["classification"] == "repair_required", gate
    assert gate["action"] == "rerender_surface", gate
    assert "visible_readability_soft_repetition:connector_ippoude" in gate["rejection_reasons"]
    assert gate["display_gate_relaxed"] is False
    assert gate["grounding_gate_relaxed"] is False


def test_phase18_8_internal_role_and_relation_skeleton_are_hard_blocks() -> None:
    surface = (
        "見えたこと：\nachievement と positive state が同じ流れにあります。\n\n"
        "Emlisから：\n別々の向きが片方だけに寄らず、同じ場所に並んでいます。"
    )
    report = build_visible_readability_quality_report(comment_text=surface)
    gate = build_visible_surface_acceptance_gate_report(
        comment_text=surface,
        current_input={},
        composer_meta=_required_two_stage_composer_meta(),
        rerender_allowed=True,
    )

    assert report["classification"] == "red", report
    assert report["action"] == "fail_closed", report
    assert any(reason.startswith("visible_readability:internal_role_") for reason in report["hard_block_reasons"])
    assert "visible_readability:relation_skeleton_same_flow" in report["hard_block_reasons"]
    assert "visible_readability:relation_skeleton_one_side" in report["hard_block_reasons"]
    assert gate["passed"] is False, gate
    assert gate["classification"] == "red", gate
    assert gate["action"] == "block", gate
    assert any(str(reason).startswith("visible_readability:") for reason in gate["rejection_reasons"])
    assert gate["display_gate_relaxed"] is False
    assert gate["grounding_gate_relaxed"] is False


def test_phase18_8_observation_reception_simple_paraphrase_is_repair_required() -> None:
    surface = (
        "見えたこと：\n不安と直したい気持ちが同時に残っています。\n\n"
        "Emlisから：\n不安と直したい気持ちが同時に残っています。"
    )
    report = build_visible_readability_quality_report(comment_text=surface)

    assert report["classification"] == "repair_required", report
    assert report["observation_reception_too_similar"] is True
    assert "visible_readability:observation_reception_too_similar" in report["soft_repair_reasons"]
    assert report["comment_text_body_included"] is False
    assert report["raw_input_included"] is False


def test_phase18_8_low_information_question_sentence_is_allowed() -> None:
    surface = (
        "見えたこと：\n疲れの重さだけが少し見えています。\n\n"
        "Emlisから：\n詳しく残せそうなら、何があったか残してみませんか。"
    )
    report = build_visible_readability_quality_report(comment_text=surface)

    assert report["passed"] is True, report
    assert report["question_sentence_allowed"] is True
    assert report["hard_block_reasons"] == []
    assert report["soft_repair_reasons"] == []
