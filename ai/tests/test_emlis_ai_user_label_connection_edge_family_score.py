# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import DerivedUserModel, InterpretiveFrameProfile, SourceBundle, ValueAnchor
from emlis_ai_user_label_connection_material import (
    assert_user_label_connection_material_meta_contract,
    build_user_label_connection_material,
)
from emlis_ai_user_label_connection_types import (
    EDGE_FAMILY_ACTION_STATE_BRIDGE,
    EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
    EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
    EDGE_FAMILY_CONTRAST_LINE_SHIFT,
    EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
    EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
    EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
    EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
)


SECRET_CURRENT_MEMO = "PHASE3_SECRET_CURRENT_MEMO_SHOULD_NOT_LEAK"
SECRET_HISTORY_MEMO = "PHASE3_SECRET_HISTORY_MEMO_SHOULD_NOT_LEAK"


def _connected_current() -> dict[str, object]:
    return {
        "id": "phase3-current-connected",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場で説明できなかった",
        "memo": "このまま続けられるかわからない",
    }


def _connected_bundle() -> SourceBundle:
    return SourceBundle(
        user_id="phase3-connected-user",
        display_name="Mash",
        current_input=_connected_current(),
        last_input={
            "id": "phase3-history-last",
            "created_at": "2026-06-01T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "職場で言葉に詰まった",
            "memo": "続けたいのに限界が近い感じがある",
        },
        same_day_recent_inputs=[
            {
                "id": "phase3-history-sameday",
                "created_at": "2026-06-03T01:00:00+00:00",
                "category": ["仕事"],
                "emotion_details": [{"type": "焦り", "strength": "weak"}],
                "memo_action": "連絡を返せなかった",
                "memo": "進めたいのに動けない感じがある",
            }
        ],
        similar_inputs=[
            {
                "id": "phase3-history-similar",
                "created_at": "2026-05-28T00:00:00+00:00",
                "category": ["仕事"],
                "emotion_details": [{"type": "不安", "strength": "strong"}],
                "memo_action": "職場で説明を求められた",
                "memo": "続けたい気持ちと限界が同時にある",
            }
        ],
        derived_user_model=DerivedUserModel(
            schema_version="emlis.derived_user_model.v1",
            model_tier="plus",
            interpretive_frame=InterpretiveFrameProfile(
                value_anchors=[ValueAnchor(key="work_continuity_line", confidence=0.8)]
            ),
        ),
    )


def _all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_all_keys(child))
    return keys


def test_phase3_builds_dynamic_edge_families_with_private_scores() -> None:
    material = build_user_label_connection_material(
        _connected_current(),
        source_bundle=_connected_bundle(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )
    meta = material.as_meta()

    edge_by_family = {edge["edge_family"]: edge for edge in meta["connection_edges"]}
    assert {
        EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
        EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
        EDGE_FAMILY_ACTION_STATE_BRIDGE,
        EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
        EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
        EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
        EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
        EDGE_FAMILY_CONTRAST_LINE_SHIFT,
    }.issubset(edge_by_family)

    recurrence = edge_by_family[EDGE_FAMILY_CATEGORY_STATE_RECURRENCE]
    assert recurrence["evidence_record_count"] >= 2
    assert recurrence["source_field_ids"] == ["category", "emotion_details", "created_at"]
    assert recurrence["source_scope_marker_required"] is True
    assert recurrence["soft_marker_required"] is True
    assert recurrence["line_is_candidate"] is True
    assert recurrence["line_is_fact"] is False

    for edge in meta["connection_edges"]:
        score = edge["edge_score"]
        assert score["schema_version"] == "cocolon.emlis.user_label_connection_edge_score.v1"
        assert score["score_is_public"] is False
        assert 0.0 <= score["label_overlap_score"] <= 1.0
        assert 0.0 <= score["axis_overlap_score"] <= 1.0
        assert 0.0 <= score["evidence_record_count_score"] <= 1.0
        assert 0.0 <= score["current_alignment_score"] <= 1.0
        assert 0.0 <= score["final_score"] <= 1.0
        assert edge["raw_text_included"] is False
        assert edge["comment_text_body_included"] is False

    assert meta["phase3_edge_family_scoring_ready"] is True
    assert meta["phase3_edge_family_scoring_deferred"] is False
    assert meta["candidate_builder_deferred"] is True
    assert meta["gate_deferred"] is True
    assert meta["surface_plan_deferred"] is True
    assert meta["comment_text_generated_by_this_layer"] is False
    assert meta["public_response_key_added"] is False
    assert_user_label_connection_material_meta_contract(meta)


def test_phase3_disconnected_history_keeps_edges_empty() -> None:
    current_input = {
        "id": "phase3-current-disconnected",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["健康"],
        "emotion_details": [{"type": "楽しい", "strength": "weak"}],
        "memo_action": "公園を歩いた",
        "memo": "朝の散歩が気持ちよかった",
    }
    source_bundle = SourceBundle(
        user_id="phase3-disconnected-user",
        display_name="Mash",
        current_input=current_input,
        last_input={
            "id": "phase3-history-disconnected",
            "created_at": "2026-05-28T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "怒り", "strength": "medium"}],
            "memo_action": "締切前に資料を提出した",
            "memo": "会議の進行だけを確認した",
        },
    )

    material = build_user_label_connection_material(
        current_input,
        source_bundle=source_bundle,
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )
    meta = material.as_meta()

    assert meta["owned_history_points_summary"]["point_count"] == 1
    assert meta["connection_edges"] == []
    assert meta["connection_edge_count"] == 0
    assert meta["comment_text_generated"] is False
    assert meta["surface_body_included"] is False
    assert_user_label_connection_material_meta_contract(meta)


def test_phase3_edge_family_meta_does_not_leak_raw_text_or_surface_body() -> None:
    current_input = {
        "id": "phase3-current-secret",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場で説明できなかった",
        "memo": SECRET_CURRENT_MEMO,
    }
    source_bundle = SourceBundle(
        user_id="phase3-secret-user",
        display_name="Mash",
        current_input=current_input,
        last_input={
            "id": "phase3-history-secret",
            "created_at": "2026-06-01T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "職場で説明を求められた",
            "memo": SECRET_HISTORY_MEMO,
        },
    )

    meta = build_user_label_connection_material(
        current_input,
        source_bundle=source_bundle,
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    ).as_meta()
    dumped = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert SECRET_CURRENT_MEMO not in dumped
    assert SECRET_HISTORY_MEMO not in dumped
    assert "candidate_body" not in _all_keys(meta)
    assert "surface_body" not in _all_keys(meta)
    assert "comment_text" not in _all_keys(meta)
    assert meta["candidate_body_included"] is False
    assert meta["surface_body_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["comment_text_generated"] is False
    assert_user_label_connection_material_meta_contract(meta)
