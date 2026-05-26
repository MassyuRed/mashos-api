# -*- coding: utf-8 -*-
from __future__ import annotations

from fixtures.emlis_ai_visible_surface_acceptance_fixtures import (
    VISIBLE_SURFACE_ACCEPTANCE_INVENTORY_VERSION,
    VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY,
    iter_visible_surface_acceptance_screenshot_inventory,
)

_ALLOWED_CLASSIFICATIONS = {"red", "repair_required", "yellow", "pass", "out_of_scope"}


def _fixture_by_id(fixture_id: str):
    for fixture in VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY:
        if fixture.fixture_id == fixture_id:
            return fixture
    raise AssertionError(f"fixture not found: {fixture_id}")


def test_step0_visible_surface_acceptance_inventory_is_screenshot_qa_only() -> None:
    fixtures = iter_visible_surface_acceptance_screenshot_inventory()

    assert VISIBLE_SURFACE_ACCEPTANCE_INVENTORY_VERSION == "emlis.visible_surface_acceptance_inventory.v2"
    assert len(fixtures) >= 10
    assert len({fixture.fixture_id for fixture in fixtures}) == len(fixtures)

    for fixture in fixtures:
        assert fixture.classification in _ALLOWED_CLASSIFICATIONS
        assert fixture.source == "screenshot_2026_05_24"
        assert fixture.source_date == "2026-05-24"
        assert not hasattr(fixture, "expected_good_body")
        assert not hasattr(fixture, "raw_input")
        assert not hasattr(fixture, "input_text")


def test_step0_inventory_locks_tari_koto_as_red_without_replacement_body() -> None:
    fixture = _fixture_by_id("visible_surface_red_malformed_tari_koto_20260524")

    assert fixture.classification == "red"
    assert fixture.expected_public_status_after_gate == "not_passed"
    assert "malformed_nominalization_tari_fragment" in fixture.expected_rejection_reasons
    assert "たりこと" in fixture.forbidden_surface_markers
    assert "no fixed replacement body" in fixture.notes


def test_step1_inventory_locks_conditional_koto_splice_as_red_without_replacement_body() -> None:
    fixture = _fixture_by_id("visible_surface_red_conditional_koto_splice_20260524")

    assert fixture.classification == "red"
    assert fixture.expected_action == "rerender_surface"
    assert fixture.expected_public_status_after_gate == "not_passed"
    assert "malformed_phrase_unit" in fixture.expected_rejection_reasons
    assert "malformed_nominalization_conditional_fragment" in fixture.expected_rejection_reasons
    assert "residual_koto_splice_fragment" in fixture.expected_rejection_reasons
    assert "なければこと" in fixture.forbidden_surface_markers
    assert "取らなければこと" in fixture.forbidden_surface_markers
    assert "no fixed replacement body" in fixture.notes


def test_step1_inventory_locks_prediction_noun_koto_splice_as_red_without_replacement_body() -> None:
    fixture = _fixture_by_id("visible_surface_red_prediction_noun_koto_splice_20260524")

    assert fixture.classification == "red"
    assert fixture.expected_action == "rerender_surface"
    assert fixture.expected_public_status_after_gate == "not_passed"
    assert "malformed_phrase_unit" in fixture.expected_rejection_reasons
    assert "malformed_nominalization_prediction_noun_fragment" in fixture.expected_rejection_reasons
    assert "residual_koto_splice_fragment" in fixture.expected_rejection_reasons
    assert "予感こと" in fixture.forbidden_surface_markers
    assert "気配こと" in fixture.forbidden_surface_markers
    assert "no fixed replacement body" in fixture.notes


def test_step1_inventory_locks_long_clause_koto_attachment_and_relation_stack() -> None:
    fixture = _fixture_by_id("visible_surface_red_long_clause_koto_attachment_20260524")

    assert fixture.classification == "red"
    assert fixture.expected_action == "rerender_surface"
    assert fixture.expected_public_status_after_gate == "not_passed"
    assert "long_clause_koto_attachment_risk" in fixture.expected_rejection_reasons
    assert "surface_relation_skeleton_major" in fixture.expected_rejection_reasons
    assert "malformed_phrase_unit" in fixture.expected_rejection_reasons
    assert "取らなければこと" in fixture.forbidden_surface_markers
    assert "予感こと" in fixture.forbidden_surface_markers
    assert "no fixed replacement body" in fixture.notes


