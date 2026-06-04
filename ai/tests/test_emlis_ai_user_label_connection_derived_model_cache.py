# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

import pytest

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_derived_model_cache import (
    BLOCKER_ACTUAL_CACHE_DATA_DETECTED,
    BLOCKER_CACHE_PERSONALITY_OR_DIAGNOSIS_CLAIM_BLOCKED,
    BLOCKER_PRODUCT_QUALITY_QA_REQUIRED,
    BLOCKER_RUNTIME_MEASUREMENT_REQUIRED,
    BLOCKER_RUNTIME_NOT_MEASURED_HEAVY,
    CACHE_DECISION_FUTURE_REVIEW_ONLY,
    CACHE_DECISION_KEEP_RUNTIME_COMPUTED,
    USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_PHASE,
    USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_PREVIEW_SCHEMA_VERSION,
    assert_user_label_connection_derived_model_cache_contract,
    build_user_label_connection_derived_model_cache_consideration,
    build_user_label_connection_future_cache_schema_preview,
    user_label_connection_derived_model_cache_public_summary,
)
from emlis_ai_user_label_connection_material import build_user_label_connection_material

SECRET_CURRENT_MEMO = "PHASE10_SECRET_CURRENT_MEMO_SHOULD_NOT_LEAK"
SECRET_HISTORY_MEMO = "PHASE10_SECRET_HISTORY_MEMO_SHOULD_NOT_LEAK"
SECRET_COMMENT_TEXT = "PHASE10_SECRET_COMMENT_TEXT_SHOULD_NOT_LEAK"

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
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "body",
    "text",
}


def _current_input() -> dict[str, object]:
    return {
        "id": "phase10-current-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "会議のあとに言葉が出なかった",
        "memo": SECRET_CURRENT_MEMO,
    }


def _history_rows() -> tuple[dict[str, object], dict[str, object]]:
    return (
        {
            "id": "phase10-history-001",
            "created_at": "2026-05-29T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "職場で説明を求められた",
            "memo": SECRET_HISTORY_MEMO,
        },
        {
            "id": "phase10-history-002",
            "created_at": "2026-06-01T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "焦り", "strength": "medium"}],
            "memo_action": "連絡を返せなかった",
            "memo": "止まっていることが重く残っている",
        },
    )


def _source_bundle_with_history() -> SourceBundle:
    last, similar = _history_rows()
    return SourceBundle(
        user_id="phase10-user",
        display_name="Mash",
        current_input=_current_input(),
        last_input=last,
        same_day_recent_inputs=[],
        similar_inputs=[similar],
    )


def _material_meta() -> dict[str, Any]:
    material = build_user_label_connection_material(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )
    return material.as_meta()


def _passing_phase9_summary() -> dict[str, object]:
    return {
        "schema_version": "cocolon.emlis.user_label_connection.product_quality_qa.v1",
        "phase9_product_quality_qa_passed": True,
        "product_value_connected_by_qa": True,
        "public_release_applied": False,
        "comment_text": SECRET_COMMENT_TEXT,
    }


def _runtime_heavy_metrics() -> dict[str, object]:
    return {
        "measured_event_count": 48,
        "material_avg_ms": 510.0,
        "material_p95_ms": 900.0,
        "total_avg_ms": 1120.0,
    }


def _runtime_light_metrics() -> dict[str, object]:
    return {
        "measured_event_count": 48,
        "material_avg_ms": 120.0,
        "material_p95_ms": 180.0,
        "total_avg_ms": 260.0,
    }


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


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_secret_or_raw_payload(value: Any) -> None:
    dumped = _dump(value)
    assert FORBIDDEN_RAW_KEYS.isdisjoint(_all_keys(value))
    for secret in (SECRET_CURRENT_MEMO, SECRET_HISTORY_MEMO, SECRET_COMMENT_TEXT):
        assert secret not in dumped


