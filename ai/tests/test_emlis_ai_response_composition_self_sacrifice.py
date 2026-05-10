from __future__ import annotations

from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, assert_phase1_display_closed, run_multi_perspective_case


SELF_SACRIFICE_MEMO = """
どこかで私が我慢していれば、誰にも心配かけないし負担もかけないと思ってしまう。
でも我慢することだけが正しいわけじゃなくて、本当はしんどい時に誰かへ話したい気持ちもある。
大切な人のことを守りたい気持ちと、自分も潰れたくない気持ちが同じ場所にある。
"""


def test_self_sacrifice_structure_is_ready_but_body_is_closed_before_composer_phase():
    result = run_multi_perspective_case(SELF_SACRIFICE_MEMO, display_name="Mash", emotion="自己理解", category="人間関係")

    assert_phase1_display_closed(result.decision)
    assert result.graph.core_tensions
    assert result.graph.pressure_sources or result.graph.self_awareness
    assert result.text == ""
    assert any(term in span.raw_text for span in result.evidence for term in ("我慢", "心配", "負担"))
    assert result.reader.understandable is False
    assert result.grounding.passed is False
    assert_no_legacy_observation_text(result.text)
