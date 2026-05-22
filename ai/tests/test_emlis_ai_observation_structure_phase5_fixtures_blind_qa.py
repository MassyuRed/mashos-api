from __future__ import annotations

import json
from typing import Any, Mapping

import pytest

from emlis_ai_observation_structure_connection_service import (
    assert_observation_structure_connection_contract,
    build_observation_structure_connection,
    observation_structure_connection_forward_composer_meta,
)
from emlis_ai_observation_structure_material_service import (
    assert_observation_structure_material_contract,
    build_observation_structure_material,
    observation_structure_material_composer_payload,
    observation_structure_material_forward_meta,
    observation_structure_material_gate_report,
)
from fixtures.emlis_ai_observation_structure_phase5_cases import (
    PHASE5_BLIND_QA_RUBRIC,
    PHASE5_CATEGORY_BOUNDARY_CASES,
    PHASE5_HUMAN_BLIND_QA_DIMENSIONS,
    PHASE5_MACHINE_QA_DIMENSIONS,
    PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES,
    PHASE5_OBSERVATION_STRUCTURE_FIXTURE_VERSION,
    PHASE5_OBSERVATION_STRUCTURE_PHASE,
    PHASE5_REQUIRED_CASE_IDS,
)

_FORBIDDEN_RAW_OR_PUBLIC_TEXT_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "current_input",
    "currentInput",
    "memo",
    "memo_action",
    "memoText",
    "memoAction",
    "thought_text",
    "action_text",
    "comment_text",
    "commentText",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "completed_reply_text",
    "body",
    "text",
}

_FORBIDDEN_TRUE_FLAGS = {
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "comment_text_generated",
    "dictionary_returns_completed_reply",
    "dictionary_returned_completed_reply",
    "completed_reply_from_dictionary",
    "display_gate_relaxed",
    "api_route_changed",
    "api_response_key_change",
    "request_key_changed",
    "response_key_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "cause_inferred_from_category",
    "cause_inferred_from_emotion_strength",
    "external_ai_used",
    "local_llm_used",
}


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            assert key not in _FORBIDDEN_RAW_OR_PUBLIC_TEXT_KEYS
            if key in _FORBIDDEN_TRUE_FLAGS:
                assert value is not True
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple, set)):
        for item in payload:
            _assert_meta_only(item)


def _assert_current_input_text_not_forwarded(payload: Mapping[str, Any], current_input: Mapping[str, Any]) -> None:
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for source_key in ("memo", "memo_action"):
        raw_text = str(current_input.get(source_key) or "").strip()
        if raw_text:
            assert raw_text not in dumped


def _selected_relations(meta: Mapping[str, Any]) -> set[str]:
    return set(meta.get("selected_relation_ids") or meta.get("composer_relation_ids") or [])


def _selected_entries(meta: Mapping[str, Any]) -> set[str]:
    return set(meta.get("selected_entry_ids") or meta.get("composer_entry_ids") or [])


def test_phase5_fixture_contract_covers_required_design_cases_without_completed_text() -> None:
    assert PHASE5_OBSERVATION_STRUCTURE_FIXTURE_VERSION == "emlis.observation_structure.phase5_fixtures.v1"
    assert PHASE5_OBSERVATION_STRUCTURE_PHASE == "Phase5_Test_Fixture_Blind_QA"
    assert {case["case_id"] for case in PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES} == set(PHASE5_REQUIRED_CASE_IDS)

    assert PHASE5_BLIND_QA_RUBRIC["exact_comment_text_locked"] is False
    assert PHASE5_BLIND_QA_RUBRIC["dictionary_returns_completed_reply"] is False
    assert PHASE5_BLIND_QA_RUBRIC["machine_metrics_separated_from_human_read_feeling"] is True
    assert set(PHASE5_BLIND_QA_RUBRIC["machine_dimensions"]) == set(PHASE5_MACHINE_QA_DIMENSIONS)
    assert set(PHASE5_BLIND_QA_RUBRIC["human_blind_qa_dimensions"]) == set(PHASE5_HUMAN_BLIND_QA_DIMENSIONS)
    _assert_meta_only(PHASE5_BLIND_QA_RUBRIC)

    for case in PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES:
        assert "expected_comment_text" not in case
        assert "comment_text" not in case
        current_input = case["current_input"]
        assert {"memo", "memo_action", "emotion_details", "category"}.issubset(current_input)


