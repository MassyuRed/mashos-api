# -*- coding: utf-8 -*-
from __future__ import annotations

"""P2 recovery-routing tests for limited_grounding reception.

P2 removes ``limited_grounding`` from the low-information recovery lane.  The
public-surface requirement layer already marks limited grounding as labelled
reception required; this file fixes the next boundary so an explicit or default
recovery plan cannot select low-information question surface for that material.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_gate_recovery_public_candidate_builder import (
    NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    build_emlis_input_material_bundle,
)
from emlis_ai_public_surface_requirement import SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision, SafetyBoundaryReport


_I_CURRENT_INPUT: dict[str, object] = {
    "memo": (
        "沢山甘えられて寂しい時にそばに居てくれるような\n"
        "存在やっぱりいいなって思う 気力が出てきた時は恋愛も\n"
        "したくなる。でもやる気力が出てきたのが嬉しいし\n"
        "このタイミング逃したら、また気力なくなって\n"
        "何も出来なくなくからこのタイミングでいろんな事に\n"
        "挑戦して、いずれは素敵な人と出会えたらいいな"
    ),
    "memo_action": "",
    "emotion_details": [{"type": "平穏", "strength": "medium"}],
    "category": ["生活", "人生"],
}

_TRUE_LOW_INFORMATION_INPUT: dict[str, object] = {
    "memo": "疲れた",
    "memo_action": "",
    "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
    "category": ["生活"],
}


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "surface_relation_skeleton_major",
        ],
        trace_id="p2-limited-grounding-reception-routing",
    )


def _original_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text="気力が戻ってきたことと、何かに挑戦したい気持ちが残っています。",
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p2-limited-original",
        attempt_count=1,
        confidence=0.73,
        response_schema_version="cocolon.emlis.complete_composer.response.v1",
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
    )


def _normal_rebuild_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text="この記録では、気力が戻りかけた中で次の動きを探している状態に見えます。",
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p2-limited-normal-rebuild",
        attempt_count=1,
        confidence=0.75,
        response_schema_version="cocolon.emlis.phase20_8.normal_observation_rebuild.response.v1",
        composer_model=NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
        generation_method="normal_observation_rebuild_after_surface_gate_failure",
        coverage_scope="current_input_normal_observation_rebuild",
        generation_scope="current_input_only",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_lineage": {
                "public_candidate_rebuilt_after_recovery": True,
            },
        },
    )


def _low_information_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=(
            "まだ詳しい出来事までは見えていません。"
            "詳しく残せそうなら、何があったか残してみませんか。"
        ),
        composer_source="low_information_observation_composer",
        status="generated",
        trace_id="p2-limited-low-information-candidate",
        attempt_count=1,
        confidence=0.62,
        response_schema_version="cocolon.emlis.phase20_6.low_information_recovery.response.v1",
        composer_model="low_information_observation_composer_recovery",
        generation_method="low_information_observation_recovery_after_gate_recovery",
        coverage_scope="current_input_low_information_recovery",
        generation_scope="current_input_only",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_lineage": {
                "public_candidate_rebuilt_after_recovery": True,
            },
        },
    )


def _assert_body_free(meta: Mapping[str, Any]) -> None:
    forbidden = {
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

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & forbidden)
            for child in value.values():
                walk(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                walk(child)

    walk(meta)


def test_p2_limited_grounding_default_plan_targets_labelled_recomposition_not_low_information() -> None:
    bundle = build_emlis_input_material_bundle(_I_CURRENT_INPUT)
    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING

    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_I_CURRENT_INPUT),
        material_route=bundle.as_meta(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p2-limited-default-plan-targets-labelled",
    )

    meta = result.as_meta()
    plan = meta["recovery_plan"]
    fallback_order = plan["fallback_public_candidate_source_order"]
    assert plan["surface_requirement"]["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert plan["surface_requirement"]["material_quality_family"] == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert plan["surface_requirement"]["low_information_allowed"] is False
    assert plan["target_public_candidate_source"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER not in fallback_order
    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE not in fallback_order
    assert BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED in plan[
        "blockers_if_no_public_candidate"
    ]
    _assert_body_free(meta)


def test_p2_limited_grounding_explicit_low_information_plan_is_rerouted_and_not_selected() -> None:
    bundle = build_emlis_input_material_bundle(_I_CURRENT_INPUT)
    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING

    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_I_CURRENT_INPUT),
        material_route=bundle.as_meta(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
                CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            ],
        },
        low_information_candidate=_low_information_candidate(),
        normal_observation_rebuild_candidate=_normal_rebuild_candidate(),
        trace_id="p2-limited-explicit-low-information-plan-rerouted",
    )

    meta = result.as_meta()
    plan = meta["recovery_plan"]
    assert plan["target_public_candidate_source"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER not in plan[
        "fallback_public_candidate_source_order"
    ]
    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE not in plan[
        "fallback_public_candidate_source_order"
    ]
    assert result.source_kind != CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert result.source_kind != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    if result.candidate is not None:
        assert result.candidate.composer_model != "low_information_observation_composer_recovery"
        assert result.candidate.composer_model != NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
    _assert_body_free(meta)


def test_p2_true_low_information_stays_on_low_information_recovery_lane() -> None:
    bundle = build_emlis_input_material_bundle(_TRUE_LOW_INFORMATION_INPUT)
    assert bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION

    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_TRUE_LOW_INFORMATION_INPUT),
        material_route=bundle.as_meta(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        low_information_candidate=_low_information_candidate(),
        trace_id="p2-true-low-information-stays-low-information",
    )

    meta = result.as_meta()
    plan = meta["recovery_plan"]
    assert plan["input_material_summary"]["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert plan["target_public_candidate_source"] == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER in plan[
        "fallback_public_candidate_source_order"
    ]
    assert result.source_kind == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    _assert_body_free(meta)
