# -*- coding: utf-8 -*-
from __future__ import annotations

"""P1 public-surface requirement tests for limited/low-information reception.

P1 separates limited_grounding from low_information routing at the requirement
layer.  limited_grounding must require labelled two-stage reception, while true
low_information keeps its own family but also requires a reception section.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    build_emlis_input_material_bundle,
)
from emlis_ai_public_surface_requirement import (
    LABELLED_TWO_STAGE_OBSERVATION_MARKER,
    LABELLED_TWO_STAGE_RECEPTION_BOUNDARY,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    assert_public_surface_requirement_decision,
    resolve_public_surface_requirement,
)


def _assert_body_free(value: Mapping[str, Any]) -> None:
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
    }

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            assert not (set(node.keys()) & forbidden)
            for child in node.values():
                walk(child)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for child in node:
                walk(child)

    walk(value)


def _i_current_input() -> dict[str, object]:
    return {
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


def _j_current_input() -> dict[str, object]:
    return {
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


def _true_low_information_input() -> dict[str, object]:
    return {
        "memo": "疲れた",
        "memo_action": "",
        "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
        "category": ["生活"],
    }


def _resolve_for(current_input: Mapping[str, Any]) -> dict[str, Any]:
    bundle = build_emlis_input_material_bundle(current_input)
    return resolve_public_surface_requirement(
        current_input=current_input,
        material_route=bundle.as_meta(),
        composer_meta={},
        diagnostic_summary={},
    )


def _assert_reception_required_shape(decision: Mapping[str, Any]) -> None:
    shape = decision["required_comment_text_shape"]
    assert shape["starts_with"] == LABELLED_TWO_STAGE_OBSERVATION_MARKER
    assert shape["contains_boundary"] == LABELLED_TWO_STAGE_RECEPTION_BOUNDARY
    assert shape["labels_required"] is True
    assert shape["observation_section_required"] is True
    assert shape["reception_section_required"] is True
    assert shape["comment_text_body_included"] is False


def test_p1_i_limited_grounding_requires_labelled_two_stage_reception() -> None:
    current_input = _i_current_input()
    bundle = build_emlis_input_material_bundle(current_input)
    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING

    decision = _resolve_for(current_input)

    assert_public_surface_requirement_decision(decision)
    assert decision["material_quality_family"] == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert decision["two_stage_required"] is True
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is False
    assert "limited_grounding_reception_required" in decision["decision_sources"]
    assert "low_information_material" not in decision["decision_sources"]
    assert decision["input_material_classification"]["low_information_material"] is False
    assert decision["input_material_classification"]["emotions_present"] is True
    _assert_reception_required_shape(decision)
    _assert_body_free(decision)


def test_p1_j_limited_grounding_requires_labelled_two_stage_reception() -> None:
    current_input = _j_current_input()
    bundle = build_emlis_input_material_bundle(current_input)
    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING

    decision = _resolve_for(current_input)

    assert_public_surface_requirement_decision(decision)
    assert decision["material_quality_family"] == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert decision["two_stage_required"] is True
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is False
    assert "limited_grounding_reception_required" in decision["decision_sources"]
    assert "low_information_material" not in decision["decision_sources"]
    assert decision["input_material_classification"]["low_information_material"] is False
    assert decision["input_material_classification"]["emotions_present"] is True
    _assert_reception_required_shape(decision)
    _assert_body_free(decision)


def test_p1_true_low_information_keeps_family_but_requires_reception_section() -> None:
    current_input = _true_low_information_input()
    bundle = build_emlis_input_material_bundle(current_input)
    assert bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION

    decision = _resolve_for(current_input)

    assert_public_surface_requirement_decision(decision)
    assert decision["material_quality_family"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
    assert decision["two_stage_required"] is False
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is True
    assert "low_information_material" in decision["decision_sources"]
    assert "low_information_reception_required" in decision["decision_sources"]
    assert decision["input_material_classification"]["low_information_material"] is True
    assert decision["input_material_classification"]["emotions_present"] is True
    _assert_reception_required_shape(decision)
    assert decision["required_comment_text_shape"]["kind"] == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
    _assert_body_free(decision)
