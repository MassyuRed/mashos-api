# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta, should_include_public_input_feedback
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_public_meta import (
    USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_META_ONLY_META_KEY,
    USER_LABEL_CONNECTION_PUBLIC_META_KEY,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY,
    assert_user_label_connection_meta_only_integration_contract,
    attach_user_label_connection_meta_only_integration,
    build_user_label_connection_meta_only_integration,
    user_label_connection_public_summary,
)
from emlis_ai_user_label_connection_surface import (
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
    build_user_label_connection_limited_visible_surface_connection,
)

SECRET_CURRENT_MEMO = "PHASE7_SECRET_CURRENT_MEMO_SHOULD_NOT_LEAK"
SECRET_CURRENT_ACTION = "PHASE7_SECRET_CURRENT_ACTION_SHOULD_NOT_LEAK"
SECRET_HISTORY_MEMO = "PHASE7_SECRET_HISTORY_MEMO_SHOULD_NOT_LEAK"
SECRET_HISTORY_ACTION = "PHASE7_SECRET_HISTORY_ACTION_SHOULD_NOT_LEAK"
SECRET_COMMENT_BODY = "PHASE7_SECRET_COMMENT_BODY_SHOULD_NOT_LEAK"

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
        "id": "phase7-current-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": SECRET_CURRENT_ACTION,
        "memo": SECRET_CURRENT_MEMO,
        "comment_text": SECRET_COMMENT_BODY,
    }


def _history() -> dict[str, object]:
    return {
        "id": "phase7-history-001",
        "created_at": "2026-06-02T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "memo_action": SECRET_HISTORY_ACTION,
        "memo": SECRET_HISTORY_MEMO,
        "comment_text": SECRET_COMMENT_BODY,
    }


