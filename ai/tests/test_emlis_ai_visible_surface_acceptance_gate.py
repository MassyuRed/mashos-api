# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_visible_surface_acceptance_gate import (
    ACTION_ALLOW,
    ACTION_RERENDER_SURFACE,
    CLASSIFICATION_PASS,
    CLASSIFICATION_RED,
    CLASSIFICATION_REPAIR_REQUIRED,
    POSITIVE_TONE_PROFILE_MIXED,
    POSITIVE_TONE_PROFILE_POSITIVE_ONLY,
    VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
    assert_visible_surface_acceptance_gate_meta_only,
    build_visible_surface_acceptance_gate_contract_meta,
    build_visible_surface_acceptance_gate_contract_schema,
    build_visible_surface_acceptance_gate_report,
    dump_visible_surface_acceptance_gate_report,
)
from fixtures.emlis_ai_visible_surface_acceptance_fixtures import (
    VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY,
)


def _fixture_by_id(fixture_id: str):
    for fixture in VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY:
        if fixture.fixture_id == fixture_id:
            return fixture
    raise AssertionError(f"fixture not found: {fixture_id}")


def test_step3_visible_surface_acceptance_gate_contract_schema_and_meta_only_dump() -> None:
    meta = build_visible_surface_acceptance_gate_contract_meta()
    schema = build_visible_surface_acceptance_gate_contract_schema()
    dumped = dump_visible_surface_acceptance_gate_report(meta)

    parsed = json.loads(dumped)
    assert parsed["version"] == VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION
    assert parsed["comment_text_body_included"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["rn_visible_contract_changed"] is False
    assert parsed["public_response_key_change"] is False
    assert parsed["db_physical_name_changed"] is False
    assert parsed["display_gate_relaxed"] is False
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped

    assert schema["$id"] == VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION
    assert set(schema["required"]) >= {
        "version",
        "evaluated",
        "passed",
        "classification",
        "action",
        "rejection_reasons",
        "raw_input_included",
        "comment_text_body_included",
        "rn_visible_contract_changed",
        "public_response_key_change",
        "db_physical_name_changed",
        "display_gate_relaxed",
    }
    assert schema["properties"]["comment_text_body_included"]["const"] is False
    assert schema["properties"]["display_gate_relaxed"]["const"] is False

    unsafe_text_payload = dict(meta)
    unsafe_text_payload["comment_text"] = "出してはいけない本文"
    with pytest.raises(ValueError):
        assert_visible_surface_acceptance_gate_meta_only(unsafe_text_payload)

    unsafe_relaxed_gate = dict(meta)
    unsafe_relaxed_gate["display_gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_visible_surface_acceptance_gate_meta_only(unsafe_relaxed_gate)


def test_step3_visible_surface_acceptance_gate_flags_screenshot_unbridged_secondary_focus() -> None:
    fixture = _fixture_by_id("visible_surface_repair_unbridged_secondary_emotion_focus_20260524")
    report = build_visible_surface_acceptance_gate_report(
        comment_text=fixture.public_body,
        selected_emotions=fixture.selected_emotions,
        visible_header_dominant_emotion=fixture.visible_header_dominant_emotion,
    )

    assert report["evaluated"] is True
    assert report["passed"] is False
    assert report["blocked"] is True
    assert report["classification"] == CLASSIFICATION_REPAIR_REQUIRED
    assert report["action"] == ACTION_RERENDER_SURFACE
    assert report["rerender_recommended"] is True
    assert report["selected_emotion_count"] == 2
    assert report["visible_header_dominant_emotion_present"] is True
    assert report["visible_header_dominant_emotion_source"] == "provided"
    assert report["opening_emotion_focus_present"] is True
    assert report["secondary_emotion_focus_detected"] is True
    assert report["dominant_emotion_bridge_present"] is False
    assert "emotion_focus_unbridged_secondary" in report["rejection_reasons"]
    assert set(fixture.expected_rejection_reasons).issubset(set(report["rejection_reasons"]))
    assert_visible_surface_acceptance_gate_meta_only(report)

    dumped = dump_visible_surface_acceptance_gate_report(report)
    assert "不安の重さ" not in dumped
    assert "悲しみ" not in dumped
    assert '"comment_text"' not in dumped


def test_step3_visible_surface_acceptance_gate_allows_bridged_secondary_focus() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text="Emlisです。\n今は、悲しみを中心に、不安も近くにあるように見えます。",
        selected_emotions=(("悲しみ", "medium"), ("不安", "medium")),
    )

    assert report["passed"] is True
    assert report["classification"] == CLASSIFICATION_PASS
    assert report["action"] == ACTION_ALLOW
    assert report["visible_header_dominant_emotion_source"] == "computed"
    assert report["visible_header_dominant_emotion_present"] is True
    assert report["dominant_emotion_bridge_present"] is True
    assert report["rejection_reasons"] == []
    assert_visible_surface_acceptance_gate_meta_only(report)


def test_step3_visible_surface_acceptance_gate_uses_rn_strength_tie_order_for_dominant() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text="今は、不安の重さが先に出ているように見えます。",
        emotion_details=[{"type": "悲しみ", "strength": "medium"}, {"type": "不安", "strength": "medium"}],
    )

    # Same strength keeps the first emotion as dominant, matching RN feedback meta.
    assert report["visible_header_dominant_emotion_source"] == "computed"
    assert report["selected_emotion_count"] == 2
    assert report["secondary_emotion_focus_detected"] is True
    assert "emotion_focus_unbridged_secondary" in report["rejection_reasons"]
    assert report["classification"] == CLASSIFICATION_REPAIR_REQUIRED


