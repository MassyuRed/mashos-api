# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

import pytest

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_candidate import build_user_label_connection_candidate_meta
from emlis_ai_user_label_connection_gate import (
    GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN,
    GATE_ACTION_BLOCK_SURFACE_PLAN,
    USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION,
    build_user_label_connection_gate_meta,
)
from emlis_ai_user_label_connection_material import build_user_label_connection_material
from emlis_ai_user_label_connection_surface import (
    CONNECTABLE_FAMILY_LONG_MEANING_ARC,
    CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
    REJECTION_CONNECTABLE_FAMILY_SUPPRESSED,
    REJECTION_GATE_NOT_PASSED,
    SURFACE_PLAN_KIND_BLOCKED,
    SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
    SURFACE_PLAN_KIND_META_ONLY,
    USER_LABEL_CONNECTION_SURFACE_PLAN_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
    assert_user_label_connection_surface_plan_meta_contract,
    assert_user_label_connection_visible_surface_connection_meta_contract,
    build_user_label_connection_limited_visible_comment_text,
    build_user_label_connection_limited_visible_surface_connection,
    build_user_label_connection_surface_plan,
    user_label_connection_surface_plan_public_summary,
    user_label_connection_visible_surface_public_summary,
)

SECRET_SURFACE_BODY = "PHASE6_SECRET_SURFACE_BODY_SHOULD_NOT_LEAK"
SECRET_COMMENT_BODY = "PHASE6_SECRET_COMMENT_BODY_SHOULD_NOT_LEAK"
SECRET_MEMO = "PHASE6_SECRET_MEMO_SHOULD_NOT_LEAK"

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
        "id": "current-phase6-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場でうまく話せなかった",
        "memo": "このまま続けられるかわからない",
    }


def _history_rows() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        {
            "id": "history-phase6-last-001",
            "created_at": "2026-06-02T22:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "会議で言葉に詰まった",
            "memo": "また同じところで止まっている気がする",
        },
        {
            "id": "history-phase6-sameday-001",
            "created_at": "2026-06-03T01:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "焦り", "strength": "weak"}],
            "memo_action": "朝から連絡を返せなかった",
            "memo": "進めたいのに動けない感じがある",
        },
        {
            "id": "history-phase6-similar-001",
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
        user_id="phase6-user",
        display_name="Mash",
        current_input=_current_input(),
        last_input=last_input,
        same_day_recent_inputs=[same_day],
        similar_inputs=[similar],
    )


def _material() -> Any:
    return build_user_label_connection_material(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )


def _candidate_meta() -> dict[str, Any]:
    return build_user_label_connection_candidate_meta(_material())


def _passed_gate_meta() -> dict[str, Any]:
    return build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        proposed_surface="この期間の記録では、今回と近い記録の範囲で、同じ線の上に出ているように見えます。",
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


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@pytest.mark.parametrize(
    "family",
    [
        CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
        CONNECTABLE_FAMILY_LONG_MEANING_ARC,
        CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    ],
)
def test_phase6_builds_limited_surface_plan_for_allowed_connectable_families(family: str) -> None:
    plan = build_user_label_connection_surface_plan(
        _passed_gate_meta(),
        candidate=_candidate_meta(),
        connectable_family=family,
    )

    assert plan["schema_version"] == USER_LABEL_CONNECTION_SURFACE_PLAN_SCHEMA_VERSION
    assert plan["step"] == "UserLabelConnection_SurfacePlan_v1"
    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    assert plan["connectable_family"] == family
    assert set(plan["section_targets"]) == {"observation", "reception"}
    assert set(plan["must_include_roles"]) >= {
        "scope_marker",
        "current_input_anchor",
        "history_line_marker",
        "soft_observation",
        "not_personality_disclaimer",
        "self_understanding_support",
    }
    assert set(plan["must_not_include_roles"]) >= {
        "advice",
        "diagnosis",
        "personality_claim",
        "future_prediction",
        "always_claim",
        "should_statement",
    }
    assert plan["surface_shape"]["current_input_observation"] == "required"
    assert plan["surface_shape"]["history_connection_observation"] == "required_when_history_surface"
    assert plan["surface_shape"]["meaning_support"] == "required"
    assert plan["fixed_sentence_template_added"] is False
    assert plan["comment_text_generated_by_this_layer"] is False
    assert plan["public_response_key_added"] is False
    assert plan["history_connection_surface_plan_allowed"] is True
    assert plan["history_connection_surface_connected"] is False
    assert plan["visible_text_generated"] is False
    assert_user_label_connection_surface_plan_meta_contract(plan)


