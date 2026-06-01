# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-15 Gate Recovery surface binding / fixed fallback prevention tests."""

import pytest

from emlis_ai_gate_recovery_loop import (
    GATE_RECOVERY_SURFACE_BINDING_META_KEY,
    GATE_RECOVERY_SURFACE_BINDING_SCHEMA_VERSION,
    GATE_RECOVERY_SURFACE_BINDING_SOURCE_PHASE,
    GATE_RECOVERY_SURFACE_REPETITION_QA_SCHEMA_VERSION,
    assert_gate_recovery_surface_binding_meta,
    assert_gate_recovery_surface_repetition_qa_report,
    build_gate_recovery_surface_binding_meta,
    build_gate_recovery_surface_repetition_qa_report,
    recover_emlis_gate_failure,
)
from emlis_ai_types import DisplayDecision, GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


def _failed_display(*reasons: str, status: str = "rejected") -> DisplayDecision:
    return DisplayDecision(
        observation_status=status,
        comment_text="",
        rejection_reasons=list(reasons),
        trace_id="phase20-15-gate-recovery-surface",
        gate_trace={
            "visible_surface_acceptance_gate": {
                "passed": False,
                "action": "rerender_surface",
                "classification": "repair_required",
                "rejection_reasons": list(reasons),
            }
        },
    )


class _MaterialRoute:
    material_quality = "eligible"
    visible_material_slots = ("event", "action", "emotion_direction", "change", "value")
    unknown_slots = ("cause",)
    generic_relation_material_ids = ("self_understanding_learning", "value_or_self_understanding_material")

    def as_meta(self) -> dict:
        return {
            "material_quality": self.material_quality,
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            "safety_triage_kind": "safe_observation",
        }


class _LowInformationRoute(_MaterialRoute):
    material_quality = "low_information"
    visible_material_slots = ("emotion_direction",)
    unknown_slots = ("cause", "event")
    generic_relation_material_ids: tuple[str, ...] = ()


class _RelationshipRoute(_MaterialRoute):
    material_quality = "eligible"
    visible_material_slots = ("relationship", "emotion_direction")
    unknown_slots = ("cause",)
    generic_relation_material_ids = ("relationship_end", "support_received_material")


class _LimitedGroundingRoute(_MaterialRoute):
    material_quality = "limited_grounding"
    visible_material_slots = ("emotion_direction",)
    unknown_slots = ("cause", "event")
    generic_relation_material_ids: tuple[str, ...] = ()


def _result_for_route(route: _MaterialRoute):
    return recover_emlis_gate_failure(
        current_input={
            "memo": "これはraw inputとしてそのまま出してはいけない本文です。",
            "memo_action": "これも本文へechoしない行動欄です。",
            "emotions": ["自己理解"],
            "category": ["学習"],
        },
        display_decision=_failed_display("surface_relation_skeleton_major", "phase20_15_probe"),
        reader_report=ListenerReaderReport(
            understandable=False,
            addressee_clear=False,
            speaker_integrity_ok=True,
            conversational=False,
            report_like=True,
            rejection_reasons=["original_gate_failed"],
        ),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["graph_evidence_not_used"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["phase20_15_probe"]),
        material_route=route,
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="phase20-15-surface-binding",
        post_final_gate_failure=route.material_quality == "low_information",
        allow_low_information_post_final_recovery=route.material_quality == "low_information",
    )


