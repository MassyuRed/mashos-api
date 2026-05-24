from __future__ import annotations

import json
from pathlib import Path

import pytest

from emlis_ai_observation_dictionary_loader import (
    CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
    CATEGORY_HUMILITY_MARKER,
    CATEGORY_QUESTION_ENDING,
    CATEGORY_RECEIVE_PHRASE,
    CATEGORY_RELATION_PHRASE,
    DEFAULT_OBSERVATION_DICTIONARY_PATH,
    DEFAULT_OBSERVATION_DICTIONARY_SCHEMA_PATH,
    OBSERVATION_DICTIONARY_SCHEMA_VERSION,
    OBSERVATION_DICTIONARY_STEP,
    assert_observation_dictionary_contract,
    dump_observation_dictionary_contract,
    load_observation_dictionary,
    load_observation_dictionary_schema,
    select_observation_dictionary_entries,
    validate_observation_dictionary_payload,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
)


def _payload() -> dict:
    with Path(DEFAULT_OBSERVATION_DICTIONARY_PATH).open("r", encoding="utf-8") as fp:
        return json.load(fp)


def test_step5_default_schema_and_dictionary_files_exist_and_load() -> None:
    assert Path(DEFAULT_OBSERVATION_DICTIONARY_SCHEMA_PATH).exists()
    assert Path(DEFAULT_OBSERVATION_DICTIONARY_PATH).exists()

    schema = load_observation_dictionary_schema()
    dictionary = load_observation_dictionary()
    meta = dictionary.as_meta()

    assert schema["properties"]["schema_version"]["const"] == OBSERVATION_DICTIONARY_SCHEMA_VERSION
    assert schema["properties"]["contract_step"]["const"] == OBSERVATION_DICTIONARY_STEP
    assert meta["schema_version"] == OBSERVATION_DICTIONARY_SCHEMA_VERSION
    assert meta["source_step"] == OBSERVATION_DICTIONARY_STEP
    assert meta["observation_dictionary_ready"] is True
    assert meta["positive_material_entry_count"] > 0
    assert meta["forbidden_template_signature_count"] > 0
    assert meta["categories"][CATEGORY_RECEIVE_PHRASE] >= 1
    assert meta["categories"][CATEGORY_RELATION_PHRASE] >= 1
    assert meta["categories"][CATEGORY_HUMILITY_MARKER] >= 1
    assert meta["categories"][CATEGORY_QUESTION_ENDING] >= 1
    assert meta["categories"][CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE] >= 1
    assert_observation_dictionary_contract(meta)


def test_step5_dictionary_entries_are_materials_not_completed_templates() -> None:
    meta = load_observation_dictionary().as_meta()
    dumped = dump_observation_dictionary_contract(meta)

    positive_entries = [entry for entry in meta["entries"] if entry["positive_material"]]
    forbidden_entries = [entry for entry in meta["entries"] if not entry["positive_material"]]

    assert all(entry["must_not_be_complete_sentence"] is True for entry in positive_entries)
    assert all(entry["category"] != CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE for entry in positive_entries)
    assert all(entry["category"] == CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE for entry in forbidden_entries)
    assert "input_feedback.comment_text" not in dumped
    assert "candidate_comment_text" not in dumped
    assert "Emlisの観測" not in dumped
    assert meta["comment_text_generated"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert meta["display_gate_relaxed"] is False


def test_step5_selects_positive_material_by_reply_kind_category_and_evidence_role() -> None:
    dictionary = load_observation_dictionary()

    low_info_questions = select_observation_dictionary_entries(
        dictionary,
        category=CATEGORY_QUESTION_ENDING,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        evidence_roles=["unknown_slot"],
        unknown_slots=["event"],
    )
    eligible_relations = select_observation_dictionary_entries(
        dictionary,
        category=CATEGORY_RELATION_PHRASE,
        reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        evidence_roles=["relation"],
    )
    hidden_forbidden = select_observation_dictionary_entries(
        dictionary,
        category=CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    )
    visible_forbidden = select_observation_dictionary_entries(
        dictionary,
        category=CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        include_forbidden_signatures=True,
    )

    assert low_info_questions
    low_info_question_surfaces = {entry["surface"] for entry in low_info_questions}
    assert "何があったか" in low_info_question_surfaces
    assert "何がありましたか" not in low_info_question_surfaces
    assert all(entry["category"] == CATEGORY_QUESTION_ENDING for entry in low_info_questions)
    assert all(entry["positive_material"] is True for entry in low_info_questions)

    changed_questions = select_observation_dictionary_entries(
        dictionary,
        category=CATEGORY_QUESTION_ENDING,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        evidence_roles=["unknown_slot"],
        unknown_slots=["desired_direction"],
    )
    hard_to_say_questions = select_observation_dictionary_entries(
        dictionary,
        category=CATEGORY_QUESTION_ENDING,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        evidence_roles=["unknown_slot"],
        unknown_slots=["current_feeling_target"],
    )
    assert {entry["surface"] for entry in changed_questions} == {"何が変わったのか"}
    assert {entry["surface"] for entry in hard_to_say_questions} == {"どこから言いにくくなっているか"}
    assert eligible_relations
    assert all(OBSERVATION_REPLY_KIND_ELIGIBLE in entry["allowed_reply_kinds"] for entry in eligible_relations)
    assert hidden_forbidden == []
    assert visible_forbidden
    assert all(entry["positive_material"] is False for entry in visible_forbidden)


def test_step5_contract_rejects_completed_positive_template_material() -> None:
    payload = _payload()
    invalid = dict(payload)
    invalid["entries"] = [dict(entry) for entry in payload["entries"]]
    invalid["entries"].append(
        {
            "entry_id": "bad_complete_sentence",
            "category": "receive_phrase",
            "surface": "つらかったですね。無理しないでくださいね。",
            "allowed_reply_kinds": [OBSERVATION_REPLY_KIND_ELIGIBLE],
            "requires_evidence_role": ["state"],
            "must_not_be_complete_sentence": True,
            "template_signature_weight": 0.9,
        }
    )

    with pytest.raises(ValueError):
        validate_observation_dictionary_payload(invalid)


def test_step5_contract_rejects_public_contract_drift_and_raw_payload_keys() -> None:
    valid = load_observation_dictionary().as_meta()

    invalid_flag = dict(valid)
    invalid_flag["api_route_changed"] = True
    with pytest.raises(ValueError):
        assert_observation_dictionary_contract(invalid_flag)

    invalid_entry = dict(valid)
    invalid_entry["entries"] = [dict(entry) for entry in valid["entries"]]
    invalid_entry["entries"][0]["comment_text"] = "表示本文は入れない"
    with pytest.raises(ValueError):
        assert_observation_dictionary_contract(invalid_entry)

    invalid_kind = _payload()
    invalid_kind["entries"] = [dict(entry) for entry in invalid_kind["entries"]]
    invalid_kind["entries"][0]["allowed_reply_kinds"] = ["low_information_status_public"]
    with pytest.raises(ValueError):
        validate_observation_dictionary_payload(invalid_kind)


def test_step5_contract_rejects_forbidden_signature_as_positive_material() -> None:
    payload = _payload()
    invalid = dict(payload)
    invalid["entries"] = [dict(entry) for entry in payload["entries"]]
    for entry in invalid["entries"]:
        if entry["category"] == CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE:
            entry["positive_material"] = True
            break

    with pytest.raises(ValueError):
        validate_observation_dictionary_payload(invalid)
