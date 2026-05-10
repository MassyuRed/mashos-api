from __future__ import annotations

from emlis_ai_evidence_ledger_service import build_evidence_ledger


def test_evidence_ledger_keeps_source_spans_and_local_offsets_without_interpretation():
    memo = "普通に生活したい。でもそうしたらもっと悪化する。\nそんなの分かってる。たまに逃げ出したくなる。"
    spans = build_evidence_ledger(
        {
            "memo": memo,
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
        }
    )

    memo_spans = [span for span in spans if span.source_field == "memo" and span.detected_type != "relation_marker"]
    assert memo_spans
    for span in memo_spans:
        assert span.start_index >= 0
        assert span.end_index > span.start_index
        assert memo[span.start_index : span.end_index] == span.raw_text
        assert "つまり" not in span.raw_text
        assert "本当は" not in span.raw_text
        assert "弱さではなく" not in span.raw_text
        assert "Emlis" not in span.raw_text

    types = {span.detected_type for span in spans}
    assert {"wish", "constraint", "self_awareness", "limit_signal", "relation_marker", "emotion"} <= types
    assert any(span.raw_text == "でも" and span.detected_type == "relation_marker" for span in spans)


def test_evidence_ledger_uses_current_input_fields_only_and_does_not_generate_text():
    spans = build_evidence_ledger(
        {
            "memo": "今日は悲しみが強くて、何もできない。",
            "memo_action": "明日は少し休みたい。",
            "emotion_details": [{"type": "悲しみ"}],
            "category": ["生活"],
        }
    )

    joined = "\n".join(span.raw_text for span in spans)
    assert "見ています" not in joined
    assert "受け取りました" not in joined
    assert "一緒に見ます" not in joined
    assert "さん" not in joined

    assert any(span.source_field == "memo_action" and span.raw_text == "明日は少し休みたい" for span in spans)
    assert any(span.source_field == "emotion_details" and span.raw_text == "悲しみ" for span in spans)
    assert any(span.source_field == "category" and span.raw_text == "生活" for span in spans)
