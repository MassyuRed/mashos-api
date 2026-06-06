# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5 Gate Recovery loop connection for normal observation rebuild.

P4 builds the normal_observation_rebuild_candidate.  P5 must connect that
candidate to the Gate Recovery loop so the rebuilt public candidate is the one
that goes through Runtime / Visible / Display gates.  The diagnostic Gate
Recovery material surface must remain blocked and must not become public text.
"""

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

from emlis_ai_gate_recovery_loop import recover_emlis_gate_failure
from emlis_ai_gate_recovery_public_candidate_builder import (
    GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY,
    NORMAL_OBSERVATION_REBUILD_SOURCE_PHASE,
    assert_public_recovery_candidate_result_meta,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
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
        trace_id="p5-normal-observation-rebuild-loop",
    )


def _original_ai_generated_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=_ORIGINAL_RELATION_SKELETON_TEXT,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p5-normal-observation-original",
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


def test_p5_loop_promotes_normal_observation_rebuild_candidate_through_existing_gates() -> None:
    result = recover_emlis_gate_failure(
        current_input=dict(_CURRENT_INPUT),
        display_decision=_surface_failed_display_decision(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["original_grounding_failed"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["surface_relation_skeleton_major"]),
        material_route=_material_route(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="p5-normal-observation-rebuild-loop",
        original_composer_candidate=_original_ai_generated_candidate(),
        original_composer_source="ai_generated",
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    assert result.blocked_reasons == ()
    assert result.composer_source == "ai_generated"
    assert result.composer_candidate is not None
    assert result.runtime_surface_pre_return_gate_report["passed"] is True
    assert result.visible_surface_acceptance_gate_report["passed"] is True

    candidate = result.composer_candidate
    assert candidate.composer_meta["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert candidate.composer_meta["source_phase"] == NORMAL_OBSERVATION_REBUILD_SOURCE_PHASE
    assert candidate.composer_meta["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert candidate.composer_meta["candidate_lineage"]["diagnostic_surface_used"] is False
    assert candidate.composer_meta["candidate_lineage"]["public_candidate_rebuilt_after_recovery"] is True
    assert candidate.composer_meta["two_stage_section_surface_plan"]["required"] is False
    assert candidate.comment_text.strip()
    assert candidate.comment_text != _ORIGINAL_RELATION_SKELETON_TEXT
    assert _CURRENT_INPUT["memo"] not in candidate.comment_text
    for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in candidate.comment_text
    _assert_meta_body_free(candidate.composer_meta)

    assert result.reader_report.summary_of_output == "phase20_8_normal_observation_rebuild"
    assert result.grounding_report.grounding_scope == "current_input_normal_observation_rebuild"
    assert result.grounding_report.binding_support_source == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )

    builder_meta = result.surface_binding_meta[GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY]
    assert builder_meta["candidate_available"] is True
    assert builder_meta["source_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert builder_meta["selection_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert builder_meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    assert builder_meta["contract_flags"]["raw_input_included"] is False
    assert builder_meta["contract_flags"]["comment_text_body_included"] is False
    assert_public_recovery_candidate_result_meta(builder_meta)
    _assert_meta_body_free(builder_meta)

    # The diagnostic Gate Recovery material surface remains blocked; the loop
    # adopts only the separate normal_observation_rebuild_candidate.
    assert result.surface_binding_meta["public_display_allowed"] is False
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in result.surface_binding_meta[
        "public_boundary_blockers"
    ]
