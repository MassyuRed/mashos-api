# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 tests for the normal-observation rebuild candidate builder.

P4 builds the public candidate internally.  The tests keep the boundary narrow:
normal rebuild is allowed only from an existing AI-generated normal candidate,
keeps public meta body-free, and does not substitute for disabled/non-AI
composer paths.
"""

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any
import re

from emlis_ai_gate_recovery_public_candidate_builder import (
    NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
    NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision, SafetyBoundaryReport

_CURRENT_INPUT = {
    "memo": "仕事の話を聞いたあと、納得したい気持ちと引っかかりがどちらも残っている。",
    "memo_action": "明日は一度、事実だけ書き出してから返事を考える。",
    "emotions": ["不安", "違和感", "迷い"],
    "category": ["仕事", "人間関係"],
}

_ORIGINAL_SURFACE = (
    "この入力では、仕事の話に対して同じ流れの中で、納得したい気持ちと"
    "引っかかりが同じ場所に残っています。片方だけに減らさず、状態が"
    "一色ではありません。"
)

_FORBIDDEN_SURFACE_FRAGMENTS = (
    "同じ流れ",
    "同じ場所",
    "別々の向き",
    "片方だけに減らさず",
    "状態が一色ではありません",
    "今回の入力では",
    "原因や結論までは決めず",
    "誰かを良い悪いで決めず",
    "Emlisから：",
    "見えたこと：",
)

_FORBIDDEN_META_KEYS = {
    "raw_input",
    "current_input",
    "memo",
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


def _surface_failed_display_decision(*extra_reasons: str) -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "surface_relation_skeleton_major",
            "surface_grammar_warning",
            *extra_reasons,
        ],
        trace_id="p4-normal-observation-rebuild-builder",
    )


def _original_candidate(*, composer_source: str = "ai_generated", ai_generated: bool = True) -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=_ORIGINAL_SURFACE,
        composer_source=composer_source,
        status="generated",
        ai_generated=ai_generated,
        trace_id="p4-original-normal-observation",
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


def _assert_body_free(meta: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & _FORBIDDEN_META_KEYS)
            for child in value.values():
                walk(child)
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                walk(child)

    walk(meta)


def test_p4_builds_normal_observation_rebuild_candidate_internally() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p4-normal-observation-rebuild-builder",
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result.selection_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE

    candidate = result.candidate
    assert candidate.composer_model == NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
    assert candidate.generation_method == NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD
    assert candidate.comment_text != _ORIGINAL_SURFACE
    assert "この記録では" in candidate.comment_text
    assert _CURRENT_INPUT["memo"] not in candidate.comment_text
    assert _CURRENT_INPUT["memo_action"] not in candidate.comment_text
    assert 2 <= len([part for part in re.split(r"(?<=[。！？!?])\s*", candidate.comment_text) if part.strip()]) <= 3
    for fragment in _FORBIDDEN_SURFACE_FRAGMENTS:
        assert fragment not in candidate.comment_text

    meta = candidate.composer_meta
    assert meta["normal_observation_rebuild_connected"] is True
    assert meta["normal_observation_rebuild_applied"] is True
    assert meta["normal_observation_rebuild_attempt_count"] == 1
    assert meta["normal_observation_rebuild_attempt_limit"] == 1
    assert meta["candidate_lineage"]["diagnostic_surface_used"] is False
    assert meta["candidate_lineage"]["public_candidate_rebuilt_after_recovery"] is True
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["runtime_surface_gate_relaxed"] is False
    assert meta["visible_surface_gate_relaxed"] is False
    _assert_body_free(meta)
    _assert_body_free(result.as_meta())


def test_p4_does_not_rebuild_from_non_ai_generated_original_candidate() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(composer_source="fallback_renderer", ai_generated=False),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p4-normal-observation-rebuild-non-ai-negative",
    )

    assert result.source_kind != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    if result.candidate is not None:
        assert result.candidate.composer_model != NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
        assert result.candidate.generation_method != NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD


def test_p4_does_not_rebuild_when_non_repairable_safety_reason_is_present() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision("safety_blocked"),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p4-normal-observation-rebuild-safety-negative",
    )

    plan = result.as_meta()["recovery_plan"]
    assert result.source_kind != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert "safety" in plan["failed_gate_summary"]["non_repairable_reason_families"]


def test_p4_does_not_rebuild_when_safety_report_requires_block() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=True),
        recovery_plan={},
        trace_id="p4-normal-observation-rebuild-safety-report-negative",
    )

    assert result.source_kind != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    if result.candidate is not None:
        assert result.candidate.composer_model != NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
        assert result.candidate.generation_method != NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD
