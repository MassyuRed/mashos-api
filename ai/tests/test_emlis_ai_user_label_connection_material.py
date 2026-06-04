# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_fact_grounding_boundary import resolve_user_fact_grounding_boundary
from emlis_ai_user_label_connection_material import (
    assert_user_label_connection_material_meta_contract,
    build_user_label_connection_material,
    build_user_label_point,
)
from emlis_ai_user_label_connection_types import (
    EDGE_FAMILY_ACTION_STATE_BRIDGE,
    EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
    EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
    EDGE_FAMILY_CONTRAST_LINE_SHIFT,
    EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
    EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
    EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
    MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED,
    MATERIAL_QUALITY_HISTORY_CONNECTION_CANDIDATE,
    MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED,
    MATERIAL_QUALITY_NO_HISTORY_AVAILABLE,
    RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY,
    RECORD_SCOPE_CURRENT_ONLY,
    RECORD_SCOPE_CURRENT_PLUS_OWNED_HISTORY,
    SOURCE_KIND_CURRENT_INPUT,
    SOURCE_KIND_LAST_INPUT,
    SOURCE_KIND_SAME_DAY_RECENT_INPUT,
    SOURCE_KIND_SIMILAR_INPUT,
    SOURCE_SCOPE_CURRENT_ONLY,
    USER_LABEL_CONNECTION_MATERIAL_SCHEMA_VERSION,
    USER_LABEL_POINT_SCHEMA_VERSION,
)


def _current_input() -> dict[str, object]:
    return {
        "id": "current-phase2-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場でうまく話せなかった",
        "memo": "このまま続けられるかわからない",
    }


def _history_rows() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        {
            "id": "history-last-001",
            "created_at": "2026-06-02T22:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "会議で言葉に詰まった",
            "memo": "また同じところで止まっている気がする",
        },
        {
            "id": "history-sameday-001",
            "created_at": "2026-06-03T01:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "焦り", "strength": "weak"}],
            "memo_action": "朝から連絡を返せなかった",
            "memo": "進めたいのに動けない感じがある",
        },
        {
            "id": "history-similar-001",
            "created_at": "2026-05-28T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "memo_action": "職場で説明を求められた",
            "memo": "続けたい気持ちと限界が同時にある",
        },
    )


