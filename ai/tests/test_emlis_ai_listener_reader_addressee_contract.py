from __future__ import annotations

import pytest

from emlis_ai_listener_reader_judge import judge_listener_readability


_RELATION_BODY = [
    "いまの迷いは、ひとつの答えに寄せきれないまま残っています。",
    "進みたい気持ちと止まる重さが、同じ時間の中に重なっています。",
    "それぞれを急いで分けず、同じ流れの中で見ています。",
]


def _observation(first_line: str) -> str:
    return "\n".join([first_line, *_RELATION_BODY])


@pytest.mark.parametrize(
    "display_name_call",
    ["Mashさん", "Mash 様", "Mashくん", "Mash君", "Mashちゃん", "Mash氏"],
)
def test_reader_accepts_greeting_policy_honorific_suffixes(display_name_call: str) -> None:
    report = judge_listener_readability(_observation(f"{display_name_call}、Emlisです。"))

    assert report.addressee_clear is True
    assert "addressee_not_clear" not in report.rejection_reasons


def test_reader_accepts_display_name_call_with_internal_space_before_desu() -> None:
    report = judge_listener_readability(_observation("Mash 様、Emlis です。"))

    assert report.addressee_clear is True
    assert "addressee_not_clear" not in report.rejection_reasons


def test_reader_keeps_plain_emlis_greeting_accepted() -> None:
    report = judge_listener_readability(_observation("Emlisです。"))

    assert report.addressee_clear is True
    assert "addressee_not_clear" not in report.rejection_reasons


def test_reader_keeps_bare_emlis_greeting_with_internal_space_valid() -> None:
    report = judge_listener_readability(_observation("Emlis です。"))

    assert report.addressee_clear is True
    assert "addressee_not_clear" not in report.rejection_reasons


def test_reader_does_not_accept_arbitrary_name_without_honorific() -> None:
    report = judge_listener_readability(_observation("Mash、Emlisです。"))

    assert report.addressee_clear is False
    assert "addressee_not_clear" in report.rejection_reasons


def test_reader_does_not_accept_unlisted_honorific_like_suffix() -> None:
    report = judge_listener_readability(_observation("Mash殿、Emlisです。"))

    assert report.addressee_clear is False
    assert "addressee_not_clear" in report.rejection_reasons
