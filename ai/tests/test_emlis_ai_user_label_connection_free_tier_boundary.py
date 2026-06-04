# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_material import (
    assert_user_label_connection_material_meta_contract,
    build_user_label_connection_material,
)
from emlis_ai_user_label_connection_types import (
    MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED,
    RECORD_SCOPE_BLOCKED_FREE_TIER,
    SOURCE_SCOPE_CURRENT_ONLY,
)


def test_phase2_free_tier_keeps_history_edges_and_history_points_empty() -> None:
    capability = resolve_emlis_ai_capability_for_tier("free")
    current_input = {
        "id": "current-free-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場で話した",
        "memo": "続けられるかわからない",
    }
    source_bundle = SourceBundle(
        user_id="phase2-free-user",
        display_name="Mash",
        current_input=current_input,
        last_input={
            "id": "history-free-last-001",
            "created_at": "2026-06-01T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "過去の行動本文はmaterial metaに出さない",
            "memo": "過去の思考本文はmaterial metaに出さない",
        },
        same_day_recent_inputs=[
            {
                "id": "history-free-same-001",
                "created_at": "2026-06-03T01:00:00+00:00",
                "category": ["仕事"],
                "emotion_details": [{"type": "焦り", "strength": "weak"}],
                "memo_action": "same day secret action",
                "memo": "same day secret thought",
            }
        ],
        similar_inputs=[
            {
                "id": "history-free-similar-001",
                "created_at": "2026-05-29T00:00:00+00:00",
                "category": ["仕事"],
                "emotion_details": [{"type": "不安", "strength": "strong"}],
                "memo_action": "similar secret action",
                "memo": "similar secret thought",
            }
        ],
    )

    material = build_user_label_connection_material(current_input, source_bundle=source_bundle, capability=capability)
    meta = material.as_meta()

    assert meta["capability_tier"] == "free"
    assert meta["source_scope"] == SOURCE_SCOPE_CURRENT_ONLY
    assert meta["record_scope"] == RECORD_SCOPE_BLOCKED_FREE_TIER
    assert meta["history_read_allowed"] is False
    # Free may run the grounding boundary for inventory, but history still must
    # not be materialized or edged.
    assert meta["current_point_present"] is True
    assert material.owned_history_points == ()
    assert meta["owned_history_points_summary"] == {
        "available": False,
        "point_count": 0,
        "same_day_count": 0,
        "similar_count": 0,
        "last_input_present": False,
        "derived_user_model_anchor_count": 0,
        "raw_text_included": False,
    }
    assert meta["connection_edges"] == []
    assert meta["connection_edge_count"] == 0
    assert meta["material_quality"] == MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    assert_user_label_connection_material_meta_contract(meta)