def _source_bundle_with_history() -> SourceBundle:
    history = _history()
    return SourceBundle(
        user_id="phase7-user",
        display_name="Mash",
        current_input=_current_input(),
        last_input=history,
        same_day_recent_inputs=[history],
        similar_inputs=[history],
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


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_secret_or_raw_payload(value: Any) -> None:
    dumped = _dump(value)
    assert FORBIDDEN_RAW_KEYS.isdisjoint(_all_keys(value))
    for secret in (
        SECRET_CURRENT_MEMO,
        SECRET_CURRENT_ACTION,
        SECRET_HISTORY_MEMO,
        SECRET_HISTORY_ACTION,
        SECRET_COMMENT_BODY,
    ):
        assert secret not in dumped


def test_phase7_builds_meta_only_integration_summary_without_visible_text_connection() -> None:
    meta = build_user_label_connection_meta_only_integration(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        observation_reply_meta={"coverage_group": "self_understanding_follow"},
    )

    assert meta["schema_version"] == USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_SCHEMA_VERSION
    assert meta["step"] == "UserLabelConnection_MetaOnlyIntegration_v1"
    assert meta["phase"] == "Phase7_MetaOnlyIntegration"
    assert meta["meta_only_connected"] is True
    assert meta["history_connection_candidate_present"] is True
    assert meta["history_connection_edge_family_count"] >= 1
    assert meta["history_connection_evidence_record_count"] >= 2
    assert meta["scope_marker_required"] is True
    assert meta["soft_marker_required"] is True
    assert meta["history_connection_applied"] is False
    assert meta["comment_text_connected"] is False
    assert meta["visible_surface_connected"] is False
    assert meta["public_response_key_added"] is False
    assert meta["raw_text_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["material_summary"]["history_read_allowed"] is True
    assert meta["candidate_summary"]["candidate_body_included"] is False
    assert meta["gate_summary"]["public_meta_summary_only"] is True
    assert meta["surface_plan_summary"]["public_meta_summary_only"] is True
    assert_user_label_connection_meta_only_integration_contract(meta)
    _assert_no_secret_or_raw_payload(meta)


def test_phase7_attach_adds_reply_meta_only_and_public_sanitizer_returns_safe_summary() -> None:
    internal_meta = {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "plus",
        "observation_status": "passed",
        "diagnostic_summary": {},
        "phase_gate": {},
    }
    attached = attach_user_label_connection_meta_only_integration(
        internal_meta,
        current_input=_current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        subscription_tier="plus",
        observation_reply_meta={"coverage_group": "self_understanding_follow"},
    )

    assert USER_LABEL_CONNECTION_META_ONLY_META_KEY in attached
    assert attached[USER_LABEL_CONNECTION_META_ONLY_META_KEY]["reply_flow_meta_only_connected"] is True
    assert attached["phase_gate"]["phase7_user_label_connection_reply_flow_meta_only_connected"] is True
    assert attached["phase_gate"]["phase7_user_label_connection_comment_text_connected"] is False
    assert attached["phase_gate"]["phase7_user_label_connection_visible_surface_connected"] is False

    public_meta = build_public_emlis_input_feedback_meta(attached, comment_text_present=True, subscription_tier="plus")
    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback("public Emlis observation body", public_meta) is True
    public_summary = public_meta[USER_LABEL_CONNECTION_PUBLIC_META_KEY]
    assert public_summary["public_meta_summary_only"] is True
    assert public_summary["meta_only_connected"] is True
    assert public_summary["reply_flow_meta_only_connected"] is True
    assert public_summary["history_connection_candidate_present"] is True
    assert public_summary["history_connection_applied"] is False
    assert public_summary["comment_text_connected"] is False
    assert public_summary["visible_surface_connected"] is False
    assert public_summary["raw_text_included"] is False
    assert public_summary["comment_text_body_included"] is False
    assert public_summary["public_response_key_added"] is False
    _assert_no_secret_or_raw_payload(attached[USER_LABEL_CONNECTION_META_ONLY_META_KEY])
    _assert_no_secret_or_raw_payload(public_summary)


def test_phase7_free_tier_keeps_current_input_only_and_blocks_history_connection() -> None:
    meta = build_user_label_connection_meta_only_integration(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("free"),
        subscription_tier="free",
    )

    assert meta["capability_tier"] == "free"
    assert meta["source_scope"] == "current_input_only"
    assert meta["history_read_allowed"] is False
    assert meta["history_connection_candidate_present"] is False
    assert meta["history_connection_blocked"] is True
    assert meta["history_connection_applied"] is False
    assert meta["comment_text_connected"] is False
    assert meta["visible_surface_connected"] is False
    assert meta["public_response_key_added"] is False
    assert_user_label_connection_meta_only_integration_contract(meta)


def test_phase7_public_summary_fails_closed_if_raw_payload_key_is_injected() -> None:
    summary = user_label_connection_public_summary(
        {
            "schema_version": USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_SCHEMA_VERSION,
            "step": "UserLabelConnection_MetaOnlyIntegration_v1",
            "meta_only_connected": True,
            "memo": SECRET_CURRENT_MEMO,
        }
    )

    assert summary["blocked"] is True
    assert summary["history_connection_blocked"] is True
    assert summary["raw_text_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["public_response_key_added"] is False
    assert SECRET_CURRENT_MEMO not in _dump(summary)



def _phase8_gate_reports_passed() -> dict[str, dict[str, bool]]:
    return {
        "tone_guard": {"passed": True},
        "grounding": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
    }


def test_phase8_public_sanitizer_reports_limited_visible_connection_without_new_response_key() -> None:
    meta_only = build_user_label_connection_meta_only_integration(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        subscription_tier="plus",
        observation_reply_meta={"coverage_group": "self_understanding_follow"},
        reply_flow_meta_only_connected=True,
    )
    visible = build_user_label_connection_limited_visible_surface_connection(
        "既存のEmlis観測本文です。",
        meta_only["surface_plan_meta"],
        existing_gate_reports=_phase8_gate_reports_passed(),
    )
    assert visible.applied is True

    internal_meta = {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "plus",
        "observation_status": "passed",
        USER_LABEL_CONNECTION_META_ONLY_META_KEY: {
            **meta_only,
            USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY: visible.as_meta(),
        },
        USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY: visible.as_meta(),
        "diagnostic_summary": {},
        "phase_gate": {},
    }
    public_meta = build_public_emlis_input_feedback_meta(internal_meta, comment_text_present=True, subscription_tier="plus")
    summary = public_meta[USER_LABEL_CONNECTION_PUBLIC_META_KEY]

    assert summary["phase"] == USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE
    assert summary["history_connection_applied"] is True
    assert summary["limited_visible_surface_connection_applied"] is True
    assert summary["visible_surface_connected"] is True
    assert summary["runtime_surface_connected"] is True
    assert summary["comment_text_connected"] is True
    assert summary["scope_marker_present"] is True
    assert summary["soft_marker_present"] is True
    assert summary["raw_text_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["public_response_key_added"] is False
    assert USER_LABEL_CONNECTION_PUBLIC_META_KEY in public_meta
    assert "user_label_connection_visible_surface" not in public_meta
    _assert_no_secret_or_raw_payload(summary)


def test_phase8_user_label_public_summary_accepts_visible_meta_directly() -> None:
    meta_only = build_user_label_connection_meta_only_integration(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        subscription_tier="plus",
        observation_reply_meta={"coverage_group": "self_understanding_follow"},
        reply_flow_meta_only_connected=True,
    )
    visible = build_user_label_connection_limited_visible_surface_connection(
        "既存のEmlis観測本文です。",
        meta_only["surface_plan_meta"],
        existing_gate_reports=_phase8_gate_reports_passed(),
    )

    summary = user_label_connection_public_summary(visible.as_meta())

    assert summary["history_connection_applied"] is True
    assert summary["visible_surface_connected"] is True
    assert summary["comment_text_connected"] is True
    assert summary["raw_text_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["public_response_key_added"] is False
    _assert_no_secret_or_raw_payload(summary)
