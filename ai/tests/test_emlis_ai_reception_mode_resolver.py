# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence
from emlis_ai_reception_mode_resolver import (
    EMLIS_RECEPTION_MODE_RESOLUTION_MATERIAL_ID,
    EMLIS_RECEPTION_MODE_RESOLUTION_SCHEMA_VERSION,
    EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE,
    MODE_DAILY_UNPLEASANT,
    MODE_LOW_INFORMATION,
    MODE_SAFETY_EXISTING_PATH,
    MODE_SELF_DENIAL,
    MODE_STRUCTURE,
    MODE_UNCERTAINTY,
    assert_emlis_reception_mode_resolution_contract,
    resolve_emlis_reception_mode,
    resolve_emlis_reception_mode_meta,
)
from fixtures.emlis_ai_two_stage_reception_cases import (
    TWO_STAGE_RECEPTION_CASES,
    current_input_for_two_stage_reception_case,
    two_stage_reception_case_by_id,
)


def _meta_for_case(case_id: str) -> dict:
    case = two_stage_reception_case_by_id(case_id)
    return resolve_emlis_reception_mode_meta(current_input_for_two_stage_reception_case(case))


def test_phase4_reception_mode_resolver_resolves_A_to_daily_unpleasant_not_low_information() -> None:
    meta = _meta_for_case("daily_unpleasant_encounter_A")

    assert meta["schema_version"] == EMLIS_RECEPTION_MODE_RESOLUTION_SCHEMA_VERSION
    assert meta["source_phase"] == EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE
    assert meta["material_id"] == EMLIS_RECEPTION_MODE_RESOLUTION_MATERIAL_ID
    assert meta["reception_mode_resolver_ready"] is True

    assert meta["reception_mode"] == MODE_DAILY_UNPLEASANT
    assert meta["primary_reason"] == "event_fact_with_explicit_negative_reaction"
    assert meta["event_fact_present"] is True
    assert meta["reaction_present"] is True
    assert meta["low_information_question_allowed"] is False
    assert meta["low_information_question_required"] is False
    assert meta["question_required"] is False
    assert meta["observation_reply_kind"] == "eligible_observation"
    assert meta["ratio_preset"] == "daily_unpleasant_reception_light"
    assert {"negative_daily_reaction", "fear_reaction", "anger_reaction"}.issubset(
        set(meta["reaction_family_ids"])
    )
    assert "public_unpleasant_encounter" in meta["event_hint_ids"]
    assert meta["event_hint_created_emotion"] is False
    assert meta["event_hint_alone_activated_mode"] is False


def test_phase4_reception_mode_resolver_resolves_B_to_self_support_not_daily_reception() -> None:
    meta = _meta_for_case("self_confidence_uncertainty_B")

    assert meta["reception_mode"] in {MODE_SELF_DENIAL, MODE_UNCERTAINTY}
    assert meta["reception_mode"] != MODE_DAILY_UNPLEASANT
    assert meta["low_information_question_allowed"] is False
    assert meta["event_fact_present"] is False
    assert meta["reaction_present"] is True
    assert "self_negative_reaction" in meta["reaction_family_ids"]
    assert "uncertainty_reaction" in meta["reaction_family_ids"]
    assert meta["mode_selection_contract"]["self_denial_must_not_be_lightly_daily"] is True
    assert meta["identity_claim_accepted_as_fact"] is False
    assert meta["action_instruction_allowed"] is False


@pytest.mark.parametrize("case", TWO_STAGE_RECEPTION_CASES, ids=lambda case: case["case_id"])
def test_phase4_reception_mode_resolver_matches_phase1_fixture_expected_modes(case: dict) -> None:
    meta = resolve_emlis_reception_mode_meta(current_input_for_two_stage_reception_case(case))

    assert meta["reception_mode"] in set(case["expected_reception_mode_any"])
    assert meta["low_information_question_allowed"] is False
    assert meta["low_information_question_required"] is False
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["observation_status_enum_extended"] is False
    assert meta["general_dictionary_used"] is False
    assert meta["unknown_word_meaning_asserted"] is False
    assert meta["event_hint_created_emotion"] is False