def test_phase20_15_builds_meta_only_surface_binding_from_material_and_relation_ids() -> None:
    meta = build_gate_recovery_surface_binding_meta(
        material_quality="eligible",
        visible_slots=("event", "action", "value"),
        unknown_slots=("cause",),
        relation_ids=("self_understanding_learning", "value_or_self_understanding_material"),
    )

    assert_gate_recovery_surface_binding_meta(meta)
    assert meta["schema_version"] == GATE_RECOVERY_SURFACE_BINDING_SCHEMA_VERSION
    assert meta["source_phase"] == GATE_RECOVERY_SURFACE_BINDING_SOURCE_PHASE
    assert meta["surface_generation_method"] == "material_bound_generic_surface"
    assert meta["generic_sentence_plan_used"] is True
    assert meta["visible_material_slot_count"] == 3
    assert meta["unknown_slot_count"] == 1
    assert meta["relation_material_id_count"] == 2
    assert meta["surface_family_id"] == "self_understanding_current_input_material"
    assert meta["closing_family_id"] == "self_understanding_non_conclusive_current_input_only"
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["fixed_fallback_used"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert meta["case_specific_route_used"] is False
    assert meta["exact_fixture_surface_used"] is False


def test_phase20_15_recovery_candidate_carries_surface_binding_without_fixed_fallback_or_raw_echo() -> None:
    result = _result_for_route(_MaterialRoute())

    assert result.applied is True
    assert result.composer_candidate is not None
    composer_meta = result.composer_candidate.composer_meta
    binding = composer_meta[GATE_RECOVERY_SURFACE_BINDING_META_KEY]

    assert_gate_recovery_surface_binding_meta(binding)
    assert composer_meta["gate_recovery_surface_binding"] == binding
    assert composer_meta["gate_recovery_surface_binding_ready"] is True
    assert composer_meta["surface_generation_method"] == "material_bound_generic_surface"
    assert composer_meta["surface_family_id"] == binding["surface_family_id"]
    assert composer_meta["closing_family_id"] == binding["closing_family_id"]
    assert binding["relation_family_ids"] == ["self_understanding_learning", "value_or_self_understanding_material"]
    assert binding["fixed_fallback_used"] is False
    assert binding["fixed_sentence_template_used"] is False
    assert binding["exact_fixture_surface_used"] is False

    comment_text = result.display_decision.comment_text
    assert "見えたこと：" in comment_text
    assert "Emlisから：" in comment_text
    assert "これはraw inputとしてそのまま出してはいけない本文" not in comment_text
    assert "これも本文へechoしない行動欄" not in comment_text


def test_phase20_15_surface_repetition_qa_detects_repeated_closing_and_surface_family_without_exact_text() -> None:
    repeated = [
        build_gate_recovery_surface_binding_meta(
            material_quality="eligible",
            visible_slots=("event", "action"),
            unknown_slots=("cause",),
            relation_ids=("self_understanding_learning",),
        )
        for _ in range(3)
    ]
    report = build_gate_recovery_surface_repetition_qa_report(repeated)

    assert_gate_recovery_surface_repetition_qa_report(report)
    assert report["schema_version"] == GATE_RECOVERY_SURFACE_REPETITION_QA_SCHEMA_VERSION
    assert report["surface_count"] == 3
    assert report["longest_same_surface_family_run"] == 3
    assert report["longest_same_closing_family_run"] == 3
    assert report["same_surface_family_repetition_detected"] is True
    assert report["same_closing_family_repetition_detected"] is True
    assert report["requires_surface_quality_review"] is True
    assert report["fixed_fallback_repetition_detected"] is False
    assert report["raw_input_included"] is False
    assert report["comment_text_body_included"] is False


def test_phase20_15_surface_repetition_qa_allows_diverse_material_bound_families() -> None:
    bindings = [
        build_gate_recovery_surface_binding_meta(
            material_quality="low_information",
            visible_slots=("emotion_direction",),
            unknown_slots=("cause",),
            relation_ids=(),
        ),
        build_gate_recovery_surface_binding_meta(
            material_quality="eligible",
            visible_slots=("relationship",),
            unknown_slots=("cause",),
            relation_ids=("relationship_end",),
        ),
        build_gate_recovery_surface_binding_meta(
            material_quality="eligible",
            visible_slots=("value",),
            unknown_slots=("cause",),
            relation_ids=("self_understanding_learning",),
        ),
        build_gate_recovery_surface_binding_meta(
            material_quality="limited_grounding",
            visible_slots=("emotion_direction",),
            unknown_slots=("cause",),
            relation_ids=(),
        ),
    ]
    report = build_gate_recovery_surface_repetition_qa_report(bindings)

    assert_gate_recovery_surface_repetition_qa_report(report)
    assert report["surface_count"] == 4
    assert report["unique_surface_family_count"] == 4
    assert report["unique_closing_family_count"] == 4
    assert report["same_surface_family_repetition_detected"] is False
    assert report["same_closing_family_repetition_detected"] is False
    assert report["requires_surface_quality_review"] is False
    assert report["fixed_fallback_used"] is False
    assert report["public_response_key_change"] is False


@pytest.mark.parametrize(
    "bad_key",
    [
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "case_specific_route_used",
        "exact_fixture_surface_used",
        "raw_input_included",
        "comment_text_body_included",
    ],
)
def test_phase20_15_surface_binding_rejects_fixed_fallback_case_route_and_text_payload_flags(bad_key: str) -> None:
    meta = build_gate_recovery_surface_binding_meta(
        material_quality="eligible",
        visible_slots=("event",),
        unknown_slots=("cause",),
        relation_ids=("self_understanding_learning",),
    )
    meta[bad_key] = True

    with pytest.raises(ValueError):
        assert_gate_recovery_surface_binding_meta(meta)
