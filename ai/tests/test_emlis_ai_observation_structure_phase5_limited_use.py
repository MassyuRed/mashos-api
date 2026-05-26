from __future__ import annotations

from typing import Any, Mapping

import pytest

from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_display_gate import decide_emlis_observation_display
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_BLOCK,
    build_runtime_surface_pre_return_gate_report,
)
from emlis_ai_types import GraphClaim, GroundingReport, ListenerReaderReport, ObservationGraph, TemplateEchoReport


_WORK_ANXIETY_INPUT: dict[str, Any] = {
    "id": "phase5-eso-001",
    "created_at": "2026-05-25T06:00:00Z",
    "memo": "この職場でやっていけるか不安",
    "memo_action": "職場で新しい仕事を任された",
    "emotion_details": [{"type": "不安", "strength": "medium"}],
    "category": ["仕事"],
}


def _evidence():
    return build_evidence_ledger(_WORK_ANXIETY_INPUT)


def _graph() -> ObservationGraph:
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="c1",
            claim_type="state",
            text="不安",
            evidence_span_ids=["s3"],
            confidence=0.9,
        ),
        pressure_sources=[
            GraphClaim(
                claim_id="c2",
                claim_type="pressure_source",
                text="職場で新しい仕事を任された",
                evidence_span_ids=["s2"],
                confidence=0.86,
            )
        ],
        limit_signals=[
            GraphClaim(
                claim_id="c3",
                claim_type="limit_signal",
                text="この職場でやっていけるか不安",
                evidence_span_ids=["s1"],
                confidence=0.88,
            )
        ],
    )


class _StaticComposerClient:
    def __init__(self, comment_text: str) -> None:
        self.comment_text = comment_text
        self.payload: Mapping[str, Any] | None = None

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.payload = payload
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "comment_text": self.comment_text,
            "used_evidence_span_ids": ["s1", "s2", "s3", "s4"],
            "confidence": 0.9,
            "composer_meta": {},
        }


def _material():
    return build_observation_structure_material(
        current_input=_WORK_ANXIETY_INPUT,
        evidence_ledger=_evidence(),
    )


def test_phase5_composer_payload_limits_environment_state_output_to_single_record_surface() -> None:
    payload = build_conversation_composer_payload(
        graph=_graph(),
        evidence_spans=_evidence(),
        observation_structure_material=_material(),
    )

    contract = payload["environment_state_output_surface_contract"]
    assert contract["connected"] is True
    assert contract["single_record_only"] is True
    assert contract["scope_marker_required"] is True
    assert contract["required_scope_marker"] == "今回の入力では"
    assert contract["allowed_surface_claim_strength"] == "single_observation"
    assert "continuation_concern" in contract["output_theme_ids"]

    composition = payload["composition_contract"]
    assert composition["environment_state_output_frame_limited_use"] is True
    assert composition["environment_state_output_single_record_only"] is True
    assert composition["must_not_claim_period_tendency_from_single_record"] is True
    assert composition["must_not_claim_personality_type"] is True
    assert composition["must_not_claim_cause_from_category"] is True
    assert composition["must_not_claim_recovery_prescription"] is True
    assert composition["dictionary_must_not_generate_completed_sentence"] is True


def test_phase5_composer_accepts_single_record_scoped_surface_only() -> None:
    client = _StaticComposerClient(
        "今回の入力では、仕事という場面で不安が選ばれ、続けられるかへの心配が置かれています。"
    )

    candidate = compose_emlis_conversation_candidate(
        graph=_graph(),
        evidence_spans=_evidence(),
        composer_client=client,
        observation_structure_material=_material(),
    )

    assert candidate.status == "generated"
    assert candidate.composer_source == "ai_generated"
    assert candidate.comment_text
    assert candidate.composer_meta["environment_state_output_frame_limited_use"] is True
    assert candidate.composer_meta["environment_state_output_frame_single_record_only"] is True
    assert candidate.composer_meta["environment_state_output_allowed_surface_claim_strength"] == "single_observation"
    assert candidate.composer_meta["period_tendency_from_single_record"] is False
    assert candidate.composer_meta["recovery_prescription_allowed"] is False


def test_phase2_composer_applies_scope_marker_to_candidate_before_surface_validation() -> None:
    client = _StaticComposerClient("仕事という場面で不安が選ばれ、続けられるかへの心配が置かれています。")

    candidate = compose_emlis_conversation_candidate(
        graph=_graph(),
        evidence_spans=_evidence(),
        composer_client=client,
        observation_structure_material=_material(),
    )

    completion = candidate.composer_meta["environment_state_output_scope_marker_completion"]
    assert candidate.status == "generated"
    assert candidate.composer_source == "ai_generated"
    assert candidate.comment_text.startswith("今回の入力では、")
    assert candidate.rejection_reasons == []
    assert completion["applied"] is True
    assert completion["target_line"] == "first_body_line"
    assert completion["before_marker_present"] is False
    assert completion["after_marker_present"] is True
    assert completion["display_gate_relaxed"] is False




