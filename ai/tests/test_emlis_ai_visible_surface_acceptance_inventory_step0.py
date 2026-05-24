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

    assert VISIBLE_SURFACE_ACCEPTANCE_INVENTORY_VERSION == "emlis.visible_surface_acceptance_inventory.v1"
    assert len(fixtures) >= 5
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


def test_step0_inventory_keeps_user_account_display_out_of_scope() -> None:
    fixture = _fixture_by_id("visible_surface_out_of_scope_user_account_display_20260524")

    assert fixture.classification == "out_of_scope"
    assert fixture.expected_public_status_after_gate == "out_of_scope"
    assert fixture.expected_rejection_reasons == ()
    assert fixture.forbidden_surface_markers == ()


def test_step0_inventory_keeps_pass_and_repair_cases_separate() -> None:
    repair = _fixture_by_id("visible_surface_repair_unbridged_secondary_emotion_focus_20260524")
    mixed_pass = _fixture_by_id("visible_surface_pass_mixed_emotion_layered_20260524")
    low_info_pass = _fixture_by_id("visible_surface_pass_low_information_prompt_20260524")

    assert repair.classification == "repair_required"
    assert repair.expected_action == "rerender_surface"
    assert repair.visible_header_dominant_emotion == "悲しみ"
    assert "emotion_focus_unbridged_secondary" in repair.expected_rejection_reasons

    assert mixed_pass.classification == "pass"
    assert mixed_pass.expected_action == "allow"
    assert "状態が一色ではありません" in mixed_pass.public_body_family_markers

    assert low_info_pass.classification == "pass"
    assert low_info_pass.expected_action == "allow"
    assert "よければ、何がありましたか" in low_info_pass.forbidden_surface_markers
