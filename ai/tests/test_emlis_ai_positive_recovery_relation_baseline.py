from __future__ import annotations

from emlis_ai_listener_reader_judge import judge_listener_readability


_POSITIVE_RECOVERY_OLD_MARKER_TEXT = "\n".join(
    [
        "Emlisです。",
        "小さな回復が少し戻ってきています。",
        "中心にある感覚として形を取り直しています。",
        "戻ってくる動きと前段の負荷の関係も残しています。",
    ]
)


def test_positive_recovery_old_self_repair_marker_should_not_remain_reader_relation_not_expressed() -> None:
    report = judge_listener_readability(_POSITIVE_RECOVERY_OLD_MARKER_TEXT)

    assert "relation_not_expressed" not in report.rejection_reasons


def test_positive_recovery_without_relation_surface_is_still_reader_rejected() -> None:
    text = "\n".join(
        [
            "Emlisです。",
            "小さな回復が少し戻ってきています。",
            "中心にある感覚として形を取り直しています。",
            "締めでは、静かにあります。",
        ]
    )
    report = judge_listener_readability(text)

    assert report.understandable is False
    assert "relation_not_expressed" in report.rejection_reasons