_PHASE3_FORBIDDEN_SURFACE_CASES = (
    ("この傾向が最近ずっと続いています。", "period_tendency_from_single_record_surface"),
    ("あなたは現実逃避しやすい性格です。", "personality_tendency_surface"),
    ("これは心理診断として不安の症状です。", "diagnosis_surface"),
    ("原因は家庭環境です。", "cause_from_category_surface"),
    ("原因は不安が強いことです。", "cause_from_emotion_strength_surface"),
    ("回復するには毎日外に出るべきです。", "recovery_prescription_surface"),
)


@pytest.mark.parametrize(("surface", "expected_reason"), _PHASE3_FORBIDDEN_SURFACE_CASES)
def test_phase3_composer_rejects_forbidden_surface_claims_instead_of_repairing(
    surface: str, expected_reason: str
) -> None:
    client = _StaticComposerClient(surface)

    candidate = compose_emlis_conversation_candidate(
        graph=_graph(),
        evidence_spans=_evidence(),
        composer_client=client,
        observation_structure_material=_material(),
    )

    completion = candidate.composer_meta["environment_state_output_scope_marker_completion"]
    assert candidate.status == "schema_invalid"
    assert candidate.comment_text == ""
    assert expected_reason in candidate.rejection_reasons
    assert "environment_state_output_scope_marker_missing" not in candidate.rejection_reasons
    assert completion["action"] == "reject"
    assert completion["applied"] is False
    assert completion["display_gate_relaxed"] is False
    assert candidate.composer_meta["environment_state_output_frame_limited_use_rejected"] is True


def test_phase5_composer_rejects_period_personality_and_scope_overclaim_from_single_record() -> None:
    client = _StaticComposerClient("あなたは仕事で不安になるといつも続けられるかを心配するタイプです。")

    candidate = compose_emlis_conversation_candidate(
        graph=_graph(),
        evidence_spans=_evidence(),
        composer_client=client,
        observation_structure_material=_material(),
    )

    assert candidate.status == "schema_invalid"
    assert candidate.comment_text == ""
    assert "environment_state_output_scope_marker_missing" not in candidate.rejection_reasons
    assert "period_tendency_from_single_record_surface" in candidate.rejection_reasons
    assert "personality_tendency_surface" in candidate.rejection_reasons
    assert candidate.composer_meta["environment_state_output_frame_limited_use_rejected"] is True


def test_phase5_runtime_surface_gate_blocks_category_cause_and_recovery_prescription_surfaces() -> None:
    material = _material()
    payload = build_conversation_composer_payload(
        graph=_graph(),
        evidence_spans=_evidence(),
        observation_structure_material=material,
    )
    composer_meta = {
        "environment_state_output_surface_contract": payload["environment_state_output_surface_contract"],
        "environment_state_output_frame_limited_use": True,
    }

    cause_report = build_runtime_surface_pre_return_gate_report(
        comment_text="今回の入力では、仕事が不安の原因です。",
        composer_meta=composer_meta,
        rerender_allowed=False,
    )
    assert cause_report["passed"] is False
    assert cause_report["action"] == ACTION_BLOCK
    assert "cause_from_category_surface" in cause_report["rejection_reasons"]
    assert cause_report["cause_from_category_surface_blocked"] is True
    assert cause_report["environment_state_output_scope_marker_present"] is True

    recovery_report = build_runtime_surface_pre_return_gate_report(
        comment_text="今回の入力では、自己理解すれば戻りやすいです。",
        composer_meta=composer_meta,
        rerender_allowed=False,
    )
    assert recovery_report["passed"] is False
    assert "recovery_prescription_surface" in recovery_report["rejection_reasons"]
    assert recovery_report["recovery_prescription_surface_blocked"] is True
    assert recovery_report["display_gate_relaxed"] is False


def test_phase5_display_gate_keeps_blocked_environment_state_output_surface_hidden() -> None:
    runtime_report = build_runtime_surface_pre_return_gate_report(
        comment_text="あなたは仕事で不安になるといつも続けられるかを心配するタイプです。",
        composer_meta={
            "environment_state_output_frame_limited_use": True,
            "environment_state_output_scope_marker_required": True,
            "environment_state_output_allowed_scope_markers": ["今回の入力では"],
        },
        rerender_allowed=False,
    )

    decision = decide_emlis_observation_display(
        comment_text="あなたは仕事で不安になるといつも続けられるかを心配するタイプです。",
        reader_report=ListenerReaderReport(understandable=True, addressee_clear=True, speaker_integrity_ok=True, conversational=True, report_like=False),
        grounding_report=GroundingReport(passed=True, coverage_ratio=1.0),
        template_echo_report=TemplateEchoReport(passed=True),
        composer_source="ai_generated",
        phase_completion_ready=True,
        runtime_surface_pre_return_gate_report=runtime_report,
    )

    assert decision.observation_status == "rejected"
    assert decision.comment_text == ""
    assert "runtime_surface_pre_return_gate_failed" in decision.rejection_reasons
    assert "period_tendency_from_single_record_surface" in decision.rejection_reasons
    assert "personality_tendency_surface" in decision.rejection_reasons
    assert decision.gate_trace["runtime_surface_pre_return_gate"]["environment_state_output_frame_surface_limited_use"] is True
    assert decision.gate_trace["runtime_surface_pre_return_gate"]["display_gate_relaxed"] is False