def test_step1_inventory_locks_relation_skeleton_actual_b_as_repair_required() -> None:
    fixture = _fixture_by_id("visible_surface_repair_relation_skeleton_mechanical_20260524")

    assert fixture.classification == "repair_required"
    assert fixture.expected_action == "rerender_surface"
    assert fixture.expected_public_status_after_gate == "not_passed"
    assert "surface_relation_skeleton_major" in fixture.expected_rejection_reasons
    assert "analytic_register_leak" in fixture.expected_rejection_reasons
    assert "状態が一色ではありません" in fixture.public_body_family_markers
    assert "片方だけに減らさず" in fixture.public_body_family_markers
    assert "重なりとして並んで" in fixture.public_body_family_markers
    assert "網羅" in fixture.public_body_family_markers
    assert fixture.input_text_available is False
    assert "input text unavailable; not classified as over-read" in fixture.notes


def test_step1_inventory_keeps_actual_a_as_low_information_positive_pass_regression() -> None:
    fixture = _fixture_by_id("visible_surface_pass_low_information_positive_prompt_20260524_actual_A")

    assert fixture.classification == "pass"
    assert fixture.expected_action == "allow"
    assert fixture.expected_public_status_after_gate == "passed"
    assert fixture.visible_header_dominant_emotion == "喜び"
    assert "まだ詳しい出来事までは見えません" in fixture.public_body_family_markers
    assert "詳しく残せそうなら" in fixture.public_body_family_markers
    assert "重さ" in fixture.forbidden_surface_markers
    assert "負荷" in fixture.forbidden_surface_markers
    assert "不安" in fixture.forbidden_surface_markers
    assert "予感こと" in fixture.forbidden_surface_markers
    assert "なければこと" in fixture.forbidden_surface_markers


def test_step1_inventory_keeps_display_absent_log_as_diagnostic_not_visible_body() -> None:
    fixture = _fixture_by_id("visible_surface_fail_closed_no_observation_display_surface_block_20260524")

    assert fixture.classification == "out_of_scope"
    assert fixture.public_body == ""
    assert fixture.expected_action == "block"
    assert fixture.expected_public_status_after_gate == "not_passed"
    assert "runtime_surface_pre_return_gate_failed" in fixture.expected_rejection_reasons
    assert "do not infer RN bug from this fixture" in fixture.notes


def test_step0_inventory_keeps_user_account_display_out_of_scope() -> None:
    fixture = _fixture_by_id("visible_surface_out_of_scope_user_account_display_20260524")

    assert fixture.classification == "out_of_scope"
    assert fixture.expected_public_status_after_gate == "out_of_scope"
    assert fixture.expected_rejection_reasons == ()
    assert fixture.forbidden_surface_markers == ()


def test_step0_inventory_keeps_pass_and_repair_cases_separate() -> None:
    repair = _fixture_by_id("visible_surface_repair_unbridged_secondary_emotion_focus_20260524")
    mixed_relation_stack = _fixture_by_id("visible_surface_pass_mixed_emotion_layered_20260524")
    low_info_pass = _fixture_by_id("visible_surface_pass_low_information_prompt_20260524")

    assert repair.classification == "repair_required"
    assert repair.expected_action == "rerender_surface"
    assert repair.visible_header_dominant_emotion == "悲しみ"
    assert "emotion_focus_unbridged_secondary" in repair.expected_rejection_reasons

    assert mixed_relation_stack.classification == "repair_required"
    assert mixed_relation_stack.expected_action == "rerender_surface"
    assert mixed_relation_stack.expected_public_status_after_gate == "not_passed"
    assert "surface_relation_skeleton_major" in mixed_relation_stack.expected_rejection_reasons
    assert "状態が一色ではありません" in mixed_relation_stack.public_body_family_markers
    assert "relation skeleton stack is no longer an unconditional pass family marker" in mixed_relation_stack.notes

    assert low_info_pass.classification == "pass"
    assert low_info_pass.expected_action == "allow"
    assert "よければ、何がありましたか" in low_info_pass.forbidden_surface_markers
