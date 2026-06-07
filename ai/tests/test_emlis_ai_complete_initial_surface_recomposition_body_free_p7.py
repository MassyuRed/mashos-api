# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 7 guards for body-free complete-initial recomposition meta.

The public ``comment_text`` candidate may contain generated public body text.
Its lineage / recovery-plan / recomposition meta must not serialize raw input,
the generated candidate body, or a Gate Recovery material surface body.
"""

from collections.abc import Mapping, Sequence
from typing import Any
import json

from emlis_ai_complete_initial_surface_recomposition import (
    build_complete_initial_surface_recomposition_candidate,
    complete_initial_surface_recomposition_public_summary,
)
from emlis_ai_gate_recovery_public_candidate_builder import (
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
)
from emlis_ai_types import DisplayDecision, SafetyBoundaryReport

_RAW_SENTINEL = "SHOULD_NOT_LEAK_RAW_INPUT_STEP7"
_CANDIDATE_SENTINEL = "SHOULD_NOT_LEAK_CANDIDATE_BODY_STEP7"

_FORBIDDEN_EXACT_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_comment_text",
    "public_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "surfaceText",
    "realized_text",
    "realizedText",
    "display_text",
    "displayText",
    "observation_text",
    "observationText",
    "reception_text",
    "receptionText",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "body",
    "text",
}


def _availability(**overrides: Any) -> dict[str, Any]:
    value = {
        "schema_version": "cocolon.emlis.complete_initial_surface_availability.v1",
        "source_phase": "PublicObservationRecovery_P4_CompleteInitialSurfaceAvailability",
        "complete_initial_client_resolved": False,
        "candidate_generation_attempted": False,
        "candidate_generated_before_display_gate": False,
        "candidate_status": "unavailable",
        "composer_source": "unavailable",
        "first_blocker_family": "source_unavailable",
        "first_blocker_code": "limited_composer_shallow_empty_candidate",
        "material_sufficient": True,
        "material_quality_family": "eligible",
        "surface_requirement_family": "labelled_two_stage",
        "recovery_lane": "complete_initial_surface_recomposition",
        "normal_observation_rebuild_allowed": False,
        "normal_observation_rebuild_blocker": "source_unavailable_not_rebuildable",
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
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
        "decision_sources": ["step7_body_free_regression"],
        "material_quality_family": "eligible",
        "input_material_classification": {
            "memo_present": True,
            "memo_action_present": True,
            "emotions_present": True,
            "categories_present": True,
            "memo_text_len": 120,
            "memo_action_text_len": 40,
            "high_information_input": True,
            "low_information_material": False,
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    value.update(overrides)
    return value


def _material_route(**overrides: Any) -> dict[str, Any]:
    value = {
        "material_quality": "eligible",
        "safety_triage_kind": "safe_observation",
        "visible_material_slots": ["relationship", "action", "change", "value"],
        "unknown_slots": ["cause"],
        "relation_material_ids": [
            "relationship_end",
            "support_from_other",
            "gratitude_or_return_intent",
        ],
    }
    value.update(overrides)
    return value


def _current_input() -> dict[str, Any]:
    return {
        "memo": f"{_RAW_SENTINEL} 関係の区切りと受け取った優しさを、次の形で返したい。",
        "memo_action": f"{_RAW_SENTINEL} 別れたあとも友達が優しくしてくれていることを整理する。",
        "emotions": ["喜び"],
        "category": ["恋愛", "人間関係", "価値観"],
    }


def _assert_body_free_meta(value: Any) -> None:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    assert _RAW_SENTINEL not in serialized
    assert _CANDIDATE_SENTINEL not in serialized
    if isinstance(value, Mapping):
        assert not (set(value.keys()) & _FORBIDDEN_EXACT_KEYS)
        for child in value.values():
            _assert_body_free_meta(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _assert_body_free_meta(child)


def test_complete_initial_recomposition_candidate_meta_ignores_raw_source_payloads() -> None:
    candidate, reasons = build_complete_initial_surface_recomposition_candidate(
        current_input=_current_input(),
        material_route=_material_route(
            raw_input=_RAW_SENTINEL,
            comment_text=_CANDIDATE_SENTINEL,
            candidate_body=_CANDIDATE_SENTINEL,
        ),
        surface_requirement=_surface_requirement(
            raw_input=_RAW_SENTINEL,
            comment_text=_CANDIDATE_SENTINEL,
            candidate_body=_CANDIDATE_SENTINEL,
            raw_input_included=True,
            comment_text_body_included=True,
            candidate_body_in_meta=True,
        ),
        availability_summary=_availability(
            raw_input=_RAW_SENTINEL,
            comment_text=_CANDIDATE_SENTINEL,
            candidate_body=_CANDIDATE_SENTINEL,
            raw_input_included=True,
            comment_text_body_included=True,
            candidate_body_in_meta=True,
        ),
        trace_id="step7-direct-body-free",
        recovery_context="pre_public_display_gate",
    )

    assert reasons == ["complete_initial_surface_recomposition_candidate_built"]
    assert candidate is not None
    assert candidate.comment_text.strip()
    assert candidate.composer_meta["raw_input_included"] is False
    assert candidate.composer_meta["comment_text_body_included"] is False
    assert candidate.composer_meta["candidate_body_in_meta"] is False
    assert candidate.composer_meta["body_boundary"]["raw_input_included"] is False
    assert candidate.composer_meta["body_boundary"]["comment_text_body_included"] is False
    assert candidate.composer_meta["body_boundary"]["candidate_body_in_meta"] is False
    assert candidate.composer_meta["gate_recovery_material_surface_used"] is False
    assert candidate.composer_meta["normal_observation_rebuild_used"] is False
    assert candidate.composer_meta["case_specific_route_used"] is False

    summary = complete_initial_surface_recomposition_public_summary(candidate.composer_meta)
    assert summary["body_free"] is True
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["candidate_body_in_meta"] is False
    assert summary["gate_recovery_material_surface_used"] is False
    assert summary["normal_observation_rebuild_used"] is False
    assert summary["case_specific_route_used"] is False
    _assert_body_free_meta(candidate.composer_meta)
    _assert_body_free_meta(summary)


def test_gate_recovery_candidate_builder_meta_stays_body_free_for_recomposition_lane() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=_current_input(),
        material_route=_material_route(raw_input=_RAW_SENTINEL, comment_text=_CANDIDATE_SENTINEL),
        original_composer_candidate=None,
        original_display_decision=DisplayDecision(
            observation_status="unavailable",
            comment_text="",
            rejection_reasons=["limited_composer_shallow_empty_candidate"],
            trace_id="step7-builder-body-free",
        ),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "surface_requirement": _surface_requirement(
                raw_input=_RAW_SENTINEL,
                comment_text=_CANDIDATE_SENTINEL,
                candidate_body=_CANDIDATE_SENTINEL,
                raw_input_included=True,
                comment_text_body_included=True,
            ),
            "input_material_summary": {
                "material_quality": "eligible",
                "visible_material_slots": ["relationship", "action", "change", "value"],
                "relation_material_ids": ["relationship_end"],
                "raw_input": _RAW_SENTINEL,
                "comment_text": _CANDIDATE_SENTINEL,
                "raw_input_included": True,
                "comment_text_body_included": True,
            },
            "failed_gate_summary": {
                "display_status_before_recovery": "unavailable",
                "rejection_reasons": ["limited_composer_shallow_empty_candidate"],
                "comment_text": _CANDIDATE_SENTINEL,
            },
            "raw_input": _RAW_SENTINEL,
            "candidate_body": _CANDIDATE_SENTINEL,
        },
        trace_id="step7-builder-body-free",
        complete_initial_surface_availability_summary=_availability(
            raw_input=_RAW_SENTINEL,
            comment_text=_CANDIDATE_SENTINEL,
            candidate_body=_CANDIDATE_SENTINEL,
            raw_input_included=True,
            comment_text_body_included=True,
        ),
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE

    result_meta = result.as_meta()
    candidate_meta = result.candidate.composer_meta
    assert result_meta["contract_flags"]["raw_input_included"] is False
    assert result_meta["contract_flags"]["comment_text_body_included"] is False
    assert result_meta["contract_flags"]["candidate_body_in_meta"] is False
    assert result_meta["contract_flags"]["gate_recovery_material_surface_used"] is False
    assert result_meta["contract_flags"]["normal_observation_rebuild_used"] is False
    assert result_meta["contract_flags"]["case_specific_route_used"] is False
    assert candidate_meta["raw_input_included"] is False
    assert candidate_meta["comment_text_body_included"] is False
    assert candidate_meta["candidate_body_in_meta"] is False
    assert candidate_meta["public_candidate_builder"]["raw_input_included"] is False
    assert candidate_meta["public_candidate_builder"]["comment_text_body_included"] is False
    _assert_body_free_meta(result_meta)
    _assert_body_free_meta(candidate_meta)
