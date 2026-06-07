# -*- coding: utf-8 -*-
from __future__ import annotations

"""P0 fixtures for H/I/J current input material classification.

These fixtures fix the baseline before changing public-surface routing: H has
sufficient material, while I/J are not empty or true low-information.  They are
limited-grounding inputs that still expose observable material slots.
"""

import json

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_EVENT,
    VISIBLE_SLOT_ACTION,
    VISIBLE_SLOT_CHANGE,
    VISIBLE_SLOT_EMOTION_DIRECTION,
    VISIBLE_SLOT_EVENT,
    VISIBLE_SLOT_RELATIONSHIP,
    VISIBLE_SLOT_TARGET,
    VISIBLE_SLOT_TIME,
    VISIBLE_SLOT_VALUE,
    assert_emlis_input_material_bundle_meta,
    build_emlis_input_material_bundle,
)


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


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


def test_p0_h_input_is_eligible_material_not_template_fixture_route() -> None:
    bundle = build_emlis_input_material_bundle(_h_current_input())
    meta = bundle.as_meta()

    assert bundle.material_quality == MATERIAL_QUALITY_ELIGIBLE
    assert set(bundle.visible_material_slots).issuperset(
        {
            VISIBLE_SLOT_EVENT,
            VISIBLE_SLOT_EMOTION_DIRECTION,
            VISIBLE_SLOT_TARGET,
            VISIBLE_SLOT_ACTION,
            VISIBLE_SLOT_TIME,
            VISIBLE_SLOT_VALUE,
        }
    )
    assert UNKNOWN_SLOT_CAUSE in bundle.unknown_slots
    assert meta["case_specific_route_used"] is False
    assert meta["phase19_runtime_cue_used"] is False
    assert "やってみたい" not in _encoded(meta)
    assert_emlis_input_material_bundle_meta(meta)


def test_p0_i_input_is_limited_grounding_with_observable_relation_and_time() -> None:
    bundle = build_emlis_input_material_bundle(_i_current_input())
    meta = bundle.as_meta()

    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert set(bundle.visible_material_slots).issuperset(
        {
            VISIBLE_SLOT_EMOTION_DIRECTION,
            VISIBLE_SLOT_RELATIONSHIP,
            VISIBLE_SLOT_TARGET,
            VISIBLE_SLOT_TIME,
        }
    )
    assert UNKNOWN_SLOT_EVENT in bundle.unknown_slots
    assert UNKNOWN_SLOT_CAUSE in bundle.unknown_slots
    assert meta["low_information_is_bundle_material_shortage"] is False
    assert meta["case_specific_route_used"] is False
    assert "恋愛" not in _encoded(meta)
    assert_emlis_input_material_bundle_meta(meta)


def test_p0_j_input_is_limited_grounding_with_self_understanding_change_material() -> None:
    bundle = build_emlis_input_material_bundle(_j_current_input())
    meta = bundle.as_meta()

    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert set(bundle.visible_material_slots).issuperset(
        {
            VISIBLE_SLOT_EMOTION_DIRECTION,
            VISIBLE_SLOT_RELATIONSHIP,
            VISIBLE_SLOT_TARGET,
            VISIBLE_SLOT_CHANGE,
            VISIBLE_SLOT_TIME,
            VISIBLE_SLOT_VALUE,
        }
    )
    assert UNKNOWN_SLOT_EVENT in bundle.unknown_slots
    assert UNKNOWN_SLOT_CAUSE in bundle.unknown_slots
    assert "self_understanding_learning" in meta["relation_material_ids"]
    assert "value_or_self_understanding_material" in meta["relation_material_ids"]
    assert meta["low_information_is_bundle_material_shortage"] is False
    assert meta["case_specific_route_used"] is False
    assert "昨日の自分" not in _encoded(meta)
    assert_emlis_input_material_bundle_meta(meta)
