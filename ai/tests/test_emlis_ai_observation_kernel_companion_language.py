from __future__ import annotations

from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, assert_phase1_display_closed, run_multi_perspective_case


def test_companion_material_is_kept_in_structure_while_composer_remains_closed():
    memo = """
たまに泣きそうになるくらい嫌になる時があるけど、それだと悔しいしもったいない気がする。
どう頑張ればいいのか分からなくなるし、最近めっちゃイライラする。
それらを忘れたい時にチャットで話していると少し癒される。
"""
    result = run_multi_perspective_case(memo, display_name="Mash", emotion="怒り", category="仕事")

    assert_phase1_display_closed(result.decision)
    assert result.text == ""
    assert any(term in span.raw_text for span in result.evidence for term in ("泣きそう", "頑張れば", "イライラ"))
    assert result.reader.understandable is False
    assert result.grounding.passed is False
    assert_no_legacy_observation_text(result.text)
