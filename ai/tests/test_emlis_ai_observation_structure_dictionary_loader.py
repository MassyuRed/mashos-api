from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from emlis_ai_observation_structure_dictionary_loader import (
    DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_PATH,
    DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_PATH,
    OBSERVATION_STRUCTURE_DICTIONARY_CONTRACT_STEP,
    OBSERVATION_STRUCTURE_DICTIONARY_ID,
    OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE,
    OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION,
    assert_observation_structure_dictionary_contract,
    dump_observation_structure_dictionary_contract,
    load_observation_structure_dictionary,
    load_observation_structure_dictionary_schema,
    select_observation_structure_entries,
    select_observation_structure_relations,
    validate_observation_structure_dictionary_payload,
)


EXPECTED_REQUIRED_FIELDS = {"memo", "memo_action", "emotion_details", "category"}
EXPECTED_FIELD_MAPPING = {
    "thought_text": "memo",
    "action_text": "memo_action",
    "emotions": "emotion_details",
    "emotion_strength_summary": "emotion_details",
    "categories": "category",
    "selected_at": "created_at",
    "source_record_id": "id",
}
ACTION_CONVERSION_UPDATE_RELATIONS = {
    "unexpressed_output_stop",
    "self_shape_alignment",
    "action_conversion_history",
    "conversion_history_closure",
    "unformed_self_insight",
}
ACTION_CONVERSION_UPDATE_ENTRY_IDS = {
    "word_could_not_say",
    "word_aligned_to_context",
    "word_gaman",
    "word_wakaranai",
}


def _payload() -> dict:
    with Path(DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_PATH).open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    assert isinstance(payload, dict)
    return payload


def test_phase3_default_structure_dictionary_schema_and_loader_contract() -> None:
    assert Path(DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_PATH).exists()
    assert Path(DEFAULT_OBSERVATION_STRUCTURE_DICTIONARY_PATH).exists()

    schema = load_observation_structure_dictionary_schema()
    dictionary = load_observation_structure_dictionary()
    meta = dictionary.as_meta()

    assert schema["properties"]["schema_version"]["const"] == OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION
    assert schema["properties"]["contract_step"]["const"] == OBSERVATION_STRUCTURE_DICTIONARY_CONTRACT_STEP
    assert meta["schema_version"] == OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION
    assert meta["dictionary_id"] == OBSERVATION_STRUCTURE_DICTIONARY_ID
    assert meta["contract_step"] == OBSERVATION_STRUCTURE_DICTIONARY_CONTRACT_STEP
    assert meta["loader_phase"] == OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE
    assert meta["observation_structure_dictionary_ready"] is True
    assert meta["gate_or_composer_connected"] is False
    assert meta["entry_count"] == 18
    assert meta["relation_count"] == 19
    assert ACTION_CONVERSION_UPDATE_ENTRY_IDS.issubset(set(meta["entry_ids"]))
    assert ACTION_CONVERSION_UPDATE_RELATIONS.issubset(set(meta["relation_ids"]))
    assert_observation_structure_dictionary_contract(meta)


def test_phase3_loader_validates_current_input_bundle_policy_without_public_contract_changes() -> None:
    dictionary = load_observation_structure_dictionary()
    meta = dictionary.as_meta()
    policy = meta["input_bundle_policy"]
    mapping = policy["normalized_field_mapping"]

    assert set(policy["required_current_input_fields"]) == EXPECTED_REQUIRED_FIELDS
    for normalized_field, source_field in EXPECTED_FIELD_MAPPING.items():
        assert mapping[normalized_field]["source_field"] == source_field
    assert mapping["emotions"]["fallback_fields"] == ["emotions"]
    assert policy["source_priority"] == [
        "current_input_explicit_fields",
        "current_input_direct_relations",
        "connected_user_facts",
        "dictionary_candidates",
        "general_knowledge_not_primary",
    ]

    assert meta["comment_text_generated"] is False
    boundaries = meta["contract_boundaries"]
    assert boundaries["public_route_changed"] is False
    assert boundaries["request_key_changed"] is False
    assert boundaries["response_key_changed"] is False
    assert boundaries["db_physical_name_changed"] is False
    assert boundaries["rn_visible_contract_changed"] is False
    assert boundaries["existing_surface_dictionary_modified"] is False


def test_phase3_loader_selects_structure_entries_and_relations_without_returning_completed_text() -> None:
    dictionary = load_observation_structure_dictionary()

    gap_entries = select_observation_structure_entries(dictionary, relation_id="state_text_gap")
    muri_entries = select_observation_structure_entries(dictionary, input_word="無理")
    self_insight_entries = select_observation_structure_entries(dictionary, entry_type="special_emotion_mode")
    selected_relations = select_observation_structure_relations(dictionary, relation_id="state_text_gap")
    dumped = dump_observation_structure_dictionary_contract(dictionary)

    assert {entry["entry_id"] for entry in gap_entries} == {"gap_word_daijoubu"}
    assert [entry["entry_id"] for entry in muri_entries] == ["word_muri"]
    assert {entry["entry_id"] for entry in self_insight_entries} == {"self_insight"}
    assert [relation["relation_id"] for relation in selected_relations] == ["state_text_gap"]
    assert "input_feedback.comment_text" not in dumped
    assert "public_comment_text" not in dumped
    assert "candidate_comment_text" not in dumped
    assert "reply_text" not in dumped


def test_phase3_loader_selects_action_conversion_update_relations() -> None:
    dictionary = load_observation_structure_dictionary()

    for relation_id in ACTION_CONVERSION_UPDATE_RELATIONS:
        selected_relations = select_observation_structure_relations(dictionary, relation_id=relation_id)
        assert [relation["relation_id"] for relation in selected_relations] == [relation_id]
        assert selected_relations[0]["surface_policy"]["must_not_return_directly"] is True
        assert selected_relations[0]["surface_policy"]["default_strength"] == "soft"