def test_phase5_actual_limited_composer_uses_frame_as_single_record_scoped_material_only() -> None:
    payload = build_conversation_composer_payload(
        graph=_graph(),
        evidence_spans=_evidence(),
        greeting_text="Mashさん、Emlisです。",
        observation_structure_material=_material(),
    )

    response = CocolonLimitedComposerClient().generate(payload)

    assert response["status"] == "generated"
    assert response["composer_source"] == "ai_generated"
    comment_text = response["comment_text"]
    assert "今回の入力では" in comment_text
    assert "継続できるかへの心配" in comment_text
    assert "タイプ" not in comment_text
    assert "いつも" not in comment_text
    assert "原因" not in comment_text
    assert "回復方法" not in comment_text
    assert "治る" not in comment_text
    assert "s1" in response["used_evidence_span_ids"]

    meta = response["composer_meta"]
    phase5_meta = meta["environment_state_output_phase5_limited_use"]
    assert phase5_meta["enabled"] is True
    assert phase5_meta["single_record_only"] is True
    assert phase5_meta["surface_use_applied"] is True
    assert phase5_meta["scope_marker_applied"] is True
    assert phase5_meta["safe_theme_unit_count"] >= 1
    assert "continuation_concern" in phase5_meta["selected_theme_ids"]
    assert meta["environment_state_output_frame_limited_use"] is True
    assert meta["environment_state_output_frame_single_record_only"] is True
    assert meta["environment_state_output_allowed_surface_claim_strength"] == "single_observation"
    assert meta["period_tendency_from_single_record"] is False
    assert meta["recovery_prescription_allowed"] is False
    assert meta["cause_inferred_from_category"] is False
    assert meta["cause_inferred_from_emotion_strength"] is False
    assert meta["personality_tendency_allowed"] is False


def test_phase3_composer_rejects_existing_marker_forbidden_claim_without_repairing() -> None:
    client = _StaticComposerClient("今回の入力では、あなたは仕事で不安になるタイプです。")

    candidate = compose_emlis_conversation_candidate(
        graph=_graph(),
        evidence_spans=_evidence(),
        composer_client=client,
        observation_structure_material=_material(),
    )

    completion = candidate.composer_meta["environment_state_output_scope_marker_completion"]
    assert candidate.status == "schema_invalid"
    assert candidate.comment_text == ""
    assert "personality_tendency_surface" in candidate.rejection_reasons
    assert "environment_state_output_scope_marker_missing" not in candidate.rejection_reasons
    assert completion["action"] == "reject"
    assert completion["applied"] is False
    assert completion["before_marker_present"] is True
    assert completion["after_marker_present"] is True
    assert completion["display_gate_relaxed"] is False
    assert candidate.composer_meta["environment_state_output_frame_limited_use_rejected"] is True


def test_phase3_runtime_gate_blocks_diagnosis_and_emotion_strength_cause_with_marker() -> None:
    material = _material()
    payload = build_conversation_composer_payload(
        graph=_graph(),
        evidence_spans=_evidence(),
        observation_structure_material=material,
    )
    composer_meta = {
        "environment_state_output_surface_contract": payload["environment_state_output_surface_contract"],
        "environment_state_output_frame_limited_use": True,
    }

    diagnosis_report = build_runtime_surface_pre_return_gate_report(
        comment_text="今回の入力では、これは不安障害の症状です。",
        composer_meta=composer_meta,
        rerender_allowed=False,
    )
    assert diagnosis_report["passed"] is False
    assert diagnosis_report["action"] == ACTION_BLOCK
    assert "diagnosis_surface" in diagnosis_report["rejection_reasons"]
    assert diagnosis_report["diagnosis_surface_blocked"] is True
    assert diagnosis_report["environment_state_output_scope_marker_present"] is True
    assert diagnosis_report["display_gate_relaxed"] is False

    cause_report = build_runtime_surface_pre_return_gate_report(
        comment_text="今回の入力では、不安が強いことが原因です。",
        composer_meta=composer_meta,
        rerender_allowed=False,
    )
    assert cause_report["passed"] is False
    assert "cause_from_emotion_strength_surface" in cause_report["rejection_reasons"]
    assert cause_report["cause_from_emotion_strength_surface_blocked"] is True
    assert cause_report["environment_state_output_scope_marker_present"] is True
    assert cause_report["display_gate_relaxed"] is False
