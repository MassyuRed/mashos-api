# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_reception_assistance_dictionary_loader import (
    RECEPTION_ASSISTANCE_DICTIONARY_ID,
    RECEPTION_ASSISTANCE_DICTIONARY_LOADER_PHASE,
    RECEPTION_ASSISTANCE_DICTIONARY_MATERIAL_ID,
    RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION,
    assert_emlis_reception_assistance_dictionary_contract,
    event_hint_can_create_emotion,
    get_reception_assistance_unknown_word_policy,
    load_reception_assistance_dictionary,
    select_reception_assistance_event_hints,
    select_reception_assistance_modes,
    select_reception_assistance_reaction_cues,
    validate_reception_assistance_dictionary_payload,
)
from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta
from fixtures.emlis_ai_two_stage_reception_cases import (
    current_input_for_two_stage_reception_case,
    two_stage_reception_case_by_id,
)


def _dictionary_payload() -> dict:
    return load_reception_assistance_dictionary().as_payload()


def test_phase3_reception_assistance_dictionary_loads_as_skeleton_material() -> None:
    dictionary = load_reception_assistance_dictionary()
    meta = dictionary.as_meta()

    assert meta["schema_version"] == RECEPTION_ASSISTANCE_DICTIONARY_SCHEMA_VERSION
    assert meta["dictionary_id"] == RECEPTION_ASSISTANCE_DICTIONARY_ID
    assert meta["loader_phase"] == RECEPTION_ASSISTANCE_DICTIONARY_LOADER_PHASE
    assert meta["material_id"] == RECEPTION_ASSISTANCE_DICTIONARY_MATERIAL_ID
    assert meta["reception_assistance_dictionary_ready"] is True
    assert meta["dictionary_material_only"] is True

    assert meta["reaction_cue_count"] >= 4
    assert {"disgust", "fear", "anger_irritation", "joy_or_surprise"}.issubset(
        set(meta["reaction_cue_ids"])
    )
    assert "public_unpleasant_encounter" in meta["event_hint_ids"]
    assert "daily_unpleasant_reception" in meta["reception_mode_ids"]
    assert "natural_short_reception" in meta["tone_family_ids"]
    assert "daily_unpleasant_brief_receiving" in meta["follow_shape_family_ids"]


@pytest.mark.parametrize(
    "required_true_policy",
    [
        "not_general_dictionary",
        "user_reaction_is_primary",
        "event_hint_must_not_create_emotion",
        "unknown_word_meaning_must_not_be_asserted",
        "completed_reply_template_forbidden",
    ],
)
def test_phase3_dictionary_global_policies_keep_it_outside_general_dictionary(
    required_true_policy: str,
) -> None:
    payload = _dictionary_payload()
    meta = load_reception_assistance_dictionary().as_meta()

    assert payload["global_policies"][required_true_policy] is True
    assert meta["global_policies"][required_true_policy] is True


@pytest.mark.parametrize(
    "required_false_boundary",
    [
        "public_response_key_added",
        "comment_text_generated_by_dictionary",
        "raw_input_included",
        "raw_text_included",
        "general_knowledge_primary",
        "rn_visible_contract_changed",
        "api_route_changed",
        "db_physical_name_changed",
    ],
)
def test_phase3_dictionary_keeps_public_contract_boundaries_false(
    required_false_boundary: str,
) -> None:
    payload = _dictionary_payload()
    meta = load_reception_assistance_dictionary().as_meta()

    assert payload["contract_boundaries"][required_false_boundary] is False
    assert meta["contract_boundaries"][required_false_boundary] is False
    assert meta[required_false_boundary] is False


def test_phase3_dictionary_has_unknown_word_policy_without_meaning_assertion() -> None:
    dictionary = load_reception_assistance_dictionary()
    unknown_word_policy = get_reception_assistance_unknown_word_policy(dictionary)

    assert unknown_word_policy == {
        "general_dictionary_used": False,
        "unknown_word_meaning_asserted": False,
        "meaning_assertion_allowed": False,
        "event_hint_can_support_mode_only": True,
        "event_hint_must_not_create_emotion": True,
    }
    assert dictionary.as_meta()["unknown_word_policy"] == unknown_word_policy


