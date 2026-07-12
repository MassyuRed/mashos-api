# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR3 contracts for semantic Depth Policy and Reception Move Plan v2."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import (
    GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION,
    build_grounded_observation_plan,
    validate_grounded_human_reception_plan,
)


_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "grounded_human_reception_exact8_v2_20260712.json"
)
_EXPECTED_DEPTH = {
    "A": ("minimal", "standard", 1, 1),
    "B": ("layered", "standard", 2, 2),
    "C": ("layered", "standard", 2, 2),
    "D": ("focused", "self_denial_bounded", 2, 2),
    "I6-S03": ("minimal", "standard", 1, 1),
    "I6-L03": ("layered", "standard", 2, 2),
    "I6-C01": ("layered", "standard", 2, 2),
    "I6-D02": ("focused", "help_seeking_bounded", 2, 2),
}
_EXPECTED_MOVE_ACTS = {
    "B": {"honor_concrete_effort", "recognize_lived_change"},
    "C": {"recognize_lived_change", "protect_retained_intention"},
    "I6-L03": {"protect_retained_intention", "honor_concrete_effort"},
    "I6-C01": {"honor_concrete_effort", "recognize_lived_change"},
    "D": {"bounded_counter_self_denial", "stay_with_current_burden"},
    "I6-D02": {"hold_help_seeking", "bounded_counter_self_denial"},
}


def _load_fixture():
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    return plan, reception_plan, resolver


def _case(case_id: str):
    row = next(
        item for item in _load_fixture()["cases"] if item["case_id"] == case_id
    )
    return _artifacts(row["exact_current_input"])


def _validate(plan, reception_plan, resolver):
    return validate_grounded_human_reception_plan(
        reception_plan,
        expected_target_ids=plan.response_plan.human_follow_target_ids,
        nucleus_index={item.nucleus_id: item for item in plan.nuclei},
        resolver=resolver,
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
    )


@pytest.mark.parametrize("case_id", tuple(_EXPECTED_DEPTH))
def test_rr3_exact8_depth_and_move_budget_are_semantically_fixed(
    case_id: str,
) -> None:
    plan, reception_plan, resolver = _case(case_id)
    depth = reception_plan.depth_policy
    expected_level, expected_safety, expected_moves, expected_sentences = (
        _EXPECTED_DEPTH[case_id]
    )

    assert reception_plan.schema_version == (
        GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION
    )
    assert depth.level == expected_level
    assert depth.safety_mode == expected_safety
    assert depth.raw_character_count_used is False
    assert depth.selected_move_count == expected_moves == len(
        reception_plan.moves
    )
    assert depth.min_sentences == expected_sentences
    assert 1 <= depth.max_sentences <= 3
    assert 1 <= len(reception_plan.moves) <= 3
    assert _validate(plan, reception_plan, resolver) == ()


@pytest.mark.parametrize("case_id", tuple(_EXPECTED_MOVE_ACTS))
def test_rr3_selected_moves_are_distinct_human_contributions(
    case_id: str,
) -> None:
    _plan, reception_plan, _resolver = _case(case_id)
    moves = reception_plan.moves
    assert {item.reception_act for item in moves} == _EXPECTED_MOVE_ACTS[case_id]
    assert [item.move_id for item in moves] == [
        f"rm{index}" for index in range(1, len(moves) + 1)
    ]
    assert moves[0].reception_act == reception_plan.primary_reception_act
    assert len(
        {
            (item.reception_act, item.target_nucleus_ids, item.move_role)
            for item in moves
        }
    ) == len(moves)
    for index, move in enumerate(moves):
        assert move.distinct_from_move_ids == tuple(
            prior.move_id for prior in moves[:index]
        )


def test_rr3_standard_compatibility_fields_do_not_cut_over_surface_early() -> None:
    for case_id in ("A", "B", "C", "I6-S03", "I6-L03", "I6-C01"):
        _plan, reception_plan, _resolver = _case(case_id)
        assert reception_plan.secondary_reception_act is None
    _plan, protected, _resolver = _case("I6-D02")
    assert protected.secondary_reception_act == "bounded_counter_self_denial"


def test_rr3_safety_moves_are_required_and_explicitly_bounded() -> None:
    for case_id in ("D", "I6-D02"):
        _plan, reception_plan, _resolver = _case(case_id)
        counter = next(
            move
            for move in reception_plan.moves
            if move.move_role == "bounded_counterposition"
        )
        assert counter.required is True
        assert counter.reception_act == "bounded_counter_self_denial"
        assert counter.speaker_presence == "explicit_emlis"
        assert counter.reference_mode == "explicit_emlis_counterposition"
        assert counter.surface_strategy == "explicit_emlis_counterposition"


