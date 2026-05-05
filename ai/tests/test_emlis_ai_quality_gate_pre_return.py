from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_quality_gate import evaluate_emlis_ai_quality_gate


def test_quality_gate_blocks_broken_connection_and_missing_presence_line():
    capability = resolve_emlis_ai_capability_for_tier("free")
    result = evaluate_emlis_ai_quality_gate(
        comment_text="Emlisです。\nたまに泣きそうになるくらい嫌になる時あるけどそれだとことが、今回大きく残っていたのですね。",
        capability=capability,
        used_sources=["current_input"],
        evidence_by_line={"receive": [{"kind": "emotion", "ref_id": "emo-cur"}]},
        fallback_used=False,
        allowed_line_count=9,
        sample_user_word_anchors=[{"text": "たまに泣きそうになるくらい嫌になる時あるけどそれだと"}],
        user_word_anchor_count=1,
        understanding_patterns=["sadness_anger_conflict"],
        final_reader_passed=False,
        pre_return_blocking_enabled=True,
    )

    assert result.passed is False
    assert result.broken_connection_blocked is False
    assert result.presence_line_present is False
    assert result.final_reader_passed is False
    assert result.pre_return_blocking_enabled is True