@pytest.mark.parametrize("case", PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES, ids=lambda case: case["case_id"])
def test_phase5_blind_qa_cases_select_expected_structure_material_without_raw_text(case: Mapping[str, Any]) -> None:
    current_input = case["current_input"]
    material = build_observation_structure_material(current_input=current_input)
    material_meta = material.as_meta()
    forward_meta = observation_structure_material_forward_meta(material)
    composer_payload = observation_structure_material_composer_payload(material)
    gate_report = observation_structure_material_gate_report(material)

    assert_observation_structure_material_contract(material_meta)
    assert_observation_structure_material_contract(forward_meta)
    assert_observation_structure_material_contract(composer_payload)
    assert_observation_structure_material_contract(gate_report)

    expected_relations = set(case["expected_relation_ids"])
    expected_entries = set(case["expected_entry_ids"])
    forbidden_relations = set(case["forbidden_relation_ids"])
    assert expected_relations.issubset(_selected_relations(material_meta))
    assert expected_entries.issubset(_selected_entries(material_meta))
    assert forbidden_relations.isdisjoint(_selected_relations(material_meta))
    assert material_meta["low_information_candidate"] is case["expected_low_information_candidate"]
    assert set(case["expected_material_fields"]).issubset(set(material_meta["matched_source_fields"]))

    assert material_meta["dictionary_is_observation_material_only"] is True
    assert material_meta["dictionary_returns_completed_reply"] is False
    assert material_meta["comment_text_generated"] is False
    assert material_meta["display_gate_relaxed"] is False
    assert material_meta["api_route_changed"] is False
    assert material_meta["response_key_changed"] is False
    assert material_meta["db_physical_name_changed"] is False
    assert material_meta["rn_visible_contract_changed"] is False
    assert material_meta["gate_policy"]["category_is_topic_direction_not_cause"] is True
    assert material_meta["gate_policy"]["emotion_strength_must_not_create_cause"] is True
    assert material_meta["composer_policy"]["dictionary_must_not_return_completed_sentence"] is True

    for payload in (material_meta, forward_meta, composer_payload, gate_report):
        _assert_meta_only(payload)
        _assert_current_input_text_not_forwarded(payload, current_input)


@pytest.mark.parametrize("case", PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES, ids=lambda case: case["case_id"])
def test_phase5_blind_qa_cases_reach_gate_and_composer_connection_meta(case: Mapping[str, Any]) -> None:
    current_input = case["current_input"]
    connection = build_observation_structure_connection(current_input=current_input)
    connection_meta = connection.as_meta()
    composer_meta = observation_structure_connection_forward_composer_meta(connection)

    assert_observation_structure_connection_contract(connection_meta)
    assert_observation_structure_connection_contract(composer_meta)

    expected_relations = set(case["expected_relation_ids"])
    expected_entries = set(case["expected_entry_ids"])
    forbidden_relations = set(case["forbidden_relation_ids"])
    assert expected_relations.issubset(_selected_relations(connection_meta))
    assert expected_entries.issubset(_selected_entries(connection_meta))
    assert forbidden_relations.isdisjoint(_selected_relations(connection_meta))

    if case["expected_low_information_candidate"]:
        assert "user_agency_prompt" in connection_meta["composer_material_roles"]
        assert connection_meta["low_information_unknown_slots"]
    else:
        assert "user_agency_prompt" not in connection_meta["composer_material_roles"]

    assert connection_meta["dictionary_material_only"] is True
    assert connection_meta["dictionary_returned_completed_reply"] is False
    assert connection_meta["comment_text_generated"] is False
    assert connection_meta["display_gate_relaxed"] is False
    assert connection_meta["api_route_changed"] is False
    assert connection_meta["api_response_key_change"] is False
    assert connection_meta["db_physical_name_changed"] is False
    assert connection_meta["rn_visible_contract_changed"] is False
    assert connection_meta["cause_inferred_from_category"] is False
    assert connection_meta["cause_inferred_from_emotion_strength"] is False
    assert composer_meta["dictionary_must_not_return_completed_sentence"] is True
    assert composer_meta["surface_realizer_owns_natural_language"] is True
    assert composer_meta["must_not_create_cause_without_evidence"] is True

    for payload in (connection_meta, composer_meta):
        _assert_meta_only(payload)
        _assert_current_input_text_not_forwarded(payload, current_input)


@pytest.mark.parametrize("case", PHASE5_CATEGORY_BOUNDARY_CASES, ids=lambda case: case["case_id"])
def test_phase5_category_boundary_parallel_vs_overlap_is_consistent_across_material_and_connection(case: Mapping[str, Any]) -> None:
    current_input = case["current_input"]
    material_meta = build_observation_structure_material(current_input=current_input).as_meta()
    connection_meta = build_observation_structure_connection(current_input=current_input).as_meta()

    expected_relations = set(case["expected_relation_ids"])
    forbidden_relations = set(case["forbidden_relation_ids"])
    assert expected_relations.issubset(_selected_relations(material_meta))
    assert expected_relations.issubset(_selected_relations(connection_meta))
    assert forbidden_relations.isdisjoint(_selected_relations(material_meta))
    assert forbidden_relations.isdisjoint(_selected_relations(connection_meta))
    assert material_meta["low_information_candidate"] is case["expected_low_information_candidate"]
    assert material_meta["gate_policy"]["category_overlap_requires_textual_evidence"] is True
    assert connection_meta["cause_inferred_from_category"] is False
    _assert_current_input_text_not_forwarded(material_meta, current_input)
    _assert_current_input_text_not_forwarded(connection_meta, current_input)