def test_phase3_dictionary_contains_no_completed_reply_templates() -> None:
    payload = _dictionary_payload()
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    forbidden_completed_reply_fragments = (
        "うわ、それは嫌でしたね。",
        "怖さも怒りも残るのは自然です。",
        "Emlisには、ここにあるものが「中途半端」だけだとは見えません。",
        '"comment_text"',
        '"completed_reply_text"',
        '"observation_text"',
        '"reception_text"',
        '"meaning"',
        '"definition"',
    )
    for fragment in forbidden_completed_reply_fragments:
        assert fragment not in encoded

    for shape in payload["follow_shape_families"]:
        assert shape["template_text_forbidden"] is True
        assert "allowed_intents" in shape
        assert "forbidden_intents" in shape


def test_phase3_dictionary_maps_A_reactions_but_does_not_define_tachishon_as_meaning() -> None:
    dictionary = load_reception_assistance_dictionary()
    thought = "この世で1番気持ち悪い瞬間に出くわしてしまいイライラが止まらなかった。＆恐怖"
    action = "立ちションのおじさんとすれ違ってしまった"

    assert [cue["cue_id"] for cue in select_reception_assistance_reaction_cues(dictionary, surface_text=thought)] == [
        "disgust",
        "fear",
        "anger_irritation",
    ]
    assert select_reception_assistance_reaction_cues(dictionary, surface_text=action) == []
    assert [hint["hint_id"] for hint in select_reception_assistance_event_hints(dictionary, surface_text=action)] == [
        "public_unpleasant_encounter",
    ]

    hint = select_reception_assistance_event_hints(dictionary, hint_id="public_unpleasant_encounter")[0]
    assert hint["event_family"] == "daily_event_encounter"
    assert hint["can_support_modes"] == ["daily_unpleasant_reception"]
    assert {"fear", "anger", "disgust", "danger", "trauma"}.issubset(
        set(hint["cannot_alone_infer"])
    )
    assert event_hint_can_create_emotion(dictionary, "public_unpleasant_encounter") is False


def test_phase3_dictionary_daily_unpleasant_mode_is_material_not_runtime_surface() -> None:
    dictionary = load_reception_assistance_dictionary()
    mode = select_reception_assistance_modes(dictionary, mode_id="daily_unpleasant_reception")[0]

    assert mode["activation"]["requires_event_fact_present"] is True
    assert mode["activation"]["requires_reaction_present"] is True
    assert mode["activation"]["event_hint_alone_can_activate"] is False
    assert set(mode["activation"]["requires_any_reaction_family"]) == {
        "negative_daily_reaction",
        "fear_reaction",
        "anger_reaction",
    }
    assert mode["ratio_preset"] == "daily_unpleasant_reception_light"
    assert mode["observation_policy"]["max_sentences"] == 1
    assert mode["observation_policy"]["must_not_prompt_for_event_if_event_fact_present"] is True
    assert mode["reception_policy"]["allowed_tone_family"] == "natural_short_reception"
    assert "target_judgement_agreement" in mode["forbidden"]
    assert "unknown_word_meaning_assertion" in mode["forbidden"]


def test_phase3_dictionary_reaction_cues_have_forbidden_inference_boundaries() -> None:
    dictionary = load_reception_assistance_dictionary()

    anger_cue = select_reception_assistance_reaction_cues(dictionary, cue_id="anger_irritation")[0]
    assert anger_cue["reaction_family"] == "anger_reaction"
    assert set(anger_cue["must_not_infer"]) == {
        "target_is_bad",
        "anger_is_correct",
        "attack_is_justified",
    }

    self_denial_cue = select_reception_assistance_reaction_cues(dictionary, cue_id="self_denial")[0]
    assert "identity_is_true" in self_denial_cue["must_not_infer"]
    assert "self_denial_support" in self_denial_cue["allowed_reception_modes"]


@pytest.mark.parametrize(
    ("case_id", "expected_hints"),
    [
        ("daily_unpleasant_encounter_A", ("public_unpleasant_encounter",)),
        ("self_confidence_uncertainty_B", ("self_confidence_uncertainty_attempt",)),
        ("positive_change_after_work_streaming", ("positive_change_after_work_streaming",)),
        ("self_blame_to_gentle_self_observation", ("self_blame_to_gentle_self_observation",)),
        ("independence_life_health_money_pace", ("independence_life_health_money_pace",)),
    ],
)
def test_phase3_dictionary_covers_phase1_fixture_signal_ids_from_shared_evidence(
    case_id: str,
    expected_hints: tuple[str, ...],
) -> None:
    dictionary = load_reception_assistance_dictionary()
    case = two_stage_reception_case_by_id(case_id)
    meta = build_emlis_shared_reception_evidence_meta(current_input_for_two_stage_reception_case(case))

    dictionary_cue_ids = set(dictionary.as_meta()["reaction_cue_ids"])
    dictionary_hint_ids = set(dictionary.as_meta()["event_hint_ids"])
    dictionary_mode_ids = set(dictionary.as_meta()["reception_mode_ids"])

    for cue_id in meta["explicit_reaction_cue_ids"]:
        assert cue_id in dictionary_cue_ids
    for hint_id in expected_hints:
        assert hint_id in meta["event_hint_ids"]
        assert hint_id in dictionary_hint_ids
    for mode_id in meta["reception_candidate_mode_ids"]:
        assert mode_id in dictionary_mode_ids


