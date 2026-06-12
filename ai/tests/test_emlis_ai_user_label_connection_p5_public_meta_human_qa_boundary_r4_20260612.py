# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pytest

from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_user_label_connection_public_meta import USER_LABEL_CONNECTION_META_ONLY_META_KEY
from test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612 import _install_p5_runtime_history_context

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLY_SERVICE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
PUBLIC_META_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_public_feedback_meta.py"

R4_REPLY_SERVICE_TOKENS = {
    "P5_RuntimeBridge_Repair_R4_20260612",
    "P5_RuntimeBridge_Repair_R3_20260612",
    "P5_RuntimeBridge_PublicMetaHumanQABoundary_R4_20260612",
    "runtime_evaluation_layer",
    "visible_application_layer",
    "product_quality_confirmation_layer",
    "product_quality_confirmation_status",
    "human_qa_required",
    "human_qa_completed",
    "human_qa_pending",
    "p5_hold_001_human_qa_unconfirmed",
    "runtime_evaluated_is_not_product_quality_confirmed",
    "visible_applied_is_not_product_quality_confirmed",
    "actual_appended_line_included",
}

R4_PUBLIC_META_TOKENS = {
    "_build_p5_runtime_bridge_public_summary",
    "_pick_p5_runtime_bridge_source",
    "p5_runtime_bridge",
    "human_qa_pending",
    "p5_hold_001_human_qa_unconfirmed",
    "comment_text_body_included",
    "reviewer_free_text_included",
}

FORBIDDEN_PUBLIC_BODY_KEYS = {
    "raw_input",
    "raw_text",
    "history_raw_text",
    "comment_text",
    "commentText",
    "comment_text_body",
    "candidate_body",
    "surface_body",
    "reviewer_free_text",
    "actual_appended_line",
}


def _missing_tokens(text: str, tokens: Iterable[str]) -> list[str]:
    return sorted(token for token in tokens if token not in text)


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for item in value:
            keys.update(_walk_keys(item))
    return keys


def _meta_only_source() -> dict[str, Any]:
    return {
        "schema_version": "cocolon.emlis.user_label_connection.meta_only_integration.v1",
        "phase": "Phase7_MetaOnlyIntegration",
        "evaluated": True,
        "meta_only_connected": True,
        "reply_flow_meta_only_connected": True,
        "history_connection_candidate_present": True,
        "history_connection_blocked": True,
        "history_connection_applied": False,
        "history_connection_edge_family_count": 1,
        "history_connection_evidence_record_count": 2,
        "scope_marker_required": True,
        "soft_marker_required": True,
        "gate_passed": False,
        "gate_action": "hold",
        "surface_plan_kind": "limited_history_line_observation",
        "limited_history_line_observation_ready": True,
        "rejection_reasons": ["ratings_only_review_rows_missing"],
        "raw_text_included": False,
        "history_raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
    }


def _p5_runtime_bridge_source(**overrides: Any) -> dict[str, Any]:
    source = {
        "schema_version": "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1",
        "step": "P5_RuntimeBridge_Repair_R4_20260612",
        "runtime_evaluated": True,
        "visible_applied": False,
        "product_quality_confirmed": False,
        "product_quality_confirmation_status": "human_qa_pending",
        "product_quality_confirmation_source": "none",
        "human_qa_status": "pending",
        "human_qa_required": True,
        "human_qa_completed": False,
        "human_qa_pending": True,
        "p5_hold_001_human_qa_unconfirmed": True,
        "runtime_evaluated_is_not_product_quality_confirmed": True,
        "visible_applied_is_not_product_quality_confirmed": False,
        "human_qa_hold_reason_codes": ["P5-HOLD-001", "p5_human_blind_qa_unconfirmed"],
        "blocked_reason_codes": ["ratings_only_review_rows_missing"],
        "comment_text_owner": "input_feedback.comment_text",
        "release_allowed": False,
        "public_contract": {
            "public_response_key_added": False,
            "rn_visible_contract_changed": False,
            "api_route_changed": False,
            "db_schema_changed": False,
            "release_allowed": False,
        },
        "body_free": {
            "raw_input_included": False,
            "raw_text_included": False,
            "history_raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "reviewer_free_text_included": False,
            "actual_appended_line_included": False,
        },
        # These payload-shaped keys are intentionally injected to prove R4 copies
        # only safe identifiers/booleans into public meta.
        "comment_text": "これはpublic metaへ出してはいけない本文です。",
        "raw_input": "これもpublic metaへ出してはいけない入力本文です。",
        "reviewer_free_text": "レビュー自由記述は出さない。",
    }
    source.update(overrides)
    return source


def test_r4_static_contract_tokens_are_present_without_removing_r3_boundary() -> None:
    reply_source = REPLY_SERVICE_PATH.read_text(encoding="utf-8")
    public_meta_source = PUBLIC_META_PATH.read_text(encoding="utf-8")

    assert _missing_tokens(reply_source, R4_REPLY_SERVICE_TOKENS) == []
    assert _missing_tokens(public_meta_source, R4_PUBLIC_META_TOKENS) == []
    assert "P5_RuntimeBridge_Repair_R3_20260612" in reply_source
    assert "build_user_label_connection_limited_visible_surface_connection" not in reply_source


