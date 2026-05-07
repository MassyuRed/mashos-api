from __future__ import annotations

from cocolon_value_observation_service import build_value_observation_plan, build_value_observation_signals


def _keys(memo: str) -> list[str]:
    return [signal.signal_key for signal in build_value_observation_signals(current_input={"memo": memo})]


def test_value_observation_extracts_five_generic_signals_without_exact_sample_matching():
    cases = {
        "stagnation_position_gap": "小さい確認ばかりで一日が終わって、前に進めていない感じが嫌だった。",
        "outer_inner_role_gap": "前より明るくなったと言われて嬉しいけど、本当は無理してそう見えているだけかもしれなくて怖い。",
        "relationship_cost_asymmetry": "こっちばっかり気を使って、毎回言葉を選んでいるのがもう面倒になってきた。",
        "inner_activity_fatigue_gap": "何もしていないのに、なぜか疲れている。",
        "ideal_capacity_switch_gap": "やることが多い時は全部整理しようとするけど、量が多すぎて結局目についたものから手をつける。",
    }
    for expected, memo in cases.items():
        assert expected in _keys(memo)


def test_value_observation_plan_keeps_grounding_and_non_diagnostic_contract():
    signals = build_value_observation_signals(
        current_input={"memo": "何もしていないのに疲れた。"},
    )
    plan = build_value_observation_plan(current_input={"memo": "何もしていないのに疲れた。"}, signals=signals)

    assert signals[0].signal_key == "inner_activity_fatigue_gap"
    assert signals[0].no_diagnosis is True
    assert signals[0].no_personality_claim is True
    assert "inner_activity_fatigue_gap" in plan.must_keep_signal_keys
    assert plan.grounding_terms
