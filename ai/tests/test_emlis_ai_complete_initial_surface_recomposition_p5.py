# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_complete_initial_surface_recomposition import (
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION,
    build_complete_initial_surface_recomposition_candidate,
    complete_initial_surface_recomposition_public_summary,
    should_attempt_complete_initial_surface_recomposition,
)
from emlis_ai_gate_recovery_public_candidate_builder import build_public_candidate_after_gate_recovery
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_types import DisplayDecision, SafetyBoundaryReport


def _availability(**overrides: Any) -> dict[str, Any]:
    value = {
        "schema_version": "cocolon.emlis.complete_initial_surface_availability.v1",
        "source_phase": "PublicObservationRecovery_P4_CompleteInitialSurfaceAvailability",
        "complete_initial_client_resolved": True,
        "candidate_generation_attempted": True,
        "candidate_generated_before_display_gate": False,
        "candidate_status": "unavailable",
        "composer_source": "unavailable",
        "first_blocker_family": "source_unavailable",
        "first_blocker_code": "complete_initial_surface_unavailable",
        "material_sufficient": True,
        "material_quality_family": "sufficient_input_material",
        "surface_requirement_family": "labelled_two_stage",
        "recovery_lane": "complete_initial_surface_recomposition",
        "normal_observation_rebuild_allowed": False,
        "normal_observation_rebuild_blocker": "source_unavailable_not_rebuildable",
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_in_meta": False,
        "case_specific_route_used": False,
    }
    value.update(overrides)
    return value


def _surface_requirement(**overrides: Any) -> dict[str, Any]:
    value = {
        "schema_version": "cocolon.emlis.public_surface_requirement.v1",
        "source_phase": "PublicObservationRecovery_P1_SurfaceRequirementDecision",
        "surface_requirement_family": "labelled_two_stage",
        "two_stage_required": True,
        "plain_state_answer_allowed": False,
        "low_information_allowed": False,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_in_meta": False,
    }
    value.update(overrides)
    return value


def _material_route(**overrides: Any) -> dict[str, Any]:
    value = {
        "material_quality": "eligible",
        "visible_material_slots": ["emotion", "memo_action", "category"],
        "generic_relation_material_ids": ["p5_relation"],
        "safety_triage_kind": "safe_observation",
    }
    value.update(overrides)
    return value


def _current_input() -> dict[str, Any]:
    return {
        "memo": "この本文はmetaへ保存しない。自分の内側が不安で分からない。",
        "memo_action": "整理して書いてみる。",
        "emotions": ["不安"],
        "category": ["自分"],
    }


