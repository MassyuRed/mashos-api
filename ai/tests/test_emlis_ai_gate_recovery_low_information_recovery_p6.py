# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6 low-information recovery connection tests.

P6 must rebuild a public candidate through the existing low-information
observation composer.  It must not promote the Gate Recovery material surface,
reuse the diagnostic recovery comment text, or serialize raw input/body text into
recovery meta.
"""

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

import emlis_ai_reply_service as reply_service
from emlis_ai_display_gate import DisplayDecision
from emlis_ai_gate_recovery_loop import (
    GateRecoveryLoopResult,
    build_gate_recovery_surface_binding_meta,
    recover_emlis_gate_failure,
)
from emlis_ai_gate_recovery_public_candidate_builder import (
    LOW_INFORMATION_RECOVERY_COMPOSER_MODEL,
    LOW_INFORMATION_RECOVERY_GENERATION_METHOD,
    LOW_INFORMATION_RECOVERY_SOURCE_PHASE,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
    RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
)
from emlis_ai_safety_triage import TRIAGE_SAFE_OBSERVATION
from emlis_ai_types import (
    ConversationComposerCandidate,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)


_LOW_INFORMATION_INPUT = {
    "memo": "なんか今日は全部だるい。\n何もしたくない。",
    "memo_action": "",
    "emotions": ["悲しみ", "不安"],
    "category": ["生活"],
}
_FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS = (
    "今回の入力では",
    "原因や結論までは",
    "誰かを良い悪い",
)


def _display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["visible_surface_acceptance_gate_failed"],
        trace_id="p6-low-information-recovery",
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
        material_quality="low_information",
        visible_material_slots=("emotion_direction", "target", "time", "unresolved_weight"),
        unknown_slots=("event", "relationship", "next_action", "impact", "cause", "user_intent"),
        generic_relation_material_ids=(),
        relation_material_ids=(),
        as_meta=lambda: {
            "material_quality": "low_information",
            "visible_material_slots": ["emotion_direction", "target", "time", "unresolved_weight"],
            "unknown_slots": ["event", "relationship", "next_action", "impact", "cause", "user_intent"],
            "generic_relation_material_ids": [],
            "relation_material_ids": [],
            "safety_triage_kind": TRIAGE_SAFE_OBSERVATION,
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


def _assert_low_information_public_candidate(candidate: ConversationComposerCandidate) -> None:
    comment_text = str(candidate.comment_text or "").strip()
    meta = candidate.composer_meta
    assert comment_text
    assert candidate.composer_source == "ai_generated"
    assert candidate.composer_model == LOW_INFORMATION_RECOVERY_COMPOSER_MODEL
    assert candidate.generation_method == LOW_INFORMATION_RECOVERY_GENERATION_METHOD
    assert meta["source_phase"] == LOW_INFORMATION_RECOVERY_SOURCE_PHASE
    assert meta["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert meta["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert meta["origin_gate_recovery_plan"] is True
    assert meta["phase20_6_low_information_recovery_connected"] is True
    assert meta["low_information_body_promoted_after_gate_recovery"] is True
    assert meta["contains_known_scope_observation"] is True
    assert meta["contains_humility_marker"] is True
    assert meta["contains_question"] is True
    assert meta["question_not_only"] is True
    assert meta["low_information_reception_required"] is True
    assert meta["low_information_reception_shape_valid"] is True
    assert meta["question_after_reception"] is True
    assert meta["question_dominant_surface"] is False
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    assert comment_text.index("詳しく残せそうなら") > comment_text.index("Emlisから：")
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["fixed_fallback_used"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert "何があったか" in comment_text
    for fragment in _FORBIDDEN_PUBLIC_SURFACE_FRAGMENTS:
        assert fragment not in comment_text
    assert _LOW_INFORMATION_INPUT["memo"].split("\n", maxsplit=1)[0] not in comment_text
    _assert_meta_body_free(meta)


def test_p6_builder_composes_low_information_candidate_without_recovery_template() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_LOW_INFORMATION_INPUT),
        material_route=_material_route(),
        original_composer_candidate=None,
        original_display_decision=_display_decision(),
        safety_triage_kind=TRIAGE_SAFE_OBSERVATION,
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "schema_version": "cocolon.emlis.recovery_observation_plan.v1",
            "recovery_context": RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
            "input_material_summary": {
                "material_quality": "low_information",
                "visible_material_slots": ["emotion_direction", "target", "time", "unresolved_weight"],
                "unknown_slots": ["event", "relationship", "next_action", "impact", "cause", "user_intent"],
                "relation_material_ids": [],
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            ],
        },
        trace_id="p6-builder",
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert result.blocked_reasons == ()
    _assert_low_information_public_candidate(result.candidate)
    meta = result.as_meta()
    assert meta["candidate_available"] is True
    assert meta["source_kind"] == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    assert meta["gate_recovery_public_boundary_decision"]["blockers"] == []
    assert meta["contract_flags"]["raw_input_included"] is False
    assert meta["contract_flags"]["comment_text_body_included"] is False
    _assert_meta_body_free(meta)


def test_p6_recover_emlis_gate_failure_promotes_only_low_information_candidate() -> None:
    result = recover_emlis_gate_failure(
        current_input=dict(_LOW_INFORMATION_INPUT),
        material_route=_material_route(),
        display_decision=_display_decision(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["original_grounding_failed"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["original_template_failed"]),
        safety_triage_kind=TRIAGE_SAFE_OBSERVATION,
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="p6-loop",
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        post_final_gate_failure=True,
        allow_low_information_post_final_recovery=True,
    )

    assert result.applied is True
    assert result.composer_candidate is not None
    assert result.display_decision.observation_status == "passed"
    assert result.blocked_reasons == ()
    assert result.composer_source == "ai_generated"
    _assert_low_information_public_candidate(result.composer_candidate)
    builder_meta = result.surface_binding_meta["phase20_5_gate_recovery_public_candidate_builder"]
    assert builder_meta["candidate_available"] is True
    assert builder_meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    assert result.surface_binding_meta["public_display_allowed"] is False
    assert "post_final_gate_recovery_material_surface_public_leak" in result.surface_binding_meta["public_boundary_blockers"]


def test_p6_reply_service_boundary_ignores_diagnostic_binding_when_candidate_is_rebuilt_public() -> None:
    candidate = ConversationComposerCandidate(
        comment_text="まだ詳しい出来事までは見えていません。詳しく残せそうなら、何があったか残してみませんか。",
        composer_source="ai_generated",
        status="generated",
        composer_model=LOW_INFORMATION_RECOVERY_COMPOSER_MODEL,
        generation_method=LOW_INFORMATION_RECOVERY_GENERATION_METHOD,
        composer_meta={
            "source_phase": LOW_INFORMATION_RECOVERY_SOURCE_PHASE,
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "candidate_lineage": {
                "original_candidate_present": False,
                "original_candidate_source": "none",
                "recovery_plan_used": True,
                "diagnostic_surface_used": False,
                "public_candidate_rebuilt_after_recovery": True,
            },
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )
    result = GateRecoveryLoopResult(
        applied=True,
        display_decision=DisplayDecision(observation_status="passed", rejection_reasons=[], trace_id="p6-p4"),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=True, rejection_reasons=[]),
        template_echo_report=TemplateEchoReport(passed=True, rejection_reasons=[]),
        composer_source="ai_generated",
        composer_candidate=candidate,
        blocked_reasons=(),
        surface_binding_meta=build_gate_recovery_surface_binding_meta(
            material_quality="low_information",
            visible_slots=("emotion_direction",),
            unknown_slots=("event",),
            relation_ids=(),
            policy="reroute_low_information",
            recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
            post_final_gate_failure=True,
        ),
    )

    decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    )

    assert decision["public_display_allowed"] is True
    assert decision["blockers"] == []
    assert decision["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert decision["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