def test_phase10_default_keeps_runtime_computed_and_does_not_implement_cache() -> None:
    meta = build_user_label_connection_derived_model_cache_consideration(
        runtime_material_meta=_material_meta(),
        product_quality_summary=None,
        runtime_metrics=None,
    )

    assert meta["schema_version"] == USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_SCHEMA_VERSION
    assert meta["phase"] == USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_PHASE
    assert meta["decision"] == CACHE_DECISION_KEEP_RUNTIME_COMPUTED
    assert meta["initial_v1_cache_implemented"] is False
    assert meta["cache_implementation_deferred"] is True
    assert meta["runtime_computed_material_kept"] is True
    assert meta["runtime_computed_material_is_source_of_truth_v1"] is True
    assert meta["cache_read_enabled"] is False
    assert meta["cache_write_enabled"] is False
    assert meta["cache_applied"] is False
    assert meta["cache_persisted"] is False
    assert meta["derived_user_model_write_attempted"] is False
    assert meta["db_physical_schema_changed"] is False
    assert meta["public_response_key_added"] is False
    assert meta["comment_text_generated"] is False
    assert meta["visible_surface_connected_by_this_layer"] is False
    assert BLOCKER_RUNTIME_MEASUREMENT_REQUIRED in meta["future_cache_candidate"]["blockers"]
    assert BLOCKER_PRODUCT_QUALITY_QA_REQUIRED in meta["future_cache_candidate"]["blockers"]
    _assert_no_secret_or_raw_payload(meta)


def test_phase10_schema_preview_is_future_only_and_contains_no_cache_data() -> None:
    preview = build_user_label_connection_future_cache_schema_preview(updated_at="2026-06-03T00:00:00Z")
    label_connection_map = preview["interpretive_frame"]["label_connection_map"]

    assert label_connection_map["schema_version"] == USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_PREVIEW_SCHEMA_VERSION
    assert label_connection_map["category_state_edges"] == []
    assert label_connection_map["state_output_edges"] == []
    assert label_connection_map["value_line_edges"] == []
    assert label_connection_map["updated_at"] == "2026-06-03T00:00:00Z"
    _assert_no_secret_or_raw_payload(preview)


def test_phase10_considers_future_cache_only_after_heavy_runtime_and_product_qa_pass() -> None:
    meta = build_user_label_connection_derived_model_cache_consideration(
        runtime_material_meta=_material_meta(),
        product_quality_summary=_passing_phase9_summary(),
        runtime_metrics=_runtime_heavy_metrics(),
    )

    assert meta["decision"] == CACHE_DECISION_FUTURE_REVIEW_ONLY
    assert meta["future_cache_candidate"]["eligible_for_future_design_review"] is True
    assert meta["future_cache_candidate"]["blockers"] == []
    assert meta["runtime_measurement"]["runtime_computed_material_measured_heavy"] is True
    assert meta["product_quality_dependency"]["phase9_product_quality_qa_passed"] is True
    assert meta["cache_read_enabled"] is False
    assert meta["cache_write_enabled"] is False
    assert meta["cache_persisted"] is False
    assert meta["db_physical_schema_changed"] is False
    _assert_no_secret_or_raw_payload(meta)


def test_phase10_blocks_future_cache_when_runtime_is_not_measured_heavy() -> None:
    meta = build_user_label_connection_derived_model_cache_consideration(
        runtime_material_meta=_material_meta(),
        product_quality_summary=_passing_phase9_summary(),
        runtime_metrics=_runtime_light_metrics(),
    )

    assert meta["decision"] == CACHE_DECISION_KEEP_RUNTIME_COMPUTED
    assert meta["future_cache_candidate"]["eligible_for_future_design_review"] is False
    assert BLOCKER_RUNTIME_NOT_MEASURED_HEAVY in meta["future_cache_candidate"]["blockers"]
    assert meta["cache_write_enabled"] is False
    assert meta["derived_user_model_write_attempted"] is False


