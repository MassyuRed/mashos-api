# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_candidate import (
    CANDIDATE_QUALITY_BLOCKED,
    CANDIDATE_QUALITY_GATE_CANDIDATE,
    CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE,
    FORBIDDEN_CLAIMS,
    MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT,
    MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE,
    USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION,
    assert_user_label_connection_candidate_meta_contract,
    build_user_label_connection_candidate_meta,
    build_user_label_connection_candidates,
)
from emlis_ai_user_label_connection_material import build_user_label_connection_material
from emlis_ai_user_label_connection_types import SOURCE_SCOPE_OWNED_HISTORY

SECRET_CURRENT_MEMO = "PHASE4_SECRET_CURRENT_MEMO_SHOULD_NOT_LEAK"
SECRET_CURRENT_ACTION = "PHASE4_SECRET_CURRENT_ACTION_SHOULD_NOT_LEAK"
SECRET_HISTORY_MEMO = "PHASE4_SECRET_HISTORY_MEMO_SHOULD_NOT_LEAK"
SECRET_HISTORY_ACTION = "PHASE4_SECRET_HISTORY_ACTION_SHOULD_NOT_LEAK"
SECRET_COMMENT_BODY = "PHASE4_SECRET_COMMENT_BODY_SHOULD_NOT_LEAK"

FORBIDDEN_RAW_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "current_input",
    "currentInput",
    "history_input",
    "historyInput",
    "memo",
    "memo_action",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "surface_body",
    "body",
    "text",
}


def _current_input() -> dict[str, object]:
    return {
        "id": "current-phase4-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場でうまく話せなかった",
        "memo": "このまま続けられるかわからない",
    }


def _history_rows() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        {
            "id": "history-phase4-last-001",
            "created_at": "2026-06-02T22:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "会議で言葉に詰まった",
            "memo": "また同じところで止まっている気がする",
        },
        {
            "id": "history-phase4-sameday-001",
            "created_at": "2026-06-03T01:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "焦り", "strength": "weak"}],
            "memo_action": "朝から連絡を返せなかった",
            "memo": "進めたいのに動けない感じがある",
        },
        {
            "id": "history-phase4-similar-001",
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
        user_id="phase4-user",
        display_name="Mash",
        current_input=_current_input(),
        last_input=last_input,
        same_day_recent_inputs=[same_day],
        similar_inputs=[similar],
    )