def _source_bundle_with_history() -> SourceBundle:
    last_input, same_day, similar = _history_rows()
    return SourceBundle(
        user_id="phase2-user",
        display_name="Mash",
        current_input=_current_input(),
        last_input=last_input,
        same_day_recent_inputs=[same_day],
        similar_inputs=[similar],
    )


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_phase2_user_label_point_normalizes_current_input_axes_without_tendency() -> None:
    point = build_user_label_point(
        _current_input(),
        source_kind=SOURCE_KIND_CURRENT_INPUT,
        selected_at_bucket="current",
    )
    meta = point.as_meta()

    assert meta["schema_version"] == USER_LABEL_POINT_SCHEMA_VERSION
    assert meta["source_kind"] == SOURCE_KIND_CURRENT_INPUT
    assert meta["source_scope"] == SOURCE_SCOPE_CURRENT_ONLY
    assert meta["source_record_id_present"] is True
    assert meta["selected_at_present"] is True
    assert meta["point_is_tendency"] is False

    axes = meta["label_axes"]
    assert axes["environment"]["category_labels"] == ["仕事"]
    assert axes["environment"]["has_action_axis"] is True
    assert axes["environment"]["source_field_ids"] == ["category", "memo_action"]
    assert axes["state"]["emotion_labels"] == ["不安"]
    assert axes["state"]["strength_bucket"] == "strong"
    assert axes["state"]["source_field_ids"] == ["emotion_details", "strength"]
    assert axes["output"]["has_thought_axis"] is True
    assert axes["output"]["thought_token_fingerprint_count"] > 0
    assert axes["output"]["source_field_ids"] == ["memo"]
    assert axes["time"]["selected_at_bucket"] == "current"
    assert axes["time"]["source_field_ids"] == ["created_at"]
    assert meta["evidence_anchor"] == {
        "record_id_hash_present": True,
        "raw_text_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


@pytest.mark.parametrize("tier", ["plus", "premium"])
def test_phase2_plus_premium_materialize_owned_history_points_after_grounding_boundary(tier: str) -> None:
    capability = resolve_emlis_ai_capability_for_tier(tier)
    bundle = _source_bundle_with_history()
    material = build_user_label_connection_material(
        _current_input(),
        source_bundle=bundle,
        capability=capability,
    )
    meta = material.as_meta()

    assert meta["schema_version"] == USER_LABEL_CONNECTION_MATERIAL_SCHEMA_VERSION
    assert meta["record_scope"] == RECORD_SCOPE_CURRENT_PLUS_OWNED_HISTORY
    assert meta["capability_tier"] == tier
    assert meta["history_read_allowed"] is True
    assert meta["user_fact_grounding_boundary_passed"] is True
    assert meta["low_information_protected"] is False
    assert meta["material_quality"] == MATERIAL_QUALITY_HISTORY_CONNECTION_CANDIDATE
    assert meta["current_point_present"] is True
    assert len(material.owned_history_points) == 3
    assert [point.source_kind for point in material.owned_history_points] == [
        SOURCE_KIND_LAST_INPUT,
        SOURCE_KIND_SAME_DAY_RECENT_INPUT,
        SOURCE_KIND_SIMILAR_INPUT,
    ]
    assert meta["owned_history_points_summary"] == {
        "available": True,
        "point_count": 3,
        "same_day_count": 1,
        "similar_count": 1,
        "last_input_present": True,
        "derived_user_model_anchor_count": 0,
        "raw_text_included": False,
    }
    assert meta["owned_history_points"][0]["label_axes"]["environment"]["source_field_ids"] == [
        "category",
        "memo_action",
    ]
    edge_families = {edge["edge_family"] for edge in meta["connection_edges"]}
    assert {
        EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
        EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
        EDGE_FAMILY_ACTION_STATE_BRIDGE,
        EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
        EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
        EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
        EDGE_FAMILY_CONTRAST_LINE_SHIFT,
    }.issubset(edge_families)
    assert meta["connection_edge_count"] == len(meta["connection_edges"])
    assert meta["connection_edge_count"] >= 6
    for edge in meta["connection_edges"]:
        assert edge["evidence_record_count"] >= 2
        assert edge["source_field_ids"]
        assert edge["source_scope_marker_required"] is True
        assert edge["soft_marker_required"] is True
        assert edge["line_is_candidate"] is True
        assert edge["line_is_fact"] is False
        assert edge["raw_text_included"] is False
        assert edge["comment_text_body_included"] is False
        assert edge["edge_score"]["score_is_public"] is False
        assert 0.0 <= edge["edge_score"]["final_score"] <= 1.0
    assert meta["phase3_edge_family_scoring_ready"] is True
    assert meta["phase3_edge_family_scoring_deferred"] is False
    assert meta["candidate_builder_deferred"] is True
    assert meta["gate_deferred"] is True
    assert meta["surface_plan_deferred"] is True
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    assert meta["raw_input_included"] is False
    assert meta["raw_text_included"] is False
    assert meta["comment_text_body_included"] is False
    assert_user_label_connection_material_meta_contract(meta)


def test_phase2_history_absent_returns_safe_empty_material_without_comment_generation() -> None:
    capability = resolve_emlis_ai_capability_for_tier("plus")
    source_bundle = SourceBundle(
        user_id="phase2-user",
        display_name="Mash",
        current_input=_current_input(),
    )

    material = build_user_label_connection_material(_current_input(), source_bundle=source_bundle, capability=capability)
    meta = material.as_meta()

    assert meta["record_scope"] == RECORD_SCOPE_CURRENT_ONLY
    assert meta["history_read_allowed"] is True
    assert meta["owned_history_points_summary"]["available"] is False
    assert meta["owned_history_points_summary"]["point_count"] == 0
    assert meta["connection_edges"] == []
    assert meta["material_quality"] == MATERIAL_QUALITY_NO_HISTORY_AVAILABLE
    assert meta["comment_text_generated_by_this_layer"] is False
    assert_user_label_connection_material_meta_contract(meta)


def test_phase2_grounding_boundary_block_keeps_history_out_of_material() -> None:
    capability = resolve_emlis_ai_capability_for_tier("plus")
    bundle = _source_bundle_with_history()
    free_decision = resolve_user_fact_grounding_boundary(
        subscription_tier="free",
        source_bundle=bundle,
        current_input=_current_input(),
    )
    material = build_user_label_connection_material(
        _current_input(),
        source_bundle=bundle,
        capability=capability,
        user_fact_grounding_decision=free_decision,
    )
    meta = material.as_meta()

    assert meta["record_scope"] == RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY
    assert meta["history_read_allowed"] is False
    assert meta["user_fact_grounding_boundary_passed"] is False
    assert meta["owned_history_points_summary"]["point_count"] == 0
    assert meta["connection_edges"] == []
    assert meta["material_quality"] == MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED
    assert_user_label_connection_material_meta_contract(meta)


def test_phase2_low_information_boundary_does_not_promote_with_history() -> None:
    capability = resolve_emlis_ai_capability_for_tier("plus")
    material = build_user_label_connection_material(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=capability,
        observation_reply_meta={
            "observation_reply_kind": "low_information_observation",
            "eligibility_status": "low_information",
            "low_information_protected": True,
        },
    )
    meta = material.as_meta()

    assert meta["record_scope"] == RECORD_SCOPE_CURRENT_ONLY
    assert meta["low_information_protected"] is True
    assert meta["history_read_allowed"] is False
    assert meta["owned_history_points_summary"]["point_count"] == 0
    assert meta["connection_edges"] == []
    assert meta["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED
    assert "eligible" not in _dump(meta["material_quality"])
    assert_user_label_connection_material_meta_contract(meta)
