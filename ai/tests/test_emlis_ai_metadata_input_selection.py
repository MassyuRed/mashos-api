from __future__ import annotations

from copy import deepcopy

import pytest

from emlis_ai_context_service import build_input_effort_signals
from emlis_ai_coverage_matrix_service import build_emlis_coverage_matrix
from emlis_ai_types import SourceBundle
from emlis_ai_world_model_service import _build_recovery_signal, _build_same_day_change, _dominant_emotion_from_input


def _bundle(current: dict, previous: dict) -> SourceBundle:
    return SourceBundle(
        user_id="synthetic-owner",
        display_name=None,
        current_input=current,
        same_day_recent_inputs=[previous],
        input_summary={"streak_days": 1},
    )


def test_effort_count_uses_legacy_selections_when_details_are_empty_without_changing_source() -> None:
    source = {
        "memo": " まだ決めていません。\n考えています。 ",
        "memo_action": "話を聞きました。\n今日は連絡しませんでした。",
        "emotion_details": [],
        "emotions": ["喜び", "悲しみ", "怒り", "不安", "平穏"],
        "category": ["生活", "仕事", "趣味", "人間関係", "恋愛", "健康", "学習", "価値観", "人生"],
    }
    before = deepcopy(source)
    signals = build_input_effort_signals(source)
    complete = {**source, "emotion_details": [{"type": value, "strength": "medium"} for value in source["emotions"]]}
    assert signals == build_input_effort_signals(complete)
    assert signals["emotion_count"] == 5
    assert signals["category_count"] == 9
    assert signals["memo_char_count"] == len(source["memo"].strip())
    assert signals["memo_action_char_count"] == len(source["memo_action"].strip())
    assert source == before


def test_old_history_selections_remain_available_to_both_change_signals() -> None:
    previous = {"id": "previous", "emotion_details": [], "emotions": ["不安"]}
    current = {"id": "current", "emotion_details": [], "emotions": ["平穏"]}
    before = deepcopy((previous, current))
    change = _build_same_day_change(_bundle(current, previous))
    recovery = _build_recovery_signal(_bundle(current, previous))
    assert change is not None
    assert "不安 から 平穏" in change.text
    assert recovery is not None
    assert [evidence.ref_id for evidence in recovery.evidence] == ["previous", "current"]
    assert (previous, current) == before


def test_same_day_comparison_uses_the_strongest_selection_for_both_records() -> None:
    previous = {"id": "previous", "emotion_details": [
        {"type": "喜び", "strength": "weak"}, {"type": "不安", "strength": "strong"},
    ]}
    unchanged = {"id": "current", "emotion_details": [{"type": "不安", "strength": "strong"}]}
    assert _build_same_day_change(_bundle(unchanged, previous)) is None
    assert _build_recovery_signal(_bundle(unchanged, previous)) is None

    changed = {"id": "current", "emotion_details": [{"type": "平穏", "strength": "weak"}]}
    change = _build_same_day_change(_bundle(changed, previous))
    assert change is not None
    assert "不安 から 平穏" in change.text
    assert _build_recovery_signal(_bundle(changed, previous)) is not None


@pytest.mark.parametrize("strength", ["weak", "medium", "strong"])
def test_equal_selected_strength_does_not_invent_a_change(strength: str) -> None:
    selected = [{"type": "平穏", "strength": strength}]
    previous = {"id": "previous", "emotion_details": selected}
    current = {"id": "current", "emotion_details": deepcopy(selected)}
    assert _build_same_day_change(_bundle(current, previous)) is None
    assert _build_recovery_signal(_bundle(current, previous)) is None


def test_changed_strength_is_compared_without_relabeling_the_emotion() -> None:
    previous = {"id": "previous", "emotion_details": [{"type": "不安", "strength": "strong"}]}
    current = {"id": "current", "emotion_details": [{"type": "不安", "strength": "weak"}]}
    change = _build_same_day_change(_bundle(current, previous))
    assert change is not None
    assert change.text == "同じ感情でも、さっきから感じ方が少し動いていますね。"
    assert _build_recovery_signal(_bundle(current, previous)) is None


@pytest.mark.parametrize("strength", ["weak", "medium", "strong"])
def test_reversing_equally_strong_selections_does_not_invent_a_center_or_change(strength: str) -> None:
    previous = {"id": "previous", "emotion_details": [
        {"type": "不安", "strength": strength}, {"type": "喜び", "strength": strength},
    ]}
    current = {"id": "current", "emotion_details": list(reversed(previous["emotion_details"]))}
    assert _dominant_emotion_from_input(previous) == (None, None)
    assert _dominant_emotion_from_input(current) == (None, None)
    assert _build_same_day_change(_bundle(current, previous)) is None
    assert _build_recovery_signal(_bundle(current, previous)) is None


@pytest.mark.parametrize("tied_side", ["previous", "current"])
def test_a_tied_record_does_not_supply_a_single_center_for_comparison(tied_side: str) -> None:
    tied = {"emotion_details": [{"type": "不安", "strength": "strong"}, {"type": "怒り", "strength": "strong"}]}
    unique = {"emotion_details": [{"type": "平穏", "strength": "strong"}]}
    previous, current = (tied, unique) if tied_side == "previous" else (unique, tied)
    assert _build_same_day_change(_bundle(current, previous)) is None
    assert _build_recovery_signal(_bundle(current, previous)) is None


def test_unique_maximum_remains_the_center_regardless_of_selection_order() -> None:
    previous = {"id": "previous", "emotion_details": [
        {"type": "喜び", "strength": "weak"}, {"type": "不安", "strength": "strong"},
    ]}
    current = {"id": "current", "emotion_details": [
        {"type": "怒り", "strength": "weak"}, {"type": "平穏", "strength": "medium"},
    ]}
    for before in [previous, {**previous, "emotion_details": list(reversed(previous["emotion_details"]))}]:
        for after in [current, {**current, "emotion_details": list(reversed(current["emotion_details"]))}]:
            assert _dominant_emotion_from_input(before) == ("不安", "strong")
            assert _dominant_emotion_from_input(after) == ("平穏", "medium")
            change = _build_same_day_change(_bundle(after, before))
            assert change is not None and "不安 から 平穏" in change.text
            assert _build_recovery_signal(_bundle(after, before)) is not None


def test_missing_selected_emotions_remain_missing() -> None:
    previous = {"id": "previous", "emotion_details": [], "emotions": []}
    current = {"id": "current", "emotion_details": [], "emotions": ["平穏"]}
    assert _build_same_day_change(_bundle(current, previous)) is None
    assert _build_recovery_signal(_bundle(current, previous)) is None
    assert build_input_effort_signals(previous)["emotion_count"] == 0


@pytest.mark.parametrize("detail_value", [None, []])
def test_coverage_metadata_already_keeps_legacy_emotion_tags_with_empty_details(detail_value: object) -> None:
    source = {"memo": "記録します。", "emotions": ["不安"], "emotion_details": detail_value}
    before = deepcopy(source)
    result = build_emlis_coverage_matrix(diagnostic_summary={}, current_input=source)
    assert "anxiety" in result["input_coverage_groups"]
    assert source == before