def _material_with_edges() -> Any:
    return build_user_label_connection_material(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
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


def test_phase4_candidate_builder_creates_gate_candidates_from_phase3_edges_without_visible_text() -> None:
    material = _material_with_edges()
    candidates = build_user_label_connection_candidates(material)
    metas = [candidate.as_meta() for candidate in candidates]

    assert metas
    families = {meta["mechanism_family"] for meta in metas}
    assert MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT in families
    assert MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE in families

    primary = metas[0]
    assert primary["schema_version"] == USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION
    assert primary["candidate_kind"] == "user_label_connection_mechanism"
    assert primary["source_scope"] == SOURCE_SCOPE_OWNED_HISTORY
    assert primary["requires_user_history"] is True
    assert primary["current_input_required"] is True
    assert primary["candidate_quality"] == CANDIDATE_QUALITY_GATE_CANDIDATE
    assert primary["supporting_edge_ids"]

    evidence = primary["evidence"]
    assert evidence["evidence_record_count"] >= 2
    assert evidence["current_record_included"] is True
    assert evidence["history_record_count"] >= 1
    assert {"category", "emotion_details"}.issubset(set(evidence["source_field_ids"]))
    assert evidence["requires_external_knowledge"] is False
    assert evidence["raw_text_included"] is False
    assert evidence["raw_input_included"] is False
    assert evidence["comment_text_body_included"] is False

    permission = primary["surface_permission"]
    assert permission["may_surface_now"] is False
    assert permission["may_surface_after_user_label_connection_gate"] is True
    assert permission["must_use_soft_expression"] is True
    assert permission["must_use_scope_marker"] is True
    assert permission["must_not_surface_as_fact"] is True
    assert permission["must_not_surface_as_personality"] is True
    assert permission["must_not_surface_as_diagnosis"] is True
    assert permission["must_not_surface_as_cause"] is True
    assert permission["must_not_surface_as_advice"] is True

    assert set(FORBIDDEN_CLAIMS).issubset(set(primary["forbidden_claims"]))
    assert primary["candidate_body_included"] is False
    assert primary["comment_text_generated"] is False
    assert primary["public_response_key_added"] is False
    assert_user_label_connection_candidate_meta_contract(primary)


def test_phase4_edge_shortage_returns_insufficient_evidence_candidate() -> None:
    capability = resolve_emlis_ai_capability_for_tier("plus")
    source_bundle = SourceBundle(
        user_id="phase4-no-history-user",
        display_name="Mash",
        current_input=_current_input(),
    )
    material = build_user_label_connection_material(_current_input(), source_bundle=source_bundle, capability=capability)

    meta = build_user_label_connection_candidate_meta(material)

    assert meta["candidate_quality"] == CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE
    assert meta["supporting_edge_ids"] == []
    assert meta["evidence"]["evidence_record_count"] == 1
    assert meta["evidence"]["history_record_count"] == 0
    assert meta["surface_permission"]["may_surface_now"] is False
    assert meta["surface_permission"]["may_surface_after_user_label_connection_gate"] is False
    assert meta["candidate_body_included"] is False
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    assert_user_label_connection_candidate_meta_contract(meta)


def test_phase4_evidence_record_count_less_than_two_does_not_become_surface_candidate() -> None:
    material_meta = _material_with_edges().as_meta()
    material_meta["connection_edges"] = [dict(material_meta["connection_edges"][0])]
    material_meta["connection_edge_count"] = 1
    material_meta["connection_edges"][0]["evidence_record_count"] = 1
    material_meta["connection_edges"][0]["evidence_point_ids"] = ["current:present"]

    meta = build_user_label_connection_candidate_meta(material_meta)

    assert meta["candidate_quality"] == CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE
    assert meta["evidence"]["evidence_record_count"] == 1
    assert meta["evidence"]["current_record_included"] is True
    assert meta["evidence"]["history_record_count"] == 0
    assert meta["surface_permission"]["may_surface_after_user_label_connection_gate"] is False
    assert_user_label_connection_candidate_meta_contract(meta)


def test_phase4_history_only_candidate_is_blocked_before_gate() -> None:
    material_meta = _material_with_edges().as_meta()
    material_meta["connection_edges"] = [dict(material_meta["connection_edges"][0])]
    material_meta["connection_edge_count"] = 1
    material_meta["connection_edges"][0]["evidence_record_count"] = 2
    material_meta["connection_edges"][0]["evidence_point_ids"] = [
        "history:last_input:001",
        "history:similar_input:001",
    ]

    meta = build_user_label_connection_candidate_meta(material_meta)

    assert meta["candidate_quality"] == CANDIDATE_QUALITY_BLOCKED
    assert meta["evidence"]["evidence_record_count"] == 2
    assert meta["evidence"]["current_record_included"] is False
    assert meta["evidence"]["history_record_count"] == 2
    assert meta["surface_permission"]["may_surface_now"] is False
    assert meta["surface_permission"]["may_surface_after_user_label_connection_gate"] is False
    assert meta["candidate_body_included"] is False
    assert meta["comment_text_generated"] is False
    assert_user_label_connection_candidate_meta_contract(meta)


def test_phase4_candidate_meta_does_not_include_raw_current_history_comment_or_candidate_body() -> None:
    current_input = {
        "id": "current-phase4-no-raw-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": SECRET_CURRENT_ACTION,
        "memo": SECRET_CURRENT_MEMO,
        "comment_text": SECRET_COMMENT_BODY,
    }
    source_bundle = SourceBundle(
        user_id="phase4-no-raw-user",
        display_name="Mash",
        current_input=current_input,
        last_input={
            "id": "history-phase4-no-raw-last-001",
            "created_at": "2026-06-01T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": SECRET_HISTORY_ACTION,
            "memo": SECRET_HISTORY_MEMO,
            "comment_text": SECRET_COMMENT_BODY,
        },
    )
    material = build_user_label_connection_material(
        current_input,
        source_bundle=source_bundle,
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )

    metas = [candidate.as_meta() for candidate in build_user_label_connection_candidates(material)]
    dumped = json.dumps(metas, ensure_ascii=False, sort_keys=True)

    for meta in metas:
        assert FORBIDDEN_RAW_KEYS.isdisjoint(_all_keys(meta))
        assert meta["candidate_body_included"] is False
        assert meta["comment_text_generated"] is False
        assert meta["public_response_key_added"] is False
        assert_user_label_connection_candidate_meta_contract(meta)
    for secret in (
        SECRET_CURRENT_MEMO,
        SECRET_CURRENT_ACTION,
        SECRET_HISTORY_MEMO,
        SECRET_HISTORY_ACTION,
        SECRET_COMMENT_BODY,
    ):
        assert secret not in dumped
