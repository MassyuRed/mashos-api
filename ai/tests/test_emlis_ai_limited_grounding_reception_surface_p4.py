# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 tests for the limited-grounding reception surface helper.

P4 moves limited-grounding reception wording and body-free surface planning out
of the P6 recomposition module.  The helper must remain material/semantic-id
driven, must not store raw input in meta, and must keep I/J away from low-info
question-dominant surfaces.
"""

from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    build_emlis_input_material_bundle,
)
from emlis_ai_labelled_two_stage_surface_recomposition import (
    build_labelled_two_stage_surface_recomposition_candidate,
)
from emlis_ai_limited_grounding_reception_surface import (
    assert_limited_grounding_reception_surface_meta,
    build_limited_grounding_reception_surface_plan,
    compose_limited_grounding_labelled_two_stage_comment,
    is_limited_grounding_reception_required,
    limited_grounding_reception_surface_public_summary,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    is_labelled_two_stage_comment_text_shape,
    resolve_public_surface_requirement,
)
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision


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
        trace_id="p4-limited-original",
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
        trace_id="p4-limited-reception-helper",
    )


def _plan_and_comment(current_input: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    bundle = build_emlis_input_material_bundle(current_input)
    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    requirement = _surface_requirement(current_input)
    assert requirement["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert is_limited_grounding_reception_required(
        material_route=bundle.as_meta(),
        surface_requirement=requirement,
    )

    plan = build_limited_grounding_reception_surface_plan(
        current_input=current_input,
        material_route=bundle.as_meta(),
        surface_requirement=requirement,
    )
    assert_limited_grounding_reception_surface_meta(plan)
    comment = compose_limited_grounding_labelled_two_stage_comment(
        current_input=current_input,
        material_route=bundle.as_meta(),
        surface_requirement=requirement,
    )
    assert is_labelled_two_stage_comment_text_shape(comment)
    return plan, comment


def test_p4_i_helper_extracts_recovery_relationship_and_future_materials_without_body_meta() -> None:
    plan, comment = _plan_and_comment(_I_CURRENT_INPUT)

    assert {"recovered_energy", "relationship_wish", "future_intention"}.issubset(
        set(plan["semantic_material_ids"])
    )
    assert plan["reception_required"] is True
    assert plan["question_policy"]["question_required"] is False
    assert "cause" in plan["observation_focus"]["must_not_assert"]
    assert "specific_event" in plan["observation_focus"]["must_not_assert"]
    assert "気力" in comment
    assert "人と近くありたい" in comment
    assert "挑戦" in comment
    assert "Emlisから：" in comment
    assert "詳しい出来事" not in comment
    assert "何があったか残してみませんか" not in comment
    _assert_body_free(plan)
    _assert_body_free(limited_grounding_reception_surface_public_summary(plan))


def test_p4_j_helper_extracts_comparison_and_small_change_materials_without_event_overread() -> None:
    plan, comment = _plan_and_comment(_J_CURRENT_INPUT)

    assert {"comparison_baseline_shift", "small_change_preservation", "value_preservation"}.issubset(
        set(plan["semantic_material_ids"])
    )
    assert "昨日の自分" in comment
    assert "少し前に進む" in comment
    assert "小さな変化" in comment
    assert "Emlisは受け取りました" in comment
    assert "詳しい出来事" not in comment
    assert "原因" not in comment
    _assert_body_free(plan)


def test_p4_helper_meta_assert_rejects_text_payload_keys() -> None:
    plan, _ = _plan_and_comment(_I_CURRENT_INPUT)
    broken = dict(plan)
    broken["memo"] = "raw text must not be stored"

    with pytest.raises(ValueError, match="must not contain text payload keys"):
        assert_limited_grounding_reception_surface_meta(broken)


def test_p4_p6_candidate_meta_carries_body_free_limited_helper_summary() -> None:
    bundle = build_emlis_input_material_bundle(_I_CURRENT_INPUT)
    requirement = _surface_requirement(_I_CURRENT_INPUT)
    candidate, reasons = build_labelled_two_stage_surface_recomposition_candidate(
        current_input=_I_CURRENT_INPUT,
        material_route=bundle.as_meta(),
        surface_requirement=requirement,
        original_composer_candidate=_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        trace_id="p4-limited-helper-p6",
        recovery_context="pre_public_display_gate",
    )

    assert candidate is not None
    assert "labelled_two_stage_surface_recomposition_candidate_built" in reasons
    assert candidate.composer_meta["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    summary = candidate.composer_meta["limited_grounding_reception_surface_summary"]
    assert summary["limited_grounding_reception_surface_used"] is True
    assert {"recovered_energy", "relationship_wish", "future_intention"}.issubset(
        set(summary["semantic_material_ids"])
    )
    assert candidate.composer_meta["labelled_two_stage_surface_recomposition_summary"][
        "limited_grounding_reception_surface_plan_connected"
    ] is True
    _assert_body_free(candidate.composer_meta)
