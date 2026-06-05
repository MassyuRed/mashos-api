# -*- coding: utf-8 -*-
from __future__ import annotations

"""P0/P1/P2/P3 tests for Gate Recovery public-surface leak blocking.

P0 fixes the RED surface-leak contract: a Gate Recovery material surface must
not become the public Emlis observation.  P1 fixes the blocker/source-kind/public
role vocabulary.  P2 adds the separate public-boundary decision; P3 wires it
into runtime Gate Recovery candidate promotion.
"""


from emlis_ai_gate_recovery_loop import (
    POST_FINAL_GATE_RECOVERY_CONTEXT,
    _gate_recovery_composer_meta,
    recover_emlis_gate_failure,
)
from emlis_ai_gate_recovery_public_boundary import (
    RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    assert_gate_recovery_public_boundary_decision,
    decide_gate_recovery_public_boundary,
    gate_recovery_public_display_allowed,
    validate_gate_recovery_public_boundary_decision,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_INTERNAL_POLICY_SENTENCE_LEAK,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    GATE_RECOVERY_MATERIAL_SURFACE_MODELS,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_product_quality_blocker_matrix import classify_product_quality_blocker
from emlis_ai_product_quality_measurement_event import normalize_product_quality_event
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision, GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


class _MaterialRoute:
    material_quality = "eligible"
    visible_material_slots = ("relationship", "action", "emotion_direction", "time")
    unknown_slots = ("cause",)
    generic_relation_material_ids = ("relationship_material",)

    def as_meta(self) -> dict[str, object]:
        return {
            "material_quality": self.material_quality,
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            "safety_triage_kind": "safe_observation",
        }


def _failed_display() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["surface_relation_skeleton_major", "phase8_repeated_sentence_tail"],
        trace_id="p0-gate-recovery-public-leak",
        gate_trace={
            "visible_surface_acceptance_gate": {
                "passed": False,
                "action": "rerender_surface",
                "classification": "repair_required",
                "rejection_reasons": ["surface_relation_skeleton_major"],
            }
        },
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


def _recovery_result(*, post_final: bool = False):
    return recover_emlis_gate_failure(
        current_input={
            "memo": "公開本文へそのまま写さない実入力",
            "memo_action": "公開本文へそのまま写さない行動入力",
            "emotions": ["平穏", "不安"],
            "category": ["生活"],
        },
        display_decision=_failed_display(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["graph_evidence_not_used"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["phase8_repeated_sentence_tail"]),
        material_route=_MaterialRoute(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="p0-gate-recovery-public-leak",
        recovery_context=POST_FINAL_GATE_RECOVERY_CONTEXT if post_final else "pre_public_display_gate",
        post_final_gate_failure=post_final,
    )




def test_p2_boundary_blocks_phase20_5_material_surface_without_storing_comment_body() -> None:
    meta = _gate_recovery_composer_meta(
        material_quality="eligible",
        visible_slots=("relationship", "action", "emotion_direction"),
        unknown_slots=("cause",),
        relation_ids=("relationship_material",),
        policy="shorten_surface",
    )
    candidate = ConversationComposerCandidate(
        comment_text="この本文はboundary decisionへ保存しない。",
        composer_source="ai_generated",
        status="generated",
        composer_model=GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
        generation_method="phase20_5_gate_recovery_loop",
        composer_meta=meta,
    )

    decision = decide_gate_recovery_public_boundary(
        candidate=candidate,
        composer_meta=meta,
        recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
        composer_resolution={"rejection_reasons": ["default_limited_composer_feature_disabled"]},
    )

    assert_gate_recovery_public_boundary_decision(decision)
    assert decision["public_display_allowed"] is False
    assert gate_recovery_public_display_allowed(decision) is False
    assert decision["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    assert decision["public_surface_role"] == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE in decision["blockers"]
    assert BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION in decision["blockers"]
    assert decision["contract_flags"]["raw_input_included"] is False
    assert decision["contract_flags"]["comment_text_body_included"] is False
    assert "comment_text" not in decision
    assert validate_gate_recovery_public_boundary_decision(decision) == []


def test_p2_boundary_blocks_post_final_material_surface() -> None:
    meta = _gate_recovery_composer_meta(
        material_quality="eligible",
        visible_slots=("relationship", "action", "emotion_direction"),
        unknown_slots=("cause",),
        relation_ids=("relationship_material",),
        policy="shorten_surface",
        recovery_context=POST_FINAL_GATE_RECOVERY_CONTEXT,
        post_final_gate_failure=True,
    )
    candidate = ConversationComposerCandidate(
        comment_text="この本文はboundary decisionへ保存しない。",
        composer_source="ai_generated",
        status="generated",
        composer_model=POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
        generation_method="phase20_13_post_final_gate_recovery_loop",
        composer_meta=meta,
    )

    decision = decide_gate_recovery_public_boundary(
        candidate=candidate,
        composer_meta=meta,
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    )

    assert_gate_recovery_public_boundary_decision(decision)
    assert decision["public_display_allowed"] is False
    assert decision["composer_model"] == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in decision["blockers"]
    assert decision["recovery_context"] == RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE


def test_p2_boundary_blocks_material_bound_surface_without_rebuilt_public_candidate() -> None:
    meta = {
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
        "phase20_15_gate_recovery_surface_binding": {
            "surface_generation_method": "material_bound_generic_surface",
            "public_candidate_rebuilt_after_recovery": False,
        },
    }

    decision = decide_gate_recovery_public_boundary(
        candidate={"composer_model": GATE_RECOVERY_MATERIAL_SURFACE_MODEL},
        composer_meta=meta,
    )

    assert decision["public_display_allowed"] is False
    assert "recovery_surface_source_lineage_missing" in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert validate_gate_recovery_public_boundary_decision(decision) == []


def test_p2_boundary_allows_explicit_low_information_public_observation_source() -> None:
    meta = {
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "candidate_lineage": {
            "original_candidate_source": "low_information_observation_composer",
            "public_candidate_rebuilt_after_recovery": True,
        },
    }
    candidate = ConversationComposerCandidate(
        comment_text="この本文はboundary decisionへ保存しない。",
        composer_source="low_information_observation_composer",
        status="generated",
        composer_model="low_information_observation_composer_recovery",
        generation_method="low_information_observation_recovery",
        composer_meta=meta,
    )

    decision = decide_gate_recovery_public_boundary(candidate=candidate, composer_meta=meta)

    assert_gate_recovery_public_boundary_decision(decision)
    assert decision["public_display_allowed"] is True
    assert decision["blockers"] == []
    assert gate_recovery_public_display_allowed(decision) is True
    assert all(value is False for value in decision["contract_flags"].values())


def test_p2_boundary_allows_explicit_complete_composer_public_observation_source() -> None:
    candidate = {
        "composer_model": "complete_initial_observation_composer",
        "generation_method": "complete_initial_composer",
        "composer_meta": {
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "source_phase": "CompleteInitialComposer",
        },
    }

    decision = decide_gate_recovery_public_boundary(candidate=candidate)

    assert_gate_recovery_public_boundary_decision(decision)
    assert decision["public_display_allowed"] is True
    assert decision["blockers"] == []
    assert decision["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER
    assert decision["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION


def test_p1_gate_recovery_material_surface_meta_is_diagnostic_role_not_public_observation() -> None:
    meta = _gate_recovery_composer_meta(
        material_quality="eligible",
        visible_slots=("relationship", "action", "emotion_direction"),
        unknown_slots=("cause",),
        relation_ids=("relationship_material",),
        policy="shorten_surface",
    )

    assert meta["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    assert meta["public_surface_role"] == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in meta["public_surface_blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in meta["public_surface_blockers"]
    assert BLOCKER_GATE_RECOVERY_INTERNAL_POLICY_SENTENCE_LEAK in meta["public_surface_blockers"]
    assert BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE in meta["public_surface_blockers"]


def test_p1_post_final_gate_recovery_meta_uses_post_final_public_leak_blocker() -> None:
    meta = _gate_recovery_composer_meta(
        material_quality="eligible",
        visible_slots=("relationship", "action", "emotion_direction"),
        unknown_slots=("cause",),
        relation_ids=("relationship_material",),
        policy="shorten_surface",
        recovery_context=POST_FINAL_GATE_RECOVERY_CONTEXT,
        post_final_gate_failure=True,
    )

    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in meta["public_surface_blockers"]
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in meta["public_surface_blockers"]


def test_p1_blocker_matrix_routes_gate_recovery_public_leak_to_boundary_owner() -> None:
    classified = classify_product_quality_blocker(
        BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
        family="daily_unpleasant",
    )

    assert classified["blocker_group"] == "surface_quality"
    assert classified["likely_owner_area"] == "surface_quality_gate_and_recovery_boundary"
    assert classified["severity"] == "critical"
    assert classified["release_blocking"] is True
    assert classified["public_contract_change_allowed"] is False
    assert classified["gate_relaxation_allowed"] is False


def test_p0_product_quality_event_marks_public_gate_recovery_material_surface_as_blocker() -> None:
    event = normalize_product_quality_event(
        run_id="p0_gate_recovery_public_leak",
        row_id="row_gate_recovery_material_surface",
        source_type="manual_internal_case",
        source_case_id="gate_recovery_material_surface_case",
        family="daily_unpleasant",
        comment_text="表示到達したが、これは本文を保存しない検査用文字列。",
        public_meta={"observation_status": "passed"},
        internal_meta={
            "observation_status": "passed",
            "composer_model": GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
        },
        composer_resolution={"rejection_reasons": ["default_limited_composer_feature_disabled"]},
        machine_metrics={
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 0,
            "template_major_count": 0,
            "safety_major_count": 0,
        },
    )

    assert event["public_display_reached"] is True
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in event["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in event["blockers"]
    assert BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION in event["blockers"]


def test_p3_phase20_5_gate_recovery_material_surface_is_blocked_by_public_boundary() -> None:
    result = _recovery_result(post_final=False)

    assert result.applied is False
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in result.blocked_reasons
    assert result.composer_candidate is None or result.composer_candidate.composer_model not in GATE_RECOVERY_MATERIAL_SURFACE_MODELS
    assert result.display_decision.observation_status != "passed"
    assert result.surface_binding_meta["public_display_allowed"] is False
    assert result.surface_binding_meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is False
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in result.surface_binding_meta["public_boundary_blockers"]
    assert "今回の入力では" not in result.display_decision.comment_text
    assert "Emlisから：" not in result.display_decision.comment_text


def test_p3_post_final_gate_recovery_material_surface_is_blocked_by_public_boundary() -> None:
    result = _recovery_result(post_final=True)

    assert result.applied is False
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in result.blocked_reasons
    assert result.composer_candidate is None or result.composer_candidate.composer_model != POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
    assert result.display_decision.observation_status != "passed"
    assert result.surface_binding_meta["public_display_allowed"] is False
    assert result.surface_binding_meta["gate_recovery_public_boundary_decision"]["recovery_context"] == RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in result.surface_binding_meta["public_boundary_blockers"]
    assert "今回の入力では" not in result.display_decision.comment_text
