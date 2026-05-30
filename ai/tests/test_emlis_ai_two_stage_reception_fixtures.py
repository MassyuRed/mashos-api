# -*- coding: utf-8 -*-
from __future__ import annotations

import re

import pytest

from fixtures.emlis_ai_two_stage_reception_display_quality_cases import (
    PHASE13_TWO_STAGE_DISPLAY_QA_CASES,
    PHASE13_TWO_STAGE_DISPLAY_QA_CASE_IDS,
    PHASE13_TWO_STAGE_DISPLAY_QA_VERSION,
    iter_phase13_blocked_surface_probes,
)
from fixtures.emlis_ai_two_stage_reception_cases import (
    COMMON_SECTION_SHAPE_EXPECTATION,
    PHASE0_DESIGN_LOCK,
    TWO_STAGE_COMMENT_TEXT_SHAPE,
    TWO_STAGE_LABEL_MARKERS,
    TWO_STAGE_RECEPTION_CASES,
    TWO_STAGE_RECEPTION_DESIGN_SOURCE,
    TWO_STAGE_RECEPTION_EVALUATION_AXES,
    TWO_STAGE_RECEPTION_FIXTURE_VERSION,
    TWO_STAGE_RECEPTION_REQUIRED_CASE_IDS,
    current_input_for_two_stage_reception_case,
    evaluate_forbidden_surface_fragments,
    split_two_stage_comment_text,
    two_stage_reception_case_by_id,
)

_EXACT_TEXT_KEYS_FORBIDDEN = {
    "expected_comment_text",
    "expected_exact_comment_text",
    "target_comment_text",
    "target_surface",
    "allowed_surface_probe",
    "blocked_surface_probe",
}

_REQUIRED_CURRENT_INPUT_KEYS = {
    "id",
    "created_at",
    "memo",
    "memo_action",
    "emotion_details",
    "emotions",
    "category",
    "is_secret",
}

_REQUIRED_RATIO_KEYS = {
    "observation_min",
    "observation_max",
    "observation_zero_allowed",
    "human_follow_zero_allowed",
}


@pytest.mark.parametrize("expected_axis", TWO_STAGE_RECEPTION_EVALUATION_AXES)
def test_phase0_design_lock_declares_expected_evaluation_axes(expected_axis: str) -> None:
    assert expected_axis


def test_phase0_design_lock_public_contract_is_unchanged() -> None:
    assert TWO_STAGE_RECEPTION_FIXTURE_VERSION == "cocolon.emlis_two_stage_reception.fixtures.v1"
    assert PHASE0_DESIGN_LOCK["design_source"] == TWO_STAGE_RECEPTION_DESIGN_SOURCE
    assert PHASE0_DESIGN_LOCK["two_stage_labels"] == {
        "observation": "見えたこと",
        "reception": "Emlisから",
    }
    assert TWO_STAGE_COMMENT_TEXT_SHAPE == (
        "見えたこと：\n{observation_section_text}\n\nEmlisから：\n{reception_section_text}"
    )

    public_contract = PHASE0_DESIGN_LOCK["public_contract"]
    assert public_contract["public_response_key_added"] is False
    assert public_contract["rn_visible_contract_changed"] is False
    assert public_contract["observation_status_public_enum_extended"] is False
    assert public_contract["comment_text_is_only_visible_body"] is True
    assert public_contract["rn_display_title_changed"] is False
    assert public_contract["rn_display_condition_changed"] is False

    fixed_boundaries = PHASE0_DESIGN_LOCK["fixed_boundaries"]
    assert fixed_boundaries["visible_body_public_key"] == "input_feedback.comment_text"
    assert fixed_boundaries["visible_status_contract"] == (
        "input_feedback.emlis_ai.observation_status == passed"
    )
    assert fixed_boundaries["observation_text_public_key_allowed"] is False
    assert fixed_boundaries["reception_text_public_key_allowed"] is False
    assert fixed_boundaries["general_dictionary_required"] is False
    assert fixed_boundaries["runtime_example_specific_branch_allowed"] is False