_PHASE3_ACTION_CONVERSION_CONNECTION_CASES: tuple[Mapping[str, Any], ...] = (
    {
        "case_id": "phase3_connection_unexpressed_output_stop_could_not_say_single_word",
        "current_input": {
            "id": "action-update-001",
            "created_at": "2026-05-22T00:00:00Z",
            "memo": "言えなかった",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_could_not_say"},
        "expected_relation_ids": {"unexpressed_output_stop"},
        "forbidden_relation_ids": {"thought_action_discrepancy", "user_agency_prompt"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_connection_unexpressed_output_stop_with_thought_action_gap",
        "current_input": {
            "id": "action-update-002",
            "created_at": "2026-05-22T00:01:00Z",
            "memo": "本当は嫌だったけど言えなかった",
            "memo_action": "笑って対応した",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_could_not_say"},
        "expected_relation_ids": {"unexpressed_output_stop", "thought_action_discrepancy"},
        "forbidden_relation_ids": set(),
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_connection_self_shape_alignment_single_word",
        "current_input": {
            "id": "action-update-003",
            "created_at": "2026-05-22T00:02:00Z",
            "memo": "合わせた",
            "memo_action": "",
            "emotion_details": [{"type": "平穏", "strength": "weak"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_aligned_to_context"},
        "expected_relation_ids": {"self_shape_alignment"},
        "forbidden_relation_ids": {"thought_action_discrepancy", "priority_pressure"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_connection_action_conversion_history_gaman_single_word",
        "current_input": {
            "id": "action-update-004",
            "created_at": "2026-05-22T00:03:00Z",
            "memo": "我慢した",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_gaman"},
        "expected_relation_ids": {"action_conversion_history"},
        "forbidden_relation_ids": {"thought_action_discrepancy", "conversion_history_closure", "load_accumulation"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_connection_action_conversion_history_with_thought_action_gap",
        "current_input": {
            "id": "action-update-005",
            "created_at": "2026-05-22T00:04:00Z",
            "memo": "本当は嫌だったけど我慢した",
            "memo_action": "言わずに対応した",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_gaman"},
        "expected_relation_ids": {"action_conversion_history", "thought_action_discrepancy"},
        "forbidden_relation_ids": {"conversion_history_closure", "load_accumulation"},
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_connection_conversion_history_closure_with_unfinished_evidence",
        "current_input": {
            "id": "action-update-006",
            "created_at": "2026-05-22T00:05:00Z",
            "memo": "我慢したけど、まだ引っかかっている",
            "memo_action": "言わずに対応した",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["人間関係"],
        },
        "expected_entry_ids": {"word_gaman"},
        "expected_relation_ids": {"action_conversion_history", "conversion_history_closure", "thought_action_discrepancy"},
        "forbidden_relation_ids": set(),
        "expected_low_information_candidate": False,
    },
    {
        "case_id": "phase3_connection_unformed_self_insight_wakaranai",
        "current_input": {
            "id": "action-update-007",
            "created_at": "2026-05-22T00:06:00Z",
            "memo": "わからない",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "category": ["自分"],
        },
        "expected_entry_ids": {"word_wakaranai"},
        "expected_relation_ids": {"unformed_self_insight"},
        "forbidden_relation_ids": set(),
        "expected_low_information_candidate": None,
    },
)


@pytest.mark.parametrize("case", _PHASE3_ACTION_CONVERSION_CONNECTION_CASES, ids=lambda case: str(case["case_id"]))
def test_phase3_action_conversion_update_connection_selection_is_evidence_bound(case: Mapping[str, Any]) -> None:
    connection = build_observation_structure_connection(current_input=case["current_input"])
    connection_meta = connection.as_meta()
    composer_meta = observation_structure_connection_forward_composer_meta(connection)

    assert_observation_structure_connection_contract(connection_meta)
    assert_observation_structure_connection_contract(composer_meta)

    selected_entry_ids = _selected_entries(connection_meta)
    selected_relation_ids = _selected_relations(connection_meta)
    assert set(case["expected_entry_ids"]).issubset(selected_entry_ids)
    assert set(case["expected_relation_ids"]).issubset(selected_relation_ids)
    assert set(case["forbidden_relation_ids"]).isdisjoint(selected_relation_ids)

    if case["expected_low_information_candidate"] is False:
        assert not connection_meta["low_information_unknown_slots"]
        assert "user_agency_prompt" not in connection_meta["composer_material_roles"]
    if case["case_id"] == "phase3_connection_unformed_self_insight_wakaranai":
        assert selected_relation_ids != {"low_information_weight"}
        assert "unformed_self_insight" in selected_relation_ids

    for payload in (connection_meta, composer_meta):
        _assert_meta_only(payload)
        _assert_current_input_text_not_forwarded(payload, case["current_input"])
