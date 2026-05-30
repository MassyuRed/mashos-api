from __future__ import annotations

import json

from emlis_ai_observation_eligibility_service import (
    OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED,
    assert_observation_eligibility_decision_contract,
    dump_observation_eligibility_decision,
    route_observation_eligibility,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
)
from fixtures.emlis_ai_two_stage_reception_cases import (
    current_input_for_two_stage_reception_case,
    two_stage_reception_case_by_id,
)


def _tired_only_input() -> dict:
    return {
        "id": "phase5-fatigue-only",
        "created_at": "2026-05-26T05:00:00Z",
        "memo": "疲れた",
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
        "is_secret": False,
    }


def _event_hint_only_input() -> dict:
    return {
        "id": "phase5-event-hint-only",
        "created_at": "2026-05-26T05:10:00Z",
        "memo": "",
        "memo_action": "立ちションのおじさんとすれ違った",
        "emotion_details": [],
        "emotions": [],
        "category": ["生活"],
        "is_secret": False,
    }


def _safety_with_event_and_reaction_input() -> dict:
    return {
        "id": "phase5-safety-with-event-reaction",
        "created_at": "2026-05-26T05:20:00Z",
        "memo": "怖くて消えたい気持ちが強い",
        "memo_action": "外で嫌な出来事があった",
        "emotion_details": [{"type": "恐怖", "strength": "strong"}],
        "emotions": ["恐怖"],
        "category": ["生活"],
        "is_secret": False,
    }


def test_phase5_daily_unpleasant_event_reaction_routes_to_eligible_observation() -> None:
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    current_input = current_input_for_two_stage_reception_case(case)

    meta = route_observation_eligibility(current_input=current_input).as_meta()
    material = meta["daily_reception_router_material"]

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["eligible_for_full_observation"] is True
    assert meta["question_required"] is False
    assert meta["primary_reason"] == "current_input_has_daily_reception_basis"
    assert meta["current_input_has_daily_reception_basis"] is True
    assert meta["current_input_has_action_event_fact"] is True
    assert meta["current_input_has_explicit_reaction"] is True
    assert material["current_input_has_daily_reception_basis"] is True
    assert material["current_input_has_action_event_fact"] is True
    assert material["current_input_has_explicit_reaction"] is True
    assert material["reception_mode_id"] == "daily_unpleasant_reception"
    assert material["low_information_question_allowed"] is False
    assert material["low_information_question_required"] is False
    assert material["daily_reception_is_public_status"] is False
    assert meta["reception_mode_id"] == "daily_unpleasant_reception"
    assert meta["daily_reception_is_public_status"] is False
    assert meta["public_status_extended"] is False
    assert meta["observation_status_enum_extended"] is False
    assert meta["comment_text_generated"] is False
    assert meta["unknown_slots"] == []
    assert "event_fact" in meta["detected_signal_roles"]
    assert "daily_reaction" in meta["detected_signal_roles"]
    assert "daily_unpleasant" in meta["detected_signal_roles"]
    assert "low_info_question" not in meta["observation_reply_meta"]["sentence_plan_observation_roles"]
    assert meta["observation_reply_meta"]["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE

    assert_observation_eligibility_decision_contract(meta)


def test_phase5_daily_router_meta_is_text_free_and_does_not_change_public_contract() -> None:
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    current_input = current_input_for_two_stage_reception_case(case)

    dumped = dump_observation_eligibility_decision(route_observation_eligibility(current_input=current_input))
    parsed = json.loads(dumped)

    assert current_input["memo"] not in dumped
    assert current_input["memo_action"] not in dumped
    assert current_input["id"] not in dumped
    assert '"raw_text"' not in dumped
    assert '"comment_text"' not in dumped
    material = parsed["daily_reception_router_material"]
    assert material["raw_input_included"] is False
    assert material["raw_text_included"] is False
    assert material["comment_text_included"] is False
    assert material["comment_text_body_included"] is False
    assert material["daily_reception_is_public_status"] is False
    assert parsed["rn_visible_contract_changed"] is False
    assert parsed["api_route_changed"] is False
    assert parsed["db_physical_name_changed"] is False


def test_phase5_reaction_without_event_fact_stays_low_information_observation() -> None:
    meta = route_observation_eligibility(current_input=_tired_only_input()).as_meta()
    material = meta["daily_reception_router_material"]

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert meta["current_input_has_daily_reception_basis"] is False
    assert meta["current_input_has_action_event_fact"] is False
    assert meta["current_input_has_explicit_reaction"] is True
    assert material["current_input_has_action_event_fact"] is False
    assert material["current_input_has_explicit_reaction"] is True
    assert material["current_input_has_daily_reception_basis"] is False
    assert meta["observation_reply_meta"]["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION


def test_phase5_event_hint_alone_does_not_create_daily_reception_or_emotion() -> None:
    meta = route_observation_eligibility(current_input=_event_hint_only_input()).as_meta()
    material = meta["daily_reception_router_material"]

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["question_required"] is True
    assert meta["current_input_has_action_event_fact"] is True
    assert meta["current_input_has_explicit_reaction"] is False
    assert meta["current_input_has_daily_reception_basis"] is False
    assert material["event_hint_ids"] == ["public_unpleasant_encounter"]
    assert material["unknown_word_meaning_asserted"] is False
    assert material["general_dictionary_used"] is False
    assert material["event_hint_created_emotion"] is False


def test_phase5_safety_boundary_stays_existing_safety_route_even_with_event_and_reaction() -> None:
    meta = route_observation_eligibility(current_input=_safety_with_event_and_reaction_input()).as_meta()

    assert meta["status"] == OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED
    assert meta["observation_reply_kind"] == OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is False
    assert meta["primary_reason"] == "safety_boundary_required"
    assert meta["public_status_extended"] is False
    assert meta["observation_status_enum_extended"] is False