def test_phase1_defines_exactly_the_required_fixture_cases() -> None:
    case_ids = {case["case_id"] for case in TWO_STAGE_RECEPTION_CASES}
    assert case_ids == TWO_STAGE_RECEPTION_REQUIRED_CASE_IDS
    assert len(TWO_STAGE_RECEPTION_CASES) == 5


@pytest.mark.parametrize("case", TWO_STAGE_RECEPTION_CASES, ids=lambda case: case["case_id"])
def test_two_stage_reception_fixture_case_contract(case: dict) -> None:
    assert case["source_label"]
    assert case["source_issue"]
    assert _EXACT_TEXT_KEYS_FORBIDDEN.isdisjoint(case.keys())

    current_input = current_input_for_two_stage_reception_case(case)
    assert _REQUIRED_CURRENT_INPUT_KEYS.issubset(current_input.keys())
    assert current_input["id"].startswith("two-stage-reception-")
    assert current_input["created_at"].startswith("2026-05-26T")
    assert isinstance(current_input["memo"], str) and current_input["memo"].strip()
    assert isinstance(current_input["memo_action"], str)
    assert isinstance(current_input["emotion_details"], list) and current_input["emotion_details"]
    assert isinstance(current_input["emotions"], list) and current_input["emotions"]
    assert isinstance(current_input["category"], list) and current_input["category"]
    assert current_input["is_secret"] is False

    mode_any = tuple(case["expected_reception_mode_any"])
    assert mode_any
    if case.get("expected_reception_mode"):
        assert case["expected_reception_mode"] in mode_any

    ratio_contract = case["expected_ratio_contract"]
    assert _REQUIRED_RATIO_KEYS.issubset(ratio_contract.keys())
    assert 0.0 < ratio_contract["observation_min"] <= ratio_contract["observation_max"] <= 1.0
    assert ratio_contract["observation_zero_allowed"] is False
    assert ratio_contract["human_follow_zero_allowed"] is False
    assert ratio_contract.get("human_follow_units_min", 1) >= 1

    low_information_boundary = case["expected_low_information_boundary"]
    assert low_information_boundary["low_information_question_required"] is False
    assert low_information_boundary["low_information_question_allowed"] is False
    assert low_information_boundary["reason"]

    section_shape = case["expected_section_shape"]
    assert section_shape == COMMON_SECTION_SHAPE_EXPECTATION
    assert section_shape["two_stage_labels_required"] is True
    assert section_shape["observation_section_must_precede_reception_section"] is True
    assert section_shape["public_response_key_added"] is False
    assert section_shape["rn_visible_contract_changed"] is False
    assert section_shape["exact_text_match_required"] is False

    assert "two_stage_labels" in case["required_surface_features"]
    assert case["forbidden_surface_fragments"]
    assert case["forbidden_inferences"]


def test_fixture_expectations_cover_design_specific_cases() -> None:
    daily_case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    assert daily_case["expected_reception_mode"] == "daily_unpleasant_reception"
    assert daily_case["expected_ratio_contract"]["expected_ratio_reason"] == (
        "daily_unpleasant_reception_light"
    )
    assert daily_case["expected_ratio_contract"]["observation_units"] == 1
    assert daily_case["expected_low_information_boundary"]["must_not_route_to"] == (
        "low_information_question"
    )
    assert "まだ詳しい出来事までは見えません" in daily_case["forbidden_surface_fragments"]
    assert "何があったか残してみませんか" in daily_case["forbidden_surface_fragments"]

    self_confidence_case = two_stage_reception_case_by_id("self_confidence_uncertainty_B")
    assert self_confidence_case["expected_reception_mode_any"] == (
        "self_denial_support",
        "uncertainty_support",
    )
    assert self_confidence_case["expected_ratio_contract"]["follow_thickened"] is True
    assert "中途半端な人" in self_confidence_case["forbidden_surface_fragments"]
    assert "得意こと" in self_confidence_case["forbidden_surface_fragments"]

    log1_case = two_stage_reception_case_by_id("positive_change_after_work_streaming")
    assert log1_case["expected_reception_mode_any"] == (
        "daily_positive_reception",
        "self_understanding_follow",
    )

    log2_case = two_stage_reception_case_by_id("self_blame_to_gentle_self_observation")
    assert log2_case["expected_reception_mode"] == "self_understanding_follow"

    log3_case = two_stage_reception_case_by_id("independence_life_health_money_pace")
    assert log3_case["expected_reception_mode_any"] == (
        "standard_state_answer",
        "effort_support",
    )