def test_step3_visible_surface_acceptance_gate_flags_positive_only_over_burden_without_text_anchor() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text="Emlisです。\n今は、不安の重さが先に出ているように見えます。",
        selected_emotions=(("平穏", "medium"), ("喜び", "medium")),
        current_text_negative_anchor_present=False,
    )

    assert report["passed"] is False
    assert report["classification"] == CLASSIFICATION_REPAIR_REQUIRED
    assert report["action"] == ACTION_RERENDER_SURFACE
    assert report["positive_tone_profile"] == POSITIVE_TONE_PROFILE_POSITIVE_ONLY
    assert report["burden_surface_without_anchor_detected"] is True
    assert "positive_tone_over_burden_without_anchor" in report["rejection_reasons"]
    assert "emotion_focus_unselected_without_evidence" not in report["rejection_reasons"]
    assert_visible_surface_acceptance_gate_meta_only(report)


def test_step3_visible_surface_acceptance_gate_allows_positive_selected_burden_when_text_anchor_exists() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text="Emlisです。\n今は、不安の重さが先に出ているように見えます。",
        selected_emotions=(("平穏", "medium"), ("喜び", "medium")),
        current_text="少し不安もあるけれど、今日は平穏も残っている。",
    )

    assert report["positive_tone_profile"] == POSITIVE_TONE_PROFILE_MIXED
    assert report["negative_text_anchor_present"] is True
    assert report["burden_surface_without_anchor_detected"] is False
    assert "positive_tone_over_burden_without_anchor" not in report["rejection_reasons"]
    assert "emotion_focus_unselected_without_evidence" not in report["rejection_reasons"]
    assert report["classification"] == CLASSIFICATION_PASS
    assert report["action"] == ACTION_ALLOW


def test_step3_visible_surface_acceptance_gate_keeps_malformed_tari_koto_as_red_case() -> None:
    fixture = _fixture_by_id("visible_surface_red_malformed_tari_koto_20260524")
    report = build_visible_surface_acceptance_gate_report(
        comment_text=fixture.public_body,
        selected_emotions=fixture.selected_emotions,
        visible_header_dominant_emotion=fixture.visible_header_dominant_emotion,
    )

    assert report["passed"] is False
    assert report["classification"] == CLASSIFICATION_RED
    assert report["action"] == ACTION_RERENDER_SURFACE
    assert report["malformed_nominalization_detected"] is True
    assert "malformed_phrase_unit" in report["rejection_reasons"]
    assert "malformed_nominalization_tari_fragment" in report["rejection_reasons"]
    assert set(fixture.expected_rejection_reasons).issubset(set(report["rejection_reasons"]))

    dumped = dump_visible_surface_acceptance_gate_report(report)
    assert "たりこと" not in dumped
    assert "無理に変えよう" not in dumped
    assert '"comment_text"' not in dumped


def test_step4_visible_surface_acceptance_gate_flags_koto_splice_fixtures_as_red() -> None:
    for fixture_id in (
        "visible_surface_red_conditional_koto_splice_20260524",
        "visible_surface_red_prediction_noun_koto_splice_20260524",
        "visible_surface_red_long_clause_koto_attachment_20260524",
    ):
        fixture = _fixture_by_id(fixture_id)
        report = build_visible_surface_acceptance_gate_report(
            comment_text=fixture.public_body,
            selected_emotions=fixture.selected_emotions,
            visible_header_dominant_emotion=fixture.visible_header_dominant_emotion,
        )

        assert report["passed"] is False
        assert report["classification"] == CLASSIFICATION_RED
        assert report["action"] == ACTION_RERENDER_SURFACE
        assert report["koto_splice_detected"] is True
        assert report["surface_repair_requested"] is True
        assert report["repair_reason_family"] == "koto_splice"
        assert "malformed_phrase_unit" in report["rejection_reasons"]
        assert set(fixture.expected_rejection_reasons).issubset(set(report["rejection_reasons"]))
        assert_visible_surface_acceptance_gate_meta_only(report)

        dumped = dump_visible_surface_acceptance_gate_report(report)
        for forbidden in fixture.forbidden_surface_markers:
            assert forbidden not in dumped
        assert '"comment_text"' not in dumped


