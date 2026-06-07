# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 tests for limited_grounding labelled two-stage recomposition.

P3 keeps true low-information out of P6, while allowing limited_grounding inputs
that already require labelled reception to be rebuilt as a two-stage public
candidate.  The candidate must be body-free in meta and must not fall back to a
low-information question surface.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_gate_recovery_public_candidate_builder import build_public_candidate_after_gate_recovery
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    build_emlis_input_material_bundle,
)
from emlis_ai_labelled_two_stage_surface_recomposition import (
    assert_labelled_two_stage_surface_recomposition_meta,
    build_labelled_two_stage_surface_recomposition_candidate,
    should_attempt_labelled_two_stage_surface_recomposition,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    is_labelled_two_stage_comment_text_shape,
    resolve_public_surface_requirement,
)
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision, SafetyBoundaryReport


_FORBIDDEN_META_KEYS = {
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
    "observation_text",
    "reception_text",
}


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


_J_CURRENT_INPUT: dict[str, object] = {
    "memo": (
        "「いきなり大きく変わろう」とするよりも、\n"
        "「昨日の自分よりほんの少し前に進めたらいい」\n"
        "そういう気持ちで過ごしていきたい。\n"
        "人と比べてしまうと、どうしても焦ったり、自分が遅い気がしてしまう。\n"
        "でも、本当は比べる相手は他の誰かじゃなくて、昨日の自分なんだと思う。\n"
        "昨日より少し出来たことが増えた。\n"
        "昨日より少し勇気が出せた。\n"
        "昨日より少し気持ちを言葉に出来た。\n"
        "そういう小さな変化を大切にしていきたい"
    ),
    "memo_action": "",
    "emotion_details": [{"type": "自己理解", "strength": "medium"}],
    "category": ["健康", "人生"],
}


_TRUE_LOW_INFORMATION_INPUT: dict[str, object] = {
    "memo": "疲れた",
    "memo_action": "",
    "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
    "category": ["生活"],
}


def _assert_body_free(value: Mapping[str, Any]) -> None:
    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            assert not (set(node.keys()) & _FORBIDDEN_META_KEYS)
            for child in node.values():
                walk(child)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for child in node:
                walk(child)

    walk(value)


def _surface_requirement(current_input: Mapping[str, Any]) -> dict[str, Any]:
    bundle = build_emlis_input_material_bundle(current_input)
    return resolve_public_surface_requirement(
        current_input=current_input,
        material_route=bundle.as_meta(),
        composer_meta={},
        diagnostic_summary={},
    )


def _original_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text="この記録では、生活についての動きがあり、次にどう扱うかを探しているように見えます。",
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p3-limited-original",
        attempt_count=1,
        confidence=0.74,
        response_schema_version="cocolon.emlis.complete_composer.response.v1",
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
        used_relation_ids=["limited_grounding_reception_material"],
    )


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "product_surface_invalid_plain_used_for_two_stage_required",
        ],
        trace_id="p3-limited-reception-recompose",
    )


def _build_candidate_for(current_input: Mapping[str, Any]) -> ConversationComposerCandidate:
    bundle = build_emlis_input_material_bundle(current_input)
    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    requirement = _surface_requirement(current_input)
    assert requirement["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert requirement["low_information_allowed"] is False

    assert should_attempt_labelled_two_stage_surface_recomposition(
        current_input=current_input,
        material_route=bundle.as_meta(),
        surface_requirement=requirement,
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
    )

    candidate, reasons = build_labelled_two_stage_surface_recomposition_candidate(
        current_input=current_input,
        material_route=bundle.as_meta(),
        surface_requirement=requirement,
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        trace_id="p3-limited-direct",
        recovery_context="pre_public_display_gate",
    )

    assert candidate is not None
    assert "labelled_two_stage_surface_recomposition_candidate_built" in reasons
    assert candidate.composer_model == "labelled_two_stage_surface_recomposition_v1"
    assert is_labelled_two_stage_comment_text_shape(candidate.comment_text)
    assert candidate.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in candidate.comment_text
    assert not candidate.comment_text.startswith("詳しく残せそうなら")
    assert "何があったか残してみませんか" not in candidate.comment_text

    meta = candidate.composer_meta
    assert_labelled_two_stage_surface_recomposition_meta(meta)
    assert meta["source_material_summary"]["material_quality"] == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert meta["source_material_summary"]["response_kind"] == "limited_grounding_observation"
    assert meta["source_material_summary"]["limited_grounding_reception_required"] is True
    assert meta["labelled_two_stage_surface_recomposition_summary"]["limited_grounding_reception_used"] is True
    assert meta["labelled_two_stage_surface_recomposition_summary"]["low_information_observation_used_as_final"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    _assert_body_free(meta)
    return candidate


def test_p3_i_limited_grounding_builds_reception_required_two_stage_candidate() -> None:
    candidate = _build_candidate_for(_I_CURRENT_INPUT)

    assert "気力" in candidate.comment_text
    assert "人と近くありたい" in candidate.comment_text
    assert "挑戦" in candidate.comment_text
    assert "Emlisは受け取りました" in candidate.comment_text
    assert "詳しい出来事" not in candidate.comment_text


def test_p3_j_limited_grounding_builds_self_understanding_two_stage_candidate() -> None:
    candidate = _build_candidate_for(_J_CURRENT_INPUT)

    assert "昨日の自分" in candidate.comment_text
    assert "少し前に進む" in candidate.comment_text
    assert "小さな変化" in candidate.comment_text
    assert "Emlisは受け取りました" in candidate.comment_text
    assert "詳しい出来事" not in candidate.comment_text


def test_p3_public_candidate_builder_selects_p6_for_limited_grounding() -> None:
    bundle = build_emlis_input_material_bundle(_I_CURRENT_INPUT)
    result = build_public_candidate_after_gate_recovery(
        current_input=dict(_I_CURRENT_INPUT),
        material_route=bundle.as_meta(),
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p3-limited-builder-selects-p6",
    )

    assert result.candidate_available is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert result.public_display_allowed is True
    assert result.candidate is not None
    assert is_labelled_two_stage_comment_text_shape(result.candidate.comment_text)
    assert "気力" in result.candidate.comment_text
    assert "Emlisから：" in result.candidate.comment_text
    meta = result.as_meta()
    assert meta["source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert meta["source_kind"] != CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert meta["recovery_plan"]["target_public_candidate_source"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    _assert_body_free(meta)


def test_p3_true_low_information_is_still_blocked_from_labelled_two_stage_p6() -> None:
    bundle = build_emlis_input_material_bundle(_TRUE_LOW_INFORMATION_INPUT)
    assert bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION
    requirement = _surface_requirement(_TRUE_LOW_INFORMATION_INPUT)

    assert not should_attempt_labelled_two_stage_surface_recomposition(
        current_input=_TRUE_LOW_INFORMATION_INPUT,
        material_route=bundle.as_meta(),
        surface_requirement=requirement,
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
    )
