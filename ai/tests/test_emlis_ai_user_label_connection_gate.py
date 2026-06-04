# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

import pytest

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_candidate import (
    CANDIDATE_QUALITY_GATE_CANDIDATE,
    build_user_label_connection_candidate_meta,
)
from emlis_ai_user_label_connection_gate import (
    GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN,
    GATE_ACTION_BLOCK_SURFACE_PLAN,
    REJECTION_ADVICE_SURFACE,
    REJECTION_ALWAYS_CLAIM_SURFACE,
    REJECTION_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE,
    REJECTION_COMMENT_TEXT_BODY_IN_META_DETECTED,
    REJECTION_CURRENT_INPUT_MISSING,
    REJECTION_DIAGNOSIS_SURFACE,
    REJECTION_FREE_HISTORY_BLOCKED,
    REJECTION_FUTURE_PREDICTION_SURFACE,
    REJECTION_HISTORY_RECORD_COUNT_INSUFFICIENT,
    REJECTION_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED,
    REJECTION_PERSONALITY_CLAIM_SURFACE,
    REJECTION_RAW_TEXT_PAYLOAD_DETECTED,
    REJECTION_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED,
    REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED,
    REJECTION_SHOULD_STATEMENT_SURFACE,
    REJECTION_SOFT_MARKER_MISSING,
    REJECTION_SOURCE_SCOPE_MARKER_MISSING,
    REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED,
    REJECTION_USER_FACT_GROUNDING_BOUNDARY_BLOCKED,
    USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION,
    assert_user_label_connection_gate_meta_contract,
    build_user_label_connection_gate_meta,
)
from emlis_ai_user_label_connection_material import build_user_label_connection_material

SECRET_SURFACE_TEXT = "PHASE5_SECRET_SURFACE_BODY_SHOULD_NOT_LEAK"
SECRET_PUBLIC_MEMO = "PHASE5_SECRET_PUBLIC_MEMO_SHOULD_NOT_LEAK"

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
        "id": "current-phase5-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場でうまく話せなかった",
        "memo": "このまま続けられるかわからない",
    }


def _history_rows() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        {
            "id": "history-phase5-last-001",
            "created_at": "2026-06-02T22:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "会議で言葉に詰まった",
            "memo": "また同じところで止まっている気がする",
        },
        {
            "id": "history-phase5-sameday-001",
            "created_at": "2026-06-03T01:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "焦り", "strength": "weak"}],
            "memo_action": "朝から連絡を返せなかった",
            "memo": "進めたいのに動けない感じがある",
        },
        {
            "id": "history-phase5-similar-001",
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
        user_id="phase5-user",
        display_name="Mash",
        current_input=_current_input(),
        last_input=last_input,
        same_day_recent_inputs=[same_day],
        similar_inputs=[similar],
    )


def _candidate_meta() -> dict[str, Any]:
    material = build_user_label_connection_material(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )
    candidate = build_user_label_connection_candidate_meta(material)
    assert candidate["candidate_quality"] == CANDIDATE_QUALITY_GATE_CANDIDATE
    return candidate


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


def test_phase5_gate_allows_limited_surface_plan_for_plus_candidate_without_public_contract_change() -> None:
    candidate = _candidate_meta()
    meta = build_user_label_connection_gate_meta(
        candidate,
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        proposed_surface="この期間の記録では、今回と近い記録の範囲で、同じ線の上に出ているように見えます。",
    )

    assert meta["schema_version"] == USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION
    assert meta["step"] == "UserLabelConnection_Gate_v1"
    assert meta["action"] == GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN
    assert meta["passed"] is True
    assert meta["blocked"] is False
    assert meta["rejection_reasons"] == []
    assert meta["gate_is_independent_from_structure_insight_gate"] is True
    assert meta["structure_insight_gate_relaxed"] is False

    assert meta["required_surface_markers"] == {
        "scope_marker_required": True,
        "soft_marker_required": True,
        "advice_marker_forbidden": True,
        "future_prediction_forbidden": True,
    }
    assert meta["evidence_contract"]["evidence_record_count"] >= 2
    assert meta["evidence_contract"]["minimum_evidence_record_count"] == 2
    assert meta["evidence_contract"]["current_record_included"] is True
    assert meta["evidence_contract"]["history_record_count"] >= 1
    assert meta["evidence_contract"]["period_tendency_from_single_record_allowed"] is False

    assert meta["capability_contract"] == {
        "tier": "plus",
        "free_history_used": False,
        "owned_history_only": True,
        "user_fact_grounding_boundary_passed": True,
    }
    for key, value in meta["public_contract"].items():
        assert value is False, key
    for key, value in meta["claim_contract"].items():
        assert value is False, key
    assert meta["comment_text_generated"] is False
    assert meta["surface_plan_generated"] is False
    assert meta["public_response_key_added"] is False
    assert_user_label_connection_gate_meta_contract(meta)