def test_step4_visible_surface_acceptance_gate_repairs_actual_b_relation_skeleton_stack() -> None:
    fixture = _fixture_by_id("visible_surface_repair_relation_skeleton_mechanical_20260524")
    report = build_visible_surface_acceptance_gate_report(
        comment_text=fixture.public_body,
        selected_emotions=fixture.selected_emotions,
        visible_header_dominant_emotion=fixture.visible_header_dominant_emotion,
    )

    assert report["passed"] is False
    assert report["classification"] == CLASSIFICATION_REPAIR_REQUIRED
    assert report["action"] == ACTION_RERENDER_SURFACE
    assert report["koto_splice_detected"] is False
    assert report["relation_skeleton_marker_count"] >= 2
    assert report["relation_skeleton_major"] is True
    assert report["analytic_register_leak_count"] >= 1
    assert report["analytic_register_leak"] is True
    assert report["surface_repair_requested"] is True
    assert report["repair_reason_family"] == "relation_skeleton"
    assert set(fixture.expected_rejection_reasons).issubset(set(report["rejection_reasons"]))
    assert_visible_surface_acceptance_gate_meta_only(report)

    dumped = dump_visible_surface_acceptance_gate_report(report)
    assert "網羅" not in dumped
    assert "状態が一色" not in dumped
    assert '"comment_text"' not in dumped


def test_step4_visible_surface_acceptance_gate_keeps_actual_a_low_information_positive_as_pass() -> None:
    fixture = _fixture_by_id("visible_surface_pass_low_information_positive_prompt_20260524_actual_A")
    report = build_visible_surface_acceptance_gate_report(
        comment_text=fixture.public_body,
        selected_emotions=fixture.selected_emotions,
        visible_header_dominant_emotion=fixture.visible_header_dominant_emotion,
    )

    assert report["passed"] is True
    assert report["classification"] == CLASSIFICATION_PASS
    assert report["action"] == ACTION_ALLOW
    assert report["koto_splice_detected"] is False
    assert report["relation_skeleton_marker_count"] == 0
    assert report["analytic_register_leak_count"] == 0
    assert report["surface_repair_requested"] is False
    assert report["repair_reason_family"] == "none"
    assert report["rejection_reasons"] == []
    assert_visible_surface_acceptance_gate_meta_only(report)


def test_phase17_5_visible_gate_blocks_internal_role_label_leak_as_terminal_red() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text=(
            "見えたこと：\n"
            "achievement が表面に出ています。\n\n"
            "Emlisから：\n"
            "positive state として扱っています。"
        ),
        rerender_allowed=False,
    )

    assert report["passed"] is False
    assert report["classification"] == CLASSIFICATION_RED
    assert report["action"] == "block"
    assert report["internal_role_label_leak_detected"] is True
    assert report["internal_role_label_marker_count"] >= 2
    assert "two_stage_internal_role_label_leak" in report["rejection_reasons"]
    assert "two_stage_complete_surface_internal_label_leak" in report["rejection_reasons"]
    assert report["comment_text_body_included"] is False
    assert report["raw_input_included"] is False
    assert report["display_gate_relaxed"] is False
    assert_visible_surface_acceptance_gate_meta_only(report)


@pytest.mark.parametrize(
    "safe_fragment",
    (
        "感じたこと",
        "必要なこと",
        "予定のこと",
        "予感があること",
        "しなければならないこと",
    ),
)
def test_step4_visible_surface_acceptance_gate_does_not_overblock_safe_koto_forms(safe_fragment: str) -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text=(
            "Emlisです。\n"
            "今は、喜びが先に出ています。\n"
            f"その近くに、{safe_fragment}も残っています。"
        ),
        selected_emotions=(("喜び", "medium"),),
        visible_header_dominant_emotion="喜び",
    )

    assert report["passed"] is True
    assert report["classification"] == CLASSIFICATION_PASS
    assert report["action"] == ACTION_ALLOW
    assert report["malformed_nominalization_detected"] is False
    assert report["koto_splice_detected"] is False
    assert "malformed_phrase_unit" not in report["rejection_reasons"]
    assert "malformed_nominalization_conditional_fragment" not in report["rejection_reasons"]
    assert "malformed_nominalization_prediction_noun_fragment" not in report["rejection_reasons"]
