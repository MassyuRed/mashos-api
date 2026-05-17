from __future__ import annotations

from emlis_ai_listener_reader_judge import judge_listener_readability


def test_reader_uses_relation_surface_contract_for_positive_recovery_bridge() -> None:
    text = "\n".join(
        [
            "Emlisです。",
            "小さな回復が少し戻ってきています。",
            "中心にある感覚として形を取り直しています。",
            "戻ってくる動きと前段の負荷が同じ流れの中でつながっています。",
        ]
    )

    report = judge_listener_readability(text, expected_relation_types=("positive_recovery",))

    assert report.understandable is True
    assert "relation_not_expressed" not in report.rejection_reasons


def test_reader_detects_existing_repair_marker_from_relation_surface_contract() -> None:
    text = "\n".join(
        [
            "Emlisです。",
            "少し戻ってくる動きが見えています。",
            "その中心は急に明るくなっただけではありません。",
            "戻ってくる動きと前段の負荷の関係も残しています。",
        ]
    )

    report = judge_listener_readability(text, expected_relation_types=("recovery",))

    assert "relation_not_expressed" not in report.rejection_reasons


def test_reader_keeps_legacy_relation_detection_for_non_recovery_text() -> None:
    text = "\n".join(
        [
            "Emlisです。",
            "迷いがまだ残っています。",
            "片方だけに寄らず、同じ場所に並んでいます。",
            "今は急がずに置かれています。",
        ]
    )

    report = judge_listener_readability(text)

    assert "relation_not_expressed" not in report.rejection_reasons