def test_phase5_gate_meta_does_not_retain_proposed_surface_body_or_raw_payload_keys() -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        proposed_surface=f"この期間の記録では、{SECRET_SURFACE_TEXT} の近くにあるように見えます。",
    )
    dumped = _dump(meta)

    assert SECRET_SURFACE_TEXT not in dumped
    assert not (FORBIDDEN_RAW_KEYS & _all_keys(meta))
    assert meta["raw_input_included"] is False
    assert meta["raw_text_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["candidate_body_included"] is False
    assert meta["surface_body_included"] is False


def test_phase5_free_tier_blocks_history_candidate_without_using_history() -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("free"),
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert meta["passed"] is False
    assert meta["blocked"] is True
    assert REJECTION_FREE_HISTORY_BLOCKED in meta["rejection_reasons"]
    assert meta["capability_contract"]["tier"] == "free"
    assert meta["capability_contract"]["free_history_used"] is False


def test_phase5_grounding_boundary_violation_blocks_history_candidate() -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        user_fact_grounding_boundary_passed=False,
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert REJECTION_USER_FACT_GROUNDING_BOUNDARY_BLOCKED in meta["rejection_reasons"]
    assert meta["capability_contract"]["user_fact_grounding_boundary_passed"] is False


def test_phase5_low_information_does_not_promote_to_history_surface_with_history_only() -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        observation_reply_meta={"observation_reply_kind": "low_information", "eligible_for_full_observation": False},
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert REJECTION_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED in meta["rejection_reasons"]


def test_phase5_evidence_record_count_less_than_two_blocks_recurrence_claim() -> None:
    candidate = _candidate_meta()
    candidate["candidate_quality"] = "insufficient_evidence"
    candidate["evidence"] = {
        **candidate["evidence"],
        "evidence_record_count": 1,
        "history_record_count": 0,
        "current_record_included": True,
    }

    meta = build_user_label_connection_gate_meta(
        candidate,
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert REJECTION_HISTORY_RECORD_COUNT_INSUFFICIENT in meta["rejection_reasons"]
    assert meta["evidence_contract"]["evidence_record_count"] == 1
    assert meta["evidence_contract"]["period_tendency_from_single_record_allowed"] is False


def test_phase5_current_input_missing_blocks_history_only_candidate() -> None:
    candidate = _candidate_meta()
    candidate["candidate_quality"] = "blocked"
    candidate["evidence"] = {
        **candidate["evidence"],
        "evidence_record_count": 2,
        "history_record_count": 2,
        "current_record_included": False,
    }

    meta = build_user_label_connection_gate_meta(
        candidate,
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert REJECTION_CURRENT_INPUT_MISSING in meta["rejection_reasons"]


def test_phase5_scope_marker_missing_and_soft_marker_missing_are_blocked() -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        proposed_surface="今回の記録では、同じ線の上に出ています。",
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert REJECTION_SOURCE_SCOPE_MARKER_MISSING in meta["rejection_reasons"]
    assert REJECTION_SOFT_MARKER_MISSING in meta["rejection_reasons"]


@pytest.mark.parametrize(
    ("surface", "reason"),
    [
        ("この期間の記録では、あなたはいつも同じ反応をしているように見えます。", REJECTION_ALWAYS_CLAIM_SURFACE),
        ("この期間の記録では、原因はあなた側にあるように見えます。", REJECTION_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE),
        ("この期間の記録では、性格として出ているように見えます。", REJECTION_PERSONALITY_CLAIM_SURFACE),
        ("この期間の記録では、診断すると不安のように見えます。", REJECTION_DIAGNOSIS_SURFACE),
        ("この期間の記録では、休むべき状態のように見えます。", REJECTION_SHOULD_STATEMENT_SURFACE),
        ("この期間の記録では、休んでくださいという方向のように見えます。", REJECTION_ADVICE_SURFACE),
        ("この期間の記録では、今後も同じ形になるように見えます。", REJECTION_FUTURE_PREDICTION_SURFACE),
    ],
)
def test_phase5_forbidden_surface_claims_are_blocked(surface: str, reason: str) -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        proposed_surface=surface,
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert reason in meta["rejection_reasons"]


def test_phase5_raw_text_key_and_comment_text_body_meta_are_blocked_but_not_returned() -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        public_meta={"memo": SECRET_PUBLIC_MEMO, "comment_text_body_included": True},
    )
    dumped = _dump(meta)

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert REJECTION_RAW_TEXT_PAYLOAD_DETECTED in meta["rejection_reasons"]
    assert REJECTION_COMMENT_TEXT_BODY_IN_META_DETECTED in meta["rejection_reasons"]
    assert SECRET_PUBLIC_MEMO not in dumped
    assert not (FORBIDDEN_RAW_KEYS & _all_keys(meta))


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"safety_adjacent": True}, REJECTION_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED),
        ({"self_denial_context": True}, REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED),
        ({"target_judgement_context": True}, REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED),
    ],
)
def test_phase5_safety_self_denial_and_target_judgement_contexts_block_normal_history_surface(
    kwargs: dict[str, object],
    reason: str,
) -> None:
    meta = build_user_label_connection_gate_meta(
        _candidate_meta(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        **kwargs,
    )

    assert meta["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert reason in meta["rejection_reasons"]
