# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import json
from dataclasses import fields
from typing import Any

import pytest

from api_contract_registry import (
    OWNER_PUBLIC_API,
    PUBLIC_API_CONTRACTS,
    REQUEST_POLICY_ADDITIVE_ONLY,
    RESPONSE_POLICY_ADDITIVE_ONLY,
)
from api_emotion_submit import EmotionSubmitInputFeedback, EmotionSubmitResponse
from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_complete_composer_client import build_complete_composer_client_contract_meta
from emlis_ai_context_service import build_emlis_ai_source_bundle
from emlis_ai_current_input_bundle import build_emlis_current_input_bundle, normalize_emlis_current_input
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_reply_service import render_emlis_ai_reply
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_contract_inventory import (
    USER_LABEL_CONNECTION_CONTRACT_INVENTORY_SCHEMA_VERSION,
    assert_user_label_connection_contract_inventory_meta_only,
    build_user_label_connection_contract_inventory,
    dump_user_label_connection_contract_inventory,
)


def _model_field_names(model: type[Any]) -> set[str]:
    fields_v2 = getattr(model, "model_fields", None)
    if isinstance(fields_v2, dict):
        return set(fields_v2)
    fields_v1 = getattr(model, "__fields__", None)
    if isinstance(fields_v1, dict):
        return set(fields_v1)
    return set()


def test_user_label_connection_phase1_inventory_is_meta_only_and_defers_runtime_layers() -> None:
    inventory = build_user_label_connection_contract_inventory()

    assert inventory["schema_version"] == USER_LABEL_CONNECTION_CONTRACT_INVENTORY_SCHEMA_VERSION
    assert inventory["implementation_scope"] == "phase0_design_doc_and_phase1_contract_inventory_only"
    assert inventory["design_document_added"] is True
    assert inventory["work_attitude_rules_folder"] == "work_attitude_rules_for_karen"

    assert inventory["api_route_changed"] is False
    assert inventory["request_key_changed"] is False
    assert inventory["response_shape_changed"] is False
    assert inventory["public_response_key_added"] is False
    assert inventory["db_physical_name_changed"] is False
    assert inventory["rn_visible_contract_changed"] is False
    assert inventory["rn_visible_title_changed"] is False
    assert inventory["structure_insight_gate_relaxed"] is False
    assert inventory["user_label_connection_runtime_connected"] is False
    assert inventory["user_label_connection_comment_text_generated"] is False
    assert inventory["fixed_sentence_template_added"] is False
    assert inventory["external_ai_added"] is False
    assert inventory["local_llm_added"] is False
    assert inventory["raw_input_included"] is False
    assert inventory["raw_text_included"] is False
    assert inventory["comment_text_body_included"] is False
    assert inventory["history_raw_text_included"] is False

    assert "emlis_ai_user_label_connection_material.py" in inventory["phase2_runtime_layers_deferred"]
    assert "emlis_ai_user_label_connection_gate.py" in inventory["phase2_runtime_layers_deferred"]
    assert "diagnosis/personality/future/advice surface" in inventory["non_targets"]

    lock_ids = {item["contract_id"] for item in inventory["contract_locks"]}
    assert "emotion_submit_route_stable" in lock_ids
    assert "input_feedback_comment_text_display_source" in lock_ids
    assert "input_feedback_emlis_ai_additive_meta" in lock_ids
    assert "rn_passed_plus_non_empty_comment_contract" in lock_ids
    assert "rn_visible_title_stable" in lock_ids
    assert "structure_insight_gate_not_relaxed" in lock_ids
    assert "public_meta_raw_body_boundary" in lock_ids

    assert_user_label_connection_contract_inventory_meta_only(inventory)
    dumped = dump_user_label_connection_contract_inventory(inventory)
    parsed = json.loads(dumped)
    assert parsed["raw_text_included"] is False
    assert "raw memo body" not in dumped

    unsafe = dict(inventory)
    unsafe["raw_text"] = "this body must not be accepted by contract inventory"
    with pytest.raises(ValueError):
        assert_user_label_connection_contract_inventory_meta_only(unsafe)