def test_phase3_dictionary_meta_contract_has_no_raw_or_public_surface_payload() -> None:
    dictionary = load_reception_assistance_dictionary()
    meta = dictionary.as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert_emlis_reception_assistance_dictionary_contract(meta)
    assert meta["general_dictionary_used"] is False
    assert meta["general_knowledge_primary"] is False
    assert meta["completed_reply_generated"] is False
    assert meta["comment_text_generated_by_dictionary"] is False
    assert meta["public_response_key_added"] is False
    assert meta["unknown_word_meaning_asserted"] is False
    assert meta["event_hint_created_emotion"] is False
    assert '"surface_patterns"' not in encoded
    assert '"comment_text"' not in encoded
    assert '"raw_text"' not in encoded

    with pytest.raises(ValueError, match="general_dictionary_used"):
        assert_emlis_reception_assistance_dictionary_contract({**meta, "general_dictionary_used": True})
    with pytest.raises(ValueError, match="unknown_word_meaning_asserted"):
        assert_emlis_reception_assistance_dictionary_contract({**meta, "unknown_word_meaning_asserted": True})
    with pytest.raises(ValueError, match="payload keys"):
        assert_emlis_reception_assistance_dictionary_contract({**meta, "comment_text": "見えたこと：..."})


def test_phase3_dictionary_validator_rejects_duplicate_ids_and_undefined_references() -> None:
    payload = _dictionary_payload()

    duplicate_cue = copy.deepcopy(payload)
    duplicate_cue["reaction_cues"].append(copy.deepcopy(duplicate_cue["reaction_cues"][0]))
    with pytest.raises(ValueError, match="duplicate.*cue_id"):
        validate_reception_assistance_dictionary_payload(duplicate_cue)

    duplicate_hint = copy.deepcopy(payload)
    duplicate_hint["event_hints"].append(copy.deepcopy(duplicate_hint["event_hints"][0]))
    with pytest.raises(ValueError, match="duplicate.*hint_id"):
        validate_reception_assistance_dictionary_payload(duplicate_hint)

    undefined_mode = copy.deepcopy(payload)
    undefined_mode["reaction_cues"][0]["allowed_reception_modes"].append("missing_mode")
    with pytest.raises(ValueError, match="undefined reception mode"):
        validate_reception_assistance_dictionary_payload(undefined_mode)

    undefined_tone = copy.deepcopy(payload)
    undefined_tone["reception_modes"][0]["reception_policy"]["allowed_tone_family"] = "missing_tone"
    with pytest.raises(ValueError, match="undefined tone family"):
        validate_reception_assistance_dictionary_payload(undefined_tone)


def test_phase3_dictionary_validator_rejects_contract_drift() -> None:
    payload = _dictionary_payload()

    general_dictionary = copy.deepcopy(payload)
    general_dictionary["global_policies"]["not_general_dictionary"] = False
    with pytest.raises(ValueError, match="not_general_dictionary"):
        validate_reception_assistance_dictionary_payload(general_dictionary)

    completed_template = copy.deepcopy(payload)
    completed_template["follow_shape_families"][0]["template_text_forbidden"] = False
    with pytest.raises(ValueError, match="template text"):
        validate_reception_assistance_dictionary_payload(completed_template)

    response_key_added = copy.deepcopy(payload)
    response_key_added["contract_boundaries"]["public_response_key_added"] = True
    with pytest.raises(ValueError, match="public_response_key_added"):
        validate_reception_assistance_dictionary_payload(response_key_added)

    raw_key = copy.deepcopy(payload)
    raw_key["reception_modes"][0]["comment_text"] = "見えたこと：..."
    with pytest.raises(ValueError, match="payload keys"):
        validate_reception_assistance_dictionary_payload(raw_key)

    event_hint_emotion_creation = copy.deepcopy(payload)
    event_hint_emotion_creation["event_hints"][0]["inferred_reaction_cue_ids"] = ["fear"]
    with pytest.raises(ValueError, match="emotion-creation key"):
        validate_reception_assistance_dictionary_payload(event_hint_emotion_creation)
