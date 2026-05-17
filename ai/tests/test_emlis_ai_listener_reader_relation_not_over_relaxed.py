from __future__ import annotations

from emlis_ai_listener_reader_judge import judge_listener_readability


def test_reader_does_not_pass_positive_recovery_on_bare_relation_word() -> None:
    text = "\n".join(
        [
            "Emlisです。",
            "少し元気になっています。",
            "今日はよかったです。",
            "回復の関係も残っています。",
        ]
    )

    report = judge_listener_readability(text, expected_relation_types=("recovery",))

    assert report.understandable is False
    assert "relation_not_expressed" in report.rejection_reasons


def test_reader_does_not_pass_recovery_on_generic_cue_only() -> None:
    text = "\n".join(
        [
            "Emlisです。",
            "少し元気になっています。",
            "今日はよかったです。",
            "同じ場所に残っています。",
        ]
    )

    report = judge_listener_readability(text, expected_relation_types=("positive_recovery",))

    assert report.understandable is False
    assert "relation_not_expressed" in report.rejection_reasons


def test_reader_keeps_relation_not_expressed_for_plain_three_sentence_candidate() -> None:
    text = "\n".join(
        [
            "Emlisです。",
            "少し元気になっています。",
            "今日はよかったです。",
            "静かに残っています。",
        ]
    )

    report = judge_listener_readability(text)

    assert report.understandable is False
    assert "relation_not_expressed" in report.rejection_reasons
