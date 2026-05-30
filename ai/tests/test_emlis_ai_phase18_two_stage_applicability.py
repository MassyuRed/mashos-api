# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_two_stage_applicability import (
    DECISION_REASON_STATE_ANSWER_CONTRACT_REQUIRED,
    EXEMPTION_REASON_LEGACY_TEXT_COMPOSER,
    EXEMPTION_REASON_LOW_INFORMATION_REPAIR_BRANCH,
    EXEMPTION_REASON_ORDINARY_UNAVAILABLE_PATH,
    TWO_STAGE_APPLICABILITY_SCHEMA_VERSION,
    build_two_stage_applicability_decision,
)
from emlis_ai_two_stage_reception_gate import build_two_stage_reception_gate_report
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report


UNLABELLED_SURFACE = "今回の入力では、疲れの重さが前面に出ているように見えます。"
TWO_STAGE_SURFACE = "見えたこと：\n疲れの重さが前面に出ているように見えます。\n\nEmlisから：\n今は無理に整え切らず、見えている重さだけを置いています。"

REQUIRED_COMPOSER_META = {
    "composer_source": "ai_generated",
    "status": "generated",
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

LOW_INFORMATION_UNAVAILABLE_META = {
    "composer_source": "unavailable",
    "status": "unavailable",
    "observation_reply_kind": "low_information_observation",
    "eligibility_status": "low_information",
    "generation_scope": "low_information_observation",
    # This intentionally mimics stale broad state-answer meta. Phase18-2 must
    # not let it make an unavailable low-information route terminally two-stage.
    "state_answer_two_stage_display_required": True,
    "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
}

LEGACY_TEXT_COMPOSER_META = {
    "composer_source": "ai_generated",
    "status": "generated",
    "composer_model": "diagnostic_fake_composer.v1",
    "generation_method": "test_composer",
    "generation_scope": "scoped_graph_only",
}


def _dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _assert_meta_only(payload: dict) -> None:
    dumped = _dump(payload)
    assert "疲れた" not in dumped
    assert UNLABELLED_SURFACE not in dumped
    assert TWO_STAGE_SURFACE not in dumped
    assert payload.get("comment_text_body_included") is not True
    assert payload.get("raw_input_included") is not True
    assert payload.get("display_gate_relaxed") is not True


def test_phase18_2_applicability_requires_labelled_shape_for_generated_complete_candidate() -> None:
    decision = build_two_stage_applicability_decision(
        composer_meta=REQUIRED_COMPOSER_META,
        candidate_source="ai_generated",
        candidate_status="generated",
        comment_text_present=True,
        labels_present=False,
    )

    assert decision["schema_version"] == TWO_STAGE_APPLICABILITY_SCHEMA_VERSION
    assert decision["required"] is True
    assert decision["terminal_when_label_missing"] is True
    assert decision["exempt"] is False
    assert decision["decision_reason"] == DECISION_REASON_STATE_ANSWER_CONTRACT_REQUIRED
    assert decision["public_contract"]["comment_text_body_included"] is False
    assert decision["public_contract"]["raw_input_included"] is False
    assert decision["public_contract"]["public_response_key_added"] is False
    assert decision["public_contract"]["rn_visible_contract_changed"] is False
    _assert_meta_only(decision)


def test_phase18_2_low_information_unavailable_branch_is_exempt_from_two_stage_label_terminal_reason() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text="",
        current_input={"memo": "疲れた", "emotion_details": [{"type": "悲しみ", "strength": "medium"}]},
        composer_meta=LOW_INFORMATION_UNAVAILABLE_META,
        rerender_allowed=False,
    )

    decision = report["two_stage_reception_gate"]["two_stage_applicability_decision"]
    assert decision["required"] is False
    assert decision["exempt"] is True
    assert decision["decision_reason"] == EXEMPTION_REASON_LOW_INFORMATION_REPAIR_BRANCH
    assert decision["terminal_when_label_missing"] is False
    assert report["two_stage_reception_gate_required"] is False
    assert "two_stage_label_missing" not in report["rejection_reasons"]
    assert "two_stage_required_but_unrealized" not in report["rejection_reasons"]
    assert "two_stage_complete_surface_blocked_by_gate" not in report["rejection_reasons"]
    _assert_meta_only(report)


def test_phase18_2_ordinary_unavailable_without_visible_candidate_is_exempt_even_with_stale_shape_meta() -> None:
    decision = build_two_stage_applicability_decision(
        composer_meta={
            "composer_source": "unavailable",
            "status": "unavailable",
            "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
        },
        comment_text_present=False,
        labels_present=False,
    )

    assert decision["required"] is False
    assert decision["exempt"] is True
    assert decision["decision_reason"] == EXEMPTION_REASON_ORDINARY_UNAVAILABLE_PATH
    assert decision["terminal_when_label_missing"] is False
    _assert_meta_only(decision)


def test_phase18_2_legacy_text_composer_candidate_is_not_rejected_by_two_stage_label_missing() -> None:
    report = build_two_stage_reception_gate_report(
        comment_text=UNLABELLED_SURFACE,
        composer_meta=LEGACY_TEXT_COMPOSER_META,
    )

    assert report["two_stage_required"] is False
    assert report["evaluated"] is False
    assert report["passed"] is True
    assert report["two_stage_applicability_decision"]["decision_reason"] == EXEMPTION_REASON_LEGACY_TEXT_COMPOSER
    assert "two_stage_label_missing" not in report["rejection_reasons"]
    assert "two_stage_required_but_unrealized" not in report["rejection_reasons"]
    _assert_meta_only(report)


def test_phase18_2_required_candidate_still_blocks_missing_labels_and_passes_labelled_surface() -> None:
    missing = build_two_stage_reception_gate_report(
        comment_text=UNLABELLED_SURFACE,
        composer_meta=REQUIRED_COMPOSER_META,
    )
    assert missing["two_stage_required"] is True
    assert missing["passed"] is False
    assert missing["two_stage_applicability_decision"]["terminal_when_label_missing"] is True
    assert "two_stage_label_missing" in missing["rejection_reasons"]
    assert "two_stage_required_but_unrealized" in missing["rejection_reasons"]

    labelled = build_two_stage_reception_gate_report(
        comment_text=TWO_STAGE_SURFACE,
        composer_meta=REQUIRED_COMPOSER_META,
    )
    assert labelled["two_stage_required"] is True
    assert labelled["passed"] is True, labelled["rejection_reasons"]
    assert labelled["two_stage_applicability_decision"]["required"] is True
    _assert_meta_only(missing)
    _assert_meta_only(labelled)
