# -*- coding: utf-8 -*-
from __future__ import annotations

"""P7 bounded original candidate repair / re-render connection tests.

Gate Recovery may use the original composer candidate as repair material, but it
must not fall back to the diagnostic Gate Recovery material surface.  The public
candidate keeps source lineage and remains body-free in serialized meta.
"""

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

from emlis_ai_display_gate import DisplayDecision
from emlis_ai_gate_recovery_loop import recover_emlis_gate_failure
from emlis_ai_gate_recovery_public_candidate_builder import (
    BOUNDED_ORIGINAL_REPAIR_COMPOSER_MODEL,
    BOUNDED_ORIGINAL_REPAIR_GENERATION_METHOD,
    BOUNDED_ORIGINAL_REPAIR_SOURCE_PHASE,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_types import (
    ConversationComposerCandidate,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)

_FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS = (
    "今回の入力では",
    "Emlisから：原因や結論までは",
    "原因や結論までは決めず",
    "誰かを良い悪い",
)

_CURRENT_INPUT = {
    "memo": "仕事のことが頭に残っていて、帰ってからも切り替えきれない。",
    "memo_action": "今日は少し早めに休む。",
    "emotions": ["不安", "疲れ"],
    "category": ["仕事"],
}

_ORIGINAL_TWO_STAGE_TEXT = (
    "見えたこと：\n"
    "今日は仕事のことが残っていて、まだ少し距離を置きながら整理しようとしているように見えます。\n"
    "Emlisから：\n"
    "いまは結論を急ぐより、扱える範囲をひとつに絞る方がよさそうです。"
)


def _display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["visible_surface_acceptance_gate_failed", "surface_too_long"],
        trace_id="p7-bounded-original-repair",
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


def _material_route() -> SimpleNamespace:
    return SimpleNamespace(
        material_quality="eligible",
        visible_material_slots=("event", "emotion_direction", "action", "time"),
        unknown_slots=("cause",),
        generic_relation_material_ids=("work_material",),
        relation_material_ids=("work_material",),
        as_meta=lambda: {
            "material_quality": "eligible",
            "visible_material_slots": ["event", "emotion_direction", "action", "time"],
            "unknown_slots": ["cause"],
            "generic_relation_material_ids": ["work_material"],
            "relation_material_ids": ["work_material"],
            "safety_triage_kind": "safe_observation",
        },
    )


def _original_candidate(comment_text: str = _ORIGINAL_TWO_STAGE_TEXT) -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=comment_text,
        composer_source="limited_composer",
        status="generated",
        ai_generated=True,
        trace_id="p7-original-candidate",
        attempt_count=1,
        used_evidence_span_ids=[],
        confidence=0.82,
        rejection_reasons=[],
        response_schema_version="cocolon.emlis.limited_composer.response.v1",
        fixed_string_renderer_used=False,
        composer_model="limited_composer_candidate",
        generation_method="limited_composer",
        coverage_scope="current_input_only",
        generation_scope="current_input_only",
        composer_meta={
            "source_phase": "limited_composer",
            "candidate_source_kind": "limited_composer_candidate",
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "contains_known_scope_observation": True,
            "contains_humility_marker": True,
            "contains_question": False,
            "question_not_only": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        used_claim_ids=[],
        used_relation_ids=["work_material"],
    )


def _gate_recovery_material_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=(
            "見えたこと：\n"
            "今回の入力では、仕事に関する記録として、不安の向きが出ています。\n"
            "Emlisから：\n原因や結論までは決めず、いま置かれた材料だけで受け取ります。"
        ),
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p7-forbidden-gate-recovery-original",
        composer_model="phase20_5_gate_recovery_material_surface",
        generation_method="phase20_5_gate_recovery_loop",
        composer_meta={
            "candidate_source_kind": "gate_recovery_material_surface",
            "public_surface_role": "diagnostic_recovery_surface",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )


def _assert_meta_body_free(meta: Mapping[str, Any]) -> None:
    text_keys = {
        "raw_input",
        "current_input",
        "memo",
        "memo_text",
        "comment_text",
        "commentText",
        "candidate_comment_text",
        "public_comment_text",
        "body",
        "text",
        "candidate_body",
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


def _assert_bounded_original_public_candidate(candidate: ConversationComposerCandidate) -> None:
    comment_text = str(candidate.comment_text or "").strip()
    meta = candidate.composer_meta
    assert comment_text
    assert candidate.composer_source == "ai_generated"
    assert candidate.composer_model == BOUNDED_ORIGINAL_REPAIR_COMPOSER_MODEL
    assert candidate.generation_method == BOUNDED_ORIGINAL_REPAIR_GENERATION_METHOD
    assert meta["source_phase"] == BOUNDED_ORIGINAL_REPAIR_SOURCE_PHASE
    assert meta["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    assert meta["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert meta["phase20_7_bounded_original_candidate_repair_connected"] is True
    assert meta["bounded_original_candidate_repair_applied"] is True
    assert meta["bounded_original_rerender_attempt_limit"] == 1
    assert meta["candidate_lineage"]["original_candidate_present"] is True
    assert meta["candidate_lineage"]["public_candidate_rebuilt_after_recovery"] is True
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["original_comment_text_body_included"] is False
    assert meta["fixed_fallback_used"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert "見えたこと：" in comment_text
    assert "Emlisから：" in comment_text
    for fragment in _FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS:
        assert fragment not in comment_text
    assert _CURRENT_INPUT["memo"] not in comment_text
    _assert_meta_body_free(meta)


def test_p7_builder_builds_bounded_repaired_original_candidate_without_gate_recovery_surface() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "schema_version": "cocolon.emlis.recovery_observation_plan.v1",
            "input_material_summary": {
                "material_quality": "eligible",
                "visible_material_slots": ["event", "emotion_direction", "action", "time"],
                "unknown_slots": ["cause"],
                "relation_material_ids": ["work_material"],
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            ],
        },
        trace_id="p7-builder",
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    assert result.blocked_reasons == ()
    _assert_bounded_original_public_candidate(result.candidate)
    meta = result.as_meta()
    assert meta["candidate_available"] is True
    assert meta["source_kind"] == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    assert meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    assert meta["gate_recovery_public_boundary_decision"]["blockers"] == []
    assert meta["contract_flags"]["raw_input_included"] is False
    assert meta["contract_flags"]["comment_text_body_included"] is False
    _assert_meta_body_free(meta)


def test_p7_builder_does_not_repair_gate_recovery_material_surface_as_original() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=_gate_recovery_material_candidate(),
        original_display_decision=_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            ],
        },
        trace_id="p7-builder-blocked",
    )

    assert result.candidate is None
    assert result.public_display_allowed is False
    assert result.source_kind == "none"
    assert "bounded_original_candidate_missing" not in result.decision_reasons
    assert "gate_recovery_material_surface_public_leak" in result.blocked_reasons
    meta = result.as_meta()
    assert meta["candidate_available"] is False
    assert meta["candidate_lineage"]["diagnostic_surface_used"] is True
    _assert_meta_body_free(meta)