def test_two_stage_comment_text_shape_helper_does_not_require_exact_surface() -> None:
    sample = "見えたこと：\n入力から見える範囲の観測です。\n\nEmlisから：\n受け取りの文です。"
    sections = split_two_stage_comment_text(sample)
    assert sections == {
        "labels_present": True,
        "label_order_valid": True,
        "observation_text": "入力から見える範囲の観測です。",
        "reception_text": "受け取りの文です。",
    }

    assert split_two_stage_comment_text("Emlisから：\n先に出た文\n\n見えたこと：\n後の文") == {
        "labels_present": True,
        "label_order_valid": False,
        "observation_text": "",
        "reception_text": "",
    }
    assert split_two_stage_comment_text("ラベルなし") == {
        "labels_present": False,
        "label_order_valid": False,
        "observation_text": "",
        "reception_text": "",
    }


def test_forbidden_surface_helper_is_case_specific() -> None:
    daily_case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    surface = "見えたこと：\nまだ詳しい出来事までは見えません。\n\nEmlisから：\n何があったか残してみませんか。"
    blocked = evaluate_forbidden_surface_fragments(surface, daily_case)
    assert blocked == ("まだ詳しい出来事までは見えません", "何があったか残してみませんか")

    safe_surface = "見えたこと：\n入力から見える範囲の観測です。\n\nEmlisから：\n受け取りの文です。"
    assert evaluate_forbidden_surface_fragments(safe_surface, daily_case) == ()


def test_label_markers_are_the_only_initial_surface_joiner_requirement() -> None:
    assert TWO_STAGE_LABEL_MARKERS == {
        "observation": "見えたこと：",
        "reception": "Emlisから：",
    }
    assert "observation_text" not in PHASE0_DESIGN_LOCK["fixed_boundaries"]
    assert "reception_text" not in PHASE0_DESIGN_LOCK["fixed_boundaries"]


_PHASE13_EXPECTED_QUALITY_AXES = {
    "daily_unpleasant_encounter_A": (
        "daily_unpleasant_observation",
        "natural_short_reception",
        "event_fact_not_missing",
        "explicit_reaction_received",
    ),
    "self_confidence_uncertainty_B": (
        "self_denial_not_fact",
        "effort_or_attempt_received",
        "uncertainty_received",
    ),
    "positive_change_after_work_streaming": (
        "positive_change_seen",
        "surprise_or_emotional_movement_received",
        "restriction_not_action_instruction",
    ),
    "self_blame_to_gentle_self_observation": (
        "self_blame_flow_seen",
        "gentle_observation_direction_seen",
        "small_effort_received",
    ),
    "independence_life_health_money_pace": (
        "independence_intention_seen",
        "health_pace_seen",
        "life_money_context_seen",
    ),
}

_SENTENCE_RE = re.compile(r"[。！？!?]+|[\r\n]+")


def _sentence_count(value: str) -> int:
    return len([part.strip() for part in _SENTENCE_RE.split(value or "") if part.strip()])


def _assert_fragment_groups(surface: str, groups: tuple[tuple[str, ...], ...], *, present: bool) -> None:
    for group in groups:
        if present:
            assert all(fragment in surface for fragment in group), group
        else:
            assert not any(fragment in surface for fragment in group), group


def test_phase13_display_quality_qa_case_set_matches_two_stage_fixtures() -> None:
    assert PHASE13_TWO_STAGE_DISPLAY_QA_VERSION == (
        "cocolon.emlis_two_stage_reception.display_quality_qa.v1"
    )
    assert PHASE13_TWO_STAGE_DISPLAY_QA_CASE_IDS == TWO_STAGE_RECEPTION_REQUIRED_CASE_IDS
    assert set(_PHASE13_EXPECTED_QUALITY_AXES) == TWO_STAGE_RECEPTION_REQUIRED_CASE_IDS


