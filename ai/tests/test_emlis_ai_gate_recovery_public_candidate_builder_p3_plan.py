# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 tests for normal-observation rebuild recovery-plan selection.

P3 does not implement the normal-observation rebuild text builder.  It only
extends the public candidate builder so that surface-gate failures target the
new public source kind first, keep the recovery plan body-free, and select an
already-built normal rebuild candidate before bounded-original fallback.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_gate_recovery_public_candidate_builder import (
    NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
    NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_NORMAL_OBSERVATION_REBUILD_CANDIDATE_MISSING,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
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


def _material_route() -> dict[str, Any]:
    return {
        "material_quality": "eligible",
        "visible_material_slots": ["event", "emotion_direction", "action", "relationship"],
        "unknown_slots": ["cause"],
        "relation_material_ids": ["work_relationship_state_answer"],
        "generic_relation_material_ids": ["work_relationship_state_answer"],
    }


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "surface_relation_skeleton_major",
            "surface_grammar_warning",
        ],
        trace_id="p3-normal-observation-rebuild-plan",
    )


def _safety_blocked_surface_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "surface_grammar_warning",
            "safety_blocked",
        ],
        trace_id="p3-normal-observation-nonrepairable-plan",
    )


def _original_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=(
            "この入力では、仕事の話に対して同じ流れの中で、納得したい気持ちと"
            "引っかかりが同じ場所に残っています。片方だけに減らさず、状態が"
            "一色ではありません。"
        ),
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p3-original-candidate",
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
        },
        used_claim_ids=["claim_work_aftertalk_state", "claim_reply_action"],
        used_relation_ids=["work_relationship_state_answer"],
    )


def _normal_rebuild_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=(
            "この記録では、仕事の話を受け取ったあとも、納得したい気持ちと引っかかりが"
            "まだ落ち着ききっていない状態として見えます。返事を急がず、事実を分けて"
            "見ようとしているところもEmlisは受け取りました。"
        ),
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p3-normal-rebuild-candidate",
        attempt_count=1,
        confidence=0.78,
        rejection_reasons=[],
        request_schema_version="emlis.composer.request.v1",
        response_schema_version="cocolon.emlis.phase20_8.normal_observation_rebuild.response.v1",
        fixed_string_renderer_used=False,
        composer_model=NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
        generation_method=NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
        coverage_scope="current_input_normal_observation_rebuild",
        generation_scope="current_input_only",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_lineage": {
                "original_candidate_present": True,
                "original_candidate_source": "complete_initial_composer",
                "recovery_plan_used": True,
                "diagnostic_surface_used": False,
                "public_candidate_rebuilt_after_recovery": True,
            },
        },
        used_claim_ids=["claim_work_aftertalk_state", "claim_reply_action"],
        used_relation_ids=["work_relationship_state_answer"],
    )


def _assert_body_free(meta: Mapping[str, Any]) -> None:
    forbidden = {
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

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & forbidden)
            for child in value.values():
                walk(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                walk(child)

    walk(meta)


def test_p3_default_recovery_plan_targets_normal_observation_rebuild_for_surface_failure() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p3-normal-observation-rebuild-plan",
    )

    plan = result.as_meta()["recovery_plan"]
    failed_summary = plan["failed_gate_summary"]
    assert plan["target_public_candidate_source"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert BLOCKER_NORMAL_OBSERVATION_REBUILD_CANDIDATE_MISSING in plan[
        "blockers_if_no_public_candidate"
    ]
    assert list(failed_summary["reason_families"]) == [
        "surface_grammar",
        "relation_skeleton",
        "visible_surface",
    ]
    assert list(failed_summary["non_repairable_reason_families"]) == []
    assert plan["input_material_summary"]["raw_input_included"] is False
    assert plan["input_material_summary"]["comment_text_body_included"] is False
    _assert_body_free(plan)


def test_p3_explicit_normal_observation_rebuild_candidate_is_selected_before_bounded_original() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            ],
        },
        normal_observation_rebuild_candidate=_normal_rebuild_candidate(),
        trace_id="p3-normal-observation-rebuild-selects-normal-first",
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result.selection_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result.candidate.composer_model == NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
    assert result.candidate.generation_method == NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD
    assert result.candidate.composer_meta["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert result.candidate.composer_meta["candidate_lineage"][
        "public_candidate_rebuilt_after_recovery"
    ] is True
    _assert_body_free(result.as_meta())


def test_p3_non_repairable_reason_keeps_default_plan_on_bounded_original() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_safety_blocked_surface_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p3-normal-observation-nonrepairable-plan",
    )

    plan = result.as_meta()["recovery_plan"]
    failed_summary = plan["failed_gate_summary"]
    assert plan["target_public_candidate_source"] == (
        CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    )
    assert list(failed_summary["reason_families"]) == ["surface_grammar"]
    assert list(failed_summary["non_repairable_reason_families"]) == ["safety"]
    assert BLOCKER_NORMAL_OBSERVATION_REBUILD_CANDIDATE_MISSING not in plan[
        "blockers_if_no_public_candidate"
    ]
    _assert_body_free(plan)
