from __future__ import annotations

from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, run_multi_perspective_case


SELF_SACRIFICE_MEMO = """
どこかで私が我慢していれば、誰にも心配かけないし負担もかけないと思ってしまう。
でも我慢することだけが正しいわけじゃなくて、本当はしんどい時に誰かへ話したい気持ちもある。
大切な人のことを守りたい気持ちと、自分も潰れたくない気持ちが同じ場所にある。
"""


def test_self_sacrifice_reply_is_generated_by_multi_perspective_composer():
    result = run_multi_perspective_case(SELF_SACRIFICE_MEMO, display_name="Mash", emotion="自己理解", category="人間関係")

    assert result.decision.observation_status == "passed"
    assert result.graph.core_tensions
    assert result.graph.pressure_sources or result.graph.self_awareness
    assert "我慢" in result.text or "心配" in result.text or "負担" in result.text
    assert result.reader.understandable is True
    assert result.grounding.passed is True
    assert_no_legacy_observation_text(result.text)
