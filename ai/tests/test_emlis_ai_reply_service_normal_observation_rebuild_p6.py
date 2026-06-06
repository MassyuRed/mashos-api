# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6 reply_service post-final path for normal observation rebuild.

P5 connects the normal_observation_rebuild_candidate to the Gate Recovery loop.
P6 pins the reply_service boundary/meta behavior: when post-final recovery adopts
that rebuilt public candidate, diagnostics must classify the actual public
candidate as normal_observation_rebuild_candidate, not as the diagnostic Gate
Recovery material surface.  The path must stay one-shot and body-free.
"""

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

import emlis_ai_reply_service as reply_service
from emlis_ai_gate_recovery_loop import recover_emlis_gate_failure
from emlis_ai_gate_recovery_public_boundary import RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_response_contract import ResponseKind
from emlis_ai_types import (
    ConversationComposerCandidate,
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)

_CURRENT_INPUT = {
    "memo": "仕事の話を聞いたあと、納得したい気持ちと引っかかりがどちらも残っている。",
    "memo_action": "明日は一度、事実だけ書き出してから返事を考える。",
    "emotions": ["不安", "違和感", "迷い"],
    "category": ["仕事", "人間関係"],
}

_ORIGINAL_RELATION_SKELETON_TEXT = (
    "この入力では、仕事の話に対して同じ流れの中で、納得したい気持ちと"
    "引っかかりが同じ場所に残っています。片方だけに減らさず、状態が"
    "一色ではありません。"
)

_FORBIDDEN_PUBLIC_FRAGMENTS = (
    "同じ流れ",
    "同じ場所",
    "片方だけに減らさず",
    "状態が一色ではありません",
    "原因や結論までは決めず",
    "誰かを良い悪いで決めず",
    "見えたこと：",
    "Emlisから：",
)

_FORBIDDEN_META_TEXT_KEYS = {
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
        trace_id="p6-reply-service-normal-observation-rebuild",
    )


def _original_ai_generated_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=_ORIGINAL_RELATION_SKELETON_TEXT,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p6-normal-observation-original",
        attempt_count=1,
        confidence=0.83,
        rejection_reasons=[],
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


def _reader_report() -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=False,
        addressee_clear=False,
        speaker_integrity_ok=True,
        conversational=False,
        report_like=True,
        rejection_reasons=["original_gate_failed"],
    )


def _assert_meta_body_free(meta: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & _FORBIDDEN_META_TEXT_KEYS)
            for item in value.values():
                walk(item)
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                walk(item)

    walk(meta)


def _post_final_normal_rebuild_loop_result() -> Any:
    result = recover_emlis_gate_failure(
        current_input=dict(_CURRENT_INPUT),
        display_decision=_surface_failed_display_decision(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["original_grounding_failed"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["surface_relation_skeleton_major"]),
        material_route=_material_route(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        runtime_surface_pre_return_gate_report={
            "evaluated": True,
            "passed": False,
            "action": "rerender_shallow_v2",
            "rejection_reasons": ["runtime_surface_pre_return_gate_action_rerender_shallow_v2"],
        },
        visible_surface_acceptance_gate_report={
            "evaluated": True,
            "passed": False,
            "action": "rerender_surface",
            "rejection_reasons": ["visible_surface_acceptance_gate_failed"],
        },
        trace_id="p6-reply-service-normal-observation-rebuild",
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        post_final_gate_failure=True,
        allow_low_information_post_final_recovery=True,
        original_composer_candidate=_original_ai_generated_candidate(),
        original_composer_source="ai_generated",
    )
    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    assert result.composer_candidate is not None
    assert result.composer_candidate.composer_meta["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    return result


def test_p6_reply_service_post_final_boundary_classifies_adopted_normal_rebuild_candidate() -> None:
    result = _post_final_normal_rebuild_loop_result()
    candidate = result.composer_candidate
    assert candidate is not None
    assert candidate.comment_text.strip()
    assert candidate.comment_text != _ORIGINAL_RELATION_SKELETON_TEXT
    for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in candidate.comment_text

    runtime_gate = dict(result.runtime_surface_pre_return_gate_report or {})
    visible_gate = dict(result.visible_surface_acceptance_gate_report or {})
    assert runtime_gate.get("passed") is True
    assert runtime_gate.get("rerender_attempted") is True
    assert runtime_gate.get("rerender_attempt_limit") == 1
    assert visible_gate.get("passed") is True
    assert visible_gate.get("rerender_attempted") is True

    boundary_decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        composer_client_resolution={"rejection_reasons": []},
    )
    assert boundary_decision["public_display_allowed"] is True
    assert boundary_decision["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert boundary_decision["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert boundary_decision["blockers"] == []

    boundary_meta = reply_service._build_reply_service_gate_recovery_public_boundary_meta(
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        gate_recovery_loop_result=result,
        public_boundary_decision=boundary_decision,
        adopted=True,
    )
    assert boundary_meta["public_display_allowed"] is True
    assert boundary_meta["adopted"] is True
    assert boundary_meta["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert boundary_meta["adopted_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert boundary_meta["final_surface_origin_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert boundary_meta["normal_observation_rebuild_attempted"] is True
    assert boundary_meta["normal_observation_rebuild_applied"] is True
    assert boundary_meta["normal_observation_rebuild_blocked_reasons"] == []
    assert boundary_meta["public_candidate_rebuilt_after_recovery"] is True
    assert boundary_meta["diagnostic_surface_used"] is False
    assert boundary_meta["raw_input_included"] is False
    assert boundary_meta["comment_text_body_included"] is False

    # The Gate Recovery loop still carries the diagnostic material surface as
    # blocked meta-only evidence, but reply_service must not use that as the
    # adopted public surface origin.
    loop_result_meta = boundary_meta["gate_recovery_loop_result"]
    assert loop_result_meta["candidate_source_kind"] != boundary_meta["candidate_source_kind"]
    assert any(
        blocker == BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK
        or blocker == "post_final_gate_recovery_material_surface_public_leak"
        for blocker in result.surface_binding_meta["public_boundary_blockers"]
    )
    _assert_meta_body_free(boundary_meta)


def test_p6_phase20_13_post_final_meta_carries_normal_rebuild_origin_without_body() -> None:
    result = _post_final_normal_rebuild_loop_result()
    boundary_decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        composer_client_resolution={"rejection_reasons": []},
    )
    boundary_meta = reply_service._build_reply_service_gate_recovery_public_boundary_meta(
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        gate_recovery_loop_result=result,
        public_boundary_decision=boundary_decision,
        adopted=True,
    )

    post_final_meta = reply_service._build_phase20_13_post_final_gate_recovery_meta(
        attempted=True,
        applied=True,
        original_final_status="rejected",
        final_status_after_recovery="passed",
        response_kind=ResponseKind.NORMAL_OBSERVATION.value,
        material_quality="eligible",
        recovery_policy="normal_observation_post_final_recheck",
        from_gate="final_visible_surface_acceptance_gate",
        blocked_reasons=["surface_relation_skeleton_major", "surface_grammar_warning"],
        public_boundary_meta=boundary_meta,
    )

    assert post_final_meta["attempted"] is True
    assert post_final_meta["applied"] is True
    assert post_final_meta["attempt_count"] == 1
    assert post_final_meta["final_status_after_recovery"] == "passed"
    assert post_final_meta["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert post_final_meta["final_surface_origin_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert post_final_meta["normal_observation_rebuild_attempted"] is True
    assert post_final_meta["normal_observation_rebuild_applied"] is True
    assert post_final_meta["normal_observation_rebuild_blocked_reasons"] == []
    assert post_final_meta["public_boundary_checked"] is True
    assert post_final_meta["public_boundary_blocked"] is False
    assert post_final_meta["public_display_allowed_by_boundary"] is True
    assert post_final_meta["display_gate_relaxed"] is False
    assert post_final_meta["safety_gate_relaxed"] is False
    assert post_final_meta["grounding_gate_relaxed"] is False
    assert post_final_meta["template_gate_relaxed"] is False
    assert post_final_meta["fixed_fallback_used"] is False
    assert post_final_meta["public_response_key_change"] is False
    assert post_final_meta["raw_input_included"] is False
    assert post_final_meta["comment_text_body_included"] is False
    _assert_meta_body_free(post_final_meta)


def test_p6_step7_summary_marks_post_final_normal_rebuild_as_repair_success() -> None:
    result = _post_final_normal_rebuild_loop_result()
    boundary_decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        composer_client_resolution={"rejection_reasons": []},
    )
    boundary_meta = reply_service._build_reply_service_gate_recovery_public_boundary_meta(
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        gate_recovery_loop_result=result,
        public_boundary_decision=boundary_decision,
        adopted=True,
    )
    post_final_meta = reply_service._build_phase20_13_post_final_gate_recovery_meta(
        attempted=True,
        applied=True,
        original_final_status="rejected",
        final_status_after_recovery="passed",
        response_kind=ResponseKind.NORMAL_OBSERVATION.value,
        material_quality="eligible",
        recovery_policy="normal_observation_post_final_recheck",
        from_gate="final_visible_surface_acceptance_gate",
        blocked_reasons=["surface_relation_skeleton_major", "surface_grammar_warning"],
        public_boundary_meta=boundary_meta,
    )

    summary = reply_service._build_step7_public_feedback_diagnostic_summary(
        display_decision=result.display_decision,
        gate_trace=dict(result.display_decision.gate_trace or {}),
        phase_gate_meta=post_final_meta,
    )

    assert summary["candidate_repair_attempted"] is True
    assert summary["candidate_repair_succeeded"] is True
    assert summary["candidate_repair_failed"] is False
    assert summary["candidate_fail_closed_display_absent"] is False
    assert summary["rn_payload_absent"] is False
    assert summary["reason_family"] == "displayed"
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False


def test_p6_post_final_recovery_guard_prevents_second_attempt() -> None:
    assert reply_service._should_attempt_post_final_gate_recovery(
        display_decision=_surface_failed_display_decision(),
        final_candidate_text="この記録では、仕事の話について気持ちが残っている状態として見えます。",
        safety_requires_block=False,
        safety_report=SafetyBoundaryReport(requires_block=False),
        safety_triage_kind="safe_observation",
        material_quality="eligible",
        response_kind=ResponseKind.NORMAL_OBSERVATION.value,
        post_final_recovery_already_attempted=True,
    ) is False
