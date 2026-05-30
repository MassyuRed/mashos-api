# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_shared_reception_evidence import (
    EMLIS_SHARED_RECEPTION_EVIDENCE_MATERIAL_ID,
    EMLIS_SHARED_RECEPTION_EVIDENCE_SCHEMA_VERSION,
    EMLIS_SHARED_RECEPTION_EVIDENCE_SOURCE_PHASE,
    assert_emlis_shared_reception_evidence_contract,
    build_emlis_shared_reception_evidence,
    build_emlis_shared_reception_evidence_meta,
)
from fixtures.emlis_ai_two_stage_reception_cases import (
    TWO_STAGE_RECEPTION_CASES,
    current_input_for_two_stage_reception_case,
    two_stage_reception_case_by_id,
)


def _encoded_meta(current_input: dict) -> tuple[dict, str]:
    meta = build_emlis_shared_reception_evidence_meta(current_input)
    return meta, json.dumps(meta, ensure_ascii=False, sort_keys=True)


def test_phase2_shared_reception_evidence_detects_A_daily_unpleasant_basis() -> None:
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    current_input = current_input_for_two_stage_reception_case(case)

    evidence = build_emlis_shared_reception_evidence(current_input)
    meta = evidence.as_meta()

    assert meta["schema_version"] == EMLIS_SHARED_RECEPTION_EVIDENCE_SCHEMA_VERSION
    assert meta["source_phase"] == EMLIS_SHARED_RECEPTION_EVIDENCE_SOURCE_PHASE
    assert meta["material_id"] == EMLIS_SHARED_RECEPTION_EVIDENCE_MATERIAL_ID
    assert meta["shared_reception_evidence_ready"] is True

    assert evidence.event_fact_present is True
    assert meta["event_fact_present"] is True
    assert meta["event_fact_source_fields"] == ["memo_action"]
    assert meta["event_fact_count"] == 1

    assert evidence.reaction_present is True
    assert meta["reaction_present"] is True
    assert meta["reaction_source_fields"] == ["memo", "emotion_details"]
    assert meta["explicit_reaction_cue_ids"] == ["disgust", "anger_irritation", "fear"]
    assert meta["explicit_emotion_label_ids"] == ["anger"]
    assert meta["category_topic_ids"] == ["life"]
    assert meta["event_hint_ids"] == ["public_unpleasant_encounter"]
    assert meta["reception_candidate_mode_ids"] == ["daily_unpleasant_reception"]
    assert meta["primary_reason"] == "event_fact_with_explicit_negative_reaction"

    assert meta["general_dictionary_used"] is False
    assert meta["unknown_word_meaning_asserted"] is False
    assert meta["unknown_word_policy"] == {
        "unknown_word_meaning_asserted": False,
        "meaning_assertion_allowed": False,
        "event_hint_can_support_mode_only": True,
        "event_hint_must_not_create_emotion": True,
    }