@pytest.mark.parametrize(
    "family",
    ["daily_unpleasant", "daily_positive", "positive_only", "low_information", "safety_triage_required"],
)
def test_phase6_suppresses_daily_positive_low_information_and_safety_families(family: str) -> None:
    plan = build_user_label_connection_surface_plan(
        _passed_gate_meta(),
        candidate=_candidate_meta(),
        connectable_family=family,
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_BLOCKED
    assert plan["connectable_family"] == ""
    assert plan["history_connection_surface_plan_allowed"] is False
    assert plan["limited_history_line_observation_ready"] is False
    assert REJECTION_CONNECTABLE_FAMILY_SUPPRESSED in plan["surface_plan_rejection_reasons"]
    assert plan["surface_shape"]["history_connection_observation"] == "forbidden"
    assert plan["fixed_sentence_template_added"] is False
    assert plan["comment_text_generated_by_this_layer"] is False
    assert_user_label_connection_surface_plan_meta_contract(plan)


def test_phase6_blocked_gate_does_not_generate_surface_plan() -> None:
    blocked_gate = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("free"),
    )
    assert blocked_gate["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN

    plan = build_user_label_connection_surface_plan(
        blocked_gate,
        candidate=_candidate_meta(),
        connectable_family=CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_BLOCKED
    assert plan["gate_passed"] is False
    assert plan["gate_blocked"] is True
    assert plan["history_connection_surface_plan_allowed"] is False
    assert plan["comment_text_generated_by_this_layer"] is False
    assert plan["public_response_key_added"] is False
    assert_user_label_connection_surface_plan_meta_contract(plan)


def test_phase6_meta_only_gate_stays_meta_only_and_invisible() -> None:
    gate = dict(_passed_gate_meta())
    gate.update(
        {
            "schema_version": USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION,
            "action": "meta_only",
            "passed": False,
            "blocked": False,
            "allow_limited_surface_plan": False,
            "may_surface_after_user_label_connection_gate": False,
        }
    )

    plan = build_user_label_connection_surface_plan(
        gate,
        candidate=_candidate_meta(),
        connectable_family=CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_META_ONLY
    assert plan["history_connection_surface_plan_allowed"] is False
    assert plan["history_connection_surface_connected"] is False
    assert REJECTION_GATE_NOT_PASSED in plan["surface_plan_rejection_reasons"]
    assert plan["visible_text_generated"] is False
    assert_user_label_connection_surface_plan_meta_contract(plan)


def test_phase6_surface_plan_does_not_retain_candidate_or_surface_body_text() -> None:
    candidate = _candidate_meta()
    candidate["safe_note"] = SECRET_MEMO
    gate = _passed_gate_meta()
    gate["safe_surface_probe"] = SECRET_SURFACE_BODY

    plan = build_user_label_connection_surface_plan(
        gate,
        candidate=candidate,
        connectable_family=CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    )
    dumped = _dump(plan)

    assert SECRET_MEMO not in dumped
    assert SECRET_SURFACE_BODY not in dumped
    assert SECRET_COMMENT_BODY not in dumped
    assert not (FORBIDDEN_RAW_KEYS & _all_keys(plan))
    assert plan["raw_input_included"] is False
    assert plan["raw_text_included"] is False
    assert plan["comment_text_body_included"] is False
    assert plan["candidate_body_included"] is False
    assert plan["surface_body_included"] is False
    assert_user_label_connection_surface_plan_meta_contract(plan)


def test_phase6_surface_plan_can_infer_family_from_mechanism_without_fixed_text() -> None:
    plan = build_user_label_connection_surface_plan(
        _passed_gate_meta(),
        candidate=_candidate_meta(),
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    assert plan["connectable_family"] == CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW
    assert plan["fixed_sentence_template_added"] is False
    assert plan["visible_text_generated"] is False
    assert "surface_text" not in _all_keys(plan)
    assert "comment_text" not in _all_keys(plan)
    assert_user_label_connection_surface_plan_meta_contract(plan)


def test_phase6_surface_plan_public_summary_is_safe_identifier_only() -> None:
    plan = build_user_label_connection_surface_plan(
        _passed_gate_meta(),
        candidate=_candidate_meta(),
        connectable_family=CONNECTABLE_FAMILY_LONG_MEANING_ARC,
    )
    summary = user_label_connection_surface_plan_public_summary(plan)

    assert summary["public_meta_summary_only"] is True
    assert summary["schema_version"] == USER_LABEL_CONNECTION_SURFACE_PLAN_SCHEMA_VERSION
    assert summary["surface_plan_kind"] == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    assert summary["connectable_family"] == CONNECTABLE_FAMILY_LONG_MEANING_ARC
    assert summary["history_connection_surface_plan_allowed"] is True
    assert summary["limited_history_line_observation_ready"] is True
    assert summary["raw_text_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["public_response_key_added"] is False
    assert not (FORBIDDEN_RAW_KEYS & _all_keys(summary))


def test_phase6_contract_assertion_blocks_raw_text_or_fixed_sentence_flags() -> None:
    plan = build_user_label_connection_surface_plan(
        _passed_gate_meta(),
        candidate=_candidate_meta(),
        connectable_family=CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
    )

    raw_plan = dict(plan)
    raw_plan["raw_text_included"] = True
    with pytest.raises(ValueError):
        assert_user_label_connection_surface_plan_meta_contract(raw_plan)

    fixed_plan = dict(plan)
    fixed_plan["fixed_sentence_template_added"] = True
    with pytest.raises(ValueError):
        assert_user_label_connection_surface_plan_meta_contract(fixed_plan)



def _phase8_surface_plan(family: str = CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW) -> dict[str, Any]:
    return build_user_label_connection_surface_plan(
        _passed_gate_meta(),
        candidate=_candidate_meta(),
        connectable_family=family,
    )


def _phase8_gate_reports_passed() -> dict[str, dict[str, Any]]:
    return {
        "tone_guard": {"passed": True},
        "grounding": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
    }


def test_phase8_connects_limited_visible_history_line_after_existing_gates_pass() -> None:
    result = build_user_label_connection_limited_visible_surface_connection(
        "今回の入力は、かなり重さのある状態として受け取ります。",
        _phase8_surface_plan(),
        existing_gate_reports=_phase8_gate_reports_passed(),
    )

    assert result.applied is True
    assert "Emlisから見える範囲では" in result.comment_text
    assert "ように見えます" in result.comment_text
    assert "あなたはこういう人" not in result.comment_text
    assert "原因は" not in result.comment_text
    meta = result.as_meta()
    assert meta["phase"] == USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE
    assert meta["history_connection_applied"] is True
    assert meta["visible_surface_connected"] is True
    assert meta["runtime_surface_connected"] is True
    assert meta["comment_text_connected"] is True
    assert meta["scope_marker_present"] is True
    assert meta["soft_marker_present"] is True
    assert meta["public_response_key_added"] is False
    assert meta["raw_text_included"] is False
    assert meta["comment_text_body_included"] is False
    assert_user_label_connection_visible_surface_connection_meta_contract(meta)
    assert not (FORBIDDEN_RAW_KEYS & _all_keys(meta))


def test_phase8_comment_text_helper_returns_connected_body_without_meta_leak() -> None:
    text = build_user_label_connection_limited_visible_comment_text(
        "今の言葉を、まず今の状態として受け取ります。",
        _phase8_surface_plan(CONNECTABLE_FAMILY_LONG_MEANING_ARC),
        existing_gate_reports=_phase8_gate_reports_passed(),
    )

    assert "Emlisから見える範囲では" in text
    assert "自己情報の長い線" in text
    assert SECRET_MEMO not in text


def test_phase8_blocks_visible_connection_when_existing_gate_is_missing_or_failed() -> None:
    missing = build_user_label_connection_limited_visible_surface_connection(
        "既存の観測本文です。",
        _phase8_surface_plan(),
        existing_gate_reports={"tone_guard": {"passed": True}},
    )
    assert missing.applied is False
    assert missing.comment_text == "既存の観測本文です。"
    assert missing.meta["visible_surface_connected"] is False
    assert any("visible_existing_gate_report_missing" in reason for reason in missing.meta["rejection_reasons"])

    failed = build_user_label_connection_limited_visible_surface_connection(
        "既存の観測本文です。",
        _phase8_surface_plan(),
        existing_gate_reports={
            **_phase8_gate_reports_passed(),
            "grounding": {"passed": False, "primary_reason": "grounding_not_passed"},
        },
    )
    assert failed.applied is False
    assert failed.meta["rejection_reasons"] == ["grounding_not_passed"]


def test_phase8_blocks_low_information_safety_and_suppressed_surface_plan() -> None:
    low_info = build_user_label_connection_limited_visible_surface_connection(
        "既存の観測本文です。",
        _phase8_surface_plan(),
        existing_gate_reports=_phase8_gate_reports_passed(),
        safety_context="low_information",
    )
    assert low_info.applied is False
    assert "visible_safety_context_blocked" in low_info.meta["rejection_reasons"]

    suppressed_plan = build_user_label_connection_surface_plan(
        _passed_gate_meta(),
        candidate=_candidate_meta(),
        connectable_family="daily_positive",
    )
    blocked = build_user_label_connection_limited_visible_surface_connection(
        "既存の観測本文です。",
        suppressed_plan,
        existing_gate_reports=_phase8_gate_reports_passed(),
    )
    assert blocked.applied is False
    assert blocked.meta["history_connection_applied"] is False
    assert blocked.meta["visible_surface_connected"] is False


def test_phase8_visible_public_summary_is_safe_identifier_boolean_count_only() -> None:
    result = build_user_label_connection_limited_visible_surface_connection(
        "既存の観測本文です。",
        _phase8_surface_plan(CONNECTABLE_FAMILY_STRUCTURE_QUESTION),
        existing_gate_reports=_phase8_gate_reports_passed(),
    )
    summary = user_label_connection_visible_surface_public_summary(result.as_meta())

    assert summary["public_meta_summary_only"] is True
    assert summary["phase"] == USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE
    assert summary["history_connection_applied"] is True
    assert summary["visible_surface_connected"] is True
    assert summary["comment_text_connected"] is True
    assert summary["scope_marker_present"] is True
    assert summary["soft_marker_present"] is True
    assert summary["raw_text_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["public_response_key_added"] is False
    assert not (FORBIDDEN_RAW_KEYS & _all_keys(summary))