def test_rr3_raw_length_control_uses_semantics_not_character_count() -> None:
    long_single = {
        "memo": (
            "今日はずっと重い。何をしても重く感じる。朝から重く、昼にも重く、"
            "今も同じ重さが続いている。何度言い直しても、ただしんどくて重い。"
        ),
        "memo_action": "",
        "emotions": ["悲しみ"],
        "category": ["生活"],
    }
    short_protected = {
        "memo": "自分には価値がない。それでも相談先は消さなかった。",
        "memo_action": "",
        "emotions": ["悲しみ"],
        "category": ["人生"],
    }
    _long_plan, long_reception, _long_resolver = _artifacts(long_single)
    _short_plan, short_reception, _short_resolver = _artifacts(short_protected)

    assert len(long_single["memo"]) > len(short_protected["memo"])
    assert long_reception.depth_policy.level == "minimal"
    assert len(long_reception.moves) == 1
    assert short_reception.depth_policy.safety_mode == "help_seeking_bounded"
    assert len(short_reception.moves) == 2
    assert long_reception.depth_policy.raw_character_count_used is False
    assert short_reception.depth_policy.raw_character_count_used is False


def test_rr3_long_arc_can_retain_three_distinct_required_moves() -> None:
    plan, reception_plan, resolver = _artifacts(
        {
            "memo": (
                "前は何も変わっていないと思った。けれど昨日より一つ進んだ。"
                "そこから、今の方向は残したいと思った。まだ結論は出ていない。"
                "次も自分で確かめたい。"
            ),
            "memo_action": "結果を表に記録して、試した順番も残した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        }
    )
    assert plan.input_profile.semantic_complexity == "long_arc"
    assert reception_plan.depth_policy.level == "layered"
    assert reception_plan.depth_policy.selected_move_count == 3
    assert reception_plan.depth_policy.max_sentences == 3
    assert reception_plan.depth_policy.min_realized_moves == 3
    assert {move.reception_act for move in reception_plan.moves} == {
        "honor_concrete_effort",
        "recognize_lived_change",
        "protect_retained_intention",
    }
    assert all(move.required for move in reception_plan.moves)
    assert _validate(plan, reception_plan, resolver) == ()


def test_rr3_standard_help_can_layer_with_another_distinct_contribution() -> None:
    plan, reception_plan, resolver = _artifacts(
        {
            "memo": "今日は二つのことを進めた。",
            "memo_action": "相談の予約を取った。必要な資料も送った。",
            "emotions": ["安堵"],
            "category": ["生活"],
        }
    )
    assert reception_plan.depth_policy.safety_mode == "standard"
    assert reception_plan.depth_policy.level == "layered"
    assert reception_plan.moves[0].reception_act == "hold_help_seeking"
    assert len(reception_plan.moves) >= 2
    assert len({move.reception_act for move in reception_plan.moves}) >= 2
    assert _validate(plan, reception_plan, resolver) == ()


def test_rr3_opportunity_only_counter_move_does_not_cut_over_legacy_surface() -> None:
    plan, reception_plan, resolver = _artifacts(
        {
            "memo": "自分には何もできない。それでも記録は残した。",
            "memo_action": "",
            "emotions": ["悲しみ"],
            "category": ["人生"],
        }
    )
    counter = next(
        move
        for move in reception_plan.moves
        if move.move_role == "bounded_counterposition"
    )
    assert counter.required is True
    assert counter.speaker_presence == "explicit_emlis"
    assert reception_plan.primary_reception_act == "stay_with_current_burden"
    assert reception_plan.secondary_reception_act is None
    assert _validate(plan, reception_plan, resolver) == ()


def test_rr3_validator_rejects_raw_count_and_move_count_corruption() -> None:
    plan, reception_plan, resolver = _case("B")
    invalid_depth = replace(
        reception_plan.depth_policy,
        raw_character_count_used=True,
        selected_move_count=1,
    )
    invalid_plan = replace(reception_plan, depth_policy=invalid_depth)
    issues = _validate(plan, invalid_plan, resolver)
    assert "human_reception_depth_raw_character_count_forbidden" in issues
    assert "human_reception_depth_selected_move_count_mismatch" in issues

    duplicate_second = replace(
        reception_plan.moves[1],
        move_id=reception_plan.moves[0].move_id,
    )
    invalid_plan = replace(
        reception_plan,
        moves=(reception_plan.moves[0], duplicate_second),
    )
    assert "human_reception_move_id_duplicate" in _validate(
        plan, invalid_plan, resolver
    )


def test_rr3_validator_rejects_dropped_required_safety_move() -> None:
    plan, reception_plan, resolver = _case("I6-D02")
    help_move = reception_plan.moves[0]
    invalid_depth = replace(
        reception_plan.depth_policy,
        selected_move_count=1,
        min_sentences=1,
        max_sentences=2,
        min_realized_moves=1,
    )
    invalid_plan = replace(
        reception_plan,
        depth_policy=invalid_depth,
        moves=(help_move,),
    )
    issues = _validate(plan, invalid_plan, resolver)
    assert "human_reception_required_safety_opportunity_unselected" in issues
    assert "human_reception_required_counterposition_move_missing" in issues

    weakened_counter = replace(reception_plan.moves[1], required=False)
    invalid_depth = replace(reception_plan.depth_policy, min_realized_moves=1)
    invalid_plan = replace(
        reception_plan,
        depth_policy=invalid_depth,
        moves=(help_move, weakened_counter),
    )
    assert "human_reception_move_required_mismatch" in _validate(
        plan, invalid_plan, resolver
    )