@pytest.mark.parametrize("case", TWO_STAGE_RECEPTION_CASES, ids=lambda case: case["case_id"])
def test_phase2_shared_reception_evidence_builds_for_all_phase1_fixtures(case: dict) -> None:
    current_input = current_input_for_two_stage_reception_case(case)
    meta, encoded = _encoded_meta(current_input)

    assert meta["schema_version"] == EMLIS_SHARED_RECEPTION_EVIDENCE_SCHEMA_VERSION
    assert meta["source_phase"] == EMLIS_SHARED_RECEPTION_EVIDENCE_SOURCE_PHASE
    assert meta["shared_reception_evidence_ready"] is True
    assert isinstance(meta["event_fact_present"], bool)
    assert isinstance(meta["reaction_present"], bool)
    assert isinstance(meta["explicit_reaction_cue_ids"], list)
    assert isinstance(meta["event_hint_ids"], list)
    assert isinstance(meta["reception_candidate_mode_ids"], list)
    assert meta["reception_candidate_mode_ids"]
    assert meta["raw_input_included"] is False
    assert meta["raw_text_included"] is False
    assert meta["comment_text_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    assert meta["public_status_extended"] is False
    assert meta["observation_status_enum_extended"] is False
    assert meta["api_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["general_dictionary_used"] is False
    assert meta["unknown_word_meaning_asserted"] is False
    assert meta["event_hint_created_emotion"] is False
    assert meta["category_used_as_cause"] is False
    assert meta["emotion_strength_used_as_cause"] is False

    if current_input["memo"]:
        assert current_input["memo"] not in encoded
    if current_input["memo_action"]:
        assert current_input["memo_action"] not in encoded
    assert current_input["id"] not in encoded
    assert current_input["created_at"] not in encoded
    assert '"memo":' not in encoded
    assert '"memo_action":' not in encoded
    assert '"raw_text":' not in encoded
    assert '"comment_text":' not in encoded
    assert '"current_input":' not in encoded


@pytest.mark.parametrize(
    ("case_id", "expected_mode_ids", "expected_hint_ids"),
    [
        (
            "self_confidence_uncertainty_B",
            ("self_denial_support", "uncertainty_support", "self_understanding_follow"),
            ("self_confidence_uncertainty_attempt",),
        ),
        (
            "positive_change_after_work_streaming",
            ("daily_positive_reception", "self_understanding_follow"),
            ("positive_change_after_work_streaming",),
        ),
        (
            "self_blame_to_gentle_self_observation",
            ("self_denial_support", "self_understanding_follow"),
            ("self_blame_to_gentle_self_observation",),
        ),
        (
            "independence_life_health_money_pace",
            ("standard_state_answer", "effort_support"),
            ("independence_life_health_money_pace",),
        ),
    ],
)
def test_phase2_shared_reception_evidence_keeps_candidate_modes_as_internal_ids(
    case_id: str,
    expected_mode_ids: tuple[str, ...],
    expected_hint_ids: tuple[str, ...],
) -> None:
    case = two_stage_reception_case_by_id(case_id)
    meta = build_emlis_shared_reception_evidence_meta(current_input_for_two_stage_reception_case(case))

    assert meta["reaction_present"] is True
    for mode_id in expected_mode_ids:
        assert mode_id in meta["reception_candidate_mode_ids"]
    for hint_id in expected_hint_ids:
        assert hint_id in meta["event_hint_ids"]
    assert meta["general_dictionary_used"] is False
    assert meta["unknown_word_meaning_asserted"] is False


def test_event_hint_alone_does_not_create_reaction_or_daily_unpleasant_mode() -> None:
    current_input = {
        "id": "shared-evidence-event-hint-only",
        "created_at": "2026-05-26T01:00:00Z",
        "memo": "",
        "memo_action": "立ちションのおじさんとすれ違った",
        "emotion_details": [],
        "emotions": [],
        "category": ["生活"],
        "is_secret": False,
    }

    meta, encoded = _encoded_meta(current_input)

    assert meta["event_fact_present"] is True
    assert meta["event_hint_ids"] == ["public_unpleasant_encounter"]
    assert meta["reaction_present"] is False
    assert meta["explicit_reaction_cue_ids"] == []
    assert meta["explicit_emotion_label_ids"] == []
    assert "daily_unpleasant_reception" not in meta["reception_candidate_mode_ids"]
    assert meta["event_hint_created_emotion"] is False
    assert meta["unknown_word_meaning_asserted"] is False
    assert current_input["memo_action"] not in encoded


def test_reaction_without_event_fact_stays_shared_evidence_not_event_assertion() -> None:
    current_input = {
        "id": "shared-evidence-reaction-only",
        "created_at": "2026-05-26T01:10:00Z",
        "memo": "なんとなく怖いし不安",
        "memo_action": "",
        "emotion_details": [{"type": "平穏", "strength": "medium"}],
        "emotions": ["平穏"],
        "category": ["生活"],
        "is_secret": False,
    }

    meta, encoded = _encoded_meta(current_input)

    assert meta["event_fact_present"] is False
    assert meta["event_fact_source_fields"] == []
    assert meta["reaction_present"] is True
    assert meta["reaction_source_fields"] == ["memo", "emotion_details"]
    assert "fear" in meta["explicit_reaction_cue_ids"]
    assert "calm" in meta["explicit_emotion_label_ids"]
    assert meta["reception_candidate_mode_ids"] == ["uncertainty_support"]
    assert "daily_unpleasant_reception" not in meta["reception_candidate_mode_ids"]
    assert meta["category_used_as_cause"] is False
    assert current_input["memo"] not in encoded


def test_shared_reception_evidence_contract_rejects_raw_text_payload_keys_and_forbidden_flags() -> None:
    meta = build_emlis_shared_reception_evidence_meta(
        {
            "id": "shared-evidence-contract",
            "created_at": "2026-05-26T01:20:00Z",
            "memo": "嫌だった",
            "memo_action": "外で嫌な場面に出くわした",
            "emotion_details": [{"type": "怒り", "strength": "medium"}],
            "category": ["生活"],
        }
    )

    assert_emlis_shared_reception_evidence_contract(meta)

    with pytest.raises(ValueError):
        assert_emlis_shared_reception_evidence_contract({**meta, "memo": "嫌だった"})
    with pytest.raises(ValueError):
        assert_emlis_shared_reception_evidence_contract({**meta, "general_dictionary_used": True})
    with pytest.raises(ValueError):
        assert_emlis_shared_reception_evidence_contract({**meta, "unknown_word_meaning_asserted": True})
    with pytest.raises(ValueError):
        assert_emlis_shared_reception_evidence_contract({**meta, "comment_text": "見えたこと：..."})