def test_phase4_event_hint_alone_does_not_activate_daily_unpleasant_reception() -> None:
    current_input = {
        "id": "phase4-event-hint-alone",
        "created_at": "2026-05-26T02:00:00Z",
        "memo": "",
        "memo_action": "立ちションのおじさんとすれ違った",
        "emotion_details": [],
        "emotions": [],
        "category": ["生活"],
        "is_secret": False,
    }

    meta = resolve_emlis_reception_mode_meta(current_input)

    assert meta["event_fact_present"] is True
    assert meta["reaction_present"] is False
    assert meta["event_hint_ids"] == ["public_unpleasant_encounter"]
    assert meta["reception_mode"] == MODE_LOW_INFORMATION
    assert meta["reception_mode"] != MODE_DAILY_UNPLEASANT
    assert meta["low_information_question_allowed"] is True
    assert meta["low_information_question_required"] is True
    assert meta["event_hint_created_emotion"] is False
    assert meta["event_hint_alone_activated_mode"] is False


def test_phase4_structure_question_routes_to_observation_thickened_internal_mode() -> None:
    current_input = {
        "id": "phase4-structure-question",
        "created_at": "2026-05-26T02:10:00Z",
        "memo": "この反応の構造を知りたい。なぜこうなるのか知りたい。",
        "memo_action": "",
        "emotion_details": [{"type": "平穏", "strength": "medium"}],
        "emotions": ["平穏"],
        "category": ["価値観"],
        "is_secret": False,
    }

    meta = resolve_emlis_reception_mode_meta(current_input)

    assert meta["reception_mode"] == MODE_STRUCTURE
    assert meta["primary_reason"] == "explicit_structure_question_observation_thickened"
    assert meta["structure_question_requested"] is True
    assert meta["observation_reply_kind"] == "eligible_observation"
    assert meta["ratio_preset"] == "structure_question_observation_thickened"
    assert meta["mode_policy"]["observation_policy"]["observation_thickened"] is True
    assert meta["public_status_extended"] is False


def test_phase4_safety_risk_routes_to_existing_safety_path_without_generation() -> None:
    current_input = {
        "id": "phase4-safety-boundary",
        "created_at": "2026-05-26T02:20:00Z",
        "memo": "消えたい気持ちが強い",
        "memo_action": "",
        "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
        "emotions": ["悲しみ"],
        "category": ["生活"],
        "is_secret": False,
    }

    meta = resolve_emlis_reception_mode_meta(current_input)

    assert meta["reception_mode"] == MODE_SAFETY_EXISTING_PATH
    assert meta["primary_reason"] == "safety_boundary_existing_path_required"
    assert meta["safety_path_required"] is True
    assert meta["existing_safety_path_required"] is True
    assert "self_harm" in meta["safety_boundary_type_ids"]
    assert meta["observation_reply_kind"] == "safety_blocked"
    assert meta["low_information_question_allowed"] is False
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False


def test_phase4_reception_mode_resolution_meta_has_no_raw_text_or_public_surface_payload() -> None:
    current_input = current_input_for_two_stage_reception_case(
        two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    )
    meta = resolve_emlis_reception_mode_meta(current_input)
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert_emlis_reception_mode_resolution_contract(meta)
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert current_input["id"] not in encoded
    assert '"memo"' not in encoded
    assert '"memo_action"' not in encoded
    assert '"raw_text"' not in encoded
    assert '"comment_text"' not in encoded
    assert '"observation_text"' not in encoded
    assert '"reception_text"' not in encoded
    assert meta["public_response_key_added"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["unknown_word_meaning_asserted"] is False

    with pytest.raises(ValueError, match="general_dictionary_used"):
        assert_emlis_reception_mode_resolution_contract({**meta, "general_dictionary_used": True})
    with pytest.raises(ValueError, match="raw/public text payload key"):
        assert_emlis_reception_mode_resolution_contract({**meta, "comment_text": "見えたこと：..."})


def test_phase4_reception_mode_resolution_accepts_prebuilt_shared_evidence_without_raw_input() -> None:
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    resolution = resolve_emlis_reception_mode(
        shared_evidence=build_emlis_shared_reception_evidence(
            current_input_for_two_stage_reception_case(case)
        )
    )

    assert resolution.reception_mode == MODE_DAILY_UNPLEASANT
    assert resolution.low_information_question_allowed is False
    assert resolution.as_meta()["comment_text_generated"] is False
