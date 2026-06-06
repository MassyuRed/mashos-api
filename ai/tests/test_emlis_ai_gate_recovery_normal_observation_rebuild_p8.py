# -*- coding: utf-8 -*-
from __future__ import annotations

"""P8 regression tests for normal observation public rebuild.

This file started as the P0 red reproduction for high-information normal
observation failures.  P8 keeps that path green: surface_grammar /
relation_skeleton failures must rebuild through normal_observation_rebuild_candidate
without relaxing RN/API/Gate contracts or promoting Gate Recovery material text.
"""

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

from emlis_ai_gate_recovery_public_candidate_builder import (
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    BLOCKER_NORMAL_OBSERVATION_REBUILD_CANDIDATE_MISSING,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision, SafetyBoundaryReport

_CURRENT_INPUT = {
    "memo": "仕事の話を聞いたあと、納得したい気持ちと引っかかりがどちらも残っている。",
    "memo_action": "明日は一度、事実だけ書き出してから返事を考える。",
    "emotions": ["不安", "違和感", "迷い"],
    "category": ["仕事", "人間関係"],
}

_RELATION_SKELETON_ORIGINAL_TEXT = (
    "この入力では、仕事の話に対して同じ流れの中で、納得したい気持ちと"
    "引っかかりが同じ場所に残っています。片方だけに減らさず、状態が"
    "一色ではありません。"
)

_FORBIDDEN_REBUILD_SURFACE_FRAGMENTS = (
    "同じ流れ",
    "同じ場所",
    "片方だけに減らさず",
    "状態が一色ではありません",
    "原因や結論までは決めず",
    "誰かを良い悪いで決めず",
    "Emlisから：",
    "見えたこと：",
)


def _material_route() -> SimpleNamespace:
    return SimpleNamespace(
        material_quality="eligible",
        visible_material_slots=("event", "emotion_direction", "action", "relationship"),
        unknown_slots=("cause",),
        relation_material_ids=("work_relationship_state_answer",),
        generic_relation_material_ids=("work_relationship_state_answer",),
        as_meta=lambda: {
            "material_quality": "eligible",
            "visible_material_slots": ["event", "emotion_direction", "action", "relationship"],
            "unknown_slots": ["cause"],
            "relation_material_ids": ["work_relationship_state_answer"],
            "generic_relation_material_ids": ["work_relationship_state_answer"],
            "safety_triage_kind": "safe_observation",
        },
    )


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "surface_relation_skeleton_major",
            "surface_grammar_warning",
            "candidate_blocked_before_display_gate",
        ],
        trace_id="p0-normal-observation-rebuild-red",
    )


def _original_ai_generated_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=_RELATION_SKELETON_ORIGINAL_TEXT,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p0-normal-observation-original",
        attempt_count=1,
        confidence=0.83,
        rejection_reasons=[],
        request_schema_version="emlis.composer.request.v1",
        response_schema_version="cocolon.emlis.complete_composer.response.v1",
        fixed_string_renderer_used=False,
        composer_model="complete_initial_composer_v1",
        generation_method="complete_initial_composer",
        coverage_scope="current_input_only",
        generation_scope="current_input_only",
        composer_meta={
            "candidate_source_kind": "complete_initial_composer",
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_lineage": {
                "original_candidate_present": False,
                "original_candidate_source": "complete_initial_composer",
                "recovery_plan_used": False,
                "diagnostic_surface_used": False,
                "public_candidate_rebuilt_after_recovery": False,
            },
        },
        used_claim_ids=["claim_work_aftertalk_state", "claim_reply_action"],
        used_relation_ids=["work_relationship_state_answer"],
    )


def _assert_meta_body_free(meta: Mapping[str, Any]) -> None:
    text_keys = {
        "raw_input",
        "current_input",
        "memo",
        "memo_text",
        "memo_action",
        "comment_text",
        "commentText",
        "candidate_comment_text",
        "public_comment_text",
        "body",
        "text",
        "candidate_body",
        "surface_body",
    }

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & text_keys)
            for item in value.values():
                walk(item)
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                walk(item)

    walk(meta)


def test_p1_normal_observation_rebuild_source_kind_is_declared_but_not_forbidden() -> None:
    assert (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        == "normal_observation_rebuild_candidate"
    )
    assert BLOCKER_NORMAL_OBSERVATION_REBUILD_CANDIDATE_MISSING == (
        "normal_observation_rebuild_candidate_missing"
    )
    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE in (
        ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS
    )
    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE not in (
        FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS
    )


def test_p8_normal_observation_surface_failure_rebuilds_public_candidate_before_bounded_original() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_ai_generated_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p0-normal-observation-rebuild-red",
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result.selection_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result.blocked_reasons == ()

    candidate = result.candidate
    assert candidate.composer_source == "ai_generated"
    assert candidate.composer_model == "normal_observation_rebuild_candidate_v1"
    assert candidate.generation_method == "normal_observation_rebuild_after_surface_gate_failure"
    assert candidate.comment_text.strip()
    assert candidate.comment_text != _RELATION_SKELETON_ORIGINAL_TEXT
    for fragment in _FORBIDDEN_REBUILD_SURFACE_FRAGMENTS:
        assert fragment not in candidate.comment_text
    assert _CURRENT_INPUT["memo"] not in candidate.comment_text

    candidate_meta = candidate.composer_meta
    assert candidate_meta["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert candidate_meta["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert candidate_meta["candidate_lineage"]["original_candidate_present"] is True
    assert candidate_meta["candidate_lineage"]["diagnostic_surface_used"] is False
    assert candidate_meta["candidate_lineage"]["public_candidate_rebuilt_after_recovery"] is True
    assert candidate_meta["raw_input_included"] is False
    assert candidate_meta["comment_text_body_included"] is False
    _assert_meta_body_free(candidate_meta)

    result_meta = result.as_meta()
    assert result_meta["candidate_available"] is True
    assert result_meta["source_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result_meta["selection_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result_meta["recovery_plan"]["target_public_candidate_source"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert set(result_meta["recovery_plan"]["failed_gate_summary"]["reason_families"]) >= {
        "relation_skeleton",
        "surface_grammar",
        "visible_surface",
    }
    assert result_meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    assert result_meta["contract_flags"]["raw_input_included"] is False
    assert result_meta["contract_flags"]["comment_text_body_included"] is False
    _assert_meta_body_free(result_meta)