def test_r4_public_meta_keeps_p5_summary_under_existing_user_label_connection_key_and_body_free() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "observation_status": "passed",
            USER_LABEL_CONNECTION_META_ONLY_META_KEY: _meta_only_source(),
            "user_label_connection_p5_runtime_bridge": _p5_runtime_bridge_source(),
        },
        comment_text_present=True,
        subscription_tier="plus",
    )

    assert "user_label_connection_p5_runtime_bridge" not in public_meta
    assert "p5_runtime_bridge" not in public_meta
    user_label_connection = public_meta.get("user_label_connection")
    assert isinstance(user_label_connection, dict)
    p5_public = user_label_connection.get("p5_runtime_bridge")
    assert isinstance(p5_public, dict)

    assert p5_public["schema_version"] == "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1"
    assert p5_public["runtime_evaluated"] is True
    assert p5_public["visible_applied"] is False
    assert p5_public["product_quality_confirmed"] is False
    assert p5_public["human_qa_status"] == "pending"
    assert p5_public["human_qa_required"] is True
    assert p5_public["human_qa_completed"] is False
    assert p5_public["human_qa_pending"] is True
    assert p5_public["p5_hold_001_human_qa_unconfirmed"] is True
    assert p5_public["release_allowed"] is False
    assert p5_public["public_response_key_added"] is False
    assert p5_public["comment_text_body_included"] is False
    assert p5_public["reviewer_free_text_included"] is False

    serialized = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    keys = _walk_keys(public_meta)
    assert not (keys & FORBIDDEN_PUBLIC_BODY_KEYS)
    assert "これはpublic metaへ出してはいけない本文" not in serialized
    assert "これもpublic metaへ出してはいけない入力本文" not in serialized
    assert "レビュー自由記述" not in serialized


@pytest.mark.asyncio
async def test_r4_actual_reply_separates_runtime_evaluated_from_human_qa_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_p5_runtime_history_context(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="p5-runtime-r4-human-qa-user",
        subscription_tier="plus",
        current_input={
            "id": "p5-runtime-r4-current-001",
            "created_at": "2026-06-12T00:00:00Z",
            "memo": "また仕事の判断で言い切れなくなっている。前も同じところで詰まった気がする。",
            "memo_action": "考え込んでいる。",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "emotions": ["不安"],
            "category": ["仕事"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    p5_runtime_bridge = reply.meta.get("user_label_connection_p5_runtime_bridge") or reply.meta.get("p5_runtime_bridge")
    assert isinstance(p5_runtime_bridge, dict)
    assert p5_runtime_bridge["step"] == "P5_RuntimeBridge_Repair_R4_20260612"
    assert p5_runtime_bridge["previous_step"] == "P5_RuntimeBridge_Repair_R3_20260612"
    assert p5_runtime_bridge["runtime_evaluated"] is True
    assert p5_runtime_bridge["product_quality_confirmed"] is False
    assert p5_runtime_bridge["product_quality_confirmation_status"] == "human_qa_pending"
    assert p5_runtime_bridge["human_qa_required"] is True
    assert p5_runtime_bridge["human_qa_completed"] is False
    assert p5_runtime_bridge["human_qa_pending"] is True
    assert p5_runtime_bridge["p5_hold_001_human_qa_unconfirmed"] is True
    assert p5_runtime_bridge["runtime_evaluated_is_not_product_quality_confirmed"] is True
    assert p5_runtime_bridge["product_quality_confirmation_layer"]["human_qa_status"] == "pending"
    assert p5_runtime_bridge["product_quality_confirmation_layer"]["review_count"] == 0
    assert "P5-HOLD-001" in p5_runtime_bridge["human_qa_hold_reason_codes"]
    assert p5_runtime_bridge["body_free"]["comment_text_body_included"] is False
    assert p5_runtime_bridge["body_free"]["actual_appended_line_included"] is False
    assert p5_runtime_bridge["public_contract"]["public_response_key_added"] is False
    assert p5_runtime_bridge["release_allowed"] is False


def test_r4_human_qa_confirmed_source_is_still_not_release_or_response_shape_change() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "observation_status": "passed",
            USER_LABEL_CONNECTION_META_ONLY_META_KEY: _meta_only_source(),
            "diagnostic_summary": {
                "user_label_connection_p5_runtime_bridge": _p5_runtime_bridge_source(
                    product_quality_confirmed=True,
                    p5_product_quality_confirmed=True,
                    product_quality_confirmation_status="confirmed",
                    product_quality_confirmation_source="human_blind_qa_ratings",
                    human_qa_status="confirmed",
                    human_qa_completed=True,
                    human_qa_pending=False,
                    p5_hold_001_human_qa_unconfirmed=False,
                    runtime_evaluated_is_not_product_quality_confirmed=False,
                    human_qa_hold_reason_codes=[],
                    blocked_reason_codes=[],
                )
            },
        },
        comment_text_present=True,
        subscription_tier="plus",
    )

    p5_public = public_meta["user_label_connection"]["p5_runtime_bridge"]
    assert p5_public["product_quality_confirmed"] is True
    assert p5_public["human_qa_status"] == "confirmed"
    assert p5_public["human_qa_pending"] is False
    assert p5_public["p5_hold_001_human_qa_unconfirmed"] is False
    assert p5_public["release_allowed"] is False
    assert p5_public["public_response_key_added"] is False
    assert p5_public["response_shape_changed"] is False
    assert p5_public["comment_text_body_included"] is False