def _assert_body_free(value: Any) -> None:
    forbidden = {
        "raw_input",
        "current_input",
        "memo",
        "memo_action",
        "comment_text",
        "candidate_comment_text",
        "public_comment_text",
        "candidate_body",
        "candidateBody",
        "realized_text",
        "surface_text",
        "body",
        "text",
    }
    if isinstance(value, Mapping):
        assert not (set(value.keys()) & forbidden)
        for child in value.values():
            _assert_body_free(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _assert_body_free(child)


def test_p5_builds_labelled_two_stage_candidate_from_complete_surface_realizer_without_body_meta() -> None:
    candidate, reasons = build_complete_initial_surface_recomposition_candidate(
        current_input=_current_input(),
        material_route=_material_route(),
        surface_requirement=_surface_requirement(),
        availability_summary=_availability(),
        trace_id="p5-direct",
        recovery_context="pre_public_display_gate",
    )

    assert reasons == ["complete_initial_surface_recomposition_candidate_built"]
    assert candidate is not None
    assert candidate.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in candidate.comment_text
    assert candidate.composer_source == "ai_generated"
    assert candidate.composer_model == "complete_initial_surface_recomposition_v1"
    assert candidate.generation_method == "complete_initial_recompose_from_material_after_source_unavailable"
    assert candidate.composer_meta["schema_version"] == COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION
    assert candidate.composer_meta["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    assert candidate.composer_meta["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert candidate.composer_meta["normal_observation_rebuild_used"] is False
    assert candidate.composer_meta["gate_recovery_material_surface_used"] is False
    assert candidate.composer_meta["candidate_body_in_meta"] is False
    assert candidate.composer_meta["case_specific_route_used"] is False
    assert candidate.composer_meta["body_boundary"]["candidate_body_in_meta"] is False
    assert candidate.composer_meta["complete_surface_recomposition_summary"]["candidate_body_in_meta"] is False
    assert candidate.composer_meta["complete_surface_recomposition_summary"]["complete_sentence_plan_connected"] is True
    assert candidate.composer_meta["complete_surface_recomposition_summary"]["complete_surface_realizer_connected"] is True
    assert candidate.composer_meta["implementation_boundary"]["fixed_fallback_used"] is False
    assert candidate.composer_meta["implementation_boundary"]["fixed_sentence_template_used"] is False
    assert candidate.used_evidence_span_ids
    _assert_body_free(candidate.composer_meta)


def test_p5_builder_selects_complete_initial_surface_recomposition_for_source_unavailable_lane() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=_current_input(),
        material_route=_material_route(),
        original_composer_candidate=None,
        original_display_decision=DisplayDecision(
            observation_status="unavailable",
            comment_text="",
            rejection_reasons=["complete_initial_surface_unavailable"],
            trace_id="p5-builder",
        ),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={"surface_requirement": _surface_requirement()},
        trace_id="p5-builder",
        complete_initial_surface_availability_summary=_availability(),
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    assert result.selection_kind == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    assert result.blocked_reasons == ()
    assert result.candidate.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in result.candidate.comment_text
    meta = result.as_meta()
    assert meta["candidate_available"] is True
    assert meta["gate_recovery_public_boundary_decision"]["public_display_allowed"] is True
    assert meta["source_kind"] != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert meta["contract_flags"]["candidate_body_in_meta"] is False
    assert meta["contract_flags"]["case_specific_route_used"] is False
    _assert_body_free(meta)
    _assert_body_free(result.candidate.composer_meta)



def test_p5_allows_limited_source_unavailable_recomposition_without_complete_client_resolution() -> None:
    availability = _availability(
        complete_initial_client_resolved=False,
        candidate_generation_attempted=False,
        candidate_generated_before_display_gate=False,
        candidate_status="unavailable",
        composer_source="unavailable",
        first_blocker_family="source_unavailable",
        first_blocker_code="limited_composer_shallow_empty_candidate",
        material_quality_family="eligible",
        surface_requirement_family="labelled_two_stage",
        recovery_lane="complete_initial_surface_recomposition",
        normal_observation_rebuild_allowed=False,
    )
    material = _material_route(
        material_quality="eligible",
        safety_triage_kind="safe_observation",
        visible_material_slots=["relationship", "action", "change", "value"],
        relation_material_ids=[
            "relationship_end",
            "support_from_other",
            "gratitude_or_return_intent",
        ],
    )

    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=availability,
        surface_requirement=None,
        material_route=material,
    ) is True
    candidate, reasons = build_complete_initial_surface_recomposition_candidate(
        current_input={
            "memo": "関係の区切りと友達から受け取った優しさを、次の形で返したい。",
            "memo_action": "別れたあとも友達が優しくしてくれていることを整理する。",
            "emotions": ["喜び"],
            "category": ["恋愛", "人間関係", "価値観"],
        },
        material_route=material,
        surface_requirement=None,
        availability_summary=availability,
        trace_id="p5-limited-source-unavailable",
        recovery_context="pre_public_display_gate",
    )

    assert reasons == ["complete_initial_surface_recomposition_candidate_built"]
    assert candidate is not None
    assert candidate.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in candidate.comment_text
    assert candidate.composer_meta["surface_requirement_family"] == "labelled_two_stage"
    assert candidate.composer_meta["surface_requirement"]["decision_sources"] == [
        "availability_surface_requirement_family"
    ]
    assert candidate.composer_meta["source_unavailable_recovered"] is True
    assert candidate.composer_meta["normal_observation_rebuild_used"] is False
    assert candidate.composer_meta["gate_recovery_material_surface_used"] is False
    assert candidate.composer_meta["candidate_body_in_meta"] is False
    assert candidate.composer_meta["case_specific_route_used"] is False
    summary = complete_initial_surface_recomposition_public_summary(candidate.composer_meta)
    assert summary["candidate_body_in_meta"] is False
    assert summary["case_specific_route_used"] is False
    _assert_body_free(candidate.composer_meta)


def test_p5_keeps_limited_source_unavailable_recomposition_closed_for_blocked_conditions() -> None:
    base_availability = _availability(
        complete_initial_client_resolved=False,
        candidate_generation_attempted=False,
        candidate_generated_before_display_gate=False,
        candidate_status="unavailable",
        composer_source="unavailable",
        first_blocker_family="source_unavailable",
        first_blocker_code="limited_composer_shallow_empty_candidate",
        material_quality_family="eligible",
        surface_requirement_family="labelled_two_stage",
        recovery_lane="complete_initial_surface_recomposition",
        normal_observation_rebuild_allowed=False,
    )
    material = _material_route(
        material_quality="eligible",
        safety_triage_kind="safe_observation",
        visible_material_slots=["relationship", "action", "change", "value"],
        relation_material_ids=["relationship_end"],
    )

    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=base_availability,
        surface_requirement=_surface_requirement(),
        material_route=material,
        safety_requires_block=True,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=base_availability,
        surface_requirement=_surface_requirement(),
        material_route=material,
        reply_timeout_or_error=True,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=base_availability,
        surface_requirement=_surface_requirement(),
        material_route=material,
        composer_disabled=True,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=dict(base_availability, first_blocker_family="infrastructure_error"),
        surface_requirement=_surface_requirement(),
        material_route=material,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=dict(base_availability, first_blocker_code="reply_timeout_or_error"),
        surface_requirement=_surface_requirement(),
        material_route=material,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=dict(base_availability, candidate_generated_before_display_gate=True),
        surface_requirement=_surface_requirement(),
        material_route=material,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=dict(base_availability, normal_observation_rebuild_allowed=True),
        surface_requirement=_surface_requirement(),
        material_route=material,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=base_availability,
        surface_requirement=_surface_requirement(surface_requirement_family="safety_blocked"),
        material_route=material,
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=base_availability,
        surface_requirement=_surface_requirement(),
        material_route=_material_route(material_quality="low_information"),
    ) is False


def test_p5_does_not_attempt_recomposition_for_low_information_or_generated_candidate() -> None:
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=_availability(material_sufficient=False),
        surface_requirement=_surface_requirement(),
        material_route=_material_route(),
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=_availability(candidate_generated_before_display_gate=True),
        surface_requirement=_surface_requirement(),
        material_route=_material_route(),
    ) is False
    assert should_attempt_complete_initial_surface_recomposition(
        availability_summary=_availability(),
        surface_requirement=_surface_requirement(),
        material_route=_material_route(material_quality="low_information"),
    ) is False
