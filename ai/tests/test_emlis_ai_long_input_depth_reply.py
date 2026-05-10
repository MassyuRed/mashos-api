from __future__ import annotations

from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, assert_phase1_display_closed, run_multi_perspective_case


LONG_MEMO = """
体も心も完全に元気な状態ではなくて、好きなことをもっとしたい気持ちはあるのに、前みたいに動けない。
休んでいるだけに見えるかもしれないけど、実際には追いついていない感じがずっとあって焦る。
楽しみたい願いもあるし、でも今は無理に動くと崩れそうな怖さもある。
"""


def test_long_clear_input_builds_multiple_observation_layers_and_stays_closed_before_composer():
    result = run_multi_perspective_case(LONG_MEMO, display_name="Mash", emotion="自己理解", category="生活")

    assert len(result.evidence) >= 4
    assert result.graph.primary_state.text
    assert result.graph.core_tensions or result.graph.pressure_sources
    assert result.graph.value_or_strength_signals or result.graph.limit_signals or result.graph.self_awareness
    assert result.text == ""
    assert result.reader.understandable is False
    assert result.grounding.passed is False
    assert_phase1_display_closed(result.decision)
    assert_no_legacy_observation_text(result.text)