def test_phase10_stale_existing_cache_never_strongly_applies_to_current_input() -> None:
    existing_model = {
        "interpretive_frame": {
            "label_connection_map": {
                "schema_version": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_PREVIEW_SCHEMA_VERSION,
                "category_state_edges": [],
                "state_output_edges": [],
                "value_line_edges": [],
                "updated_at": "2026-05-01T00:00:00Z",
            }
        }
    }
    meta = build_user_label_connection_derived_model_cache_consideration(
        runtime_material_meta=_material_meta(),
        product_quality_summary=_passing_phase9_summary(),
        runtime_metrics=_runtime_heavy_metrics(),
        existing_derived_user_model=existing_model,
        now_iso="2026-06-03T00:00:00Z",
    )

    assert meta["existing_derived_user_model_cache_summary"]["existing_cache_detected"] is True
    assert meta["existing_derived_user_model_cache_summary"]["existing_cache_may_be_stale"] is True
    assert meta["stale_cache_safety_contract"]["stale_cache_strong_application_allowed"] is False
    assert meta["stale_cache_safety_contract"]["stale_cache_current_input_strong_apply_blocked"] is True
    assert meta["future_cache_candidate"]["eligible_for_future_design_review"] is False
    assert "stale_cache_strong_application_blocked" in meta["future_cache_candidate"]["blockers"]
    assert meta["cache_applied"] is False




def test_phase10_existing_cache_with_actual_edges_or_personality_claim_is_future_blocked() -> None:
    existing_model = {
        "interpretive_frame": {
            "label_connection_map": {
                "schema_version": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_PREVIEW_SCHEMA_VERSION,
                "category_state_edges": [{"edge_id": "phase10-should-not-cache-actual-edge"}],
                "state_output_edges": [],
                "value_line_edges": [],
                "personality_claim": True,
                "updated_at": "2026-06-03T00:00:00Z",
            }
        }
    }
    meta = build_user_label_connection_derived_model_cache_consideration(
        runtime_material_meta=_material_meta(),
        product_quality_summary=_passing_phase9_summary(),
        runtime_metrics=_runtime_heavy_metrics(),
        existing_derived_user_model=existing_model,
        now_iso="2026-06-03T00:00:00Z",
    )

    assert meta["future_cache_candidate"]["eligible_for_future_design_review"] is False
    assert BLOCKER_ACTUAL_CACHE_DATA_DETECTED in meta["future_cache_candidate"]["blockers"]
    assert BLOCKER_CACHE_PERSONALITY_OR_DIAGNOSIS_CLAIM_BLOCKED in meta["future_cache_candidate"]["blockers"]
    assert meta["existing_derived_user_model_cache_summary"]["existing_cache_actual_edge_data_detected"] is True
    assert meta["existing_derived_user_model_cache_summary"]["existing_cache_personality_or_diagnosis_claim_detected"] is True
    assert meta["cache_applied"] is False
    assert meta["cache_write_enabled"] is False
    assert meta["claim_contract"]["cache_used_for_personality_claim"] is False
    assert meta["claim_contract"]["cache_used_for_diagnosis"] is False

@pytest.mark.parametrize(
    "bad_meta",
    [
        {"comment_text": SECRET_COMMENT_TEXT},
        {"cache_write_enabled": True},
        {"cache_read_enabled": True},
        {"db_physical_schema_changed": True},
        {"public_response_key_added": True},
        {"cache_used_for_personality_claim": True},
        {"cache_used_for_diagnosis": True},
        {"future_cache_candidate": {"schema_preview": {"category_state_edges": [{"edge_id": "actual"}]}}},
    ],
)
def test_phase10_contract_rejects_raw_text_actual_cache_and_contract_relaxation(bad_meta: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_derived_model_cache_contract(bad_meta)


def test_phase10_public_summary_is_counts_and_flags_only() -> None:
    meta = build_user_label_connection_derived_model_cache_consideration(
        runtime_material_meta=_material_meta(),
        product_quality_summary=_passing_phase9_summary(),
        runtime_metrics=_runtime_heavy_metrics(),
    )
    summary = user_label_connection_derived_model_cache_public_summary(meta)

    assert summary["schema_version"] == USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_SCHEMA_VERSION
    assert summary["runtime_computed_material_kept"] is True
    assert summary["initial_v1_cache_implemented"] is False
    assert summary["cache_implementation_deferred"] is True
    assert summary["cache_read_enabled"] is False
    assert summary["cache_write_enabled"] is False
    assert summary["derived_user_model_write_attempted"] is False
    assert summary["db_physical_schema_changed"] is False
    assert summary["public_response_key_added"] is False
    assert summary["future_cache_design_review_candidate"] is True
    _assert_no_secret_or_raw_payload(summary)