def test_p8_surface_grammar_failure_prefers_normal_rebuild_over_bounded_original_repair() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        original_composer_candidate=ConversationComposerCandidate(
            comment_text=(
                "この入力では、仕事のことが同じ流れの中で残っています。"
                "片方だけに減らさず、状態が一色ではありません。"
            ),
            composer_source="ai_generated",
            status="generated",
            ai_generated=True,
            trace_id="p8-normal-rebuild-original",
            attempt_count=1,
            confidence=0.82,
            response_schema_version="cocolon.emlis.complete_composer.response.v1",
            fixed_string_renderer_used=False,
            composer_model="complete_initial_composer_v1",
            generation_method="complete_initial_composer",
            coverage_scope="current_input_only",
            generation_scope="current_input_only",
            composer_meta={
                "source_phase": "complete_initial_composer",
                "candidate_source_kind": "complete_initial_composer",
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            used_relation_ids=["work_material"],
        ),
        original_display_decision=DisplayDecision(
            observation_status="rejected",
            comment_text="",
            rejection_reasons=[
                "visible_surface_acceptance_gate_failed",
                "surface_relation_skeleton_major",
                "surface_grammar_warning",
            ],
            trace_id="p8-normal-rebuild-over-bounded-original",
        ),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p8-normal-rebuild-over-bounded-original",
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result.selection_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert result.source_kind != CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    assert result.blocked_reasons == ()
    comment_text = str(result.candidate.comment_text or "")
    assert "同じ流れ" not in comment_text
    assert "片方だけに減らさず" not in comment_text
    assert "状態が一色ではありません" not in comment_text
    assert "今回の入力では" not in comment_text
    assert "原因や結論までは" not in comment_text
    assert "誰かを良い悪い" not in comment_text
    assert _CURRENT_INPUT["memo"] not in comment_text
    meta = result.as_meta()
    assert meta["recovery_plan"]["target_public_candidate_source"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    _assert_meta_body_free(meta)
    _assert_meta_body_free(result.candidate.composer_meta)


def test_p7_recover_emlis_gate_failure_promotes_bounded_original_candidate_through_existing_gates() -> None:
    result = recover_emlis_gate_failure(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        display_decision=_display_decision(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["original_grounding_failed"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["original_template_failed"]),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="p7-loop",
        original_composer_candidate=_original_candidate(),
        original_composer_source="limited_composer",
    )

    assert result.applied is True
    assert result.composer_candidate is not None
    assert result.display_decision.observation_status == "passed"
    assert result.blocked_reasons == ()
    assert result.composer_source == "ai_generated"
    _assert_bounded_original_public_candidate(result.composer_candidate)
    builder_meta = result.surface_binding_meta["phase20_5_gate_recovery_public_candidate_builder"]
    assert builder_meta["candidate_available"] is True
    assert builder_meta["source_kind"] == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    assert builder_meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    assert result.surface_binding_meta["public_display_allowed"] is False
    assert "gate_recovery_material_surface_public_leak" in result.surface_binding_meta["public_boundary_blockers"]


def test_p7_recover_emlis_gate_failure_keeps_gate_recovery_material_original_blocked() -> None:
    result = recover_emlis_gate_failure(
        current_input=dict(_CURRENT_INPUT),
        material_route=_material_route(),
        display_decision=_display_decision(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["original_grounding_failed"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["original_template_failed"]),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="p7-loop-blocked",
        original_composer_candidate=_gate_recovery_material_candidate(),
        original_composer_source="ai_generated",
    )

    assert result.applied is False
    assert result.composer_candidate is None
    assert result.display_decision.observation_status == "rejected"
    assert "gate_recovery_material_surface_public_leak" in result.blocked_reasons
    builder_meta = result.surface_binding_meta["phase20_5_gate_recovery_public_candidate_builder"]
    assert builder_meta["candidate_available"] is False
    assert builder_meta["source_kind"] == "none"
    _assert_meta_body_free(builder_meta)
