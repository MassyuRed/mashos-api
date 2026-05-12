from __future__ import annotations

from emotion_piece_generation_service import generate_emotion_reflection_preview


def _preview(memo: str):
    return generate_emotion_reflection_preview(
        emotion_details=[{"type": "自己理解", "strength": "medium"}],
        memo=memo,
        memo_action="",
        categories=["自己理解"],
    )


def test_piece_uses_value_observation_without_overcompressing_user_claims():
    preview = _preview("やることが多い時は全部整理しようとする。でも量が多すぎて嫌になって、結局目についたものから手をつける。終わったあとで最初の整理って何だったんだろうと思う。")
    core = preview.get("piece_core") or {}
    answer = preview["answer_display_text"]

    assert core.get("focus_key") == "ideal_capacity_switch_gap"
    assert "ideal_capacity_switch_gap" in core.get("must_keep_signal_keys", [])
    assert core.get("answer_preservation_policy") == "preserve_user_claims"
    assert core.get("piece_composer_connected") is True
    assert core.get("core_guard_passed") is True
    assert (core.get("text_generation_core") or {}).get("answer_passed") is True
    assert "整理" in answer and "量" in answer and "目についた" in answer
    assert answer.count("。") >= 2
    assert "自己理解で大切にしているのは" not in answer


def test_piece_value_observation_blocks_broken_display_rewrite():
    preview = _preview("友達に前より明るくなったねって言われた。嬉しかったけど、本当は無理しているだけなんじゃないかって怖くなった。")
    answer = preview["answer_display_text"]
    core = preview.get("piece_core") or {}

    assert core.get("focus_key") == "outer_inner_role_gap"
    assert "明る" in answer and "嬉" in answer and "怖" in answer
    assert "ますです" not in answer
    assert core.get("communicative_core_ok") is True
    assert (core.get("text_generation_core") or {}).get("piece_composer_connected") is True
    assert core.get("piece_composer_connected") is True
    assert (core.get("text_generation_core") or {}).get("answer_passed") is True