def test_user_label_connection_phase1_emotion_submit_registry_and_response_shape_stay_stable() -> None:
    matches = [
        entry
        for entry in PUBLIC_API_CONTRACTS
        if entry.method == "POST" and entry.path == "/emotion/submit"
    ]
    assert len(matches) == 1
    entry = matches[0]

    assert entry.contract_id == "emotion.submit.v1"
    assert entry.owner == OWNER_PUBLIC_API
    assert entry.request_policy == REQUEST_POLICY_ADDITIVE_ONLY
    assert entry.response_policy == RESPONSE_POLICY_ADDITIVE_ONLY
    assert entry.deprecated is False
    assert "input_feedback.comment_text stays stable" in str(entry.notes or "")
    assert "input_feedback.emlis_ai remains additive-only" in str(entry.notes or "")

    assert _model_field_names(EmotionSubmitResponse) == {"status", "id", "created_at", "input_feedback"}
    assert _model_field_names(EmotionSubmitInputFeedback) == {"comment_text", "emlis_ai"}


def test_user_label_connection_phase1_public_feedback_still_requires_passed_and_non_empty_comment_text() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": "plus",
            "observation_status": "passed",
            "user_label_connection_contract_probe": {
                "history_connection_candidate_present": True,
                "public_response_key_added": False,
                "raw_text_included": False,
                "comment_text_body_included": False,
            },
        },
        comment_text_present=True,
        subscription_tier="plus",
    )

    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback("public Emlis observation body", public_meta) is True
    assert should_include_public_input_feedback("   ", public_meta) is False
    assert should_include_public_input_feedback("public Emlis observation body", None) is False

    for status in ("rejected", "unavailable", "safety_blocked", ""):
        candidate = dict(public_meta)
        candidate["observation_status"] = status
        assert should_include_public_input_feedback("public Emlis observation body", candidate) is False


def test_user_label_connection_phase1_public_meta_sanitizer_does_not_expose_raw_text_or_comment_body() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": "premium",
            "observation_status": "passed",
            "raw_input": "ulc secret raw input must not leak",
            "raw_text": "ulc secret evidence text must not leak",
            "comment_text": "ulc internal comment body must not leak",
            "candidate_comment_text": "ulc candidate body must not leak",
            "candidate_body": "ulc candidate body must not leak",
            "diagnostic_summary": {
                "stage": "ulc_phase1_contract",
                "observation_status": "passed",
                "raw_input": "ulc diagnostic raw input must not leak",
                "raw_text": "ulc diagnostic raw text must not leak",
                "comment_text": "ulc diagnostic comment body must not leak",
            },
            "evidence_spans": [
                {"raw_text": "ulc evidence span raw text must not leak"},
            ],
        },
        comment_text_present=True,
        subscription_tier="premium",
    )

    dumped = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    for fragment in (
        "ulc secret raw input must not leak",
        "ulc secret evidence text must not leak",
        "ulc internal comment body must not leak",
        "ulc candidate body must not leak",
        "ulc diagnostic raw input must not leak",
        "ulc diagnostic raw text must not leak",
        "ulc diagnostic comment body must not leak",
        "ulc evidence span raw text must not leak",
        "candidate_comment_text",
    ):
        assert fragment not in dumped

    # Step 8 adds explicit body-free boundary markers.
    # Keep forbidding the raw candidate body key itself, while allowing
    # candidate_body_included=false as a public sanitizer marker.
    assert '"candidate_body":' not in dumped
    boundary = public_meta["public_feedback_meta_boundary"]
    assert boundary["raw_input_included"] is False
    assert boundary["comment_text_body_included"] is False
    assert boundary["candidate_body_included"] is False
    assert boundary["internal_meta_returned"] is False
    assert public_meta["observation_status"] == "passed"


