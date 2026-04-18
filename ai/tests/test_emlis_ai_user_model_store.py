from __future__ import annotations

import asyncio


def test_user_model_store_roundtrip_with_memory_fallback(monkeypatch):
    import emlis_ai_user_model_store as store_module
    from emlis_ai_types import EvidenceRef, MeaningMapEntry

    store_module._MEMORY_MODELS.clear()
    monkeypatch.setattr(store_module, "sb_get", None)
    monkeypatch.setattr(store_module, "sb_patch", None)
    monkeypatch.setattr(store_module, "sb_post", None)

    model = store_module.new_empty_derived_user_model(tier="premium")
    model.source_cursor.last_emotion_id = "emo-1"
    model.factual_profile = {"frequent_categories": [{"label": "仕事", "count": 3}]}
    model.interpretive_frame.meaning_map = [
        MeaningMapEntry(
            trigger="仕事",
            likely_meaning="評価不安",
            confidence=0.72,
            evidence=[EvidenceRef(kind="emotion", ref_id="emo-1")],
            last_seen_at="2026-04-18T00:00:00Z",
        )
    ]

    asyncio.run(store_module.save_emlis_ai_user_model_for_user(user_id="user-1", model=model))
    loaded = asyncio.run(store_module.load_emlis_ai_user_model_for_user("user-1", expected_tier="premium"))

    assert loaded is not None
    assert loaded.schema_version == store_module.MODEL_SCHEMA_VERSION
    assert loaded.model_tier == "premium"
    assert loaded.source_cursor.last_emotion_id == "emo-1"
    assert loaded.interpretive_frame.meaning_map[0].trigger == "仕事"
    assert loaded.interpretive_frame.meaning_map[0].likely_meaning == "評価不安"


def test_parse_serialize_derived_user_model_keeps_anchor_and_hypothesis_shape():
    import emlis_ai_user_model_store as store_module
    from emlis_ai_types import DerivedModelHypothesis, EvidenceRef, TopicAnchor

    model = store_module.new_empty_derived_user_model(tier="plus")
    model.open_topic_anchors = [
        TopicAnchor(
            anchor_key="category:仕事",
            label="仕事",
            confidence=0.61,
            evidence=[EvidenceRef(kind="emotion", ref_id="emo-2")],
            last_seen_at="2026-04-18T00:00:00Z",
        )
    ]
    model.hypotheses = [
        DerivedModelHypothesis(
            key="work_validation",
            text="仕事関連で評価不安が再浮上しやすい",
            confidence=0.66,
            evidence=[EvidenceRef(kind="emotion", ref_id="emo-2")],
            status="active",
            last_seen_at="2026-04-18T00:00:00Z",
        )
    ]

    payload = store_module.serialize_derived_user_model(model)
    reparsed = store_module.parse_derived_user_model(payload)

    assert reparsed.open_topic_anchors[0].anchor_key == "category:仕事"
    assert reparsed.hypotheses[0].key == "work_validation"
    assert reparsed.hypotheses[0].status == "active"