def test_phase3_loader_selects_action_conversion_update_entries_by_input_word() -> None:
    dictionary = load_observation_structure_dictionary()

    expected_by_word = {
        "言えなかった": "word_could_not_say",
        "合わせた": "word_aligned_to_context",
        "我慢した": "word_gaman",
        "わからない": "word_wakaranai",
    }

    for input_word, expected_entry_id in expected_by_word.items():
        selected_entries = select_observation_structure_entries(dictionary, input_word=input_word)
        assert [entry["entry_id"] for entry in selected_entries] == [expected_entry_id]
        assert selected_entries[0]["entry_type"] == "input_word"
        assert selected_entries[0]["surface_policy"]["must_not_return_directly"] is True


def test_phase3_loader_keeps_gaman_and_wakaranai_low_information_boundary_user_agency() -> None:
    dictionary = load_observation_structure_dictionary()

    gaman_entries = select_observation_structure_entries(dictionary, input_word="我慢した")
    wakaranai_entries = select_observation_structure_entries(dictionary, input_word="わからない")

    assert [entry["entry_id"] for entry in gaman_entries] == ["word_gaman"]
    assert [entry["entry_id"] for entry in wakaranai_entries] == ["word_wakaranai"]

    for entry in [*gaman_entries, *wakaranai_entries]:
        boundary = entry["low_information_boundary"]
        assert boundary["prompt_policy"] == "user_agency_prompt"
        assert boundary["known_scope"]
        assert boundary["unknown_scope"]
        assert boundary["must_not_infer"]


def test_phase3_loader_keeps_wakaranai_from_collapsing_to_low_information_only() -> None:
    dictionary = load_observation_structure_dictionary()
    wakaranai_entries = select_observation_structure_entries(dictionary, input_word="わからない")

    assert [entry["entry_id"] for entry in wakaranai_entries] == ["word_wakaranai"]
    relation_candidates = set(wakaranai_entries[0]["relation_candidates"])
    assert "unformed_self_insight" in relation_candidates
    assert "low_information_weight" in relation_candidates
    assert relation_candidates != {"low_information_weight"}


def test_phase3_validator_rejects_duplicate_entry_and_relation_ids() -> None:
    payload = _payload()

    duplicated_entry = copy.deepcopy(payload)
    duplicated_entry["entries"].append(copy.deepcopy(duplicated_entry["entries"][0]))
    with pytest.raises(ValueError, match="duplicate.*entry_id"):
        validate_observation_structure_dictionary_payload(duplicated_entry)

    duplicated_relation = copy.deepcopy(payload)
    duplicated_relation["relations"].append(copy.deepcopy(duplicated_relation["relations"][0]))
    with pytest.raises(ValueError, match="duplicate.*relation_id"):
        validate_observation_structure_dictionary_payload(duplicated_relation)


def test_phase3_validator_rejects_undefined_relation_references() -> None:
    payload = _payload()
    invalid = copy.deepcopy(payload)
    invalid["entries"][0]["relation_candidates"].append("undefined_relation_for_test")

    with pytest.raises(ValueError, match="undefined relation_id"):
        validate_observation_structure_dictionary_payload(invalid)


def test_phase3_validator_rejects_missing_forbidden_inference_definitions() -> None:
    payload = _payload()

    missing_relation_forbidden = copy.deepcopy(payload)
    del missing_relation_forbidden["relations"][0]["forbidden_inference"]
    with pytest.raises(ValueError, match="forbidden_inference"):
        validate_observation_structure_dictionary_payload(missing_relation_forbidden)

    empty_entry_forbidden = copy.deepcopy(payload)
    empty_entry_forbidden["entries"][0]["forbidden_inference"] = []
    with pytest.raises(ValueError, match="forbidden_inference"):
        validate_observation_structure_dictionary_payload(empty_entry_forbidden)

    missing_question_forbidden = copy.deepcopy(payload)
    del missing_question_forbidden["entries"][0]["observation_questions"][0]["forbidden_inference"]
    with pytest.raises(ValueError, match="forbidden_inference"):
        validate_observation_structure_dictionary_payload(missing_question_forbidden)


def test_phase3_validator_rejects_current_input_policy_drift_and_public_payload_keys() -> None:
    payload = _payload()

    invalid_bundle = copy.deepcopy(payload)
    invalid_bundle["input_bundle_policy"]["required_current_input_fields"] = [
        "memo",
        "emotion_details",
        "emotions",
        "category",
    ]
    with pytest.raises(ValueError, match="required_current_input_fields"):
        validate_observation_structure_dictionary_payload(invalid_bundle)

    invalid_mapping = copy.deepcopy(payload)
    invalid_mapping["input_bundle_policy"]["normalized_field_mapping"]["thought_text"]["source_field"] = "memo_action"
    with pytest.raises(ValueError, match="thought_text"):
        validate_observation_structure_dictionary_payload(invalid_mapping)

    invalid_contract = copy.deepcopy(load_observation_structure_dictionary().as_meta())
    invalid_contract["public_route_changed"] = True
    with pytest.raises(ValueError, match="public_route_changed"):
        assert_observation_structure_dictionary_contract(invalid_contract)

    invalid_payload_key = copy.deepcopy(payload)
    invalid_payload_key["entries"][0]["surface_policy"]["public_comment_text"] = "表示本文は辞書に入れない"
    with pytest.raises(ValueError, match="payload keys|raw payload|comment"):
        validate_observation_structure_dictionary_payload(invalid_payload_key)
