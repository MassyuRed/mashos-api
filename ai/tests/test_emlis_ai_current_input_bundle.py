from __future__ import annotations

import json

from emlis_ai_current_input_bundle import (
    EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
    ENVIRONMENT_STATE_OUTPUT_CURRENT_INPUT_CONNECTION_PHASE,
    ENVIRONMENT_STATE_OUTPUT_INPUT_CONNECTION_SCHEMA_VERSION,
    build_emlis_current_input_bundle,
    normalize_emlis_current_input,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger


def test_current_input_bundle_maps_legacy_emotion_submit_fields_without_contract_rename() -> None:
    current_input = {
        "id": "emo-1",
        "created_at": "2026-05-21T00:00:00Z",
        "memo": "大丈夫",
        "memo_action": "笑って対応した",
        "emotion_details": [
            {"type": "悲しみ", "strength": "strong"},
            {"type": "怒り", "strength": "medium"},
        ],
        "emotions": ["悲しみ", "怒り"],
        "category": ["仕事", "人間関係", "仕事"],
        "is_secret": False,
        "selection_seed": "emo-1|2026-05-21T00:00:00Z",
    }

    bundle = build_emlis_current_input_bundle(current_input)

    assert bundle.schema_version == EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION
    assert bundle.source_record_id == "emo-1"
    assert bundle.selected_at == "2026-05-21T00:00:00Z"
    assert bundle.thought_text == "大丈夫"
    assert bundle.action_text == "笑って対応した"
    assert [emotion.type for emotion in bundle.emotions] == ["悲しみ", "怒り"]
    assert [emotion.strength for emotion in bundle.emotions] == ["strong", "medium"]
    assert bundle.categories == ("仕事", "人間関係")
    assert bundle.emotion_strength_summary.primary_type == "悲しみ"
    assert bundle.emotion_strength_summary.primary_strength == "strong"
    assert bundle.emotion_strength_summary.strongest_type == "悲しみ"
    assert bundle.emotion_strength_summary.has_strong is True

    normalized = normalize_emlis_current_input(current_input)
    assert normalized["id"] == "emo-1"
    assert normalized["created_at"] == "2026-05-21T00:00:00Z"
    assert normalized["memo"] == "大丈夫"
    assert normalized["memo_action"] == "笑って対応した"
    assert normalized["emotion_details"] == [
        {"type": "悲しみ", "strength": "strong"},
        {"type": "怒り", "strength": "medium"},
    ]
    assert normalized["emotions"] == ["悲しみ", "怒り"]
    assert normalized["category"] == ["仕事", "人間関係"]
    assert "thought_text" not in normalized
    assert "action_text" not in normalized


def test_current_input_bundle_accepts_phase1_aliases_and_keeps_summary_text_free() -> None:
    alias_input = {
        "source_record_id": "emo-alias",
        "selected_at": "2026-05-21T01:23:45Z",
        "thought_text": "本当は嫌だった",
        "action_text": "笑って対応した",
        "emotion_details": [{"type": "怒り", "strength": "強"}],
        "categories": ["人間関係", "人間関係"],
        "isSecret": "false",
    }

    bundle = build_emlis_current_input_bundle(alias_input)
    normalized = normalize_emlis_current_input(alias_input)
    summary = bundle.to_internal_summary()

    assert normalized["id"] == "emo-alias"
    assert normalized["created_at"] == "2026-05-21T01:23:45Z"
    assert normalized["memo"] == "本当は嫌だった"
    assert normalized["memo_action"] == "笑って対応した"
    assert normalized["emotion_details"] == [{"type": "怒り", "strength": "strong"}]
    assert normalized["category"] == ["人間関係"]
    assert normalized["is_secret"] is False
    assert summary["has_thought_text"] is True
    assert summary["has_action_text"] is True
    assert summary["emotion_count"] == 1
    assert summary["category_count"] == 1
    assert "本当は嫌だった" not in str(summary)
    assert "笑って対応した" not in str(summary)


def test_evidence_ledger_reads_normalized_bundle_fields_as_current_input_sources() -> None:
    spans = build_evidence_ledger(
        {
            "thought_text": "大丈夫",
            "action_text": "笑って対応した",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "categories": ["仕事"],
        }
    )

    assert any(span.source_field == "memo" and span.raw_text == "大丈夫" for span in spans)
    assert any(span.source_field == "memo_action" and span.raw_text == "笑って対応した" for span in spans)
    assert any(span.source_field == "emotion_details" and span.raw_text == "悲しみ" for span in spans)
    assert any(span.source_field == "category" and span.raw_text == "仕事" for span in spans)


def test_current_input_bundle_exposes_environment_state_output_connection_without_public_contract_drift() -> None:
    current_input = {
        "id": "emo-env-1",
        "created_at": "2026-05-25T00:00:00Z",
        "memo": "この職場でやっていけるか不安",
        "memo_action": "職場で新しい仕事を任された",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "emotions": ["不安"],
        "category": ["仕事"],
        "is_secret": False,
    }

    bundle = build_emlis_current_input_bundle(current_input)
    connection = bundle.to_environment_state_output_connection_summary()
    summary = bundle.to_internal_summary()
    normalized = normalize_emlis_current_input(current_input)

    assert connection["schema_version"] == ENVIRONMENT_STATE_OUTPUT_INPUT_CONNECTION_SCHEMA_VERSION
    assert connection["phase"] == ENVIRONMENT_STATE_OUTPUT_CURRENT_INPUT_CONNECTION_PHASE
    assert connection["bundle_schema_version"] == EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION
    assert connection["axis_presence"] == {
        "has_environment_axis_material": True,
        "has_state_axis_material": True,
        "has_output_axis_material": True,
        "has_all_single_record_axes": True,
    }
    assert connection["environment_axis"]["source_fields"] == ["category", "memo_action"]
    assert connection["environment_axis"]["confidence_kind"] == "category_plus_action_evidence"
    assert connection["environment_axis"]["must_not_read_as"] == ["cause"]
    assert connection["state_axis"]["source_fields"] == ["emotion_details"]
    assert connection["state_axis"]["read_as"] == "state_label"
    assert "diagnosis" in connection["state_axis"]["must_not_read_as"]
    assert connection["output_axis"]["source_fields"] == ["memo"]
    assert connection["output_axis"]["read_as"] == "output_content"
    assert connection["time_axis"]["period_scope"] == "single_record"
    assert connection["time_axis"]["must_not_use_for_period_tendency"] is True
    assert connection["surface_policy"]["public_payload_changed"] is False
    assert connection["surface_policy"]["public_response_key_added"] is False
    assert connection["surface_policy"]["api_route_changed"] is False
    assert connection["surface_policy"]["response_key_changed"] is False
    assert connection["surface_policy"]["db_physical_name_changed"] is False
    assert connection["surface_policy"]["rn_visible_contract_changed"] is False
    assert connection["surface_policy"]["raw_input_included"] is False
    assert connection["surface_policy"]["raw_text_included"] is False
    assert connection["surface_policy"]["schema_file_materialized"] is False
    assert connection["surface_policy"]["full_frame_built_in_phase2"] is False
    assert connection["surface_policy"]["period_tendency_from_single_record"] is False
    assert connection["surface_policy"]["cause_from_category"] is False
    assert connection["surface_policy"]["cause_from_emotion_strength"] is False
    assert connection["surface_policy"]["personality_tendency_allowed"] is False
    assert connection["surface_policy"]["recovery_prescription_allowed"] is False
    assert summary["environment_state_output_connection"] == connection

    assert "environment_state_output_connection" not in normalized
    assert "environment_state_output_frame" not in normalized
    assert "thought_text" not in normalized
    assert "action_text" not in normalized
    assert normalized["memo"] == "この職場でやっていけるか不安"
    assert normalized["memo_action"] == "職場で新しい仕事を任された"


def test_environment_state_output_connection_summary_is_text_free_and_json_safe() -> None:
    current_input = {
        "source_record_id": "emo-env-2",
        "selected_at": "2026-05-25T01:23:45Z",
        "thought_text": "本当は嫌だった",
        "action_text": "笑って対応した",
        "emotion_details": [{"type": "怒り", "strength": "強"}],
        "categories": ["人間関係"],
    }

    bundle = build_emlis_current_input_bundle(current_input)
    connection = bundle.to_environment_state_output_connection_summary()
    encoded = json.dumps(connection, ensure_ascii=False, sort_keys=True)

    assert "本当は嫌だった" not in encoded
    assert "笑って対応した" not in encoded
    assert "emo-env-2" not in encoded
    assert "2026-05-25T01:23:45Z" not in encoded
    assert connection["axis_presence"]["has_all_single_record_axes"] is True
    assert connection["time_axis"]["selected_at_present"] is True
    assert connection["time_axis"]["source_record_id_present"] is True
    assert connection["environment_axis"]["confidence_kind"] == "category_plus_action_evidence"
    assert connection["state_axis"]["max_strength_score"] == 3
    assert connection["state_axis"]["has_strong"] is True
    assert connection["surface_policy"]["comment_text_included"] is False


def test_environment_state_output_connection_category_only_stays_topic_direction_not_cause() -> None:
    current_input = {
        "id": "emo-env-3",
        "created_at": "2026-05-25T02:00:00Z",
        "memo": "なんとなく怖い",
        "memo_action": "",
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "category": ["仕事"],
    }

    bundle = build_emlis_current_input_bundle(current_input)
    connection = bundle.to_environment_state_output_connection_summary()

    assert connection["environment_axis"]["source_fields"] == ["category"]
    assert connection["environment_axis"]["confidence_kind"] == "category_only_topic_direction"
    assert connection["environment_axis"]["must_not_read_as"] == ["cause"]
    assert connection["state_axis"]["max_strength_score"] == 3
    assert connection["state_axis"]["must_not_read_as"] == ["diagnosis", "cause"]
    assert connection["surface_policy"]["cause_from_category"] is False
    assert connection["surface_policy"]["cause_from_emotion_strength"] is False
    assert connection["surface_policy"]["period_tendency_from_single_record"] is False
