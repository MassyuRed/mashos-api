from __future__ import annotations

import json

from cocolon_environment_state_output_frame import (
    ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    ENVIRONMENT_STATE_OUTPUT_FRAME_PHASE,
    ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION,
    build_environment_state_output_frame,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input


def test_environment_state_output_frame_builds_single_record_text_free_material() -> None:
    current_input = {
        "id": "emo-frame-1",
        "created_at": "2026-05-25T00:00:00Z",
        "memo": "この職場でやっていけるか不安",
        "memo_action": "職場で新しい仕事を任された",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "emotions": ["不安"],
        "category": ["仕事"],
        "is_secret": False,
    }

    frame = build_environment_state_output_frame(
        current_input,
        observation_structure_relation_ids=["pressure_gap", "action_blocked"],
    )
    encoded = json.dumps(frame, ensure_ascii=False, sort_keys=True)

    assert frame["schema_version"] == ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION
    assert frame["material_id"] == ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID
    assert frame["phase"] == ENVIRONMENT_STATE_OUTPUT_FRAME_PHASE
    assert frame["source"]["source_kind"] == "current_input"
    assert frame["axis_presence"] == {
        "has_environment_axis": True,
        "has_state_axis": True,
        "has_output_axis": True,
        "has_all_single_record_axes": True,
    }
    assert frame["environment_axis"]["confidence_kind"] == "category_plus_action_evidence"
    assert frame["environment_axis"]["category_labels"][0]["label"] == "仕事"
    assert frame["environment_axis"]["category_labels"][0]["must_not_read_as"] == "cause"
    assert frame["environment_axis"]["action_evidence"]["has_action_text"] is True
    assert frame["environment_axis"]["action_evidence"]["raw_text_included"] is False
    assert frame["state_axis"]["emotion_labels"][0]["type"] == "不安"
    assert frame["state_axis"]["emotion_labels"][0]["read_as"] == "state_label"
    assert frame["state_axis"]["emotion_labels"][0]["must_not_read_as"] == "diagnosis"
    assert frame["state_axis"]["strength_summary"]["primary_strength"] == "medium"
    assert frame["output_axis"]["thought_evidence"]["has_thought_text"] is True
    assert frame["output_axis"]["thought_evidence"]["raw_text_included"] is False
    assert frame["output_axis"]["output_theme_candidates"][0]["theme_id"] == "continuation_concern"
    assert frame["output_axis"]["output_theme_candidates"][0]["evidence_span_ids"]
    assert frame["output_axis"]["output_theme_candidates"][0]["supporting_observation_relation_ids"] == [
        "pressure_gap",
        "action_blocked",
    ]
    assert frame["time_axis"]["period_scope"] == "single_record"
    assert frame["time_axis"]["must_not_use_for_period_tendency"] is True
    assert frame["surface_policy"]["single_record_only"] is True
    assert frame["surface_policy"]["comment_text_generated"] is False
    assert frame["surface_policy"]["public_payload_changed"] is False
    assert frame["surface_policy"]["cause_from_category"] is False
    assert frame["surface_policy"]["cause_from_emotion_strength"] is False
    assert frame["surface_policy"]["period_tendency_from_single_record"] is False
    assert frame["surface_policy"]["personality_tendency_allowed"] is False
    assert frame["surface_policy"]["recovery_prescription_allowed"] is False
    assert '"raw_text":' not in encoded
    assert "この職場でやっていけるか不安" not in encoded
    assert "職場で新しい仕事を任された" not in encoded
    assert "comment_text" not in normalize_emlis_current_input(current_input)
    assert "environment_state_output_frame" not in normalize_emlis_current_input(current_input)


def test_environment_state_output_frame_category_only_stays_topic_direction_not_cause() -> None:
    current_input = {
        "id": "emo-frame-2",
        "created_at": "2026-05-25T02:00:00Z",
        "memo": "なんとなく怖い",
        "memo_action": "",
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "category": ["仕事"],
    }

    frame = build_environment_state_output_frame(current_input, observation_structure_relation_ids=[])

    assert frame["environment_axis"]["confidence_kind"] == "category_only_topic_direction"
    assert frame["environment_axis"]["category_labels"][0]["read_as"] == "topic_direction"
    assert frame["environment_axis"]["category_labels"][0]["must_not_read_as"] == "cause"
    assert frame["environment_axis"]["action_evidence"]["has_action_text"] is False
    assert frame["state_axis"]["strength_summary"]["has_strong"] is True
    assert frame["surface_policy"]["cause_from_category"] is False
    assert frame["surface_policy"]["cause_from_emotion_strength"] is False
    assert "cause_from_category" in frame["surface_policy"]["forbidden_claims"]
    assert frame["output_axis"]["output_theme_candidates"] == []


def test_environment_state_output_frame_state_text_gap_candidate_does_not_create_hidden_truth() -> None:
    current_input = {
        "id": "emo-frame-3",
        "created_at": "2026-05-25T03:00:00Z",
        "memo": "大丈夫",
        "memo_action": "職場で嫌なことがあった",
        "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
        "category": ["仕事"],
    }

    frame = build_environment_state_output_frame(current_input, observation_structure_relation_ids=["state_text_gap"])
    gap_candidates = frame["state_axis"]["state_text_gap_candidates"]
    encoded = json.dumps(frame, ensure_ascii=False, sort_keys=True)

    assert gap_candidates
    assert gap_candidates[0]["candidate_id"] == "state_text_gap"
    assert gap_candidates[0]["evidence_span_ids"]
    assert "hidden_truth" in gap_candidates[0]["must_not_read_as"]
    assert "diagnosis" in gap_candidates[0]["must_not_read_as"]
    assert frame["surface_policy"]["personality_tendency_allowed"] is False
    assert "職場で嫌なことがあった" not in encoded
    assert '"raw_text":' not in encoded


def test_environment_state_output_frame_missing_axes_stays_internal_and_single_record() -> None:
    frame = build_environment_state_output_frame(
        {"memo": "", "memo_action": "", "emotion_details": [], "category": []},
        observation_structure_relation_ids=[],
    )

    assert frame["axis_presence"] == {
        "has_environment_axis": False,
        "has_state_axis": False,
        "has_output_axis": False,
        "has_all_single_record_axes": False,
    }
    assert frame["environment_axis"]["confidence_kind"] == "environment_axis_missing"
    assert frame["environment_axis"]["ambiguity_flags"] == ["environment_axis_missing"]
    assert frame["state_axis"]["confidence_kind"] == "state_axis_missing"
    assert frame["output_axis"]["confidence_kind"] == "output_axis_missing"
    assert frame["evidence"]["spans"] == []
    assert frame["surface_policy"]["public_response_key_added"] is False
    assert frame["surface_policy"]["rn_visible_contract_changed"] is False
    assert frame["surface_policy"]["period_tendency_from_single_record"] is False
