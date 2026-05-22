from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

AI_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = AI_ROOT / "services" / "ai_inference" / "config"
SCHEMA_PATH = CONFIG_DIR / "emlis_observation_structure_dictionary.schema.json"
DICTIONARY_PATH = CONFIG_DIR / "emlis_observation_structure_dictionary.v1.json"
SURFACE_DICTIONARY_PATH = CONFIG_DIR / "emlis_observation_dictionary.v1.json"

EXPECTED_RELATIONS = {
    "desire_stagnation",
    "load_accumulation",
    "action_blocked",
    "pressure_gap",
    "repetition",
    "priority_pressure",
    "low_information_weight",
    "state_text_gap",
    "emotion_nesting",
    "thought_action_discrepancy",
    "category_parallel",
    "category_overlap",
    "self_insight_discovery",
    "user_agency_prompt",
    "unexpressed_output_stop",
    "self_shape_alignment",
    "action_conversion_history",
    "conversion_history_closure",
    "unformed_self_insight",
}
EXPECTED_ENTRY_IDS = {
    "word_muri",
    "word_tired",
    "gap_word_daijoubu",
    "word_change_want",
    "word_change_blocked",
    "word_scary",
    "word_action_blocked",
    "word_need_change",
    "word_not_working",
    "self_insight",
    "emotion_nesting",
    "thought_action_discrepancy",
    "category_parallel_overlap",
    "user_agency_prompt",
    "word_could_not_say",
    "word_aligned_to_context",
    "word_gaman",
    "word_wakaranai",
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
FORBIDDEN_TRUE_FLAGS = {
    "public_route_changed",
    "request_key_changed",
    "response_key_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "display_gate_relaxed",
    "raw_text_added_to_public_metadata",
    "existing_surface_dictionary_modified",
}
FORBIDDEN_PAYLOAD_KEY_HINTS = {
    "completed_reply_text",
    "fixed_fallback_sentence",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "raw_current_input",
    "raw_input",
    "raw_text",
}


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    assert isinstance(payload, dict)
    return payload


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield key, item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def test_phase2_structure_dictionary_schema_and_dictionary_files_exist() -> None:
    assert SCHEMA_PATH.exists()
    assert DICTIONARY_PATH.exists()
    assert SURFACE_DICTIONARY_PATH.exists()

    schema = _load(SCHEMA_PATH)
    dictionary = _load(DICTIONARY_PATH)

    assert schema["$id"] == "https://cocolon.local/schemas/emlis_observation_structure_dictionary.v1.json"
    assert schema["properties"]["schema_version"]["const"] == "emlis.observation_structure_dictionary.v1"
    assert schema["properties"]["contract_step"]["const"] == "Phase2_Observation_Structure_Dictionary_Schema"
    assert dictionary["dictionary_id"] == "emlis_observation_structure_dictionary"
    assert dictionary["schema_version"] == "emlis.observation_structure_dictionary.v1"
    assert dictionary["contract_step"] == "Phase2_Observation_Structure_Dictionary_Schema"
    assert dictionary["base_dictionary"] == "cocolon_foundation_structure_dictionary"
    assert dictionary["status"] == "implementation_schema_phase2"


def test_phase2_keeps_structure_dictionary_separate_from_existing_surface_dictionary() -> None:
    structure_dictionary = _load(DICTIONARY_PATH)
    surface_dictionary = _load(SURFACE_DICTIONARY_PATH)

    assert structure_dictionary["contract_step"] == "Phase2_Observation_Structure_Dictionary_Schema"
    assert any("loader" in note.lower() for note in structure_dictionary["implementation_notes"])
    assert structure_dictionary["contract_boundaries"]["existing_surface_dictionary_modified"] is False

    assert surface_dictionary["schema_version"] == "emlis.observation_dictionary.v1"
    assert "entries" in surface_dictionary
    assert "relations" not in surface_dictionary
    assert "input_bundle_policy" not in surface_dictionary
    assert "contract_boundaries" not in surface_dictionary


def test_phase2_contract_boundary_flags_stay_closed() -> None:
    dictionary = _load(DICTIONARY_PATH)
    boundaries = dictionary["contract_boundaries"]

    for flag in FORBIDDEN_TRUE_FLAGS:
        assert boundaries[flag] is False, flag

    for key, item in _walk(dictionary):
        key_text = str(key)
        assert "input_feedback.comment_text" not in key_text
        assert key_text not in FORBIDDEN_PAYLOAD_KEY_HINTS
        if key_text in FORBIDDEN_TRUE_FLAGS:
            assert item is False


def test_phase2_input_bundle_policy_matches_phase1_current_input_bundle_shape() -> None:
    dictionary = _load(DICTIONARY_PATH)
    input_bundle_policy = dictionary["input_bundle_policy"]
    mapping = input_bundle_policy["normalized_field_mapping"]

    assert set(input_bundle_policy["required_current_input_fields"]) == {
        "memo",
        "memo_action",
        "emotion_details",
        "category",
    }
    assert mapping["thought_text"]["source_field"] == "memo"
    assert mapping["action_text"]["source_field"] == "memo_action"
    assert mapping["emotions"]["source_field"] == "emotion_details"
    assert mapping["emotions"]["fallback_fields"] == ["emotions"]
    assert mapping["emotion_strength_summary"]["source_field"] == "emotion_details"
    assert mapping["categories"]["source_field"] == "category"
    assert mapping["selected_at"]["source_field"] == "created_at"
    assert mapping["source_record_id"]["source_field"] == "id"
    assert input_bundle_policy["source_priority"] == [
        "current_input_explicit_fields",
        "current_input_direct_relations",
        "connected_user_facts",
        "dictionary_candidates",
        "general_knowledge_not_primary",
    ]


def test_phase2_relations_and_entries_are_reference_consistent() -> None:
    dictionary = _load(DICTIONARY_PATH)
    relation_ids = [relation["relation_id"] for relation in dictionary["relations"]]
    entry_ids = [entry["entry_id"] for entry in dictionary["entries"]]

    assert len(relation_ids) == 19
    assert len(entry_ids) == 18
    assert len(relation_ids) == len(set(relation_ids))
    assert len(entry_ids) == len(set(entry_ids))
    assert EXPECTED_RELATIONS == set(relation_ids)
    assert EXPECTED_ENTRY_IDS == set(entry_ids)

    relation_id_set = set(relation_ids)
    for entry in dictionary["entries"]:
        assert entry["relation_candidates"], entry["entry_id"]
        assert set(entry["relation_candidates"]).issubset(relation_id_set), entry["entry_id"]
        assert entry["surface_policy"]["must_not_return_directly"] is True
        if "low_information_boundary" in entry:
            assert entry["low_information_boundary"]["prompt_policy"] == "user_agency_prompt"


def test_phase2_action_conversion_update_entries_are_schema_safe_observation_material() -> None:
    dictionary = _load(DICTIONARY_PATH)
    relations_by_id = {relation["relation_id"]: relation for relation in dictionary["relations"]}
    entries_by_id = {entry["entry_id"]: entry for entry in dictionary["entries"]}

    assert ACTION_CONVERSION_UPDATE_RELATIONS.issubset(relations_by_id)
    assert ACTION_CONVERSION_UPDATE_ENTRY_IDS.issubset(entries_by_id)

    for relation_id in ACTION_CONVERSION_UPDATE_RELATIONS:
        relation = relations_by_id[relation_id]
        assert relation["surface_policy"]["must_not_return_directly"] is True
        assert relation["surface_policy"]["default_strength"] == "soft"
        assert relation["allowed_inference"], relation_id
        assert relation["forbidden_inference"], relation_id
        assert relation["evidence_requirements"], relation_id

    for entry_id in ACTION_CONVERSION_UPDATE_ENTRY_IDS:
        entry = entries_by_id[entry_id]
        assert entry["entry_type"] == "input_word"
        assert entry["input_words"], entry_id
        assert entry["relation_candidates"], entry_id
        assert set(entry["relation_candidates"]).issubset(relations_by_id), entry_id
        assert entry["surface_policy"]["must_not_return_directly"] is True
        assert "default_direction" in entry["surface_policy"]
        for key, _item in _walk(entry):
            assert str(key) not in FORBIDDEN_PAYLOAD_KEY_HINTS


def test_phase2_action_conversion_update_low_information_boundaries_keep_user_agency() -> None:
    dictionary = _load(DICTIONARY_PATH)
    entries_by_id = {entry["entry_id"]: entry for entry in dictionary["entries"]}
    required_entry_ids = {"word_could_not_say", "word_gaman", "word_wakaranai"}

    assert required_entry_ids.issubset(entries_by_id)
    for entry_id in required_entry_ids:
        boundary = entries_by_id[entry_id]["low_information_boundary"]
        assert boundary["prompt_policy"] == "user_agency_prompt"
        assert boundary["known_scope"], entry_id
        assert boundary["unknown_scope"], entry_id
        assert boundary["must_not_infer"], entry_id


def test_phase2_action_conversion_update_keeps_surface_dictionary_unmodified() -> None:
    surface_dictionary = _load(SURFACE_DICTIONARY_PATH)

    assert "relations" not in surface_dictionary
    assert "input_bundle_policy" not in surface_dictionary
    assert "contract_boundaries" not in surface_dictionary

    surface_text = json.dumps(surface_dictionary, ensure_ascii=False)
    for relation_id in ACTION_CONVERSION_UPDATE_RELATIONS:
        assert relation_id not in surface_text
    for entry_id in ACTION_CONVERSION_UPDATE_ENTRY_IDS:
        assert entry_id not in surface_text


def test_phase2_structure_dictionary_has_core_observation_rules() -> None:
    dictionary = _load(DICTIONARY_PATH)
    policies = dictionary["global_policies"]

    assert policies["emotion_policy"]["selected_emotion_is_state_premise"] is True
    assert policies["emotion_policy"]["emotion_strength_must_not_create_cause"] is True
    assert policies["category_policy"]["category_is_topic_direction_not_cause"] is True
    assert policies["category_policy"]["category_overlap_requires_textual_evidence"] is True
    assert policies["thought_action_policy"]["memo_is_self_world_event"] is True
    assert policies["thought_action_policy"]["memo_action_is_real_world_event"] is True
    assert policies["state_text_gap_policy"]["strong_surface_requires"] == [
        "emotion_strength_strong",
        "clear_gap_word",
        "supporting_memo_or_action_evidence",
    ]
    assert policies["low_information_policy"]["must_not_fill_unknown_event"] is True
    assert "教えてください" in policies["user_agency_prompt_policy"]["avoid_verbs"]
    assert policies["surface_policy"]["dictionary_is_not_completed_reply_template"] is True
    assert policies["surface_policy"]["must_not_return_entry_text_directly"] is True


def test_phase2_surface_policy_is_instructional_material_not_direct_reply_text() -> None:
    dictionary = _load(DICTIONARY_PATH)

    for relation in dictionary["relations"]:
        assert relation["surface_policy"]["must_not_return_directly"] is True
        assert relation["surface_policy"]["default_strength"] in {"soft", "medium", "strong_when_high_grounding"}

    for entry in dictionary["entries"]:
        surface_policy = entry["surface_policy"]
        assert surface_policy["must_not_return_directly"] is True
        for key, _item in _walk(surface_policy):
            assert str(key) not in FORBIDDEN_PAYLOAD_KEY_HINTS
        assert "default_direction" in surface_policy
