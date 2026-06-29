# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 runtime backfill R2/R3 repair for H future-direction labelled surface.

R2/R3 must not add an H-case route or exact fixture branch.  The test fixes the
semantic-focus contract for eligible current-input material and verifies that
labelled two-stage recomposition carries that focus into visible surface text
without raw-body meta leakage.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_labelled_two_stage_surface_recomposition import (
    assert_labelled_two_stage_surface_recomposition_meta,
    build_labelled_two_stage_surface_recomposition_candidate,
    should_attempt_labelled_two_stage_surface_recomposition,
)
from emlis_ai_observation_eligibility_router import route_emlis_observation_material_eligibility
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    is_labelled_two_stage_comment_text_shape,
    public_surface_requirement_public_summary,
)
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision
import test_emlis_ai_hij_reception_required_regression_p8 as p8_regression

_TARGET_CASE_ID: Final = "p8_H_recovered_energy_future_direction"
_EXPECTED_FRAGMENTS: Final[tuple[str, ...]] = ("やってみたい", "次の頑張り方", "出来るかもしれない")
_FORBIDDEN_GENERIC_FRAGMENTS: Final[tuple[str, ...]] = (
    "生活について、平穏の動き",
    "次にどう扱うかを探している動き",
    "良かった動きも迷いもどちらかに寄せず",
)
_REQUIRED_SEMANTIC_MATERIAL_IDS: Final[frozenset[str]] = frozenset(
    {"recovered_energy", "future_intention", "value_preservation", "self_observation"}
)
_FORBIDDEN_META_KEYS: Final[frozenset[str]] = frozenset(
    {
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
)


def _target_case() -> p8_regression.P8HijCase:
    for case in p8_regression.P8_HIJ_CASES:
        if case.case_id == _TARGET_CASE_ID:
            return case
    raise AssertionError(f"target case not found: {_TARGET_CASE_ID}")


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _assert_body_free(value: Any) -> None:
    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            assert not (_FORBIDDEN_META_KEYS & set(node.keys()))
            for child in node.values():
                walk(child)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for child in node:
                walk(child)

    walk(value)


def _labelled_runtime_requirement(*, material_quality: str) -> dict[str, Any]:
    return public_surface_requirement_public_summary(
        {
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "two_stage_required": True,
            "plain_state_answer_allowed": False,
            "low_information_allowed": False,
            "required_comment_text_shape": {
                "kind": "labelled_two_stage",
                "starts_with": "見えたこと：\\n",
                "contains_boundary": "\\n\\nEmlisから：\\n",
                "observation_section_required": True,
                "reception_section_required": True,
                "comment_text_body_included": False,
            },
            "decision_sources": ["p4_runtime_backfill_r2_r3_test"],
            "material_quality_family": material_quality,
            "raw_input_included": False,
            "comment_text_body_included": False,
        }
    )


def _original_complete_initial_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text="この記録では、生活について、平穏の動きと次にどう扱うかを探している動きが重なっている状態として見えます。",
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p4-r2-r3-original",
        attempt_count=1,
        confidence=0.79,
        rejection_reasons=["visible_surface_acceptance_gate_failed"],
        request_schema_version="emlis.composer.request.v1",
        response_schema_version="cocolon.emlis.complete_composer.response.v1",
        fixed_string_renderer_used=False,
        composer_model="complete_initial_composer_v1",
        generation_method="complete_initial_composer",
        coverage_scope="current_input_only",
        generation_scope="current_input_only",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        used_relation_ids=list(_REQUIRED_SEMANTIC_MATERIAL_IDS),
    )


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["visible_surface_acceptance_gate_failed", "surface_specificity_missing"],
        trace_id="p4-r2-r3-surface-specificity",
    )


def test_p4_r2_r3_eligible_future_direction_focus_reaches_labelled_two_stage_surface_body_free() -> None:
    case = _target_case()
    current_input = p8_regression._current_input(case)
    material_route = route_emlis_observation_material_eligibility(current_input)
    material_meta = material_route.as_meta()
    assert material_meta["material_quality"] == "eligible"
    assert _REQUIRED_SEMANTIC_MATERIAL_IDS.issubset(set(material_meta["relation_material_ids"]))

    requirement = _labelled_runtime_requirement(material_quality="eligible")
    original_candidate = _original_complete_initial_candidate()
    display_decision = _surface_failed_display_decision()

    assert should_attempt_labelled_two_stage_surface_recomposition(
        current_input=current_input,
        material_route=material_route,
        surface_requirement=requirement,
        original_composer_candidate=original_candidate,
        original_display_decision=display_decision,
    )

    candidate, reasons = build_labelled_two_stage_surface_recomposition_candidate(
        current_input=current_input,
        material_route=material_route,
        surface_requirement=requirement,
        original_composer_candidate=original_candidate,
        original_display_decision=display_decision,
        trace_id="p4-r2-r3-h-future-direction",
        recovery_context="pre_public_display_gate",
    )

    assert candidate is not None
    assert "labelled_two_stage_surface_recomposition_candidate_built" in reasons
    assert candidate.composer_meta["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert is_labelled_two_stage_comment_text_shape(candidate.comment_text)
    assert candidate.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in candidate.comment_text
    for fragment in _EXPECTED_FRAGMENTS:
        assert fragment in candidate.comment_text
    for fragment in _FORBIDDEN_GENERIC_FRAGMENTS:
        assert fragment not in candidate.comment_text

    meta = candidate.composer_meta
    assert_labelled_two_stage_surface_recomposition_meta(meta)
    labelled_summary = _as_mapping(meta["labelled_two_stage_surface_recomposition_summary"])
    focus = _as_mapping(labelled_summary["eligible_surface_semantic_focus"])
    assert labelled_summary["eligible_surface_semantic_focus_connected"] is True
    assert focus["schema_version"] == "cocolon.emlis.surface_semantic_focus.v1"
    assert focus["semantic_focus_id"] == "recovered_energy_future_direction"
    assert _REQUIRED_SEMANTIC_MATERIAL_IDS.issubset(set(_as_sequence(focus["semantic_material_ids"])))
    assert "show_future_direction_as_next_effort" in focus["surface_role_requirements"]
    assert "show_self_possibility_without_prediction" in focus["surface_role_requirements"]
    assert "category_emotion_action_generic" in focus["blocked_generic_signature_ids"]
    assert meta["implementation_boundary"]["case_specific_route_used"] is False
    assert meta["implementation_boundary"]["fixed_sentence_template_used"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    _assert_body_free(meta)
