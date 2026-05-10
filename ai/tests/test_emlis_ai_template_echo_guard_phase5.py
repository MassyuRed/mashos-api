from __future__ import annotations

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_template_echo_guard import guard_template_echo


def _evidence():
    return build_evidence_ledger(
        {
            "id": "phase5-template-guard",
            "created_at": "2026-05-10T00:00:00Z",
            "memo": "家にいると少し整う。現実に戻ると苦しくなる。普通に生活したい。たまに逃げ出したくなる。",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        }
    )


def _quote_heavy_evidence():
    return build_evidence_ledger(
        {
            "id": "phase5-raw-copy",
            "created_at": "2026-05-10T00:00:00Z",
            "memo": "家にいると少し整って落ち着ける。現実に戻ると苦しくなって動けなくなる。普通に生活したい気持ちは残っている。",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        }
    )


def _limited_kwargs():
    return {
        "composer_source": "ai_generated",
        "composer_model": "cocolon_limited_composer.v1",
        "generation_method": "scoped_graph_evidence_composer",
        "generation_scope": "scoped_graph_only",
    }


def test_phase5_guard_rejects_repeated_limited_composer_surface_patterns():
    evidence = _evidence()
    text = (
        "Mashさん、Emlisです。\n"
        "家にいると少し整う感覚が重なっています。\n"
        "現実に戻ると苦しくなる重さが重なっています。\n"
        "普通に生活したい願いが重なっています。"
    )

    report = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        **_limited_kwargs(),
    )

    assert report.passed is False
    assert "repeated_limited_surface_pattern" in report.rejection_reasons
    assert report.limited_surface_repetition_score >= 0.67
    assert "stacking" in report.matched_limited_surface_patterns


def test_phase5_guard_rejects_excessive_limited_raw_evidence_copy():
    evidence = _quote_heavy_evidence()
    text = (
        "Mashさん、Emlisです。\n"
        "家にいると少し整って落ち着ける。\n"
        "現実に戻ると苦しくなって動けなくなる。\n"
        "普通に生活したい気持ちは残っている。"
    )

    report = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        **_limited_kwargs(),
    )

    assert report.passed is False
    assert "excessive_raw_quote" in report.rejection_reasons
    assert report.raw_quote_span_count >= 2
    assert report.raw_quote_char_ratio >= 0.32


def test_phase5_guard_allows_short_limited_partial_observation_without_repeated_surface():
    evidence = _evidence()
    text = (
        "Mashさん、Emlisです。\n"
        "家の中で少し落ち着ける感覚と、現実へ戻る時の重さが重なっています。\n"
        "普通に過ごしたい願いも、その重さとつながっています。"
    )

    report = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        **_limited_kwargs(),
    )

    assert report.passed is True
    assert "repeated_limited_surface_pattern" not in report.rejection_reasons
    assert "excessive_raw_quote" not in report.rejection_reasons
