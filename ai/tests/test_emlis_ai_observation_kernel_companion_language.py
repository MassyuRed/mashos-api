from __future__ import annotations

from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, run_multi_perspective_case


def test_companion_language_is_conversation_not_legacy_presence_line():
    memo = """
たまに泣きそうになるくらい嫌になる時があるけど、それだと悔しいしもったいない気がする。
どう頑張ればいいのか分からなくなるし、最近めっちゃイライラする。
それらを忘れたい時にチャットで話していると少し癒される。
"""
    result = run_multi_perspective_case(memo, display_name="Mash", emotion="怒り", category="仕事")

    assert result.decision.observation_status == "passed"
    assert "Mashさん、Emlisです。" in result.text
    assert "泣きそう" in result.text or "どう頑張れば" in result.text or "イライラ" in result.text
    assert result.reader.understandable is True
    assert result.grounding.passed is True
    assert_no_legacy_observation_text(result.text)