def test_user_label_connection_phase1_current_input_contract_keeps_label_connection_source_fields() -> None:
    normalized = normalize_emlis_current_input(
        {
            "id": "emotion-ulc-current-001",
            "created_at": "2026-06-03T00:00:00+09:00",
            "emotions": ["不安"],
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "memo": "今は公開本文ではなく内部bundle確認用の思考本文",
            "memo_action": "内部bundle確認用の行動本文",
            "category": ["仕事"],
            "is_secret": False,
        }
    )

    assert normalized["id"] == "emotion-ulc-current-001"
    assert normalized["created_at"] == "2026-06-03T00:00:00+09:00"
    assert normalized["emotions"] == ["不安"]
    assert normalized["emotion_details"] == [{"type": "不安", "strength": "strong"}]
    assert normalized["category"] == ["仕事"]
    assert normalized["memo"]
    assert normalized["memo_action"]

    bundle = build_emlis_current_input_bundle(normalized)
    summary = bundle.to_environment_state_output_connection_summary()

    assert summary["axis_presence"]["has_all_single_record_axes"] is True
    assert summary["environment_axis"]["source_fields"] == ["category", "memo_action"]
    assert summary["state_axis"]["source_fields"] == ["emotion_details"]
    assert summary["output_axis"]["source_fields"] == ["memo"]
    assert summary["time_axis"]["selected_at_present"] is True
    assert summary["time_axis"]["source_record_id_present"] is True
    assert summary["time_axis"]["must_not_use_for_period_tendency"] is True
    assert summary["surface_policy"]["public_response_key_added"] is False
    assert summary["surface_policy"]["raw_input_included"] is False
    assert summary["surface_policy"]["raw_text_included"] is False
    assert summary["surface_policy"]["comment_text_included"] is False
    assert summary["surface_policy"]["period_tendency_from_single_record"] is False
    assert summary["surface_policy"]["cause_from_category"] is False
    assert summary["surface_policy"]["cause_from_emotion_strength"] is False
    assert summary["surface_policy"]["personality_tendency_allowed"] is False


def test_user_label_connection_phase1_capability_boundary_keeps_free_current_only_and_subscription_owned_history() -> None:
    free = resolve_emlis_ai_capability_for_tier("free")
    plus = resolve_emlis_ai_capability_for_tier("plus")
    premium = resolve_emlis_ai_capability_for_tier("premium")

    assert free.tier == "free"
    assert free.history_mode == "none"
    assert free.model_read_enabled is False
    assert free.model_write_enabled is False
    assert free.source_scope == "current_input_only"
    assert free.max_same_day_inputs == 0
    assert free.max_similar_inputs == 0

    assert plus.history_mode != "none"
    assert plus.model_read_enabled is True
    assert plus.include_derived_user_model is True
    assert plus.source_scope == "current_input_with_owned_history"
    assert plus.cross_core_enabled is False

    assert premium.history_mode != "none"
    assert premium.model_read_enabled is True
    assert premium.include_derived_user_model is True
    assert premium.source_scope == "current_input_with_owned_history_and_cross_core"
    assert premium.cross_core_enabled is True


def test_user_label_connection_phase1_source_bundle_and_reply_service_connection_points_are_present() -> None:
    source_bundle_fields = {field.name for field in fields(SourceBundle)}
    assert {"current_input", "last_input", "same_day_recent_inputs", "similar_inputs", "derived_user_model"}.issubset(
        source_bundle_fields
    )

    source_bundle_signature = inspect.signature(build_emlis_ai_source_bundle)
    assert set(source_bundle_signature.parameters) >= {
        "user_id",
        "current_input",
        "capability",
        "display_name",
        "timezone_name",
    }

    reply_signature = inspect.signature(render_emlis_ai_reply)
    assert set(reply_signature.parameters) >= {
        "user_id",
        "subscription_tier",
        "current_input",
        "display_name",
        "timezone_name",
        "composer_client",
    }

    reply_source = inspect.getsource(render_emlis_ai_reply)
    assert "resolve_emlis_ai_capability_for_tier" in reply_source
    assert "build_emlis_ai_source_bundle" in reply_source
    assert "normalize_emlis_current_input" in reply_source


def test_user_label_connection_phase1_complete_composer_contract_keeps_public_rn_db_boundaries() -> None:
    meta = build_complete_composer_client_contract_meta()

    assert meta["response_shape_changed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["grounding_gate_relaxed"] is False
    assert meta["reader_gate_relaxed"] is False
    assert meta["raw_input_included"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
