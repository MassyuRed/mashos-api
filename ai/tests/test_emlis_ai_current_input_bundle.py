from __future__ import annotations

from emlis_ai_current_input_bundle import (
    EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
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
