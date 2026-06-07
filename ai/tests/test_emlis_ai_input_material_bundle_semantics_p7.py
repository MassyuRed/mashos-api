# -*- coding: utf-8 -*-
from __future__ import annotations

"""P7 tests for generic semantic material ids in the input bundle.

P7 expands body-free material semantics used by limited-grounding reception.
These tests intentionally avoid case-id routes and fixed surface text: H/I/J are
fixtures for semantic coverage, not runtime branches.
"""

from collections.abc import Mapping, Sequence
from typing import Any
import json

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    assert_emlis_input_material_bundle_meta,
    build_emlis_input_material_bundle,
)
from emlis_ai_limited_grounding_reception_surface import (
    assert_limited_grounding_reception_surface_meta,
    build_limited_grounding_reception_surface_plan,
    limited_grounding_reception_surface_public_summary,
)

_FORBIDDEN_RAW_MARKERS = (
    "やってみたい",
    "気力",
    "恋愛",
    "昨日の自分",
    "小さな変化",
    "そばに",
)
_SEMANTIC_IDS = {
    "recovered_energy",
    "future_intention",
    "relationship_wish",
    "comparison_baseline_shift",
    "small_change_preservation",
    "value_preservation",
    "self_observation",
}


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_body_free(value: Mapping[str, Any]) -> None:
    encoded = _encoded(value)
    for marker in _FORBIDDEN_RAW_MARKERS:
        assert marker not in encoded

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            assert "memo" not in node
            assert "memo_action" not in node
            assert "comment_text" not in node
            assert "body" not in node
            assert "text" not in node
            for child in node.values():
                walk(child)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for child in node:
                walk(child)

    walk(value)


def _h_current_input() -> dict[str, object]:
    return {
        "memo": (
            "ふとした時に、これやってみたいなとか\n"
            "自分にも出来るかもしれないって思う瞬間がある\n"
            "でもそのあとに、なんで私はそう思ったんだろうって考えることが多い\n"
            "きっと今までの経験とか気持ちとか\n"
            "色んなものが重なってその考えが出てきてるんだと思う\n"
            "だから私は、その「やりたい」と思った気持ちを大事にしたい\n"
            "頑張って良かった もっと色々挑戦したい\n"
            "そう思えることが大きな一歩だと思う\n"
            "ずっと落ち込んでて何もしたくなくて\n"
            "自信をなくして諦めていたから\n"
            "この気持ちになれたことを大切にして\n"
            "つぎどう頑張るか知って行きたい"
        ),
        "memo_action": "",
        "emotion_details": [{"type": "平穏", "strength": "medium"}],
        "category": ["生活"],
    }


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


def test_p7_h_material_bundle_adds_recovery_future_value_self_semantics_without_raw_text() -> None:
    bundle = build_emlis_input_material_bundle(_h_current_input())
    meta = bundle.as_meta()

    assert bundle.material_quality == MATERIAL_QUALITY_ELIGIBLE
    assert {"recovered_energy", "future_intention", "value_preservation", "self_observation"}.issubset(
        set(meta["relation_material_ids"])
    )
    assert meta["case_specific_route_used"] is False
    assert meta["fixed_fallback_used"] is False
    assert_emlis_input_material_bundle_meta(meta)
    _assert_body_free(meta)


def test_p7_i_material_bundle_adds_recovery_relationship_future_semantics_without_case_route() -> None:
    bundle = build_emlis_input_material_bundle(_i_current_input())
    meta = bundle.as_meta()

    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert {"recovered_energy", "relationship_wish", "future_intention"}.issubset(
        set(meta["relation_material_ids"])
    )
    assert meta["case_specific_route_used"] is False
    assert meta["phase19_runtime_cue_used"] is False
    assert_emlis_input_material_bundle_meta(meta)
    _assert_body_free(meta)


def test_p7_j_material_bundle_adds_comparison_small_change_value_semantics_without_raw_text() -> None:
    bundle = build_emlis_input_material_bundle(_j_current_input())
    meta = bundle.as_meta()

    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert {"comparison_baseline_shift", "small_change_preservation", "value_preservation"}.issubset(
        set(meta["relation_material_ids"])
    )
    assert "self_understanding_learning" in meta["relation_material_ids"]
    assert "value_or_self_understanding_material" in meta["relation_material_ids"]
    assert meta["case_specific_route_used"] is False
    assert_emlis_input_material_bundle_meta(meta)
    _assert_body_free(meta)


def test_p7_category_alone_does_not_create_new_semantic_material_ids() -> None:
    bundle = build_emlis_input_material_bundle(
        {
            "memo": "",
            "memo_action": "",
            "emotion_details": [{"type": "平穏", "strength": "medium"}],
            "category": ["恋愛"],
        }
    )
    meta = bundle.as_meta()

    assert "relationship_category_direction" in meta["relation_material_ids"]
    assert "relationship_material" in meta["relation_material_ids"]
    assert not (_SEMANTIC_IDS & set(meta["relation_material_ids"]))
    assert_emlis_input_material_bundle_meta(meta)
    _assert_body_free(meta)


def test_p7_limited_reception_plan_can_use_bundle_semantics_without_raw_current_input() -> None:
    bundle = build_emlis_input_material_bundle(_i_current_input())
    meta = bundle.as_meta()
    plan = build_limited_grounding_reception_surface_plan(
        current_input=None,
        material_route=meta,
        surface_requirement={"material_quality_family": "limited_grounding"},
    )

    assert {"recovered_energy", "relationship_wish", "future_intention"}.issubset(
        set(plan["semantic_material_ids"])
    )
    assert plan["reception_required"] is True
    assert plan["question_policy"]["question_required"] is False
    assert_limited_grounding_reception_surface_meta(plan)
    summary = limited_grounding_reception_surface_public_summary(plan)
    assert {"recovered_energy", "relationship_wish", "future_intention"}.issubset(
        set(summary["semantic_material_ids"])
    )
    _assert_body_free(plan)
    _assert_body_free(summary)