@pytest.mark.parametrize("case", TWO_STAGE_RECEPTION_CASES, ids=lambda case: case["case_id"])
def test_phase13_display_quality_matrix_matches_fixture_boundaries(case: dict) -> None:
    expected_axes = _PHASE13_EXPECTED_QUALITY_AXES[case["case_id"]]
    assert set(expected_axes).issubset(set(case["required_surface_features"]))
    assert case["expected_low_information_boundary"]["low_information_question_required"] is False
    assert case["expected_low_information_boundary"]["low_information_question_allowed"] is False
    assert case["expected_section_shape"] == COMMON_SECTION_SHAPE_EXPECTATION
    assert case["expected_section_shape"]["exact_text_match_required"] is False

    if case["case_id"] == "daily_unpleasant_encounter_A":
        assert case["expected_reception_mode"] == "daily_unpleasant_reception"
        assert case["expected_ratio_contract"]["range_key"] == "daily_reception"
        assert "何があったか残してみませんか" in case["forbidden_surface_fragments"]
        assert "target_judgement_agreement" in case["forbidden_inferences"]
    if case["case_id"] == "self_confidence_uncertainty_B":
        assert case["expected_reception_mode_any"] == ("self_denial_support", "uncertainty_support")
        assert "中途半端な人" in case["forbidden_surface_fragments"]
        assert "identity_claim_accepted_as_fact" in case["forbidden_inferences"]
    if case["case_id"] == "positive_change_after_work_streaming":
        assert "我慢しなくていいです" in case["forbidden_surface_fragments"]
        assert "action_instruction" in case["forbidden_inferences"]
    if case["case_id"] == "self_blame_to_gentle_self_observation":
        assert "成長しています" in case["forbidden_surface_fragments"]
        assert "stable_growth_assertion" in case["forbidden_inferences"]
    if case["case_id"] == "independence_life_health_money_pace":
        assert "自立できます" in case["forbidden_surface_fragments"]
        assert "future_success_assertion" in case["forbidden_inferences"]


@pytest.mark.parametrize(
    "qa_case",
    PHASE13_TWO_STAGE_DISPLAY_QA_CASES,
    ids=[case["case_id"] for case in PHASE13_TWO_STAGE_DISPLAY_QA_CASES],
)
def test_phase13_display_quality_accepted_surface_probes_match_fixture_contracts(qa_case: dict) -> None:
    fixture_case = two_stage_reception_case_by_id(qa_case["case_id"])
    surface = qa_case["accepted_surface_probe"]
    sections = split_two_stage_comment_text(surface)

    assert qa_case["reception_mode"] in fixture_case["expected_reception_mode_any"]
    assert sections["labels_present"] is True
    assert sections["label_order_valid"] is True
    assert sections["observation_text"]
    assert sections["reception_text"]
    assert evaluate_forbidden_surface_fragments(surface, fixture_case) == ()
    assert qa_case["observation_sentence_count_min"] <= _sentence_count(sections["observation_text"]) <= qa_case["observation_sentence_count_max"]
    assert qa_case["reception_sentence_count_min"] <= _sentence_count(sections["reception_text"]) <= qa_case["reception_sentence_count_max"]
    _assert_fragment_groups(surface, qa_case["required_fragment_groups"], present=True)
    _assert_fragment_groups(surface, qa_case["forbidden_fragment_groups"], present=False)


@pytest.mark.parametrize(
    "blocked_probe",
    iter_phase13_blocked_surface_probes(),
    ids=[probe["probe_id"] for probe in iter_phase13_blocked_surface_probes()],
)
def test_phase13_blocked_surface_probes_keep_two_stage_shape_but_hit_forbidden_examples(blocked_probe: dict) -> None:
    fixture_case = two_stage_reception_case_by_id(blocked_probe["case_id"])
    surface = blocked_probe["surface"]
    sections = split_two_stage_comment_text(surface)

    assert sections["labels_present"] is True
    assert sections["label_order_valid"] is True
    assert evaluate_forbidden_surface_fragments(surface, fixture_case) or blocked_probe["expected_reason_any"]
